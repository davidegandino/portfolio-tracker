from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class AssetClass(str, enum.Enum):
    ETF = "ETF"
    AZIONE = "AZIONE"
    FONDO = "FONDO"

class TransactionType(str, enum.Enum):
    ACQUISTO = "acquisto"
    VENDITA = "vendita"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # 2FA TOTP
    totp_secret = Column(String(32), nullable=True)  # Secret per Google Authenticator
    totp_enabled = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazione con holdings
    holdings = relationship("Holding", back_populates="user", cascade="all, delete-orphan")

class Holding(Base):
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    ticker = Column(String(20), nullable=False)
    nome = Column(String(255), nullable=False)
    asset_class = Column(Enum(AssetClass), nullable=False)
    valuta = Column(String(3), default="EUR")
    quantita = Column(Float, default=0.0)
    prezzo_medio = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relazioni
    user = relationship("User", back_populates="holdings")
    transactions = relationship("Transaction", back_populates="holding", cascade="all, delete-orphan")
    price_history = relationship("PriceHistory", back_populates="holding", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    holding_id = Column(Integer, ForeignKey("holdings.id"), nullable=False)
    tipo = Column(Enum(TransactionType), nullable=False)  # Ora usa Enum, non stringa libera
    quantita = Column(Float, nullable=False)
    prezzo_unitario = Column(Float, nullable=False)
    valuta = Column(String(3), default="EUR")
    data_transazione = Column(DateTime, nullable=False)
    note = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relazioni
    holding = relationship("Holding", back_populates="transactions")

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    holding_id = Column(Integer, ForeignKey("holdings.id"), nullable=False)
    data = Column(DateTime, nullable=False)
    prezzo = Column(Float, nullable=False)
    valuta = Column(String(3), default="EUR")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relazioni
    holding = relationship("Holding", back_populates="price_history")
