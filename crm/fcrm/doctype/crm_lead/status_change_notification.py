# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Listener per cambio stato dei Lead che invia notifiche WhatsApp tramite AI.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, add_days
import json
from typing import Dict, Any, Optional


def on_lead_status_change(doc, method=None):
	"""
	Hook chiamato quando lo status di un Lead cambia.
	Invia una notifica WhatsApp tramite AI al contatto associato.
	"""
	try:
		# Verifica se ai_module è installato
		if not _is_ai_module_installed():
			frappe.logger("crm").info(
				f"ai_module non installato, skip notifica cambio stato per Lead {doc.name}"
			)
			return
		
		# Verifica se lo status è cambiato
		if not doc.has_value_changed("status"):
			return
		
		# Ottieni lo status precedente dal log
		old_status = _get_previous_status(doc)
		new_status = doc.status
		
		if not new_status:
			return
		
		# Se lo status è lo stesso, non fare nulla
		if old_status == new_status:
			return
		
		# Ottieni il numero di telefono del contatto
		phone = _get_contact_phone(doc)
		if not phone:
			frappe.logger("crm").info(
				f"Lead {doc.name}: Nessun numero di telefono trovato, skip notifica WhatsApp"
			)
			return
		
		# Prepara i dati per l'AI
		context_data = _prepare_status_change_context(doc, old_status, new_status)
		
		# Invia il messaggio tramite AI
		_send_status_change_notification(phone, context_data, doc.name)
		
	except Exception as e:
		# Logga l'errore ma non sopprimerlo
		frappe.log_error(
			message=f"Errore nell'invio notifica cambio stato per Lead {doc.name}: {frappe.get_traceback()}",
			title="CRM Lead Status Change Notification Error",
		)
		frappe.logger("crm").error(
			f"Errore nell'invio notifica cambio stato per Lead {doc.name}: {str(e)}"
		)
		# Rilancia l'eccezione per non nascondere il problema
		raise


def _is_ai_module_installed() -> bool:
	"""Verifica se ai_module è installato."""
	try:
		installed_apps = frappe.get_installed_apps()
		return "ai_module" in installed_apps
	except Exception as e:
		frappe.log_error(
			message=f"Errore nel controllo app installate: {frappe.get_traceback()}",
			title="CRM Check Installed Apps Error",
		)
		frappe.logger("crm").error(f"Errore nel controllo app installate: {str(e)}")
		return False


def _get_previous_status(doc) -> Optional[str]:
	"""Ottieni lo status precedente dal log dei cambi di stato."""
	try:
		if doc.status_change_log:
			# Prendi l'ultimo log entry
			last_log = doc.status_change_log[-1] if doc.status_change_log else None
			if last_log and hasattr(last_log, 'from_status'):
				return last_log.from_status
		
		# Fallback: cerca nel database
		logs = frappe.get_all(
			"CRM Status Change Log",
			filters={"reference_doctype": "CRM Lead", "reference_name": doc.name},
			fields=["from_status"],
			order_by="creation desc",
			limit=1
		)
		if logs:
			return logs[0].get("from_status")
		
		return None
	except Exception:
		return None


def _get_contact_phone(doc) -> Optional[str]:
	"""Ottieni il numero di telefono del contatto associato al Lead."""
	# Prova prima mobile_no, poi phone
	phone = doc.mobile_no or doc.phone
	if phone:
		# Normalizza il numero (rimuovi spazi, mantieni solo cifre)
		phone = "".join(c for c in phone if c.isdigit())
		if phone and not phone.startswith("+"):
			phone = "+" + phone
		return phone
	
	# Se non c'è telefono diretto, cerca nel contatto associato
	try:
		if doc.email:
			contact = frappe.db.get_value(
				"Contact Email",
				{"email_id": doc.email},
				"parent"
			)
			if contact:
				contact_doc = frappe.get_cached_doc("Contact", contact)
				phone = contact_doc.mobile_no or contact_doc.phone
				if phone:
					phone = "".join(c for c in phone if c.isdigit())
					if phone and not phone.startswith("+"):
						phone = "+" + phone
					return phone
	except Exception:
		pass
	
	return None


def _prepare_status_change_context(doc, old_status: str, new_status: str) -> Dict[str, Any]:
	"""
	Prepara i dati strutturati per l'AI in base al cambio di stato.
	"""
	context = {
		"lead_id": doc.name,
		"order_number": doc.name,  # Il nome del lead è il numero d'ordine (es. 25-XXX...)
		"old_status": old_status or "N/A",
		"new_status": new_status,
		"customer_name": doc.lead_name or doc.first_name or "Cliente",
		"has_order_details": False,
	}
	
	# Se lo stato è "Attesa Pagamento", aggiungi dettagli ordine
	if new_status == "Attesa Pagamento":
		context["has_order_details"] = True
		context["order_summary"] = _prepare_order_summary(doc)
		context["payment_info"] = _get_payment_info()
	
	return context


def _prepare_order_summary(doc) -> Dict[str, Any]:
	"""Prepara il riepilogo dell'ordine con prodotti, quantità e prezzi."""
	summary = {
		"products": [],
		"subtotal": float(doc.total or 0),
		"net_total": float(doc.net_total or 0),
		"currency": doc.currency or "EUR",
	}
	
	# Aggiungi i prodotti
	if doc.products:
		for product in doc.products:
			product_info = {
				"name": product.product_name or "Prodotto",
				"quantity": float(product.qty or 0),
				"unit_price": float(product.rate or 0),
				"total_price": float(product.amount or 0),
			}
			summary["products"].append(product_info)
	
	return summary


def _get_payment_info() -> Dict[str, Any]:
	"""
	Restituisce le informazioni di pagamento dalle impostazioni CRM.
	Legge il campo 'payment_info_text' da FCRM Settings.
	"""
	try:
		# Verifica se FCRM Settings esiste
		if not frappe.db.exists("DocType", "FCRM Settings"):
			frappe.logger("crm").warning(
				"FCRM Settings non trovato, uso informazioni di pagamento di default"
			)
			return _get_default_payment_info()
		
		# Leggi le impostazioni
		settings = frappe.get_cached_doc("FCRM Settings", "FCRM Settings")
		payment_text = getattr(settings, "payment_info_text", None)
		
		if payment_text and payment_text.strip():
			# Restituisci il testo così com'è - l'AI lo interpreterà
			return {
				"text": payment_text.strip(),
				"source": "settings",
			}
		else:
			# Se non c'è testo nelle impostazioni, usa quello di default
			frappe.logger("crm").info(
				"Nessun testo pagamento nelle impostazioni, uso informazioni di default"
			)
			return _get_default_payment_info()
			
	except Exception as e:
		frappe.log_error(
			message=f"Errore nel recupero informazioni pagamento: {frappe.get_traceback()}",
			title="CRM Payment Info Error",
		)
		frappe.logger("crm").error(f"Errore nel recupero informazioni pagamento: {str(e)}")
		# Fallback a informazioni di default
		return _get_default_payment_info()


def _get_default_payment_info() -> Dict[str, Any]:
	"""Restituisce informazioni di pagamento di default se non configurate."""
	return {
		"bank_transfer": {
			"bank_name": "Banca Fittizia S.p.A.",
			"iban": "IT60 X054 2811 1010 0000 0123 456",
			"swift": "FICTIT01",
			"account_holder": "Azienda Fittizia",
			"reference": "Ordine {order_number}",
		},
		"paypal": {
			"email": "pagamenti@aziendafittizia.it",
			"note": "Includere il numero d'ordine nel pagamento",
		},
		"instructions": (
			"Puoi effettuare il pagamento tramite bonifico bancario o PayPal. "
			"Assicurati di includere il numero d'ordine nella causale del pagamento."
		),
		"source": "default",
	}


def _send_status_change_notification(phone: str, context_data: Dict[str, Any], lead_name: str):
	"""
	Invia una notifica WhatsApp tramite AI quando lo status cambia.
	"""
	try:
		# Verifica se ai_module è installato
		if not _is_ai_module_installed():
			frappe.logger("crm").warning(
				f"ai_module non installato, impossibile inviare notifica per Lead {lead_name}"
			)
			return
		
		# Importa la funzione per chiamare l'AI
		try:
			from ai_module.integrations.status_change import process_status_change_notification
		except ImportError as import_error:
			# Logga l'errore di importazione
			frappe.log_error(
				message=f"Errore importazione ai_module.integrations.status_change: {str(import_error)}\n{frappe.get_traceback()}",
				title="CRM Status Change Notification - Import Error",
			)
			frappe.logger("crm").error(
				f"ai_module.integrations.status_change non disponibile: {str(import_error)}"
			)
			return
		
		# Prepara il payload simile a quello WhatsApp
		payload = {
			"phone": phone,
			"context": context_data,
			"lead_name": lead_name,
			"reference_doctype": "CRM Lead",
			"reference_name": lead_name,
		}
		
		# Processa la notifica (può essere inline o in background)
		process_status_change_notification(payload)
		
		frappe.logger("crm").info(
			f"Notifica cambio stato inviata per Lead {lead_name} a {phone}"
		)
		
	except Exception as e:
		# Logga l'errore ma non sopprimerlo completamente
		frappe.log_error(
			message=f"Errore nell'invio notifica cambio stato per Lead {lead_name}: {frappe.get_traceback()}",
			title="CRM Status Change Notification Error",
		)
		frappe.logger("crm").error(
			f"Errore nell'invio notifica cambio stato per Lead {lead_name}: {str(e)}"
		)
		# Non rilanciamo l'eccezione qui perché non vogliamo bloccare il salvataggio del Lead


def check_pending_payments():
	"""
	Scheduled job: Controlla gli ordini in "Attesa Pagamento" da più di 3 giorni
	e li cambia automaticamente a "Non Pagato".
	"""
	try:
		# Verifica che il DocType CRM Lead esista
		if not frappe.db.exists("DocType", "CRM Lead"):
			frappe.logger("crm").warning(
				"CRM Lead DocType non trovato, skip controllo pagamenti pendenti"
			)
			return
		
		# Calcola la data limite (3 giorni fa)
		cutoff_date = add_days(now_datetime(), -3)
		
		# Trova tutti i Lead in "Attesa Pagamento"
		leads = frappe.get_all(
			"CRM Lead",
			filters={
				"status": "Attesa Pagamento",
			},
			fields=["name", "modified", "status"],
		)
		
		updated_count = 0
		for lead in leads:
			try:
				lead_doc = frappe.get_cached_doc("CRM Lead", lead.name)
				
				# Controlla quando è stato cambiato a "Attesa Pagamento"
				status_change_date = _get_status_change_date(lead_doc.name, "Attesa Pagamento")
				
				if status_change_date and status_change_date < cutoff_date:
					# Cambia lo status a "Non Pagato"
					lead_doc.status = "Non Pagato"
					lead_doc.save(ignore_permissions=True)
					updated_count += 1
					
					frappe.logger("crm").info(
						f"Lead {lead_doc.name} cambiato automaticamente da 'Attesa Pagamento' a 'Non Pagato'"
					)
			except Exception as lead_error:
				# Logga errore per singolo lead ma continua con gli altri
				frappe.log_error(
					message=f"Errore nel processare Lead {lead.name}: {frappe.get_traceback()}",
					title="CRM Check Pending Payments - Lead Error",
				)
				frappe.logger("crm").error(
					f"Errore nel processare Lead {lead.name}: {str(lead_error)}"
				)
				continue
		
		if updated_count > 0:
			frappe.db.commit()
			frappe.logger("crm").info(
				f"Job completato: {updated_count} ordini cambiati a 'Non Pagato'"
			)
		
	except Exception as e:
		# Logga l'errore ma non sopprimerlo
		frappe.log_error(
			message=f"Errore nel job check_pending_payments: {frappe.get_traceback()}",
			title="CRM Check Pending Payments Error",
		)
		frappe.logger("crm").error(f"Errore nel job check_pending_payments: {str(e)}")
		# Rilancia l'eccezione per far sapere al scheduler che c'è stato un problema
		raise


def _get_status_change_date(lead_name: str, status: str) -> Optional[Any]:
	"""Ottieni la data dell'ultimo cambio di stato a un determinato status."""
	try:
		logs = frappe.get_all(
			"CRM Status Change Log",
			filters={
				"reference_doctype": "CRM Lead",
				"reference_name": lead_name,
				"to_status": status,
			},
			fields=["creation"],
			order_by="creation desc",
			limit=1,
		)
		
		if logs:
			return logs[0].get("creation")
		
		return None
	except Exception:
		return None

