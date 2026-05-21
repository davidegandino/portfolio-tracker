from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class AssetClassEnum(str, Enum):
    azione = "azione"
    etf = "etf"
    fondo = "fondo"

# Holding schemas
class HoldingBase(BaseModel):
    ticker: str
    nome: str
    asset_class: AssetClassEnum
    valuta: str = "EUR"

class HoldingCreate(HoldingBase):
    pass

class HoldingUpdate(BaseModel):
    quantita: Optional[float] = None
    prezzo_medio: Optional[float] = None

class Holding(HoldingBase):
    id: int
    quantita: float = 0.0
    prezzo_medio: float = 0.0
    
    class Config:
        from_attributes = True

# Transaction schemas
class TransactionBase(BaseModel):
    tipo: str  # "acquisto" o "vendita"
    quantita: float
    prezzo_unitario: float
    valuta: str = "EUR"
    note: Optional[str] = None

class TransactionCreate(TransactionBase):
    holding_id: int
    data_transazione: Optional[datetime] = None

class Transaction(TransactionBase):
    id: int
    holding_id: int
    data_transazione: datetime
    
    class Config:
        from_attributes = True

# Price history schema
class PriceHistory(BaseModel):
    id: int
    holding_id: int
    data_prezzo: datetime
    prezzo_chiusura: float
    prezzo_apertura: Optional[float] = None
    prezzo_max: Optional[float] = None
    prezzo_min: Optional[float] = None
    volume: Optional[float] = None
    
    class Config:
        from_attributes = True

# Portfolio summary schema
class PortfolioSummary(BaseModel):
    valore_totale: float
    valore_investito: float
    guadagno_perdita: float
    percentuale_guadagno: float
    numero_holdings: int

# Holding con dati estesi
class HoldingDetail(Holding):
    prezzo_attuale: Optional[float] = None
    valore_attuale: Optional[float] = None
    guadagno_perdita: Optional[float] = None
    percentuale_guadagno: Optional[float] = None
