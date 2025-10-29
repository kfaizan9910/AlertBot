import requests
import datetime
import time
import schedule

# ----------------------------
# 🔧 Telegram Configuration
# ----------------------------
BOT_TOKEN = "8353558883:AAEzt0e3J7eSztLfyQ8qfFVIpthfbifLoOA"       # Apna Telegram bot token yahan dalein
CHAT_ID = "849104070" # Replace with your actual Telegram Chat ID


# ----------------------------
# 📡 Fetch Live NSE Data
# ----------------------------
def get_live_indices():
    """Fetch live index data (NIFTY 50 & BANK NIFTY) from NSE official API."""
    try:
        url = "https://www.nseindia.com/api/allIndices"
        headers = {"User-Agent": "Mozilla/5.0"}
        session = requests.Session()
        session.headers.update(headers)

        response = session.get(url, timeout=10)
        data = response.json()

        result = {}
        for item in data["data"]:
            if item["index"] in ["NIFTY 50", "NIFTY BANK"]:
                last_price = float(item["last"])
                prev_close = float(item["previousClose"])
                change = round(last_price - prev_close, 2)
                direction = "UP 📈" if change > 0 else "DOWN 📉"
                result[item["index"]] = {
                    "last_price": last_price,
                    "prev_close": prev_close,
                    "change": change,
                    "direction": direction
                }

        if not result:
            raise Exception("No index data found.")
        return result

    except Exception as e:
        raise Exception(f"Error fetching NSE data: {e}")

# ----------------------------
# 📬 Telegram Notification
# ----------------------------
def send_telegram_message(text):
    """Send message to Telegram bot."""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        requests.post(url, data=payload, timeout=10)
    except Exception as e:
        print("Telegram send failed:", e)

# ----------------------------
# ⚡ Market Monitor Logic
# ----------------------------
last_directions = {"NIFTY 50": None, "NIFTY BANK": None}

def monitor_market():
    global last_directions
    try:
        indices = get_live_indices()
        now = datetime.datetime.now().strftime('%H:%M:%S')

        for index_name, data in indices.items():
            last_price = data["last_price"]
            change = data["change"]
            direction = data["direction"]

            message = (
                f"<b>📊 {index_name} Update - {now}</b>\n"
                f"Last Price: <b>{last_price}</b>\n"
                f"Change: <b>{change}</b> points\n"
                f"Direction: {direction}"
            )

            print(message)

            # 🚨 Alert when direction flips
            if last_directions[index_name] is None:
                last_directions[index_name] = direction
                send_telegram_message(f"🚀 Tracking started for {index_name}\n" + message)
            elif direction != last_directions[index_name]:
                send_telegram_message(f"⚡ Direction changed for {index_name}!\n" + message)
                last_directions[index_name] = direction

    except Exception as e:
        err_msg = f"⚠️ {e}"
        print(err_msg)
        send_telegram_message(err_msg)

# ----------------------------
# ⏰ Schedule
# ----------------------------
print("✅ Nifty + BankNifty Live Alert Bot Running...\n")

# Run once immediately
monitor_market()

# Run every 2 minutes
schedule.every(1).minutes.do(monitor_market)

while True:
    schedule.run_pending()
    time.sleep(10)
