"""CRM Workflow API - Contact and Lead management functions.

This module provides workflow functions for managing CRM entities:
- Contact creation and updates (with phone protection)
- Lead creation (idempotent)
- WhatsApp message integration
- Organization management

All functions are designed to be called by:
- AI agents (with phone_from injection)
- Web API (whitelisted endpoints)
- Internal CRM workflows

Security: Phone numbers are NEVER accepted from user input in AI context.
They are always injected from the thread mapping by the AI module.
"""

import frappe
from frappe import _
import re
from typing import Optional, Dict, Any, List

# Import validation function with backward compatibility
try:
    from frappe.utils import validate_email_address  # Frappe 15+
except ImportError:
    from frappe.utils.data import validate_email_address  # Frappe 14

# Constants
PHONE_PATTERN = r"\D+"  # Non-digit pattern for normalization
PRETTY_COUNTRY_CODE_LENGTH = 2
PRETTY_GROUP_SIZES = [3, 3, 4]  # Groups for pretty phone format


def _log():
	"""Get Frappe logger for workflow module.
	
	Returns a silent logger when called from AI tool calls to avoid
	permission issues with log file access.
	"""
	import os
	
	# Check environment variable first (most reliable)
	if os.getenv('AI_TOOL_CALL_MODE') == '1':
		class SilentLogger:
			def info(self, msg): pass
			def error(self, msg): pass
			def warning(self, msg): pass
			def debug(self, msg): pass
		return SilentLogger()
	
	# Check if we're in an AI context (tool call) by examining call stack
	import inspect
	frame = inspect.currentframe()
	
	# Walk up the call stack to see if we're in an AI tool call
	while frame:
		filename = frame.f_code.co_filename
		if 'ai_module' in filename or 'tool' in filename.lower():
			# We're in an AI context - return a silent logger
			class SilentLogger:
				def info(self, msg): pass
				def error(self, msg): pass
				def warning(self, msg): pass
				def debug(self, msg): pass
			return SilentLogger()
		frame = frame.f_back
	
	# Normal context - return real logger
	return frappe.logger("crm.workflow")

def _normalize_phone_to_digits(phone: str) -> str:
	"""Normalize phone number to digits only.
	
	Args:
		phone: Raw phone number (may contain +, spaces, etc.)
	
	Returns:
		Digits-only string (e.g., "393331234567")
	"""
	return re.sub(PHONE_PATTERN, "", phone or "")


def _infer_phone_from_reference(ref_dt: str, ref_dn: str) -> Optional[str]:
	"""Infer phone from latest Incoming WhatsApp Message for a reference.
	
	Looks up the most recent Incoming WhatsApp Message linked to the
	given reference DocType/Name and extracts the 'from' field.
	
	Args:
		ref_dt: Reference DocType (e.g., "CRM Deal")
		ref_dn: Reference Name
	
	Returns:
		Raw phone from WhatsApp Message or None if not found
	
	Example:
		phone = _infer_phone_from_reference("CRM Deal", "DEAL-0001")
		# Returns: "+393331234567" or None
	"""
	ref_dt = (ref_dt or "").strip()
	ref_dn = (ref_dn or "").strip()
	
	if not (ref_dt and ref_dn):
		return None
	
	row = frappe.db.get_value(
		"WhatsApp Message",
		{
			"reference_doctype": ref_dt,
			"reference_name": ref_dn,
			"type": "Incoming",
		},
		["from"],
		as_dict=True,
		order_by="creation desc",
	)
	
	phone = (row or {}).get("from")
	return str(phone).strip() if phone else None


def _format_pretty_number(digits_only: str) -> str:
	"""Format phone number as "+CC GGG GGG GGGG" for display.
	
	Assumes 2-digit country code, then groups of 3-3-4 digits.
	This is best-effort formatting for human readability.
	
	Args:
		digits_only: Digits-only phone number
	
	Returns:
		Pretty-formatted phone or original if too short
	
	Examples:
		_format_pretty_number("393331234567")
		# Returns: "+39 333 123 4567"
		
		_format_pretty_number("123")
		# Returns: "123" (too short)
	"""
	digits = _normalize_phone_to_digits(digits_only)
	
	if len(digits) < 4:
		return digits
	
	# Extract country code (first 2 digits)
	country_code = digits[:PRETTY_COUNTRY_CODE_LENGTH] if len(digits) > 2 else digits
	rest = digits[PRETTY_COUNTRY_CODE_LENGTH:] if len(digits) > 2 else ""
	
	# Split remaining into groups
	groups: List[str] = []
	offset = 0
	for size in PRETTY_GROUP_SIZES:
		if offset < len(rest):
			group = rest[offset:offset + size]
			if group:
				groups.append(group)
			offset += size
	
	# Append any remaining digits
	if offset < len(rest):
		groups.append(rest[offset:])
	
	# Format: +CC GGG GGG GGGG
	formatted = "+" + country_code
	if groups:
		formatted += " " + " ".join(groups)
	
	return formatted


def _ensure_organization_exists(org_name: str, website: Optional[str] = None) -> Dict[str, str]:
	"""Ensure CRM Organization exists, create if missing.
	
	Args:
		org_name: Organization name
		website: Optional website URL
	
	Returns:
		Dict with 'name' key containing organization DocType name
	"""
	org = frappe.db.get_value(
		"CRM Organization",
		{"organization_name": org_name},
		["name"],
		as_dict=True
	)
	
	if org:
		return org
	
	# Create new organization
	org_doc = frappe.get_doc({
		"doctype": "CRM Organization",
		"organization_name": org_name,
		"website": website,
	})
	org_doc.insert(ignore_permissions=True)
	
	_log().info(f"Created organization: {org_doc.name}")
	return {"name": org_doc.name}


def _link_contact_to_organization(mobile_no: str, org_name: str, email: Optional[str] = None) -> None:
	"""Link existing Contact to Organization if contact exists for phone.
	
	Args:
		mobile_no: Digits-only phone number
		org_name: Organization DocType name
		email: Optional email to update on contact
	"""
	if not mobile_no:
		return
	
	existing_contact = frappe.get_all(
		"Contact",
		filters={"mobile_no": mobile_no},
		fields=["name"],
		limit=1,
	)
	
	if not existing_contact:
		return
	
	contact = frappe.get_doc("Contact", existing_contact[0].name)
	
	# Update email if provided and different
	if email and (contact.get("email_id") or "").strip().lower() != email.lower():
		contact.email_id = email.lower()
		
		# Update/create primary email row
		primary_found = False
		for row in (getattr(contact, "email_ids", []) or []):
			if int(getattr(row, "is_primary", 0) or 0) == 1:
				row.email_id = email.lower()
				primary_found = True
				break
		
		if not primary_found:
			contact.append("email_ids", {"email_id": email.lower(), "is_primary": 1})
	
	# Link to organization if not already linked
	links = list(getattr(contact, "links", []) or [])
	already_linked = any(
		getattr(li, "link_doctype", "") == "CRM Organization" and 
		getattr(li, "link_name", "") == org_name
		for li in links
	)
	
	if not already_linked:
		contact.append("links", {"link_doctype": "CRM Organization", "link_name": org_name})
	
	contact.save(ignore_permissions=True)
	_log().info(f"Linked contact {contact.name} to organization {org_name}")


def _find_existing_lead(
	first_name: str,
	last_name: str,
	org_name: str,
	email: Optional[str],
	mobile_no: Optional[str]
) -> Optional[Any]:
	"""Find existing Lead to avoid duplicates.
	
	Checks by:
	1. Name + org + email (if email provided)
	2. Name + org + mobile (if mobile provided)
	
	Args:
		first_name, last_name, org_name, email, mobile_no
	
	Returns:
		Lead doc if found, None otherwise
	"""
	# Try by name + org + email
	filters = {
		"first_name": first_name,
		"last_name": last_name,
		"organization": org_name,
	}
	
	if email:
		filters["email"] = email
		existing = frappe.get_all("CRM Lead", filters=filters, fields=["name"], limit=1)
		if existing:
			return frappe.get_doc("CRM Lead", existing[0].name)
	
	# Try by mobile + org
	if mobile_no:
		existing = frappe.get_all(
			"CRM Lead",
			filters={"mobile_no": mobile_no, "organization": org_name},
			fields=["name"],
			limit=1
		)
		if existing:
			return frappe.get_doc("CRM Lead", existing[0].name)
	
	return None


def new_client_lead(**data) -> Dict[str, Any]:
	"""Create a new CRM Lead (idempotent).
	
	This function safely creates a Lead for a client, handling:
	- Field validation
	- Email and phone normalization
	- Organization creation (if needed)
	- Contact linking to organization
	- Duplicate prevention
	
	Required fields:
		- first_name: Client first name
		- last_name: Client last name
		- organization: Organization name
	
	Optional fields:
		- email: Email address
		- mobile_no: Phone number
		- website: Organization website
		- territory, industry, source: Classification fields
		- reference_doctype, reference_name: For phone inference
	
	Returns:
		{
			"success": bool,
			"lead": {...lead doc...},
			"message": str
		}
	
	Example:
		result = new_client_lead(
			first_name="Mario",
			last_name="Rossi",
			email="mario@example.com",
			mobile_no="+39 333 123 4567",
			organization="Acme Corp"
		)
	"""
	try:
		# Parse request data if not provided
		if not data and frappe.request and frappe.request.method == "POST":
			data = frappe.parse_json(frappe.request.data or {}) or {}
		
		# Validate required fields
		required = ["first_name", "last_name", "organization"]
		missing = [f for f in required if not (data.get(f) and str(data.get(f)).strip())]
		
		if missing:
			frappe.response["http_status_code"] = 400
			return {"success": False, "error": _(f"Campi mancanti: {', '.join(missing)}")}
		
		# Normalize inputs
		first_name = str(data.get("first_name")).strip()
		last_name = str(data.get("last_name")).strip()
		email = (str(data.get("email") or "").strip().lower()) or None
		mobile_no = str(data.get("mobile_no") or "").strip()
		org_name = str(data.get("organization")).strip()
		website = (data.get("website") or "").strip() or None
		territory = (data.get("territory") or "").strip() or None
		industry = (data.get("industry") or "").strip() or None
		source = (data.get("source") or "").strip() or None
		
		# Infer phone from WhatsApp if missing
		if not mobile_no:
			mobile_no = _infer_phone_from_reference(
				ref_dt=str(data.get("reference_doctype") or ""),
				ref_dn=str(data.get("reference_name") or ""),
			) or ""
		
		# Normalize phone to digits
		mobile_digits = _normalize_phone_to_digits(mobile_no) if mobile_no else None
		
		# Log request (safe)
		_log().info(
			f"new_client_lead: first='{first_name}' last='{last_name}' "
			f"org='{org_name}' email={bool(email)} phone_len={len(mobile_digits) if mobile_digits else 0}"
		)
		
		# Validate email
		if email and not validate_email_address(email):
			frappe.response["http_status_code"] = 400
			return {"success": False, "error": _("Email non valida")}
		
		# Ensure organization exists
		org = _ensure_organization_exists(org_name, website)
		
		# Link existing contact to organization (if phone matches)
		_link_contact_to_organization(mobile_digits, org["name"], email)
		
		# Check for existing lead (idempotency)
		existing_lead = _find_existing_lead(first_name, last_name, org_name, email, mobile_digits)
		
		if existing_lead:
			_log().info(f"Existing lead returned: {existing_lead.name}")
			frappe.response["http_status_code"] = 200
			return {
				"success": True,
				"message": _("Lead già esistente. Ho restituito il record."),
				"lead": existing_lead.as_dict(),
			}
		
		# Create new lead
		lead = frappe.get_doc({
			"doctype": "CRM Lead",
			"first_name": first_name,
			"last_name": last_name,
			"email": email,
			"mobile_no": mobile_digits,
			"organization": org_name,
			"status": "New",
			"website": website,
			"territory": territory,
			"industry": industry,
			"source": source,
		})
		lead.insert(ignore_permissions=True)
		
		pretty_phone = _format_pretty_number(mobile_digits or "")
		_log().info(f"Created lead: {lead.name} phone='{pretty_phone}'")
		
		frappe.response["http_status_code"] = 201
		return {
			"success": True,
			"message": _("Lead creato con successo"),
			"lead": lead.as_dict(),
		}
	
	except frappe.ValidationError as ve:
		frappe.response["http_status_code"] = 422
		return {"success": False, "error": _(str(ve))}
	except Exception as e:
		frappe.log_error(message=frappe.get_traceback(), title="workflow.new_client_lead")
		frappe.response["http_status_code"] = 500
		return {"success": False, "error": _(str(e))} 


def _find_contact_by_phone(digits: str) -> Optional[str]:
	"""Find existing Contact by phone number.
	
	Searches:
	1. Direct match on Contact.mobile_no
	2. Child table Contact Phone (normalized to digits)
	
	Args:
		digits: Digits-only phone number
	
	Returns:
		Contact name (DocType primary key) or None
	"""
	# Try direct match
	existing = frappe.get_all(
		"Contact",
		filters={"mobile_no": digits},
		fields=["name"],
		limit=1,
	)
	
	if existing:
		return existing[0].name
	
	# Try child table match (normalized)
	rows = frappe.db.sql(
		"""
		SELECT parent
		FROM `tabContact Phone`
		WHERE REGEXP_REPLACE(phone, '[^0-9]', '') = %s
		LIMIT 1
		""",
		(digits,),
		as_dict=True,
	)
	
	return rows[0].parent if rows else None


def _normalize_contact_phone(contact: Any, digits: str) -> bool:
	"""Normalize contact phone to pretty format.
	
	Args:
		contact: Contact document
		digits: Digits-only phone number
	
	Returns:
		True if changes were made, False otherwise
	"""
	pretty = _format_pretty_number(digits)
	changed = False
	
	# Update main mobile_no field
	if pretty and (contact.mobile_no or "").strip() != pretty:
		contact.mobile_no = pretty
		changed = True
	
	# Update primary mobile row in child table
	for phone_row in (getattr(contact, "phone_nos", []) or []):
		if int(getattr(phone_row, "is_primary_mobile_no", 0) or 0) == 1:
			if (phone_row.phone or "").strip() != pretty:
				phone_row.phone = pretty
				changed = True
			break
	
	return changed


def _ensure_contact_for_digits(digits: str) -> Dict[str, Any]:
	"""Ensure a Contact exists for given phone (idempotent).
	
	Finds existing contact or creates new one with phone as display name.
	Updates phone formatting to pretty format if needed.
	
	Args:
		digits: Digits-only phone number
	
	Returns:
		{
			"success": bool,
			"message": str,
			"contact": {...contact doc...}
		}
	"""
	contact_name = _find_contact_by_phone(digits)
	
	if contact_name:
		contact = frappe.get_doc("Contact", contact_name)
		
		# Normalize phone formatting
		if _normalize_contact_phone(contact, digits):
			contact.save(ignore_permissions=True)
			_log().info(f"Normalized phone for contact: {contact.name}")
		
		frappe.response["http_status_code"] = 200
		return {
			"success": True,
			"message": _("Contatto esistente trovato"),
			"contact": contact.as_dict()
		}
	
	# Create new contact
	pretty = _format_pretty_number(digits)
	display_name = pretty or f"+{digits}"
	
	new_contact = frappe.get_doc({
		"doctype": "Contact",
		"first_name": display_name,
		"mobile_no": pretty or f"+{digits}",
		"phone_nos": [{"phone": pretty or f"+{digits}", "is_primary_mobile_no": 1}],
	})
	new_contact.insert(ignore_permissions=True)
	
	_log().info(f"Created contact: {new_contact.name} phone_len={len(digits)}")
	
	frappe.response["http_status_code"] = 201
	return {
		"success": True,
		"message": _("Contatto creato"),
		"contact": new_contact.as_dict()
	}


def _extract_phone_from_message(message_name: str) -> Optional[str]:
	"""Extract phone number from WhatsApp Message document.
	
	Args:
		message_name: WhatsApp Message DocType name
	
	Returns:
		Raw phone from 'from' field or None
	"""
	if not message_name.strip():
		return None
	
	try:
		msg = frappe.get_doc("WhatsApp Message", message_name)
		phone = str(msg.get("from") or "").strip()
		return phone if phone else None
	except Exception:
		return None


def ensure_contact_from_message(
	reference_doctype: Optional[str] = None,
	reference_name: Optional[str] = None,
	message_name: Optional[str] = None,
) -> Dict[str, Any]:
	"""Ensure a Contact exists for an incoming WhatsApp message.
	
	Phone is ALWAYS inferred from internal WhatsApp Message records,
	NEVER from user input or AI. This ensures phone number security.
	
	If a matching Contact exists (by phone), it is returned.
	Otherwise, a new Contact is created with the phone as display name.
	
	Args:
		reference_doctype: Optional reference DocType (e.g., "CRM Deal")
		reference_name: Optional reference name
		message_name: Optional WhatsApp Message name
	
	Returns:
		{
			"success": bool,
			"message": str,
			"contact": {...contact doc...},
			"error": str (if failed)
		}
	
	Example:
		result = ensure_contact_from_message(
			message_name="WAMSG-0001"
		)
	"""
	try:
		# Extract phone from message or reference
		phone_raw = _extract_phone_from_message(message_name or "")
		
		if not phone_raw:
			phone_raw = _infer_phone_from_reference(
				ref_dt=str(reference_doctype or ""),
				ref_dn=str(reference_name or ""),
			)
		
		# Normalize to digits
		digits = _normalize_phone_to_digits(phone_raw or "")
		
		if not digits:
			frappe.response["http_status_code"] = 400
			return {
				"success": False,
				"error": _("Impossibile determinare il numero di telefono dal messaggio")
			}
		
		# Ensure contact exists
		return _ensure_contact_for_digits(digits)
	
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="workflow.ensure_contact_from_message"
		)
		frappe.response["http_status_code"] = 500
		return {"success": False, "error": _(str(e))}


def on_whatsapp_after_insert_ensure_contact(doc, method=None) -> None:
	"""DocEvent hook: ensure Contact exists for incoming WhatsApp messages.
	
	Called automatically by Frappe after WhatsApp Message insert.
	Internal-only; not whitelisted.
	
	Args:
		doc: WhatsApp Message document
		method: Hook method name (unused)
	"""
	try:
		# Only process incoming messages
		if (getattr(doc, "type", "") or "").lower() != "incoming":
			return
		
		# Extract and normalize phone
		phone_raw = str(doc.get("from") or "").strip()
		digits = _normalize_phone_to_digits(phone_raw)
		
		if not digits:
			_log().debug("No phone found in WhatsApp message")
			return
		
		# Ensure contact exists
		_ensure_contact_for_digits(digits)
	
	except Exception:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="workflow.on_whatsapp_after_insert_ensure_contact",
		)


def _verify_contact_phone_ownership(contact: Any, digits: str) -> bool:
	"""Verify that contact owns the given phone number.
	
	Checks both primary mobile_no and child phone_nos table.
	
	Args:
		contact: Contact document
		digits: Digits-only phone to verify
	
	Returns:
		True if contact owns this phone, False otherwise
	"""
	# Check primary mobile_no
	primary_digits = _normalize_phone_to_digits(contact.mobile_no or "")
	if primary_digits and primary_digits == digits:
		return True
	
	# Check child table
	for phone_row in (getattr(contact, "phone_nos", []) or []):
		phone_digits = _normalize_phone_to_digits(getattr(phone_row, "phone", "") or "")
		if phone_digits == digits:
			return True
	
	return False


def _update_contact_email(contact: Any, email: str) -> None:
	"""Update contact email and ensure primary row in child table.
	
	Args:
		contact: Contact document
		email: Email address to set
	"""
	email_normalized = email.strip().lower()
	
	# Set main email_id field
	contact.email_id = email_normalized
	
	# Update/create child table row
	primary_found = False
	for row in (getattr(contact, "email_ids", []) or []):
		if (row.email_id or "").strip().lower() == email_normalized:
			row.is_primary = 1
			primary_found = True
		else:
			# Demote other emails
			row.is_primary = 0
	
	if not primary_found:
		contact.append("email_ids", {
			"email_id": email_normalized,
			"is_primary": 1
		})


def _link_contact_to_org(contact: Any, org_name: str) -> None:
	"""Link Contact to CRM Organization via Dynamic Link.
	
	Args:
		contact: Contact document
		org_name: Organization DocType name
	"""
	links = list(getattr(contact, "links", []) or [])
	
	# Check if already linked
	already_linked = any(
		getattr(li, "link_doctype", "") == "CRM Organization" and
		getattr(li, "link_name", "") == org_name
		for li in links
	)
	
	if not already_linked:
		contact.append("links", {
			"link_doctype": "CRM Organization",
			"link_name": org_name
		})


def update_contact_from_thread(
	first_name: str,
	last_name: str,
	email: Optional[str] = None,
	organization: Optional[str] = None,
	confirm_organization: Optional[bool] = None,
	phone_from: Optional[str] = None,
	delivery_address: Optional[str] = None,
	website: Optional[str] = None,
	company_name: Optional[str] = None,
) -> Dict[str, Any]:
	"""Update or create Contact tied to current AI thread (by phone).
	
	This function is called by AI agents to update contact information
	during conversation. The phone number is ALWAYS injected by the
	AI runtime from the thread mapping, NEVER from user input.
	
	Required fields:
		- first_name: Contact first name
		- last_name: Contact last name
	
	Optional fields:
		- email: Email address
		- organization: Organization name
		- confirm_organization: If True, link to existing org
		- phone_from: Phone number (injected by AI runtime)
		- website: Website URL
		- company_name: Company name (saved as custom field if exists)
		- delivery_address: Delivery address (parameter kept for compatibility, but NOT saved on Contact)
	
	Behavior:
		1. Finds Contact by phone (or creates new)
		2. Updates name, email, website, and company_name
		3. If organization provided:
		   - Existing org + confirm=True: Link contact to org
		   - Existing org + confirm=False: Return needs_confirmation
		   - Non-existing org: Do NOT create (security)
	
	Note: delivery_address is NOT saved on Contact because the 'address' field
	      is a Link to Address doctype. Delivery address is saved on Lead/Deal instead.
	
	Returns:
		{
			"success": bool,
			"message": str,
			"contact": {...contact doc...},
			"organization": str (if linked),
			"needs_confirmation": bool (if org match needs confirm)
		}
	
	Example:
		result = update_contact_from_thread(
			first_name="Mario",
			last_name="Rossi",
			email="mario@example.com",
			organization="Acme Corp",
			confirm_organization=True,
			phone_from="+393331234567",  # Injected by AI runtime
		)
	"""
	try:
		# Validate required fields
		fn = (first_name or "").strip()
		ln = (last_name or "").strip()
		
		if not (fn and ln):
			frappe.response["http_status_code"] = 400
			return {
				"success": False,
				"error": _("Campi mancanti: first_name, last_name")
			}
		
		# Extract and validate phone
		raw_phone = (phone_from or "").strip()
		digits = _normalize_phone_to_digits(raw_phone)
		
		if not digits:
			frappe.response["http_status_code"] = 400
			return {
				"success": False,
				"error": _("Impossibile determinare il numero di telefono dal thread")
			}
		
		# Find or create contact
		contact_name = _find_contact_by_phone(digits)
		pretty = _format_pretty_number(digits)
		is_new = False
		
		if contact_name:
			contact = frappe.get_doc("Contact", contact_name)
			
			# Security: verify phone ownership
			if not _verify_contact_phone_ownership(contact, digits):
				frappe.response["http_status_code"] = 403
				return {
					"success": False,
					"error": _("Non autorizzato: numero non corrispondente al contatto")
				}
		else:
			# Create new contact
			display_name = pretty or f"+{digits}"
			contact = frappe.get_doc({
				"doctype": "Contact",
				"first_name": display_name,
				"mobile_no": pretty or f"+{digits}",
				"phone_nos": [{
					"phone": pretty or f"+{digits}",
					"is_primary_mobile_no": 1
				}],
			})
			contact.insert(ignore_permissions=True)
			is_new = True
			_log().info(f"Created contact from thread: {contact.name}")
		
		# Update core fields
		contact.first_name = fn
		contact.last_name = ln
		
		# Update email if provided
		if email:
			_update_contact_email(contact, email)
		
		# Update website if provided
		if website:
			contact.website = website.strip()
		
		# Update company name if provided (custom field)
		if company_name:
			company = company_name.strip()
			if hasattr(contact, 'company_name'):
				contact.company_name = company
			else:
				# Try to set via db if field exists
				try:
					frappe.db.set_value("Contact", contact.name, "company_name", company, update_modified=False)
				except Exception:
					_log().warning(f"Could not set company_name on contact: field may not exist")
		
		# Note: delivery_address is NOT saved on Contact because the 'address' field 
		# is a Link field to Address doctype, not a text field.
		# The delivery address is saved on the Lead/Deal documents instead.
		
		contact.save(ignore_permissions=True)
		_log().info(f"Updated contact: {contact.name}")
		
		# Handle organization linking
		linked_org = None
		org_name_in = (organization or "").strip()
		
		if org_name_in:
			org_row = frappe.db.get_value(
				"CRM Organization",
				{"organization_name": org_name_in},
				["name"],
				as_dict=True
			)
			
			if org_row:
				# Organization exists - check if confirmation needed
				if not bool(confirm_organization):
					frappe.response["http_status_code"] = 200
					return {
						"success": False,
						"needs_confirmation": True,
						"organization_match": org_name_in,
						"contact": contact.as_dict(),
					}
				
				# Link to organization
				linked_org = org_row.get("name")
				_link_contact_to_org(contact, linked_org)
				contact.save(ignore_permissions=True)
				_log().info(f"Linked contact {contact.name} to org {linked_org}")
		
		frappe.response["http_status_code"] = 201 if is_new else 200
		return {
			"success": True,
			"message": _("Contatto creato" if is_new else "Contatto aggiornato"),
			"contact": contact.as_dict(),
			"organization": linked_org,
			"organization_created": False,
		}
	
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="workflow.update_contact_from_thread"
		)
		frappe.response["http_status_code"] = 500
		return {"success": False, "error": _(str(e))}


def search_products(
	filter_value: Optional[str] = None,
	filter_type: Optional[str] = None,
	limit: Optional[int] = None
) -> Dict[str, Any]:
	"""Search CRM Products by tag, price, or name.
	
	This function allows AI agents to search for products using flexible filtering.
	The AI can determine the filter type automatically or specify it explicitly.
	If no filter_value is provided, returns ALL active products.
	
	Args:
		filter_value: Optional value to search for (tag name, price, or product name). If empty, returns ALL products
		filter_type: Optional filter type ("tag", "price", "name"). If None, auto-detects
		limit: Maximum number of results to return (default: 50)
	
	Returns:
		{
			"success": bool,
			"products": [
				{
					"name": str,           # Product name
					"product_code": str,   # Product code
					"standard_rate": float, # Price
					"tags": [str],         # List of tag names
					"description": str,    # Product description
					"disabled": bool        # Is disabled
				}
			],
			"total_found": int,
			"filter_applied": str,
			"message": str
		}
	
	Example:
		result = search_products("Elettronica", "tag")
		result = search_products("100", "price") 
		result = search_products("iPhone", "name")
		result = search_products("50")  # Auto-detect filter type
		result = search_products()  # Returns ALL products
	"""
	try:
		# Parse request data if not provided
		if not filter_value and frappe.request and frappe.request.method == "POST":
			data = frappe.form_dict or {}
			filter_value = data.get("filter_value", "")
			filter_type = data.get("filter_type")
			limit = data.get("limit", 50)
		
		# Set defaults for optional parameters
		filter_value = filter_value or ""
		filter_type = filter_type or None
		limit = limit or 50
		
		# Validate inputs
		filter_value = filter_value.strip()
		limit = max(1, min(int(limit), 200))  # Clamp between 1-200
		
		# If no filter_value provided, return ALL products
		if not filter_value:
			_log().info(f"Searching ALL products: limit={limit}")
			try:
				products = frappe.get_all(
					"CRM Product",
					filters={"disabled": 0},  # Only active products
					fields=[
						"name", "product_code", "product_name", "standard_rate",
						"description", "disabled"
					],
					order_by="product_name",
					limit=limit
				)
				products = _enrich_products_with_tags(products)
				
				formatted_products = []
				for product in products:
					formatted_product = _format_product_for_ai(product)
					formatted_products.append(formatted_product)
				
				frappe.response["http_status_code"] = 200
				return {
					"success": True,
					"products": formatted_products,
					"total_found": len(formatted_products),
					"filter_applied": "all",
					"message": _("Trovati {0} prodotti (tutti)").format(len(formatted_products))
				}
			except Exception as query_error:
				_log().error(f"Query failed for ALL products: {query_error}")
				frappe.response["http_status_code"] = 500
				return {"success": False, "error": f"Query failed: {str(query_error)}"}
		
		# Auto-detect filter type if not specified
		if not filter_type:
			filter_type = _detect_filter_type(filter_value)
		
		_log().info(f"Searching products: filter='{filter_value}' type='{filter_type}' limit={limit}")
		
		# Build query based on filter type
		try:
			products = _build_product_query(filter_value, filter_type, limit)
		except Exception as query_error:
			_log().error(f"Query failed for filter '{filter_value}' type '{filter_type}': {query_error}")
			frappe.response["http_status_code"] = 500
			return {"success": False, "error": f"Query failed: {str(query_error)}"}
			
		# Format results for AI consumption
		formatted_products = []
		for product in products:
			formatted_product = _format_product_for_ai(product)
			formatted_products.append(formatted_product)
		
		frappe.response["http_status_code"] = 200
		return {
			"success": True,
			"products": formatted_products,
			"total_found": len(formatted_products),
			"filter_applied": filter_type,
			"message": _("Trovati {0} prodotti").format(len(formatted_products))
		}
	
	except Exception as e:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="workflow.search_products"
		)
		frappe.response["http_status_code"] = 500
		return {"success": False, "error": _(str(e))}


def _detect_filter_type(filter_value: str) -> str:
	"""Auto-detect filter type based on input value.
	
	Args:
		filter_value: The filter value to analyze
	
	Returns:
		Filter type: "price", "tag", or "name"
	"""
	# Check if it's a price (numeric with optional currency symbols)
	price_pattern = r'^[\d\s.,€$£¥]+$'
	if re.match(price_pattern, filter_value.replace(' ', '')):
		return "price"
	
	# Check if it's likely a tag (short, single word, title case)
	if len(filter_value.split()) == 1 and filter_value.istitle():
		return "tag"
	
	# Default to name search
	return "name"


def _build_product_query(filter_value: str, filter_type: str, limit: int) -> List[Dict[str, Any]]:
	"""Build and execute product search query.
	
	Args:
		filter_value: The filter value
		filter_type: Type of filter ("tag", "price", "name")
		limit: Maximum results
	
	Returns:
		List of product dictionaries
	"""
	base_filters = {"disabled": 0}  # Only active products
	
	if filter_type == "price":
		return _query_by_price(filter_value, base_filters, limit)
	elif filter_type == "tag":
		return _query_by_tag(filter_value, base_filters, limit)
	else:  # name
		return _query_by_name(filter_value, base_filters, limit)


def _query_by_price(filter_value: str, base_filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
	"""Query products by price range.
	
	Args:
		filter_value: Price value (e.g., "100", "50-200")
		base_filters: Base filters to apply
		limit: Maximum results
	
	Returns:
		List of product dictionaries
	"""
	# Extract numeric value from price string
	price_str = re.sub(r'[^\d.,]', '', filter_value)
	try:
		price_value = float(price_str.replace(',', '.'))
	except ValueError:
		_log().warning(f"Invalid price format: {filter_value}")
		return []
	
	# Search for products with price close to the target (±20%)
	tolerance = price_value * 0.2
	min_price = max(0, price_value - tolerance)
	max_price = price_value + tolerance
	
	filters = {
		**base_filters,
		"standard_rate": [">=", min_price]
	}
	
	# Use frappe.get_all with range filter
	products = frappe.get_all(
		"CRM Product",
		filters=filters,
		fields=[
			"name", "product_code", "product_name", "standard_rate",
			"description", "disabled"
		],
		order_by="standard_rate asc",
		limit=limit * 2  # Get more to account for Python filtering
	)
	
	# Filter by max price in Python (since frappe doesn't support range filters well)
	products = [p for p in products if float(p.get("standard_rate", 0)) <= max_price]
	
	# Apply final limit
	products = products[:limit]
	
	# Get tags for each product
	return _enrich_products_with_tags(products)


def _query_by_tag(filter_value: str, base_filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
	"""Query products by tag name.
	
	Args:
		filter_value: Tag name to search for
		base_filters: Base filters to apply
		limit: Maximum results
	
	Returns:
		List of product dictionaries
	"""
	# Find products that have the specified tag
	products = frappe.db.sql("""
		SELECT DISTINCT p.name, p.product_code, p.product_name, 
		       p.standard_rate, p.description, p.disabled
		FROM `tabCRM Product` p
		INNER JOIN `tabCRM Product Tag` pt ON pt.parent = p.name
		INNER JOIN `tabCRM Product Tag Master` ptm ON pt.tag_name = ptm.name
		WHERE p.disabled = 0
		AND ptm.tag_name LIKE %s
		ORDER BY p.product_name
		LIMIT %s
	""", (f"%{filter_value}%", limit), as_dict=True)
	
	return _enrich_products_with_tags(products)


def _query_by_name(filter_value: str, base_filters: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
	"""Query products by name (LIKE search).
	
	Args:
		filter_value: Product name to search for
		base_filters: Base filters to apply
		limit: Maximum results
	
	Returns:
		List of product dictionaries
	"""
	filters = {
		**base_filters,
		"product_name": ["like", f"%{filter_value}%"]
	}
	
	products = frappe.get_all(
		"CRM Product",
		filters=filters,
		fields=[
			"name", "product_code", "product_name", "standard_rate",
			"description", "disabled"
		],
		order_by="product_name",
		limit=limit
	)
	
	return _enrich_products_with_tags(products)


def _enrich_products_with_tags(products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
	"""Enrich product list with tag information.
	
	Args:
		products: List of product dictionaries
	
	Returns:
		List of enriched product dictionaries
	"""
	if not products:
		return []
	
	try:
		product_names = [p["name"] for p in products]
		
		# Get all tags for these products
		tags_query = frappe.db.sql("""
			SELECT pt.parent, ptm.tag_name
			FROM `tabCRM Product Tag` pt
			INNER JOIN `tabCRM Product Tag Master` ptm ON pt.tag_name = ptm.name
			WHERE pt.parent IN %s
			ORDER BY pt.parent, ptm.tag_name
		""", (product_names,), as_dict=True)
		
		# Group tags by product
		tags_by_product = {}
		for tag in tags_query:
			parent = tag["parent"]
			if parent not in tags_by_product:
				tags_by_product[parent] = []
			tags_by_product[parent].append(tag["tag_name"])
		
		# Enrich products with tags
		for product in products:
			product["tags"] = tags_by_product.get(product["name"], [])
		
		return products
	except Exception as exc:
		_log().warning(f"Failed to enrich products with tags: {exc}")
		# Return products without tags if enrichment fails
		for product in products:
			product["tags"] = []
		return products


def _format_product_for_ai(product: Dict[str, Any]) -> Dict[str, Any]:
	"""Format product data for AI consumption.
	
	Args:
		product: Raw product dictionary
	
	Returns:
		Formatted product dictionary
	"""
	import re
	
	# Clean HTML from description
	description = product.get("description", "")
	if description:
		# Remove HTML tags
		description = re.sub(r'<[^>]+>', '', description)
		# Decode HTML entities
		description = description.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
		# Clean up extra whitespace
		description = re.sub(r'\s+', ' ', description).strip()
	
	return {
		"name": product.get("product_name", ""),
		"product_code": product.get("product_code", ""),
		"standard_rate": float(product.get("standard_rate", 0)),
		"tags": product.get("tags", []),
		"description": description,
		"disabled": bool(product.get("disabled", 0))
	}