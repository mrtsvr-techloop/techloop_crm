import frappe
from frappe import _

@frappe.whitelist()
def get_product_with_tags(name):
    """Get a product with its tags"""
    try:
        product = frappe.get_doc("CRM Product", name)
        product_dict = product.as_dict()
        
        # Get tags manually if child table has issues
        try:
            tags = frappe.db.get_all("CRM Product Tag", 
                                   filters={"parent": name},
                                   fields=["tag_name"])
            product_dict["product_tags"] = tags
        except Exception:
            product_dict["product_tags"] = []
            
        return product_dict
    except Exception as e:
        frappe.throw(str(e))

@frappe.whitelist()
def create_product_with_tags(product_data):
    """Create a product with tags"""
    try:
        # Remove tags from product data
        tags_data = product_data.pop("product_tags", [])
        
        # Create the product
        product = frappe.get_doc({
            "doctype": "CRM Product",
            **product_data
        })
        product.insert()
        
        # Add tags if any
        for tag_row in tags_data:
            if tag_row.get("tag_name"):
                try:
                    # Check if tag master exists, create if not
                    if not frappe.db.exists("CRM Product Tag Master", tag_row["tag_name"]):
                        tag_master = frappe.get_doc({
                            "doctype": "CRM Product Tag Master",
                            "tag_name": tag_row["tag_name"]
                        })
                        tag_master.insert()
                    
                    # Create tag link
                    frappe.db.sql("""
                        INSERT INTO `tabCRM Product Tag` 
                        (name, parent, parenttype, parentfield, tag_name, creation, modified, owner, modified_by)
                        VALUES (%(name)s, %(parent)s, 'CRM Product', 'product_tags', %(tag_name)s, NOW(), NOW(), %(user)s, %(user)s)
                    """, {
                        "name": frappe.generate_hash(length=10),
                        "parent": product.name,
                        "tag_name": tag_row["tag_name"],
                        "user": frappe.session.user
                    })
                except Exception as e:
                    frappe.log_error(f"Error creating tag: {str(e)}")
        
        frappe.db.commit()
        return product.as_dict()
        
    except Exception as e:
        frappe.db.rollback()
        frappe.throw(str(e))

@frappe.whitelist()
def update_product_with_tags(name, product_data):
    """Update a product with tags"""
    try:
        # Get the product
        product = frappe.get_doc("CRM Product", name)
        
        # Remove tags from product data
        tags_data = product_data.pop("product_tags", [])
        
        # Update product fields
        for field, value in product_data.items():
            if hasattr(product, field):
                setattr(product, field, value)
        
        product.save()
        
        # Delete existing tags
        frappe.db.sql("DELETE FROM `tabCRM Product Tag` WHERE parent = %s", name)
        
        # Add new tags
        for tag_row in tags_data:
            if tag_row.get("tag_name"):
                try:
                    # Check if tag master exists, create if not
                    if not frappe.db.exists("CRM Product Tag Master", tag_row["tag_name"]):
                        tag_master = frappe.get_doc({
                            "doctype": "CRM Product Tag Master",
                            "tag_name": tag_row["tag_name"]
                        })
                        tag_master.insert()
                    
                    # Create tag link
                    frappe.db.sql("""
                        INSERT INTO `tabCRM Product Tag` 
                        (name, parent, parenttype, parentfield, tag_name, creation, modified, owner, modified_by)
                        VALUES (%(name)s, %(parent)s, 'CRM Product', 'product_tags', %(tag_name)s, NOW(), NOW(), %(user)s, %(user)s)
                    """, {
                        "name": frappe.generate_hash(length=10),
                        "parent": product.name,
                        "tag_name": tag_row["tag_name"],
                        "user": frappe.session.user
                    })
                except Exception as e:
                    frappe.log_error(f"Error creating tag: {str(e)}")
        
        frappe.db.commit()
        return product.as_dict()
        
    except Exception as e:
        frappe.db.rollback()
        frappe.throw(str(e))

@frappe.whitelist()
def delete_product_safe(name):
    """Safely delete a product"""
    try:
        # Delete tags first
        frappe.db.sql("DELETE FROM `tabCRM Product Tag` WHERE parent = %s", name)
        
        # Delete the product
        frappe.delete_doc("CRM Product", name)
        
        frappe.db.commit()
        return {"success": True}
        
    except Exception as e:
        frappe.db.rollback()
        frappe.throw(str(e)) 