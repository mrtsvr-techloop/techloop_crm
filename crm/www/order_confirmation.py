# Copyright (c) 2025, Techloop and Contributors
# License: MIT License

import frappe
from frappe import _
import frappe.utils

no_cache = 1


def get_context():
    """Get context for order confirmation form."""
    context = frappe._dict()
    
    # Get parameters from URL (pre-filled by AI)
    context.customer_name = frappe.request.args.get('customer_name', '')
    context.phone_number = frappe.request.args.get('phone_number', '')
    context.product_name = frappe.request.args.get('product_name', '')
    context.quantity = frappe.request.args.get('quantity', '1')
    context.unit_price = frappe.request.args.get('unit_price', '')
    context.total_price = frappe.request.args.get('total_price', '')
    context.delivery_address = frappe.request.args.get('delivery_address', '')
    context.notes = frappe.request.args.get('notes', '')
    
    return context


@frappe.whitelist(allow_guest=True, methods=["POST"])
def submit_order():
    """Submit order confirmation form."""
    try:
        # Get form data
        data = frappe.form_dict
        
        # Validate required fields
        required_fields = ['customer_name', 'phone_number', 'product_name', 'quantity']
        for field in required_fields:
            if not data.get(field):
                frappe.throw(_("Campo obbligatorio mancante: {0}").format(field))
        
        # Validate terms acceptance
        if not data.get('terms_accepted'):
            frappe.throw(_("Devi accettare i termini e condizioni"))
        
        # Create CRM Lead with order details
        lead_doc = frappe.get_doc({
            "doctype": "CRM Lead",
            "first_name": data.get('customer_name'),
            "phone": data.get('phone_number'),
            "lead_source": "WhatsApp AI",
            "status": "Confirmed Order",
            "company_name": data.get('customer_name'),  # Use customer name as company
            "email_id": f"whatsapp_{data.get('phone_number', '').replace('+', '')}@techloop.local",
            "custom_order_details": frappe.as_json({
                "product_name": data.get('product_name'),
                "quantity": int(data.get('quantity')),
                "unit_price": float(data.get('unit_price', 0)),
                "total_price": float(data.get('total_price', 0)),
                "delivery_address": data.get('delivery_address'),
                "notes": data.get('notes'),
                "confirmation_method": "WhatsApp Form",
                "form_submission_time": frappe.utils.now()
            })
        })
        
        lead_doc.insert(ignore_permissions=True)
        
        # Log the order confirmation
        frappe.logger("crm").info(f"Order confirmed via WhatsApp form: {lead_doc.name}")
        
        return {
            "success": True,
            "message": _("Ordine confermato con successo"),
            "lead_id": lead_doc.name,
            "redirect_url": "/crm/order-success"
        }
        
    except Exception as e:
        frappe.logger("crm").error(f"Order confirmation error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
