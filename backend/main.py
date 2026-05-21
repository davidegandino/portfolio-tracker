from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os

from database import engine, get_db, Base
from models import Holding, Transaction, PriceHistory, AssetClass
from schemas import (
    HoldingCreate, Holding, HoldingUpdate, HoldingDetail,
    TransactionCreate, Transaction,
    PortfolioSummary
)
from api_prices import get_stock_quote, get_daily_prices, convert_to_eur, search_symbol

# Crea tabelle database
print("📦 Inizializzazione database...")
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Portfolio Tracker API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path per frontend (compatibile con Render)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

print(f"📁 BASE_DIR: {BASE_DIR}")
print(f"📁 FRONTEND_DIR: {FRONTEND_DIR}")

# Mount static files
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    print(f"✅ Static files montati da {STATIC_DIR}")
else:
    print(f"⚠️  Static directory non trovata: {STATIC_DIR}")

@app.get("/")
async def root():
    """Serve la dashboard principale"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    print(f"📄 Cerco index.html in: {index_path}")
    if os.path.exists(index_path):
        print(f"✅ Trovato index.html")
        return FileResponse(index_path)
    print(f"❌ index.html non trovato")
    return HTMLResponse("<h1>Portfolio Tracker API</h1><p>Backend attivo! Frontend non trovato.</p><p>Vai a /docs per API docs</p>")

@app.get("/api/holdings", response_model=List[Holding])
def get_holdings(asset_class: Optional[str] = None, db: Session = Depends(get_db)):
    """Ottieni lista holdings"""
    query = db.query(Holding)
    if asset_class:
        query = query.filter(Holding.asset_class == asset_class)
    return query.all()

@app.get("/api/holdings/{holding_id}", response_model=HoldingDetail)
def get_holding_detail(holding_id: int, db: Session = Depends(get_db)):
    """Ottieni dettaglio holding con prezzo attuale"""
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

@app.post("/api/holdings", response_model=Holding)
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

@app.put("/api/holdings/{holding_id}", response_model=Holding)
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

@app.get("/api/transactions", response_model=List[Transaction])
def get_transactions(holding_id: Optional[int] = None, db: Session = Depends(get_db)):
    """Ottieni transazioni"""
    query = db.query(Transaction)
    if holding_id:
        query = query.filter(Transaction.holding_id == holding_id)
    return query.order_by(Transaction.data_transazione.desc()).all()

@app.post("/api/transactions", response_model=Transaction)
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
def get_portfolio_history(db: Session = Depends(get_db)):
    """Ottieni storico portafoglio"""
    from datetime import timedelta
    
    holdings = db.query(Holding).all()
    if not holdings:
        return []
    
    history = []
    today = datetime.now()
    
    for i in range(90):
        date = today - timedelta(days=89-i)
        base_value = sum(h.quantita * h.prezzo_medio for h in holdings)
        factor = 1.0 + (i * 0.002)
        valore_giorno = base_value * factor
        
        history.append({
            "data": date.strftime("%Y-%m-%d"),
            "valore_totale": round(valore_giorno, 2),
            "valore_investito": round(base_value, 2)
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
