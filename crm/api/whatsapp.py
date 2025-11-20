import json

import frappe
from frappe import _

from crm.api.doc import get_assigned_users
from crm.fcrm.doctype.crm_notification.crm_notification import notify_user
from crm.integrations.api import get_contact_lead_or_deal_from_number


def validate(doc, method):
	# Ensure incoming messages never have label="Manual"
	# Manual label is only for outgoing messages sent from CRM (not from AI)
	if doc.type == "Incoming":
		if doc.get("label") == "Manual":
			doc.label = None  # Clear Manual label for incoming messages
	
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
	
	# Get phone number from Lead or Deal
	phone_numbers = []
	
	if reference_doctype and reference_name:
		try:
			ref_doc = frappe.get_doc(reference_doctype, reference_name)
			mobile_no = ref_doc.get("mobile_no")
			if mobile_no:
				phone_numbers.append(mobile_no)
			
			# For Deal, also get phone from associated Lead
			if reference_doctype == "CRM Deal":
				lead = ref_doc.get("lead")
				if lead:
					lead_doc = frappe.get_doc("CRM Lead", lead)
					lead_mobile = lead_doc.get("mobile_no")
					if lead_mobile:
						phone_numbers.append(lead_mobile)
		except Exception:
			pass
	
	if not phone_numbers:
		return []
	
	# Normalize phone numbers: remove spaces, dashes, parentheses, and +
	# This function normalizes a phone number for comparison
	def normalize_phone(phone):
		if not phone:
			return ""
		return phone.strip().replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace("+", "")
	
	normalized_phones = [normalize_phone(p) for p in phone_numbers if p]
	
	if not normalized_phones:
		return []
	
	# Get ALL messages (incoming and outgoing) for these phone numbers
	# Normalize phone numbers in SQL for comparison
	messages = frappe.db.sql("""
		SELECT 
			name, type, `to`, `from`, profile_name, content_type, message_type,
			attach, template, use_template, message_id, is_reply, reply_to_message_id,
			creation, message, status, reference_doctype, reference_name,
			template_parameters, template_header_parameters
		FROM `tabWhatsApp Message`
		WHERE (
			REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(`from`, ' ', ''), '-', ''), '(', ''), ')', ''), '+', '') IN %(normalized_phones)s
			OR REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(`to`, ' ', ''), '-', ''), '(', ''), ')', ''), '+', '') IN %(normalized_phones)s
		)
		ORDER BY creation ASC
	""", {
		"normalized_phones": normalized_phones,
	}, as_dict=True)

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

			template_message["template"] = template.template or ""
			if template_message["template_header_parameters"]:
				header_parameters = json.loads(template_message["template_header_parameters"])
				template.header = parse_template_parameters(template.header, header_parameters)
			template_message["header"] = template.header or ""
			template_message["footer"] = template.footer or ""

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
		if not reply_message:
			continue
		
		reply_to_message_id = reply_message.get("reply_to_message_id")
		if not reply_to_message_id:
			# Message marked as reply but has no reply_to_message_id - data inconsistency
			frappe.log_error(
				f"WhatsApp Message {reply_message.get('name')} has is_reply=True but no reply_to_message_id",
				"WhatsApp Message Data Inconsistency"
			)
			continue
		
		# Find the message that this message is replying to in the local messages list
		replied_message = next(
			(m for m in messages if m.get("message_id") == reply_to_message_id),
			None,
		)
		
		# If not found locally, search in the database
		if not replied_message:
			replied_message_list = frappe.get_all(
				"WhatsApp Message",
				filters={"message_id": reply_to_message_id},
				fields=[
					"name",
					"type",
					"to",
					"from",
					"profile_name",
					"content_type",
					"message_type",
					"attach",
					"template",
					"use_template",
					"message_id",
					"message",
					"status",
					"reference_doctype",
					"reference_name",
					"template_parameters",
					"template_header_parameters",
				],
				limit=1,
			)
			
			if replied_message_list:
				replied_message = replied_message_list[0]
				# If it's a template message, process it
				if replied_message.get("message_type") == "Template" and replied_message.get("template"):
					template = frappe.get_doc("WhatsApp Templates", replied_message["template"])
					if template:
						replied_message["template_name"] = template.template_name
						if replied_message.get("template_parameters"):
							parameters = json.loads(replied_message["template_parameters"])
							template.template = parse_template_parameters(template.template, parameters)
						replied_message["template"] = template.template or ""
						if replied_message.get("template_header_parameters"):
							header_parameters = json.loads(replied_message["template_header_parameters"])
							template.header = parse_template_parameters(template.header, header_parameters)
						replied_message["header"] = template.header or ""
						replied_message["footer"] = template.footer or ""

		# If the replied message is found, add the reply details to the reply message
		if replied_message:
			from_name = get_from_name(replied_message) if replied_message.get("from") else _("You")
			message = replied_message.get("message") or ""
			if replied_message.get("message_type") == "Template":
				message = replied_message.get("template") or ""
			reply_message["reply_message"] = message or ""
			reply_message["header"] = replied_message.get("header") or ""
			reply_message["footer"] = replied_message.get("footer") or ""
			reply_message["reply_to"] = replied_message.get("name") or ""
			reply_message["reply_to_type"] = replied_message.get("type") or ""
			reply_message["reply_to_from"] = from_name
		else:
			# Message references a reply_to_message_id that doesn't exist - log error
			frappe.log_error(
				f"WhatsApp Message {reply_message.get('name')} references reply_to_message_id {reply_to_message_id} which doesn't exist",
				"WhatsApp Message Missing Reference"
			)

	# Ensure all messages have message field as string (never None)
	for message in messages:
		if message.get("message") is None:
			message["message"] = ""
		if message.get("template") is None:
			message["template"] = ""
	
	return [message for message in messages if message["content_type"] != "reaction"]


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

	# Determine message type and label
	# Outgoing messages from CRM should have label="Manual" (unless explicitly set)
	# Incoming messages should never have label="Manual"
	message_type = "Manual"
	final_label = label
	
	# If no label specified and this is an outgoing message, default to "Manual"
	# For incoming messages, label should be None or explicitly set (not "Manual")
	if not final_label:
		# Default to "Manual" only for outgoing messages
		# The type will be set to "Outgoing" by Frappe based on the "to" field
		final_label = "Manual"
	
	doc.update(
		{
			"reference_doctype": reference_doctype,
			"reference_name": reference_name,
			"message": message or attach,
			"to": to,
			"attach": attach,
			"content_type": content_type,
			"message_type": message_type,
			"label": final_label,
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
	reference_doctype = message.get("reference_doctype")
	reference_name = message.get("reference_name")
	
	# If message doesn't have reference, try to get name from profile_name or from field
	if not reference_doctype or not reference_name:
		# Try to get profile name from the message itself
		profile_name = message.get("profile_name")
		if profile_name:
			return profile_name
		# Fallback to phone number
		from_field = message.get("from")
		if from_field:
			return from_field
		return _("Unknown")
	
	try:
		doc = frappe.get_doc(reference_doctype, reference_name)
		from_name = ""
		if reference_doctype == "CRM Deal":
			if doc.get("contacts"):
				for c in doc.get("contacts"):
					if c.is_primary:
						from_name = c.full_name or c.mobile_no
						break
			else:
				from_name = doc.get("lead_name")
		else:
			from_name = " ".join(filter(None, [doc.get("first_name"), doc.get("last_name")]))
		return from_name or _("Unknown")
	except Exception:
		# If document doesn't exist or can't be accessed, fallback to profile_name or from
		profile_name = message.get("profile_name")
		if profile_name:
			return profile_name
		from_field = message.get("from")
		if from_field:
			return from_field
		return _("Unknown")
