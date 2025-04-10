# Rilevatore Automatico di Scene Video

Un'applicazione web che rileva automaticamente i cambi di scena nei video e salva il primo frame di ogni scena rilevata.

## Funzionalità

- Interfaccia drag-and-drop per il caricamento dei video
- Rilevamento automatico delle scene utilizzando algoritmi di analisi del contenuto
- Estrazione e salvataggio del primo frame di ogni scena rilevata
- Visualizzazione delle anteprime delle scene rilevate
- Informazioni dettagliate sul video (durata, risoluzione, FPS, formato)
- Possibilità di scaricare tutte le scene in un unico file ZIP
- Regolazione della sensibilità del rilevamento delle scene

## Requisiti Tecnici

- Python 3.7+
- Flask
- OpenCV
- PySceneDetect
- Browser moderno con supporto HTML5

## Formati Video Supportati

- MP4
- AVI
- MOV

## Installazione

1. Clona il repository:
   ```
   git clone https://github.com/tuonome/rilevatore-scene-video.git
   cd rilevatore-scene-video
   ```

2. Crea un ambiente virtuale e attivalo:
   ```
   python -m venv venv
   source venv/bin/activate  # Su Windows: venv\Scripts\activate
   ```

3. Installa le dipendenze:
   ```
   pip install -r requirements.txt
   ```

4. Avvia l'applicazione:
   ```
   python app.py
   ```

5. Apri il browser e vai a `http://localhost:5000`

## Utilizzo

1. Trascina un file video nell'area di caricamento o fai clic per selezionare un file
2. Attendi il completamento del rilevamento delle scene
3. Visualizza le scene rilevate e le informazioni sul video
4. Regola la sensibilità del rilevamento se necessario
5. Scarica tutte le scene in un unico file ZIP

## Limitazioni

- Dimensione massima del file: 500MB
- Il rilevamento delle scene potrebbe non essere perfetto per tutti i tipi di video
- L'elaborazione di video lunghi o ad alta risoluzione potrebbe richiedere più tempo

## Licenza

MIT

## Autore

[Il tuo nome] 