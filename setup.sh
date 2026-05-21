#!/bin/bash
# Script di setup per Portfolio Tracker

echo "🚀 Setup Portfolio Tracker..."

# Crea virtual environment
echo "📦 Creazione virtual environment..."
cd backend
python3 -m venv venv

# Attiva e installa dipendenze
echo "📥 Installazione dipendenze..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Torna alla root
cd ..

# Inizializza database
echo "💾 Inizializzazione database..."
source backend/venv/bin/activate
python demo_data.py

echo ""
echo "✅ Setup completato!"
echo ""
echo "🚀 Per avviare il server:"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "Poi apri http://localhost:8000 nel browser"
