from pydantic import BaseModel, Field, validator, EmailStr
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

# ============================================
# Enums
# ============================================
class TransactionType(str, Enum):
    BUY = "buy"
    SELL = "sell"

class AssetClass(str, Enum):
    STOCKS = "stocks"
    BONDS = "bonds"
    ETF = "etf"
    CRYPTO = "crypto"
    CASH = "cash"
    OTHER = "other"

# ============================================
# User Schemas
# ============================================
class UserBase(BaseModel):
    email: str  # Uso str invece di EmailStr
    
    @validator("email")
    def validate_email(cls, v):
        if "@" not in v or "." not in v:
            raise ValueError("Email non valida")
        return v.lower().strip()

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    
    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password deve avere almeno 8 caratteri")
        if not any(c.isupper() for c in v):
            raise ValueError("Password deve contenere almeno una maiuscola")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password deve contenere almeno un numero")
        return v

class UserLogin(BaseModel):
    username: str  # Uso str invece di EmailStr
    password: str
    totp: Optional[str] = Field(None, min_length=6, max_length=6)
    
    @validator("username")
    def validate_username(cls, v):
        if "@" not in v:
            raise ValueError("Username deve essere una email")
        return v.lower().strip()

class UserResponse(UserBase):
    id: int
    email: str
    totp_enabled: bool = False
    
    class Config:
        from_attributes = True

# ============================================
# Token Schema
# ============================================
class Token(BaseModel):
    access_token: str
    token_type: str
    totp_enabled: bool = False

# ============================================
# Holding Schemas
# ============================================
class HoldingBase(BaseModel):
    symbol: str
    name: str
    quantity: float = Field(..., gt=0)
    average_price: float = Field(..., gt=0)
    asset_class: AssetClass = AssetClass.OTHER
    currency: str = "USD"

class HoldingCreate(HoldingBase):
    pass

class HoldingUpdate(BaseModel):
    symbol: Optional[str] = None
    name: Optional[str] = None
    quantity: Optional[float] = Field(None, gt=0)
    average_price: Optional[float] = Field(None, gt=0)
    asset_class: Optional[AssetClass] = None
    currency: Optional[str] = None

class HoldingResponse(HoldingBase):
    id: int
    user_id: int
    current_price: float = 0.0
    current_value: float = 0.0
    gain_loss: float = 0.0
    gain_loss_percent: float = 0.0
    
    class Config:
        from_attributes = True

# ============================================
# Transaction Schemas
# ============================================
class TransactionBase(BaseModel):
    symbol: str
    type: TransactionType
    quantity: float = Field(..., gt=0)
    price: float = Field(..., gt=0)
    date: datetime = Field(default_factory=datetime.now)
    notes: Optional[str] = None

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True

# ============================================
# Portfolio Schemas
# ============================================
class PortfolioSummary(BaseModel):
    total_value: float
    total_cost: float
    total_gain: float
    total_gain_percent: float
    holdings_count: int
    allocation: Dict[str, float]

class PortfolioHistoryPoint(BaseModel):
    date: datetime
    value: float
