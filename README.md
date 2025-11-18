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
