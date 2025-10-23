#!/bin/bash
# Script per creare prodotti di test bakery nel CRM

echo "🍰 Creazione prodotti di test per Bakery..."
echo "=============================================="

# Esegui la funzione Frappe
cd /workspace/frappe-bench
bench --site site.localhost execute crm.api.bakery_test_products.create_bakery_test_products

echo ""
echo "✅ Operazione completata!"
echo ""
echo "Per pulire i prodotti di test, esegui:"
echo "bench --site site.localhost execute crm.api.bakery_test_products.cleanup_bakery_test_products"
