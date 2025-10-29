import yfinance as yf
import pandas as pd
import numpy as np
import time
from datetime import datetime
import requests

# 🧩 Replace with your credentials
BOT_TOKEN = "8353558883:AAEzt0e3J7eSztLfyQ8qfFVIpthfbifLoOA"       # Apna Telegram bot token yahan dalein
CHAT_ID = "849104070" 

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

    o, c, h, l = map(float, [last["Open"], last["Close"], last["High"], last["Low"]])
    po, pc = map(float, [prev["Open"], prev["Close"]])

    body = abs(c - o)
    candle_range = h - l
    upper_shadow = h - max(c, o)
    lower_shadow = min(c, o) - l

    if body < (candle_range * 0.3) and lower_shadow > body * 2:
        return "Hammer 🟢 (Potential Reversal Up)"
    elif body < (candle_range * 0.3) and upper_shadow > body * 2:
        return "Shooting Star 🔴 (Potential Reversal Down)"
    elif c > o and pc < po:
        return "Bullish Engulfing 🟢"
    elif c < o and pc > po:
        return "Bearish Engulfing 🔴"
    else:
        return "No clear pattern"

# 📊 Trend detection + EMA strategy
def analyze_trend(df):
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    df["EMA50"] = df["Close"].ewm(span=50, adjust=False).mean()

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Make sure these are floats
    ema20_now = float(last["EMA20"])
    ema50_now = float(last["EMA50"])
    ema20_prev = float(prev["EMA20"])
    ema50_prev = float(prev["EMA50"])

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

    # ✅ Fix: ensure scalar values for change
    ticker = "^NSEI"
    hist = yf.download(ticker, period="2d", interval="1d", progress=False)
    if len(hist) >= 2:
        prev_close = float(hist["Close"].iloc[-2])
    else:
        prev_close = float(hist["Close"].iloc[0])

    last_close = float(df["Close"].iloc[-1])
    change = round(last_close - prev_close, 2)

    return direction, signal, last_close, change

# 🧮 Smart combined prediction message
def smart_predict(df):
    direction, signal, price, change = analyze_trend(df)
    pattern = detect_candlestick_pattern(df)

    move_alert = ""
    if abs(change) >= 100:  # Big move alert
        move_alert = f"⚡ Big move alert: {change:+.2f} points today!"

    msg = (
        f"📈 <b>NIFTY Live Alert</b>\n"
        f"💰 Price: {price:.2f}\n"
        f"📊 Trend: {direction}\n"
        f"🧭 Signal: {signal}\n"
        f"🕯 Pattern: {pattern}\n"
        f"📉 Change: {change:+.2f} pts\n"
    )
    if move_alert:
        msg += f"\n{move_alert}"
    return msg

# 🔁 Main bot loop
def run_bot():
    print("🚀 NIFTY Smart Alert Bot Started...")
    last_message = ""
    while True:
        if is_market_open():
            try:
                df = yf.download("^NSEI", period="5d", interval="1m", progress=False)
                if df is not None and len(df) > 50:
                    msg = smart_predict(df)
                    if msg != last_message:
                        send_telegram_message(msg)
                        print(f"✅ Sent update at {datetime.now().strftime('%H:%M:%S')}")
                        last_message = msg
                else:
                    print("⚠️ Insufficient data.")
            except Exception as e:
                print(f"⚠️ Error: {e}")
        else:
            print("⏸ Market closed. Waiting for 9:15 AM...")
        time.sleep(60)  # Check every 1 minute

# ▶️ Run bot
if __name__ == "__main__":
    run_bot()
