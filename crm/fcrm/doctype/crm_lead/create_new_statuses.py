# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# Script per creare i nuovi stati "Attesa Pagamento", "Confermato" e "Non Pagato"

import frappe


def execute():
	"""Crea i nuovi stati per CRM Lead Status se non esistono già."""
	
	# Trova la posizione massima esistente
	max_position = frappe.db.sql("""
		SELECT MAX(position) as max_pos
		FROM `tabCRM Lead Status`
	""", as_dict=True)
	
	next_position = (max_position[0].get("max_pos") or 0) + 1
	
	# Stati da creare
	new_statuses = [
		{
			"lead_status": "Attesa Pagamento",
			"color": "orange",
			"position": next_position,
		},
		{
			"lead_status": "Confermato",
			"color": "green",
			"position": next_position + 1,
		},
		{
			"lead_status": "Non Pagato",
			"color": "red",
			"position": next_position + 2,
		},
	]
	
	for status_data in new_statuses:
		status_name = status_data["lead_status"]
		
		# Verifica se esiste già
		if frappe.db.exists("CRM Lead Status", status_name):
			frappe.logger("crm").info(f"Status '{status_name}' già esistente, skip")
			continue
		
		# Crea il nuovo stato
		try:
			doc = frappe.new_doc("CRM Lead Status")
			doc.lead_status = status_name
			doc.color = status_data["color"]
			doc.position = status_data["position"]
			doc.insert(ignore_permissions=True)
			
			frappe.logger("crm").info(f"Creato nuovo status: {status_name}")
		except Exception as e:
			frappe.log_error(
				message=f"Errore nella creazione dello status {status_name}: {str(e)}",
				title="Create Lead Status Error",
			)
	
	frappe.db.commit()
	frappe.logger("crm").info("Script completato: nuovi stati creati")

