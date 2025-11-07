# Sistema di Notifiche WhatsApp per Cambio Stato Lead

## Panoramica

Questo documento descrive il sistema integrato nel CRM per inviare automaticamente notifiche WhatsApp quando lo stato di un Lead cambia. Il sistema compone e invia i messaggi direttamente dal codice CRM, senza dipendere da moduli esterni per la generazione dei messaggi.

## Changelog

### 2025-11-07: Sistema Modulare per Notifiche Stato

**Modifiche principali:**
- ✅ Sistema reso completamente modulare e dinamico
- ✅ Creazione automatica di Custom Fields per ogni stato Lead
- ✅ Generazione dinamica dell'interfaccia utente nel frontend
- ✅ Rimozione automatica dei campi degli stati eliminati
- ✅ Traduzioni automatiche delle label dei campi
- ✅ Eliminata la mappa hardcoded degli stati nel backend

**File modificati:**
- `crm/fcrm/doctype/fcrm_settings/fcrm_settings.py`: Aggiunte funzioni per sincronizzazione dinamica Custom Fields
- `crm/fcrm/doctype/crm_lead/status_change_notification.py`: Lettura dinamica degli stati invece di mappa hardcoded
- `frontend/src/components/Settings/BrandSettings.vue`: Generazione dinamica dei campi per ogni stato

**Vantaggi:**
- Nessuna modifica codice necessaria quando si aggiungono nuovi stati
- Retrocompatibilità con i campi esistenti
- Manutenzione ridotta e scalabilità migliorata

## Architettura

### Componenti Principali

1. **CRM Module** (`apps/crm/`)
   - Listener per cambio stato Lead
   - Composizione messaggi WhatsApp
   - Gestione informazioni pagamento
   - Invio diretto messaggi tramite frappe_whatsapp

2. **frappe_whatsapp** (richiesto)
   - Invio messaggi WhatsApp
   - Gestione comunicazioni

### Flusso Dati

```
CRM Lead Status Change
    ↓
on_lead_status_change() [CRM]
    ↓
Prepara context_data strutturato
    ↓
_compose_status_change_message() [CRM]
    ↓
Componi messaggio direttamente nel codice
    ↓
create_whatsapp_message() → Invia WhatsApp
```

## File Implementati

### CRM Module

1. **`apps/crm/crm/fcrm/doctype/crm_lead/status_change_notification.py`**
   - `on_lead_status_change()`: Hook principale chiamato quando lo status cambia
   - `_compose_status_change_message()`: Componi messaggio WhatsApp direttamente nel codice
   - `_send_status_change_notification()`: Invia messaggio WhatsApp tramite frappe_whatsapp
   - `_get_payment_info()`: Legge informazioni pagamento da Brand Settings
   - `_prepare_order_summary()`: Prepara riepilogo ordine con prodotti
   - `check_pending_payments()`: Scheduled job per controllo pagamenti pendenti
   - `_get_status_notification_settings()`: **Legge dinamicamente le impostazioni per qualsiasi stato** (modulare)
   - `_slugify_status_name()`: Converte nomi stati in slug per i nomi dei campi

2. **`apps/crm/crm/fcrm/doctype/crm_lead/crm_lead.py`**
   - Hook `validate()` modificato per chiamare `on_lead_status_change()`

3. **`apps/crm/crm/fcrm/doctype/crm_lead/create_new_statuses.py`**
   - Script per creare nuovi status: "Awaiting Payment", "Confirmed", "Not Paid" (in inglese)

4. **`apps/crm/crm/fcrm/doctype/fcrm_settings/fcrm_settings.py`** ⭐ **NUOVO**
   - `sync_status_notification_fields()`: **Sincronizza dinamicamente i Custom Fields per ogni stato Lead**
   - `_create_or_update_custom_field()`: Crea/aggiorna Custom Fields per le notifiche
   - `_remove_obsolete_status_fields()`: Rimuove i campi degli stati eliminati
   - `_slugify_status_name()`: Converte nomi stati in slug
   - Chiamata automatica in `after_migrate()` per sincronizzare i campi

5. **`apps/crm/crm/fcrm/doctype/fcrm_settings/fcrm_settings.json`**
   - Campo `payment_info_text` aggiunto nel tab "Branding"
   - Sezione `status_notifications_section` per le notifiche

6. **`apps/crm/frontend/src/components/Settings/BrandSettings.vue`** ⭐ **MODIFICATO**
   - **Generazione dinamica dei campi per ogni stato disponibile** (non più hardcoded)
   - Interfaccia per inserire testo informazioni pagamento
   - Funzioni helper per slugify e generazione nomi campi
   - Traduzioni automatiche delle label

7. **`apps/crm/crm/hooks.py`**
   - Scheduled job giornaliero: `check_pending_payments`

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

Puoi inserire testo libero che verrà incluso direttamente nel messaggio WhatsApp. Esempio:

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

Il testo verrà incluso così com'è nel messaggio WhatsApp. Puoi usare `{numero_ordine}` o `{order_number}` come placeholder che verrà sostituito automaticamente.

## Funzionalità Implementate

### 1. Notifica Cambio Stato Generico

Quando lo status di un Lead cambia:
- Viene inviato un messaggio WhatsApp al contatto
- Il messaggio include: numero ordine, stato precedente, nuovo stato
- Il messaggio è composto direttamente dal codice per essere chiaro e professionale

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
   - `_is_whatsapp_installed()`: Verifica se frappe_whatsapp è installato
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

**Status Richiesti per CRM Lead (nomi in inglese nel database):**
- Awaiting Payment (Attesa Pagamento)
- Confirmed (Confermato)
- Not Paid (Non Pagato)

**Se gli status mancano:**
- Viene restituito un errore con messaggio chiaro
- Viene suggerito di eseguire lo script `create_new_statuses.execute()`
- L'operazione di reset viene interrotta

**Messaggio di Errore:**
```
Errore nel reset viste: gli status seguenti non sono presenti nel sistema: Attesa Pagamento, Confermato, Non Pagato. 
Esegui lo script 'crm.fcrm.doctype.crm_lead.create_new_statuses.execute' per crearli.
```

## Dati Strutturati per Messaggi

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

## Composizione Messaggi

Il sistema compone messaggi direttamente nel codice:

**Per cambio stato generico:**
- Saluto personalizzato con nome cliente
- Numero d'ordine in formato abbreviato (es. 25-00021)
- Stato precedente e nuovo stato (tradotti in italiano)
- Messaggio professionale e cortese

**Per stato "Attesa Pagamento":**
- Saluto personalizzato
- Notifica cambio stato
- Riepilogo completo ordine (prodotti, quantità, prezzi)
- Totale ordine
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

## Vantaggi Approccio Diretto

✅ **Affidabilità**: La logica hardcoded garantisce che eventi e dati siano sempre corretti
✅ **Prevedibilità**: I messaggi sono sempre consistenti e formattati correttamente
✅ **Manutenibilità**: Il codice è facile da modificare e personalizzare
✅ **Sicurezza**: I dati sensibili sono preparati in modo controllato
✅ **Tracciabilità**: Ogni passo è loggato per debugging
✅ **Performance**: Nessuna chiamata esterna all'AI, invio immediato
✅ **Indipendenza**: Non richiede ai_module, solo frappe_whatsapp

## Troubleshooting

### Messaggi non vengono inviati

1. Verifica che il Lead abbia un numero di telefono (`mobile_no` o `phone`)
2. Controlla i log di Frappe per errori
3. Verifica che `frappe_whatsapp` sia installato e configurato
4. Controlla che le impostazioni WhatsApp siano corrette

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

## Note Tecniche

Informazioni chiave per sviluppatori:

1. **Hook Location**: `CRMLead.validate()` chiama `on_lead_status_change()`
2. **Payment Info**: Legge da `FCRM Settings.payment_info_text` (tab Branding)
3. **Status Required**: "Awaiting Payment", "Confirmed", "Not Paid" devono esistere (nomi in inglese nel DB)
4. **Error Handling**: Tutte le eccezioni sono loggate, non soppresse
5. **Module Check**: Verifica sempre se `frappe_whatsapp` è installato prima di inviare messaggi
6. **Scheduled Job**: `check_pending_payments()` esegue giornalmente
7. **Status Creation**: Gli status vengono creati automaticamente durante install/update
8. **Message Composition**: I messaggi sono composti da `_compose_status_change_message()`
9. **WhatsApp Integration**: Usa `crm.api.whatsapp.create_whatsapp_message()` per inviare

## Sistema Modulare per Notifiche Stato ⭐ NUOVO

### Panoramica

Il sistema è stato reso completamente **modulare** e **dinamico**. Non è più necessario modificare il codice quando vengono aggiunti nuovi stati Lead. Il sistema:

1. **Rileva automaticamente** tutti gli stati Lead disponibili nel database
2. **Crea dinamicamente** i Custom Fields necessari per ogni stato
3. **Genera automaticamente** l'interfaccia utente per configurare le notifiche
4. **Rimuove automaticamente** i campi degli stati eliminati
5. **Traduce automaticamente** le label usando il sistema di traduzione di Frappe

### Come Funziona

#### Backend (Python)

Quando viene eseguita una migrazione o viene chiamato `after_migrate()`:

1. Il sistema recupera tutti gli stati Lead dal database:
   ```python
   lead_statuses = frappe.get_all("CRM Lead Status", fields=["name"], order_by="position asc")
   ```

2. Per ogni stato, crea due Custom Fields in `FCRM Settings`:
   - `enable_notification_<status_slug>` (Check): Abilita/disabilita la notifica
   - `custom_message_<status_slug>` (Long Text): Messaggio personalizzato

3. I nomi dei campi vengono generati convertendo il nome dello stato in slug:
   - "Awaiting Payment" → `enable_notification_awaiting_payment`
   - "Confirmed" → `enable_notification_confirmed`
   - "Nuovo Stato" → `enable_notification_nuovo_stato`

4. Le label vengono tradotte automaticamente:
   - `_("Enable notification for {0}").format(_(status_name))`
   - `_("Custom message for {0}").format(_(status_name))`

#### Frontend (Vue)

Il componente `BrandSettings.vue`:

1. Recupera dinamicamente tutti gli stati Lead usando `statusesStore`:
   ```javascript
   const { leadStatuses } = statusesStore()
   ```

2. Genera automaticamente i campi per ogni stato:
   ```vue
   <div v-for="status in leadStatuses.data" :key="status.name">
     <FormControl
       type="checkbox"
       v-model="settings.doc[getEnableFieldName(status.name)]"
       :label="getEnableNotificationLabel(status.name)"
     />
     <FormControl
       v-if="settings.doc[getEnableFieldName(status.name)]"
       type="textarea"
       v-model="settings.doc[getMessageFieldName(status.name)]"
       :label="getCustomMessageLabel(status.name)"
     />
   </div>
   ```

3. Usa funzioni helper per generare i nomi dei campi e le label tradotte

#### Lettura Impostazioni

La funzione `_get_status_notification_settings()`:

1. Verifica se lo stato esiste nel database
2. Converte il nome dello stato in slug
3. Legge dinamicamente i Custom Fields:
   ```python
   enable_fieldname = f"enable_notification_{status_slug}"
   message_fieldname = f"custom_message_{status_slug}"
   enabled = getattr(settings, enable_fieldname, None)
   custom_message = getattr(settings, message_fieldname, None)
   ```

### Vantaggi del Sistema Modulare

✅ **Nessuna modifica codice**: Aggiungi un nuovo stato e il sistema lo gestisce automaticamente  
✅ **Retrocompatibilità**: I campi esistenti continuano a funzionare  
✅ **Pulizia automatica**: I campi degli stati eliminati vengono rimossi  
✅ **Traduzioni automatiche**: Le label vengono tradotte usando il sistema di Frappe  
✅ **Manutenzione ridotta**: Non serve aggiornare mappe hardcoded o template  
✅ **Scalabilità**: Funziona con qualsiasi numero di stati  

### Sincronizzazione Automatica

I Custom Fields vengono sincronizzati automaticamente quando:

1. Viene eseguita una migrazione (`bench migrate`)
2. Viene chiamato `after_migrate()` da altri script
3. Viene eseguito manualmente:
   ```python
   from crm.fcrm.doctype.fcrm_settings.fcrm_settings import sync_status_notification_fields
   sync_status_notification_fields()
   ```

### Configurazione Manuale

Per configurare le notifiche per uno stato:

1. Vai su: **Settings → Brand Settings → Tab "Branding"**
2. Scorri fino alla sezione **"Status Change Notifications"**
3. Per ogni stato vedrai:
   - Checkbox: "Enable notification for [Nome Stato]"
   - Textarea: "Custom message for [Nome Stato]" (appare solo se la checkbox è selezionata)
4. Abilita la notifica e opzionalmente inserisci un messaggio personalizzato
5. Clicca su **"Update"** per salvare

### Messaggi di Default

Se non viene specificato un messaggio personalizzato, il sistema usa messaggi di default:

- **Rejected**: "La richiesta d'ordine è stata rifiutata, pertanto l'ordine è stato annullato."
- **Awaiting Payment**: "Per proseguire con l'ordine, ti invitiamo a eseguire il pagamento utilizzando i metodi forniti di seguito."
- **Confirmed**: "L'ordine è stato preso in carico e sta venendo preparato."
- **Not Paid**: "L'ordine non è stato pagato nei tempi consentiti. Per maggiori informazioni, ti invitiamo a contattare l'assistenza."
- **Altri stati**: "Lo stato dell'ordine è stato aggiornato a: [Nome Stato]."

## Prossimi Passi

1. **Sostituire dati pagamento fittizi**: Configura `payment_info_text` nelle Brand Settings
2. **Personalizzare messaggi**: Configura i messaggi personalizzati per ogni stato nelle Brand Settings
3. **Aggiungere altri stati**: Crea nuovi stati Lead e il sistema li gestirà automaticamente
4. **Aggiungere template**: Crea template predefiniti per messaggi comuni (futuro)

## Note Importanti

- Il sistema richiede che `frappe_whatsapp` sia installato e configurato
- I numeri di telefono devono essere nel formato internazionale (+39...)
- Il sistema compone i messaggi direttamente nel codice CRM
- I messaggi vengono inviati tramite `create_whatsapp_message()` del CRM
- Gli status vengono creati automaticamente durante install/update (nomi in inglese)
- Le traduzioni degli status sono gestite tramite localizations di Frappe
