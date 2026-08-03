import pandas as pd
import numpy as np
import ta

def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 50:
        return df
    
    df = df.copy()
    
    # Moving Averages
    df["EMA_9"] = ta.trend.ema_indicator(df["Close"], window=9)
    df["EMA_21"] = ta.trend.ema_indicator(df["Close"], window=21)
    df["SMA_50"] = ta.trend.sma_indicator(df["Close"], window=50)
    
    # RSI
    df["RSI"] = ta.momentum.rsi(df["Close"], window=14)
    
    # Bollinger Bands
    bb = ta.volatility.BollingerBands(df["Close"], window=20, window_dev=2)
    df["BB_Upper"] = bb.bollinger_hband()
    df["BB_Middle"] = bb.bollinger_mavg()
    df["BB_Lower"] = bb.bollinger_lband()
    df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / df["BB_Middle"]
    
    # MACD
    macd = ta.trend.MACD(df["Close"], window_slow=26, window_fast=12, window_sign=9)
    df["MACD"] = macd.macd()
    df["MACD_Signal"] = macd.macd_signal()
    df["MACD_Hist"] = macd.macd_diff()
    
    # Stochastic
    stoch = ta.momentum.StochasticOscillator(df["High"], df["Low"], df["Close"], window=14, smooth_window=3)
    df["STOCH_K"] = stoch.stoch()
    df["STOCH_D"] = stoch.stoch_signal()
    
    # ATR
    df["ATR"] = ta.volatility.average_true_range(df["High"], df["Low"], df["Close"], window=14)
    
    # Support & Resistance
    df = add_support_resistance(df)
    
    # Candlestick Patterns
    df = add_candlestick_patterns(df)
    
    return df


def add_support_resistance(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    df = df.copy()
    df["Resistance"] = df["High"].rolling(window=window, center=False).max()
    df["Support"] = df["Low"].rolling(window=window, center=False).min()
    df["Dist_to_Res"] = (df["Resistance"] - df["Close"]) / df["Close"] * 100
    df["Dist_to_Sup"] = (df["Close"] - df["Support"]) / df["Close"] * 100
    return df


def add_candlestick_patterns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    
    df["Body"] = df["Close"] - df["Open"]
    df["Body_Abs"] = abs(df["Body"])
    df["Upper_Wick"] = df["High"] - df[["Open", "Close"]].max(axis=1)
    df["Lower_Wick"] = df[["Open", "Close"]].min(axis=1) - df["Low"]
    df["Range"] = df["High"] - df["Low"]
    
    df["Body_Pct"] = np.where(df["Range"] > 0, df["Body_Abs"] / df["Range"], 0)
    
    df["Bullish_Engulfing"] = (
        (df["Body"].shift(1) < 0) &
        (df["Body"] > 0) &
        (df["Open"] < df["Close"].shift(1)) &
        (df["Close"] > df["Open"].shift(1))
    )
    
    df["Bearish_Engulfing"] = (
        (df["Body"].shift(1) > 0) &
        (df["Body"] < 0) &
        (df["Open"] > df["Close"].shift(1)) &
        (df["Close"] < df["Open"].shift(1))
    )
    
    df["Bullish_Pinbar"] = (
        (df["Lower_Wick"] > 2 * df["Body_Abs"]) &
        (df["Upper_Wick"] < df["Body_Abs"]) &
        (df["Body_Pct"] < 0.3)
    )
    
    df["Bearish_Pinbar"] = (
        (df["Upper_Wick"] > 2 * df["Body_Abs"]) &
        (df["Lower_Wick"] < df["Body_Abs"]) &
        (df["Body_Pct"] < 0.3)
    )
    
    df["Doji"] = df["Body_Pct"] < 0.1
    
    return df
