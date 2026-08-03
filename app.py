import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import time

from utils.data_fetcher import fetch_data, get_available_pairs
from utils.indicators import add_all_indicators
from utils.signals import generate_signal

# ---------------------- Page Config ----------------------
st.set_page_config(
    page_title="Market Signal Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------- Custom CSS ----------------------
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E88E5;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #666;
        margin-bottom: 1.5rem;
    }
    .signal-box {
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1E88E5;
    }
    .disclaimer {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 8px;
        padding: 1rem;
        font-size: 0.9rem;
        color: #856404;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------- Sidebar ----------------------
st.sidebar.title("⚙️ Settings")

pairs = get_available_pairs()
market_type = st.sidebar.selectbox("Market Type", ["Crypto", "Forex"])

symbol = st.sidebar.selectbox("Pair", pairs[market_type])

timeframe = st.sidebar.selectbox("Timeframe", ["1m", "5m", "15m"], index=1)

limit = st.sidebar.slider("Candles to load", min_value=100, max_value=500, value=250, step=50)

auto_refresh = st.sidebar.checkbox("Auto-refresh (60s)", value=False)

st.sidebar.markdown("---")
st.sidebar.markdown("### ℹ️ Data Notes")
if market_type == "Forex":
    st.sidebar.warning("Forex data from Yahoo Finance is usually **delayed 15-60 minutes**.")
else:
    st.sidebar.success("Crypto data is near real-time (Binance).")

st.sidebar.markdown("---")
st.sidebar.markdown("""
**Disclaimer**  
This tool is for educational purposes only.  
Not financial advice. Trading involves high risk of loss.
""")

# ---------------------- Header ----------------------
st.markdown('<div class="main-header">📊 Market Signal Dashboard</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">Analyzing <b>{symbol}</b> • {timeframe} • {market_type}</div>', unsafe_allow_html=True)

# ---------------------- Load Data ----------------------
@st.cache_data(ttl=60, show_spinner=False)
def load_and_process(market_type, symbol, timeframe, limit):
    df = fetch_data(market_type, symbol, timeframe, limit)
    if df.empty:
        return None, None
    df = add_all_indicators(df)
    signal_data = generate_signal(df)
    return df, signal_data

with st.spinner("Fetching market data and calculating indicators..."):
    df, signal_data = load_and_process(market_type, symbol, timeframe, limit)

if df is None or df.empty:
    st.error("Failed to fetch data. Please try another pair or try again later.")
    st.stop()

# ---------------------- Signal Card ----------------------
col1, col2, col3 = st.columns([1.2, 1, 1])

with col1:
    signal = signal_data["signal"]
    score = signal_data["score"]
    color = signal_data["color"]
    confidence = signal_data["confidence"]
    
    st.markdown(f"""
    <div class="signal-box" style="background: linear-gradient(135deg, {color}22, {color}44); border: 2px solid {color};">
        <h2 style="color: {color}; margin: 0;">{signal}</h2>
        <p style="font-size: 1.8rem; font-weight: bold; margin: 0.3rem 0;">{score}/100</p>
        <p style="margin: 0; color: #555;">Confidence: <b>{confidence}</b></p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    levels = signal_data["key_levels"]
    st.markdown("### Key Levels")
    st.metric("Current Price", f"{levels.get('Close', 0):,.5f}")
    st.metric("Support", f"{levels.get('Support', 0):,.5f}")
    st.metric("Resistance", f"{levels.get('Resistance', 0):,.5f}")

with col3:
    st.markdown("### Indicators")
    st.metric("RSI (14)", f"{levels.get('RSI', 'N/A')}")
    st.metric("EMA 9", f"{levels.get('EMA_9', 'N/A')}")
    st.metric("EMA 21", f"{levels.get('EMA_21', 'N/A')}")

# ---------------------- Reasons ----------------------
st.markdown("### 📝 Signal Reasons")
if signal_data["reasons"]:
    for reason in signal_data["reasons"]:
        st.markdown(f"- {reason}")
else:
    st.info("No strong directional reasons detected.")

# ---------------------- Chart ----------------------
st.markdown("### 📈 Price Chart with Indicators")

fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.03,
    row_heights=[0.6, 0.2, 0.2],
    subplot_titles=("Price + Bollinger + MAs", "RSI", "MACD")
)

# Candlestick
fig.add_trace(go.Candlestick(
    x=df.index,
    open=df["Open"],
    high=df["High"],
    low=df["Low"],
    close=df["Close"],
    name="Price"
), row=1, col=1)

# Bollinger Bands
if "BB_Upper" in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_Upper"], name="BB Upper", line=dict(color="rgba(100,100,100,0.5)", width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["BB_Lower"], name="BB Lower", line=dict(color="rgba(100,100,100,0.5)", width=1), fill="tonexty", fillcolor="rgba(100,100,100,0.1)"), row=1, col=1)

# EMAs
if "EMA_9" in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA_9"], name="EMA 9", line=dict(color="#2196F3", width=1.5)), row=1, col=1)
if "EMA_21" in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df["EMA_21"], name="EMA 21", line=dict(color="#FF9800", width=1.5)), row=1, col=1)

# Support / Resistance lines (last values)
if "Support" in df.columns:
    last_sup = df["Support"].iloc[-1]
    last_res = df["Resistance"].iloc[-1]
    fig.add_hline(y=last_sup, line_dash="dot", line_color="green", annotation_text="Support", row=1, col=1)
    fig.add_hline(y=last_res, line_dash="dot", line_color="red", annotation_text="Resistance", row=1, col=1)

# RSI
if "RSI" in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI", line=dict(color="#9C27B0", width=1.5)), row=2, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=2, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=2, col=1)

# MACD
if "MACD" in df.columns:
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD"], name="MACD", line=dict(color="#2196F3", width=1.5)), row=3, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df["MACD_Signal"], name="Signal", line=dict(color="#FF9800", width=1.5)), row=3, col=1)
    if "MACD_Hist" in df.columns:
        colors = ["#26a69a" if val >= 0 else "#ef5350" for val in df["MACD_Hist"]]
        fig.add_trace(go.Bar(x=df.index, y=df["MACD_Hist"], name="Histogram", marker_color=colors), row=3, col=1)

fig.update_layout(
    height=800,
    xaxis_rangeslider_visible=False,
    template="plotly_white",
    showlegend=True,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=40, b=40)
)

fig.update_yaxes(title_text="Price", row=1, col=1)
fig.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1)
fig.update_yaxes(title_text="MACD", row=3, col=1)

st.plotly_chart(fig, use_container_width=True)

# ---------------------- Data Table (last 10 candles) ----------------------
with st.expander("Recent Candles + Indicators (last 10)"):
    display_cols = ["Open", "High", "Low", "Close", "Volume", "RSI", "EMA_9", "EMA_21", "MACD"]
    available_cols = [c for c in display_cols if c in df.columns]
    st.dataframe(df[available_cols].tail(10).style.format("{:.5f}"), use_container_width=True)

# ---------------------- Disclaimer ----------------------
st.markdown("---")
st.markdown("""
<div class="disclaimer">
<strong>⚠️ Risk Disclaimer</strong><br>
This dashboard is for <strong>educational and informational purposes only</strong>. 
It does not constitute financial, investment, or trading advice. 
Technical indicators and signals can (and often do) fail. 
Cryptocurrency and Forex trading involve substantial risk of loss. 
Never trade with money you cannot afford to lose. 
The creators assume no liability for any losses incurred.
</div>
""", unsafe_allow_html=True)

# ---------------------- Auto Refresh ----------------------
if auto_refresh:
    time.sleep(60)
    st.rerun()
