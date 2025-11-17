# Fix: Conflitti Timestamp e Errori MandatoryError nell'Aggiunta Prodotti

## Problema

Quando si aggiungeva un prodotto al Lead e lo si selezionava dal menu a tendina, il sistema generava multipli errori:

1. **MandatoryError**: `product_name` era obbligatorio ma veniva salvato vuoto
2. **TimestampMismatchError**: Il documento veniva modificato da chiamate simultanee, causando conflitti di timestamp

### Errori Generati

```
frappe.exceptions.MandatoryError: [CRM Lead, CRM-LEAD-2025-00021]: product_name
frappe.exceptions.TimestampMismatchError: Errore: Il Documento è stato modificato dopo averlo aperto
```

## Cause Identificate

### 1. Chiamate Multiple Simultanee

Quando si selezionava un prodotto:
- `onProductChange()` emetteva un update **immediato**
- `calculateTotals()` emetteva un altro update dopo **300ms di debounce**
- `updateProducts()` chiamava `updateField()` **due volte separate** (products e total/net_total)

Questo causava 3-4 chiamate API simultanee che tentavano di salvare lo stesso documento, generando conflitti di timestamp.

### 2. Salvataggio Prodotti Vuoti

Quando si aggiungeva un nuovo prodotto:
- Veniva creato con `product_name: ''` (vuoto)
- Veniva emesso un update immediato che tentava di salvare il prodotto vuoto
- Il backend rifiutava il salvataggio perché `product_name` è obbligatorio

## Soluzioni Implementate

### 1. Rimozione Update Immediato in `onProductChange`

**File**: `frontend/src/components/ProductsTab.vue`

**Prima**:
```javascript
function onProductChange(index) {
  // ...
  if (selectedProduct) {
    product.product_name = selectedProduct.product_name
    product.rate = selectedProduct.standard_rate || 0
    calculateTotals(index)
    emit('update', products.value) // ❌ Update immediato
  }
}
```

**Dopo**:
```javascript
function onProductChange(index) {
  // ...
  if (selectedProduct) {
    product.product_name = selectedProduct.product_name
    product.rate = selectedProduct.standard_rate || 0
    // ✅ calculateTotals emetterà l'update dopo il debounce
    calculateTotals(index)
  }
}
```

### 2. Unificazione Salvataggio in Singola Chiamata

**File**: `frontend/src/pages/Lead.vue`

**Prima**:
```javascript
function updateProducts(products) {
  const validProducts = products.filter(/* ... */)
  updateField('products', validProducts) // ❌ Prima chiamata
  const total = /* ... */
  const netTotal = /* ... */
  updateField(['total', 'net_total'], [total, netTotal]) // ❌ Seconda chiamata
}
```

**Dopo**:
```javascript
function updateProducts(products) {
  // Filtra prodotti vuoti
  const validProducts = products.filter(p => p.product_name && p.product_name.trim() !== '')
  
  // Calcola totali
  const total = validProducts.reduce(/* ... */)
  const netTotal = validProducts.reduce(/* ... */)
  
  // Aggiorna valori locali
  doc.value.products = validProducts
  doc.value.total = total
  doc.value.net_total = netTotal
  
  // ✅ Salva tutto in una singola chiamata
  document.save.submit(null, {
    onSuccess: () => { /* ... */ },
    onError: (err) => { /* ... */ }
  })
}
```

### 3. Lock per Evitare Chiamate Simultanee

**File**: `frontend/src/pages/Lead.vue`

```javascript
// Lock per evitare chiamate simultanee
let isUpdatingProducts = false

function updateProducts(products) {
  // ✅ Se c'è già un aggiornamento in corso, ignora questa chiamata
  if (isUpdatingProducts) {
    return
  }
  
  isUpdatingProducts = true
  
  document.save.submit(null, {
    onSuccess: () => {
      isUpdatingProducts = false
      // ...
    },
    onError: (err) => {
      isUpdatingProducts = false
      // ...
    }
  })
}
```

### 4. Filtro Prodotti Vuoti

**File**: `frontend/src/components/ProductsTab.vue`

```javascript
function addProduct() {
  products.value.push({
    product_code: '',
    product_name: '', // Vuoto inizialmente
    // ...
  })
  // ✅ Non emettere update quando si aggiunge un prodotto vuoto
  // L'update verrà emesso quando l'utente seleziona un prodotto
}

function calculateTotals(index) {
  // ...
  // ✅ Emetti update solo se il prodotto ha un product_name valido
  if (product.product_name && product.product_name.trim() !== '') {
    updateTimeout = setTimeout(() => {
      const validProducts = products.value.filter(p => 
        p.product_name && p.product_name.trim() !== ''
      )
      emit('update', validProducts)
    }, 300)
  }
}
```

### 5. Gestione TimestampMismatchError con Retry Automatico

**File**: `frontend/src/pages/Lead.vue`

```javascript
document.save.submit(null, {
  onError: (err) => {
    // ✅ Se c'è un errore di timestamp mismatch, ricarica e riprova
    if (err.exc_type === 'TimestampMismatchError') {
      document.reload().then(() => {
        // Riprova dopo il reload
        doc.value.products = validProducts
        doc.value.total = total
        doc.value.net_total = netTotal
        document.save.submit(null, {
          onSuccess: () => { /* ... */ },
          onError: (retryErr) => {
            // Se anche il retry fallisce, ricarica il documento
            document.reload()
          }
        })
      })
      return
    }
    // Per altri errori, ricarica il documento per sincronizzare
    document.reload()
  }
})
```

## Flusso Corretto Dopo il Fix

1. **Utente clicca "Aggiungi Prodotto"**
   - Viene aggiunta una riga vuota localmente
   - ❌ Nessun salvataggio (prodotto vuoto)

2. **Utente seleziona un prodotto dal menu**
   - `onProductChange()` aggiorna `product_name` e `rate` localmente
   - `calculateTotals()` calcola i totali
   - ⏱️ Dopo 300ms di debounce, viene emesso un singolo update

3. **`updateProducts()` riceve l'update**
   - Filtra i prodotti vuoti
   - Calcola i totali
   - Aggiorna i valori locali
   - 🔒 Verifica il lock (se c'è già un salvataggio in corso, ignora)
   - 💾 Salva tutto in una singola chiamata API

4. **In caso di TimestampMismatchError**
   - 🔄 Ricarica il documento
   - 🔄 Riprova automaticamente il salvataggio
   - ✅ Se fallisce anche il retry, ricarica il documento per sincronizzare

## File Modificati

1. `frontend/src/components/ProductsTab.vue`
   - Rimossa chiamata update immediata in `onProductChange()`
   - Aggiunto filtro prodotti vuoti in `calculateTotals()`
   - Modificato `addProduct()` per non emettere update

2. `frontend/src/pages/Lead.vue`
   - Unificato salvataggio in `updateProducts()`
   - Aggiunto lock `isUpdatingProducts`
   - Implementato retry automatico su `TimestampMismatchError`
   - Migliorata gestione cleanup funzioni toast

## Testing

Per testare il fix:

1. Aprire un Lead
2. Andare alla tab "Prodotti"
3. Cliccare "Aggiungi Prodotto"
4. Selezionare un prodotto dal menu a tendina
5. Verificare che:
   - ✅ Non ci siano errori in console
   - ✅ Il prodotto venga salvato correttamente
   - ✅ I totali vengano calcolati correttamente
   - ✅ Non ci siano conflitti di timestamp

## Note Tecniche

- Il debounce di 300ms in `calculateTotals()` evita troppi aggiornamenti durante la digitazione
- Il lock `isUpdatingProducts` previene race conditions
- Il retry automatico migliora l'esperienza utente in caso di conflitti temporanei
- Il filtro prodotti vuoti previene errori di validazione backend

## Commit

```
fix: risolti conflitti timestamp quando si seleziona prodotto

- Rimossa chiamata update immediata in onProductChange
- Unificata salvataggio prodotti e totali in singola chiamata
- Aggiunto lock per evitare chiamate simultanee
- Migliorata gestione errori con retry automatico su TimestampMismatchError
- Corretto cleanup funzioni toast in tutti i percorsi
```

