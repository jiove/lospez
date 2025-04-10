# Guida al Deployment di GeneJam su Render.com

Questa guida ti aiuterà a deployare l'applicazione GeneJam (Lo Spezzettatore) su Render.com.

## Prerequisiti

- Un account su [Render.com](https://render.com)
- Un repository Git con il codice dell'applicazione

## Passi per il Deployment

### 1. Preparazione del Repository

Assicurati che il tuo repository contenga i seguenti file:

- `app.py`: Il file principale dell'applicazione Flask
- `requirements.txt`: Elenco delle dipendenze Python
- `render.yaml`: Configurazione per Render.com
- `Procfile`: Istruzioni per l'avvio dell'applicazione
- `static/`: Cartella con i file statici (CSS, JS, ecc.)
- `templates/`: Cartella con i template HTML
- `uploads/` e `results/`: Cartelle per i file caricati e i risultati (con .gitkeep)

### 2. Creazione di un Nuovo Servizio Web su Render.com

1. Accedi al tuo account Render.com
2. Vai alla dashboard e clicca su "New +"
3. Seleziona "Web Service"
4. Collega il tuo repository Git
5. Configura il servizio:
   - **Nome**: GeneJam (o un nome a tua scelta)
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Piano**: Free (o un piano a pagamento se necessario)

### 3. Configurazione delle Variabili d'Ambiente (se necessario)

Se la tua applicazione utilizza variabili d'ambiente, puoi configurarle nella sezione "Environment" del tuo servizio web su Render.com.

### 4. Deploy

Clicca su "Create Web Service" per avviare il deployment. Render.com clonerà il tuo repository, installerà le dipendenze e avvierà l'applicazione.

### 5. Verifica

Una volta completato il deployment, Render.com ti fornirà un URL per accedere alla tua applicazione (ad esempio, `https://genejam.onrender.com`). Visita questo URL per verificare che l'applicazione funzioni correttamente.

## Note Importanti

- **Persistenza dei Dati**: Render.com non offre storage persistente per i file nei piani gratuiti. Per un'applicazione di produzione, considera l'utilizzo di servizi di storage come AWS S3 o simili per salvare i file caricati e i risultati.
- **Limiti del Piano Gratuito**: Il piano gratuito di Render.com ha alcune limitazioni, come lo spegnimento automatico dopo un periodo di inattività. Consulta la documentazione di Render.com per maggiori dettagli.

## Risoluzione dei Problemi

Se incontri problemi durante il deployment, controlla i log dell'applicazione nella dashboard di Render.com. I problemi più comuni includono:

- Dipendenze mancanti nel file `requirements.txt`
- Errori nel file `app.py`
- Problemi con le variabili d'ambiente

Per assistenza più dettagliata, consulta la [documentazione ufficiale di Render.com](https://render.com/docs).
