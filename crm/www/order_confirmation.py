# Copyright (c) 2025, Techloop and Contributors
# License: MIT License

import frappe
from frappe import _
import frappe.utils

no_cache = 1


def find_product_by_id(product_id_raw):
    """Find CRM Product by ID with multiple fallback strategies.
    
    Tries:
    1. Direct uppercase lookup
    2. Underscore to dash conversion + uppercase
    3. Search by product name (fuzzy matching)
    
    Returns:
        Product document or None
    """
    # Try 1: Direct ID lookup (uppercase)
    try:
        return frappe.get_doc("CRM Product", product_id_raw.upper())
    except Exception:
        pass
    
    # Try 2: Direct ID lookup with underscore to dash conversion
    try:
        product_id_converted = product_id_raw.replace('_', '-').upper()
        return frappe.get_doc("CRM Product", product_id_converted)
    except Exception:
        pass
    
    # Try 3: Search by product name (convert underscore to space for better matching)
    try:
        search_term = product_id_raw.replace('_', ' ')
        
        # Search in product_name field
        products_by_name = frappe.get_all("CRM Product", 
            filters=[
                ["disabled", "=", 0],
                ["product_name", "like", f"%{search_term}%"]
            ],
            fields=["name"],
            limit=1
        )
        
        if not products_by_name:
            # Fallback: search in name field
            products_by_name = frappe.get_all("CRM Product", 
                filters=[
                    ["disabled", "=", 0],
                    ["name", "like", f"%{search_term}%"]
                ],
                fields=["name"],
                limit=1
            )
        
        if products_by_name:
            return frappe.get_doc("CRM Product", products_by_name[0].name)
    except Exception as e:
        frappe.logger("crm").error(f"Error searching product {product_id_raw}: {str(e)}")
    
    return None


def get_context():
    """Get context for order confirmation form."""
    context = frappe._dict()
    
    # Get FCRM TEMP ORDINE ID from query parameter (order_id)
    temp_order_id = frappe.form_dict.get('order_id')
    
    if temp_order_id:
        # Import FCRM TEMP ORDINE functions
        from crm.fcrm.doctype.fcrm_temp_ordine.fcrm_temp_ordine import get_temp_order_data
        
        # Get order data from FCRM TEMP ORDINE
        order_data, error = get_temp_order_data(temp_order_id)
        
        if order_data:
            context.temp_order_id = temp_order_id
            context.customer_name = order_data.get('customer_name', '')
            context.customer_surname = order_data.get('customer_surname', '')
            context.phone_number = order_data.get('phone_number', '')
            context.company_name = order_data.get('company_name', '')
            context.delivery_address = order_data.get('delivery_address', '')
            context.notes = order_data.get('notes', '')
            context.products = order_data.get('products', [])
            
            # Get product details from CRM Product
            context.product_details = []
            total_price = 0
            
            for product in context.products:
                try:
                    product_id_raw = product['product_id']
                    product_doc = find_product_by_id(product_id_raw)
                    
                    if not product_doc:
                        frappe.logger("crm").error(f"Product not found: {product_id_raw}")
                        continue
                    
                    # Get product tags
                    product_tags = []
                    for tag_row in product_doc.product_tags:
                        tag_master = frappe.get_doc("CRM Product Tag Master", tag_row.tag_name)
                        product_tags.append({
                            'name': tag_master.tag_name,
                            'color': tag_master.color
                        })
                    
                    product_detail = {
                        'id': product_doc.name,  # Use the actual product ID from database
                        'name': product_doc.product_name,
                        'quantity': product['product_quantity'],
                        'unit_price': float(product_doc.standard_rate or 0),
                        'total_price': float(product_doc.standard_rate or 0) * int(product['product_quantity']),
                        'tags': product_tags
                    }
                    context.product_details.append(product_detail)
                    total_price += product_detail['total_price']
                except Exception as e:
                    frappe.logger("crm").error(f"Error loading product {product.get('product_id')}: {str(e)}")
            
            context.total_price = total_price
            context.order_valid = True
            
            # Get all available products for the add product functionality with tags
            all_products = frappe.get_all("CRM Product", 
                fields=["name", "product_name", "standard_rate"],
                filters={"disabled": 0}
            )
            
            # Add tags to each product
            for product in all_products:
                try:
                    product_doc = frappe.get_doc("CRM Product", product.name)
                    product_tags = []
                    for tag_row in product_doc.product_tags:
                        tag_master = frappe.get_doc("CRM Product Tag Master", tag_row.tag_name)
                        product_tags.append({
                            'name': tag_master.tag_name,
                            'color': tag_master.color
                        })
                    product['tags'] = product_tags
                except Exception as e:
                    frappe.logger("crm").error(f"Error loading tags for product {product.name}: {str(e)}")
                    product['tags'] = []
            
            context.all_products = all_products
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
        required_fields = ['customer_name', 'customer_surname', 'phone_number', 'delivery_address']
        for field in required_fields:
            if not data.get(field):
                frappe.throw(_("Campo obbligatorio mancante: {0}").format(field))
        
        # Prepare products data for CRM Lead table
        products_table = []
        total_price = 0
        
        # Get products from form (they can be modified by user)
        # Try new JSON format first, fallback to old format
        products_json = data.get('products_json')
        if products_json:
            try:
                products_data = frappe.parse_json(products_json)
                
                for product_data in products_data:
                    product_id = product_data.get('product_id')
                    quantity = int(product_data.get('quantity', 1))
                    
                    try:
                        product_doc = frappe.get_doc("CRM Product", product_id)
                        unit_price = float(product_data.get('unit_price', product_doc.standard_rate or 0))
                        product_total = unit_price * quantity
                        
                        # Add to CRM Products table format
                        product_row = {
                            "product_code": product_id,
                            "product_name": product_doc.product_name,
                            "qty": quantity,
                            "rate": unit_price,
                            "amount": product_total,
                            "net_amount": product_total  # No discount for now
                        }
                        products_table.append(product_row)
                        total_price += product_total
                    except Exception as e:
                        frappe.logger("crm").error(f"Error processing product {product_id}: {str(e)}")
                        
            except Exception as e:
                frappe.logger("crm").error(f"Error parsing products JSON: {str(e)}")
                # Fallback to old method
                products_json = None
        
        # Fallback to old method if JSON parsing failed
        if not products_json:
            product_ids = data.get('product_ids', [])
            product_quantities = data.get('product_quantities', [])
            
            # Ensure we have lists
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
                        
                        # Add to CRM Products table format
                        product_row = {
                            "product_code": product_id,
                            "product_name": product_doc.product_name,
                            "qty": quantity,
                            "rate": unit_price,
                            "amount": product_total,
                            "net_amount": product_total  # No discount for now
                        }
                        products_table.append(product_row)
                        total_price += product_total
                    except Exception as e:
                        frappe.logger("crm").error(f"Error processing product {product_id}: {str(e)}")
        
        # Create CRM Lead with order details
        customer_full_name = f"{data.get('customer_name', '')} {data.get('customer_surname', '')}".strip()
        company_name = data.get('company_name', '') or customer_full_name
        
        # Normalize phone number to pretty format
        from crm.api.workflow import _normalize_phone_to_digits, _format_pretty_number
        raw_phone = data.get('phone_number', '')
        digits = _normalize_phone_to_digits(raw_phone)
        pretty_phone = _format_pretty_number(digits) if digits else raw_phone
        
        # Create the lead document
        lead_doc = frappe.get_doc({
            "doctype": "CRM Lead",
            "first_name": data.get('customer_name'),
            "last_name": data.get('customer_surname'),
            "mobile_no": pretty_phone,
            "lead_source": "WhatsApp AI",
            "status": "New",
            "total": total_price,
            "net_total": total_price,
            "custom_order_details": frappe.as_json({
                "delivery_address": data.get('delivery_address'),
                "notes": data.get('notes'),
                "confirmation_method": "WhatsApp Form",
                "temp_order_id": temp_order_id,
                "form_submission_time": frappe.utils.now(),
                "company_name": data.get('company_name', ''),
                "customer_full_name": customer_full_name
            })
        })
        
        # Add optional fields only if provided
        if data.get('email'):
            lead_doc.email = data.get('email')
        
        if data.get('website'):
            lead_doc.website = data.get('website')
        
        if data.get('company_name'):
            lead_doc.organization = data.get('company_name')
        
        # Insert the lead first
        lead_doc.insert(ignore_permissions=True)
        
        # Now add products to the lead
        if products_table:
            for product_row in products_table:
                try:
                    # Create CRM Products child document
                    product_child = frappe.get_doc({
                        "doctype": "CRM Products",
                        "parent": lead_doc.name,
                        "parenttype": "CRM Lead",
                        "parentfield": "products",
                        "product_code": product_row["product_code"],
                        "product_name": product_row["product_name"],
                        "qty": product_row["qty"],
                        "rate": product_row["rate"],
                        "amount": product_row["amount"],
                        "net_amount": product_row["net_amount"]
                    })
                    product_child.insert(ignore_permissions=True)
                except Exception as e:
                    frappe.logger("crm").error(f"Error adding product {product_row['product_name']} to lead: {str(e)}")
        
        # Reload the lead to get updated totals
        lead_doc.reload()
        
        # Update totals
        lead_doc.total = total_price
        lead_doc.net_total = total_price
        lead_doc.save(ignore_permissions=True)
        
        # Update contact with form data (only if provided)
        try:
            from crm.api.workflow import update_contact_from_thread
            
            # Build parameters dict with only provided values
            contact_params = {
                'phone_from': data.get('phone_number'),
                'first_name': data.get('customer_name'),
                'last_name': data.get('customer_surname'),
            }
            
            # Add optional fields only if provided
            if data.get('email'):
                contact_params['email'] = data.get('email')
            
            if data.get('company_name'):
                contact_params['organization'] = data.get('company_name')
                contact_params['confirm_organization'] = True
            
            update_contact_from_thread(**contact_params)
        except Exception as e:
            frappe.logger("crm").error(f"Error updating contact: {str(e)}")
        
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
