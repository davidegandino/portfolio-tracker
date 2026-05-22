from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pyotp import TOTP
import qrcode
import io
import base64
import os

# ============ CONFIGURAZIONE ============
SECRET_KEY = os.getenv("JWT_SECRET", "change-this-secret-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 ore

# Per TOTP: usa secret diverso per ogni utente
TOTP_ISSUER = "Portfolio Tracker"

# ============ PASSWORD HASHING ============
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se una password corrisponde all'hash"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Genera hash bcrypt di una password"""
    return pwd_context.hash(password)

# ============ JWT TOKEN ============
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Crea JWT token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decodifica JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

# ============ TOTP (Google Authenticator) ============
def generate_totp_secret() -> str:
    """Genera secret TOTP casuale"""
    import secrets
    return secrets.token_hex(16)

def get_totp_uri(email: str, secret: str) -> str:
    """Crea URI per Google Authenticator"""
    from urllib.parse import quote
    
    issuer = quote(TOTP_ISSUER)
    label = f"{issuer}:{email}"
    return f"otpauth://totp/{label}?secret={secret}&issuer={issuer}"

def generate_qr_code(uri: str) -> str:
    """Genera QR code come base64 PNG"""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    img_base64 = base64.b64encode(buffer.read()).decode()
    return f"data:image/png;base64,{img_base64}"

def verify_totp_code(secret: str, code: str) -> bool:
    """Verifica codice TOTP"""
    try:
        totp = TOTP(secret)
        return totp.verify(code, valid_window=1)  # Accetta codice corrente e precedente
    except Exception:
        return False

# ============ SECURITY UTILITIES ============
def validate_email(email: str) -> bool:
    """Valida formato email"""
    import re
    pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    return re.match(pattern, email) is not None

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Valida forza password.
    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "La password deve avere almeno 8 caratteri"
    
    if not any(c.isupper() for c in password):
        return False, "La password deve contenere almeno una maiuscola"
    
    if not any(c.isdigit() for c in password):
        return False, "La password deve contenere almeno un numero"
    
    if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
        return False, "La password deve contenere almeno un carattere speciale"
    
    return True, ""
