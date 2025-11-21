# Import Prodotti da JSON - Documentazione Tecnica

## Come Funziona la Funzione `import_products_from_json`

### Panoramica

La funzione `import_products_from_json()` permette di importare prodotti nel CRM tramite un file JSON. La funzione gestisce automaticamente la creazione di prodotti, l'aggiornamento di prodotti esistenti e **la creazione automatica dei tag**.

### Flusso di Esecuzione

```
1. Validazione JSON
   ↓
2. Parsing JSON → Array di prodotti
   ↓
3. Per ogni prodotto:
   ├─ Validazione campi obbligatori (product_code, product_name)
   ├─ Controllo se prodotto esiste già
   │  ├─ Se esiste → AGGIORNA
   │  └─ Se non esiste → CREA NUOVO
   ├─ Gestione tag (se presenti)
   │  ├─ Per ogni tag:
   │  │  ├─ Verifica se tag master esiste
   │  │  ├─ Se NON esiste → CREA AUTOMATICAMENTE
   │  │  └─ Aggiungi tag al prodotto
   └─ Salvataggio prodotto
   ↓
4. Commit transazione
   ↓
5. Ritorna statistiche (creati, aggiornati, errori)
```

### Gestione dei Tag

#### ✅ Creazione Automatica dei Tag

**IMPORTANTE:** La funzione **crea automaticamente i tag** se non esistono!

Quando un prodotto ha un array `tags` nel JSON:

```json
{
  "product_code": "PROD-001",
  "product_name": "Prodotto Esempio",
  "tags": ["nuovo-tag", "altro-tag"]
}
```

La funzione:

1. **Verifica se il tag esiste** come `CRM Product Tag Master`
2. **Se il tag NON esiste:**
   - Crea automaticamente un nuovo `CRM Product Tag Master`
   - Genera un colore automatico basato sul nome del tag (hash MD5)
   - Usa il nome del tag come descrizione (formattato)
3. **Se il tag esiste già:**
   - Riutilizza il tag esistente (non lo sovrascrive)
   - Mantiene il colore e la descrizione esistenti
4. **Aggiunge il tag al prodotto** nella child table `product_tags`

#### Esempio Pratico

**JSON di input:**
```json
[
  {
    "product_code": "TEST-001",
    "product_name": "Prodotto Test",
    "standard_rate": 25.00,
    "tags": ["tag-nuovo", "tag-esistente"]
  }
]
```

**Cosa succede:**

1. Se `tag-nuovo` non esiste:
   - ✅ Viene creato automaticamente come `CRM Product Tag Master`
   - Colore generato automaticamente (es. `#a3f5c2`)
   - Descrizione: "Tag Nuovo"

2. Se `tag-esistente` esiste già:
   - ✅ Viene riutilizzato (mantiene colore e descrizione originali)

3. Entrambi i tag vengono aggiunti al prodotto `TEST-001`

### Campi del JSON

#### Campi Obbligatori

- **`product_code`** (string): Codice univoco del prodotto
  - Se un prodotto con lo stesso codice esiste, verrà **aggiornato**
  - Non può essere vuoto o mancante

- **`product_name`** (string): Nome del prodotto
  - Non può essere vuoto o mancante

#### Campi Opzionali

- **`standard_rate`** (number): Prezzo del prodotto
  - Default: `0.00`
  - Deve essere un numero valido

- **`description`** (string): Descrizione del prodotto
  - Default: stringa vuota `""`
  - Può essere omesso

- **`tags`** (array di stringhe): Lista di nomi tag
  - Default: array vuoto `[]`
  - Può essere omesso
  - **I tag vengono creati automaticamente se non esistono**

### Gestione Errori

La funzione gestisce gli errori in modo robusto:

1. **Errori di validazione JSON:**
   - JSON malformato → Ritorna errore immediato
   - JSON non è un array → Ritorna errore

2. **Errori per prodotto:**
   - Campi obbligatori mancanti → Aggiunto a lista errori, prodotto saltato
   - Errori durante creazione/aggiornamento → Aggiunto a lista errori, prodotto saltato
   - **Gli altri prodotti continuano ad essere processati**

3. **Errori di tag:**
   - Se un tag non può essere creato → Log dell'errore, tag saltato
   - **Il prodotto viene comunque creato/aggiornato**

### Risposta della Funzione

La funzione ritorna un dizionario con:

```python
{
    "success": True/False,
    "message": "Messaggio descrittivo",
    "created_products": ["PROD-001", "PROD-002"],  # Nomi prodotti creati
    "updated_products": ["PROD-003"],              # Nomi prodotti aggiornati
    "errors": [                                    # Lista errori (se presenti)
        "Prodotto 5: product_code mancante",
        "Errore processando prodotto 7: ..."
    ]
}
```

### Esempio Completo

**Input JSON:**
```json
[
  {
    "product_code": "EXTRA-CHOCOLATE",
    "product_name": "Extra chocolate",
    "standard_rate": 40.00,
    "description": "Impasto al cioccolato con cubetti di cioccolato fondente.",
    "tags": ["limited-edition", "cioccolato", "nuovo-tag-2025"]
  },
  {
    "product_code": "PROD-SEMPLICE",
    "product_name": "Prodotto Semplice",
    "standard_rate": 25.50
  }
]
```

**Cosa succede:**

1. **Prodotto 1 (EXTRA-CHOCOLATE):**
   - Se non esiste → Viene creato
   - Se esiste → Viene aggiornato (nome, prezzo, descrizione)
   - Tag `limited-edition`: Se esiste → riutilizzato, altrimenti creato
   - Tag `cioccolato`: Se esiste → riutilizzato, altrimenti creato
   - Tag `nuovo-tag-2025`: **Creato automaticamente** (non esiste)

2. **Prodotto 2 (PROD-SEMPLICE):**
   - Viene creato/aggiornato
   - Nessun tag (array tags omesso)

**Output:**
```python
{
    "success": True,
    "message": "Importati 1 nuovi prodotti e aggiornati 1 esistenti",
    "created_products": ["EXTRA-CHOCOLATE"],
    "updated_products": ["PROD-SEMPLICE"],
    "errors": None
}
```

### Funzioni Helper

#### `_create_or_get_tag_master(tag_name, color=None)`

Crea un tag master se non esiste, altrimenti lo restituisce.

- **Parametri:**
  - `tag_name`: Nome del tag
  - `color`: Colore hex (opzionale, default: generato automaticamente)

- **Ritorna:** Nome del documento `CRM Product Tag Master`

#### `_add_tags_to_product(product_name, tag_names, auto_create_tags=True)`

Aggiunge tag a un prodotto.

- **Parametri:**
  - `product_name`: Nome del documento CRM Product
  - `tag_names`: Lista di nomi tag
  - `auto_create_tags`: Se `True`, crea automaticamente i tag mancanti

### Permessi

La funzione richiede il ruolo **System Manager** per essere eseguita:

```python
frappe.only_for("System Manager")
```

### Transazioni

La funzione usa una transazione database:
- Se tutto va bene → `frappe.db.commit()`
- Se c'è un errore generale → `frappe.db.rollback()`

Gli errori per singolo prodotto non causano rollback, solo log e aggiunta alla lista errori.


