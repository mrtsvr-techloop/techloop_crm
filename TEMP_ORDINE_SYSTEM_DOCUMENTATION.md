# Sistema Temp Ordine - Documentazione Tecnica

**Data:** 20 Gennaio 2025  
**Versione:** 1.0  
**Autore:** AI Assistant  
**Modulo:** CRM - Temp Ordine System  

## 📋 Panoramica

Il sistema **Temp Ordine** è stato implementato per gestire in modo sicuro e temporaneo le conferme d'ordine generate dall'AI via WhatsApp. Questo sistema risolve il problema dei conflitti di ID e delle sessioni scadute durante il processo di conferma ordini.

## 🎯 Problema Risolto

### **Problema Originale:**
- L'AI generava link con query parameters lunghi e complessi
- Non c'era gestione delle sessioni temporanee
- Possibili conflitti se più clienti tentavano di confermare ordini simultaneamente
- Nessun controllo sulla scadenza dei link di conferma

### **Soluzione Implementata:**
- **DocType temporaneo** per gestire sessioni ordine
- **Link corti** usando ID Frappe invece di query parameters
- **Scadenza automatica** dopo 5 minuti (Unix timestamp)
- **Gestione atomica** del consumo dei record

## 🏗️ Architettura del Sistema

### **1. DocType `Temp Ordine`**

**Percorso:** `crm/fcrm/doctype/temp_ordine/`

**Struttura:**
```json
{
  "name": "Temp Ordine",
  "module": "CRM",
  "fields": [
    {
      "fieldname": "order_data",
      "fieldtype": "JSON",
      "description": "Dati completi dell'ordine"
    },
    {
      "fieldname": "created_at", 
      "fieldtype": "Int",
      "description": "Unix timestamp creazione"
    },
    {
      "fieldname": "expires_at",
      "fieldtype": "Int", 
      "description": "Unix timestamp scadenza (+300 secondi)"
    },
    {
      "fieldname": "status",
      "fieldtype": "Select",
      "options": "Active|Consumed|Expired"
    }
  ]
}
```

**Vantaggi Unix Timestamp:**
- ✅ Standard universale (secondi dal 1/1/1970 UTC)
- ✅ Calcoli semplici: `expires_at = created_at + 300`
- ✅ Comparazioni efficienti: `if current_time > expires_at`
- ✅ Timezone indipendente
- ✅ Database ottimizzato (integer, indicizzabile)

### **2. Tool AI Aggiornato**

**File:** `CRM_AI_MODULE/ai_module/agents/tools/generate_order_form.py`

**Schema Aggiornato:**
```python
"products": {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "product_id": {"type": "string"},
            "product_quantity": {"type": "integer", "minimum": 1}
        }
    }
}
```

**Flusso:**
1. AI chiama tool con `products` array
2. Tool crea `Temp Ordine` record
3. Tool ritorna link corto: `/order_confirmation/{temp_order_id}`
4. AI invia link WhatsApp al cliente

### **3. Form Dinamico**

**File:** `techloop_crm/crm/www/order_confirmation.py`

**Funzionalità:**
- Legge dati da `Temp Ordine` invece che da query params
- Carica prodotti dal DB usando `product_id`
- Calcola prezzi dinamici dal CRM Product
- Gestisce prodotti multipli con quantità editabili
- Mostra errore se link scaduto

**Gestione Errori:**
```python
if not order_data:
    context.order_valid = False
    context.error_message = "Order link has expired"
```

### **4. Cleanup Automatico**

**File:** `techloop_crm/crm/hooks.py`

**Scheduled Task:**
```python
scheduler_events = {
    "all": [
        "crm.fcrm.doctype.temp_ordine.temp_ordine.cleanup_expired_temp_orders"
    ]
}
```

**Funzione Cleanup:**
```python
def cleanup_expired_temp_orders():
    current_time = int(time.time())
    expired_records = frappe.get_all(
        "Temp Ordine",
        filters={
            "expires_at": ["<", current_time],
            "status": "Active"
        }
    )
    # Marca come Expired invece di cancellare
```

## 🔄 Flusso Completo

### **1. Generazione Ordine (AI)**
```python
# AI chiama tool
generate_order_confirmation_form(
    customer_name="Mario Rossi",
    phone_number="+393401234567", 
    products=[
        {"product_id": "PROD-001", "product_quantity": 2},
        {"product_id": "PROD-002", "product_quantity": 1}
    ],
    delivery_address="Via Roma 123"
)
```

### **2. Creazione Temp Ordine**
```python
# Tool crea record
temp_order_doc = frappe.get_doc({
    "doctype": "Temp Ordine",
    "order_data": json.dumps(order_data),
    "created_at": int(time.time()),
    "expires_at": int(time.time()) + 300,  # +5 minuti
    "status": "Active"
})
```

### **3. Link WhatsApp**
```
https://site.com/order_confirmation/ABC123DEF456
```

### **4. Conferma Cliente**
- Cliente clicca link → Form precompilato
- Cliente può modificare quantità → Prezzo si aggiorna
- Cliente conferma → Crea CRM Lead + marca Temp Ordine come "Consumed"

### **5. Cleanup Automatico**
- Ogni minuto: marca record scaduti come "Expired"
- Se cliente clicca link scaduto: mostra errore

## 🛡️ Sicurezza e Robustezza

### **Gestione Sessioni:**
- ✅ **Timeout automatico**: 5 minuti
- ✅ **Consumo atomico**: Un solo utilizzo per record
- ✅ **Stati chiari**: Active → Consumed/Expired
- ✅ **Nessun conflitto**: ID univoci Frappe

### **Gestione Errori:**
- ✅ **Link scaduto**: Messaggio chiaro al cliente
- ✅ **Record non trovato**: Gestione graceful
- ✅ **Prodotti mancanti**: Log errori, continua con altri
- ✅ **Validazione completa**: Campi obbligatori controllati

### **Performance:**
- ✅ **Indexes**: Su `expires_at` e `status`
- ✅ **Cleanup efficiente**: Query ottimizzate
- ✅ **JSON field**: Dati strutturati, queryabili
- ✅ **Unix timestamp**: Comparazioni veloci

## 📊 Struttura Dati

### **JSON Order Data:**
```json
{
  "customer_name": "Mario Rossi",
  "phone_number": "+393401234567",
  "products": [
    {
      "product_id": "PROD-001",
      "product_quantity": 2
    }
  ],
  "delivery_address": "Via Roma 123",
  "notes": "Consegna urgente"
}
```

### **CRM Lead Creato:**
```json
{
  "doctype": "CRM Lead",
  "first_name": "Mario Rossi",
  "phone": "+393401234567",
  "lead_source": "WhatsApp AI",
  "status": "Confirmed Order",
  "custom_order_details": {
    "products": [
      {
        "product_id": "PROD-001",
        "product_name": "Torta al Cioccolato",
        "quantity": 2,
        "unit_price": 15.00,
        "total_price": 30.00
      }
    ],
    "total_price": 30.00,
    "temp_order_id": "ABC123DEF456"
  }
}
```

## 🔧 Configurazione Tecnica

### **File Modificati:**

1. **`crm/fcrm/doctype/temp_ordine/temp_ordine.json`** - Definizione DocType
2. **`crm/fcrm/doctype/temp_ordine/temp_ordine.py`** - Logica business
3. **`CRM_AI_MODULE/ai_module/agents/tools/generate_order_form.py`** - Tool AI
4. **`techloop_crm/crm/www/order_confirmation.py`** - Form backend
5. **`techloop_crm/crm/www/order_confirmation.html`** - Form frontend
6. **`techloop_crm/crm/hooks.py`** - Scheduled tasks

### **Dipendenze:**
- ✅ Frappe Framework
- ✅ CRM Module
- ✅ AI Module
- ✅ Unix timestamp (standard Python)

## 🚀 Deployment

### **Passi per Attivazione:**

1. **Migrazione Database:**
   ```bash
   bench migrate
   ```

2. **Verifica DocType:**
   ```bash
   bench console
   >>> frappe.get_doc("Temp Ordine", "test")
   ```

3. **Test Tool AI:**
   ```python
   # Test generazione form
   generate_order_confirmation_form(
       customer_name="Test",
       phone_number="+393401234567",
       products=[{"product_id": "PROD-001", "product_quantity": 1}]
   )
   ```

4. **Test Cleanup:**
   ```bash
   bench execute crm.fcrm.doctype.temp_ordine.temp_ordine.cleanup_expired_temp_orders
   ```

## 📈 Benefici Implementati

### **Per l'AI:**
- ✅ **Tool semplificato**: Solo product_id + quantity
- ✅ **Link corti**: Facili da inviare via WhatsApp
- ✅ **Gestione automatica**: Scadenza e cleanup

### **Per il Cliente:**
- ✅ **Form pulito**: Senza header/footer Frappe
- ✅ **Dati precompilati**: Nome, telefono, prodotti
- ✅ **Quantità editabili**: Può correggere errori AI
- ✅ **Prezzo dinamico**: Calcolato dal DB in tempo reale

### **Per il Sistema:**
- ✅ **Sicurezza**: Nessun conflitto di ID
- ✅ **Performance**: Cleanup automatico
- ✅ **Scalabilità**: Gestisce ordini multipli
- ✅ **Audit**: Tracciamento completo

## 🔮 Estensioni Future

### **Possibili Miglioramenti:**
- 📧 **Email notifications**: Conferma via email
- 📱 **SMS backup**: Se WhatsApp non disponibile  
- 🔄 **Retry mechanism**: Nuovo link se scaduto
- 📊 **Analytics**: Statistiche conversioni
- 🎨 **Templates**: Form personalizzabili
- 🔐 **Encryption**: Dati sensibili criptati

---

**Conclusione:** Il sistema Temp Ordine rappresenta una soluzione robusta e scalabile per la gestione delle conferme d'ordine via WhatsApp, eliminando i conflitti di sessione e fornendo un'esperienza utente ottimale.
