# 🍰 Prodotti di Test Bakery per CRM

Questo modulo contiene funzioni per creare e gestire prodotti di test per una Bakery nel CRM Frappe.

## 📋 Prodotti Creati

La funzione crea **6 prodotti diversi** con caratteristiche realistiche:

1. **Croissant Classico** (€1.50) - Tradizionale, colazione, burro
2. **Brioche Vegana** (€2.20) - Vegano, colazione, naturale  
3. **Panettone Senza Glutine** (€18.00) - Senza glutine, natalizio, artigianale
4. **Cannoli Siciliani** (€3.50) - Tradizionale, siciliano, ricotta
5. **Tiramisù Vegano** (€4.80) - Vegano, dolce, caffè
6. **Biscotti Chocolate Chip** (€2.80) - Americano, cioccolato, biscotti

## 🏷️ Tag Creati

Vengono creati **15 tag** per le caratteristiche dei prodotti:

- **tradizionale** - Ricetta tradizionale
- **vegano** - Senza ingredienti di origine animale  
- **senza-glutine** - Adatto a celiaci
- **colazione** - Perfetto per la colazione
- **naturale** - Ingredienti naturali
- **burro** - Contiene burro
- **natalizio** - Prodotto natalizio
- **artigianale** - Fatto a mano
- **siciliano** - Specialità siciliana
- **ricotta** - Contiene ricotta
- **dolce** - Prodotto dolce
- **caffè** - Contiene caffè
- **americano** - Specialità americana
- **cioccolato** - Contiene cioccolato
- **biscotti** - Tipo biscotti

## 🚀 Come Usare

### Metodo 1: Script Bash (Raccomandato)

```bash
# Crea i prodotti di test
./create_bakery_products.sh

# Pulisce i prodotti di test
./cleanup_bakery_products.sh
```

### Metodo 2: Comando Bench

```bash
# Crea i prodotti di test
bench --site site.localhost execute crm.api.bakery_test_products.create_bakery_test_products

# Pulisce i prodotti di test
bench --site site.localhost execute crm.api.bakery_test_products.cleanup_bakery_test_products

# Pulisce solo i tag
bench --site site.localhost execute crm.api.bakery_test_products.cleanup_bakery_test_tags
```

### Metodo 3: API Call

```python
import frappe

# Crea prodotti
result = frappe.call("crm.api.bakery_test_products.create_bakery_test_products")
print(result)

# Pulisce prodotti
result = frappe.call("crm.api.bakery_test_products.cleanup_bakery_test_products")
print(result)
```

## 📁 File Creati

- `apps/crm/crm/api/bakery_test_products.py` - Funzioni API Frappe
- `apps/crm/create_bakery_test_products.py` - Script standalone Python
- `create_bakery_products.sh` - Script bash per creare prodotti
- `cleanup_bakery_products.sh` - Script bash per pulire prodotti

## 🔧 Funzioni Disponibili

### `create_bakery_test_products()`
Crea tutti i prodotti e tag di test per la bakery.

**Returns:**
```json
{
    "success": true,
    "message": "Creati 6 nuovi prodotti e aggiornati 0 esistenti",
    "created_products": ["CROISSANT-CLASSICO", "BRIOCHE-VEGANA", ...],
    "updated_products": [],
    "created_tags": ["tradizionale", "vegano", ...],
    "total_products": 6
}
```

### `cleanup_bakery_test_products()`
Rimuove tutti i prodotti di test bakery.

**Returns:**
```json
{
    "success": true,
    "message": "Rimossi 6 prodotti di test",
    "deleted_count": 6
}
```

### `cleanup_bakery_test_tags()`
Rimuove tutti i tag di test bakery.

**Returns:**
```json
{
    "success": true,
    "message": "Rimossi 15 tag di test",
    "deleted_count": 15
}
```

## ⚠️ Note Importanti

- I prodotti vengono creati con **codici unici** per evitare duplicati
- Se un prodotto esiste già, viene **aggiornato** invece che duplicato
- I tag hanno **colori specifici** per il frontend CRM
- Tutte le operazioni sono **transazionali** (rollback in caso di errore)
- I prodotti sono **abilitati** per default (non disabled)

## 🎯 Utilizzo per Test

Questi prodotti sono perfetti per:
- Testare il form di ordine WhatsApp
- Verificare la selezione prodotti tramite lista
- Testare i filtri per tag nel CRM
- Demo del sistema di ordini
- Test dell'AI assistant con prodotti realistici

## 🔄 Aggiornamenti

Per aggiornare i prodotti esistenti, basta rieseguire la funzione `create_bakery_test_products()` - aggiornerà automaticamente i prodotti esistenti con i nuovi dati.
