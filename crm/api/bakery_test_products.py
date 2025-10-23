# Copyright (c) 2025, Techloop and Contributors
# License: MIT License

import frappe
from frappe import _


@frappe.whitelist()
def create_bakery_test_products():
    """Crea prodotti di test per una Bakery nel CRM.
    
    Questa funzione crea:
    - Tag master per le caratteristiche dei prodotti
    - 6 prodotti di test diversi con prezzi realistici
    - Associa i tag appropriati a ogni prodotto
    
    Returns:
        dict: Risultato dell'operazione con lista prodotti creati
    """
    
    try:
        print("🍰 Creazione prodotti di test per Bakery...")
        
        # Prima crea i tag master se non esistono
        created_tags = _create_bakery_tags()
        
        # Poi crea i prodotti
        products_data = [
            {
                "product_code": "CROISSANT-CLASSICO",
                "product_name": "Croissant Classico",
                "standard_rate": 1.50,
                "description": "Croissant tradizionale francese, croccante fuori e morbido dentro. Perfetto per la colazione.",
                "tags": ["tradizionale", "colazione", "burro"]
            },
            {
                "product_code": "BRIOCHE-VEGANA",
                "product_name": "Brioche Vegana",
                "standard_rate": 2.20,
                "description": "Brioche soffice e profumata, completamente vegana. Realizzata con ingredienti naturali e senza derivati animali.",
                "tags": ["vegano", "colazione", "naturale"]
            },
            {
                "product_code": "PANETTONE-SENZA-GLUTINE",
                "product_name": "Panettone Senza Glutine",
                "standard_rate": 18.00,
                "description": "Panettone artigianale senza glutine, perfetto per chi ha intolleranze. Stesso sapore tradizionale, ingredienti sicuri.",
                "tags": ["senza-glutine", "natalizio", "artigianale"]
            },
            {
                "product_code": "CANNOLI-SICILIANI",
                "product_name": "Cannoli Siciliani",
                "standard_rate": 3.50,
                "description": "Cannoli tradizionali siciliani con ricotta fresca e gocce di cioccolato. Croccanti e cremosi.",
                "tags": ["tradizionale", "siciliano", "ricotta"]
            },
            {
                "product_code": "TIRAMISU-VEGANO",
                "product_name": "Tiramisù Vegano",
                "standard_rate": 4.80,
                "description": "Tiramisù completamente vegano con mascarpone di anacardi e caffè espresso. Stesso sapore, ingredienti plant-based.",
                "tags": ["vegano", "dolce", "caffè"]
            },
            {
                "product_code": "BISCOTTI-CHOCOLATE-CHIP",
                "product_name": "Biscotti Chocolate Chip",
                "standard_rate": 2.80,
                "description": "Biscotti americani con gocce di cioccolato fondente. Croccanti fuori, morbidi dentro.",
                "tags": ["americano", "cioccolato", "biscotti"]
            }
        ]
        
        created_products = []
        updated_products = []
        
        for product_data in products_data:
            try:
                # Controlla se il prodotto esiste già
                existing = frappe.db.exists("CRM Product", {"product_code": product_data["product_code"]})
                if existing:
                    print(f"⚠️  Prodotto {product_data['product_code']} già esistente, aggiorno...")
                    product_doc = frappe.get_doc("CRM Product", existing)
                    product_doc.product_name = product_data["product_name"]
                    product_doc.standard_rate = product_data["standard_rate"]
                    product_doc.description = product_data["description"]
                    product_doc.save()
                    updated_products.append(product_doc.name)
                else:
                    # Crea nuovo prodotto
                    product_doc = frappe.get_doc({
                        "doctype": "CRM Product",
                        "product_code": product_data["product_code"],
                        "product_name": product_data["product_name"],
                        "standard_rate": product_data["standard_rate"],
                        "description": product_data["description"],
                        "disabled": 0
                    })
                    product_doc.insert()
                    print(f"✅ Creato prodotto: {product_data['product_name']}")
                    created_products.append(product_doc.name)
                
                # Aggiungi i tag al prodotto
                _add_tags_to_product(product_doc.name, product_data["tags"])
                
            except Exception as e:
                frappe.log_error(f"Errore creando prodotto {product_data['product_code']}: {str(e)}")
                return {
                    "success": False,
                    "error": f"Errore creando prodotto {product_data['product_code']}: {str(e)}"
                }
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Creati {len(created_products)} nuovi prodotti e aggiornati {len(updated_products)} esistenti",
            "created_products": created_products,
            "updated_products": updated_products,
            "created_tags": created_tags,
            "total_products": len(created_products) + len(updated_products)
        }
        
    except Exception as e:
        frappe.log_error(f"Errore generale creando prodotti bakery: {str(e)}")
        return {
            "success": False,
            "error": f"Errore generale: {str(e)}"
        }


def _create_bakery_tags():
    """Crea i tag master per le caratteristiche dei prodotti bakery."""
    
    print("🏷️  Creazione tag per caratteristiche prodotti...")
    
    tags_data = [
        {"tag_name": "tradizionale", "description": "Ricetta tradizionale", "color": "#f59e0b"},
        {"tag_name": "vegano", "description": "Senza ingredienti di origine animale", "color": "#10b981"},
        {"tag_name": "senza-glutine", "description": "Adatto a celiaci", "color": "#3b82f6"},
        {"tag_name": "colazione", "description": "Perfetto per la colazione", "color": "#f97316"},
        {"tag_name": "naturale", "description": "Ingredienti naturali", "color": "#84cc16"},
        {"tag_name": "burro", "description": "Contiene burro", "color": "#fbbf24"},
        {"tag_name": "natalizio", "description": "Prodotto natalizio", "color": "#dc2626"},
        {"tag_name": "artigianale", "description": "Fatto a mano", "color": "#7c3aed"},
        {"tag_name": "siciliano", "description": "Specialità siciliana", "color": "#ef4444"},
        {"tag_name": "ricotta", "description": "Contiene ricotta", "color": "#f3f4f6"},
        {"tag_name": "dolce", "description": "Prodotto dolce", "color": "#ec4899"},
        {"tag_name": "caffè", "description": "Contiene caffè", "color": "#92400e"},
        {"tag_name": "americano", "description": "Specialità americana", "color": "#1d4ed8"},
        {"tag_name": "cioccolato", "description": "Contiene cioccolato", "color": "#7c2d12"},
        {"tag_name": "biscotti", "description": "Tipo biscotti", "color": "#a3a3a3"}
    ]
    
    created_tags = []
    
    for tag_data in tags_data:
        try:
            # Controlla se il tag esiste già
            existing = frappe.db.exists("CRM Product Tag Master", {"tag_name": tag_data["tag_name"]})
            if existing:
                print(f"⚠️  Tag {tag_data['tag_name']} già esistente")
            else:
                # Crea nuovo tag master
                tag_doc = frappe.get_doc({
                    "doctype": "CRM Product Tag Master",
                    "tag_name": tag_data["tag_name"],
                    "description": tag_data["description"],
                    "color": tag_data["color"]
                })
                tag_doc.insert()
                print(f"✅ Creato tag: {tag_data['tag_name']}")
                created_tags.append(tag_doc.name)
                
        except Exception as e:
            frappe.log_error(f"Errore creando tag {tag_data['tag_name']}: {str(e)}")
    
    print(f"🏷️  Creati {len(created_tags)} nuovi tag!")
    return created_tags


def _add_tags_to_product(product_name: str, tag_names: list):
    """Aggiunge i tag specificati al prodotto."""
    
    try:
        product_doc = frappe.get_doc("CRM Product", product_name)
        
        # Rimuovi tag esistenti
        product_doc.product_tags = []
        
        # Aggiungi nuovi tag
        for tag_name in tag_names:
            # Verifica che il tag master esista
            tag_master = frappe.db.exists("CRM Product Tag Master", {"tag_name": tag_name})
            if tag_master:
                product_doc.append("product_tags", {
                    "tag_name": tag_master,
                    "color": frappe.get_value("CRM Product Tag Master", tag_master, "color")
                })
            else:
                print(f"⚠️  Tag master '{tag_name}' non trovato per prodotto {product_name}")
        
        product_doc.save()
        print(f"🏷️  Aggiunti {len(tag_names)} tag a {product_name}")
        
    except Exception as e:
        frappe.log_error(f"Errore aggiungendo tag a {product_name}: {str(e)}")


@frappe.whitelist()
def cleanup_bakery_test_products():
    """Rimuove tutti i prodotti di test bakery creati."""
    
    try:
        print("🧹 Pulizia prodotti di test bakery...")
        
        test_product_codes = [
            "CROISSANT-CLASSICO",
            "BRIOCHE-VEGANA", 
            "PANETTONE-SENZA-GLUTINE",
            "CANNOLI-SICILIANI",
            "TIRAMISU-VEGANO",
            "BISCOTTI-CHOCOLATE-CHIP"
        ]
        
        deleted_count = 0
        
        for product_code in test_product_codes:
            try:
                existing = frappe.db.exists("CRM Product", {"product_code": product_code})
                if existing:
                    frappe.delete_doc("CRM Product", existing)
                    print(f"🗑️  Rimosso prodotto: {product_code}")
                    deleted_count += 1
            except Exception as e:
                frappe.log_error(f"Errore rimuovendo prodotto {product_code}: {str(e)}")
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Rimossi {deleted_count} prodotti di test",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        frappe.log_error(f"Errore generale pulendo prodotti bakery: {str(e)}")
        return {
            "success": False,
            "error": f"Errore generale: {str(e)}"
        }


@frappe.whitelist()
def cleanup_bakery_test_tags():
    """Rimuove tutti i tag di test bakery creati."""
    
    try:
        print("🧹 Pulizia tag di test bakery...")
        
        test_tag_names = [
            "tradizionale", "vegano", "senza-glutine", "colazione", "naturale",
            "burro", "natalizio", "artigianale", "siciliano", "ricotta",
            "dolce", "caffè", "americano", "cioccolato", "biscotti"
        ]
        
        deleted_count = 0
        
        for tag_name in test_tag_names:
            try:
                existing = frappe.db.exists("CRM Product Tag Master", {"tag_name": tag_name})
                if existing:
                    frappe.delete_doc("CRM Product Tag Master", existing)
                    print(f"🗑️  Rimosso tag: {tag_name}")
                    deleted_count += 1
            except Exception as e:
                frappe.log_error(f"Errore rimuovendo tag {tag_name}: {str(e)}")
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Rimossi {deleted_count} tag di test",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        frappe.log_error(f"Errore generale pulendo tag bakery: {str(e)}")
        return {
            "success": False,
            "error": f"Errore generale: {str(e)}"
        }
