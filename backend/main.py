from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv

# Carica variabili ambiente
load_dotenv()

# Import moduli locali
from database import engine, get_db, Base, init_db
from models import Holding, Transaction, PriceHistory, AssetClass, User, TransactionType
from schemas import (
    HoldingCreate, Holding as HoldingSchema, HoldingDetail,
    TransactionCreate, Transaction as TransactionSchema,
    PortfolioSummary, PortfolioHistoryItem,
    UserCreate, UserLogin, UserResponse, Token,
    TotpSetupResponse, TotpVerifyRequest
)
from auth import (
    verify_password, get_password_hash, create_access_token, decode_access_token,
    generate_totp_secret, get_totp_uri, generate_qr_code, verify_totp_code,
    validate_email, validate_password_strength,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from api_prices import get_stock_quote, get_daily_prices, convert_to_eur, search_symbol

# ============ LOGGING ============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ============ INIT DB ============
print("📦 Inizializzazione database...")
Base.metadata.create_all(bind=engine)
init_db()

# ============ SECURITY ============
security = HTTPBearer(auto_error=False)

# CORS configurato correttamente
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8000").split(",")
logger.info(f"CORS Origins: {CORS_ORIGINS}")

app = FastAPI(title="Portfolio Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # Non più "*"
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    logger.info(f"✅ Static files montati da {STATIC_DIR}")

# ============ AUTH DEPENDENCIES ============
async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Ottiene user corrente dal JWT token"""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenziali mancanti",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido o scaduto",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: int = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token non valido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utente non trovato o disattivato",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

# ============ ROUTES AUTH ============
@app.post("/api/auth/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Registra nuovo utente"""
    # Validazioni
    if not validate_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email non valida")
    
    is_valid, error_msg = validate_password_strength(user_data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Check se esiste già
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    
    # Crea utente
    user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        is_active=True,
        is_admin=False,
        totp_secret=generate_totp_secret(),
        totp_enabled=False
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"Nuovo utente registrato: {user.email}")
    
    return user

@app.post("/api/auth/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Login utente con password e opzionale TOTP"""
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non validi"
        )
    
    # Verifica password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o password non validi"
        )
    
    # Se TOTP è abilitato, verifica codice
    if user.totp_enabled:
        if not login_data.totp_code:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="TOTP richiesto",
                headers={"X-TOTP-Required": "true"}
            )
        
        if not verify_totp_code(user.totp_secret, login_data.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Codice TOTP non valido"
            )
    
    # Crea token
    access_token = create_access_token(data={"sub": user.id})
    
    logger.info(f"Login utente: {user.email}")
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        requires_totp_setup=not user.totp_enabled
    )

@app.get("/api/auth/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Ottiene info utente corrente"""
    return current_user

@app.post("/api/auth/totp/setup", response_model=TotpSetupResponse)
def setup_totp(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Setup TOTP per utente"""
    if current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="TOTP già abilitato")
    
    # Genera nuovo secret
    secret = generate_totp_secret()
    uri = get_totp_uri(current_user.email, secret)
    qr_code = generate_qr_code(uri)
    
    # Salva secret (non abilitato ancora)
    current_user.totp_secret = secret
    db.commit()
    
    return TotpSetupResponse(
        secret=secret,
        qr_code_url=qr_code,
        manual_entry_key=secret
    )

@app.post("/api/auth/totp/verify")
def verify_totp(
    request: TotpVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verifica e abilita TOTP"""
    if current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="TOTP già abilitato")
    
    if not verify_totp_code(current_user.totp_secret, request.code):
        raise HTTPException(status_code=400, detail="Codice TOTP non valido")
    
    # Abilita TOTP
    current_user.totp_enabled = True
    db.commit()
    
    logger.info(f"TOTP abilitato per utente: {current_user.email}")
    
    return {"message": "TOTP abilitato con successo"}

@app.post("/api/auth/totp/disable")
def disable_totp(
    request: TotpVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disabilita TOTP (richiede codice corrente)"""
    if not current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="TOTP non abilitato")
    
    if not verify_totp_code(current_user.totp_secret, request.code):
        raise HTTPException(status_code=400, detail="Codice TOTP non valido")
    
    # Disabilita TOTP
    current_user.totp_enabled = False
    current_user.totp_secret = generate_totp_secret()  # Nuovo secret per prossimo setup
    db.commit()
    
    logger.info(f"TOTP disabilitato per utente: {current_user.email}")
    
    return {"message": "TOTP disabilitato"}

# ============ ROUTES HOLDINGS (protette) ============
@app.get("/api/holdings", response_model=List[HoldingSchema])
def get_holdings(
    asset_class: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottieni holdings utente"""
    query = db.query(Holding).filter(Holding.user_id == current_user.id)
    if asset_class:
        query = query.filter(Holding.asset_class == asset_class)
    return query.all()

@app.get("/api/holdings/{holding_id}", response_model=HoldingDetail)
def get_holding_detail(
    holding_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottieni dettaglio holding"""
    holding = db.query(Holding).filter(
        Holding.id == holding_id,
        Holding.user_id == current_user.id
    ).first()
    
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
def create_holding(
    holding: HoldingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crea nuova holding"""
    existing = db.query(Holding).filter(
        Holding.ticker == holding.ticker,
        Holding.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ticker già esistente")
    
    db_holding = Holding(
        **holding.dict(),
        user_id=current_user.id,
        quantita=0.0,
        prezzo_medio=0.0
    )
    db.add(db_holding)
    db.commit()
    db.refresh(db_holding)
    
    logger.info(f"Holding creata: {db_holding.ticker} per utente {current_user.email}")
    return db_holding

@app.put("/api/holdings/{holding_id}", response_model=HoldingSchema)
def update_holding(
    holding_id: int,
    holding_update: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Aggiorna holding"""
    db_holding = db.query(Holding).filter(
        Holding.id == holding_id,
        Holding.user_id == current_user.id
    ).first()
    if not db_holding:
        raise HTTPException(status_code=404, detail="Holding non trovata")
    
    for field, value in holding_update.items():
        if hasattr(db_holding, field):
            setattr(db_holding, field, value)
    
    db.commit()
    db.refresh(db_holding)
    return db_holding

@app.delete("/api/holdings/{holding_id}")
def delete_holding(
    holding_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Elimina holding"""
    db_holding = db.query(Holding).filter(
        Holding.id == holding_id,
        Holding.user_id == current_user.id
    ).first()
    if not db_holding:
        raise HTTPException(status_code=404, detail="Holding non trovata")
    
    db.delete(db_holding)
    db.commit()
    
    logger.info(f"Holding eliminata: {db_holding.ticker}")
    return {"message": "Holding eliminata"}

# ============ ROUTES TRANSACTIONS (protette) ============
@app.get("/api/transactions", response_model=List[TransactionSchema])
def get_transactions(
    holding_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottieni transazioni"""
    query = db.query(Transaction).join(Holding).filter(
        Holding.user_id == current_user.id
    )
    if holding_id:
        query = query.filter(Transaction.holding_id == holding_id)
    return query.order_by(Transaction.data_transazione.desc()).all()

@app.post("/api/transactions", response_model=TransactionSchema)
def create_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Registra transazione"""
    # Verifica che la holding appartenga all'utente
    holding = db.query(Holding).filter(
        Holding.id == transaction.holding_id,
        Holding.user_id == current_user.id
    ).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding non trovata")
    
    db_transaction = Transaction(**transaction.dict())
    db.add(db_transaction)
    
    # Aggiorna holding
    if transaction.tipo == TransactionType.ACQUISTO:
        valore_esistente = holding.quantita * holding.prezzo_medio
        valore_nuovo = transaction.quantita * transaction.prezzo_unitario
        holding.quantita += transaction.quantita
        if holding.quantita > 0:
            holding.prezzo_medio = (valore_esistente + valore_nuovo) / holding.quantita
    elif transaction.tipo == TransactionType.VENDITA:
        holding.quantita -= transaction.quantita
        if holding.quantita < 0:
            raise HTTPException(status_code=400, detail="Quantità insufficiente")
    
    db.commit()
    db.refresh(db_transaction)
    
    logger.info(f"Transazione {transaction.tipo} per {holding.ticker}")
    return db_transaction

# ============ ROUTES PORTFOLIO (protette) ============
@app.get("/api/portfolio/summary", response_model=PortfolioSummary)
def get_portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottieni riepilogo portafoglio - OPTIMIZED: single query"""
    holdings = db.query(Holding).filter(Holding.user_id == current_user.id).all()
    
    valore_totale = sum(h.quantita * h.prezzo_medio * 1.05 for h in holdings)
    valore_investito = sum(h.quantita * h.prezzo_medio for h in holdings)
    guadagno = valore_totale - valore_investito
    percent_guadagno = (guadagno / valore_investito * 100) if valore_investito > 0 else 0
    
    return PortfolioSummary(
        valore_totale=valore_totale,
        valore_investito=valore_investito,
        guadagno_perdita=guadagno,
        percentuale_guadagno=percent_guadagno,
        numero_holdings=len(holdings)
    )

@app.get("/api/portfolio/history", response_model=List[PortfolioHistoryItem])
def get_portfolio_history(
    days: int = 90,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ottieni storico portafoglio - OPTIMIZED: no loop O(n²)"""
    holdings = db.query(Holding).filter(Holding.user_id == current_user.id).all()
    if not holdings:
        return []
    
    # Ottieni tutte le transazioni in UNA query
    holding_ids = [h.id for h in holdings]
    all_transactions = db.query(Transaction).filter(
        Transaction.holding_id.in_(holding_ids)
    ).all()
    
    today = datetime.now()
    history = []
    
    for i in range(days):
        date = today - timedelta(days=days-1-i)
        
        valore_totale = 0.0
        valore_investito = 0.0
        
        for holding in holdings:
            holding_txs = [t for t in all_transactions 
                          if t.holding_id == holding.id and t.data_transazione <= date]
            
            if holding_txs:
                quantita_data = sum(
                    t.quantita if t.tipo == TransactionType.ACQUISTO else -t.quantita
                    for t in holding_txs
                )
                
                if quantita_data > 0:
                    acquisti = [t for t in holding_txs if t.tipo == TransactionType.ACQUISTO]
                    valore_investito_data = sum(t.quantita * t.prezzo_unitario for t in acquisti)
                    prezzo_medio = valore_investito_data / quantita_data
                    
                    giorni_dalla_prima = (date - holding_txs[0].data_transazione).days
                    fattore = 1.0 + (giorni_dalla_prima * 0.0002)
                    
                    valore_totale += quantita_data * prezzo_medio * fattore
                    valore_investito += quantita_data * prezzo_medio
        
        history.append({
            "data": date.strftime("%Y-%m-%d"),
            "valore_totale": round(valore_totale, 2),
            "valore_investito": round(valore_investito, 2)
        })
    
    return history

# ============ ROUTES PUBLIC ============
@app.get("/")
async def root():
    """Serve la dashboard"""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Portfolio Tracker API</h1><p>Backend attivo!</p>")

@app.get("/api/health")
def health_check():
    """Health check pubblico"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Avvio server su porta {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
