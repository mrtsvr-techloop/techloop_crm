# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# Script per rimuovere gli stati italiani e sostituirli con quelli inglesi

import frappe
from frappe import _


def execute():
	"""
	Rimuove gli stati italiani dal database e aggiorna tutti i Lead che li usano.
	"""
	# Mappa stati italiani -> inglesi
	italian_to_english = {
		"Attesa Pagamento": "Awaiting Payment",
		"Confermato": "Confirmed",
		"Non Pagato": "Not Paid",
	}
	
	removed_count = 0
	updated_leads = 0
	
	for italian_status, english_status in italian_to_english.items():
		# Verifica che lo stato italiano esista
		if not frappe.db.exists("CRM Lead Status", italian_status):
			continue
		
		# Verifica che lo stato inglese esista
		if not frappe.db.exists("CRM Lead Status", english_status):
			frappe.log_error(
				message=f"Stato inglese '{english_status}' non esiste! Deve essere creato prima di rimuovere '{italian_status}'",
				title="Remove Italian Statuses Error"
			)
			continue
		
		# Conta quanti Lead usano questo stato italiano
		leads_count = frappe.db.count("CRM Lead", {"status": italian_status})
		
		if leads_count > 0:
			# Aggiorna tutti i Lead che usano lo stato italiano
			frappe.db.sql(
				"""
				UPDATE `tabCRM Lead`
				SET status = %s
				WHERE status = %s
				""",
				(english_status, italian_status)
			)
			updated_leads += leads_count
			frappe.log_error(
				message=f"Aggiornati {leads_count} Lead da '{italian_status}' a '{english_status}'",
				title="Remove Italian Statuses"
			)
		
		# Rimuovi lo stato italiano
		try:
			frappe.delete_doc("CRM Lead Status", italian_status, force=1, ignore_permissions=True)
			removed_count += 1
			frappe.log_error(
				message=f"Rimosso stato italiano: {italian_status}",
				title="Remove Italian Statuses"
			)
		except Exception as e:
			frappe.log_error(
				message=f"Errore nella rimozione dello stato '{italian_status}': {str(e)}",
				title="Remove Italian Statuses Error"
			)
	
	frappe.db.commit()
	
	frappe.log_error(
		message=f"Script completato: rimossi {removed_count} stati italiani, aggiornati {updated_leads} Lead",
		title="Remove Italian Statuses"
	)
	
	return {
		"removed_statuses": removed_count,
		"updated_leads": updated_leads
	}

