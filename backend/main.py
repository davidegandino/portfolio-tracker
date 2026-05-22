import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel, Field, validator
from jose import JWTError, jwt
import pyotp
import qrcode
import base64
from io import BytesIO

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal, engine, Base, get_db, init_db
from models import User, Holding, Transaction, TransactionType
from schemas import (
    UserCreate, UserLogin, UserResponse, Token, HoldingCreate, 
    HoldingResponse, TransactionCreate, TransactionResponse,
    PortfolioSummary, PortfolioHistoryPoint
)
from auth import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    verify_password, get_password_hash, create_access_token,
    verify_totp_code, generate_totp_secret, get_totp_uri
)
from api_prices import get_stock_quote, get_daily_prices, convert_to_eur, search_symbol

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("AVVIO SERVER - Caricamento configurazione...")
logger.info("=" * 60)

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
JWT_SECRET = os.getenv("JWT_SECRET", "fallback_secret_change_in_production")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:8000").split(",")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@portfolio.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

logger.info(f"ALPHA_VANTAGE_API_KEY: {'***' if ALPHA_VANTAGE_API_KEY else 'MISSING'}")
logger.info(f"JWT_SECRET: {'***' if JWT_SECRET else 'MISSING'}")
logger.info(f"ENVIRONMENT: {ENVIRONMENT}")
logger.info(f"CORS_ORIGINS: {CORS_ORIGINS}")
logger.info(f"ADMIN_EMAIL: {ADMIN_EMAIL}")
logger.info(f"ADMIN_PASSWORD: {'***' if ADMIN_PASSWORD else 'MISSING'}")

if os.getenv("JWT_SECRET"):
    SECRET_KEY = os.getenv("JWT_SECRET")
    logger.info("✅ JWT_SECRET caricato da variabile ambiente")
else:
    logger.warning("⚠️ JWT_SECRET non impostato, uso fallback")

logger.info("Inizializzazione database...")
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Tabelle database create")
    init_db()
    logger.info("✅ Admin user inizializzato")
except Exception as e:
    logger.error(f"❌ Errore database: {e}")
    raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 FastAPI startup...")
    yield
    logger.info("🛑 FastAPI shutdown...")

app = FastAPI(title="Portfolio Tracker API", version="2.0.0", lifespan=lifespan)

logger.info(f"Configura CORS per: {CORS_ORIGINS}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(status_code=401, detail="Credenziali non valide", headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user

@app.get("/", response_class=HTMLResponse)
async def root():
    logger.info("Richiesta pagina login")
    try:
        frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.exists(index_path):
            logger.info(f"Servo index.html da: {index_path}")
            return FileResponse(index_path)
        else:
            logger.error(f"index.html non trovato in {frontend_dir}")
            return HTMLResponse(content="<h1>Portfolio Tracker</h1><p>Server online!</p>", status_code=200)
    except Exception as e:
        logger.error(f"Errore serving index.html: {e}")
        return HTMLResponse(content="<h1>Errore</h1><p>Contatta l'admin</p>", status_code=500)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    logger.info("Richiesta dashboard")
    try:
        frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")
        dashboard_path = os.path.join(frontend_dir, "dashboard.html")
        if os.path.exists(dashboard_path):
            logger.info(f"Servo dashboard.html da: {dashboard_path}")
            return FileResponse(dashboard_path)
        else:
            logger.error(f"dashboard.html non trovato in {frontend_dir}")
            return HTMLResponse(content="<h1>Dashboard</h1><p>Caricamento...</p>", status_code=200)
    except Exception as e:
        logger.error(f"Errore serving dashboard.html: {e}")
        return HTMLResponse(content="<h1>Errore</h1><p>Contatta l'admin</p>", status_code=500)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "environment": ENVIRONMENT, "timestamp": datetime.now().isoformat()}

@app.post("/api/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    logger.info(f"Tentativo registrazione: {user_data.email}")
    existing = db.query(User).filter(User.email == user_data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email già registrata")
    user = User(email=user_data.email, hashed_password=get_password_hash(user_data.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info(f"✅ Utente registrato: {user.email}")
    return user

@app.post("/api/auth/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    logger.info(f"Tentativo login: {form_data.username}")
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user:
        logger.warning(f"Utente non trovato: {form_data.username}")
        raise HTTPException(status_code=401, detail="Email o password errati")
    if not verify_password(form_data.password, user.hashed_password):
        logger.warning(f"Password errata per: {form_data.username}")
        raise HTTPException(status_code=401, detail="Email o password errati")
    if user.totp_enabled and user.totp_secret:
        totp_code = form_data.kwargs.get("totp")
        if not totp_code:
            logger.info(f"TOTP richiesto per {form_data.username}")
            raise HTTPException(status_code=401, detail="TOTP_REQUIRED", headers={"X-TOTP-Required": "true"})
        if not verify_totp_code(user.totp_secret, totp_code):
            logger.warning(f"TOTP errato per: {form_data.username}")
            raise HTTPException(status_code=401, detail="Codice 2FA errato")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    logger.info(f"✅ Login riuscito: {user.email}")
    return {"access_token": access_token, "token_type": "bearer", "totp_enabled": user.totp_enabled}

@app.get("/api/auth/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/api/auth/totp/setup")
async def setup_totp(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"Setup TOTP per: {current_user.email}")
    if current_user.totp_enabled:
        raise HTTPException(status_code=400, detail="TOTP già attivo")
    secret = generate_totp_secret()
    totp_uri = get_totp_uri(current_user.email, secret)
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    current_user.totp_secret = secret
    db.commit()
    logger.info(f"✅ TOTP generato per: {current_user.email}")
    return {"secret": secret, "totp_uri": totp_uri, "qr_code": f"data:image/png;base64,{qr_code_base64}"}

class TOTPVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)

@app.post("/api/auth/totp/verify")
async def verify_totp_endpoint(
    request: TOTPVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Verifica TOTP per: {current_user.email}")
    if not current_user.totp_secret:
        raise HTTPException(status_code=400, detail="Setup TOTP non iniziato")
    if not verify_totp_code(current_user.totp_secret, request.code):
        raise HTTPException(status_code=400, detail="Codice non valido")
    current_user.totp_enabled = True
    db.commit()
    logger.info(f"✅ TOTP attivato per: {current_user.email}")
    return {"message": "TOTP attivato con successo"}

@app.post("/api/auth/totp/disable")
async def disable_totp(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    logger.info(f"Disabilita TOTP per: {current_user.email}")
    current_user.totp_enabled = False
    current_user.totp_secret = None
    db.commit()
    logger.info(f"✅ TOTP disabilitato per: {current_user.email}")
    return {"message": "TOTP disabilitato"}

@app.get("/api/holdings", response_model=List[HoldingResponse])
async def get_holdings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    holdings = db.query(Holding).filter(Holding.user_id == current_user.id).offset(skip).limit(limit).all()
    for h in holdings:
        quote = get_stock_quote(h.symbol)
        if quote:
            h.current_price = quote["price"]
    db.commit()
    return holdings

@app.post("/api/holdings", response_model=HoldingResponse)
async def create_holding(holding_data: HoldingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logger.info(f"Crea holding: {holding_data.symbol} per {current_user.email}")
    quote = get_stock_quote(holding_data.symbol)
    current_price = quote["price"] if quote else holding_data.average_price
    holding = Holding(**holding_data.dict(), user_id=current_user.id, current_price=current_price)
    db.add(holding)
    db.commit()
    db.refresh(holding)
    logger.info(f"✅ Holding creata: {holding.symbol}")
    return holding

@app.put("/api/holdings/{holding_id}", response_model=HoldingResponse)
async def update_holding(holding_id: int, holding_data: HoldingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    holding = db.query(Holding).filter(and_(Holding.id == holding_id, Holding.user_id == current_user.id)).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding non trovata")
    for key, value in holding_data.dict().items():
        setattr(holding, key, value)
    quote = get_stock_quote(holding.symbol)
    if quote:
        holding.current_price = quote["price"]
    db.commit()
    db.refresh(holding)
    logger.info(f"✅ Holding aggiornata: {holding.symbol}")
    return holding

@app.delete("/api/holdings/{holding_id}")
async def delete_holding(holding_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    holding = db.query(Holding).filter(and_(Holding.id == holding_id, Holding.user_id == current_user.id)).first()
    if not holding:
        raise HTTPException(status_code=404, detail="Holding non trovata")
    db.delete(holding)
    db.commit()
    logger.info(f"✅ Holding eliminata: {holding.symbol}")
    return {"message": "Holding eliminata"}

@app.get("/api/transactions", response_model=List[TransactionResponse])
async def get_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    transactions = db.query(Transaction).filter(Transaction.user_id == current_user.id).offset(skip).limit(limit).all()
    return transactions

@app.post("/api/transactions", response_model=TransactionResponse)
async def create_transaction(transaction_data: TransactionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    logger.info(f"Crea transazione: {transaction_data.type} {transaction_data.symbol}")
    transaction = Transaction(**transaction_data.dict(), user_id=current_user.id)
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    holding = db.query(Holding).filter(and_(Holding.symbol == transaction_data.symbol, Holding.user_id == current_user.id)).first()
    if holding:
        if transaction_data.type == TransactionType.BUY:
            total_cost = holding.quantity * holding.average_price + transaction_data.quantity * transaction_data.price
            holding.quantity += transaction_data.quantity
            holding.average_price = total_cost / holding.quantity if holding.quantity > 0 else 0
        else:
            holding.quantity -= transaction_data.quantity
            if holding.quantity <= 0:
                db.delete(holding)
    db.commit()
    logger.info(f"✅ Transazione registrata: {transaction.symbol}")
    return transaction

@app.get("/api/portfolio/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    holdings = db.query(Holding).filter(Holding.user_id == current_user.id).all()
    total_value = sum(h.current_price * h.quantity for h in holdings)
    total_cost = sum(h.average_price * h.quantity for h in holdings)
    total_gain = total_value - total_cost
    total_gain_percent = (total_gain / total_cost * 100) if total_cost > 0 else 0
    allocation = {}
    for h in holdings:
        value = h.current_price * h.quantity
        allocation[h.asset_class] = allocation.get(h.asset_class, 0) + value
    allocation_percent = {k: round(v / total_value * 100, 2) if total_value > 0 else 0 for k, v in allocation.items()}
    return PortfolioSummary(total_value=round(total_value, 2), total_cost=round(total_cost, 2), total_gain=round(total_gain, 2), total_gain_percent=round(total_gain_percent, 2), holdings_count=len(holdings), allocation=allocation_percent)

@app.get("/api/portfolio/history", response_model=List[PortfolioHistoryPoint])
async def get_portfolio_history(days: int = 30, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    holdings = db.query(Holding).filter(Holding.user_id == current_user.id).all()
    if not holdings:
        return []
    history = []
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    transactions = db.query(Transaction).filter(and_(Transaction.user_id == current_user.id, Transaction.date >= start_date, Transaction.date <= end_date)).all()
    for i in range(days + 1):
        date = start_date + timedelta(days=i)
        active_holdings = {}
        for t in transactions:
            if t.date <= date:
                symbol = t.symbol
                if symbol not in active_holdings:
                    active_holdings[symbol] = {"quantity": 0, "cost": 0}
                if t.type == TransactionType.BUY:
                    active_holdings[symbol]["quantity"] += t.quantity
                    active_holdings[symbol]["cost"] += t.quantity * t.price
                else:
                    active_holdings[symbol]["quantity"] -= t.quantity
        total_value = 0
        for symbol, data in active_holdings.items():
            if data["quantity"] > 0:
                prices = get_daily_prices(symbol, days=days)
                if prices and len(prices) > i:
                    price = prices[i]["close"]
                else:
                    quote = get_stock_quote(symbol)
                    price = quote["price"] if quote else 0
                total_value += price * data["quantity"]
        history.append(PortfolioHistoryPoint(date=date, value=round(total_value, 2)))
    return history

@app.get("/api/prices/{symbol}")
async def get_price(symbol: str):
    quote = get_stock_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail="Simbolo non trovato")
    return quote

@app.get("/api/search/{query}")
async def search_instruments(query: str):
    results = search_symbol(query)
    return {"results": results}

if __name__ == "__main__":
    import uvicorn
    logger.info("=" * 60)
    logger.info("🚀 AVVIO SERVER UVICORN...")
    logger.info("=" * 60)
    port = int(os.getenv("PORT", 8000))
    logger.info(f"Porta: {port}")
    logger.info(f"Environment: {ENVIRONMENT}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
