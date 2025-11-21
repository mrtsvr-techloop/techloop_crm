#!/bin/bash
# Script per resettare tutte le viste default (List e Kanban) per CRM Lead, CRM Deal e Contact
# Sincronizza le colonne dai default definiti nel codice, inclusi tutti gli status custom per le viste Kanban

SITE="${1:-site.localhost}"

echo "🔄 Reset viste default..."
echo "=========================="
echo "Questa operazione resetta:"
echo "   - CRM Lead (List e Kanban)"
echo "   - CRM Deal (List e Kanban)"
echo "   - Contact (List)"
echo ""
echo "Tutte le viste verranno sincronizzate con le definizioni default dal database."
echo ""
read -p "Sei sicuro di voler continuare? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Operazione annullata."
    exit 1
fi

cd /workspace/frappe-bench
bench --site "$SITE" execute crm.fcrm.doctype.crm_view_settings.crm_view_settings.reset_default_views

echo ""
echo "✅ Reset completato!"



