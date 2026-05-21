import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Leggi variabili d'ambiente
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./portfolio.db")

# Crea engine database
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base per modelli
Base = declarative_base()

# Funzione per ottenere sessione DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
