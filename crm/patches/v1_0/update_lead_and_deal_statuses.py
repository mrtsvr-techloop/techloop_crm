import frappe
from crm.install import add_default_lead_statuses, add_default_deal_statuses


def execute():
	# Map Italian status names to English status names
	lead_status_map = {
		"Nuovo": "New",
		"Contattato": "Contacted",
		"Contrattazione": "Negotiation",
		"Rischedulazione": "Rescheduled",
		"Rifiutato": "Rejected",
	}
	
	deal_status_map = {
		"Nuovo": "New",
		"Negoziazione": "Negotiation",
		"Rischedulazione": "Rescheduled",
		"Preparazione": "Preparation",
		"Completato": "Completed",
		"Perso": "Lost",
	}
	
	# First, create all English statuses if they don't exist
	add_default_lead_statuses()
	add_default_deal_statuses()
	
	# Rename Italian lead statuses to English by updating references
	for italian_name, english_name in lead_status_map.items():
		if frappe.db.exists("CRM Lead Status", italian_name):
			# Update all leads that reference this status first
			frappe.db.sql(
				"""
				UPDATE `tabCRM Lead`
				SET status = %s
				WHERE status = %s
				""",
				(english_name, italian_name)
			)
			# Delete the Italian status
			frappe.delete_doc("CRM Lead Status", italian_name, force=1)
	
	# Rename Italian deal statuses to English by updating references
	for italian_name, english_name in deal_status_map.items():
		if frappe.db.exists("CRM Deal Status", italian_name):
			# Update all deals that reference this status first
			frappe.db.sql(
				"""
				UPDATE `tabCRM Deal`
				SET status = %s
				WHERE status = %s
				""",
				(english_name, italian_name)
			)
			# Delete the Italian status
			frappe.delete_doc("CRM Deal Status", italian_name, force=1)
	
	# Delete other old statuses that are not in the new list
	old_lead_statuses_to_delete = ["Nurture", "Qualified", "Unqualified", "Junk"]
	old_deal_statuses_to_delete = ["Qualification", "Demo/Making", "Proposal/Quotation", "Ready to Close", "Won"]
	
	for status in old_lead_statuses_to_delete:
		if frappe.db.exists("CRM Lead Status", status):
			frappe.db.sql("UPDATE `tabCRM Lead` SET status = 'New' WHERE status = %s", (status,))
			frappe.delete_doc("CRM Lead Status", status, force=1)
	
	for status in old_deal_statuses_to_delete:
		if frappe.db.exists("CRM Deal Status", status):
			frappe.db.sql("UPDATE `tabCRM Deal` SET status = 'New' WHERE status = %s", (status,))
			frappe.delete_doc("CRM Deal Status", status, force=1)
	
	# Update any remaining leads/deals with invalid statuses to 'New'
	frappe.db.sql(
		"""
		UPDATE `tabCRM Lead`
		SET status = 'New'
		WHERE status NOT IN ('New', 'Contacted', 'Negotiation', 'Rescheduled', 'Rejected')
	"""
	)
	
	frappe.db.sql(
		"""
		UPDATE `tabCRM Deal`
		SET status = 'New'
		WHERE status NOT IN ('New', 'Negotiation', 'Rescheduled', 'Preparation', 'Completed', 'Lost')
	"""
	)
	
	frappe.db.commit()

