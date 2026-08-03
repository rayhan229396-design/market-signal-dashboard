import pandas as pd
import numpy as np

def generate_signal(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 30:
        return {
            "signal": "Neutral",
            "score": 50,
            "confidence": "Low",
            "reasons": ["Insufficient data"],
            "color": "gray",
            "key_levels": {}
        }
    
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    score = 50
    reasons = []
    
    # RSI
    rsi = latest.get("RSI", 50)
    if rsi < 30:
        score += 12
        reasons.append(f"RSI oversold ({rsi:.1f})")
    elif rsi < 40:
        score += 6
        reasons.append(f"RSI approaching oversold ({rsi:.1f})")
    elif rsi > 70:
        score -= 12
        reasons.append(f"RSI overbought ({rsi:.1f})")
    elif rsi > 60:
        score -= 6
        reasons.append(f"RSI approaching overbought ({rsi:.1f})")
    
    # Moving Averages
    ema9 = latest.get("EMA_9")
    ema21 = latest.get("EMA_21")
    sma50 = latest.get("SMA_50")
    close = latest["Close"]
    
    if ema9 and ema21:
        if ema9 > ema21 and prev.get("EMA_9", 0) <= prev.get("EMA_21", 0):
            score += 10
            reasons.append("EMA 9 crossed above EMA 21 (bullish)")
        elif ema9 < ema21 and prev.get("EMA_9", 0) >= prev.get("EMA_21", 0):
            score -= 10
            reasons.append("EMA 9 crossed below EMA 21 (bearish)")
        elif ema9 > ema21:
            score += 5
            reasons.append("EMA 9 above EMA 21 (uptrend)")
        else:
            score -= 5
            reasons.append("EMA 9 below EMA 21 (downtrend)")
    
    if sma50 and close > sma50:
        score += 4
        reasons.append("Price above SMA 50")
    elif sma50 and close < sma50:
        score -= 4
        reasons.append("Price below SMA 50")
    
    # Bollinger Bands
    bb_upper = latest.get("BB_Upper")
    bb_lower = latest.get("BB_Lower")
    
    if bb_lower and close <= bb_lower * 1.002:
        score += 8
        reasons.append("Price at/near lower Bollinger Band")
    elif bb_upper and close >= bb_upper * 0.998:
        score -= 8
        reasons.append("Price at/near upper Bollinger Band")
    
    # MACD
    macd = latest.get("MACD")
    macd_signal = latest.get("MACD_Signal")
    macd_hist = latest.get("MACD_Hist")
    
    if macd is not None and macd_signal is not None:
        if macd > macd_signal and prev.get("MACD", 0) <= prev.get("MACD_Signal", 0):
            score += 8
            reasons.append("MACD bullish crossover")
        elif macd < macd_signal and prev.get("MACD", 0) >= prev.get("MACD_Signal", 0):
            score -= 8
            reasons.append("MACD bearish crossover")
        elif macd_hist and macd_hist > 0:
            score += 3
            reasons.append("MACD histogram positive")
        elif macd_hist and macd_hist < 0:
            score -= 3
            reasons.append("MACD histogram negative")
    
    # Stochastic
    stoch_k = latest.get("STOCH_K")
    stoch_d = latest.get("STOCH_D")
    
    if stoch_k is not None:
        if stoch_k < 20:
            score += 7
            reasons.append(f"Stochastic oversold ({stoch_k:.1f})")
        elif stoch_k > 80:
            score -= 7
            reasons.append(f"Stochastic overbought ({stoch_k:.1f})")
        
        if stoch_k and stoch_d and stoch_k > stoch_d and prev.get("STOCH_K", 0) <= prev.get("STOCH_D", 0):
            score += 5
            reasons.append("Stochastic bullish crossover")
        elif stoch_k and stoch_d and stoch_k < stoch_d and prev.get("STOCH_K", 0) >= prev.get("STOCH_D", 0):
            score -= 5
            reasons.append("Stochastic bearish crossover")
    
    # Support / Resistance
    dist_sup = latest.get("Dist_to_Sup")
    dist_res = latest.get("Dist_to_Res")
    
    if dist_sup is not None and dist_sup < 0.4:
        score += 9
        reasons.append(f"Price near Support ({dist_sup:.2f}% away)")
    if dist_res is not None and dist_res < 0.4:
        score -= 9
        reasons.append(f"Price near Resistance ({dist_res:.2f}% away)")
    
    # Candlestick Patterns
    if latest.get("Bullish_Engulfing", False):
        score += 10
        reasons.append("Bullish Engulfing pattern")
    if latest.get("Bearish_Engulfing", False):
        score -= 10
        reasons.append("Bearish Engulfing pattern")
    if latest.get("Bullish_Pinbar", False):
        score += 8
        reasons.append("Bullish Pinbar / Hammer")
    if latest.get("Bearish_Pinbar", False):
        score -= 8
        reasons.append("Bearish Pinbar / Shooting Star")
    
    score = max(0, min(100, score))
    
    if score >= 75:
        signal = "Strong Buy"
        color = "#00c853"
        confidence = "High"
    elif score >= 60:
        signal = "Buy"
        color = "#69f0ae"
        confidence = "Medium"
    elif score <= 25:
        signal = "Strong Sell"
        color = "#d50000"
        confidence = "High"
    elif score <= 40:
        signal = "Sell"
        color = "#ff5252"
        confidence = "Medium"
    else:
        signal = "Neutral"
        color = "#9e9e9e"
        confidence = "Low"
    
    key_levels = {
        "Close": round(close, 5),
        "Support": round(latest.get("Support", 0), 5),
        "Resistance": round(latest.get("Resistance", 0), 5),
        "RSI": round(rsi, 1) if rsi else None,
        "EMA_9": round(ema9, 5) if ema9 else None,
        "EMA_21": round(ema21, 5) if ema21 else None,
    }
    
    return {
        "signal": signal,
        "score": int(score),
        "confidence": confidence,
        "reasons": reasons[:8],
        "color": color,
        "key_levels": key_levels
    }
