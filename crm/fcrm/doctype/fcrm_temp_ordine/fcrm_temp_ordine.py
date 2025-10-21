# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import time
import json
from frappe.model.document import Document


class FCRMTEMPORDINE(Document):
	pass


def cleanup_expired_temp_orders():
	"""Cleanup expired FCRM TEMP ORDINE records."""
	try:
		current_time = int(time.time())
		expired_records = frappe.get_all(
			"FCRM TEMP ORDINE",
			filters={
				"expires_at": ["<", current_time],
				"status": "Active"
			},
			fields=["name"]
		)
		
		for record in expired_records:
			frappe.db.set_value("FCRM TEMP ORDINE", record.name, "status", "Expired")
		
		frappe.db.commit()
		
		if expired_records:
			frappe.logger("crm").info(f"Marked {len(expired_records)} FCRM TEMP ORDINE records as expired")
			
	except Exception as e:
		frappe.logger("crm").error(f"Error cleaning up expired FCRM TEMP ORDINE: {str(e)}")


def get_temp_order_data(temp_order_id):
	"""Get FCRM TEMP ORDINE data by ID."""
	try:
		# Check if record exists and is not expired
		current_time = int(time.time())
		record = frappe.get_doc("FCRM TEMP ORDINE", temp_order_id)
		
		if record.status != "Active":
			return None, "Order already processed or expired"
		
		if record.expires_at < current_time:
			# Mark as expired
			frappe.db.set_value("FCRM TEMP ORDINE", temp_order_id, "status", "Expired")
			frappe.db.commit()
			return None, "Order link has expired"
		
		# Parse JSON data - il campo si chiama "content" nel doctype creato
		order_data = json.loads(record.content) if isinstance(record.content, str) else record.content
		return order_data, None
		
	except frappe.DoesNotExistError:
		return None, "Order not found"
	except Exception as e:
		frappe.logger("crm").error(f"Error getting FCRM TEMP ORDINE data: {str(e)}")
		return None, "Error retrieving order data"


def consume_temp_order(temp_order_id):
	"""Mark FCRM TEMP ORDINE as consumed."""
	try:
		frappe.db.set_value("FCRM TEMP ORDINE", temp_order_id, "status", "Consumed")
		frappe.db.commit()
		return True
	except Exception as e:
		frappe.logger("crm").error(f"Error consuming FCRM TEMP ORDINE: {str(e)}")
		return False
