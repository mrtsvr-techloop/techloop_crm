# Copyright (c) 2025, Techloop and Contributors
# License: MIT License

import frappe
from frappe import _


def reset_crm_database():
    """
    Pulisce completamente il database CRM eliminando tutti i dati operativi.
    
    Elimina:
    - Tutti i Deal e Lead
    - Tutti i Contact e Organization
    - Tutti i Product e Product Tags
    - Tutti i Notes e Call Logs
    - Tutti i Task
    - Tutti i CRM Products (child table)
    
    NON elimina:
    - Status (Lead Status, Deal Status)
    - Impostazioni di sistema
    - Utenti e permessi
    - Configurazioni
    
    ATTENZIONE: Questa funzione elimina TUTTI i dati operativi!
    
    NOTA: Questa funzione NON è esposta come API. Può essere eseguita solo tramite:
    - bench --site <site> execute crm.api.products.reset_crm_database
    
    Returns:
        dict: Risultato dell'operazione con statistiche
    """
    
    try:
        print("🧹 Pulizia completa database CRM...")
        
        deleted_stats = {
            "deals": 0,
            "leads": 0,
            "contacts": 0,
            "organizations": 0,
            "products": 0,
            "product_tags": 0,
            "product_tag_masters": 0,
            "notes": 0,
            "call_logs": 0,
            "tasks": 0,
        }
        
        # Lista dei doctype da eliminare
        doctypes_to_delete = [
            ("CRM Deal", "deals"),
            ("CRM Lead", "leads"),
            ("Contact", "contacts"),
            ("CRM Organization", "organizations"),
            ("CRM Product", "products"),
            ("CRM Product Tag", "product_tags"),
            ("CRM Product Tag Master", "product_tag_masters"),
            ("FCRM Note", "notes"),
            ("CRM Call Log", "call_logs"),
            ("CRM Task", "tasks"),
        ]
        
        # Prima elimina tutti i CRM Products (child table) che potrebbero essere collegati
        print("🗑️  Eliminazione CRM Products (child table)...")
        if frappe.db.exists("DocType", "CRM Products"):
            crm_products = frappe.get_all("CRM Products", pluck="name")
            for product_name in crm_products:
                try:
                    frappe.delete_doc("CRM Products", product_name, force=True, ignore_permissions=True)
                except Exception as e:
                    frappe.log_error(f"Errore eliminando CRM Products {product_name}: {str(e)}")
        
        # Poi elimina i doctype principali
        for doctype, stat_key in doctypes_to_delete:
            if not frappe.db.exists("DocType", doctype):
                print(f"⚠️  Doctype {doctype} non trovato, salto...")
                continue
            
            print(f"🗑️  Eliminazione {doctype}...")
            docs = frappe.get_all(doctype, pluck="name")
            for doc_name in docs:
                try:
                    frappe.delete_doc(doctype, doc_name, force=True, ignore_permissions=True)
                    deleted_stats[stat_key] += 1
                except Exception as e:
                    frappe.log_error(f"Errore eliminando {doctype} {doc_name}: {str(e)}")
        
        frappe.db.commit()
        
        total_deleted = sum(deleted_stats.values())
        print(f"✅ Pulizia completata: {total_deleted} documenti eliminati")
        
        return {
            "success": True,
            "message": f"Database pulito con successo! Eliminati {total_deleted} documenti.",
            "deleted": deleted_stats,
            "summary": deleted_stats
        }
        
    except Exception as e:
        frappe.log_error(f"Errore generale durante pulizia database: {str(e)}")
        frappe.db.rollback()
        return {
            "success": False,
            "error": f"Errore generale: {str(e)}"
        }


def create_products():
    """
    Crea prodotti di default nel CRM.
    
    Questa funzione crea:
    - Tag master per le caratteristiche dei prodotti
    - 6 prodotti di esempio con prezzi realistici
    - Associa i tag appropriati a ogni prodotto
    
    NOTA: Questa funzione NON è esposta come API. Può essere eseguita solo tramite:
    - bench --site <site> execute crm.api.products.create_products
    
    Returns:
        dict: Risultato dell'operazione con lista prodotti creati
    """
    
    try:
        print("📦 Creazione prodotti...")
        
        # Prima crea i tag master se non esistono
        created_tags = _create_default_tags()
        
        # Poi crea i prodotti
        products_data = [
            {
                "product_code": "EXTRA-CHOCOLATE",
                "product_name": "Extra chocolate",
                "standard_rate": 40.00,
                "description": "Impasto al cioccolato con cubetti di cioccolato fondente. Disponibile solo in formato da 1KG.",
                "tags": ["limited-edition", "cioccolato", "cioccolato-fondente", "1kg"]
            },
            {
                "product_code": "CARAMELLO-CAFFE",
                "product_name": "Caramello e caffè",
                "standard_rate": 45.00,
                "description": "Impasto al caramello con cubetti di caramello mau e glassa al caffè. Con vasetto di caramello salato al caffè. Disponibile solo in formato da 1KG.",
                "tags": ["limited-edition", "caramello", "caffè", "1kg"]
            },
            {
                "product_code": "ORO-VERDE",
                "product_name": "Oro verde",
                "standard_rate": 50.00,
                "description": "Pistacchio e cioccolato bianco Valrhona. Senza lattosio. Disponibile solo in formato da 1KG.",
                "tags": ["limited-edition", "pistacchio", "cioccolato-bianco", "senza-lattosio", "1kg"]
            },
            {
                "product_code": "DONNA-MARIA",
                "product_name": "Donna Maria",
                "standard_rate": 38.00,
                "description": "Mela Annurca semicondita e impasto alla cannella. Senza lattosio. Disponibile solo in formato da 1KG.",
                "tags": ["mela-annurca", "cannella", "senza-lattosio", "1kg"]
            },
            {
                "product_code": "PANDORO-ARTIGIANALE",
                "product_name": "Pandoro Artigianale",
                "standard_rate": 35.00,
                "description": "Con vaniglia thaithiensis e scorza di arancia navel condita. Senza lattosio. Disponibile solo in formato da 1KG.",
                "tags": ["limited-edition", "vaniglia", "arancia-navel", "senza-lattosio", "1kg", "artigianale"]
            },
            {
                "product_code": "PANETTONE-TRADIZIONALE",
                "product_name": "Panettone tradizionale",
                "standard_rate": 38.00,
                "description": "Arancia Navel candita e uvetta. Senza lattosio. Disponibile solo in formato da 1KG.",
                "tags": ["arancia-navel", "uvetta", "senza-lattosio", "1kg", "tradizionale"]
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
        frappe.log_error(f"Errore generale creando prodotti: {str(e)}")
        return {
            "success": False,
            "error": f"Errore generale: {str(e)}"
        }


def _create_default_tags():
    """Crea i tag master per le caratteristiche dei prodotti."""
    
    print("🏷️  Creazione tag per caratteristiche prodotti...")
    
    tags_data = [
        {"tag_name": "limited-edition", "description": "Edizione limitata", "color": "#dc2626"},
        {"tag_name": "1kg", "description": "Formato da 1KG", "color": "#3b82f6"},
        {"tag_name": "senza-lattosio", "description": "Senza lattosio", "color": "#10b981"},
        {"tag_name": "cioccolato", "description": "Contiene cioccolato", "color": "#7c2d12"},
        {"tag_name": "cioccolato-fondente", "description": "Cioccolato fondente", "color": "#92400e"},
        {"tag_name": "cioccolato-bianco", "description": "Cioccolato bianco", "color": "#fbbf24"},
        {"tag_name": "caramello", "description": "Contiene caramello", "color": "#f59e0b"},
        {"tag_name": "caffè", "description": "Contiene caffè", "color": "#92400e"},
        {"tag_name": "pistacchio", "description": "Contiene pistacchio", "color": "#84cc16"},
        {"tag_name": "mela-annurca", "description": "Mela Annurca", "color": "#f97316"},
        {"tag_name": "cannella", "description": "Contiene cannella", "color": "#a16207"},
        {"tag_name": "vaniglia", "description": "Contiene vaniglia", "color": "#fef3c7"},
        {"tag_name": "arancia-navel", "description": "Arancia Navel", "color": "#f97316"},
        {"tag_name": "uvetta", "description": "Contiene uvetta", "color": "#7c2d12"},
        {"tag_name": "artigianale", "description": "Fatto a mano", "color": "#7c3aed"},
        {"tag_name": "tradizionale", "description": "Ricetta tradizionale", "color": "#f59e0b"}
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


def _create_or_get_tag_master(tag_name: str, color: str = None):
    """
    Crea un tag master se non esiste, altrimenti lo restituisce.
    
    Args:
        tag_name: Nome del tag
        color: Colore del tag in formato hex (es. "#dc2626"). Se None, usa un colore default.
        
    Returns:
        str: Nome del documento CRM Product Tag Master
    """
    # Verifica se il tag esiste già
    existing = frappe.db.exists("CRM Product Tag Master", {"tag_name": tag_name})
    if existing:
        return existing
    
    # Colore default se non specificato
    if not color:
        # Genera un colore basato sul nome del tag (hash semplice)
        import hashlib
        hash_obj = hashlib.md5(tag_name.encode())
        hash_hex = hash_obj.hexdigest()[:6]
        color = f"#{hash_hex}"
    
    # Crea nuovo tag master
    try:
        tag_doc = frappe.get_doc({
            "doctype": "CRM Product Tag Master",
            "tag_name": tag_name,
            "description": tag_name.replace("-", " ").title(),
            "color": color
        })
        tag_doc.insert()
        print(f"✅ Creato tag master: {tag_name}")
        return tag_doc.name
    except Exception as e:
        frappe.log_error(f"Errore creando tag master '{tag_name}': {str(e)}")
        raise


def _add_tags_to_product(product_name: str, tag_names: list, auto_create_tags: bool = True):
    """
    Aggiunge i tag specificati al prodotto.
    
    Args:
        product_name: Nome del documento CRM Product
        tag_names: Lista di nomi tag da aggiungere
        auto_create_tags: Se True, crea automaticamente i tag master se non esistono
    """
    
    try:
        product_doc = frappe.get_doc("CRM Product", product_name)
        
        # Rimuovi tag esistenti
        product_doc.product_tags = []
        
        # Aggiungi nuovi tag
        for tag_name in tag_names:
            try:
                if auto_create_tags:
                    # Crea il tag master se non esiste
                    tag_master = _create_or_get_tag_master(tag_name)
                else:
                    # Verifica che il tag master esista
                    tag_master = frappe.db.exists("CRM Product Tag Master", {"tag_name": tag_name})
                    if not tag_master:
                        print(f"⚠️  Tag master '{tag_name}' non trovato per prodotto {product_name}")
                        continue
                
                # Aggiungi il tag al prodotto
                tag_color = frappe.get_value("CRM Product Tag Master", tag_master, "color")
                product_doc.append("product_tags", {
                    "tag_name": tag_master,
                    "color": tag_color
                })
            except Exception as e:
                frappe.log_error(f"Errore processando tag '{tag_name}' per prodotto {product_name}: {str(e)}")
        
        product_doc.save()
        print(f"🏷️  Aggiunti {len([t for t in tag_names if t])} tag a {product_name}")
        
    except Exception as e:
        frappe.log_error(f"Errore aggiungendo tag a {product_name}: {str(e)}")


@frappe.whitelist()
def import_products_from_json(products_json: str):
    """
    Importa prodotti da un JSON.
    
    Formato JSON atteso:
    [
        {
            "product_code": "PROD-001",              # OBBLIGATORIO: Codice univoco del prodotto
            "product_name": "Nome Prodotto",         # OBBLIGATORIO: Nome del prodotto
            "standard_rate": 10.00,                  # Opzionale: Prezzo (default: 0.00)
            "description": "Descrizione prodotto",   # Opzionale: Descrizione del prodotto
            "tags": ["tag1", "tag2"]                 # Opzionale: Lista di nomi tag (devono esistere come CRM Product Tag Master)
        }
    ]
    
    Esempio completo:
    [
        {
            "product_code": "EXTRA-CHOCOLATE",
            "product_name": "Extra chocolate",
            "standard_rate": 40.00,
            "description": "Impasto al cioccolato con cubetti di cioccolato fondente. Disponibile solo in formato da 1KG.",
            "tags": ["limited-edition", "cioccolato", "cioccolato-fondente", "1kg"]
        },
        {
            "product_code": "PROD-SEMPLICE",
            "product_name": "Prodotto Semplice",
            "standard_rate": 25.50,
            "description": "Un prodotto senza tag opzionali"
        },
        {
            "product_code": "PROD-MINIMO",
            "product_name": "Prodotto Minimo",
            "standard_rate": 15.00
        }
    ]
    
    Note:
    - Se un prodotto con lo stesso product_code esiste già, verrà aggiornato
    - I tag vengono creati automaticamente se non esistono come CRM Product Tag Master
    - I tag creati automaticamente avranno un colore generato automaticamente basato sul nome
    - Vedi products_import_example.json per un esempio completo
    
    Args:
        products_json: Stringa JSON contenente l'array di prodotti
        
    Returns:
        dict: Risultato dell'operazione con statistiche:
            {
                "success": True/False,
                "message": "Messaggio descrittivo",
                "created_products": ["PROD-001", "PROD-002"],
                "updated_products": ["PROD-003"],
                "errors": ["Lista errori se presenti"]
            }
    """
    frappe.only_for("System Manager")
    
    try:
        import json
        
        # Parse JSON
        try:
            products_data = json.loads(products_json)
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON non valido: {str(e)}"
            }
        
        if not isinstance(products_data, list):
            return {
                "success": False,
                "error": "Il JSON deve contenere un array di prodotti"
            }
        
        created_products = []
        updated_products = []
        errors = []
        
        for idx, product_data in enumerate(products_data):
            try:
                # Validazione campi obbligatori
                if not product_data.get("product_code"):
                    errors.append(f"Prodotto {idx + 1}: product_code mancante")
                    continue
                
                if not product_data.get("product_name"):
                    errors.append(f"Prodotto {idx + 1}: product_name mancante")
                    continue
                
                product_code = product_data["product_code"]
                product_name = product_data["product_name"]
                standard_rate = float(product_data.get("standard_rate", 0))
                description = product_data.get("description", "")
                tags = product_data.get("tags", [])
                
                # Controlla se il prodotto esiste già
                existing = frappe.db.exists("CRM Product", {"product_code": product_code})
                
                if existing:
                    # Aggiorna prodotto esistente
                    product_doc = frappe.get_doc("CRM Product", existing)
                    product_doc.product_name = product_name
                    product_doc.standard_rate = standard_rate
                    product_doc.description = description
                    product_doc.save()
                    updated_products.append(product_doc.name)
                else:
                    # Crea nuovo prodotto
                    product_doc = frappe.get_doc({
                        "doctype": "CRM Product",
                        "product_code": product_code,
                        "product_name": product_name,
                        "standard_rate": standard_rate,
                        "description": description,
                        "disabled": 0
                    })
                    product_doc.insert()
                    created_products.append(product_doc.name)
                
                # Aggiungi i tag se specificati
                if tags:
                    _add_tags_to_product(product_doc.name, tags)
                
            except Exception as e:
                error_msg = f"Errore processando prodotto {idx + 1} ({product_data.get('product_code', 'N/A')}): {str(e)}"
                errors.append(error_msg)
                frappe.log_error(error_msg)
        
        frappe.db.commit()
        
        return {
            "success": True,
            "message": f"Importati {len(created_products)} nuovi prodotti e aggiornati {len(updated_products)} esistenti",
            "created_products": created_products,
            "updated_products": updated_products,
            "errors": errors if errors else None
        }
        
    except Exception as e:
        frappe.log_error(f"Errore generale durante import prodotti: {str(e)}")
        frappe.db.rollback()
        return {
            "success": False,
            "error": f"Errore generale: {str(e)}"
        }

