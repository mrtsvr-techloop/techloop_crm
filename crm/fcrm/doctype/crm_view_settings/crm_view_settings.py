# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
import json

import frappe
from frappe import _
from frappe.model.document import Document, get_controller
from frappe.utils import parse_json


class CRMViewSettings(Document):
	pass


@frappe.whitelist()
def create(view):
	view = frappe._dict(view)

	view.filters = parse_json(view.filters) or {}
	view.columns = parse_json(view.columns or "[]")
	view.rows = parse_json(view.rows or "[]")
	view.kanban_columns = parse_json(view.kanban_columns or "[]")
	view.kanban_fields = parse_json(view.kanban_fields or "[]")

	default_rows = sync_default_rows(view.doctype)
	view.rows = view.rows + default_rows if default_rows else view.rows
	view.rows = remove_duplicates(view.rows)

	if not view.kanban_columns and view.type == "kanban":
		view.kanban_columns = sync_default_columns(view)
	elif not view.columns:
		view.columns = sync_default_columns(view)

	doc = frappe.new_doc("CRM View Settings")
	doc.name = view.label
	doc.label = view.label
	doc.type = view.type or "list"
	doc.icon = view.icon
	doc.dt = view.doctype
	doc.user = frappe.session.user
	doc.route_name = view.route_name or get_route_name(view.doctype)
	doc.load_default_columns = view.load_default_columns or False
	doc.filters = json.dumps(view.filters)
	doc.order_by = view.order_by
	doc.group_by_field = view.group_by_field
	doc.column_field = view.column_field
	doc.title_field = view.title_field
	doc.kanban_columns = json.dumps(view.kanban_columns)
	doc.kanban_fields = json.dumps(view.kanban_fields)
	doc.columns = json.dumps(view.columns)
	doc.rows = json.dumps(view.rows)
	doc.insert()
	return doc


@frappe.whitelist()
def update(view):
	view = frappe._dict(view)

	filters = parse_json(view.filters or {})
	columns = parse_json(view.columns or [])
	rows = parse_json(view.rows or [])
	kanban_columns = parse_json(view.kanban_columns or [])
	kanban_fields = parse_json(view.kanban_fields or [])

	default_rows = sync_default_rows(view.doctype)
	rows = rows + default_rows if default_rows else rows
	rows = remove_duplicates(rows)

	doc = frappe.get_doc("CRM View Settings", view.name)
	doc.label = view.label
	doc.type = view.type or "list"
	doc.icon = view.icon
	doc.route_name = view.route_name or get_route_name(view.doctype)
	doc.load_default_columns = view.load_default_columns or False
	doc.filters = json.dumps(filters)
	doc.order_by = view.order_by
	doc.group_by_field = view.group_by_field
	doc.column_field = view.column_field
	doc.title_field = view.title_field
	doc.kanban_columns = json.dumps(kanban_columns)
	doc.kanban_fields = json.dumps(kanban_fields)
	doc.columns = json.dumps(columns)
	doc.rows = json.dumps(rows)
	doc.save()
	return doc


@frappe.whitelist()
def delete(name):
	if frappe.db.exists("CRM View Settings", name):
		frappe.delete_doc("CRM View Settings", name)


@frappe.whitelist()
def public(name, value):
	if frappe.session.user != "Administrator" and "Sales Manager" not in frappe.get_roles():
		frappe.throw("Not permitted", frappe.PermissionError)

	doc = frappe.get_doc("CRM View Settings", name)
	if doc.pinned:
		doc.pinned = False
	doc.public = value
	doc.user = "" if value else frappe.session.user
	doc.save()


@frappe.whitelist()
def pin(name, value):
	doc = frappe.get_doc("CRM View Settings", name)
	doc.pinned = value
	doc.save()


def remove_duplicates(l):
	return list(dict.fromkeys(l))


def sync_default_rows(doctype, type="list"):
	list = get_controller(doctype)
	rows = []

	if hasattr(list, "default_list_data"):
		rows = list.default_list_data().get("rows")

	return rows


def sync_default_columns(view):
	list = get_controller(view.doctype)
	columns = []

	if view.type == "kanban" and view.column_field:
		field_meta = frappe.get_meta(view.doctype).get_field(view.column_field)
		if field_meta.fieldtype == "Link":
			# For CRM Lead Status and CRM Deal Status, include color and position
			if field_meta.options in ["CRM Lead Status", "CRM Deal Status"]:
				fields_to_get = ["name", "color", "position"]
				if field_meta.options == "CRM Deal Status":
					fields_to_get.append("type")
				
				statuses = frappe.get_all(
					field_meta.options,
					fields=fields_to_get,
					order_by="position asc",
				)
				
				# Ensure red color is only used for Lost statuses (Deal) or similar negative statuses
				for status in statuses:
					# If it's a Deal Status and type is Lost, ensure color is red
					if field_meta.options == "CRM Deal Status" and status.get("type") == "Lost":
						if not status.get("color") or status.get("color") not in ["red"]:
							status["color"] = "red"
					# If it's a positive status with red color, change it to gray
					elif status.get("color") == "red":
						if field_meta.options == "CRM Deal Status" and status.get("type") not in ["Lost"]:
							status["color"] = "gray"
						elif field_meta.options == "CRM Lead Status":
							# For Lead Status, we don't have a type field, so we'll keep red only if explicitly set
							# But we'll default to gray for safety
							status["color"] = status.get("color") or "gray"
				
				columns = statuses
			else:
				columns = frappe.get_all(
					field_meta.options,
					fields=["name"],
					order_by="modified asc",
				)
		elif field_meta.fieldtype == "Select":
			columns = [{"name": option} for option in field_meta.options.split("\n")]
	elif hasattr(list, "default_list_data"):
		columns = list.default_list_data().get("columns")

	return columns


@frappe.whitelist()
def set_as_default(name=None, type=None, doctype=None):
	if name:
		frappe.db.set_value("CRM View Settings", name, "is_default", 1)
	else:
		doc = create_or_update_standard_view({"type": type, "doctype": doctype, "is_default": 1})
		name = doc.name

	# remove default from other views of same user
	frappe.db.set_value(
		"CRM View Settings",
		{"name": ("!=", name), "user": frappe.session.user, "is_default": 1},
		"is_default",
		0,
	)


@frappe.whitelist()
def create_or_update_standard_view(view):
	view = frappe._dict(view)

	filters = parse_json(view.filters) or {}
	# Check if columns/rows were explicitly passed (even if empty)
	columns_explicitly_passed = "columns" in view
	rows_explicitly_passed = "rows" in view
	kanban_columns_explicitly_passed = "kanban_columns" in view
	kanban_columns_force_reset = view.kanban_columns == ""  # Force reset if empty string
	
	columns = parse_json(view.columns or "[]")
	rows = parse_json(view.rows or "[]")
	kanban_columns = parse_json(view.kanban_columns or "[]")
	kanban_fields = parse_json(view.kanban_fields or "[]")
	view.column_field = view.column_field or "status"

	doc = frappe.db.exists(
		"CRM View Settings",
		{"dt": view.doctype, "type": view.type or "list", "is_standard": True, "user": frappe.session.user},
	)
	
	existing_doc = None
	# Preserve existing columns/rows only if they weren't explicitly passed (even if empty)
	if doc:
		existing_doc = frappe.get_doc("CRM View Settings", doc)
		existing_columns = parse_json(existing_doc.columns or "[]")
		existing_rows = parse_json(existing_doc.rows or "[]")
		existing_kanban_columns = parse_json(existing_doc.kanban_columns or "[]")
		
		# If columns/rows weren't explicitly passed, preserve existing ones
		# This prevents reset during install/updates unless explicitly requested
		if not columns_explicitly_passed and existing_columns:
			columns = existing_columns
		if not rows_explicitly_passed and existing_rows:
			rows = existing_rows
		# For kanban_columns, if explicitly passed as empty string, force sync from database
		if kanban_columns_force_reset:
			kanban_columns = []  # Force sync from database
		elif not kanban_columns and existing_kanban_columns:
			kanban_columns = existing_kanban_columns

	default_rows = sync_default_rows(view.doctype, view.type)
	rows = rows + default_rows if default_rows else rows
	rows = remove_duplicates(rows)

	# Always sync default columns if creating new view or if columns are empty
	# This ensures new users get the full default view, not just name and modified
	if not doc:  # Creating new view - always use defaults
		if view.type == "kanban":
			kanban_columns = sync_default_columns(view)
		else:
			columns = sync_default_columns(view)
	elif not kanban_columns and view.type == "kanban":
		kanban_columns = sync_default_columns(view)
	elif not columns:
		columns = sync_default_columns(view)

	if doc:
		doc = existing_doc
		doc.label = view.label
		doc.type = view.type or "list"
		doc.route_name = view.route_name or get_route_name(view.doctype)
		doc.load_default_columns = view.load_default_columns or False
		doc.filters = json.dumps(filters)
		doc.order_by = view.order_by or "modified desc"
		doc.group_by_field = view.group_by_field or "owner"
		doc.column_field = view.column_field
		doc.title_field = view.title_field
		doc.kanban_columns = json.dumps(kanban_columns)
		doc.kanban_fields = json.dumps(kanban_fields)
		doc.columns = json.dumps(columns)
		doc.rows = json.dumps(rows)
		doc.is_default = view.is_default or False
		doc.save()
	else:
		doc = frappe.new_doc("CRM View Settings")

		label = "List"
		if view.type == "group_by":
			label = "Group By"
		elif view.type == "kanban":
			label = "Kanban"

		doc.name = view.label or label
		doc.label = view.label or label
		doc.type = view.type or "list"
		doc.dt = view.doctype
		doc.user = frappe.session.user
		doc.route_name = view.route_name or get_route_name(view.doctype)
		doc.load_default_columns = view.load_default_columns or False
		doc.filters = json.dumps(filters)
		doc.order_by = view.order_by or "modified desc"
		doc.group_by_field = view.group_by_field or "owner"
		doc.column_field = view.column_field
		doc.title_field = view.title_field
		doc.kanban_columns = json.dumps(kanban_columns)
		doc.kanban_fields = json.dumps(kanban_fields)
		doc.columns = json.dumps(columns)
		doc.rows = json.dumps(rows)
		doc.is_standard = True
		doc.is_default = view.is_default or False
		doc.insert()

	return doc


def get_route_name(doctype):
	# Example: "CRM Lead" -> "Leads"
	if doctype.startswith("CRM "):
		doctype = doctype[4:]

	if doctype[-1] != "s":
		doctype += "s"

	return doctype


def reset_default_views():
	"""
	Resetta tutte le viste default (List e Kanban) per CRM Lead, CRM Deal e Contact.
	
	Questa funzione forza la sincronizzazione delle colonne dai default definiti nel codice,
	inclusi:
	- Colonne lista per CRM Lead, CRM Deal e Contact
	- Colonne kanban per CRM Lead e CRM Deal (con stati sincronizzati dal database)
	
	IMPORTANTE: Verifica che gli status richiesti esistano prima di resettare le viste.
	Se gli status "Attesa Pagamento", "Confermato" o "Non Pagato" non esistono per CRM Lead,
	viene mostrato un messaggio di errore.
	
	NOTA: Questa funzione NON è esposta come API. Può essere eseguita solo tramite:
	- bench --site <site> execute crm.fcrm.doctype.crm_view_settings.crm_view_settings.reset_default_views
	
	Returns:
		dict: Risultato dell'operazione con statistiche
	"""
	
	try:
		# Verifica che gli status nuovi esistano per CRM Lead (nomi in inglese)
		required_lead_statuses = ["Awaiting Payment", "Confirmed", "Not Paid"]
		missing_statuses = []
		
		for status_name in required_lead_statuses:
			if not frappe.db.exists("CRM Lead Status", status_name):
				missing_statuses.append(status_name)
		
		if missing_statuses:
			error_message = _(
				"Errore nel reset viste: gli status seguenti non sono presenti nel sistema: {0}. "
				"Esegui lo script 'crm.fcrm.doctype.crm_lead.create_new_statuses.execute' per crearli."
			).format(", ".join(missing_statuses))
			
			frappe.log_error(
				message=error_message,
				title="Reset Default Views - Status Mancanti",
			)
			
			return {
				"success": False,
				"error": error_message,
				"missing_statuses": missing_statuses,
			}
		
		reset_stats = {
			"leads": {"list": False, "kanban": False},
			"deals": {"list": False, "kanban": False},
			"contacts": {"list": False},
		}
		
		# Reset viste per CRM Lead
		try:
			# Reset vista lista
			create_or_update_standard_view({
				"doctype": "CRM Lead",
				"type": "list",
				"columns": "",  # Stringa vuota forza sincronizzazione default
				"rows": "",  # Stringa vuota forza sincronizzazione default
				"is_default": True,
			})
			reset_stats["leads"]["list"] = True
			
			# Reset vista kanban
			create_or_update_standard_view({
				"doctype": "CRM Lead",
				"type": "kanban",
				"column_field": "status",
				"title_field": "lead_name",
				"kanban_columns": "",  # Stringa vuota forza sincronizzazione default (con stati dal DB)
				"kanban_fields": '["lead_name", "mobile_no", "delivery_date", "delivery_region", "delivery_address", "net_total"]',
				"is_default": True,
			})
			reset_stats["leads"]["kanban"] = True
		except Exception as e:
			frappe.log_error(f"Errore resettando viste CRM Lead: {str(e)}")
		
		# Reset viste per CRM Deal
		try:
			# Reset vista lista
			create_or_update_standard_view({
				"doctype": "CRM Deal",
				"type": "list",
				"columns": "",  # Stringa vuota forza sincronizzazione default
				"rows": "",  # Stringa vuota forza sincronizzazione default
				"is_default": True,
			})
			reset_stats["deals"]["list"] = True
			
			# Reset vista kanban
			create_or_update_standard_view({
				"doctype": "CRM Deal",
				"type": "kanban",
				"column_field": "status",
				"title_field": "lead_name",
				"kanban_columns": "",  # Stringa vuota forza sincronizzazione default (con stati dal DB)
				"kanban_fields": '["lead_name", "mobile_no", "delivery_date", "delivery_region", "delivery_address", "net_total"]',
				"is_default": True,
			})
			reset_stats["deals"]["kanban"] = True
		except Exception as e:
			frappe.log_error(f"Errore resettando viste CRM Deal: {str(e)}")
		
		# Reset vista per Contact
		try:
			# Reset vista lista
			create_or_update_standard_view({
				"doctype": "Contact",
				"type": "list",
				"columns": "",  # Stringa vuota forza sincronizzazione default
				"rows": "",  # Stringa vuota forza sincronizzazione default
				"is_default": True,
			})
			reset_stats["contacts"]["list"] = True
		except Exception as e:
			frappe.log_error(f"Errore resettando vista Contact: {str(e)}")
		
		frappe.db.commit()
		
		total_reset = sum([
			reset_stats["leads"]["list"],
			reset_stats["leads"]["kanban"],
			reset_stats["deals"]["list"],
			reset_stats["deals"]["kanban"],
			reset_stats["contacts"]["list"],
		])
		
		return {
			"success": True,
			"message": _("Viste default resettate con successo! Reset {0} viste.").format(total_reset),
			"reset": reset_stats,
			"summary": reset_stats
		}
		
	except Exception as e:
		frappe.log_error(f"Errore generale durante reset viste: {str(e)}")
		frappe.db.rollback()
		return {
			"success": False,
			"error": _("Errore generale: {0}").format(str(e))
		}
