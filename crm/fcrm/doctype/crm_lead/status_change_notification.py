# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Listener per cambio stato dei Lead che invia notifiche WhatsApp automaticamente.
"""

import frappe
import re
from frappe import _
from frappe.utils import now_datetime, add_days
import json
from typing import Dict, Any, Optional


def on_lead_status_change(doc, method=None):
	"""
	Hook chiamato quando lo status di un Lead cambia.
	Invia una notifica WhatsApp automatica al contatto associato.
	"""
	try:
		# Log iniziale per verificare che la funzione viene chiamata
		# Usa sia log_error (database) che logger (file)
		frappe.log_error(
			message=f"[STATUS_CHANGE] on_lead_status_change chiamato per Lead {doc.name}",
			title="CRM Status Change Debug"
		)
		frappe.logger("crm").info(f"[STATUS_CHANGE] on_lead_status_change chiamato per Lead {doc.name}")
		print(f"[STATUS_CHANGE] on_lead_status_change chiamato per Lead {doc.name}")
		
		# Verifica se frappe_whatsapp è installato
		if not _is_whatsapp_installed():
			frappe.log_error(
				message=f"[STATUS_CHANGE] frappe_whatsapp non installato, skip notifica per Lead {doc.name}",
				title="CRM Status Change Debug"
			)
			return
		
		# Verifica se lo status è cambiato
		if not doc.has_value_changed("status"):
			frappe.log_error(
				message=f"[STATUS_CHANGE] Status non cambiato per Lead {doc.name}",
				title="CRM Status Change Debug"
			)
			return
		
		# Ottieni lo status precedente dal documento prima del salvataggio
		old_status = _get_previous_status(doc)
		new_status = doc.status
		
		frappe.log_error(
			message=f"[STATUS_CHANGE] Lead {doc.name} - old_status: '{old_status}', new_status: '{new_status}' (raw: {repr(new_status)})",
			title="CRM Status Change Debug"
		)
		
		if not new_status:
			frappe.log_error(
				message=f"[STATUS_CHANGE] new_status vuoto per Lead {doc.name}",
				title="CRM Status Change Debug"
			)
			return
		
		# Se lo status è lo stesso, non fare nulla
		if old_status == new_status:
			frappe.log_error(
				message=f"[STATUS_CHANGE] old_status == new_status per Lead {doc.name}",
				title="CRM Status Change Debug"
			)
			return
		
		# FLUSSO UNIFICATO: Verifica se la notifica è abilitata per questo stato
		# La funzione normalizza automaticamente lo stato al nome inglese
		notification_settings = _get_status_notification_settings(new_status)
		
		if not notification_settings.get("enabled", False):
			frappe.log_error(
				message=f"[STATUS_CHANGE] Notifica disabilitata per stato '{new_status}' (normalizzato: '{notification_settings.get('status_en', 'N/A')}') per Lead {doc.name}",
				title="CRM Status Change Debug"
			)
			return
		
		# Ottieni il nome inglese normalizzato per usarlo nel resto del flusso
		normalized_status_en = notification_settings.get("status_en")
		if not normalized_status_en:
			frappe.log_error(
				message=f"[STATUS_CHANGE] Impossibile normalizzare stato '{new_status}' per Lead {doc.name}",
				title="CRM Status Change Debug"
			)
			return
		
		# Ottieni il numero di telefono del contatto
		phone = _get_contact_phone(doc)
		if not phone:
			frappe.log_error(
				message=f"[STATUS_CHANGE] Nessun numero di telefono trovato per Lead {doc.name}",
				title="CRM Status Change Debug"
			)
			return
		
		frappe.log_error(
			message=f"[STATUS_CHANGE] Preparando context per Lead {doc.name} - old_status: '{old_status}', new_status: '{new_status}'",
			title="CRM Status Change Debug"
		)
		
		# Prepara i dati per il messaggio usando il nome inglese normalizzato
		# Normalizza anche old_status per coerenza
		normalized_old_status_en = _normalize_status_to_english(old_status) if old_status else None
		context_data = _prepare_status_change_context(doc, normalized_old_status_en or old_status, normalized_status_en)
		
		# Aggiungi il messaggio dalle impostazioni al context per usarlo nella composizione
		context_data["status_notification_message"] = notification_settings.get("message", "")
		
		frappe.log_error(
			message=f"[STATUS_CHANGE] Context preparato - new_status_en: '{context_data.get('new_status_en')}', new_status: '{context_data.get('new_status')}'",
			title="CRM Status Change Debug"
		)
		
		# Componi e invia il messaggio WhatsApp
		_send_status_change_notification(phone, context_data, doc.name)
		
	except Exception as e:
		# Logga l'errore ma non bloccare il salvataggio del Lead
		frappe.log_error(
			message=f"Errore nell'invio notifica cambio stato per Lead {doc.name}: {frappe.get_traceback()}",
			title="CRM Lead Status Change Notification Error",
		)
		frappe.logger("crm").error(
			f"Errore nell'invio notifica cambio stato per Lead {doc.name}: {str(e)}"
		)
		# Non rilanciamo l'eccezione per non bloccare il salvataggio del Lead


def _is_whatsapp_installed() -> bool:
	"""Verifica se frappe_whatsapp è installato."""
	try:
		installed_apps = frappe.get_installed_apps()
		return "frappe_whatsapp" in installed_apps
	except Exception as e:
		frappe.log_error(
			message=f"Errore nel controllo app installate: {frappe.get_traceback()}",
			title="CRM Check Installed Apps Error",
		)
		frappe.logger("crm").error(f"Errore nel controllo app installate: {str(e)}")
		return False


def _get_previous_status(doc) -> Optional[str]:
	"""Ottieni lo status precedente dal documento prima del salvataggio."""
	try:
		# Usa get_doc_before_save() per ottenere lo status precedente
		# Questo è il modo più affidabile perché viene chiamato durante validate()
		doc_before_save = doc.get_doc_before_save()
		if doc_before_save and doc_before_save.status:
			return doc_before_save.status
		
		# Fallback: cerca nel log dei cambi di stato
		if doc.status_change_log:
			# Prendi il penultimo log entry (l'ultimo è quello corrente che si sta creando)
			# Il campo si chiama "from" non "from_status" (usare getattr perché "from" è parola riservata)
			if len(doc.status_change_log) >= 2:
				previous_log = doc.status_change_log[-2]
				from_status = getattr(previous_log, 'from', None)
				if from_status:
					return from_status
			elif len(doc.status_change_log) == 1:
				# Se c'è solo un log, usa quello
				previous_log = doc.status_change_log[0]
				from_status = getattr(previous_log, 'from', None)
				if from_status:
					return from_status
		
		# Fallback finale: cerca nel database
		# Nota: "from" è una parola riservata SQL, ma frappe.get_all lo gestisce correttamente
		logs = frappe.get_all(
			"CRM Status Change Log",
			filters={"reference_doctype": "CRM Lead", "reference_name": doc.name},
			fields=["from"],  # Campo "from" del log
			order_by="creation desc",
			limit=2  # Prendi gli ultimi 2 per avere quello precedente
		)
		if len(logs) >= 2:
			# Il secondo è quello precedente
			return logs[1].get("from")
		elif len(logs) == 1:
			# Se c'è solo un log, usa quello
			return logs[0].get("from")
		
		return None
	except Exception:
		return None


def _format_order_number(order_number: str) -> str:
	"""
	Converte il numero ordine da formato completo a formato abbreviato.
	Esempio: "CRM-LEAD-2025-00021" -> "25-00021"
	"""
	try:
		# Se il formato è "CRM-LEAD-YYYY-XXXXX", estrai anno e numero
		if order_number.startswith("CRM-LEAD-"):
			parts = order_number.split("-")
			if len(parts) >= 4:
				year = parts[2]  # 2025
				number = parts[3]  # 00021
				# Prendi solo le ultime 2 cifre dell'anno
				year_short = year[-2:] if len(year) >= 2 else year
				return f"{year_short}-{number}"
		# Se il formato è già abbreviato o diverso, restituisci così com'è
		return order_number
	except Exception:
		# In caso di errore, restituisci il numero originale
		return order_number


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
	Prepara i dati strutturati per il messaggio in base al cambio di stato.
	"""
	# Debug: log per vedere cosa viene passato
	frappe.logger("crm").info(
		f"[STATUS_CHANGE_CTX] Preparing context - old_status: '{old_status}', new_status: '{new_status}'"
	)
	
	# Traduci gli stati in italiano (gli stati nel DB sono in inglese)
	old_status_translated = _(old_status) if old_status else "N/A"
	new_status_translated = _(new_status) if new_status else "N/A"
	
	frappe.logger("crm").info(
		f"[STATUS_CHANGE_CTX] Translated - old_status_translated: '{old_status_translated}', new_status_translated: '{new_status_translated}'"
	)
	
	context = {
		"lead_id": doc.name,
		"order_number": _format_order_number(doc.name),  # Formato abbreviato: 25-00021
		"old_status": old_status_translated,  # Tradotto in italiano
		"old_status_en": old_status,  # Mantieni anche la versione inglese per controlli
		"new_status": new_status_translated,  # Tradotto in italiano
		"new_status_en": new_status,  # Mantieni anche la versione inglese per controlli
		"customer_name": doc.lead_name or doc.first_name or "Cliente",
		"has_order_details": False,
	}
	
	frappe.log_error(
		message=f"[STATUS_CHANGE_CTX] Context created - new_status_en: '{context.get('new_status_en')}', new_status: '{context.get('new_status')}', new_status originale: '{new_status}'",
		title="CRM Status Change Debug"
	)
	
	# Se lo stato è "Awaiting Payment" (Attesa Pagamento), aggiungi dettagli ordine
	# new_status qui è lo stato inglese dal DB (doc.status)
	if new_status == "Awaiting Payment":
		frappe.log_error(
			message="[STATUS_CHANGE_CTX] Stato è 'Awaiting Payment', aggiungo dettagli ordine e payment_info",
			title="CRM Status Change Debug"
		)
		context["has_order_details"] = True
		context["order_summary"] = _prepare_order_summary(doc)
		context["payment_info"] = _get_payment_info()
		frappe.log_error(
			message=f"[STATUS_CHANGE_CTX] payment_info aggiunto - source: {context['payment_info'].get('source')}, text presente: {bool(context['payment_info'].get('text'))}",
			title="CRM Status Change Debug"
		)
	else:
		frappe.log_error(
			message=f"[STATUS_CHANGE_CTX] Stato NON è 'Awaiting Payment' (è '{new_status}'), NON aggiungo dettagli ordine",
			title="CRM Status Change Debug"
		)
	
	return context


def _prepare_order_summary(doc) -> Dict[str, Any]:
	"""Prepara il riepilogo dell'ordine con prodotti, quantità e prezzi."""
	summary = {
		"products": [],
		"subtotal": float(doc.total or 0),
		"net_total": float(doc.net_total or 0),
		"currency": "EUR",  # Valuta fissa: solo Euro
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
			frappe.log_error(
				message="[PAYMENT_INFO] FCRM Settings non trovato, uso informazioni di pagamento di default",
				title="CRM Payment Info Debug"
			)
			return _get_default_payment_info()
		
		# Leggi le impostazioni
		settings = frappe.get_cached_doc("FCRM Settings", "FCRM Settings")
		payment_text = getattr(settings, "payment_info_text", None)
		
		log_msg = f"[PAYMENT_INFO] Lettura da FCRM Settings - payment_text presente: {payment_text is not None}, valore: {repr(payment_text[:100] if payment_text else None)}"
		frappe.log_error(message=log_msg, title="CRM Payment Info Debug")
		frappe.logger("crm").info(log_msg)
		print(log_msg)
		
		if payment_text and payment_text.strip():
			# Restituisci il testo così com'è
			result = {
				"text": payment_text.strip(),
				"source": "settings",
			}
			frappe.log_error(
				message=f"[PAYMENT_INFO] Restituito testo da settings - lunghezza: {len(result['text'])}",
				title="CRM Payment Info Debug"
			)
			return result
		else:
			# Se non c'è testo nelle impostazioni, usa quello di default
			frappe.log_error(
				message="[PAYMENT_INFO] payment_info_text vuoto nelle impostazioni, uso informazioni di default",
				title="CRM Payment Info Debug"
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


def _slugify_status_name(status_name: str) -> str:
	"""
	Converte il nome di uno stato in uno slug valido per i nomi dei campi.
	Es: "Awaiting Payment" -> "awaiting_payment"
	"""
	# Converti in lowercase e sostituisci spazi e caratteri speciali con underscore
	slug = status_name.lower()
	slug = re.sub(r'[^a-z0-9]+', '_', slug)
	slug = slug.strip('_')
	return slug


def _normalize_status_to_english(status_name: str) -> Optional[str]:
	"""
	Normalizza il nome di uno stato al nome inglese del database.
	
	NOTA: Tutti gli stati nel database sono in inglese. Questa funzione:
	1. Verifica se lo stato esiste direttamente nel database (già in inglese)
	2. Se non trovato, cerca usando la traduzione di Frappe (per gestire stati passati tradotti)
	
	Args:
		status_name: Nome dello stato (può essere tradotto dall'UI o inglese dal DB)
	
	Returns:
		Nome inglese dello stato nel database, o None se non trovato
	
	Esempi:
		"Awaiting Payment" -> "Awaiting Payment" (se esiste nel DB)
		"Attesa Pagamento" -> "Awaiting Payment" (tradotto da Frappe)
	"""
	if not status_name:
		return None
	
	status_name = str(status_name).strip()
	
	# PRIORITÀ 1: Se lo stato esiste direttamente nel database (già in inglese), restituiscilo
	if frappe.db.exists("CRM Lead Status", status_name):
		return status_name
	
	# PRIORITÀ 2: Cerca nel database usando le traduzioni di Frappe
	# (per gestire il caso in cui lo stato viene passato tradotto dall'UI)
	all_statuses = frappe.get_all("CRM Lead Status", fields=["name"], limit=1000)
	
	for status in all_statuses:
		# Confronta usando la traduzione di Frappe
		translated = _(status.name)
		if translated == status_name or status.name == status_name:
			return status.name
	
	# PRIORITÀ 3: Cerca case-insensitive
	for status in all_statuses:
		if status.name.lower() == status_name.lower():
			return status.name
	
	return None


def _get_status_notification_settings(status: str) -> Dict[str, Any]:
	"""
	Restituisce le impostazioni di notifica per uno stato specifico.
	Legge dinamicamente da FCRM Settings se la notifica è abilitata e il messaggio personalizzato.
	Funziona con qualsiasi stato disponibile nel database, non solo quelli hardcoded.
	
	Args:
		status: Nome dello stato (può essere tradotto o inglese)
	
	Returns:
		Dict con "enabled" (bool) e "message" (str)
	"""
	if not status:
		return {"enabled": False, "message": ""}
	
	# FLUSSO UNIFICATO: Converti sempre al nome inglese del database
	status_en = _normalize_status_to_english(status)
	
	if not status_en:
		# Se non riesco a normalizzare, restituisci disabled
		frappe.log_error(
			message=f"[STATUS_NOTIF] Impossibile normalizzare stato '{status}' al nome inglese",
			title="CRM Status Notification Settings Error"
		)
		return {"enabled": False, "message": ""}
	
	# Verifica che lo stato esista nel database (dovrebbe esistere se normalizzato correttamente)
	if not frappe.db.exists("CRM Lead Status", status_en):
		frappe.log_error(
			message=f"[STATUS_NOTIF] Stato normalizzato '{status_en}' non esiste nel database",
			title="CRM Status Notification Settings Error"
		)
		return {"enabled": False, "message": ""}
	
	# Converti il nome inglese dello stato in slug per i nomi dei campi
	status_slug = _slugify_status_name(status_en)
	enable_fieldname = f"enable_notification_{status_slug}"
	message_fieldname = f"custom_message_{status_slug}"
	
	try:
		# Usa get_doc invece di get_cached_doc per assicurarsi che i Custom Fields siano inclusi
		settings = frappe.get_doc("FCRM Settings", "FCRM Settings")
		
		# Leggi se la notifica è abilitata
		# Prova prima con getattr, poi con get_value come fallback
		enabled = getattr(settings, enable_fieldname, None)
		
		if enabled is None:
			# Fallback: prova a leggere direttamente dal database
			try:
				enabled = frappe.db.get_value("FCRM Settings", "FCRM Settings", enable_fieldname)
			except Exception:
				pass
		
		if enabled is None:
			# Se il campo non esiste ancora, potrebbe essere uno stato nuovo
			# In questo caso, restituisci False per sicurezza
			frappe.log_error(
				message=f"[STATUS_NOTIF] Campo '{enable_fieldname}' non trovato per stato '{status_en}' (slug: '{status_slug}')",
				title="CRM Status Notification Settings Warning"
			)
			enabled = False
		else:
			enabled = bool(enabled)
		
		# Leggi il messaggio personalizzato
		custom_message = getattr(settings, message_fieldname, None)
		if custom_message is None:
			# Fallback: prova a leggere direttamente dal database
			try:
				custom_message = frappe.db.get_value("FCRM Settings", "FCRM Settings", message_fieldname)
			except Exception:
				pass
		
		if custom_message and custom_message.strip():
			message = custom_message.strip()
		else:
			# Usa il messaggio di default (generico se non specificato)
			default_messages = {
				"Rejected": "La richiesta d'ordine è stata rifiutata, pertanto l'ordine è stato annullato.",
				"Awaiting Payment": "Per proseguire con l'ordine, ti invitiamo a eseguire il pagamento utilizzando i metodi forniti di seguito.",
				"Confirmed": "L'ordine è stato preso in carico e sta venendo preparato.",
				"Not Paid": "L'ordine non è stato pagato nei tempi consentiti. Per maggiori informazioni, ti invitiamo a contattare l'assistenza.",
			}
			# Se c'è un messaggio di default per questo stato, usalo, altrimenti usa un messaggio generico
			message = default_messages.get(status_en, f"Lo stato dell'ordine è stato aggiornato a: {_(status_en)}.")
		
		return {"enabled": enabled, "message": message, "status_en": status_en}
	except Exception as e:
		error_msg = f"Errore nel recupero impostazioni notifica per stato '{status}' (normalizzato: '{status_en}'): {str(e)}\n{frappe.get_traceback()}"
		try:
			frappe.log_error(
				message=error_msg,
				title="CRM Status Notification Settings Error"
			)
		except Exception:
			# Se non riesce a loggare, ignora (potrebbe essere problema di permessi)
			pass
		# In caso di errore, restituisci disabled ma mantieni status_en se disponibile
		return {"enabled": False, "message": "", "status_en": status_en if status_en else None}


def _get_status_specific_info(status_en: str) -> str:
	"""
	DEPRECATED: Usa _get_status_notification_settings() invece.
	Mantiene compatibilità con codice esistente.
	"""
	settings = _get_status_notification_settings(status_en)
	return settings.get("message", "") if settings.get("enabled", False) else ""


def _compose_status_change_message(context_data: Dict[str, Any]) -> str:
	"""
	Componi il messaggio WhatsApp in base al cambio di stato.
	"""
	order_number = context_data.get("order_number", "")
	old_status = context_data.get("old_status", "N/A")
	new_status = context_data.get("new_status", "")
	new_status_en = context_data.get("new_status_en", "")
	customer_name = context_data.get("customer_name", "Cliente")
	
	# Debug: log per verificare i valori
	frappe.logger("crm").info(
		f"[STATUS_CHANGE_MSG] Composing message - new_status: '{new_status}', new_status_en: '{new_status_en}', "
		f"old_status: '{old_status}', has_order_details: {context_data.get('has_order_details')}"
	)
	
	# FLUSSO UNIFICATO: new_status_en dovrebbe essere già normalizzato dal context
	# Se non lo è, normalizzalo ora (fallback per sicurezza)
	if not new_status_en or new_status_en == "":
		new_status_en = _normalize_status_to_english(new_status) or new_status
	
	# Debug: verifica i valori prima del controllo
	frappe.log_error(
		message=f"[STATUS_CHANGE_MSG] Prima del controllo - has_order_details: {context_data.get('has_order_details')}, new_status_en: '{new_status_en}', new_status: '{new_status}'",
		title="CRM Status Change Debug"
	)
	
	# Messaggio base per cambio stato generico
	# Usa new_status_en per il controllo (stato in inglese dal DB)
	if context_data.get("has_order_details") and new_status_en == "Awaiting Payment":
		frappe.log_error(
			message="[STATUS_CHANGE_MSG] Entrato nel blocco 'Awaiting Payment' con dettagli ordine",
			title="CRM Status Change Debug"
		)
		# Messaggio completo per "Attesa Pagamento" con dettagli ordine
		message_parts = [
			f"Ciao {customer_name},",
			f"",
			f"ti informiamo che lo stato del tuo ordine {order_number} è cambiato a '{new_status}'.",
			f"",
		]
		
		# Aggiungi riepilogo ordine
		order_summary = context_data.get("order_summary", {})
		if order_summary.get("products"):
			message_parts.append("*Riepilogo Ordine:*")
			message_parts.append("")
			
			for product in order_summary["products"]:
				product_name = product.get("name", "Prodotto")
				quantity = product.get("quantity", 0)
				unit_price = product.get("unit_price", 0)
				total_price = product.get("total_price", 0)
				
				message_parts.append(
					f"{product_name}: {quantity:.1f} x €{unit_price:.2f} = €{total_price:.2f}"
				)
			
			message_parts.append("")
			net_total = order_summary.get("net_total", 0)
			currency = order_summary.get("currency", "EUR")
			message_parts.append(f"*Totale: {currency} {net_total:.2f}*")
			message_parts.append("")
		
		# PRIMA: Aggiungi il messaggio personalizzato per lo stato (dal context)
		status_message = context_data.get("status_notification_message", "")
		if status_message:
			message_parts.append("")
			message_parts.append(status_message)
		
		# POI: Aggiungi informazioni pagamento (solo per "Awaiting Payment")
		payment_info = context_data.get("payment_info", {})
		
		log_msg = f"[PAYMENT_INFO] Componendo messaggio - payment_info presente: {bool(payment_info)}, source: '{payment_info.get('source')}', text presente: {bool(payment_info.get('text'))}, text value: {repr(payment_info.get('text', '')[:50])}"
		frappe.log_error(message=log_msg, title="CRM Payment Info Debug")
		frappe.logger("crm").info(log_msg)
		print(log_msg)
		
		if payment_info.get("source") == "settings" and payment_info.get("text"):
			# Usa il testo dalle impostazioni
			log_msg2 = f"[PAYMENT_INFO] Aggiungendo testo da settings - lunghezza: {len(payment_info['text'])}, testo: {repr(payment_info['text'][:100])}"
			frappe.log_error(message=log_msg2, title="CRM Payment Info Debug")
			frappe.logger("crm").info(log_msg2)
			print(log_msg2)
			message_parts.append("")
			message_parts.append("*Informazioni Pagamento:*")
			message_parts.append("")
			payment_text = payment_info["text"]
			# Sostituisci placeholder {numero_ordine} se presente
			payment_text = payment_text.replace("{numero_ordine}", order_number)
			payment_text = payment_text.replace("{order_number}", order_number)
			message_parts.append(payment_text)
			frappe.log_error(
				message=f"[PAYMENT_INFO] Testo aggiunto al messaggio - lunghezza finale: {len(payment_text)}",
				title="CRM Payment Info Debug"
			)
		else:
			frappe.log_error(
				message=f"[PAYMENT_INFO] Usando informazioni di default - source: '{payment_info.get('source')}', text presente: {bool(payment_info.get('text'))}, payment_info keys: {list(payment_info.keys())}",
				title="CRM Payment Info Debug"
			)
			# Usa informazioni di default
			default_info = payment_info
			if default_info.get("bank_transfer"):
				bank = default_info["bank_transfer"]
				message_parts.append("")
				message_parts.append("*Bonifico Bancario:*")
				message_parts.append(f"- Banca: {bank.get('bank_name', '')}")
				message_parts.append(f"- IBAN: {bank.get('iban', '')}")
				if bank.get("swift"):
					message_parts.append(f"- SWIFT: {bank.get('swift')}")
				message_parts.append(f"- Intestatario: {bank.get('account_holder', '')}")
				message_parts.append(f"- Causale: Ordine {order_number}")
				message_parts.append("")
			
			if default_info.get("paypal"):
				paypal = default_info["paypal"]
				message_parts.append(f"*PayPal:* {paypal.get('email', '')}")
				message_parts.append("")
			
			if default_info.get("instructions"):
				message_parts.append(default_info["instructions"])
		
		return "\n".join(message_parts)
	else:
		frappe.log_error(
			message=f"[STATUS_CHANGE_MSG] Entrato nel blocco ELSE - has_order_details: {context_data.get('has_order_details')}, new_status_en: '{new_status_en}'",
			title="CRM Status Change Debug"
		)
		# Messaggio semplice per cambio stato generico
		message_parts = []
		
		if old_status == "N/A":
			message_parts.append(f"Ciao {customer_name},")
			message_parts.append("")
			message_parts.append(f"ti informiamo che lo stato del tuo ordine {order_number} è cambiato a '{new_status}'.")
		else:
			message_parts.append(f"Ciao {customer_name},")
			message_parts.append("")
			message_parts.append(f"ti informiamo che lo stato del tuo ordine {order_number} è cambiato da '{old_status}' a '{new_status}'.")
		
		# PRIMA: Aggiungi il messaggio personalizzato dal context (già recuperato)
		status_message = context_data.get("status_notification_message", "")
		if status_message:
			message_parts.append("")
			message_parts.append(status_message)
		
		# POI: Se lo stato è "Awaiting Payment", aggiungi le informazioni di pagamento
		# anche se non ci sono dettagli ordine (has_order_details = False)
		if new_status_en == "Awaiting Payment":
			frappe.log_error(
				message="[STATUS_CHANGE_MSG] Stato è 'Awaiting Payment' nel blocco ELSE, aggiungo payment_info",
				title="CRM Status Change Debug"
			)
			payment_info = context_data.get("payment_info", {})
			# Se payment_info non è nel context, leggilo direttamente
			if not payment_info:
				payment_info = _get_payment_info()
			
			frappe.log_error(
				message=f"[PAYMENT_INFO] (else branch) payment_info presente: {bool(payment_info)}, source: '{payment_info.get('source')}', text presente: {bool(payment_info.get('text'))}",
				title="CRM Payment Info Debug"
			)
			
			if payment_info.get("source") == "settings" and payment_info.get("text"):
				message_parts.append("")
				message_parts.append("*Informazioni Pagamento:*")
				message_parts.append("")
				payment_text = payment_info["text"]
				payment_text = payment_text.replace("{numero_ordine}", order_number)
				payment_text = payment_text.replace("{order_number}", order_number)
				message_parts.append(payment_text)
				frappe.log_error(
					message=f"[PAYMENT_INFO] (else branch) Testo aggiunto - lunghezza: {len(payment_text)}",
					title="CRM Payment Info Debug"
				)
			elif payment_info.get("bank_transfer") or payment_info.get("paypal"):
				# Usa informazioni di default
				message_parts.append("")
				message_parts.append("*Informazioni Pagamento:*")
				message_parts.append("")
				if payment_info.get("bank_transfer"):
					bank = payment_info["bank_transfer"]
					message_parts.append("*Bonifico Bancario:*")
					message_parts.append(f"- Banca: {bank.get('bank_name', '')}")
					message_parts.append(f"- IBAN: {bank.get('iban', '')}")
					if bank.get("swift"):
						message_parts.append(f"- SWIFT: {bank.get('swift')}")
					message_parts.append(f"- Intestatario: {bank.get('account_holder', '')}")
					message_parts.append(f"- Causale: Ordine {order_number}")
					message_parts.append("")
				if payment_info.get("paypal"):
					paypal = payment_info["paypal"]
					message_parts.append(f"*PayPal:* {paypal.get('email', '')}")
					message_parts.append("")
				if payment_info.get("instructions"):
					message_parts.append(payment_info["instructions"])
		
		return "\n".join(message_parts)


def _send_status_change_notification(phone: str, context_data: Dict[str, Any], lead_name: str):
	"""
	Componi e invia una notifica WhatsApp quando lo status cambia.
	"""
	try:
		# Verifica se frappe_whatsapp è installato
		if not _is_whatsapp_installed():
			frappe.logger("crm").warning(
				f"frappe_whatsapp non installato, impossibile inviare notifica per Lead {lead_name}"
			)
			return
		
		# Importa la funzione per inviare messaggi WhatsApp
		try:
			from crm.api.whatsapp import create_whatsapp_message
		except ImportError as import_error:
			frappe.log_error(
				message=f"Errore importazione crm.api.whatsapp: {str(import_error)}\n{frappe.get_traceback()}",
				title="CRM Status Change Notification - Import Error",
			)
			frappe.logger("crm").error(
				f"crm.api.whatsapp non disponibile: {str(import_error)}"
			)
			return
		
		# Componi il messaggio
		message_text = _compose_status_change_message(context_data)
		
		if not message_text:
			frappe.logger("crm").warning(
				f"Messaggio vuoto per Lead {lead_name}, skip invio"
			)
			return
		
		# Il numero viene normalizzato automaticamente da WhatsAppMessage.format_number()
		# Mantieni il formato con +, verrà gestito automaticamente
		phone_normalized = phone
		
		# Invia il messaggio WhatsApp
		message_name = create_whatsapp_message(
			reference_doctype="CRM Lead",
			reference_name=lead_name,
			message=message_text,
			to=phone_normalized,
			attach="",
			reply_to="",
			content_type="text",
			label="Status Change Notification",
		)
		
		frappe.logger("crm").info(
			f"Notifica cambio stato inviata per Lead {lead_name} a {phone_normalized} (messaggio: {message_name})"
		)
		
	except Exception as e:
		# Logga l'errore ma non bloccare il salvataggio del Lead
		frappe.log_error(
			message=f"Errore nell'invio notifica cambio stato per Lead {lead_name}: {frappe.get_traceback()}",
			title="CRM Status Change Notification Error",
		)
		frappe.logger("crm").error(
			f"Errore nell'invio notifica cambio stato per Lead {lead_name}: {str(e)}"
		)


def check_pending_payments():
	"""
	Scheduled job: Controlla gli ordini in "Awaiting Payment" (Attesa Pagamento) da più di 3 giorni
	e li cambia automaticamente a "Not Paid" (Non Pagato).
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
		
		# Trova tutti i Lead in "Awaiting Payment" (Attesa Pagamento)
		leads = frappe.get_all(
			"CRM Lead",
			filters={
				"status": "Awaiting Payment",
			},
			fields=["name", "modified", "status"],
		)
		
		updated_count = 0
		for lead in leads:
			try:
				lead_doc = frappe.get_cached_doc("CRM Lead", lead.name)
				
				# Controlla quando è stato cambiato a "Awaiting Payment"
				status_change_date = _get_status_change_date(lead_doc.name, "Awaiting Payment")
				
				if status_change_date and status_change_date < cutoff_date:
					# Cambia lo status a "Not Paid" (Non Pagato)
					lead_doc.status = "Not Paid"
					lead_doc.save(ignore_permissions=True)
					updated_count += 1
					
					frappe.logger("crm").info(
						f"Lead {lead_doc.name} cambiato automaticamente da 'Awaiting Payment' a 'Not Paid'"
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
				f"Job completato: {updated_count} ordini cambiati a 'Not Paid'"
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

