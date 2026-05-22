#!/usr/bin/env python3
"""
Wrapper per avviare main.py e catturare errori
"""
import sys
import os
import traceback

# Aggiungi backend al path
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)

print("=" * 60)
print("WRAPPER: Avvio applicazione...")
print("=" * 60)
print(f"Working directory: {os.getcwd()}")
print(f"Python path: {sys.path}")
print(f"File in backend: {os.listdir('.')}")
print("=" * 60)

try:
    print("Import main...")
    import main
    print("Import riuscito!")
except Exception as e:
    print("=" * 60)
    print("❌ ERRORE DURANTE L'IMPORT:")
    print("=" * 60)
    print(f"Tipo: {type(e).__name__}")
    print(f"Messaggio: {e}")
    print()
    print("Traceback completo:")
    traceback.print_exc()
    print("=" * 60)
    sys.exit(1)
