# Copyright (c) 2025, Techloop and Contributors
# License: MIT License

import frappe
from frappe import _
import frappe.utils

no_cache = 1


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
                    # Debug logging
                    frappe.logger("crm").info(f"Loading product from temp_ordine: {product}")
                    
                    # Try to find product by ID first, then by name if ID fails
                    product_doc = None
                    try:
                        product_doc = frappe.get_doc("CRM Product", product['product_id'])
                        frappe.logger("crm").info(f"Found product by ID: {product['product_id']}")
                    except Exception:
                        # Try to find by product name
                        frappe.logger("crm").info(f"Product ID {product['product_id']} not found, searching by name")
                        products_by_name = frappe.get_all("CRM Product", 
                            filters={"product_name": ["like", f"%{product['product_id']}%"], "disabled": 0},
                            fields=["name", "product_name", "standard_rate"]
                        )
                        if products_by_name:
                            product_doc = frappe.get_doc("CRM Product", products_by_name[0].name)
                            frappe.logger("crm").info(f"Found product by name: {products_by_name[0].name}")
                        else:
                            frappe.logger("crm").error(f"Product not found by ID or name: {product['product_id']}")
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
                    
                    frappe.logger("crm").info(f"Added product to form: {product_detail}")
                except Exception as e:
                    frappe.logger("crm").error(f"Error loading product {product['product_id']}: {str(e)}")
            
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
                frappe.logger("crm").info(f"Processing products from JSON: {products_data}")
                
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
                        
                        frappe.logger("crm").info(f"Added product to table: {product_row}")
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
            
            # Debug logging
            frappe.logger("crm").info(f"Processing products - IDs: {product_ids}, Quantities: {product_quantities}")
            
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
                        
                        frappe.logger("crm").info(f"Added product to table: {product_row}")
                    except Exception as e:
                        frappe.logger("crm").error(f"Error processing product {product_id}: {str(e)}")
        
        frappe.logger("crm").info(f"Final products table: {products_table}")
        
        # Create CRM Lead with order details
        customer_full_name = f"{data.get('customer_name', '')} {data.get('customer_surname', '')}".strip()
        company_name = data.get('company_name', '') or customer_full_name
        
        # Create the lead document
        lead_doc = frappe.get_doc({
            "doctype": "CRM Lead",
            "first_name": data.get('customer_name'),
            "last_name": data.get('customer_surname'),
            "phone": data.get('phone_number'),
            "lead_source": "WhatsApp AI",
            "status": "New",
            "company_name": company_name,
            "email_id": f"whatsapp_{data.get('phone_number', '').replace('+', '')}@techloop.local",
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
        
        # Insert the lead first
        lead_doc.insert(ignore_permissions=True)
        
        # Now add products to the lead
        if products_table:
            frappe.logger("crm").info(f"Adding {len(products_table)} products to lead {lead_doc.name}")
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
                    frappe.logger("crm").info(f"Added product {product_row['product_name']} to lead")
                except Exception as e:
                    frappe.logger("crm").error(f"Error adding product {product_row['product_name']} to lead: {str(e)}")
        
        # Reload the lead to get updated totals
        lead_doc.reload()
        
        # Update totals
        lead_doc.total = total_price
        lead_doc.net_total = total_price
        lead_doc.save(ignore_permissions=True)
        
        # Update contact with form data
        try:
            from crm.api.workflow import update_contact_from_thread
            update_contact_from_thread(
                phone_from=data.get('phone_number'),
                first_name=data.get('customer_name'),
                last_name=data.get('customer_surname'),
                organization=data.get('company_name', ''),
                confirm_organization=bool(data.get('company_name'))
            )
            frappe.logger("crm").info(f"Updated contact for phone: {data.get('phone_number')}")
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
