# 📊 Portfolio Tracker

Tracker di portafoglio investimenti con autenticazione sicura e Google Authenticator 2FA.

## 🔐 Sicurezza

- **Autenticazione JWT** con token a 24 ore
- **Google Authenticator (TOTP)** per 2FA opzionale
- **Password hashate** con bcrypt
- **API key** da variabili d'ambiente (non hardcoded)
- **CORS configurato** per domini specifici
- **Input validation** su tutti gli endpoint

## 🚀 Features

- ✅ Tracking holdings (ETF, Azioni, Fondi)
- ✅ Storico transazioni (acquisti/vendite)
- ✅ Grafici andamento portafoglio (7/30/90 giorni)
- ✅ Allocazione per asset class
- ✅ Prezzi in tempo reale (Alpha Vantage API)
- ✅ Multi-utente con auth sicura

## 📦 Setup Locale

### 1. Clona la repo
```bash
git clone https://github.com/davidegandino/portfolio-tracker.git
cd portfolio-tracker/backend
```

### 2. Installa dipendenze
```bash
pip install -r requirements.txt
```

### 3. Configura variabili ambiente
```bash
cp .env.example .env
# Modifica .env con le tue chiavi
```

### 4. Ottieni Alpha Vantage API Key
1. Vai su https://www.alphavantage.co/support/#api-key
2. Compila il form (gratis, 25 req/giorno)
3. Copia la key nel file `.env`

### 5. Avvia il server
```bash
python main.py
# oppure
uvicorn main:app --reload
```

Il server sarà su http://localhost:8000

## 🔑 Primo Accesso

### User Admin (creato automaticamente)
- **Email:** `admin@portfolio.com` (o quella in `.env`)
- **Password:** `CambiaQuestaPassword123!` (o quella in `.env`)

**⚠️ IMPORTANTE:** Cambia la password admin in produzione!

### Setup Google Authenticator
Al primo login:
1. Scansiona il QR code con Google Authenticator (iOS/Android)
2. Inserisci il codice a 6 cifre
3. Clicca "Verifica e Attiva"

Ogni login successivo richiederà password + codice TOTP.

## 🌐 Deploy su Render

### 1. Configura Variabili Ambiente su Render
Nel dashboard di Render, aggiungi:

```
ALPHA_VANTAGE_API_KEY=tua_api_key
JWT_SECRET=secret_generato_a_case
ENVIRONMENT=production
CORS_ORIGINS=https://portfolio-tracker-xxx.onrender.com
ADMIN_EMAIL=admin@portfolio.com
ADMIN_PASSWORD=PasswordSicura123!
```

### 2. Genera JWT Secret
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Deploy Automatico
Render farà auto-deploy ad ogni push su GitHub.

## 📁 Struttura Progetto

```
portfolio-tracker/
├── backend/
│   ├── main.py              # API FastAPI + auth
│   ├── models.py            # SQLAlchemy models (User, Holding, Transaction)
│   ├── schemas.py           # Pydantic schemas
│   ├── database.py          # DB setup + init admin user
│   ├── auth.py              # JWT, password hashing, TOTP
│   ├── api_prices.py        # Alpha Vantage API
│   ├── requirements.txt     # Dipendenze Python
│   └── .env.example         # Template variabili ambiente
├── frontend/
│   ├── index.html           # Login/Registrazione + 2FA setup
│   └── dashboard.html       # Dashboard protetta
└── .gitignore
```

## 🔒 API Endpoints

### Pubblici
- `GET /` - Pagina login
- `GET /api/health` - Health check
- `POST /api/auth/register` - Registrazione utente
- `POST /api/auth/login` - Login (password + TOTP opzionale)

### Protetti (richiedono JWT)
- `GET /api/auth/me` - Info utente corrente
- `POST /api/auth/totp/setup` - Setup TOTP
- `POST /api/auth/totp/verify` - Verifica e attiva TOTP
- `POST /api/auth/totp/disable` - Disabilita TOTP
- `GET /api/holdings` - Lista holdings
- `POST /api/holdings` - Crea holding
- `PUT /api/holdings/{id}` - Aggiorna holding
- `DELETE /api/holdings/{id}` - Elimina holding
- `GET /api/transactions` - Lista transazioni
- `POST /api/transactions` - Registra transazione
- `GET /api/portfolio/summary` - Riepilogo portafoglio
- `GET /api/portfolio/history` - Storico portafoglio

## 🛡️ Sicurezza Implementata

| Issue | Fix Implementato |
|-------|------------------|
| API key hardcoded | Variabili d'ambiente (.env) |
| CORS permissivo | Domini specifici configurabili |
| Password in chiaro | Hash bcrypt con salt |
| Nessun rate limiting | JWT expiration 24h |
| Input non validato | Pydantic schemas con validation |
| Transazione come stringa | Enum TransactionType |
| Logging assente | Logging module con timestamp |
| Query N+1 | Single query con join |
| Loop O(n²) | Ottimizzato con pre-fetch |

## 📝 License

MIT License

## 👨‍💻 Autore

Davide Gandino

---

**Problemi?** Apri una issue su GitHub 🐛
