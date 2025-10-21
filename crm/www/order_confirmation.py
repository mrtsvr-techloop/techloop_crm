# Copyright (c) 2025, Techloop and Contributors
# License: MIT License

import frappe
from frappe import _
import frappe.utils

no_cache = 1


def get_context():
    """Get context for order confirmation form."""
    context = frappe._dict()
    
    # Get FCRM TEMP ORDINE ID from URL path
    temp_order_id = frappe.request.path.split('/')[-1] if '/' in frappe.request.path else None
    
    if temp_order_id:
        # Import FCRM TEMP ORDINE functions
        from crm.fcrm.doctype.fcrm_temp_ordine.fcrm_temp_ordine import get_temp_order_data
        
        # Get order data from FCRM TEMP ORDINE
        order_data, error = get_temp_order_data(temp_order_id)
        
        if order_data:
            context.temp_order_id = temp_order_id
            context.customer_name = order_data.get('customer_name', '')
            context.phone_number = order_data.get('phone_number', '')
            context.delivery_address = order_data.get('delivery_address', '')
            context.notes = order_data.get('notes', '')
            context.products = order_data.get('products', [])
            
            # Get product details from CRM Product
            context.product_details = []
            total_price = 0
            
            for product in context.products:
                try:
                    product_doc = frappe.get_doc("CRM Product", product['product_id'])
                    product_detail = {
                        'id': product['product_id'],
                        'name': product_doc.product_name,
                        'quantity': product['product_quantity'],
                        'unit_price': float(product_doc.standard_rate or 0),
                        'total_price': float(product_doc.standard_rate or 0) * int(product['product_quantity'])
                    }
                    context.product_details.append(product_detail)
                    total_price += product_detail['total_price']
                except Exception as e:
                    frappe.logger("crm").error(f"Error loading product {product['product_id']}: {str(e)}")
            
            context.total_price = total_price
            context.order_valid = True
        else:
            context.order_valid = False
            context.error_message = error or "Order not found"
    else:
        context.order_valid = False
        context.error_message = "Invalid order link"
    
    # CSRF token for POST from guest/page
    try:
        context.csrf_token = frappe.sessions.get_csrf_token()
    except Exception:
        context.csrf_token = None
    
    return context


@frappe.whitelist(allow_guest=True, methods=["POST"])
def submit_order():
    """Submit order confirmation form."""
    try:
        # Get form data
        data = frappe.form_dict
        
        # Get FCRM TEMP ORDINE ID
        temp_order_id = data.get('temp_order_id')
        if not temp_order_id:
            frappe.throw(_("Temp Order ID mancante"))
        
        # Import FCRM TEMP ORDINE functions
        from crm.fcrm.doctype.fcrm_temp_ordine.fcrm_temp_ordine import get_temp_order_data, consume_temp_order
        
        # Get and validate FCRM TEMP ORDINE
        order_data, error = get_temp_order_data(temp_order_id)
        if not order_data:
            frappe.throw(_("Ordine scaduto o non valido: {0}").format(error or "Unknown error"))
        
        # Validate required fields
        required_fields = ['customer_name', 'phone_number']
        for field in required_fields:
            if not data.get(field):
                frappe.throw(_("Campo obbligatorio mancante: {0}").format(field))
        
        # Validate terms acceptance
        if not data.get('terms_accepted'):
            frappe.throw(_("Devi accettare i termini e condizioni"))
        
        # Prepare products data from form
        products_data = []
        total_price = 0
        
        # Get products from form (they can be modified by user)
        product_ids = data.get('product_ids', [])
        product_quantities = data.get('product_quantities', [])
        
        if isinstance(product_ids, str):
            product_ids = [product_ids]
        if isinstance(product_quantities, str):
            product_quantities = [int(product_quantities)]
        
        for i, product_id in enumerate(product_ids):
            if i < len(product_quantities):
                quantity = int(product_quantities[i])
                try:
                    product_doc = frappe.get_doc("CRM Product", product_id)
                    unit_price = float(product_doc.standard_rate or 0)
                    product_total = unit_price * quantity
                    
                    products_data.append({
                        "product_id": product_id,
                        "product_name": product_doc.product_name,
                        "quantity": quantity,
                        "unit_price": unit_price,
                        "total_price": product_total
                    })
                    total_price += product_total
                except Exception as e:
                    frappe.logger("crm").error(f"Error processing product {product_id}: {str(e)}")
        
        # Create CRM Lead with order details
        lead_doc = frappe.get_doc({
            "doctype": "CRM Lead",
            "first_name": data.get('customer_name'),
            "phone": data.get('phone_number'),
            "lead_source": "WhatsApp AI",
            "status": "Confirmed Order",
            "company_name": data.get('customer_name'),
            "email_id": f"whatsapp_{data.get('phone_number', '').replace('+', '')}@techloop.local",
            "custom_order_details": frappe.as_json({
                "products": products_data,
                "total_price": total_price,
                "delivery_address": data.get('delivery_address'),
                "notes": data.get('notes'),
                "confirmation_method": "WhatsApp Form",
                "temp_order_id": temp_order_id,
                "form_submission_time": frappe.utils.now()
            })
        })
        
        lead_doc.insert(ignore_permissions=True)
        
        # Mark FCRM TEMP ORDINE as consumed
        consume_temp_order(temp_order_id)
        
        # Compute public order number from Lead name, e.g. CRM-LEAD-2025-00002 -> 25-00002
        lead_name = str(lead_doc.name or "")
        try:
            parts = lead_name.split("-")
            year = parts[2]
            seq = parts[3]
            order_no = f"{year[-2:]}-{seq}"
        except Exception:
            order_no = lead_name

        # Log the order confirmation
        frappe.logger("crm").info(f"Order confirmed via WhatsApp form: {lead_doc.name}")
        
        return {
            "success": True,
            "message": _("Ordine confermato con successo"),
            "lead_id": lead_doc.name,
            "redirect_url": f"/order-success?order_no={order_no}"
        }
        
    except Exception as e:
        frappe.logger("crm").error(f"Order confirmation error: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
