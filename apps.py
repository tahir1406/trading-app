import streamlit as st
import yfinance as yf
import pandas as pd
import time

st.set_page_config(page_title="Live Stock App", layout="wide")

st.title("🔴 LIVE - Top 50 Stock Prediction")
st.write(f"Last Update: {time.strftime('%H:%M:%S')}")
if st.button("🔄 Abhi Update Karo"):
    st.rerun()

nifty50 = {
    "RELIANCE": "RELIANCE.NS", "HDFC BANK": "HDFCBANK.NS", "ICICI BANK": "ICICIBANK.NS",
    "INFOSYS": "INFY.NS", "TCS": "TCS.NS", "TITAN": "TITAN.NS", "ITC": "ITC.NS",
    "TATA MOTORS": "TATAMOTORS.NS", "SBI": "SBIN.NS", "TATA STEEL": "TATASTEEL.NS",
    "BAJAJ FINANCE": "BAJFINANCE.NS", "MARUTI": "MARUTI.NS", "NTPC": "NTPC.NS",
    "POWER GRID": "POWERGRID.NS", "ONGC": "ONGC.NS", "ASIAN PAINTS": "ASIANPAINT.NS",
    "HCL TECH": "HCLTECH.NS", "AXIS BANK": "AXISBANK.NS", "KOTAK BANK": "KOTAKBANK.NS",
    "ADANI ENTERPRISES": "ADANIENT.NS", "BHARTI AIRTEL": "BHARTIARTL.NS",
    "SUN PHARMA": "SUNPHARMA.NS", "ULTRATECH": "ULTRACEMCO.NS", "HUL": "HINDUNILVR.NS",
    "TATA POWER": "TATAPOWER.NS", "COAL INDIA": "COALINDIA.NS", "JSW STEEL": "JSWSTEEL.NS",
    "HINDALCO": "HINDALCO.NS", "CIPLA": "CIPLA.NS", "WIPRO": "WIPRO.NS",
    "TECH MAHINDRA": "TECHM.NS", "TRENT": "TRENT.NS", "GRASIM": "GRASIM.NS",
    "EICHER MOTORS": "EICHERMOT.NS", "HERO MOTOCORP": "HEROMOTOCO.NS",
    "BRITANNIA": "BRITANNIA.NS", "NESTLE": "NESTLEIND.NS", "BPCL": "BPCL.NS",
    "TATA CONSUMER": "TATACONSUM.NS", "DIVIS LAB": "DIVISLAB.NS", "DR REDDY": "DRREDDY.NS",
    "APOLLO HOSPITAL": "APOLLOHOSP.NS", "LTIMINDTREE": "LTIM.NS", "SBILIFE": "SBILIFE.NS",
    "HDFCLIFE": "HDFCLIFE.NS", "INDUSIND BANK": "INDUSINDBK.NS", "SHRIRAM FINANCE": "SHRIRAMFIN.NS",
    "LARSEN": "LT.NS", "ADANI PORTS": "ADANIPORTS.NS",
}

search = st.text_input("🔍 Stock Search Karo").upper()
if search:
    filtered = {k:v for k,v in nifty50.items() if search in k}
else:
    filtered = nifty50

stock_name = st.selectbox("Stock Chuno:", list(filtered.keys()) if filtered else list(nifty50.keys()))
ticker = nifty50.get(stock_name, stock_name+".NS")

@st.cache_data(ttl=60)
def get_live_data(ticker):
    daily = yf.download(ticker, period="3mo", interval="1d", progress=False)
    live = yf.download(ticker, period="1d", interval="1m", progress=False)
    return daily, live

def calculate_all(daily, live):
    if len(daily) < 20: return None
    close = pd.Series(daily['Close'].values.flatten())
    high = pd.Series(daily['High'].values.flatten())
    low = pd.Series(daily['Low'].values.flatten())
    live_price = float(live['Close'].values.flatten()[-1]) if len(live)>0 else float(close.iloc[-1])
    open_price = float(live['Open'].values.flatten()[0]) if len(live)>0 else float(close.iloc[-2])
    day_change = (live_price - open_price)/open_price*100
    tr = pd.concat([high-low, (high-close.shift()).abs(), (low-close.shift()).abs()], axis=1).max(axis=1)
    atr = float(tr.rolling(14).mean().iloc[-1])
    prev_high = float(high.iloc[-2]); prev_low = float(low.iloc[-2]); prev_close = float(close.iloc[-2])
    pivot = (prev_high+prev_low+prev_close)/3
    r1 = 2*pivot-prev_low; r2 = pivot+(prev_high-prev_low)
    s1 = 2*pivot-prev_high; s2 = pivot-(prev_high-prev_low)
    delta = close.diff()
    gain = delta.where(delta>0,0).rolling(14).mean()
    loss = -delta.where(delta<0,0).rolling(14).mean()
    rsi = 100-(100/(1+gain/loss))
    rsi_val = float(rsi.iloc[-1])
    ma10 = float(close.rolling(10).mean().iloc[-1])
    ma50 = float(close.rolling(50).mean().iloc[-1])
    score = 50
    if rsi_val < 30: score += 15
    elif rsi_val > 70: score -= 15
    if live_price > ma10: score += 15
    else: score -= 15
    if live_price > ma50: score += 10
    else: score -= 10
    if day_change > 0: score += 5
    else: score -= 5
    if score >= 55:
        target_up = live_price + atr*1.5
        target_down = live_price - atr*1.0
        direction = "UP"
    else:
        target_up = live_price + atr*1.0
        target_down = live_price - atr*1.5
        direction = "DOWN"
    return {"live_price": live_price, "day_change": day_change, "score": score, "rsi": rsi_val, "atr": atr, "r1": r1, "r2": r2, "s1": s1, "s2": s2, "pivot": pivot, "target_up": target_up, "target_down": target_down, "direction": direction, "live_df": live}

daily, live = get_live_data(ticker)
r = calculate_all(daily, live)
if r:
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"{stock_name} LIVE", f"₹{r['live_price']:.2f}", f"{r['day_change']:.2f}%")
    c2.metric("Prediction", "🟢 UP" if r['direction']=="UP" else "🔴 DOWN", f"{r['score']}%")
    c3.metric("Upar Target", f"₹{r['target_up']:.2f}", f"+₹{r['target_up']-r['live_price']:.2f}")
    c4.metric("Neeche Target", f"₹{r['target_down']:.2f}", f"-₹{r['live_price']-r['target_down']:.2f}")
    if r['direction']=="UP":
        st.success(f"🟢 {stock_name} UP me hai. Upar ₹{r['target_up']:.2f} tak, Neeche ₹{r['target_down']:.2f} tak.")
    else:
        st.error(f"🔴 {stock_name} DOWN me hai. Neeche ₹{r['target_down']:.2f} tak, Upar ₹{r['target_up']:.2f} tak.")
    st.subheader(f"📈 {stock_name} - Aaj Ka Live Graph")
import altair as alt
prices = r['live_df']['Close'].values.flatten()
chart_df = pd.DataFrame({"Time": r['live_df'].index, "Price": prices})
y_min = float(min(prices) * 0.995)
y_max = float(max(prices) * 1.005)
chart = alt.Chart(chart_df).mark_line(color='green').encode(x='Time:T', y=alt.Y('Price:Q', scale=alt.Scale(domain=[y_min, y_max])))
st.altair_chart(chart, use_container_width=True)

st.divider()
st.subheader("🔥 Top 50 - Live Table")
if st.button("Sare 50 Ko Live Update Karo"):
    rows = []
    bar = st.progress(0)
    for i, (name, tick) in enumerate(filtered.items()):
        d, l = get_live_data(tick)
        rr = calculate_all(d, l)
        if rr:
            mood = "🟢 UP" if rr['direction']=="UP" else "🔴 DOWN"
            rows.append([name, f"₹{rr['live_price']:.2f}", f"{rr['day_change']:.2f}%", mood, f"₹{rr['target_up']:.2f}", f"₹{rr['target_down']:.2f}"])
        bar.progress((i+1)/len(filtered))
    df = pd.DataFrame(rows, columns=["Stock","Live Price","Aaj Change","Prediction","Upar Target","Neeche Target"])
    st.dataframe(df, use_container_width=True)