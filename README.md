Replica modificata del CRM di frappe.

## Requisiti:

- CRM
- Frappe_whatsapp
- ai_module

## Setup cliente:

### Dentro frappe:
Impostazioni sito, cambiare le informazioni del login per customizzare la login page.

### Whatsapp:
1. Creare una nuova applicazione sulla business platform di meta.
2. Successivamente come prodotto aggiungere Whatsapp.
3. Creare un ruolo ADMIN per creare un token d'accesso permanente.

### Dentro il crm:
Tenere aperta la configurazione di Whatsapp dalla meta business platform. Dalla pagina di config recuperare tutti i dati necessari:

- **token**: token
- **URL**: https://graph.facebook.com 
- **Versione**: v22.0
- **Phone id**: Scritto in chiaro sulla business platform
- **Business id**: Scritto in chiaro sulla business platform
- **App id**: Scritto in alto a sinistra sulla busines platform
- **Webhook Verify Token**: Password da usare per il token (settata da frappe, puoi mettere anche ABC e su meta metti ABC)

### Configurazione Lingua Utente
Dopo aver creato un nuovo utente, è necessario impostare la lingua su Italiano:
- Vai su **Utenti** → **User Details** → **Lingua**
- Seleziona **Italiano** come lingua

### Configurazione Brand e Valuta
Nel CRM, in alto a sinistra, clicca su **Impostazioni** per configurare:
- **Brand name**: Nome del brand
- **Valuta**: Valuta principale del CRM (una volta impostata, non può essere modificata)
- **Brand Settings**: Logo, favicon e altre impostazioni del brand

## Script Bash per Sviluppatori

Gli script bash per le funzioni amministrative sono disponibili nella directory `scripts/`.

### Come Eseguire gli Script

**Opzione 1: Dalla directory `apps/crm/`**
```bash
cd /workspace/frappe-bench/apps/crm
./scripts/reset_crm_database.sh [site_name]
```

**Opzione 2: Con path completo**
```bash
/workspace/frappe-bench/apps/crm/scripts/reset_crm_database.sh [site_name]
```

**Opzione 3: Dalla root del bench**
```bash
cd /workspace/frappe-bench
./apps/crm/scripts/reset_crm_database.sh [site_name]
```

**Nota:** Se non specifichi il nome del sito, verrà usato `site.localhost` come default.

### Reset Database CRM
Pulisce completamente il database CRM eliminando tutti i dati operativi (Deals, Leads, Contacts, Organizations, Products, Tags, Notes, Call Logs, Tasks).

```bash
# Dalla directory apps/crm/
./scripts/reset_crm_database.sh

# Con nome sito specifico
./scripts/reset_crm_database.sh site.localhost

# Con path completo
/workspace/frappe-bench/apps/crm/scripts/reset_crm_database.sh site.localhost
```

**⚠️ ATTENZIONE:** Questo script richiede conferma interattiva prima di procedere.

### Crea Prodotti Default
Crea prodotti di default nel CRM con tag master e 6 prodotti di esempio.

```bash
# Dalla directory apps/crm/
./scripts/create_default_products.sh

# Con nome sito specifico
./scripts/create_default_products.sh site.localhost

# Con path completo
/workspace/frappe-bench/apps/crm/scripts/create_default_products.sh site.localhost
```

### Reset Viste Default
Resetta tutte le viste default (List e Kanban) per CRM Lead, CRM Deal e Contact, sincronizzando le colonne dai default definiti nel codice.

```bash
# Dalla directory apps/crm/
./scripts/reset_default_views.sh

# Con nome sito specifico
./scripts/reset_default_views.sh site.localhost

# Con path completo
/workspace/frappe-bench/apps/crm/scripts/reset_default_views.sh site.localhost
```

**⚠️ ATTENZIONE:** Questo script richiede conferma interattiva prima di procedere.

### Popola Database con Dati di Test
Popola il database CRM con dati di test realistici: Lead, Deal, Contatti, Aziende, Ordini e Prodotti ordinati.

```bash
# Dalla directory apps/crm/
./scripts/populate_test_data.sh [site_name] [count]

# Esempio: crea 20 ordini di test
./scripts/populate_test_data.sh site.localhost 20

# Esempio: crea 50 ordini di test
./scripts/populate_test_data.sh site.localhost 50

# Con path completo
/workspace/frappe-bench/apps/crm/scripts/populate_test_data.sh site.localhost 20
```

**Parametri:**
- `site_name` (opzionale): Nome del sito (default: `site.localhost`)
- `count` (opzionale): Numero di ordini da creare (default: `20`)

**Cosa crea:**
- **Contatti**: Uno per ogni ordine
- **Aziende**: 50% dei contatti avranno un'azienda associata
- **Lead**: Uno per ogni ordine (con prodotti ordinati)
- **Deal**: Uno per ogni ordine (con prodotti ordinati)
- **Prodotti ordinati**: 1-4 prodotti casuali per ogni Lead/Deal

**Esempio:** Con `count=40` creerà esattamente 40 Contatti, 40 Lead e 40 Deal.

**⚠️ ATTENZIONE:** Questo script richiede conferma interattiva prima di procedere.

## Import Prodotti da JSON

Puoi importare prodotti nel CRM tramite JSON dalla pagina **Listino Prodotti** usando il bottone "Importa da JSON".

### Formato JSON

Il JSON deve essere un array di oggetti prodotto con i seguenti campi:

- **product_code** (obbligatorio): Codice univoco del prodotto
- **product_name** (obbligatorio): Nome del prodotto
- **standard_rate** (opzionale): Prezzo del prodotto (default: 0.00)
- **description** (opzionale): Descrizione del prodotto
- **tags** (opzionale): Array di nomi tag (devono esistere come CRM Product Tag Master)

### Esempio

Vedi il file `products_import_example.json` nella root del progetto per un esempio completo.

**Esempio minimo:**
```json
[
  {
    "product_code": "PROD-001",
    "product_name": "Nome Prodotto",
    "standard_rate": 10.00,
    "description": "Descrizione prodotto",
    "tags": ["tag1", "tag2"]
  }
]
```

**Note:**
- Se un prodotto con lo stesso `product_code` esiste già, verrà aggiornato
- **I tag vengono creati automaticamente** se non esistono come CRM Product Tag Master
- I tag creati automaticamente avranno un colore generato automaticamente basato sul nome del tag
- Se un tag esiste già, verrà riutilizzato (non verrà sovrascritto)
