#!/bin/bash
# Script per pulire completamente il database CRM
# Elimina tutti i dati operativi (Deals, Leads, Contacts, Organizations, Products, Tags, Notes, Call Logs, Tasks)
# NON elimina: Status, Settings, Users, Permissions

SITE="${1:-site.localhost}"

echo "🧹 Pulizia completa database CRM..."
echo "====================================="
echo "⚠️  ATTENZIONE: Questa operazione eliminerà TUTTI i dati operativi!"
echo "   - Deals e Leads"
echo "   - Contacts e Organizations"
echo "   - Products e Tags"
echo "   - Notes e Call Logs"
echo "   - Tasks"
echo ""
echo "   NON verranno eliminati:"
echo "   - Status (Lead Status, Deal Status)"
echo "   - Impostazioni di sistema"
echo "   - Utenti e permessi"
echo "   - Configurazioni"
echo ""
read -p "Sei sicuro di voler continuare? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "❌ Operazione annullata."
    exit 1
fi

cd /workspace/frappe-bench
bench --site "$SITE" execute crm.api.products.reset_crm_database

echo ""
echo "✅ Pulizia completata!"



