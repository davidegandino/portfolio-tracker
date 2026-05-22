from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

from models import Base, User
from auth import get_password_hash, generate_totp_secret

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./portfolio.db")

# Setup engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency per FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Inizializza database con tabelle e user admin"""
    print("📦 Inizializzazione database...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Crea user admin se non esiste
        admin_email = os.getenv("ADMIN_EMAIL", "admin@portfolio.com")
        admin_exists = db.query(User).filter(User.email == admin_email).first()
        
        if not admin_exists:
            admin_password = os.getenv("ADMIN_PASSWORD", "Admin123!")
            totp_secret = generate_totp_secret()
            
            admin_user = User(
                email=admin_email,
                hashed_password=get_password_hash(admin_password),
                is_active=True,
                is_admin=True,
                totp_secret=totp_secret,
                totp_enabled=False  # L'utente dovrà abilitarlo al primo login
            )
            
            db.add(admin_user)
            db.commit()
            
            print(f"✅ User admin creato: {admin_email}")
            print(f"🔑 TOTP Secret (per setup): {totp_secret}")
            print(f"⚠️  Password admin: {admin_password} (cambiala in produzione!)")
        else:
            print(f"✅ User admin già esistente: {admin_email}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
