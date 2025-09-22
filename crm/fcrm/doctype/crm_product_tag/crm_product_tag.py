# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMProductTag(Document):
	def validate(self):
		self.validate_tag_name()

	def validate_tag_name(self):
		if self.tag_name:
			self.tag_name = self.tag_name.strip().lower()
			
			# Check for duplicates
			existing = frappe.db.exists("CRM Product Tag", {"tag_name": self.tag_name, "name": ["!=", self.name]})
			if existing:
				frappe.throw(f"Tag '{self.tag_name}' already exists")
