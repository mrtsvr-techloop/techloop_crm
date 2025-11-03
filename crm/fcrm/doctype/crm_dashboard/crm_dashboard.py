# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class CRMDashboard(Document):
	pass


def default_manager_dashboard_layout():
	"""
	Returns the default layout for the CRM Manager Dashboard.
	"""
	import json
	layout = [
		{"name": "total_leads", "type": "number_chart", "tooltip": "Total number of leads", "layout": {"x": 0, "y": 0, "w": 4, "h": 3, "i": "total_leads"}},
		{"name": "total_deals", "type": "number_chart", "tooltip": "Total number of deals", "layout": {"x": 4, "y": 0, "w": 4, "h": 3, "i": "total_deals"}},
		{"name": "average_lead_value", "type": "number_chart", "tooltip": "Average lead value", "layout": {"x": 8, "y": 0, "w": 4, "h": 3, "i": "average_lead_value"}},
		{"name": "average_deal_value_new", "type": "number_chart", "tooltip": "Average deal value", "layout": {"x": 12, "y": 0, "w": 4, "h": 3, "i": "average_deal_value_new"}},
		{"name": "total_leads_by_status", "type": "donut_chart", "layout": {"x": 0, "y": 3, "w": 8, "h": 9, "i": "total_leads_by_status"}},
		{"name": "total_deals_by_status", "type": "donut_chart", "layout": {"x": 8, "y": 3, "w": 8, "h": 9, "i": "total_deals_by_status"}},
		{"name": "forecasted_revenue_new", "type": "axis_chart", "layout": {"x": 0, "y": 12, "w": 16, "h": 9, "i": "forecasted_revenue_new"}},
		{"name": "products_by_tag_donut", "type": "donut_chart", "layout": {"x": 0, "y": 21, "w": 8, "h": 9, "i": "products_by_tag_donut"}},
		{"name": "products_by_tag_bar", "type": "axis_chart", "layout": {"x": 8, "y": 21, "w": 8, "h": 9, "i": "products_by_tag_bar"}},
		{"name": "products_by_type_donut", "type": "donut_chart", "layout": {"x": 0, "y": 30, "w": 8, "h": 9, "i": "products_by_type_donut"}},
		{"name": "products_by_type_bar", "type": "axis_chart", "layout": {"x": 8, "y": 30, "w": 8, "h": 9, "i": "products_by_type_bar"}},
	]
	return json.dumps(layout)


def create_default_manager_dashboard(force=False):
	"""
	Creates the default CRM Manager Dashboard if it does not exist.
	"""
	if not frappe.db.exists("CRM Dashboard", "Manager Dashboard"):
		doc = frappe.new_doc("CRM Dashboard")
		doc.title = "Manager Dashboard"
		doc.layout = default_manager_dashboard_layout()
		doc.insert(ignore_permissions=True)
	else:
		doc = frappe.get_doc("CRM Dashboard", "Manager Dashboard")
		if force:
			doc.layout = default_manager_dashboard_layout()
			doc.save(ignore_permissions=True)
	return doc.layout
