import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
import requests

# 🧩 Replace with your Telegram credentials
BOT_TOKEN = "8353558883:AAEzt0e3J7eSztLfyQ8qfFVIpthfbifLoOA"       # Apna Telegram bot token yahan dalein
CHAT_ID = "849104070" # Replace with your actual Telegram Chat ID


# 🔧 Telegram message sender
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"⚠️ Telegram send error: {e}")

# 🕒 Market time check (9:15–15:30)
def is_market_open():
    now = datetime.now()
    return now.hour >= 9 and (now.hour < 15 or (now.hour == 15 and now.minute <= 30))

# 🧠 Candlestick pattern detection
def detect_candlestick_pattern(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Safe extraction of scalar values
    o = float(last["Open"].iloc[0] if isinstance(last["Open"], pd.Series) else last["Open"])
    c = float(last["Close"].iloc[0] if isinstance(last["Close"], pd.Series) else last["Close"])
    h = float(last["High"].iloc[0] if isinstance(last["High"], pd.Series) else last["High"])
    l = float(last["Low"].iloc[0] if isinstance(last["Low"], pd.Series) else last["Low"])
    po = float(prev["Open"].iloc[0] if isinstance(prev["Open"], pd.Series) else prev["Open"])
    pc = float(prev["Close"].iloc[0] if isinstance(prev["Close"], pd.Series) else prev["Close"])

    body = abs(c - o)
    candle_range = h - l
    upper_shadow = h - max(c, o)
    lower_shadow = min(c, o) - l

    if body < (candle_range * 0.3) and lower_shadow > body * 2:
        return "Hammer 🟢 (Reversal Up)"
    elif body < (candle_range * 0.3) and upper_shadow > body * 2:
        return "Shooting Star 🔴 (Reversal Down)"
    elif c > o and pc < po:
        return "Bullish Engulfing 🟢"
    elif c < o and pc > po:
        return "Bearish Engulfing 🔴"
    else:
        return "No clear pattern"

# 📊 Trend detection + EMA strategy
def analyze_trend(df, ticker_name):
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    ema20_now = float(last["EMA20"].iloc[0] if isinstance(last["EMA20"], pd.Series) else last["EMA20"])
    ema50_now = float(last["EMA50"].iloc[0] if isinstance(last["EMA50"], pd.Series) else last["EMA50"])
    ema20_prev = float(prev["EMA20"].iloc[0] if isinstance(prev["EMA20"], pd.Series) else prev["EMA20"])
    ema50_prev = float(prev["EMA50"].iloc[0] if isinstance(prev["EMA50"], pd.Series) else prev["EMA50"])

    direction = ""
    signal = ""

    if ema20_now > ema50_now and ema20_prev <= ema50_prev:
        direction = "Bullish 🟢"
        signal = "EMA20 crossed above EMA50"
    elif ema20_now < ema50_now and ema20_prev >= ema50_prev:
        direction = "Bearish 🔴"
        signal = "EMA20 crossed below EMA50"
    else:
        direction = "Sideways ⚪"
        signal = "No major crossover"

    hist = yf.download(ticker_name, period="2d", interval="1d", progress=False)
    prev_close = float(hist["Close"].iloc[-2].item() if isinstance(hist["Close"].iloc[-2], (pd.Series, np.ndarray)) else hist["Close"].iloc[-2])
    last_close = float(df["Close"].iloc[-1].item() if isinstance(df["Close"].iloc[-1], (pd.Series, np.ndarray)) else df["Close"].iloc[-1])
    change = round(last_close - prev_close, 2)

    return direction, signal, last_close, change

# 🧮 Smart combined prediction message
def smart_predict(ticker_name, display_name):
    df = yf.download(ticker_name, period="5d", interval="1m", progress=False)
    if df is None or len(df) < 50:
        return f"⚠️ Not enough data for {display_name}"

    direction, signal, price, change = analyze_trend(df, ticker_name)
    pattern = detect_candlestick_pattern(df)

    move_alert = ""
    if abs(change) >= 100:
        move_alert = f"⚡ Big move alert: {change:+.2f} points today!"

    msg = (
        f"📊 <b>{display_name} Live Alert</b>\n"
        f"💰 Price: {price:.2f}\n"
        f"📈 Trend: {direction}\n"
        f"🧭 Signal: {signal}\n"
        f"🕯 Pattern: {pattern}\n"
        f"📉 Change: {change:+.2f} pts\n"
    )
    if move_alert:
        msg += f"\n{move_alert}"
    return msg

# 🔁 Main bot loop
def run_bot():
    print("🚀 NIFTY + BANKNIFTY + SENSEX Smart Alert Bot Started...")
    last_messages = {}

    indices = {
        "^NSEI": "NIFTY 50",
        "^NSEBANK": "BANKNIFTY",
        "^BSESN": "SENSEX",
    }

    while True:
        if is_market_open():
            try:
                for ticker, name in indices.items():
                    msg = smart_predict(ticker, name)
                    if last_messages.get(ticker) != msg:
                        send_telegram_message(msg)
                        last_messages[ticker] = msg
                        print(f"✅ {name} update sent at {datetime.now().strftime('%H:%M:%S')}")

            except Exception as e:
                print(f"⚠️ Error: {e}")
        else:
            print("⏸ Market closed. Waiting for 9:15 AM...")

        time.sleep(60)  # check every minute

# ▶️ Run bot
if __name__ == "__main__":
    run_bot()
