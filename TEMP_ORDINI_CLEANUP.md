# Sistema Automatico di Pulizia TEMP ORDINI

## Panoramica

Il sistema pulisce automaticamente i record FCRM TEMP ORDINE vecchi o scaduti per mantenere il database pulito.

## Configurazione Attuale

### Scheduler
- **Frequenza**: Ogni ora (configurato in `hooks.py`)
- **Funzione**: `cleanup_expired_temp_orders()`
- **Stato**: ✅ Attivo (verificato via System Settings)

### Regole di Pulizia

1. **Record Attivi Scaduti** → Marcati come "Expired"
   - Quando: `expires_at < current_time`
   - Azione: Cambio status da "Active" a "Expired"

2. **Record Expired Vecchi** → Eliminati fisicamente
   - Quando: Scaduti da più di **1 ora**
   - Azione: `frappe.delete_doc()` con `force=True`

3. **Record Consumed Vecchi** → Eliminati fisicamente  
   - Quando: Consumati da più di **24 ore**
   - Azione: `frappe.delete_doc()` con `force=True`

## Comandi Manuali

### Eseguire Pulizia Immediata
```bash
bench --site site.localhost execute crm.fcrm.doctype.fcrm_temp_ordine.fcrm_temp_ordine.force_cleanup_temp_orders
```

### Verificare Stato Record
```bash
# Contare record per status
bench --site site.localhost mariadb -e "SELECT status, COUNT(*) as count FROM \`tabFCRM TEMP ORDINE\` GROUP BY status;"

# Vedere dettagli ultimi 10 record
bench --site site.localhost mariadb -e "SELECT name, status, modified, FROM_UNIXTIME(expires_at) as expires_at FROM \`tabFCRM TEMP ORDINE\` ORDER BY modified DESC LIMIT 10;"

# Vedere record vecchi da eliminare
bench --site site.localhost mariadb -e "SELECT name, status, modified FROM \`tabFCRM TEMP ORDINE\` WHERE status='Consumed' AND modified < DATE_SUB(NOW(), INTERVAL 24 HOUR);"
```

### Verificare Scheduler
```bash
# Verificare se scheduler è attivo
bench --site site.localhost mariadb -e "SELECT value FROM \`tabSingles\` WHERE doctype='System Settings' AND field='enable_scheduler';"

# Vedere ultimi job schedulati
bench --site site.localhost mariadb -e "SELECT * FROM \`tabScheduled Job Log\` WHERE scheduled_job_type LIKE '%cleanup_expired%' ORDER BY creation DESC LIMIT 5;"
```

## Logs

I log della pulizia sono disponibili in:
- **Info**: Log Frappe → filtra per "crm"
- **Pattern**: 
  - `"Marked {N} FCRM TEMP ORDINE records as expired"`
  - `"Deleted {N} old expired FCRM TEMP ORDINE records"`
  - `"Deleted {N} old consumed FCRM TEMP ORDINE records"`

## Modificare Tempi di Retention

Per modificare quando i record vengono eliminati, modifica il file:
`apps/crm/crm/fcrm/doctype/fcrm_temp_ordine/fcrm_temp_ordine.py`

```python
# Elimina record Expired dopo 1 ora (default)
one_hour_ago = current_time - 3600  # Cambia 3600 con secondi desiderati

# Elimina record Consumed dopo 24 ore (default)
twenty_four_hours_ago = frappe.utils.add_to_date(frappe.utils.now(), hours=-24)  # Cambia -24
```

### Esempi Comuni
- **30 minuti**: `1800` secondi o `hours=-0.5`
- **2 ore**: `7200` secondi o `hours=-2`
- **12 ore**: `43200` secondi o `hours=-12`
- **48 ore**: `172800` secondi o `hours=-48`

## Troubleshooting

### La pulizia non funziona
1. Verificare che scheduler sia attivo: `enable_scheduler = 1`
2. Verificare logs per errori
3. Eseguire pulizia manuale per testare
4. Verificare permessi database

### Record non vengono eliminati
1. Verificare timestamp `modified` dei record
2. Controllare se rispettano le soglie temporali
3. Eseguire query SQL manuale per debug

### Database cresce troppo velocemente
- Ridurre tempi di retention (es. da 24h a 6h per Consumed)
- Aumentare frequenza scheduler (da hourly a ogni 30 minuti con cron custom)

## Note Importanti

⚠️ **I record vengono eliminati PERMANENTEMENTE dopo la retention period**
- Assicurati di aver già processato tutti gli ordini importanti
- I log rimangono nei Lead/Deal creati anche dopo eliminazione temp_ordini
- Per debugging, considera di aumentare retention period temporaneamente

✅ **Best Practices**
- Retention 24h per Consumed è sufficiente per troubleshooting
- Retention 1h per Expired evita accumulo di link non usati
- Monitora periodicamente con query SQL per verificare che funzioni



