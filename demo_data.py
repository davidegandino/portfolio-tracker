#!/usr/bin/env python3
"""
Script per inizializzare il database con dati demo.
Esegue:
1. Crea tabelle database
2. Inserisce holdings demo (ETF, Azioni, Fondi)
3. Inserisce transazioni demo
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import engine, Base, SessionLocal
from models import Holding, Transaction, AssetClass
from datetime import datetime, timedelta

# Crea tabelle
print("📦 Creazione tabelle database...")
Base.metadata.create_all(bind=engine)

# Crea sessione
db = SessionLocal()

try:
    # Holdings demo
    holdings_demo = [
        Holding(
            ticker="VWRP",
            nome="Vanguard FTSE All-World UCITS ETF Accumulating",
            asset_class=AssetClass.ETF,
            valuta="EUR",
            quantita=50.0,
            prezzo_medio=95.50
        ),
        Holding(
            ticker="VUAA",
            nome="Vanguard S&P 500 UCITS ETF Accumulating",
            asset_class=AssetClass.ETF,
            valuta="EUR",
            quantita=20.0,
            prezzo_medio=88.20
        ),
        Holding(
            ticker="AAPL",
            nome="Apple Inc.",
            asset_class=AssetClass.AZIONE,
            valuta="USD",
            quantita=15.0,
            prezzo_medio=175.30
        ),
        Holding(
            ticker="MSFT",
            nome="Microsoft Corporation",
            asset_class=AssetClass.AZIONE,
            valuta="USD",
            quantita=10.0,
            prezzo_medio=380.50
        ),
        Holding(
            ticker="FUND1",
            nome="Fondo Azionario Europeo ESG",
            asset_class=AssetClass.FONDO,
            valuta="EUR",
            quantita=100.0,
            prezzo_medio=45.80
        )
    ]
    
    print("\n📊 Inserimento holdings demo...")
    for h in holdings_demo:
        db.add(h)
        print(f"  ✓ {h.ticker} - {h.nome[:40]}...")
    
    db.commit()
    
    # Transazioni demo
    print("\n💰 Inserimento transazioni demo...")
    today = datetime.now()
    
    transactions_demo = [
        Transaction(
            holding_id=1,  # VWRP
            tipo="acquisto",
            quantita=30.0,
            prezzo_unitario=92.00,
            valuta="EUR",
            data_transazione=today - timedelta(days=60),
            note="Primo acquisto VWRP"
        ),
        Transaction(
            holding_id=1,  # VWRP
            tipo="acquisto",
            quantita=20.0,
            prezzo_unitario=100.50,
            valuta="EUR",
            data_transazione=today - timedelta(days=30),
            note="Acquisto mensile"
        ),
        Transaction(
            holding_id=2,  # VUAA
            tipo="acquisto",
            quantita=20.0,
            prezzo_unitario=88.20,
            valuta="EUR",
            data_transazione=today - timedelta(days=45),
            note="Primo acquisto VUAA"
        ),
        Transaction(
            holding_id=3,  # AAPL
            tipo="acquisto",
            quantita=15.0,
            prezzo_unitario=175.30,
            valuta="USD",
            data_transazione=today - timedelta(days=90),
            note="Acquisto Apple"
        ),
        Transaction(
            holding_id=4,  # MSFT
            tipo="acquisto",
            quantita=10.0,
            prezzo_unitario=380.50,
            valuta="USD",
            data_transazione=today - timedelta(days=75),
            note="Acquisto Microsoft"
        ),
        Transaction(
            holding_id=5,  # FONDO1
            tipo="acquisto",
            quantita=100.0,
            prezzo_unitario=45.80,
            valuta="EUR",
            data_transazione=today - timedelta(days=120),
            note="Investimento fondo europeo"
        )
    ]
    
    for t in transactions_demo:
        db.add(t)
        print(f"  ✓ {t.tipo.capitalize()} {t.quantita} {db.query(Holding).get(t.holding_id).ticker} @ €{t.prezzo_unitario}")
    
    db.commit()
    
    print("\n✅ Database inizializzato con successo!")
    print("\n📈 Portafoglio demo creato:")
    print("   - 2 ETF (VWRP, VUAA)")
    print("   - 2 Azioni (AAPL, MSFT)")
    print("   - 1 Fondo (Fondo Azionario Europeo)")
    print("\n🚀 Ora puoi avviare il server con: cd backend && python main.py")
    print("   Poi apri http://localhost:8000 nel browser")

except Exception as e:
    print(f"\n❌ Errore: {e}")
    db.rollback()
finally:
    db.close()
