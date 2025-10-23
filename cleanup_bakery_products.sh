#!/bin/bash
# Script per pulire i prodotti di test bakery dal CRM

echo "🧹 Pulizia prodotti di test Bakery..."
echo "====================================="

# Esegui la funzione di pulizia Frappe
cd /workspace/frappe-bench
bench --site site.localhost execute crm.api.bakery_test_products.cleanup_bakery_test_products

echo ""
echo "✅ Pulizia completata!"
