from pydantic import BaseModel, EmailStr, Field, Enum
from typing import Optional, List
from datetime import datetime
from enum import Enum as PyEnum

class AssetClass(str, PyEnum):
    ETF = "ETF"
    AZIONE = "AZIONE"
    FONDO = "FONDO"

class TransactionType(str, PyEnum):
    ACQUISTO = "acquisto"
    VENDITA = "vendita"

# ============ AUTH SCHEMAS ============

class UserBase(BaseModel):
    email: EmailStr
    is_active: bool = True

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password minima 8 caratteri")

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    totp_code: Optional[str] = Field(None, min_length=6, max_length=6, description="Codice TOTP 6 cifre")

class UserResponse(UserBase):
    id: int
    is_admin: bool
    totp_enabled: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    requires_totp_setup: bool = False

class TotpSetupResponse(BaseModel):
    secret: str
    qr_code_url: str
    manual_entry_key: str

class TotpVerifyRequest(BaseModel):
    code: str = Field(..., min_length=6, max_length=6)

# ============ HOLDING SCHEMAS ============

class HoldingBase(BaseModel):
    ticker: str = Field(..., max_length=20)
    nome: str = Field(..., max_length=255)
    asset_class: AssetClass
    valuta: str = "EUR"

class HoldingCreate(HoldingBase):
    pass

class HoldingUpdate(BaseModel):
    ticker: Optional[str] = None
    nome: Optional[str] = None
    asset_class: Optional[AssetClass] = None
    valuta: Optional[str] = None
    quantita: Optional[float] = None
    prezzo_medio: Optional[float] = None

class Holding(HoldingBase):
    id: int
    user_id: int
    quantita: float
    prezzo_medio: float
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class HoldingDetail(Holding):
    prezzo_attuale: Optional[float] = None
    valore_attuale: Optional[float] = None
    guadagno_perdita: Optional[float] = None
    percentuale_guadagno: Optional[float] = None

# ============ TRANSACTION SCHEMAS ============

class TransactionBase(BaseModel):
    tipo: TransactionType
    quantita: float = Field(..., gt=0, description="Quantità deve essere positiva")
    prezzo_unitario: float = Field(..., gt=0, description="Prezzo deve essere positivo")
    valuta: str = "EUR"
    note: Optional[str] = None

class TransactionCreate(TransactionBase):
    holding_id: int
    data_transazione: datetime

class TransactionUpdate(BaseModel):
    tipo: Optional[TransactionType] = None
    quantita: Optional[float] = None
    prezzo_unitario: Optional[float] = None
    note: Optional[str] = None

class Transaction(TransactionBase):
    id: int
    holding_id: int
    data_transazione: datetime
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============ PORTFOLIO SCHEMAS ============

class PortfolioSummary(BaseModel):
    valore_totale: float
    valore_investito: float
    guadagno_perdita: float
    percentuale_guadagno: float
    numero_holdings: int

class PortfolioHistoryItem(BaseModel):
    data: str
    valore_totale: float
    valore_investito: float
