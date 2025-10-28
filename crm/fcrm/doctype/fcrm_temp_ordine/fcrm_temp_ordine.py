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
	"""
	Cleanup FCRM TEMP ORDINE records:
	1. Mark expired Active records as Expired
	2. Delete old Expired records (older than 1 hour)
	3. Delete old Consumed records (older than 24 hours)
	"""
	try:
		current_time = int(time.time())
		
		# Step 1: Mark expired Active records as Expired
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
		
		if expired_records:
			frappe.logger("crm").info(f"Marked {len(expired_records)} FCRM TEMP ORDINE records as expired")
		
		# Step 2: Delete old Expired records (expired more than 1 hour ago)
		one_hour_ago = current_time - 3600  # 1 hour = 3600 seconds
		old_expired_records = frappe.get_all(
			"FCRM TEMP ORDINE",
			filters={
				"expires_at": ["<", one_hour_ago],
				"status": "Expired"
			},
			fields=["name"]
		)
		
		for record in old_expired_records:
			frappe.delete_doc("FCRM TEMP ORDINE", record.name, force=True)
		
		if old_expired_records:
			frappe.logger("crm").info(f"Deleted {len(old_expired_records)} old expired FCRM TEMP ORDINE records")
		
		# Step 3: Delete old Consumed records (consumed more than 24 hours ago)
		# Use modified timestamp as proxy for when it was consumed
		twenty_four_hours_ago = frappe.utils.add_to_date(frappe.utils.now(), hours=-24)
		old_consumed_records = frappe.get_all(
			"FCRM TEMP ORDINE",
			filters={
				"status": "Consumed",
				"modified": ["<", twenty_four_hours_ago]
			},
			fields=["name"]
		)
		
		for record in old_consumed_records:
			frappe.delete_doc("FCRM TEMP ORDINE", record.name, force=True)
		
		if old_consumed_records:
			frappe.logger("crm").info(f"Deleted {len(old_consumed_records)} old consumed FCRM TEMP ORDINE records")
		
		frappe.db.commit()
			
	except Exception as e:
		frappe.logger("crm").error(f"Error cleaning up FCRM TEMP ORDINE: {str(e)}")
		frappe.db.rollback()


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
	"""Mark FCRM TEMP ORDINE as consumed and update timestamp."""
	try:
		# Update status and modified timestamp
		doc = frappe.get_doc("FCRM TEMP ORDINE", temp_order_id)
		doc.status = "Consumed"
		doc.save(ignore_permissions=True)
		frappe.db.commit()
		return True
	except Exception as e:
		frappe.logger("crm").error(f"Error consuming FCRM TEMP ORDINE: {str(e)}")
		return False


def force_cleanup_temp_orders():
	"""
	Force cleanup of all old FCRM TEMP ORDINE records immediately.
	Can be called manually from console: 
	bench --site site.localhost execute crm.fcrm.doctype.fcrm_temp_ordine.fcrm_temp_ordine.force_cleanup_temp_orders
	"""
	frappe.logger("crm").info("Starting forced cleanup of FCRM TEMP ORDINE records...")
	cleanup_expired_temp_orders()
	frappe.logger("crm").info("Forced cleanup completed")
