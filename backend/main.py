from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
import os

from database import engine, get_db, Base
from models import Holding, Transaction, PriceHistory, AssetClass
from schemas import (
    HoldingCreate, Holding as HoldingSchema, HoldingDetail,
    TransactionCreate, Transaction as TransactionSchema,
    PortfolioSummary
)
from api_prices import get_stock_quote, get_daily_prices, convert_to_eur, search_symbol

# Crea tabelle database
print("📦 Inizializzazione database...")
Base.metadata.create_all(bind=engine)

# Inizializza con dati demo se vuoto
def init_demo_data(db: Session):
    """Inizializza database con dati demo se non ci sono holdings"""
    holdings_count = db.query(Holding).count()
    if holdings_count == 0:
        print("📊 Database vuoto - creo dati demo...")
        
        # Crea holdings
        holdings_data = [
            {"ticker": "VWRP", "nome": "Vanguard FTSE All-World UCITS ETF Accumulating", "asset_class": AssetClass.ETF, "valuta": "EUR"},
            {"ticker": "VUAA", "nome": "Vanguard S&P 500 UCITS ETF Accumulating", "asset_class": AssetClass.ETF, "valuta": "EUR"},
            {"ticker": "AAPL", "nome": "Apple Inc.", "asset_class": AssetClass.AZIONE, "valuta": "USD"},
            {"ticker": "MSFT", "nome": "Microsoft Corporation", "asset_class": AssetClass.AZIONE, "valuta": "USD"},
            {"ticker": "EQQQ", "nome": "Invesco EQQQ Nasdaq-100 UCITS ETF", "asset_class": AssetClass.FONDO, "valuta": "EUR"},
            {"ticker": "VWRL", "nome": "Vanguard FTSE All-World UCITS ETF Distributing", "asset_class": AssetClass.FONDO, "valuta": "EUR"},
        ]
        
        for h in holdings_data:
            holding = Holding(**h, quantita=0.0, prezzo_medio=0.0)
            db.add(holding)
        
        db.commit()
        
        # Recupera holdings create
        holdings_by_ticker = {h.ticker: h for h in db.query(Holding).all()}
        
        # Transazioni demo
        transactions_data = [
            # VWRP
            {"ticker": "VWRP", "tipo": "acquisto", "quantita": 20.0, "prezzo": 96.50, "data": datetime(2024, 1, 15), "note": "Inizio 2024"},
            {"ticker": "VWRP", "tipo": "acquisto", "quantita": 15.0, "prezzo": 108.20, "data": datetime(2024, 12, 10), "note": "Fine 2024"},
            {"ticker": "VWRP", "tipo": "acquisto", "quantita": 10.0, "prezzo": 115.80, "data": datetime(2025, 6, 15), "note": "Metà 2025"},
            # VUAA
            {"ticker": "VUAA", "tipo": "acquisto", "quantita": 15.0, "prezzo": 87.30, "data": datetime(2024, 1, 15), "note": "Inizio 2024"},
            {"ticker": "VUAA", "tipo": "acquisto", "quantita": 12.0, "prezzo": 102.50, "data": datetime(2024, 12, 10), "note": "Fine 2024"},
            {"ticker": "VUAA", "tipo": "acquisto", "quantita": 8.0, "prezzo": 118.90, "data": datetime(2025, 6, 15), "note": "Metà 2025"},
            # AAPL
            {"ticker": "AAPL", "tipo": "acquisto", "quantita": 10.0, "prezzo": 185.50, "data": datetime(2024, 1, 15), "note": "Inizio 2024"},
            {"ticker": "AAPL", "tipo": "acquisto", "quantita": 8.0, "prezzo": 232.80, "data": datetime(2024, 12, 10), "note": "Fine 2024"},
            {"ticker": "AAPL", "tipo": "acquisto", "quantita": 5.0, "prezzo": 245.20, "data": datetime(2025, 6, 15), "note": "Metà 2025"},
            # MSFT
            {"ticker": "MSFT", "tipo": "acquisto", "quantita": 8.0, "prezzo": 375.20, "data": datetime(2024, 1, 15), "note": "Inizio 2024"},
            {"ticker": "MSFT", "tipo": "acquisto", "quantita": 6.0, "prezzo": 438.50, "data": datetime(2024, 12, 10), "note": "Fine 2024"},
            {"ticker": "MSFT", "tipo": "acquisto", "quantita": 4.0, "prezzo": 485.30, "data": datetime(2025, 6, 15), "note": "Metà 2025"},
            # EQQQ
            {"ticker": "EQQQ", "tipo": "acquisto", "quantita": 5.0, "prezzo": 415.60, "data": datetime(2024, 1, 15), "note": "Inizio 2024"},
            {"ticker": "EQQQ", "tipo": "acquisto", "quantita": 4.0, "prezzo": 498.30, "data": datetime(2024, 12, 10), "note": "Fine 2024"},
            {"ticker": "EQQQ", "tipo": "acquisto", "quantita": 3.0, "prezzo": 572.40, "data": datetime(2025, 6, 15), "note": "Metà 2025"},
            # VWRL
            {"ticker": "VWRL", "tipo": "acquisto", "quantita": 25.0, "prezzo": 89.80, "data": datetime(2024, 1, 15), "note": "Inizio 2024"},
            {"ticker": "VWRL", "tipo": "acquisto", "quantita": 18.0, "prezzo": 100.50, "data": datetime(2024, 12, 10), "note": "Fine 2024"},
            {"ticker": "VWRL", "tipo": "acquisto", "quantita": 12.0, "prezzo": 108.20, "data": datetime(2025, 6, 15), "note": "Metà 2025"},
        ]
        
        for t in transactions_data:
            holding = holdings_by_ticker[t["ticker"]]
            trans = Transaction(
                holding_id=holding.id,
                tipo=t["tipo"],
                quantita=t["quantita"],
                prezzo_unitario=t["prezzo"],
                valuta=holding.valuta,
                data_transazione=t["data"],
                note=t["note"]
            )
            db.add(trans)
            
            # Aggiorna holding
            if t["tipo"] == "acquisto":
                valore_esistente = holding.quantita * holding.prezzo_medio
                valore_nuovo = t["quantita"] * t["prezzo"]
                holding.quantita += t["quantita"]
                if holding.quantita > 0:
                    holding.prezzo_medio = (valore_esistente + valore_nuovo) / holding.quantita
        
        db.commit()
        print(f"✅ Creati {len(holdings_data)} holdings e {len(transactions_data)} transazioni demo")
    else:
        print(f"✅ Database già popolato con {holdings_count} holdings")

app = FastAPI(title="Portfolio Tracker API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path per frontend
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

print(f"📁 BASE_DIR: {BASE_DIR}")
print(f"📁 FRONTEND_DIR: {FRONTEND_DIR}")

# Mount static files
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print(f"✅ Static files montati da {STATIC_DIR}")

@app.on_event("startup")
async def startup_event():
    """Inizializza database all'avvio"""
    db = next(get_db())
    try:
        init_demo_data(db)
    finally:
        db.close()

@app.get("/")
async def root():
    """Serve la dashboard principale"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    print(f"📄 Cerco index.html in: {index_path}")
    if os.path.exists(index_path):
        print(f"✅ Trovato index.html")
        return FileResponse(index_path)
    print(f"❌ index.html non trovato")
    return HTMLResponse("<h1>Portfolio Tracker API</h1><p>Backend attivo! Frontend non trovato.</p>")

@app.get("/api/holdings", response_model=List[HoldingSchema])
def get_holdings(asset_class: Optional[str] = None, db: Session = Depends(get_db)):
    """Ottieni lista holdings"""
    query = db.query(Holding)
    if asset_class:
        query = query.filter(Holding.asset_class == asset_class)
    return query.all()

@app.get("/api/holdings/{holding_id}", response_model=HoldingDetail)
def get_holding_detail(holding_id: int, db: Session = Depends(get_db)):
    """Ottieni dettaglio holding"""
    holding = db.query(Holding).filter(Holding.id == holding_id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding non trovata")
    
    prezzo_attuale = holding.prezzo_medio * 1.05
    valore_attuale = holding.quantita * prezzo_attuale
    valore_investito = holding.quantita * holding.prezzo_medio
    guadagno = valore_attuale - valore_investito
    percent_guadagno = (guadagno / valore_investito * 100) if valore_investito > 0 else 0
    
    return HoldingDetail(
        id=holding.id, ticker=holding.ticker, nome=holding.nome,
        asset_class=holding.asset_class, valuta=holding.valuta,
        quantita=holding.quantita, prezzo_medio=holding.prezzo_medio,
        prezzo_attuale=prezzo_attuale, valore_attuale=valore_attuale,
        guadagno_perdita=guadagno, percentuale_guadagno=percent_guadagno
    )

@app.post("/api/holdings", response_model=HoldingSchema)
def create_holding(holding: HoldingCreate, db: Session = Depends(get_db)):
    """Crea nuova holding"""
    existing = db.query(Holding).filter(Holding.ticker == holding.ticker).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ticker già esistente")
    
    db_holding = Holding(**holding.dict())
    db.add(db_holding)
    db.commit()
    db.refresh(db_holding)
    return db_holding

@app.put("/api/holdings/{holding_id}", response_model=HoldingSchema)
def update_holding(holding_id: int, holding_update: HoldingUpdate, db: Session = Depends(get_db)):
    """Aggiorna holding"""
    db_holding = db.query(Holding).filter(Holding.id == holding_id).first()
    if not db_holding:
        raise HTTPException(status_code=404, detail="Holding non trovata")
    
    update_data = holding_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_holding, field, value)
    
    db.commit()
    db.refresh(db_holding)
    return db_holding

@app.delete("/api/holdings/{holding_id}")
def delete_holding(holding_id: int, db: Session = Depends(get_db)):
    """Elimina holding"""
    db_holding = db.query(Holding).filter(Holding.id == holding_id).first()
    if not db_holding:
        raise HTTPException(status_code=404, detail="Holding non trovata")
    
    db.delete(db_holding)
    db.commit()
    return {"message": "Holding eliminata"}

@app.get("/api/transactions", response_model=List[TransactionSchema])
def get_transactions(holding_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Ottieni transazioni"""
    query = db.query(Transaction)
    if holding_id:
        query = query.filter(Transaction.holding_id == holding_id)
    return query.order_by(Transaction.data_transazione.desc()).all()

@app.post("/api/transactions", response_model=TransactionSchema)
def create_transaction(transaction: TransactionCreate, db: Session = Depends(get_db)):
    """Registra transazione"""
    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)
    
    holding = db.query(Holding).filter(Holding.id == transaction.holding_id).first()
    if holding:
        if transaction.tipo == "acquisto":
            valore_esistente = holding.quantita * holding.prezzo_medio
            valore_nuovo = transaction.quantita * transaction.prezzo_unitario
            holding.quantita += transaction.quantita
            if holding.quantita > 0:
                holding.prezzo_medio = (valore_esistente + valore_nuovo) / holding.quantita
        elif transaction.tipo == "vendita":
            holding.quantita -= transaction.quantita
    
    db.commit()
    db.refresh(db_transaction)
    return db_transaction

@app.get("/api/portfolio/summary", response_model=PortfolioSummary)
def get_portfolio_summary(db: Session = Depends(get_db)):
    """Ottieni riepilogo portafoglio"""
    holdings = db.query(Holding).all()
    
    valore_totale = 0.0
    valore_investito = 0.0
    
    for holding in holdings:
        prezzo_attuale = holding.prezzo_medio * 1.05
        valore_totale += holding.quantita * prezzo_attuale
        valore_investito += holding.quantita * holding.prezzo_medio
    
    guadagno = valore_totale - valore_investito
    percent_guadagno = (guadagno / valore_investito * 100) if valore_investito > 0 else 0
    
    return PortfolioSummary(
        valore_totale=valore_totale,
        valore_investito=valore_investito,
        guadagno_perdita=guadagno,
        percentuale_guadagno=percent_guadagno,
        numero_holdings=len(holdings)
    )

@app.get("/api/portfolio/history")
def get_portfolio_history(days: int = 90, db: Session = Depends(get_db)):
    """Ottieni storico portafoglio - dati REALI basati su transazioni"""
    holdings = db.query(Holding).all()
    if not holdings:
        return []
    
    # Ottieni tutte le transazioni
    all_transactions = db.query(Transaction).all()
    
    # Crea storico giorno per giorno
    today = datetime.now()
    history = []
    
    for i in range(days):
        date = today - timedelta(days=days-1-i)
        
        # Calcola valore portafoglio a questa data
        valore_totale = 0.0
        valore_investito = 0.0
        
        for holding in holdings:
            # Transazioni fino a questa data
            holding_txs = [t for t in all_transactions 
                          if t.holding_id == holding.id and t.data_transazione <= date]
            
            if holding_txs:
                # Calcola quantità e prezzo medio a questa data
                quantita_data = 0.0
                valore_totale_acquisti = 0.0
                
                for tx in holding_txs:
                    if tx.tipo == "acquisto":
                        quantita_data += tx.quantita
                        valore_totale_acquisti += tx.quantita * tx.prezzo_unitario
                    elif tx.tipo == "vendita":
                        quantita_data -= tx.quantita
                
                if quantita_data > 0:
                    prezzo_medio_data = valore_totale_acquisti / quantita_data
                    # Simula crescita mercato (+5% medio annuale = ~0.013% al giorno)
                    giorni_dalla_prima_tx = (date - holding_txs[0].data_transazione).days
                    fattore_crescita = 1.0 + (giorni_dalla_prima_tx * 0.0002)
                    prezzo_attuale_data = prezzo_medio_data * fattore_crescita
                    
                    valore_totale += quantita_data * prezzo_attuale_data
                    valore_investito += quantita_data * prezzo_medio_data
        
        history.append({
            "data": date.strftime("%Y-%m-%d"),
            "valore_totale": round(valore_totale, 2),
            "valore_investito": round(valore_investito, 2)
        })
    
    return history

@app.get("/api/portfolio/history/{holding_id}")
def get_holding_history(holding_id: int, days: int = 90, db: Session = Depends(get_db)):
    """Ottieni storico singolo titolo"""
    holding = db.query(Holding).filter(Holding.id == holding_id).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding non trovata")
    
    transactions = db.query(Transaction).filter(
        Transaction.holding_id == holding_id
    ).order_by(Transaction.data_transazione).all()
    
    if not transactions:
        return []
    
    today = datetime.now()
    history = []
    
    for i in range(days):
        date = today - timedelta(days=days-1-i)
        
        # Transazioni fino a questa data
        txs_fino_a_data = [t for t in transactions if t.data_transazione <= date]
        
        if txs_fino_a_data:
            quantita = 0.0
            valore_investito = 0.0
            
            for tx in txs_fino_a_data:
                if tx.tipo == "acquisto":
                    quantita += tx.quantita
                    valore_investito += tx.quantita * tx.prezzo_unitario
                elif tx.tipo == "vendita":
                    quantita -= tx.quantita
            
            if quantita > 0:
                prezzo_medio = valore_investito / quantita
                # Simula crescita
                giorni_dalla_prima = (date - txs_fino_a_data[0].data_transazione).days
                fattore = 1.0 + (giorni_dalla_prima * 0.0002)
                valore_totale = quantita * prezzo_medio * fattore
                
                history.append({
                    "data": date.strftime("%Y-%m-%d"),
                    "valore_totale": round(valore_totale, 2),
                    "quantita": round(quantita, 2)
                })
        else:
            history.append({
                "data": date.strftime("%Y-%m-%d"),
                "valore_totale": 0,
                "quantita": 0
            })
    
    return history

@app.get("/api/search/{query}")
def search_instruments(query: str):
    """Cerca strumenti"""
    results = search_symbol(query)
    return results

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    print(f"🚀 Avvio server su porta {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
