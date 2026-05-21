# Portfolio Tracker - Guida Rapida

## 🚀 Avvio Rapido (5 minuti)

### 1. Installa dipendenze

```bash
cd portfolio_tracker_v2/backend
pip install -r requirements.txt
```

### 2. Configura API Key (opzionale per demo)

Copia il file `.env.example`:

```bash
cp .env.example .env
```

Se vuoi prezzi reali, ottieni una API key gratis da [Alpha Vantage](https://www.alphavantage.co/support/#api-key) e inseriscila in `.env`.

Per la demo, puoi usare `"demo"` (dati limitati ma funzionanti).

### 3. Inizializza database con dati demo

```bash
python demo_data.py
```

Questo crea:
- ✅ 2 ETF (VWRP, VUAA)
- ✅ 2 Azioni (AAPL, MSFT)
- ✅ 1 Fondo europeo
- ✅ Transazioni demo storiche

### 4. Avvia il server

```bash
python main.py
```

Il server parte su **http://localhost:8000**

### 5. Apri il browser

Vai su http://localhost:8000 e vedi la tua dashboard!

---

## 📊 Cosa Puoi Fare

### Dashboard Principale
- **Riepilogo portafoglio:** Valore totale, investito, guadagno/perdita
- **Grafico valore nel tempo:** Ultimi 90 giorni
- **Grafico allocazione:** Suddivisione per asset class (Azioni, ETF, Fondi)

### Tabella Holdings
- **Filtra per asset class:** Azioni / ETF / Fondi
- **Filtra per singolo titolo:** dropdown con tutti i tuoi strumenti
- **Vedi performance:** Prezzo medio vs attuale, guadagno € e %

### Aggiungi Strumenti
1. Compila il form "Aggiungi Nuovo Strumento"
2. Inserisci: Ticker, Nome, Asset Class, Quantità, Prezzo Medio
3. Clicca "Aggiungi Strumento"

### Registra Transazioni
1. Seleziona lo strumento dal dropdown
2. Scegli: Acquisto o Vendita
3. Inserisci: Quantità, Prezzo Unitario, Data
4. Clicca "Registra"

Il sistema aggiorna automaticamente:
- ✅ Quantità posseduta
- ✅ Prezzo medio di carico
- ✅ Valore totale portafoglio
- ✅ Grafici

---

## 🛠️ Comandi Utili

### Reset database (cancella tutto e ricrea demo)

```bash
rm portfolio.db
python demo_data.py
```

### Vedi log API calls

Il backend stampa a console ogni chiamata API a Alpha Vantage.

### API Documentation

Con il server attivo, vai su http://localhost:8000/docs per vedere tutte le API endpoint (Swagger UI).

---

## 🌐 Deploy Online (Gratis)

### Backend su Render

1. Crea repo GitHub e pusha il codice
2. Vai su https://render.com
3. Crea "New Web Service"
4. Connetti il repo
5. Imposta:
   - **Root Directory:** `portfolio_tracker_v2/backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
6. Aggiungi variabili d'ambiente:
   - `ALPHA_VANTAGE_API_KEY`
   - `DATABASE_URL` (Render fornisce PostgreSQL gratis)

### Frontend su Cloudflare Pages

1. Vai su https://pages.cloudflare.com
2. "Create a project" → "Connect to Git"
3. Seleziona repo
4. **Build command:** `echo "No build needed"`
5. **Publish directory:** `portfolio_tracker_v2/frontend`
6. Deploy!

### Aggiorna URL API

Nel frontend (`index.html`), cambia le chiamate API da `/api/...` a `https://tuo-backend.onrender.com/api/...`

Oppure usa variabili d'ambiente in Cloudflare Pages.

---

## 📝 Note

- **Limiti API Alpha Vantage:** 25 richieste/giorno (gratis). Per uso intensivo, considera piano paid o caching.
- **Valuta:** Tutti i prezzi sono convertiti in EUR automaticamente.
- **Database:** SQLite per sviluppo, PostgreSQL per produzione (Render lo fornisce gratis).

---

## 🆘 Troubleshooting

**Errore "Module not found":**
```bash
pip install -r requirements.txt
```

**Errore database:**
```bash
rm portfolio.db
python demo_data.py
```

**Prezzi non aggiornati:**
- Controlla che `ALPHA_VANTAGE_API_KEY` sia impostata in `.env`
- Verifica di non aver superato i 25 calls/giorno

**Porta 8000 già in uso:**
```bash
# Cambia porta in main.py
uvicorn.run(app, host="0.0.0.0", port=8001)
```

---

**Buon tracking! 📈**
