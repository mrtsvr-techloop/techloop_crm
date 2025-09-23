#!/usr/bin/env python3

import frappe

def create_sample_tags():
    tags = ["elettronica", "smartphone", "premium", "accessori", "notebook", "gaming", "audio", "casa"]
    
    for tag in tags:
        if not frappe.db.exists("CRM Product Tag Master", tag):
            doc = frappe.get_doc({
                "doctype": "CRM Product Tag Master",
                "tag_name": tag
            })
            doc.insert()
            print(f"Created tag: {tag}")
    
    frappe.db.commit()
    print("Sample tags created!")

if __name__ == "__main__":
    create_sample_tags() 