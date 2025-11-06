# Gestione degli Status nel CRM

## Panoramica

Questo documento descrive come sono stati modificati gli status nel CRM, come crearne di nuovi, come rimuoverli e come evitare errori comuni. La documentazione è strutturata per essere comprensibile sia da sviluppatori umani che da sistemi AI.

---

## Modifiche Implementate

### File Modificati

Gli status sono gestiti attraverso modifiche in due file principali:

1. **`apps/crm/crm/fcrm/doctype/crm_view_settings/crm_view_settings.py`**
   - Funzione `sync_default_columns()` (linee 128-174)
   - Funzione `create_or_update_standard_view()` (linee 195-292)
   - Funzione `reset_default_views()` (linee 295-370)

2. **`apps/crm/crm/api/doc.py`**
   - Funzione `get_data()` (linee 276-600)
   - Logica per la costruzione delle colonne Kanban (linee 407-450)

### Logica di Sincronizzazione

Gli status vengono sincronizzati automaticamente dal database quando:
- Si crea una nuova vista Kanban
- Si resetta una vista default usando la funzione "Reset Default Views"
- Si carica una vista Kanban senza colonne predefinite

La sincronizzazione avviene attraverso:
1. Query al database per ottenere tutti gli status dal DocType appropriato (`CRM Lead Status` o `CRM Deal Status`)
2. Recupero dei campi: `name`, `color`, `position` (e `type` per Deal Status)
3. Ordinamento per `position asc`
4. Validazione dei colori (rosso solo per status "Lost" nei Deal)

---

## DocType degli Status

### CRM Lead Status

**Percorso**: `apps/crm/crm/fcrm/doctype/crm_lead_status/`

**Campi disponibili**:
- `lead_status` (Data, required, unique): Nome dello status
- `color` (Select): Colore della colonna Kanban (default: "gray")
  - Opzioni: black, gray, blue, green, red, pink, orange, amber, yellow, cyan, teal, violet, purple
- `position` (Int): Posizione di ordinamento (default: 1)

**Regole**:
- Il colore rosso dovrebbe essere evitato per status positivi
- Se non specificato, il colore default è "gray"

### CRM Deal Status

**Percorso**: `apps/crm/crm/fcrm/doctype/crm_deal_status/`

**Campi disponibili**:
- `deal_status` (Data, required, unique): Nome dello status
- `type` (Select): Tipo di status (default: "Open")
  - Opzioni: Open, Ongoing, On Hold, Won, Lost
- `color` (Select): Colore della colonna Kanban (default: "gray")
  - Opzioni: black, gray, blue, green, red, pink, orange, amber, yellow, cyan, teal, violet, purple
- `position` (Int): Posizione di ordinamento
- `probability` (Percent): Probabilità di chiusura (0-100)

**Regole CRITICHE**:
- **Il colore ROSSO può essere usato SOLO per status con `type = "Lost"`**
- Se uno status positivo ha colore rosso, viene automaticamente convertito a "gray"
- Se uno status "Lost" non ha colore rosso, viene automaticamente impostato a "red"

---

## Come Creare un Nuovo Status

### Per CRM Lead Status

1. **Accedi al DocType**:
   - Vai su: List → CRM Lead Status
   - Oppure usa la ricerca: "CRM Lead Status"

2. **Crea nuovo documento**:
   - Clicca su "New"
   - Compila i campi:
     - **Status**: Nome dello status (es. "Nuovo Contatto")
     - **Color**: Seleziona un colore appropriato (evita rosso per status positivi)
     - **Position**: Imposta la posizione nell'ordinamento (es. 1, 2, 3...)
   - Salva

3. **Aggiorna le viste**:
   - Vai su: Settings → Special Functions
   - Clicca su "Reset Default Views"
   - Questo sincronizzerà le colonne Kanban con i nuovi status dal database

### Per CRM Deal Status

1. **Accedi al DocType**:
   - Vai su: List → CRM Deal Status
   - Oppure usa la ricerca: "CRM Deal Status"

2. **Crea nuovo documento**:
   - Clicca su "New"
   - Compila i campi:
     - **Status**: Nome dello status (es. "In Attesa")
     - **Type**: Seleziona il tipo appropriato:
       - "Open": Status iniziale
       - "Ongoing": In corso
       - "On Hold": In pausa
       - "Won": Vinto/Completato
       - "Lost": Perso (usa SOLO questo per status negativi)
     - **Color**: 
       - Se `type = "Lost"`: DEVI usare "red"
       - Altrimenti: usa qualsiasi colore tranne "red" (consigliato: gray, blue, green, orange)
     - **Position**: Posizione nell'ordinamento
     - **Probability**: Probabilità di chiusura (0-100)
   - Salva

3. **Aggiorna le viste**:
   - Vai su: Settings → Special Functions
   - Clicca su "Reset Default Views"
   - Questo sincronizzerà le colonne Kanban con i nuovi status dal database

---

## Come Rimuovere uno Status

### Procedura Standard

1. **Verifica utilizzo**:
   - Prima di eliminare, verifica se ci sono Lead o Deal che utilizzano questo status
   - Vai su: List → CRM Lead (o CRM Deal)
   - Applica un filtro per lo status che vuoi rimuovere
   - Se ci sono documenti, cambia il loro status prima di eliminare

2. **Elimina lo status**:
   - Vai su: List → CRM Lead Status (o CRM Deal Status)
   - Trova lo status da eliminare
   - Clicca su "Delete"
   - Conferma l'eliminazione

3. **Aggiorna le viste**:
   - Vai su: Settings → Special Functions
   - Clicca su "Reset Default Views"
   - Questo rimuoverà la colonna Kanban corrispondente

### Nota Importante

Se elimini uno status senza cambiare i documenti che lo utilizzano:
- I Lead/Deal con quello status NON appariranno nella vista Kanban
- Appariranno solo nella vista Lista
- Dovrai manualmente cambiare il loro status

---

## Errori Comuni e Come Evitarli

### 1. Status Non Appare nella Vista Kanban

**Sintomi**:
- Hai creato un nuovo status ma non appare nella colonna Kanban
- Le colonne Kanban mostrano ancora gli status vecchi

**Cause**:
- Le viste non sono state sincronizzate dopo la creazione dello status
- Lo status è stato creato ma le colonne Kanban sono state salvate manualmente senza includerlo

**Soluzione**:
1. Vai su: Settings → Special Functions
2. Clicca su "Reset Default Views"
3. Verifica che lo status appaia nella vista Kanban

**Prevenzione**:
- Dopo ogni creazione/modifica/rimozione di status, esegui sempre "Reset Default Views"
- Non modificare manualmente le colonne Kanban nelle impostazioni delle viste

---

### 2. Colore Rosso Usato per Status Positivi

**Sintomi**:
- Uno status positivo (non "Lost") ha colore rosso nella vista Kanban
- Il colore rosso appare per status che non dovrebbero essere negativi

**Cause**:
- Lo status è stato creato con colore "red" ma `type` non è "Lost"
- Lo status è stato modificato manualmente senza rispettare le regole

**Soluzione**:
1. Vai su: List → CRM Deal Status
2. Trova lo status con colore rosso
3. Se `type` non è "Lost", cambia il colore a "gray" o altro colore appropriato
4. Salva
5. Esegui "Reset Default Views" per applicare le modifiche

**Prevenzione**:
- Per Deal Status: usa rosso SOLO se `type = "Lost"`
- Per Lead Status: evita completamente il colore rosso
- Il sistema applica automaticamente queste regole durante la sincronizzazione

---

### 3. Status Duplicati o Nomi Errati

**Sintomi**:
- Due status con lo stesso nome
- Status con nomi che non corrispondono alle traduzioni

**Cause**:
- Creazione manuale senza verificare duplicati
- Nomi inseriti in inglese invece che nella lingua del sistema

**Soluzione**:
1. Verifica i nomi degli status esistenti
2. Elimina i duplicati
3. Rinomina gli status con nomi corretti nella lingua del sistema
4. Esegui "Reset Default Views"

**Prevenzione**:
- Il campo `lead_status` e `deal_status` sono unici: il sistema impedisce duplicati
- Usa sempre nomi nella lingua del sistema (italiano nel nostro caso)
- Verifica sempre prima di creare un nuovo status

---

### 4. Posizione di Ordinamento Non Corretta

**Sintomi**:
- Gli status appaiono in ordine errato nella vista Kanban
- Lo status più importante non appare per primo

**Cause**:
- Campo `position` non impostato correttamente
- Posizioni duplicate o non sequenziali

**Soluzione**:
1. Vai su: List → CRM Lead Status (o CRM Deal Status)
2. Ordina per "Position"
3. Modifica le posizioni per avere un ordine logico:
   - Status iniziali: 1, 2, 3...
   - Status intermedi: 10, 20, 30...
   - Status finali: 90, 100
4. Salva tutti gli status modificati
5. Esegui "Reset Default Views"

**Prevenzione**:
- Usa numeri sequenziali con spazi (es. 10, 20, 30) per facilitare inserimenti futuri
- Documenta l'ordine logico degli status nel tuo processo di vendita

---

### 5. Viste Non Aggiornate Dopo Modifiche

**Sintomi**:
- Modifichi uno status ma le modifiche non appaiono nella vista Kanban
- Le colonne Kanban mostrano ancora valori vecchi

**Cause**:
- Le viste sono state salvate manualmente con colonne hardcoded
- La funzione di sincronizzazione non è stata eseguita

**Soluzione**:
1. Vai su: Settings → Special Functions
2. Clicca su "Reset Default Views"
3. Questo forza la risincronizzazione di tutte le colonne dal database

**Prevenzione**:
- Dopo OGNI modifica agli status, esegui sempre "Reset Default Views"
- Non modificare manualmente le colonne Kanban nelle impostazioni delle viste
- Lascia che il sistema gestisca automaticamente la sincronizzazione

---

### 7. Errore "Status Non Presenti" Durante Reset Viste

**Sintomi**:
- Quando esegui "Reset Default Views" ricevi un errore
- Messaggio: "Errore nel reset viste: gli status seguenti non sono presenti nel sistema: ..."

**Cause**:
- Gli status richiesti ("Attesa Pagamento", "Confermato", "Non Pagato") non sono stati creati
- Lo script `create_new_statuses.py` non è stato eseguito

**Soluzione**:
1. Esegui lo script per creare gli status mancanti:
   ```python
   from crm.fcrm.doctype.crm_lead.create_new_statuses import execute
   execute()
   ```
2. Verifica che gli status siano stati creati:
   - Vai su: List → CRM Lead Status
   - Controlla che "Attesa Pagamento", "Confermato" e "Non Pagato" esistano
3. Poi esegui nuovamente "Reset Default Views"

**Prevenzione**:
- Sempre esegui `create_new_statuses.execute()` PRIMA di eseguire "Reset Default Views"
- Verifica che tutti gli status richiesti esistano prima di resettare le viste
- Il sistema ora verifica automaticamente e mostra un errore chiaro se mancano

---

### 6. Status Eliminato ma Documenti Ancora Lo Utilizzano

**Sintomi**:
- Elimini uno status ma i Lead/Deal con quello status non appaiono più nella vista Kanban
- I documenti sono ancora presenti ma "invisibili" nella vista Kanban

**Cause**:
- Eliminazione dello status senza prima cambiare i documenti che lo utilizzano
- Lo status è stato eliminato ma i documenti hanno ancora quel valore nel campo `status`

**Soluzione**:
1. Vai su: List → CRM Lead (o CRM Deal)
2. Applica un filtro per trovare i documenti con lo status eliminato
3. Seleziona tutti i documenti
4. Cambia manualmente il loro status a uno valido
5. Salva

**Prevenzione**:
- Prima di eliminare uno status:
  1. Verifica quanti documenti lo utilizzano
  2. Cambia tutti i documenti a un altro status
  3. Solo dopo elimina lo status

---

## Struttura Tecnica

### Come Funziona la Sincronizzazione

La funzione `sync_default_columns()` in `crm_view_settings.py`:

```python
def sync_default_columns(view):
    # ...
    if field_meta.options in ["CRM Lead Status", "CRM Deal Status"]:
        fields_to_get = ["name", "color", "position"]
        if field_meta.options == "CRM Deal Status":
            fields_to_get.append("type")
        
        statuses = frappe.get_all(
            field_meta.options,
            fields=fields_to_get,
            order_by="position asc",
        )
        
        # Validazione colori
        for status in statuses:
            if field_meta.options == "CRM Deal Status" and status.get("type") == "Lost":
                if not status.get("color") or status.get("color") not in ["red"]:
                    status["color"] = "red"
            elif status.get("color") == "red":
                if field_meta.options == "CRM Deal Status" and status.get("type") not in ["Lost"]:
                    status["color"] = "gray"
                elif field_meta.options == "CRM Lead Status":
                    status["color"] = status.get("color") or "gray"
        
        columns = statuses
    # ...
```

### Quando Viene Chiamata

La sincronizzazione avviene automaticamente quando:
1. Si crea una nuova vista Kanban senza colonne predefinite
2. Si chiama `reset_default_views()` dalla funzione "Reset Default Views"
3. Si chiama `create_or_update_standard_view()` con `kanban_columns = ""` (stringa vuota)

---

## Checklist per la Gestione degli Status

### Quando Crei un Nuovo Status

- [ ] Verifico che non esista già uno status simile
- [ ] Imposto il nome nella lingua corretta del sistema
- [ ] Per Deal Status: scelgo il `type` appropriato
- [ ] Per Deal Status: uso rosso SOLO se `type = "Lost"`
- [ ] Per Lead Status: evito il colore rosso
- [ ] Imposto la `position` corretta per l'ordinamento
- [ ] Salvo lo status
- [ ] Eseguo "Reset Default Views" per sincronizzare

### Quando Modifichi uno Status

- [ ] Verifico che le modifiche rispettino le regole dei colori
- [ ] Se cambio il nome, verifico che non crei duplicati
- [ ] Se cambio la position, verifico l'ordine logico
- [ ] Salvo le modifiche
- [ ] Eseguo "Reset Default Views" per applicare le modifiche

### Quando Elimini uno Status

- [ ] Verifico quanti documenti utilizzano questo status
- [ ] Cambio tutti i documenti a un altro status valido
- [ ] Elimino lo status
- [ ] Eseguo "Reset Default Views" per rimuoverlo dalle viste

---

## Note per Sistemi AI

Se stai leggendo questo documento come sistema AI, ecco le informazioni chiave:

1. **DocType**: Gli status sono memorizzati in `CRM Lead Status` e `CRM Deal Status`
2. **Sincronizzazione**: Le colonne Kanban vengono sincronizzate dalla funzione `sync_default_columns()` che legge dal database
3. **Reset**: La funzione `reset_default_views()` forza la risincronizzazione di tutte le viste
4. **Validazione Colori**: Il sistema applica automaticamente regole sui colori durante la sincronizzazione
5. **Ordinamento**: Gli status sono ordinati per il campo `position` in ordine ascendente
6. **Campi Richiesti**: 
   - Lead Status: `lead_status` (unique), `color`, `position`
   - Deal Status: `deal_status` (unique), `type`, `color`, `position`, `probability`
7. **Regola Critica**: Rosso può essere usato SOLO per Deal Status con `type = "Lost"`

---

## Supporto

Per problemi o domande sulla gestione degli status:
1. Consulta questa documentazione
2. Verifica i log del sistema per errori
3. Esegui "Reset Default Views" come prima soluzione
4. Contatta l'amministratore di sistema se il problema persiste

