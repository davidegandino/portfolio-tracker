#!/usr/bin/env python3
"""
Script per inizializzare il database con dati demo reali.
Crea 6 holdings (2 per asset class) con transazioni storiche a:
- Inizio 2024 (Gennaio)
- Fine 2024 (Dicembre)
- Metà 2025 (Giugno)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database import engine, Base, SessionLocal
from models import Holding, Transaction, AssetClass
from datetime import datetime

# Crea tabelle
print("📦 Creazione tabelle database...")
Base.metadata.create_all(bind=engine)

# Crea sessione
db = SessionLocal()

try:
    # Holdings demo - 2 per asset class
    holdings_demo = [
        # ETF
        Holding(
            ticker="VWRP",
            nome="Vanguard FTSE All-World UCITS ETF Accumulating",
            asset_class=AssetClass.ETF,
            valuta="EUR",
            quantita=0.0,
            prezzo_medio=0.0
        ),
        Holding(
            ticker="VUAA",
            nome="Vanguard S&P 500 UCITS ETF Accumulating",
            asset_class=AssetClass.ETF,
            valuta="EUR",
            quantita=0.0,
            prezzo_medio=0.0
        ),
        # Azioni
        Holding(
            ticker="AAPL",
            nome="Apple Inc.",
            asset_class=AssetClass.AZIONE,
            valuta="USD",
            quantita=0.0,
            prezzo_medio=0.0
        ),
        Holding(
            ticker="MSFT",
            nome="Microsoft Corporation",
            asset_class=AssetClass.AZIONE,
            valuta="USD",
            quantita=0.0,
            prezzo_medio=0.0
        ),
        # Fondi (ETF tematici come proxy)
        Holding(
            ticker="EQQQ",
            nome="Invesco EQQQ Nasdaq-100 UCITS ETF",
            asset_class=AssetClass.FONDO,
            valuta="EUR",
            quantita=0.0,
            prezzo_medio=0.0
        ),
        Holding(
            ticker="VWRL",
            nome="Vanguard FTSE All-World UCITS ETF Distributing",
            asset_class=AssetClass.FONDO,
            valuta="EUR",
            quantita=0.0,
            prezzo_medio=0.0
        )
    ]
    
    print("\n📊 Inserimento holdings...")
    for h in holdings_demo:
        db.add(h)
        print(f"  ✓ {h.ticker} - {h.nome[:50]}...")
    
    db.commit()
    
    # Recupera ID holdings
    holdings_by_ticker = {}
    for h in db.query(Holding).all():
        holdings_by_ticker[h.ticker] = h
    
    # Transazioni demo con prezzi realistici
    print("\n💰 Inserimento transazioni storiche...")
    
    transactions_demo = [
        # VWRP - 3 acquisti nel tempo
        Transaction(
            holding_id=holdings_by_ticker["VWRP"].id,
            tipo="acquisto",
            quantita=20.0,
            prezzo_unitario=96.50,
            valuta="EUR",
            data_transazione=datetime(2024, 1, 15),
            note="Inizio 2024 - Primo investimento"
        ),
        Transaction(
            holding_id=holdings_by_ticker["VWRP"].id,
            tipo="acquisto",
            quantita=15.0,
            prezzo_unitario=108.20,
            valuta="EUR",
            data_transazione=datetime(2024, 12, 10),
            note="Fine 2024 - Accumulo annuale"
        ),
        Transaction(
            holding_id=holdings_by_ticker["VWRP"].id,
            tipo="acquisto",
            quantita=10.0,
            prezzo_unitario=115.80,
            valuta="EUR",
            data_transazione=datetime(2025, 6, 15),
            note="Metà 2025 - Continuo accumulo"
        ),
        
        # VUAA - 3 acquisti
        Transaction(
            holding_id=holdings_by_ticker["VUAA"].id,
            tipo="acquisto",
            quantita=15.0,
            prezzo_unitario=87.30,
            valuta="EUR",
            data_transazione=datetime(2024, 1, 15),
            note="Inizio 2024 - Esposizione USA"
        ),
        Transaction(
            holding_id=holdings_by_ticker["VUAA"].id,
            tipo="acquisto",
            quantita=12.0,
            prezzo_unitario=102.50,
            valuta="EUR",
            data_transazione=datetime(2024, 12, 10),
            note="Fine 2024 - S&P 500 in crescita"
        ),
        Transaction(
            holding_id=holdings_by_ticker["VUAA"].id,
            tipo="acquisto",
            quantita=8.0,
            prezzo_unitario=118.90,
            valuta="EUR",
            data_transazione=datetime(2025, 6, 15),
            note="Metà 2025 - Tech traina mercati"
        ),
        
        # AAPL - 3 acquisti
        Transaction(
            holding_id=holdings_by_ticker["AAPL"].id,
            tipo="acquisto",
            quantita=10.0,
            prezzo_unitario=185.50,
            valuta="USD",
            data_transazione=datetime(2024, 1, 15),
            note="Inizio 2024 - Apple entry"
        ),
        Transaction(
            holding_id=holdings_by_ticker["AAPL"].id,
            tipo="acquisto",
            quantita=8.0,
            prezzo_unitario=232.80,
            valuta="USD",
            data_transazione=datetime(2024, 12, 10),
            note="Fine 2024 - iPhone sales forti"
        ),
        Transaction(
            holding_id=holdings_by_ticker["AAPL"].id,
            tipo="acquisto",
            quantita=5.0,
            prezzo_unitario=245.20,
            valuta="USD",
            data_transazione=datetime(2025, 6, 15),
            note="Metà 2025 - AI integration"
        ),
        
        # MSFT - 3 acquisti
        Transaction(
            holding_id=holdings_by_ticker["MSFT"].id,
            tipo="acquisto",
            quantita=8.0,
            prezzo_unitario=375.20,
            valuta="USD",
            data_transazione=datetime(2024, 1, 15),
            note="Inizio 2024 - Microsoft entry"
        ),
        Transaction(
            holding_id=holdings_by_ticker["MSFT"].id,
            tipo="acquisto",
            quantita=6.0,
            prezzo_unitario=438.50,
            valuta="USD",
            data_transazione=datetime(2024, 12, 10),
            note="Fine 2024 - Azure growth"
        ),
        Transaction(
            holding_id=holdings_by_ticker["MSFT"].id,
            tipo="acquisto",
            quantita=4.0,
            prezzo_unitario=485.30,
            valuta="USD",
            data_transazione=datetime(2025, 6, 15),
            note="Metà 2025 - AI leadership"
        ),
        
        # EQQQ - 3 acquisti
        Transaction(
            holding_id=holdings_by_ticker["EQQQ"].id,
            tipo="acquisto",
            quantita=5.0,
            prezzo_unitario=415.60,
            valuta="EUR",
            data_transazione=datetime(2024, 1, 15),
            note="Inizio 2024 - Tech exposure"
        ),
        Transaction(
            holding_id=holdings_by_ticker["EQQQ"].id,
            tipo="acquisto",
            quantita=4.0,
            prezzo_unitario=498.30,
            valuta="EUR",
            data_transazione=datetime(2024, 12, 10),
            note="Fine 2024 - Nasdaq rally"
        ),
        Transaction(
            holding_id=holdings_by_ticker["EQQQ"].id,
            tipo="acquisto",
            quantita=3.0,
            prezzo_unitario=572.40,
            valuta="EUR",
            data_transazione=datetime(2025, 6, 15),
            note="Metà 2025 - AI boom"
        ),
        
        # VWRL - 3 acquisti
        Transaction(
            holding_id=holdings_by_ticker["VWRL"].id,
            tipo="acquisto",
            quantita=25.0,
            prezzo_unitario=89.80,
            valuta="EUR",
            data_transazione=datetime(2024, 1, 15),
            note="Inizio 2024 - Globale distributing"
        ),
        Transaction(
            holding_id=holdings_by_ticker["VWRL"].id,
            tipo="acquisto",
            quantita=18.0,
            prezzo_unitario=100.50,
            valuta="EUR",
            data_transazione=datetime(2024, 12, 10),
            note="Fine 2024 - Dividendi raccolti"
        ),
        Transaction(
            holding_id=holdings_by_ticker["VWRL"].id,
            tipo="acquisto",
            quantita=12.0,
            prezzo_unitario=108.20,
            valuta="EUR",
            data_transazione=datetime(2025, 6, 15),
            note="Metà 2025 - Yield attraente"
        )
    ]
    
    for t in transactions_demo:
        db.add(t)
        holding = db.query(Holding).get(t.holding_id)
        print(f"  ✓ {t.tipo.capitalize()} {t.quantita} {holding.ticker} @ €{t.prezzo_unitario} ({t.data_transazione.strftime('%b %Y')})")
    
    db.commit()
    
    # Aggiorna quantità e prezzo medio per ogni holding
    print("\n📈 Calcolo quantità e prezzi medi...")
    for holding in db.query(Holding).all():
        transazioni = db.query(Transaction).filter(
            Transaction.holding_id == holding.id,
            Transaction.tipo == "acquisto"
        ).all()
        
        if transazioni:
            totale_quantita = sum(t.quantita for t in transazioni)
            totale_valore = sum(t.quantita * t.prezzo_unitario for t in transazioni)
            prezzo_medio = totale_valore / totale_quantita if totale_quantita > 0 else 0
            
            holding.quantita = totale_quantita
            holding.prezzo_medio = prezzo_medio
            
            print(f"  {holding.ticker}: {totale_quantita} quote, prezzo medio €{prezzo_medio:.2f}")
    
    db.commit()
    
    print("\n✅ Database inizializzato con successo!")
    print("\n📈 Portafoglio demo creato:")
    print("   ETF (2): VWRP, VUAA")
    print("   Azioni (2): AAPL, MSFT")
    print("   Fondi (2): EQQQ, VWRL")
    print("\n📅 Transazioni storiche:")
    print("   - Inizio 2024 (Gennaio)")
    print("   - Fine 2024 (Dicembre)")
    print("   - Metà 2025 (Giugno)")
    print("\n🚀 Avvia il server con: cd backend && python main.py")
    print("   Poi apri http://localhost:8000 nel browser")

except Exception as e:
    print(f"\n❌ Errore: {e}")
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
