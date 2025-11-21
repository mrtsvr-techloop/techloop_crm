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

### Special Functions
Il pulsante **Special Functions** è presente nelle impostazioni del CRM ma è nascosto (invisibile). Si trova in fondo alla lista delle impostazioni.
