# Copyright (c) 2023, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from crm.fcrm.doctype.fcrm_settings.fcrm_settings import get_exchange_rate


class CRMOrganization(Document):
	def validate(self):
		self.update_exchange_rate()

	def update_exchange_rate(self):
		if self.has_value_changed("currency") or not self.exchange_rate:
			system_currency = frappe.db.get_single_value("FCRM Settings", "currency") or "USD"
			exchange_rate = 1
			if self.currency and self.currency != system_currency:
				exchange_rate = get_exchange_rate(self.currency, system_currency)

			self.db_set("exchange_rate", exchange_rate)

	@staticmethod
	def default_list_data():
		from frappe import _
		columns = [
			{
				"label": _("Organization"),
				"type": "Data",
				"key": "organization_name",
				"width": "16rem",
			},
			{
				"label": _("Name"),
				"type": "Data",
				"key": "name",
				"width": "14rem",
			},
			{
				"label": _("Address"),
				"type": "Data",
				"key": "address",
				"width": "16rem",
			},
			{
				"label": _("Website"),
				"type": "Data",
				"key": "website",
				"width": "14rem",
			},
		]
		rows = [
			"name",
			"organization_name",
			"organization_logo",
			"address",
			"website",
			"industry",
			"currency",
			"annual_revenue",
			"modified",
		]
		return {"columns": columns, "rows": rows}
