#!/bin/bash
# Script per popolare il database CRM con dati di test
# Crea: Lead, Deal, Contatti, Aziende, Ordini e Prodotti ordinati

SITE="${1:-site.localhost}"
COUNT="${2:-20}"

echo "📦 Popolamento database CRM con dati di test..."
echo "================================================"
echo "Sito: $SITE"
echo "Numero di ordini da creare: $COUNT"
echo ""
echo "Questo script creerà:"
echo "   - Contatti (uno per ogni ordine)"
echo "   - Aziende (50% dei contatti avranno un'azienda)"
echo "   - Lead (uno per ogni ordine, con prodotti ordinati)"
echo "   - Deal (uno per ogni ordine, con prodotti ordinati)"
echo "   - Prodotti ordinati (1-4 prodotti per Lead/Deal)"
echo ""
read -p "Vuoi continuare? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Operazione annullata."
    exit 1
fi

cd /workspace/frappe-bench
bench --site "$SITE" execute crm.api.generate_test_data.generate_test_data --kwargs "{'count': $COUNT}"

echo ""
echo "✅ Popolamento completato!"

