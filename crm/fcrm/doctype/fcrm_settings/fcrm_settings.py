# Copyright (c) 2024, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
import requests
import re
from frappe import _
from frappe.custom.doctype.property_setter.property_setter import delete_property_setter, make_property_setter
from frappe.model.document import Document

from crm.install import after_install, add_default_lead_statuses


class FCRMSettings(Document):
	@frappe.whitelist()
	def restore_defaults(self, force=False):
		after_install(force)

	def validate(self):
		self.do_not_allow_to_delete_if_standard()
		self.setup_forecasting()
		self.make_currency_read_only()

	def do_not_allow_to_delete_if_standard(self):
		if not self.has_value_changed("dropdown_items"):
			return
		old_items = self.get_doc_before_save().get("dropdown_items")
		standard_new_items = [d.name1 for d in self.dropdown_items if d.is_standard]
		standard_old_items = [d.name1 for d in old_items if d.is_standard]
		deleted_standard_items = set(standard_old_items) - set(standard_new_items)
		if deleted_standard_items:
			standard_dropdown_items = get_standard_dropdown_items()
			if not deleted_standard_items.intersection(standard_dropdown_items):
				return
			frappe.throw(_("Cannot delete standard items {0}").format(", ".join(deleted_standard_items)))

	def setup_forecasting(self):
		if self.has_value_changed("enable_forecasting"):
			if not self.enable_forecasting:
				delete_property_setter(
					"CRM Deal",
					"reqd",
					"expected_closure_date",
				)
				delete_property_setter(
					"CRM Deal",
					"reqd",
					"expected_deal_value",
				)
			else:
				make_property_setter(
					"CRM Deal",
					"expected_closure_date",
					"reqd",
					1 if self.enable_forecasting else 0,
					"Check",
				)
				make_property_setter(
					"CRM Deal",
					"expected_deal_value",
					"reqd",
					1 if self.enable_forecasting else 0,
					"Check",
				)

	def make_currency_read_only(self):
		if self.currency and self.has_value_changed("currency"):
			make_property_setter(
				"FCRM Settings",
				"currency",
				"read_only",
				1,
				"Check",
			)


def get_standard_dropdown_items():
	return [item.get("name1") for item in frappe.get_hooks("standard_dropdown_items")]


def after_migrate():
	sync_table("dropdown_items", "standard_dropdown_items")
	# Assicura che i nuovi stati Lead vengano creati anche dopo un aggiornamento
	add_default_lead_statuses()
	# Sincronizza i Custom Fields per le notifiche degli stati
	sync_status_notification_fields()


def sync_table(key, hook):
	crm_settings = FCRMSettings("FCRM Settings")
	existing_items = {d.name1: d for d in crm_settings.get(key)}
	new_standard_items = {}

	# add new items
	count = 0  # maintain count because list may come from seperate apps
	for item in frappe.get_hooks(hook):
		if item.get("name1") not in existing_items:
			crm_settings.append(key, item, count)
		new_standard_items[item.get("name1")] = True
		count += 1

	# remove unused items
	items = crm_settings.get(key)
	items = [item for item in items if not (item.is_standard and (item.name1 not in new_standard_items))]
	crm_settings.set(key, items)

	crm_settings.save()


def create_forecasting_script():
	if not frappe.db.exists("CRM Form Script", "Forecasting Script"):
		script = get_forecasting_script()
		frappe.get_doc(
			{
				"doctype": "CRM Form Script",
				"name": "Forecasting Script",
				"dt": "CRM Deal",
				"view": "Form",
				"script": script,
				"enabled": 1,
				"is_standard": 1,
			}
		).insert()


def get_forecasting_script():
	return """class CRMDeal {
    async status() {
        await this.doc.trigger('updateProbability')
    }
    async updateProbability() {
        let status = await call("frappe.client.get_value", {
            doctype: "CRM Deal Status",
            fieldname: "probability",
            filters: { name: this.doc.status },
        })

        this.doc.probability = status.probability
    }
}"""


def get_exchange_rate(from_currency, to_currency, date=None):
	if not date:
		date = "latest"

	api_used = "frankfurter"

	api_endpoint = f"https://api.frankfurter.app/{date}?from={from_currency}&to={to_currency}"
	res = requests.get(api_endpoint, timeout=5)
	if res.ok:
		data = res.json()
		return data["rates"][to_currency]

	# Fallback to exchangerate.host if Frankfurter API fails
	settings = FCRMSettings("FCRM Settings")
	if settings and settings.service_provider == "exchangerate.host":
		api_used = "exchangerate.host"
		if not settings.access_key:
			frappe.throw(
				_("Access Key is required for Service Provider: {0}").format(
					frappe.bold(settings.service_provider)
				)
			)

		params = {
			"access_key": settings.access_key,
			"from": from_currency,
			"to": to_currency,
			"amount": 1,
		}

		if date != "latest":
			params["date"] = date

		api_endpoint = "https://api.exchangerate.host/convert"

		res = requests.get(api_endpoint, params=params, timeout=5)
		if res.ok:
			data = res.json()
			return data["result"]

	frappe.log_error(
		title="Exchange Rate Fetch Error",
		message=f"Failed to fetch exchange rate from {from_currency} to {to_currency} using {api_used} API.",
	)

	if api_used == "frankfurter":
		user = frappe.session.user
		is_manager = (
			"System Manager" in frappe.get_roles(user)
			or "Sales Manager" in frappe.get_roles(user)
			or user == "Administrator"
		)

		if not is_manager:
			frappe.throw(
				_(
					"Ask your manager to set up the Exchange Rate Provider, as default provider does not support currency conversion for {0} to {1}."
				).format(from_currency, to_currency)
			)
		else:
			frappe.throw(
				_(
					"Setup the Exchange Rate Provider as 'Exchangerate Host' in settings, as default provider does not support currency conversion for {0} to {1}."
				).format(from_currency, to_currency)
			)

	frappe.throw(
		_(
			"Failed to fetch exchange rate from {0} to {1} on {2}. Please check your internet connection or try again later."
		).format(from_currency, to_currency, date)
	)


def _slugify_status_name(status_name: str) -> str:
	"""
	Converte il nome di uno stato in uno slug valido per i nomi dei campi.
	Es: "Awaiting Payment" -> "awaiting_payment"
	"""
	# Converti in lowercase e sostituisci spazi e caratteri speciali con underscore
	slug = status_name.lower()
	slug = re.sub(r'[^a-z0-9]+', '_', slug)
	slug = slug.strip('_')
	return slug


def sync_status_notification_fields():
	"""
	Sincronizza dinamicamente i Custom Fields per le notifiche di cambio stato.
	Crea un campo boolean (enable_notification_<status>) e un campo text (custom_message_<status>)
	per ogni stato Lead disponibile nel database.
	"""
	try:
		# Recupera tutti gli stati Lead dal database
		lead_statuses = frappe.get_all(
			"CRM Lead Status",
			fields=["name"],
			order_by="position asc"
		)
		
		if not lead_statuses:
			frappe.log_error(
				message="Nessuno stato Lead trovato durante la sincronizzazione dei Custom Fields",
				title="CRM Status Notification Fields Sync"
			)
			return
		
		# Lista degli stati attuali (per rimuovere quelli obsoleti)
		current_status_slugs = set()
		
		# Crea/aggiorna i Custom Fields per ogni stato
		for status in lead_statuses:
			status_name = status.name
			status_slug = _slugify_status_name(status_name)
			current_status_slugs.add(status_slug)
			
			# Nomi dei campi
			enable_fieldname = f"enable_notification_{status_slug}"
			message_fieldname = f"custom_message_{status_slug}"
			
			# Traduzione automatica del nome dello stato per le label
			status_label = _(status_name)
			
			# Crea/aggiorna il campo boolean per abilitare/disabilitare la notifica
			_create_or_update_custom_field(
				doctype="FCRM Settings",
				fieldname=enable_fieldname,
				fieldtype="Check",
				label=_("Enable notification for {0}").format(status_label),
				default=1,
				insert_after="status_notifications_section"
			)
			
			# Crea/aggiorna il campo text per il messaggio personalizzato
			_create_or_update_custom_field(
				doctype="FCRM Settings",
				fieldname=message_fieldname,
				fieldtype="Long Text",
				label=_("Custom message for {0}").format(status_label),
				depends_on=f"enable_notification_{status_slug}",
				insert_after=enable_fieldname
			)
		
		# Rimuovi i Custom Fields per stati che non esistono più
		_remove_obsolete_status_fields(current_status_slugs)
		
		# Ricarica il DocType per applicare le modifiche
		frappe.clear_cache(doctype="FCRM Settings")
		frappe.reload_doctype("FCRM Settings")
		
	except Exception as e:
		frappe.log_error(
			message=f"Errore durante la sincronizzazione dei Custom Fields per le notifiche stato: {str(e)}",
			title="CRM Status Notification Fields Sync Error"
		)


def _create_or_update_custom_field(doctype: str, fieldname: str, fieldtype: str, label: str, 
									default=None, depends_on=None, insert_after=None):
	"""
	Crea o aggiorna un Custom Field per un DocType.
	"""
	try:
		# Verifica se il campo esiste già
		custom_field_name = f"{doctype}-{fieldname}"
		
		if frappe.db.exists("Custom Field", custom_field_name):
			# Aggiorna il campo esistente
			custom_field = frappe.get_doc("Custom Field", custom_field_name)
			custom_field.label = label
			custom_field.fieldtype = fieldtype
			if default is not None:
				custom_field.default = default
			if depends_on:
				custom_field.depends_on = depends_on
			if insert_after:
				custom_field.insert_after = insert_after
			custom_field.save(ignore_permissions=True)
		else:
			# Crea un nuovo campo
			custom_field = frappe.get_doc({
				"doctype": "Custom Field",
				"dt": doctype,
				"fieldname": fieldname,
				"fieldtype": fieldtype,
				"label": label,
			})
			if default is not None:
				custom_field.default = default
			if depends_on:
				custom_field.depends_on = depends_on
			if insert_after:
				custom_field.insert_after = insert_after
			custom_field.insert(ignore_permissions=True)
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(
			message=f"Errore durante la creazione/aggiornamento del Custom Field {fieldname}: {str(e)}",
			title="CRM Custom Field Creation Error"
		)
		frappe.db.rollback()


def _remove_obsolete_status_fields(current_status_slugs: set):
	"""
	Rimuove i Custom Fields per stati che non esistono più.
	"""
	try:
		# Recupera tutti i Custom Fields di FCRM Settings che iniziano con enable_notification_ o custom_message_
		all_custom_fields = frappe.get_all(
			"Custom Field",
			filters={"dt": "FCRM Settings"},
			fields=["name", "fieldname"]
		)
		
		for custom_field in all_custom_fields:
			fieldname = custom_field.fieldname
			
			# Verifica se è un campo di notifica stato
			if fieldname.startswith("enable_notification_") or fieldname.startswith("custom_message_"):
				# Estrai lo slug dello stato dal nome del campo
				if fieldname.startswith("enable_notification_"):
					status_slug = fieldname.replace("enable_notification_", "")
				else:
					status_slug = fieldname.replace("custom_message_", "")
				
				# Se lo stato non esiste più, rimuovi il campo
				if status_slug not in current_status_slugs:
					try:
						frappe.delete_doc("Custom Field", custom_field.name, force=1, ignore_permissions=True)
						frappe.db.commit()
					except Exception as e:
						frappe.log_error(
							message=f"Errore durante la rimozione del Custom Field {fieldname}: {str(e)}",
							title="CRM Custom Field Removal Error"
						)
						frappe.db.rollback()
		
	except Exception as e:
		frappe.log_error(
			message=f"Errore durante la rimozione dei Custom Fields obsoleti: {str(e)}",
			title="CRM Custom Field Cleanup Error"
		)
