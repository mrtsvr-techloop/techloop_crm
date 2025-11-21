#!/bin/bash
# Script per creare prodotti di default nel CRM
# Crea tag master e 6 prodotti di esempio con prezzi realistici

SITE="${1:-site.localhost}"

echo "📦 Creazione prodotti di default..."
echo "===================================="

cd /workspace/frappe-bench
bench --site "$SITE" execute crm.api.products.create_products

echo ""
echo "✅ Operazione completata!"



