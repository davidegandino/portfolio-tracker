# Portfolio Tracker - Investment Portfolio Dashboard

Applicazione web per tracciare il portafoglio di investimenti con dati finanziari in tempo reale.

## Features

- ✅ **Tracking multi-asset:** Azioni, ETF, Fondi
- ✅ **Prezzi giornalieri** da Alpha Vantage API (gratis, 25 req/giorno)
- ✅ **Dashboard con grafici** (valore totale, valore investito, performance)
- ✅ **Filtri** per asset class e singolo titolo
- ✅ **Valuta base:** EUR
- ✅ **Inserimento manuale** transazioni (nessun broker richiesto)
- ✅ **Database:** SQLite (semplice, nessun setup richiesto)
- ✅ **Hosting gratuito:** Render (backend) + Cloudflare Pages (frontend)

## Stack Tecnologico

- **Backend:** Python 3.11+ con FastAPI
- **Frontend:** HTML + HTMX + Alpine.js + Chart.js
- **Database:** SQLite
- **API Prezzi:** Alpha Vantage (gratis)

## Struttura Progetto

```
portfolio_tracker/
├── backend/
│   ├── main.py              # FastAPI app + endpoints
│   ├── database.py          # Database setup
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── api_prices.py        # Alpha Vantage integration
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Dashboard principale
│   ├── static/
│   │   ├── css/style.css
│   │   └── js/charts.js
├── demo_data.py             # Script per dati demo
└── README.md
```

## Quick Start (Locale)

### 1. Installa dipendenze

```bash
cd portfolio_tracker/backend
pip install -r requirements.txt
```

### 2. Configura API Key

Crea file `.env` in `backend/`:

```
ALPHA_VANTAGE_API_KEY=tua_api_key
DATABASE_URL=sqlite:///./portfolio.db
```

Ottieni API key gratis: https://www.alphavantage.co/support/#api-key

### 3. Inizializza database

```bash
python demo_data.py
```

### 4. Avvia server

```bash
python main.py
```

Apri http://localhost:8000

## Deploy Gratuito

### Backend su Render

1. Crea account su https://render.com
2. Nuovo "Web Service"
3. Connetti repository GitHub
4. Variabili d'ambiente: `ALPHA_VANTAGE_API_KEY`, `DATABASE_URL`

### Frontend su Cloudflare Pages

1. Crea account su https://pages.cloudflare.com
2. Connetti repository
3. Publish directory: `frontend/`

## License

MIT License
