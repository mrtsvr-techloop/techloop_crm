# Copyright (c) 2025, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Sistema di notifiche WhatsApp per cambio stato Lead.
Semplice e pulito: prende gli stati dal DB, verifica se abilitati, invia il messaggio.
"""

import frappe
from frappe import _
import re


def send_status_change_notification(doc):
	"""
	Invia notifica WhatsApp quando lo stato del Lead cambia.
	Verifica se la notifica è abilitata per lo stato specifico nelle impostazioni.
	"""
	try:
		# 1. Verifica che frappe_whatsapp sia installato
		if "frappe_whatsapp" not in frappe.get_installed_apps():
			return
		
		# 2. Verifica che lo stato sia cambiato
		if not doc.has_value_changed("status"):
			return
		
		# 3. Ottieni lo stato attuale (nome inglese dal database)
		current_status = doc.status
		if not current_status:
			return
		
		# 4. Verifica se la notifica è abilitata per questo stato
		if not is_notification_enabled(current_status):
			return
		
		# 5. Ottieni il numero di telefono del contatto
		phone = get_contact_phone(doc)
		if not phone:
			return
		
		# 6. Componi il messaggio
		message = compose_message(doc, current_status)
		if not message:
			return
		
		# 7. Invia il messaggio WhatsApp
		send_whatsapp_message(doc, phone, message)
		
	except Exception as e:
		# Logga l'errore ma non bloccare il salvataggio
		frappe.log_error(
			message=f"Errore invio notifica cambio stato per Lead {doc.name}: {frappe.get_traceback()}",
			title="Status Change Notification Error"
		)


def is_notification_enabled(status):
	"""
	Verifica se la notifica è abilitata per un determinato stato.
	Legge dalle impostazioni FCRM Settings.
	"""
	try:
		# Converti il nome dello stato in slug per il nome del campo
		status_slug = slugify(status)
		fieldname = f"enable_notification_{status_slug}"
		
		# Leggi dalle impostazioni
		settings = frappe.get_doc("FCRM Settings", "FCRM Settings")
		enabled = getattr(settings, fieldname, None)
		
		# Se il campo non esiste, prova a leggerlo dal database
		if enabled is None:
			enabled = frappe.db.get_value("FCRM Settings", "FCRM Settings", fieldname)
		
		return bool(enabled) if enabled is not None else False
		
	except Exception:
		return False


def get_custom_message(status):
	"""
	Ottiene il messaggio personalizzato per un determinato stato.
	Se non configurato, ritorna il messaggio di default.
	"""
	try:
		# Converti il nome dello stato in slug per il nome del campo
		status_slug = slugify(status)
		fieldname = f"custom_message_{status_slug}"
		
		# Leggi dalle impostazioni
		settings = frappe.get_doc("FCRM Settings", "FCRM Settings")
		custom_message = getattr(settings, fieldname, None)
		
		# Se il campo non esiste, prova a leggerlo dal database
		if custom_message is None:
			custom_message = frappe.db.get_value("FCRM Settings", "FCRM Settings", fieldname)
		
		# Se c'è un messaggio personalizzato, usalo
		if custom_message and custom_message.strip():
			return custom_message.strip()
		
		# Altrimenti usa il messaggio di default
		return get_default_message(status)
		
	except Exception:
		return get_default_message(status)


def get_default_message(status):
	"""Messaggi di default per ogni stato."""
	default_messages = {
		"Awaiting Payment": "Per proseguire con l'ordine, ti invitiamo a eseguire il pagamento utilizzando i metodi forniti.",
		"Confirmed": "L'ordine è stato preso in carico e sta venendo preparato.",
		"Not Paid": "L'ordine non è stato pagato nei tempi consentiti. Per maggiori informazioni, contatta l'assistenza.",
		"Rejected": "La richiesta d'ordine è stata rifiutata, pertanto l'ordine è stato annullato.",
	}
	# Se c'è un messaggio di default per questo stato, usalo
	if status in default_messages:
		return default_messages[status]
	# Altrimenti ritorna un messaggio generico
	return f"Lo stato dell'ordine è stato aggiornato a: {_(status)}."


def get_contact_phone(doc):
	"""Ottieni il numero di telefono del contatto associato al Lead."""
	# Prova prima mobile_no, poi phone
	phone = doc.mobile_no or doc.phone
	if phone:
		# Normalizza il numero: rimuovi spazi, mantieni solo cifre e +
		phone = "".join(c for c in phone if c.isdigit() or c == "+")
		if phone and not phone.startswith("+"):
			phone = "+" + phone
		return phone
	return None


def get_status_emoji(status):
	"""
	Ottiene l'emoji appropriata basata sul colore/tipo dello stato.
	"""
	try:
		# Ottieni il colore dello stato dal database
		status_color = frappe.db.get_value("CRM Lead Status", status, "color")
		
		# Mappa colori a emoji
		color_emoji_map = {
			"green": "✅",
			"red": "❌",
			"orange": "⚠️",
			"amber": "🟡",
			"yellow": "💛",
			"blue": "🔵",
			"cyan": "💙",
			"teal": "🩵",
			"violet": "💜",
			"purple": "🟣",
			"pink": "💗",
			"gray": "⚪",
			"black": "⚫",
		}
		
		# Emoji basata sul colore
		emoji = color_emoji_map.get(status_color, "📋")
		
		# Emoji aggiuntive basate sul nome dello stato
		status_emoji_map = {
			"Awaiting Payment": "💳",
			"Confirmed": "✅",
			"Not Paid": "❌",
			"Rejected": "🚫",
			"Qualified": "⭐",
			"New": "🆕",
		}
		
		# Se c'è un'emoji specifica per lo stato, usala insieme al colore
		status_emoji = status_emoji_map.get(status, "")
		
		# Combina emoji colore e stato
		if status_emoji:
			return f"{emoji} {status_emoji}"
		return emoji
		
	except Exception:
		return "📋"


def compose_message(doc, status):
	"""
	Componi il messaggio WhatsApp per il cambio di stato.
	"""
	try:
		customer_name = doc.lead_name or doc.first_name or "Cliente"
		order_number = format_order_number(doc.name)
		status_label = _(status)
		status_emoji = get_status_emoji(status)
		
		# Ottieni il messaggio personalizzato o default
		status_message = get_custom_message(status)
		
		# Componi il messaggio base con emoji
		message_parts = [
			f"{status_emoji} Ciao {customer_name},",
			"",
			f"ti informiamo che lo stato del tuo ordine {order_number} è cambiato a '{status_label}'.",
			"",
			status_message,
		]
		
		# Aggiungi informazioni di consegna se disponibili (per stati positivi)
		if status in ["Confirmed", "Awaiting Payment"]:
			delivery_info_parts = []
			if hasattr(doc, "delivery_date") and doc.delivery_date:
				from frappe.utils import formatdate
				delivery_date_str = formatdate(doc.delivery_date, "dd/MM/yyyy")
				delivery_info_parts.append(f"📅 Data di consegna: {delivery_date_str}")
			
			if hasattr(doc, "delivery_address") and doc.delivery_address:
				delivery_address_str = doc.delivery_address
				if hasattr(doc, "delivery_city") and doc.delivery_city:
					delivery_address_str += f", {doc.delivery_city}"
				if hasattr(doc, "delivery_zip") and doc.delivery_zip:
					delivery_address_str += f" ({doc.delivery_zip})"
				delivery_info_parts.append(f"📍 Indirizzo: {delivery_address_str}")
			
			if delivery_info_parts:
				message_parts.append("")
				message_parts.append("📦 *Dettagli Consegna:*")
				for info in delivery_info_parts:
					message_parts.append(info)
		
		# Se lo stato è "Awaiting Payment", aggiungi dettagli ordine e pagamento
		if status == "Awaiting Payment":
			# Aggiungi riepilogo prodotti se disponibili
			if doc.products:
				message_parts.append("")
				message_parts.append("📋 *Riepilogo Ordine:*")
				message_parts.append("")
			
				for product in doc.products:
					product_name = product.product_name or "Prodotto"
					qty = float(product.qty or 0)
					rate = float(product.rate or 0)
					amount = float(product.amount or 0)
					message_parts.append(f"• {product_name}: {qty:.1f} x €{rate:.2f} = €{amount:.2f}")
				
				message_parts.append("")
				net_total = float(doc.net_total or 0)
				message_parts.append(f"💰 *Totale: EUR {net_total:.2f}*")
			
			# Aggiungi informazioni di pagamento
			payment_info = get_payment_info()
			if payment_info:
				message_parts.append("")
				message_parts.append("💳 *Informazioni Pagamento:*")
				message_parts.append("")
				# Sostituisci placeholder nel testo
				payment_text = payment_info.replace("{numero_ordine}", order_number)
				payment_text = payment_text.replace("{order_number}", order_number)
				message_parts.append(payment_text)
		
		return "\n".join(message_parts)
		
	except Exception as e:
		frappe.log_error(
			message=f"Errore composizione messaggio per Lead {doc.name}: {frappe.get_traceback()}",
			title="Message Composition Error"
		)
		return None


def get_payment_info():
	"""
	Legge le informazioni di pagamento dalle impostazioni FCRM.
	"""
	try:
		settings = frappe.get_doc("FCRM Settings", "FCRM Settings")
		payment_text = getattr(settings, "payment_info_text", None)
		
		if payment_text and payment_text.strip():
			return payment_text.strip()
		
		# Informazioni di default se non configurate
		return (
			"Puoi effettuare il pagamento tramite bonifico bancario.\n"
			"Assicurati di includere il numero d'ordine nella causale."
		)
		
	except Exception:
		return None


def send_whatsapp_message(doc, phone, message):
	"""Invia il messaggio WhatsApp."""
	try:
		from crm.api.whatsapp import create_whatsapp_message
		
		# Invia il messaggio
		message_name = create_whatsapp_message(
			reference_doctype="CRM Lead",
			reference_name=doc.name,
			message=message,
			to=phone,
			attach="",
			reply_to="",
			content_type="text",
			label="Status Change Notification",
		)
		
		frappe.logger("crm").info(
			f"Notifica cambio stato inviata per Lead {doc.name} (WhatsApp Message: {message_name})"
		)
		
	except ImportError:
		frappe.logger("crm").error("crm.api.whatsapp non disponibile")
	except Exception as e:
		frappe.log_error(
			message=f"Errore invio WhatsApp per Lead {doc.name}: {frappe.get_traceback()}",
			title="WhatsApp Send Error"
		)


def format_order_number(order_number):
	"""
	Formatta il numero ordine in modo più leggibile.
	Esempio: "CRM-LEAD-2025-00021" -> "25-00021"
	"""
	try:
		if order_number.startswith("CRM-LEAD-"):
			parts = order_number.split("-")
			if len(parts) >= 4:
				year = parts[2][-2:]  # Ultime 2 cifre dell'anno
				number = parts[3]
				return f"{year}-{number}"
		return order_number
	except Exception:
		return order_number


def slugify(text):
	"""
	Converte un testo in uno slug valido per i nomi dei campi.
	Esempio: "Awaiting Payment" -> "awaiting_payment"
	"""
	slug = text.lower()
	slug = re.sub(r'[^a-z0-9]+', '_', slug)
	slug = slug.strip('_')
	return slug
