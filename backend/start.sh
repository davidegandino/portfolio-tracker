#!/bin/bash
# Script di avvio per Render
echo "🚀 Avvio Portfolio Tracker..."

# Inizializza database (se vuoto)
if [ ! -f portfolio.db ]; then
    echo "📦 Creazione database..."
    python demo_data.py || echo "⚠️  demo_data.py fallito, continuo comunque"
fi

# Avvia server
echo "🌐 Avvio server..."
python main.py
