# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.desk.form.assign_to import add as assign
from frappe.model.document import Document
from frappe.utils import has_gravatar, validate_email_address

from crm.fcrm.doctype.crm_service_level_agreement.utils import get_sla
from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import (
	add_status_change_log,
)
from crm.fcrm.doctype.crm_lead.status_change_notification import send_status_change_notification


class CRMLead(Document):
	# begin: auto-generated types
	# This code is auto-generated. Do not modify anything in this block.

	from typing import TYPE_CHECKING

	if TYPE_CHECKING:
		from crm.fcrm.doctype.crm_products.crm_products import CRMProducts
		from crm.fcrm.doctype.crm_rolling_response_time.crm_rolling_response_time import CRMRollingResponseTime
		from crm.fcrm.doctype.crm_status_change_log.crm_status_change_log import CRMStatusChangeLog
		from frappe.types import DF

		annual_revenue: DF.Currency
		communication_status: DF.Link | None
		converted: DF.Check
		email: DF.Data | None
		facebook_form_id: DF.Data | None
		facebook_lead_id: DF.Data | None
		first_name: DF.Data
		first_responded_on: DF.Datetime | None
		first_response_time: DF.Duration | None
		gender: DF.Link | None
		image: DF.AttachImage | None
		industry: DF.Link | None
		job_title: DF.Data | None
		last_name: DF.Data | None
		last_responded_on: DF.Datetime | None
		last_response_time: DF.Duration | None
		lead_name: DF.Data | None
		lead_owner: DF.Link | None
		middle_name: DF.Data | None
		mobile_no: DF.Data | None
		naming_series: DF.Literal["CRM-LEAD-.YYYY.-"]
		net_total: DF.Currency
		no_of_employees: DF.Literal["1-10", "11-50", "51-200", "201-500", "501-1000", "1000+"]
		organization: DF.Data | None
		phone: DF.Data | None
		products: DF.Table[CRMProducts]
		response_by: DF.Datetime | None
		rolling_responses: DF.Table[CRMRollingResponseTime]
		salutation: DF.Link | None
		sla: DF.Link | None
		sla_creation: DF.Datetime | None
		sla_status: DF.Literal["", "First Response Due", "Rolling Response Due", "Failed", "Fulfilled"]
		source: DF.Link | None
		status: DF.Link
		status_change_log: DF.Table[CRMStatusChangeLog]
		territory: DF.Link | None
		total: DF.Currency
		website: DF.Data | None
	# end: auto-generated types

	def _validate_links(self):
		"""Fix: Converti lo status dalla traduzione al nome inglese prima della validazione."""
		# Se lo status è impostato, cerca di trovare il record corrispondente nel database
		if self.status:
			# Controlla se esiste già come è
			if not frappe.db.exists("CRM Lead Status", self.status):
				# Non esiste: potrebbe essere tradotto
				# Usa un mapping diretto italiano -> inglese
				translation_map = self._get_status_translation_map()
				if self.status in translation_map:
					self.status = translation_map[self.status]
		
		# Chiama la validazione parent
		super()._validate_links()
	
	def _get_status_translation_map(self):
		"""
		Ritorna un mapping dalle traduzioni ai nomi inglesi degli stati.
		Usa un fallback hardcoded per garantire che funzioni sempre.
		"""
		# Mapping hardcoded per le traduzioni comuni (fallback robusto)
		hardcoded_map = {
			"Attesa Pagamento": "Awaiting Payment",
			"Confermato": "Confirmed",
			"Non Pagato": "Not Paid",
			"Rifiutato": "Rejected",
			"Nuovo": "New",
			"Contattato": "Contacted",
			"Negoziazione": "Negotiation",
			"Ripianificato": "Rescheduled",
		}
		
		# Verifica che gli stati esistano nel database
		verified_map = {}
		for translated, english in hardcoded_map.items():
			if frappe.db.exists("CRM Lead Status", english):
				verified_map[translated] = english
		
		return verified_map
	

	def before_validate(self):
		self.set_sla()

	def validate(self):
		self.set_full_name()
		self.set_lead_name()
		self.set_title()
		self.validate_email()
		if not self.is_new() and self.has_value_changed("lead_owner") and self.lead_owner:
			self.share_with_agent(self.lead_owner)
			self.assign_agent(self.lead_owner)
		if self.has_value_changed("status"):
			add_status_change_log(self)
			# Invia notifica WhatsApp se configurata per questo stato
			send_status_change_notification(self)

	def after_insert(self):
		if self.lead_owner:
			self.assign_agent(self.lead_owner)

	def before_save(self):
		self.apply_sla()

	def set_full_name(self):
		if self.first_name:
			self.lead_name = " ".join(
				filter(
					None,
					[
						self.salutation,
						self.first_name,
						self.middle_name,
						self.last_name,
					],
				)
			)

	def set_lead_name(self):
		if not self.lead_name:
			# Check for leads being created through data import
			if not self.organization and not self.email and not self.flags.ignore_mandatory:
				frappe.throw(_("A Lead requires either a person's name or an organization's name"))
			elif self.organization:
				self.lead_name = self.organization
			elif self.email:
				self.lead_name = self.email.split("@")[0]
			else:
				self.lead_name = "Unnamed Lead"

	def set_title(self):
		self.title = self.organization or self.lead_name

	def validate_email(self):
		if self.email:
			if not self.flags.ignore_email_validation:
				validate_email_address(self.email, throw=True)

			if self.email == self.lead_owner:
				frappe.throw(_("Lead Owner cannot be same as the Lead Email Address"))

			if self.is_new() or not self.image:
				self.image = has_gravatar(self.email)

	def assign_agent(self, agent):
		if not agent:
			return

		assignees = self.get_assigned_users()
		if assignees:
			for assignee in assignees:
				if agent == assignee:
					# the agent is already set as an assignee
					return

		assign({"assign_to": [agent], "doctype": "CRM Lead", "name": self.name})

	def share_with_agent(self, agent):
		if not agent:
			return

		docshares = frappe.get_all(
			"DocShare",
			filters={"share_name": self.name, "share_doctype": self.doctype},
			fields=["name", "user"],
		)

		shared_with = [d.user for d in docshares] + [agent]

		for user in shared_with:
			if user == agent and not frappe.db.exists(
				"DocShare",
				{"user": agent, "share_name": self.name, "share_doctype": self.doctype},
			):
				frappe.share.add_docshare(
					self.doctype,
					self.name,
					agent,
					write=1,
					flags={"ignore_share_permission": True},
				)
			elif user != agent:
				frappe.share.remove(self.doctype, self.name, user)

	def create_contact(self, existing_contact=None, throw=True):
		if not self.lead_name:
			self.set_full_name()
			self.set_lead_name()

		existing_contact = existing_contact or self.contact_exists(throw)
		if existing_contact:
			self.update_lead_contact(existing_contact)
			return existing_contact

		contact = frappe.new_doc("Contact")
		contact.update(
			{
				"first_name": self.first_name or self.lead_name,
				"last_name": self.last_name,
				"salutation": self.salutation,
				"gender": self.gender,
				"designation": self.job_title,
				"company_name": self.organization,
				"image": self.image or "",
			}
		)

		if self.email:
			contact.append("email_ids", {"email_id": self.email, "is_primary": 1})

		if self.phone:
			contact.append("phone_nos", {"phone": self.phone, "is_primary_phone": 1})

		if self.mobile_no:
			contact.append("phone_nos", {"phone": self.mobile_no, "is_primary_mobile_no": 1})

		contact.insert(ignore_permissions=True)
		contact.reload()  # load changes by hooks on contact

		return contact.name

	def create_organization(self, existing_organization=None):
		if not self.organization and not existing_organization:
			return

		# If existing_organization is provided, use it
		if existing_organization:
			self.db_set("organization", existing_organization)
			return existing_organization

		# Check if self.organization is already a valid ID (not a name)
		# First, try to load it as an ID
		org_id_exists = frappe.db.exists("CRM Organization", self.organization)
		if org_id_exists:
			# It's already a valid ID, just return it
			return self.organization

		# If it looks like an ID (starts with CRMORG-) but doesn't exist, clear it
		if self.organization and self.organization.startswith("CRMORG-"):
			# It's an ID that doesn't exist anymore, clear the reference
			frappe.logger("crm").warning(f"Organization ID {self.organization} does not exist, clearing reference")
			self.db_set("organization", None)
			return None

		# Otherwise, treat it as a name and search by organization_name
		existing_organization = frappe.db.exists(
			"CRM Organization", {"organization_name": self.organization}
		)
		if existing_organization:
			self.db_set("organization", existing_organization)
			return existing_organization

		# Create new organization with the name
		organization = frappe.new_doc("CRM Organization")
		organization.update(
			{
				"organization_name": self.organization,
				"website": self.website,
				"territory": self.territory,
				"industry": self.industry,
				"annual_revenue": self.annual_revenue,
			}
		)
		organization.insert(ignore_permissions=True)
		return organization.name

	def update_lead_contact(self, contact):
		contact = frappe.get_cached_doc("Contact", contact)
		frappe.db.set_value(
			"CRM Lead",
			self.name,
			{
				"salutation": contact.salutation,
				"first_name": contact.first_name,
				"last_name": contact.last_name,
				"email": contact.email_id,
				"mobile_no": contact.mobile_no,
			},
		)

	def contact_exists(self, throw=True):
		email_exist = frappe.db.exists("Contact Email", {"email_id": self.email})
		phone_exist = frappe.db.exists("Contact Phone", {"phone": self.phone})
		mobile_exist = frappe.db.exists("Contact Phone", {"phone": self.mobile_no})

		doctype = "Contact Email" if email_exist else "Contact Phone"
		name = email_exist or phone_exist or mobile_exist

		if name:
			text = "Email" if email_exist else "Phone" if phone_exist else "Mobile No"
			data = self.email if email_exist else self.phone if phone_exist else self.mobile_no

			value = "{0}: {1}".format(text, data)

			contact = frappe.db.get_value(doctype, name, "parent")

			if throw:
				frappe.throw(
					_("Contact already exists with {0}").format(value),
					title=_("Contact Already Exists"),
				)
			return contact

		return False

	def create_deal(self, contact, organization, deal=None):
		new_deal = frappe.new_doc("CRM Deal")

		lead_deal_map = {
			"lead_owner": "deal_owner",
		}

		restricted_fieldtypes = [
			"Tab Break",
			"Section Break",
			"Column Break",
			"HTML",
			"Button",
			"Attach",
		]
		restricted_map_fields = [
			"name",
			"naming_series",
			"creation",
			"owner",
			"modified",
			"modified_by",
			"idx",
			"docstatus",
			"status",
			"email",
			"mobile_no",
			"phone",
			"sla",
			"sla_status",
			"response_by",
			"first_response_time",
			"first_responded_on",
			"communication_status",
			"sla_creation",
			"status_change_log",
			"products",  # Don't copy products here - they're copied manually later
		]

		for field in self.meta.fields:
			if field.fieldtype in restricted_fieldtypes:
				continue
			if field.fieldname in restricted_map_fields:
				continue

			fieldname = field.fieldname
			if field.fieldname in lead_deal_map:
				fieldname = lead_deal_map[field.fieldname]

			if hasattr(new_deal, fieldname):
				if fieldname == "organization":
					new_deal.update({fieldname: organization})
				else:
					new_deal.update({fieldname: self.get(field.fieldname)})

		# Ensure delivery fields are copied if they exist on lead and deal
		try:
			if hasattr(self, "delivery_date") and getattr(self, "delivery_date", None):
				new_deal.update({"delivery_date": self.delivery_date})
			if hasattr(self, "delivery_address") and getattr(self, "delivery_address", None):
				new_deal.update({"delivery_address": self.delivery_address})
			# Copy new delivery fields (region, city, zip)
			if hasattr(self, "delivery_region") and getattr(self, "delivery_region", None):
				new_deal.update({"delivery_region": self.delivery_region})
			if hasattr(self, "delivery_city") and getattr(self, "delivery_city", None):
				new_deal.update({"delivery_city": self.delivery_city})
			if hasattr(self, "delivery_zip") and getattr(self, "delivery_zip", None):
				new_deal.update({"delivery_zip": self.delivery_zip})
			if hasattr(self, "order_date") and getattr(self, "order_date", None):
				new_deal.update({"order_date": self.order_date})
			# Copy order notes from custom_order_details JSON field
			if hasattr(self, "custom_order_details") and self.custom_order_details:
				import json
				try:
					order_details = json.loads(self.custom_order_details) if isinstance(self.custom_order_details, str) else self.custom_order_details
					if order_details and order_details.get("notes"):
						new_deal.update({"order_notes": order_details.get("notes")})
				except (json.JSONDecodeError, AttributeError):
					pass
		except Exception:
			pass

		new_deal.update(
			{
				"lead": self.name,
				"contacts": [{"contact": contact}],
			}
		)

		if self.first_responded_on:
			new_deal.update(
				{
					"sla_creation": self.sla_creation,
					"response_by": self.response_by,
					"sla_status": self.sla_status,
					"communication_status": self.communication_status,
					"first_response_time": self.first_response_time,
					"first_responded_on": self.first_responded_on,
				}
			)

		if deal:
			new_deal.update(deal)

		# Set expected_closure_date from delivery_date automatically
		if self.delivery_date and not new_deal.get("expected_closure_date"):
			new_deal.update({"expected_closure_date": self.delivery_date})

		new_deal.insert(ignore_permissions=True)
		
		# Explicitly copy products from Lead to Deal
		if self.products:
			for lead_product in self.products:
				deal_product = frappe.get_doc({
					"doctype": "CRM Products",
					"parent": new_deal.name,
					"parenttype": "CRM Deal",
					"parentfield": "products",
					"product_code": lead_product.product_code,
					"product_name": lead_product.product_name,
					"qty": lead_product.qty,
					"rate": lead_product.rate,
					"amount": lead_product.amount,
					"discount_percentage": lead_product.discount_percentage if hasattr(lead_product, "discount_percentage") else 0,
					"discount_amount": lead_product.discount_amount if hasattr(lead_product, "discount_amount") else 0,
					"net_amount": lead_product.net_amount if hasattr(lead_product, "net_amount") else lead_product.amount,
				})
				deal_product.insert(ignore_permissions=True)
			
			# Reload deal to get updated products and recalculate totals
			new_deal.reload()
			new_deal.save(ignore_permissions=True)
		
		return new_deal.name

	def set_sla(self):
		"""
		Find an SLA to apply to the lead.
		"""
		if self.sla:
			return

		sla = get_sla(self)
		if not sla:
			self.first_responded_on = None
			self.first_response_time = None
			return
		self.sla = sla.name

	def apply_sla(self):
		"""
		Apply SLA if set.
		"""
		if not self.sla:
			return
		sla = frappe.get_last_doc("CRM Service Level Agreement", {"name": self.sla})
		if sla:
			sla.apply(self)

	def convert_to_deal(self, deal=None):
		return convert_to_deal(lead=self.name, doc=self, deal=deal)

	@staticmethod
	def get_non_filterable_fields():
		return ["converted"]

	@staticmethod
	def default_list_data():
		columns = [
			{
				"label": _("Full Name"),
				"type": "Data",
				"key": "lead_name",
				"width": "14rem",
			},
			{
				"label": _("Mobile No"),
				"type": "Data",
				"key": "mobile_no",
				"width": "12rem",
			},
			{
				"label": _("Email"),
				"type": "Data",
				"key": "email",
				"width": "14rem",
			},
			{
				"label": _("Organization"),
				"type": "Link",
				"key": "organization",
				"options": "CRM Organization",
				"width": "12rem",
			},
			{
				"label": _("Delivery Address"),
				"type": "Data",
				"key": "delivery_address",
				"width": "15rem",
			},
			{
				"label": _("Net Total"),
				"type": "Currency",
				"key": "net_total",
				"align": "right",
				"width": "10rem",
			},
			{
				"label": _("Order Date"),
				"type": "Datetime",
				"key": "order_date",
				"width": "12rem",
			},
			{
				"label": _("Delivery Date"),
				"type": "Date",
				"key": "delivery_date",
				"width": "12rem",
			},
			{
				"label": _("Custom Order Details"),
				"type": "Data",
				"key": "custom_order_details",
				"width": "15rem",
			},
		]
		rows = [
			"name",
			"lead_name",
			"mobile_no",
			"email",
			"organization",
			"delivery_address",
			"net_total",
			"currency",
			"order_date",
			"delivery_date",
			"custom_order_details",
			"status",
			"lead_owner",
			"first_name",
			"last_name",
			"modified",
			"_assign",
			"image",
		]
		return {"columns": columns, "rows": rows}

	@staticmethod
	def default_kanban_settings():
		return {
			"column_field": "status",
			"title_field": "lead_name",
			"kanban_fields": '["organization", "email", "mobile_no", "_assign", "modified"]',
		}


def _send_convert_to_deal_whatsapp_notification(lead, deal_name):
	"""
	Send WhatsApp notification when Lead is converted to Deal.
	"""
	try:
		# Get deal document
		deal = frappe.get_doc("CRM Deal", deal_name)
		
		# Check if lead has mobile number
		if not lead.mobile_no:
			return
		
		# Get brand name from settings
		brand_name = frappe.db.get_single_value("FCRM Settings", "brand_name")
		
		# Format order number: CRM-DEAL-2025-00021 -> 25-00021
		# or CRM-LEAD-2025-00021 -> 25-00021
		order_number = deal_name
		if "-" in deal_name:
			parts = deal_name.split("-")
			# Find the year (4 digits) and the number after it
			for i, part in enumerate(parts):
				if len(part) == 4 and part.isdigit():
					# Found the year
					year_short = part[-2:]  # Last 2 digits of year
					if i + 1 < len(parts):
						number = parts[i + 1]
						order_number = f"{year_short}-{number}"
						break
		
		# Build delivery address string
		delivery_parts = []
		if deal.delivery_address:
			delivery_parts.append(deal.delivery_address)
		if deal.delivery_region:
			delivery_parts.append(deal.delivery_region)
		if deal.delivery_city:
			delivery_parts.append(deal.delivery_city)
		if deal.delivery_zip:
			delivery_parts.append(deal.delivery_zip)
		delivery_address_str = ", ".join(delivery_parts) if delivery_parts else "Non specificato"
		
		# Format delivery date
		delivery_date_str = ""
		if deal.delivery_date:
			from frappe.utils import formatdate
			delivery_date_str = formatdate(deal.delivery_date, "dd/MM/yyyy")
		
		# Compose message
		message_parts = []
		message_parts.append("✅ Il tuo ordine è stato processato e preso in carico!")
		message_parts.append("L'ordine è ora in preparazione.")
		message_parts.append("")
		message_parts.append("📋 Riepilogo Ordine:")
		if delivery_date_str:
			message_parts.append(f"📅 Data di consegna: {delivery_date_str}")
		message_parts.append(f"📍 Indirizzo di consegna: {delivery_address_str}")
		message_parts.append("")
		message_parts.append(f"🔢 Numero ordine aggiornato: {order_number}")
		
		if brand_name:
			message_parts.append("")
			message_parts.append(f"Grazie per aver ordinato da {brand_name}")
		
		message = "\n".join(message_parts)
		
		# Send WhatsApp message
		from crm.api.whatsapp import create_whatsapp_message
		create_whatsapp_message(
			reference_doctype="CRM Deal",
			reference_name=deal_name,
			message=message,
			to=lead.mobile_no,
			attach="",
			reply_to=None,
			content_type="text",
			label="Convert to Deal Notification",
		)
	except Exception as e:
		# Log error but don't fail the conversion
		frappe.log_error(
			title="Error sending WhatsApp notification on convert to deal",
			message=f"Lead: {lead.name}, Deal: {deal_name}, Error: {str(e)}"
		)


@frappe.whitelist()
def convert_to_deal(lead, doc=None, deal=None, existing_contact=None, existing_organization=None):
	if not (doc and doc.flags.get("ignore_permissions")) and not frappe.has_permission(
		"CRM Lead", "write", lead
	):
		frappe.throw(_("Not allowed to convert Lead to Deal"), frappe.PermissionError)

	lead = frappe.get_cached_doc("CRM Lead", lead)
	if frappe.db.exists("CRM Lead Status", "Confirmed"):
		lead.db_set("status", "Confirmed")
	lead.db_set("converted", 1)
	if lead.sla and frappe.db.exists("CRM Communication Status", "Replied"):
		lead.db_set("communication_status", "Replied")
	contact = lead.create_contact(existing_contact, False)
	organization = lead.create_organization(existing_organization)
	_deal = lead.create_deal(contact, organization, deal)
	
	# Send WhatsApp notification after deal creation
	_send_convert_to_deal_whatsapp_notification(lead, _deal)
	
	return _deal
