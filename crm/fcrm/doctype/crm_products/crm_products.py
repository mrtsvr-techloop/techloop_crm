# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CRMProducts(Document):
	def validate(self):
		self.calculate_amounts()

	def calculate_amounts(self):
		"""Calculate amount, discount_amount and net_amount"""
		if not self.qty or not self.rate:
			self.amount = 0
			self.discount_amount = 0
			self.net_amount = 0
			return

		# Calculate base amount
		self.amount = self.qty * self.rate

		# Calculate discount amount
		if self.discount_percentage:
			self.discount_amount = self.amount * (self.discount_percentage / 100)
		else:
			self.discount_amount = 0

		# Calculate net amount (after discount)
		self.net_amount = self.amount - self.discount_amount

	def on_update(self):
		"""Update parent document totals when child row is updated"""
		self.update_parent_totals()

	def update_parent_totals(self):
		"""Update totals in parent CRM Lead document"""
		if not self.parent:
			return

		try:
			parent_doc = frappe.get_doc("CRM Lead", self.parent)
			
			# Calculate totals from all products
			total_amount = 0
			total_net_amount = 0
			
			for product in parent_doc.products:
				total_amount += product.amount or 0
				total_net_amount += product.net_amount or 0
			
			# Update parent totals
			parent_doc.total = total_amount
			parent_doc.net_total = total_net_amount
			parent_doc.save(ignore_permissions=True)
			
		except Exception as e:
			frappe.log_error(f"Error updating parent totals: {str(e)}", "CRM Products Update Error")