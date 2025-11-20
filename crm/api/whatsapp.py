import json

import frappe
from frappe import _

from crm.api.doc import get_assigned_users
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user
from crm.integrations.api import get_contact_lead_or_deal_from_number


def validate(doc, method):
	# Fix message_type for incoming messages - they should NOT be "Manual"
	# "Manual" should only be for messages sent manually from CRM
	if doc.type == "Incoming":
		# Incoming messages from WhatsApp should not have message_type "Manual"
		if doc.get("message_type") == "Manual":
			# Set to empty or None, or keep it as is if it's a template
			if not doc.get("use_template"):
				doc.message_type = None
	
	# Set message_type for outgoing messages sent from CRM
	if doc.type == "Outgoing" and not doc.get("use_template"):
		# If message_type is not set and it's not a template, it's a manual message
		if not doc.get("message_type"):
			doc.message_type = "Manual"
	
	if doc.type == "Incoming" and doc.get("from"):
		result = get_contact_lead_or_deal_from_number(doc.get("from"))
		if result:
			name, doctype = result
			if name is not None:
				doc.reference_doctype = doctype
				doc.reference_name = name

	if doc.type == "Outgoing" and doc.get("to"):
		result = get_contact_lead_or_deal_from_number(doc.get("to"))
		if result:
			name, doctype = result
			if name is not None:
				doc.reference_doctype = doctype
				doc.reference_name = name


def on_update(doc, method):
	frappe.publish_realtime(
		"whatsapp_message",
		{
			"reference_doctype": doc.reference_doctype,
			"reference_name": doc.reference_name,
		},
	)

	notify_agent(doc)


def notify_agent(doc):
	if doc.type == "Incoming":
		doctype = doc.reference_doctype
		if doctype and doctype.startswith("CRM "):
			doctype = doctype[4:].lower()
		notification_text = f"""
            <div class="mb-2 leading-5 text-ink-gray-5">
                <span class="font-medium text-ink-gray-9">{_("You")}</span>
                <span>{_("received a whatsapp message in {0}").format(doctype)}</span>
                <span class="font-medium text-ink-gray-9">{doc.reference_name}</span>
            </div>
        """
		assigned_users = get_assigned_users(doc.reference_doctype, doc.reference_name)
		for user in assigned_users:
			notify_user(
				{
					"owner": doc.owner,
					"assigned_to": user,
					"notification_type": "WhatsApp",
					"message": doc.message,
					"notification_text": notification_text,
					"reference_doctype": "WhatsApp Message",
					"reference_docname": doc.name,
					"redirect_to_doctype": doc.reference_doctype,
					"redirect_to_docname": doc.reference_name,
				}
			)


@frappe.whitelist()
def is_whatsapp_enabled():
	if not frappe.db.exists("DocType", "WhatsApp Settings"):
		return False
	return frappe.get_cached_value("WhatsApp Settings", "WhatsApp Settings", "enabled")


@frappe.whitelist()
def is_whatsapp_installed():
	if not frappe.db.exists("DocType", "WhatsApp Settings"):
		return False
	return True


@frappe.whitelist()
def get_whatsapp_messages(reference_doctype, reference_name):
	# twilio integration app is not compatible with crm app
	# crm has its own twilio integration in built
	if "twilio_integration" in frappe.get_installed_apps():
		return []
	if not frappe.db.exists("DocType", "WhatsApp Message"):
		return []
	
	# Get phone numbers associated with this document
	phone_numbers = []
	doc = frappe.get_doc(reference_doctype, reference_name)
	
	if reference_doctype == "CRM Lead":
		if doc.mobile_no:
			phone_numbers.append(doc.mobile_no)
		if doc.phone:
			phone_numbers.append(doc.phone)
	elif reference_doctype == "CRM Deal":
		# Get lead phone numbers
		if doc.lead:
			lead = frappe.get_doc("CRM Lead", doc.lead)
			if lead.mobile_no:
				phone_numbers.append(lead.mobile_no)
			if lead.phone:
				phone_numbers.append(lead.phone)
		# Get contact phone numbers
		if doc.contacts:
			for contact_link in doc.contacts:
				if contact_link.contact:
					contact = frappe.get_doc("Contact", contact_link.contact)
					if contact.mobile_no:
						phone_numbers.append(contact.mobile_no)
					if contact.phone:
						phone_numbers.append(contact.phone)
					# Also check phone_nos child table
					if hasattr(contact, "phone_nos") and contact.phone_nos:
						for phone in contact.phone_nos:
							if phone.phone:
								phone_numbers.append(phone.phone)
	
	# If no phone numbers found, return empty list
	if not phone_numbers:
		return []
	
	# Get ALL messages and filter by phone number match
	# This ensures we show ALL messages for this phone number, regardless of reference_doctype/reference_name
	from crm.utils import are_same_phone_number
	
	all_messages = frappe.get_all(
		"WhatsApp Message",
		fields=[
			"name",
			"type",
			"to",
			"from",
			"content_type",
			"message_type",
			"attach",
			"template",
			"use_template",
			"message_id",
			"is_reply",
			"reply_to_message_id",
			"creation",
			"message",
			"status",
			"reference_doctype",
			"reference_name",
			"template_parameters",
			"template_header_parameters",
		],
		order_by="creation asc",
	)
	
	# Filter messages by phone number match - show ALL messages for this phone number
	messages = []
	for msg in all_messages:
		# Check if message from/to matches any of our phone numbers
		msg_from = msg.get("from") or ""
		msg_to = msg.get("to") or ""
		
		# For incoming messages, check if 'from' matches
		# For outgoing messages, check if 'to' matches
		should_include = False
		
		if msg.get("type") == "Incoming" and msg_from:
			for phone in phone_numbers:
				if phone and are_same_phone_number(msg_from, phone, validate=False):
					should_include = True
					break
		elif msg.get("type") == "Outgoing" and msg_to:
			for phone in phone_numbers:
				if phone and are_same_phone_number(msg_to, phone, validate=False):
					should_include = True
					break
		
		if should_include:
			messages.append(msg)

	# Filter messages to get only Template messages
	template_messages = [message for message in messages if message["message_type"] == "Template"]

	# Iterate through template messages
	for template_message in template_messages:
		# Find the template that this message is using
		template = frappe.get_doc("WhatsApp Templates", template_message["template"])

		# If the template is found, add the template details to the template message
		if template:
			template_message["template_name"] = template.template_name
			if template_message["template_parameters"]:
				parameters = json.loads(template_message["template_parameters"])
				template.template = parse_template_parameters(template.template, parameters)

			template_message["template"] = template.template
			if template_message["template_header_parameters"]:
				header_parameters = json.loads(template_message["template_header_parameters"])
				template.header = parse_template_parameters(template.header, header_parameters)
			template_message["header"] = template.header
			template_message["footer"] = template.footer

	# Filter messages to get only reaction messages
	reaction_messages = [message for message in messages if message["content_type"] == "reaction"]

	# Iterate through reaction messages
	for reaction_message in reaction_messages:
		# Find the message that this reaction is reacting to
		reacted_message = next(
			(m for m in messages if m["message_id"] == reaction_message["reply_to_message_id"]),
			None,
		)

		# If the reacted message is found, add the reaction to it
		if reacted_message:
			reacted_message["reaction"] = reaction_message["message"]

	for message in messages:
		from_name = get_from_name(message) if message["from"] else _("You")
		message["from_name"] = from_name
	# Filter messages to get only replies
	reply_messages = [message for message in messages if message["is_reply"]]

	# Iterate through reply messages
	for reply_message in reply_messages:
		# Find the message that this message is replying to
		replied_message = next(
			(m for m in messages if m["message_id"] == reply_message["reply_to_message_id"]),
			None,
		)

		# If the replied message is found, add the reply details to the reply message
		if replied_message:
			from_name = get_from_name(reply_message) if replied_message.get("from") else _("You")
			message = replied_message["message"]
			if replied_message["message_type"] == "Template":
				message = replied_message["template"]
			reply_message["reply_message"] = message
			reply_message["header"] = replied_message.get("header") or ""
			reply_message["footer"] = replied_message.get("footer") or ""
			reply_message["reply_to"] = replied_message["name"]
			reply_message["reply_to_type"] = replied_message["type"]
			reply_message["reply_to_from"] = from_name
		else:
			# If replied message not found, set default values
			reply_message["reply_to_from"] = _("Unknown")

	# Filter out reactions and sort by creation date
	filtered_messages = [message for message in messages if message["content_type"] != "reaction"]
	
	# Sort by creation date (ascending - oldest first)
	filtered_messages.sort(key=lambda x: x.get("creation", ""))
	
	return filtered_messages


@frappe.whitelist()
def create_whatsapp_message(
	reference_doctype,
	reference_name,
	message,
	to,
	attach,
	reply_to,
	content_type="text",
	label=None,
):
	doc = frappe.new_doc("WhatsApp Message")

	if reply_to:
		reply_doc = frappe.get_doc("WhatsApp Message", reply_to)
		doc.update(
			{
				"is_reply": True,
				"reply_to_message_id": reply_doc.message_id,
			}
		)

	doc.update(
		{
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"message": message or attach,
			"to": to,
			"attach": attach,
			"content_type": content_type,
			"message_type": "Manual",
			"label": label or "Manual",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def send_whatsapp_template(reference_doctype, reference_name, template, to):
	doc = frappe.new_doc("WhatsApp Message")
	doc.update(
		{
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"message_type": "Template",
			"message": "Template message",
			"content_type": "text",
			"use_template": True,
			"template": template,
			"to": to,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


@frappe.whitelist()
def react_on_whatsapp_message(emoji, reply_to_name):
	reply_to_doc = frappe.get_doc("WhatsApp Message", reply_to_name)
	to = (reply_to_doc.type == "Incoming" and reply_to_doc.get("from")) or reply_to_doc.to
	doc = frappe.new_doc("WhatsApp Message")
	doc.update(
		{
			"reference_doctype": reply_to_doc.reference_doctype,
			"reference_name": reply_to_doc.reference_name,
			"message": emoji,
			"to": to,
			"reply_to_message_id": reply_to_doc.message_id,
			"content_type": "reaction",
		}
	)
	doc.insert(ignore_permissions=True)
	return doc.name


def parse_template_parameters(string, parameters):
	for i, parameter in enumerate(parameters, start=1):
		placeholder = "{{" + str(i) + "}}"
		string = string.replace(placeholder, parameter)

	return string


def get_from_name(message):
	doc = frappe.get_doc(message["reference_doctype"], message["reference_name"])
	from_name = ""
	if message["reference_doctype"] == "CRM Deal":
		if doc.get("contacts"):
			for c in doc.get("contacts"):
				if c.is_primary:
					from_name = c.full_name or c.mobile_no
					break
		else:
			from_name = doc.get("lead_name")
	else:
		from_name = " ".join(filter(None, [doc.get("first_name"), doc.get("last_name")]))
	return from_name
