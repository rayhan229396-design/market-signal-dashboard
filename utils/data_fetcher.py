import pandas as pd
import yfinance as yf
import ccxt
from datetime import datetime, timedelta

def fetch_crypto_data(symbol: str, timeframe: str = "5m", limit: int = 300) -> pd.DataFrame:
    """Try multiple sources for crypto data"""
    
    # Convert symbol format
    base = symbol.replace("/USDT", "").replace("USDT", "")
    
    # ---------- Method 1: yfinance (most reliable on Render) ----------
    try:
        yf_symbol = f"{base}-USD"
        interval_map = {"1m": "1m", "5m": "5m", "15m": "15m"}
        interval = interval_map.get(timeframe, "5m")
        
        period = "7d" if interval == "1m" else "60d"
        
        df = yf.download(yf_symbol, period=period, interval=interval, progress=False)
        
        if not df.empty:
            df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
            df.columns = ["Open", "High", "Low", "Close", "Volume"]
            df = df.tail(limit)
            return df
    except Exception as e:
        print(f"yfinance failed: {e}")

    # ---------- Method 2: ccxt with Bybit (backup) ----------
    try:
        exchange = ccxt.bybit({"enableRateLimit": True})
        ohlcv = exchange.fetch_ohlcv(f"{base}/USDT", timeframe=timeframe, limit=limit)
        
        df = pd.DataFrame(ohlcv, columns=["timestamp", "Open", "High", "Low", "Close", "Volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        return df.astype(float)
    except Exception as e:
        print(f"Bybit failed: {e}")

    return pd.DataFrame()


FOREX_YAHOO_MAP = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "USD/CHF": "USDCHF=X",
    "NZD/USD": "NZDUSD=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
}

def fetch_forex_data(symbol: str, timeframe: str = "5m", limit: int = 300) -> pd.DataFrame:
    try:
        yahoo_symbol = FOREX_YAHOO_MAP.get(symbol, symbol.replace("/", "") + "=X")
        
        interval_map = {"1m": "1m", "5m": "5m", "15m": "15m"}
        interval = interval_map.get(timeframe, "5m")
        
        period = "7d" if interval == "1m" else "60d"
            
        df = yf.download(yahoo_symbol, period=period, interval=interval, progress=False)
        
        if df.empty:
            return pd.DataFrame()
        
        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.columns = ["Open", "High", "Low", "Close", "Volume"]
        return df.tail(limit)
    except Exception as e:
        print(f"Error fetching forex: {e}")
        return pd.DataFrame()


def get_available_pairs():
    crypto = [
        "BTC/USDT", "ETH/USDT", "SOL/USDT", "BNB/USDT", "XRP/USDT",
        "ADA/USDT", "DOGE/USDT", "AVAX/USDT", "DOT/USDT", "LINK/USDT"
    ]
    forex = list(FOREX_YAHOO_MAP.keys())
    return {"Crypto": crypto, "Forex": forex}


def fetch_data(market_type: str, symbol: str, timeframe: str, limit: int = 300) -> pd.DataFrame:
    if market_type == "Crypto":
        return fetch_crypto_data(symbol, timeframe, limit)
    else:
        return fetch_forex_data(symbol, timeframe, limit)
