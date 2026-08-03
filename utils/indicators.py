import pandas as pd
import numpy as np
import pandas_ta as ta

def add_all_indicators(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 50:
        return df
    
    df = df.copy()
    
    df["EMA_9"] = ta.ema(df["Close"], length=9)
    df["EMA_21"] = ta.ema(df["Close"], length=21)
    df["SMA_50"] = ta.sma(df["Close"], length=50)
    
    df["RSI"] = ta.rsi(df["Close"], length=14)
    
    bb = ta.bbands(df["Close"], length=20, std=2)
    if bb is not None and not bb.empty:
        df["BB_Upper"] = bb.iloc[:, 0]
        df["BB_Middle"] = bb.iloc[:, 1]
        df["BB_Lower"] = bb.iloc[:, 2]
        df["BB_Width"] = (df["BB_Upper"] - df["BB_Lower"]) / df["BB_Middle"]
    
    macd = ta.macd(df["Close"], fast=12, slow=26, signal=9)
    if macd is not None and not macd.empty:
        df["MACD"] = macd.iloc[:, 0]
        df["MACD_Hist"] = macd.iloc[:, 1]
        df["MACD_Signal"] = macd.iloc[:, 2]
    
    stoch = ta.stoch(df["High"], df["Low"], df["Close"], k=14, d=3, smooth_k=3)
    if stoch is not None and not stoch.empty:
        df["STOCH_K"] = stoch.iloc[:, 0]
        df["STOCH_D"] = stoch.iloc[:, 1]
    
    df["ATR"] = ta.atr(df["High"], df["Low"], df["Close"], length=14)
    
    df = add_support_resistance(df)
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
