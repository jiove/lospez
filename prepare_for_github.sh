#!/bin/bash

echo "Preparazione del progetto per GitHub..."

# Esegui la pulizia dei file temporanei
./clean.sh

# Rimuovi gli ambienti virtuali se esistono
if [ -d "venv" ]; then
    echo "Rimozione dell'ambiente virtuale venv..."
    rm -rf venv
fi

if [ -d "venv_new" ]; then
    echo "Rimozione dell'ambiente virtuale venv_new..."
    rm -rf venv_new
fi

# Rimuovi la cartella .git esistente se presente
if [ -d ".git" ]; then
    echo "Rimozione del repository git esistente..."
    rm -rf .git
fi

# Inizializza un nuovo repository git
echo "Inizializzazione di un nuovo repository git..."
git init

# Aggiungi tutti i file tranne quelli in .gitignore
echo "Aggiunta dei file al repository..."
git add .

echo "Preparazione completata!"
echo "Ora puoi collegare questo repository al tuo GitHub con i seguenti comandi:"
echo ""
echo "  git commit -m \"Commit iniziale\""
echo "  git branch -M main"
echo "  git remote add origin https://github.com/USERNAME/REPO-NAME.git"
echo "  git push -u origin main"
echo ""
echo "Sostituisci USERNAME con il tuo nome utente GitHub e REPO-NAME con il nome del repository." 