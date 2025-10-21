# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMProduct(Document):
	def validate(self):
		self.validate_duplicate_product_code()
		self.set_product_name()

	def validate_duplicate_product_code(self):
		if not self.product_code:
			return
			
		existing = frappe.db.exists("CRM Product", {
			"product_code": self.product_code,
			"name": ["!=", self.name or ""]
		})
		
		if existing:
			frappe.throw(f"Product with code '{self.product_code}' already exists")

	def set_product_name(self):
		if not self.product_name:
			self.product_name = self.product_code
		else:
			self.product_name = self.product_name.strip()

@frappe.whitelist()
def get_products_for_selection():
	"""Get all CRM Products for selection in frontend"""
	products = frappe.get_all("CRM Product", 
		fields=["name", "product_name", "product_code", "standard_rate"],
		filters={"disabled": 0},
		order_by="product_name"
	)
	return products
