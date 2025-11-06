# Sistema di Notifiche WhatsApp per Cambio Stato Lead

## Panoramica

Questo documento descrive il sistema integrato tra CRM e AI Module per inviare automaticamente notifiche WhatsApp quando lo stato di un Lead cambia. Il sistema utilizza un approccio ibrido: logica hardcoded per catturare eventi e preparare dati strutturati, AI per generare messaggi personalizzati.

## Architettura

### Componenti Principali

1. **CRM Module** (`apps/crm/`)
   - Listener per cambio stato Lead
   - Preparazione dati strutturati
   - Gestione informazioni pagamento

2. **AI Module** (`apps/ai_module/`)
   - Generazione messaggi tramite AI
   - Invio messaggi WhatsApp
   - Gestione sessioni conversazione

### Flusso Dati

```
CRM Lead Status Change
    ↓
on_lead_status_change() [CRM]
    ↓
Prepara context_data strutturato
    ↓
process_status_change_notification() [AI Module]
    ↓
Costruisce prompt per AI
    ↓
run_agent() → Genera messaggio
    ↓
_send_autoreply() → Invia WhatsApp
```

## File Implementati

### CRM Module

1. **`apps/crm/crm/fcrm/doctype/crm_lead/status_change_notification.py`**
   - `on_lead_status_change()`: Hook principale chiamato quando lo status cambia
   - `_get_payment_info()`: Legge informazioni pagamento da Brand Settings
   - `_prepare_order_summary()`: Prepara riepilogo ordine con prodotti
   - `check_pending_payments()`: Scheduled job per controllo pagamenti pendenti

2. **`apps/crm/crm/fcrm/doctype/crm_lead/crm_lead.py`**
   - Hook `validate()` modificato per chiamare `on_lead_status_change()`

3. **`apps/crm/crm/fcrm/doctype/crm_lead/create_new_statuses.py`**
   - Script per creare nuovi status: "Attesa Pagamento", "Confermato", "Non Pagato"

4. **`apps/crm/crm/fcrm/doctype/fcrm_settings/fcrm_settings.json`**
   - Campo `payment_info_text` aggiunto nel tab "Branding"

5. **`apps/crm/frontend/src/components/Settings/BrandSettings.vue`**
   - Interfaccia per inserire testo informazioni pagamento

6. **`apps/crm/crm/hooks.py`**
   - Scheduled job giornaliero: `check_pending_payments`

### AI Module

1. **`apps/ai_module/ai_module/integrations/status_change.py`**
   - `process_status_change_notification()`: Processa notifiche e genera messaggi
   - `_build_status_change_prompt()`: Costruisce prompt strutturato per AI

## Stati Lead Implementati

### Nuovi Stati Creati

1. **Attesa Pagamento** (arancione)
   - Indica che l'ordine è in attesa di pagamento
   - Quando attivato, invia messaggio con riepilogo ordine e dati pagamento

2. **Confermato** (verde)
   - Indica che l'ordine è stato confermato

3. **Non Pagato** (rosso)
   - Indica che il pagamento non è stato effettuato
   - Impostato automaticamente dopo 3 giorni in "Attesa Pagamento"

### Creazione Stati

Per creare gli stati, esegui:
```python
from crm.fcrm.doctype.crm_lead.create_new_statuses import execute
execute()
```

**IMPORTANTE**: Dopo aver creato gli stati, esegui "Reset Default Views" nelle impostazioni per sincronizzare le colonne Kanban.

## Configurazione Informazioni Pagamento

### Dove Configurare

Le informazioni di pagamento sono configurabili nelle **Brand Settings**:
- Settings → Brand Settings → Tab "Branding"
- Sezione "Informazioni Pagamento"
- Campo "Testo Informazioni Pagamento"

### Formato

Puoi inserire testo libero che l'AI interpreterà automaticamente. Esempio:

```
Bonifico Bancario:
- Banca: Tua Banca S.p.A.
- IBAN: IT60 X054 2811 1010 0000 0123 456
- SWIFT: TUOSWIFT01
- Intestatario: Tua Azienda
- Causale: Ordine {numero_ordine}

PayPal: pagamenti@tuaazienda.it

Istruzioni: Puoi effettuare il pagamento tramite bonifico o PayPal.
Assicurati di includere il numero d'ordine nella causale.
```

L'AI formatterà automaticamente queste informazioni nel messaggio WhatsApp.

## Funzionalità Implementate

### 1. Notifica Cambio Stato Generico

Quando lo status di un Lead cambia:
- Viene inviato un messaggio WhatsApp al contatto
- Il messaggio include: numero ordine, stato precedente, nuovo stato
- Il messaggio è generato dall'AI per essere naturale e professionale

### 2. Notifica "Attesa Pagamento"

Quando lo status è cambiato a "Attesa Pagamento":
- Il messaggio include riepilogo completo ordine:
  - Lista prodotti con quantità e prezzi
  - Totale ordine
- Include informazioni pagamento:
  - Dati bonifico bancario (se configurati)
  - Dati PayPal (se configurati)
  - Istruzioni per il pagamento

### 3. Controllo Automatico Pagamenti Pendenti

Scheduled job giornaliero che:
- Controlla tutti i Lead in stato "Attesa Pagamento"
- Verifica quando è stato cambiato a questo stato
- Se sono passati più di 3 giorni, cambia automaticamente a "Non Pagato"

## Gestione Errori e Robustezza

### Controlli Implementati

1. **Verifica Moduli Installati**
   - `_is_ai_module_installed()`: Verifica se ai_module è installato
   - Se non installato: logga e salta notifica (non blocca salvataggio Lead)

2. **Verifica DocType Esistenti**
   - Controlla che FCRM Settings esista prima di leggere informazioni pagamento
   - Controlla che CRM Lead esista prima di eseguire scheduled job

3. **Gestione Eccezioni**
   - Tutte le eccezioni sono loggate con `frappe.log_error()`
   - Traceback completo incluso nei log
   - Le eccezioni critiche vengono rilanciate dove appropriato
   - Le eccezioni non critiche non bloccano il flusso principale

### Logging

Tutti gli eventi sono loggati:
- Cambio stato rilevato
- Numero telefono trovato/non trovato
- Invio notifica riuscito/fallito
- Errori di importazione moduli
- Errori nel scheduled job

## Verifica Status Prima di Reset Viste

La funzione `reset_default_views()` ora verifica che gli status richiesti esistano prima di resettare le viste.

**Status Richiesti per CRM Lead:**
- Attesa Pagamento
- Confermato
- Non Pagato

**Se gli status mancano:**
- Viene restituito un errore con messaggio chiaro
- Viene suggerito di eseguire lo script `create_new_statuses.execute()`
- L'operazione di reset viene interrotta

**Messaggio di Errore:**
```
Errore nel reset viste: gli status seguenti non sono presenti nel sistema: Attesa Pagamento, Confermato, Non Pagato. 
Esegui lo script 'crm.fcrm.doctype.crm_lead.create_new_statuses.execute' per crearli.
```

## Dati Strutturati per AI

Il sistema prepara un dizionario `context_data` con:

```python
{
    "lead_id": "CRM-LEAD-2025-00001",
    "order_number": "CRM-LEAD-2025-00001",
    "old_status": "Nuovo",
    "new_status": "Attesa Pagamento",
    "customer_name": "Mario Rossi",
    "has_order_details": True,  # Solo se stato = "Attesa Pagamento"
    "order_summary": {
        "products": [
            {
                "name": "Prodotto 1",
                "quantity": 2,
                "unit_price": 10.00,
                "total_price": 20.00
            }
        ],
        "subtotal": 20.00,
        "net_total": 20.00,
        "currency": "EUR"
    },
    "payment_info": {
        "text": "...",  # Se da Brand Settings
        "source": "settings"  # o "default"
    }
}
```

## Prompt AI

Il sistema costruisce prompt dettagliati che includono:

**Per cambio stato generico:**
- Numero d'ordine
- Stato precedente e nuovo stato
- Nome cliente
- Istruzioni per generare messaggio professionale

**Per stato "Attesa Pagamento":**
- Riepilogo completo ordine (prodotti, quantità, prezzi)
- Informazioni pagamento (da Brand Settings o default)
- Istruzioni chiare per il pagamento

## Scheduled Jobs

### check_pending_payments()

**Frequenza**: Giornaliera (configurata in `hooks.py`)

**Funzionalità**:
- Controlla Lead in "Attesa Pagamento"
- Verifica data cambio stato
- Cambia automaticamente a "Non Pagato" dopo 3 giorni

**Configurazione**:
```python
# apps/crm/crm/hooks.py
scheduler_events = {
    "daily": [
        "crm.fcrm.doctype.crm_lead.status_change_notification.check_pending_payments"
    ],
}
```

## Vantaggi Approccio Ibrido

✅ **Affidabilità**: La logica hardcoded garantisce che eventi e dati siano sempre corretti
✅ **Flessibilità**: L'AI genera messaggi personalizzati e naturali
✅ **Manutenibilità**: I prompt strutturati sono facili da modificare
✅ **Sicurezza**: I dati sensibili sono preparati in modo controllato
✅ **Tracciabilità**: Ogni passo è loggato per debugging

## Troubleshooting

### Messaggi non vengono inviati

1. Verifica che il Lead abbia un numero di telefono (`mobile_no` o `phone`)
2. Controlla i log: `apps/crm/logs/status_change.log`
3. Verifica che `ai_module` sia installato e configurato
4. Controlla che l'agente AI sia configurato correttamente

### Stati non creati

1. Esegui manualmente lo script `create_new_statuses.py`
2. Verifica i permessi per creare CRM Lead Status
3. Controlla i log per errori

### Errore "Status non presenti" durante Reset Viste

1. Esegui lo script per creare gli status:
   ```python
   from crm.fcrm.doctype.crm_lead.create_new_statuses import execute
   execute()
   ```
2. Poi esegui "Reset Default Views"

### Scheduled job non esegue

1. Verifica che il scheduler sia attivo: `bench --site [site] scheduler status`
2. Controlla i log del scheduler
3. Verifica la configurazione in `hooks.py`

## Note per Sistemi AI

Se stai leggendo questo documento come sistema AI, ecco le informazioni chiave:

1. **Hook Location**: `CRMLead.validate()` chiama `on_lead_status_change()`
2. **Payment Info**: Legge da `FCRM Settings.payment_info_text` (tab Branding)
3. **Status Required**: "Attesa Pagamento", "Confermato", "Non Pagato" devono esistere
4. **Error Handling**: Tutte le eccezioni sono loggate, non soppresse
5. **Module Check**: Verifica sempre se `ai_module` è installato prima di chiamare funzioni AI
6. **Scheduled Job**: `check_pending_payments()` esegue giornalmente
7. **Status Creation**: Usa `create_new_statuses.execute()` per creare nuovi status

## Prossimi Passi

1. **Sostituire dati pagamento fittizi**: Configura `payment_info_text` nelle Brand Settings
2. **Personalizzare prompt**: Modifica `_build_status_change_prompt()` per il tuo stile
3. **Aggiungere altri stati**: Estendi il sistema per altri stati che richiedono notifiche
4. **Aggiungere template**: Crea template predefiniti per messaggi comuni

## Note Importanti

- Il sistema richiede che `ai_module` sia installato e configurato
- I numeri di telefono devono essere nel formato internazionale (+39...)
- Il sistema usa la stessa infrastruttura WhatsApp del listener esistente
- I messaggi vengono inviati tramite la funzione `_send_autoreply()` esistente
- Gli status devono essere creati PRIMA di eseguire "Reset Default Views"
