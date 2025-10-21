#!/usr/bin/env python3
"""
Script per correggere il modulo del doctype Temp Ordine nel database.
Esegui questo script dal bench environment.
"""

import frappe

def fix_temp_ordine_module():
    """Corregge il modulo del doctype Temp Ordine nel database."""
    try:
        # Verifica se il doctype esiste
        if not frappe.db.exists("DocType", "Temp Ordine"):
            print("❌ DocType 'Temp Ordine' non trovato nel database")
            return False
        
        # Ottieni il doctype
        doctype = frappe.get_doc("DocType", "Temp Ordine")
        
        print(f"📋 DocType trovato:")
        print(f"   Nome: {doctype.name}")
        print(f"   Modulo attuale: {doctype.module}")
        
        # Controlla se il modulo è sbagliato
        if doctype.module != "FCRM":
            print(f"🔧 Correggendo modulo da '{doctype.module}' a 'FCRM'")
            doctype.module = "FCRM"
            doctype.save()
            frappe.db.commit()
            print("✅ Modulo corretto nel database")
        else:
            print("✅ Modulo già corretto")
        
        # Verifica la correzione
        doctype.reload()
        print(f"📋 Verifica finale:")
        print(f"   Nome: {doctype.name}")
        print(f"   Modulo: {doctype.module}")
        
        return True
        
    except Exception as e:
        print(f"❌ Errore: {e}")
        return False

if __name__ == "__main__":
    fix_temp_ordine_module()
