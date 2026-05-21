from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from database import Base

class AssetClass(str, enum.Enum):
    AZIONE = "azione"
    ETF = "etf"
    FONDO = "fondo"

class Holding(Base):
    __tablename__ = "holdings"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(20), unique=True, index=True, nullable=False)
    nome = Column(String(200), nullable=False)
    asset_class = Column(Enum(AssetClass), nullable=False)
    valuta = Column(String(3), default="EUR")
    quantita = Column(Float, default=0.0)
    prezzo_medio = Column(Float, default=0.0)
    
    # Relazioni
    transazioni = relationship("Transaction", back_populates="holding", cascade="all, delete-orphan")
    prezzi_storici = relationship("PriceHistory", back_populates="holding", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    holding_id = Column(Integer, ForeignKey("holdings.id"), nullable=False)
    tipo = Column(String(10), nullable=False)  # "acquisto" o "vendita"
    quantita = Column(Float, nullable=False)
    prezzo_unitario = Column(Float, nullable=False)
    valuta = Column(String(3), default="EUR")
    data_transazione = Column(DateTime, default=datetime.utcnow)
    note = Column(String(500), nullable=True)
    
    # Relazione
    holding = relationship("Holding", back_populates="transazioni")

class PriceHistory(Base):
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    holding_id = Column(Integer, ForeignKey("holdings.id"), nullable=False)
    data_prezzo = Column(DateTime, nullable=False)
    prezzo_apertura = Column(Float)
    prezzo_chiusura = Column(Float)
    prezzo_max = Column(Float)
    prezzo_min = Column(Float)
    volume = Column(Float)
    
    # Relazione
    holding = relationship("Holding", back_populates="prezzi_storici")
    
    # Unique constraint per evitare duplicati
    __table_args__ = (
        # Constraint gestita a livello applicativo per SQLite
    )
