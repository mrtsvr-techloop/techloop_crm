# Copyright (c) 2025, Techloop and Contributors
# License: MIT License

import frappe
from frappe import _
import time
import json


def cleanup_expired_temp_orders():
	"""Cleanup expired Temp Ordine records."""
	try:
		current_time = int(time.time())
		expired_records = frappe.get_all(
			"Temp_Ordine",
			filters={
				"expires_at": ["<", current_time],
				"status": "Active"
			},
			fields=["name"]
		)
		
		for record in expired_records:
			frappe.db.set_value("Temp_Ordine", record.name, "status", "Expired")
		
		frappe.db.commit()
		
		if expired_records:
			frappe.logger("crm").info(f"Marked {len(expired_records)} Temp Ordine records as expired")
			
	except Exception as e:
		frappe.logger("crm").error(f"Error cleaning up expired Temp Ordine: {str(e)}")


def get_temp_order_data(temp_order_id):
	"""Get Temp Ordine data by ID."""
	try:
		# Check if record exists and is not expired
		current_time = int(time.time())
		record = frappe.get_doc("Temp_Ordine", temp_order_id)
		
		if record.status != "Active":
			return None, "Order already processed or expired"
		
		if record.expires_at < current_time:
			# Mark as expired
			frappe.db.set_value("Temp_Ordine", temp_order_id, "status", "Expired")
			frappe.db.commit()
			return None, "Order link has expired"
		
		# Parse JSON data
		order_data = json.loads(record.order_data) if isinstance(record.order_data, str) else record.order_data
		return order_data, None
		
	except frappe.DoesNotExistError:
		return None, "Order not found"
	except Exception as e:
		frappe.logger("crm").error(f"Error getting Temp Ordine data: {str(e)}")
		return None, "Error retrieving order data"


def consume_temp_order(temp_order_id):
	"""Mark Temp Ordine as consumed."""
	try:
		frappe.db.set_value("Temp_Ordine", temp_order_id, "status", "Consumed")
		frappe.db.commit()
		return True
	except Exception as e:
		frappe.logger("crm").error(f"Error consuming Temp Ordine: {str(e)}")
		return False