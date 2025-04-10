# Lo Spezzettatore - Guida Rapida

Ciao collega! Ti invio questo progetto per poterci lavorare insieme. Ecco una guida rapida per iniziare:

## Struttura del Progetto

- `app.py` - File principale dell'applicazione Flask
- `templates/` - Contiene i template HTML
- `static/` - Contiene CSS, JavaScript e altre risorse statiche
- `uploads/` - Cartella dove vengono caricati i video dagli utenti
- `results/` - Cartella dove vengono salvati i risultati dell'elaborazione
- `clean.sh` - Script per pulire i file temporanei e ripristinare le cartelle

## Installazione

1. Crea un ambiente virtuale Python:
   ```
   python3 -m venv venv
   ```

2. Attiva l'ambiente virtuale:
   - macOS/Linux: `source venv/bin/activate`
   - Windows: `venv\Scripts\activate`

3. Installa le dipendenze:
   ```
   pip install -r requirements.txt
   ```

## Esecuzione

1. Attiva l'ambiente virtuale (se non è già attivo)
2. Avvia l'applicazione Flask:
   ```
   python3 app.py
   ```
   
3. Apri il browser e vai a http://localhost:5004 (o l'URL mostrato nel terminale)

## Pulizia dei File Temporanei

Ho incluso uno script `clean.sh` che pulisce le cartelle temporanee. È utile da eseguire:
- Prima di inviare il progetto a qualcun altro
- Se hai accumulato troppi file di test
- Se vuoi assicurarti di avere un ambiente pulito

Per eseguire lo script:
```
./clean.sh
```

## Funzionalità Principali

- Upload di video
- Rilevamento automatico delle scene
- Visualizzazione delle scene rilevate
- Download delle scene rilevate
- Supporto per video da YouTube

Sentiti libero di modificare il codice e implementare nuove funzionalità. Se hai domande, non esitare a contattarmi!

## Repository GitHub

Il progetto è disponibile su GitHub. Per clonarlo:

```
git clone https://github.com/USERNAME/REPO-NAME.git
cd REPO-NAME
```

Dopo aver clonato il repository, segui le istruzioni nella sezione "Installazione" per configurare l'ambiente di sviluppo.

Se hai accesso in scrittura al repository, puoi inviare le tue modifiche con:

```
git add .
git commit -m "Descrizione delle modifiche"
git push origin main
``` 