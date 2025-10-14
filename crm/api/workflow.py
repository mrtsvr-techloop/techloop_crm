import frappe
from frappe import _
import re
from typing import Optional
try:
    from frappe.utils import validate_email_address  # Frappe 15+
except Exception:  # pragma: no cover
    from frappe.utils.data import validate_email_address  # Backward-compat

# Public API: workflow.new_client_lead
# Purpose: Create a new CRM Lead for a client in a safe, idempotent, and well-documented way.
# How it works:
# - Validates required fields
# - Normalizes and validates email and phone
# - Ensures the Organization exists (creates if missing)
# - Ensures we don't duplicate an existing Lead for the same person + org
# - Returns a clean JSON payload suitable for forms or AI agents
#
# Required JSON args:
#   first_name, last_name, email, mobile_no, organization
# Optional JSON args:
#   website, territory, industry, source
#
# Response format (examples):
#   { "success": true, "lead": { ...full lead doc... }, "message": "Lead creato" }
#   { "success": false, "error": "Campi mancanti: first_name, email" }

def _infer_phone_from_reference(ref_dt: str, ref_dn: str) -> Optional[str]:
	"""Try to infer phone from the latest Incoming WhatsApp Message for the same reference.

	Returns raw `from` field (as provided by WhatsApp connector) or None.
	"""
	try:
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
		val = (row or {}).get("from")
		return str(val).strip() if val else None
	except Exception:
		return None


def _format_pretty_number(digits_only: str) -> str:
	"""Return number formatted as "+XX YYY WWW ZZZZ" when length allows, else return as-is.

	This is best-effort and assumes 2-digit country code, then groups of 3-3-4.
	"""
	try:
		d = re.sub(r"\D+", "", digits_only or "")
		if len(d) < 4:
			return d
		cc = d[:2] if len(d) > 2 else d
		rest = d[2:] if len(d) > 2 else ""
		g1, g2, g3 = rest[:3], rest[3:6], rest[6:10]
		rem = rest[10:]
		parts = [p for p in [g1, g2, g3] if p]
		if rem:
			parts.append(rem)
		return "+" + cc + (" " + " ".join(parts) if parts else "")
	except Exception:
		return digits_only or ""


@frappe.whitelist(allow_guest=True)
def new_client_lead(**data):
	try:
		# Collect JSON body if not provided as kwargs
		if not data and frappe.request and frappe.request.method == "POST":
			data = frappe.parse_json(frappe.request.data or {}) or {}

		required_fields = ["first_name", "last_name", "organization"]
		missing = [f for f in required_fields if not (data.get(f) and str(data.get(f)).strip())]
		if missing:
			frappe.response["http_status_code"] = 400
			frappe.response["message"] = {"success": False, "error": _(f"Campi mancanti: {', '.join(missing)}")}
			return frappe.response["message"]

		# Normalize inputs
		first_name = str(data.get("first_name")).strip()
		last_name = str(data.get("last_name")).strip()
		email = str(data.get("email")).strip().lower()
		mobile_no = str(data.get("mobile_no")).strip()
		org_name = str(data.get("organization")).strip()
		website = (data.get("website") or "").strip() or None
		territory = (data.get("territory") or "").strip() or None
		industry = (data.get("industry") or "").strip() or None
		source = (data.get("source") or "").strip() or None


		# If mobile is missing, try to infer from WhatsApp Message
		if not mobile_no:
			mobile_no = _infer_phone_from_reference(
				ref_dt=str(data.get("reference_doctype") or ""),
				ref_dn=str(data.get("reference_name") or ""),
			)

		# Normalize phone: digits-only for idempotency matching
		if mobile_no:
			mobile_no = re.sub(r"\D+", "", mobile_no)

		# Trace input (safe keys only)
		try:
			frappe.logger().info(
				f"[crm.workflow] new_client_lead first='{first_name}' last='{last_name}' org='{org_name}' email_present={bool(email)} phone_len={len(mobile_no) if mobile_no else 0}"
			)
		except Exception:
			pass

		# Basic validations (email optional)
		if email and not validate_email_address(email):
			frappe.response["http_status_code"] = 400
			frappe.response["message"] = {"success": False, "error": _("Email non valida")}
			return frappe.response["message"]

		# Ensure Organization exists (idempotent)
		org_name_key = org_name
		org = frappe.db.get_value("CRM Organization", {"organization_name": org_name_key}, ["name"], as_dict=True)
		if not org:
			org_doc = frappe.get_doc({
				"doctype": "CRM Organization",
				"organization_name": org_name_key,
				"website": website,
			})
			org_doc.insert(ignore_permissions=True)
			org = {"name": org_doc.name}

		# Idempotency: avoid duplicate leads for the same person + org (email OR mobile as key)
		existing_lead = frappe.get_all(
			"CRM Lead",
			filters={
				"first_name": first_name,
				"last_name": last_name,
				"organization": org_name_key,
				# If email is present, match on it; else do not enforce email filter here
				# (second stage checks by phone if needed)
				**({"email": email} if email else {}),
			},
			fields=["name"],
			limit=1,
		)
		if not existing_lead and mobile_no:
			existing_lead = frappe.get_all(
				"CRM Lead",
				filters={"mobile_no": mobile_no, "organization": org_name_key},
				fields=["name"],
				limit=1,
			)

		if existing_lead:
			lead = frappe.get_doc("CRM Lead", existing_lead[0].name)
			try:
				frappe.logger().info(f"[crm.workflow] existing lead returned name={lead.name}")
			except Exception:
				pass
			frappe.response["http_status_code"] = 200
			return {
				"success": True,
				"message": _("Lead già esistente. Ho restituito il record."),
				"lead": lead.as_dict(),
			}

		# Create new Lead
		lead = frappe.get_doc({
			"doctype": "CRM Lead",
			"first_name": first_name,
			"last_name": last_name,
			"email": email,
			"mobile_no": mobile_no,
			"organization": org_name_key,
			"status": "New",
			"website": website,
			"territory": territory,
			"industry": industry,
			"source": source,
		})
		lead.insert(ignore_permissions=True)
		try:
			pretty = _format_pretty_number(mobile_no or "")
			frappe.logger().info(f"[crm.workflow] created lead name={lead.name} phone_pretty='{pretty}'")
		except Exception:
			pass

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


def _ensure_contact_for_digits(digits: str) -> dict:
	"""Idempotently ensure a Contact exists for the given digits-only phone."""
	# 1) Try direct match on Contact.mobile_no
	existing = frappe.get_all(
		"Contact",
		filters={"mobile_no": digits},
		fields=["name"],
		limit=1,
	)
	contact_name: Optional[str] = existing[0].name if existing else None

	# 2) Fallback: match on child table Contact Phone.phone (normalize by digits)
	if not contact_name:
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
		contact_name = rows[0].parent if rows else None

	if contact_name:
		doc = frappe.get_doc("Contact", contact_name)
		# Normalize stored values to pretty format for consistency
		try:
			pretty_digits = _format_pretty_number(digits)
			need_save = False
			if pretty_digits and (doc.mobile_no or "").strip() != pretty_digits:
				doc.mobile_no = pretty_digits
				need_save = True
			# Update primary mobile row if present
			for ph in (getattr(doc, "phone_nos", []) or []):
				if int(getattr(ph, "is_primary_mobile_no", 0) or 0) == 1:
					if (ph.phone or "").strip() != pretty_digits:
						ph.phone = pretty_digits
						need_save = True
					break
			if need_save:
				doc.save(ignore_permissions=True)
		except Exception:
			pass
		frappe.response["http_status_code"] = 200
		return {"success": True, "message": _("Contatto esistente trovato"), "contact": doc.as_dict()}

	# Create new Contact with phone as display-first name (no unreliable full name import)
	pretty = _format_pretty_number(digits)
	new_doc = frappe.get_doc({
		"doctype": "Contact",
		"first_name": pretty or f"+{digits}",
		"mobile_no": pretty or f"+{digits}",
		"phone_nos": [{"phone": pretty or f"+{digits}", "is_primary_mobile_no": 1}],
	})
	new_doc.insert(ignore_permissions=True)
	try:
		frappe.logger().info(f"[crm.workflow] ensure_contact: created contact name={new_doc.name} phone_len={len(digits)}")
	except Exception:
		pass
	frappe.response["http_status_code"] = 201
	return {"success": True, "message": _("Contatto creato"), "contact": new_doc.as_dict()}


def ensure_contact_from_message(
	reference_doctype: Optional[str] = None,
	reference_name: Optional[str] = None,
	message_name: Optional[str] = None,
) -> dict:
	"""Ensure a Contact exists for an incoming message source.

	- Phone is inferred from WhatsApp Message when possible; never taken from the end user via AI.
	- If a matching Contact exists (by exact mobile digits or Contact Phone child), it is returned.
	- Otherwise, a new Contact is created with the inferred phone set as primary.
	
	Args:
		reference_doctype: Optional doctype linked to the message (e.g., "CRM Deal").
		reference_name: Optional name linked to the message.
		message_name: Optional WhatsApp Message name to derive phone from.
		full_name: Optional contact display name to use on creation.
		email: Optional email to set on creation.
	"""
	try:
		# Resolve phone number source (internal only; never from user input)
		phone_raw: Optional[str] = None
		if (message_name or "").strip():
			try:
				msg = frappe.get_doc("WhatsApp Message", message_name)
				phone_raw = str(msg.get("from") or "").strip()
			except Exception:
				phone_raw = None
		if not phone_raw:
			phone_raw = _infer_phone_from_reference(
				ref_dt=str(reference_doctype or ""),
				ref_dn=str(reference_name or ""),
			)

		# Normalize to digits-only for matching/idempotency
		digits = re.sub(r"\D+", "", phone_raw or "")
		if not digits:
			frappe.response["http_status_code"] = 400
			return {"success": False, "error": _("Impossibile determinare il numero di telefono dal messaggio")}

		# Ensure or create
		return _ensure_contact_for_digits(digits)

	except Exception as e:
		frappe.log_error(message=frappe.get_traceback(), title="workflow.ensure_contact_from_message")
		frappe.response["http_status_code"] = 500
		return {"success": False, "error": _(str(e))}


def on_whatsapp_after_insert_ensure_contact(doc, method=None):
	"""DocEvent hook: ensure contact exists for every incoming WhatsApp message.

	Internal-only; not whitelisted. Uses message's `from` to derive digits.
	"""
	try:
		if (getattr(doc, "type", "") or "").lower() != "incoming":
			return
		phone_raw = str(doc.get("from") or "").strip()
		digits = re.sub(r"\D+", "", phone_raw or "")
		if not digits:
			return
		_ensure_contact_for_digits(digits)
	except Exception:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="workflow.on_whatsapp_after_insert_ensure_contact",
		)