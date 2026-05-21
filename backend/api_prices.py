import os
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")
BASE_URL = "https://www.alphavantage.co/query"

def get_stock_quote(symbol: str, currency: str = "USD") -> Optional[Dict]:
    """
    Ottieni quotazione attuale di un'azione/ETF.
    Per titoli europei, usa simbolo con suffisso exchange (es. VWRL.L per Londra).
    """
    try:
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if "Global Quote" in data and data["Global Quote"]:
            quote = data["Global Quote"]
            return {
                "prezzo": float(quote.get("05. price", 0)),
                "variazione": float(quote.get("09. change", 0)),
                "variazione_percentuale": float(quote.get("10. change percent", 0)),
                "volume": float(quote.get("06. volume", 0)),
                "aggiornato": quote.get("07. latest trading day", "")
            }
        return None
    except Exception as e:
        print(f"Errore get_stock_quote: {e}")
        return None

def get_daily_prices(symbol: str, months: int = 6) -> Optional[List[Dict]]:
    """
    Ottieni storico prezzi giornalieri.
    Returns lista di dict con data, open, high, low, close, volume.
    """
    try:
        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "outputsize": "compact",  # 100 giorni (usa "full" per 20+ anni)
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if "Time Series (Daily)" in data and data["Time Series (Daily)"]:
            prices = []
            cutoff_date = datetime.now() - timedelta(days=months*30)
            
            for date_str, price_data in data["Time Series (Daily)"].items():
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                if date_obj >= cutoff_date:
                    prices.append({
                        "data": date_obj,
                        "apertura": float(price_data.get("1. open", 0)),
                        "massimo": float(price_data.get("2. high", 0)),
                        "minimo": float(price_data.get("3. low", 0)),
                        "chiusura": float(price_data.get("4. close", 0)),
                        "volume": float(price_data.get("5. volume", 0))
                    })
            
            # Ordina per data crescente
            prices.sort(key=lambda x: x["data"])
            return prices
        return None
    except Exception as e:
        print(f"Errore get_daily_prices: {e}")
        return None

def get_currency_exchange_rate(from_currency: str, to_currency: str = "EUR") -> Optional[float]:
    """
    Ottieni tasso di cambio tra due valute.
    """
    try:
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if "Realtime Currency Exchange Rate" in data:
            rate = data["Realtime Currency Exchange Rate"]
            return float(rate.get("5. Exchange Rate", 1.0))
        return 1.0
    except Exception as e:
        print(f"Errore get_currency_exchange_rate: {e}")
        return 1.0

def search_symbol(keywords: str) -> List[Dict]:
    """
    Cerca simboli di azioni/ETF per parola chiave.
    """
    try:
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords,
            "apikey": ALPHA_VANTAGE_API_KEY
        }
        response = requests.get(BASE_URL, params=params, timeout=10)
        data = response.json()
        
        if "bestMatches" in data:
            return [
                {
                    "simbolo": match.get("1. symbol", ""),
                    "nome": match.get("2. name", ""),
                    "tipo": match.get("3. type", ""),
                    "regione": match.get("4. region", ""),
                    "valuta": match.get("8. currency", "")
                }
                for match in data["bestMatches"][:10]
            ]
        return []
    except Exception as e:
        print(f"Errore search_symbol: {e}")
        return []

# Funzione helper per convertire prezzi in EUR
def convert_to_eur(price: float, currency: str) -> float:
    if currency == "EUR":
        return price
    rate = get_currency_exchange_rate(currency, "EUR")
    return price * rate if rate else price
