import requests
import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List

logger = logging.getLogger(__name__)

# API Key da variabile d'ambiente (NON hardcoded)
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

if not ALPHA_VANTAGE_API_KEY:
    logger.warning("⚠️  ALPHA_VANTAGE_API_KEY non impostata - uso demo key (limitata)")
    ALPHA_VANTAGE_API_KEY = "demo"

BASE_URL = "https://www.alphavantage.co/query"

# Cache semplice in memoria (per evitare troppe chiamate API)
_price_cache: Dict[str, Dict] = {}
_cache_expiry: Dict[str, datetime] = {}
CACHE_TTL_MINUTES = 30  # Cache valida per 30 minuti

def get_stock_quote(symbol: str) -> Optional[Dict]:
    """
    Ottiene prezzo corrente di un titolo.
    Supporta sia ticker US (AAPL) che ETF europei (VWRP.MI).
    """
    # Check cache
    cache_key = f"quote_{symbol}"
    if cache_key in _price_cache:
        expiry = _cache_expiry.get(cache_key)
        if expiry and datetime.now() < expiry:
            logger.debug(f"Cache hit per {symbol}")
            return _price_cache[cache_key]
    
    try:
        # Mappa ticker europei a formato Alpha Vantage
        if symbol.endswith(".MI"):
            # ETF italiano - rimuovi .MI per Alpha Vantage
            symbol_clean = symbol.replace(".MI", "")
        else:
            symbol_clean = symbol
        
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol_clean,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        logger.info(f"Richiesta prezzo per {symbol}...")
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "Global Quote" not in data:
            logger.warning(f"Nessun dato per {symbol}: {data}")
            return None
        
        quote = data["Global Quote"]
        price = float(quote.get("05. price", 0))
        
        result = {
            "symbol": symbol,
            "price": price,
            "currency": "USD",  # Alpha Vantage restituisce USD
            "timestamp": datetime.now()
        }
        
        # Salva in cache
        _price_cache[cache_key] = result
        _cache_expiry[cache_key] = datetime.now() + timedelta(minutes=CACHE_TTL_MINUTES)
        
        logger.info(f"Prezzo {symbol}: ${price}")
        return result
        
    except requests.RequestException as e:
        logger.error(f"Errore API per {symbol}: {e}")
        return None
    except (KeyError, ValueError) as e:
        logger.error(f"Errore parsing risposta per {symbol}: {e}")
        return None

def get_daily_prices(symbol: str, days: int = 90) -> List[Dict]:
    """
    Ottiene storico prezzi giornalieri.
    """
    cache_key = f"daily_{symbol}_{days}"
    if cache_key in _price_cache:
        expiry = _cache_expiry.get(cache_key)
        if expiry and datetime.now() < expiry:
            return _price_cache[cache_key]
    
    try:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "compact",  # ultimi 100 giorni
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        logger.info(f"Richiesta storico per {symbol} ({days} giorni)...")
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "Time Series (Daily)" not in data:
            logger.warning(f"Nessuno storico per {symbol}")
            return []
        
        time_series = data["Time Series (Daily)"]
        prices = []
        
        for date_str, prices_data in list(time_series.items())[:days]:
            prices.append({
                "date": datetime.strptime(date_str, "%Y-%m-%d"),
                "open": float(prices_data.get("1. open", 0)),
                "high": float(prices_data.get("2. high", 0)),
                "low": float(prices_data.get("3. low", 0)),
                "close": float(prices_data.get("4. close", 0)),
                "volume": int(prices_data.get("5. volume", 0))
            })
        
        prices.reverse()  # Ordina per data crescente
        
        # Salva in cache
        _price_cache[cache_key] = prices
        _cache_expiry[cache_key] = datetime.now() + timedelta(minutes=CACHE_TTL_MINUTES)
        
        logger.info(f"Ottenuti {len(prices)} prezzi per {symbol}")
        return prices
        
    except requests.RequestException as e:
        logger.error(f"Errore API storico per {symbol}: {e}")
        return []
    except (KeyError, ValueError) as e:
        logger.error(f"Errore parsing storico per {symbol}: {e}")
        return []

def convert_to_eur(amount: float, currency: str = "USD") -> float:
    """
    Converte importo in EUR.
    Usa tasso di cambio fisso per semplicità (in produzione usare API cambio).
    """
    if currency == "EUR":
        return amount
    
    # Tasso USD -> EUR approssimativo (in produzione usare API ECB)
    USD_TO_EUR = 0.92
    return amount * USD_TO_EUR

def search_symbol(query: str) -> List[Dict]:
    """
    Cerca simboli strumenti per keyword.
    """
    if not query or len(query) < 2:
        return []
    
    try:
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": query,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        
        logger.info(f"Ricerca simboli per '{query}'...")
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if "bestMatches" not in data:
            return []
        
        matches = data["bestMatches"][:10]  # Top 10 risultati
        
        results = []
        for match in matches:
            results.append({
                "symbol": match.get("1. symbol", ""),
                "name": match.get("2. name", ""),
                "type": match.get("3. type", ""),
                "region": match.get("4. region", ""),
                "currency": match.get("8. currency", "")
            })
        
        logger.info(f"Trovati {len(results)} simboli per '{query}'")
        return results
        
    except requests.RequestException as e:
        logger.error(f"Errore ricerca simboli: {e}")
        return []
    except (KeyError, ValueError) as e:
        logger.error(f"Errore parsing ricerca: {e}")
        return []

# Test diretto
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Test Alpha Vantage API...")
    
    # Test quotazione
    quote = get_stock_quote("AAPL")
    if quote:
        print(f"✅ AAPL: ${quote['price']}")
    else:
        print("❌ AAPL: Nessun dato")
    
    # Test storico
    prices = get_daily_prices("AAPL", days=30)
    if prices:
        print(f"✅ Storico AAPL: {len(prices)} giorni")
        print(f"   Ultimo prezzo: ${prices[-1]['close']}")
    else:
        print("❌ Storico AAPL: Nessun dato")
    
    # Test ricerca
    results = search_symbol("Vanguard")
    if results:
        print(f"✅ Ricerca 'Vanguard': {len(results)} risultati")
        for r in results[:3]:
            print(f"   - {r['symbol']}: {r['name']}")
    else:
        print("❌ Ricerca 'Vanguard': Nessun risultato")
