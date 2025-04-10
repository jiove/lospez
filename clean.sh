#!/bin/bash

# Rimuovi tutto il contenuto di uploads e results
rm -rf uploads/*
rm -rf results/*

# Rimuovi i file di cache Python
rm -rf __pycache__/*
rm -rf **/__pycache__/*

# Assicurati che le cartelle uploads e results esistano
mkdir -p uploads
mkdir -p results

# Crea file .gitkeep nelle cartelle
touch uploads/.gitkeep
touch results/.gitkeep

echo "Pulizia completata! Le cartelle uploads, results e i file di cache sono stati rimossi." 