import os
import asyncio
import requests
from telegram import Bot

# ======================
# CONFIG
# ======================

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not set in Railway Variables")
if not CHAT_ID:
    raise Exception("CHAT_ID not set in Railway Variables")

# Your category link
CATEGORY_URL = "https://www.sheinindia.in/c/sverse-5939-37961"

# Public search API (STILL WORKS)
SEARCH_API = "https://www.shein.com/api/search/search"

CHECK_INTERVAL = 20

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Referer": "https://www.shein.com/"
}

bot = Bot(token=BOT_TOKEN)
last_stock = None

# ======================
# FETCH STOCK
# ======================

def get_stock():
    params = {
        "url": CATEGORY_URL,
        "page": 1,
        "limit": 1
    }

    r = requests.get(SEARCH_API, headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()

    data = r.json()

    # SHEIN returns total count here
    total = data.get("info", {}).get("total", None)

    if total is None:
        raise Exception("Stock count not found in API response")

    return int(total)

# ======================
# TELEGRAM SEND
# ======================

async def send(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg)

# ======================
# MAIN LOOP
# ======================

async def main():
    global last_stock

    print("🤖 Shein Stock Bot running (Public API mode)...")

    try:
        last_stock = get_stock()
        print(f"Initial stock: {last_stock}")
        await send(f"🟢 Bot Started\nInitial Stock: {last_stock}")
    except Exception as e:
        print("Startup error:", e)
        await send(f"🔴 Startup Error:\n{e}")
        return

    while True:
        try:
            current = get_stock()
            print(f"Checked: {current}")

            if current != last_stock:
                diff = current - last_stock
                emoji = "📈" if diff > 0 else "📉"

                msg = (
                    f"{emoji} SHEIN STOCK CHANGED\n\n"
                    f"Previous: {last_stock}\n"
                    f"Current: {current}\n"
                    f"Change: {diff:+}\n\n"
                    f"🔗 {CATEGORY_URL}"
                )

                await send(msg)
                last_stock = current

        except Exception as e:
            print("Error:", e)
            await send(f"⚠️ Error:\n{e}")

        await asyncio.sleep(CHECK_INTERVAL)

# ======================
# START
# ======================

if __name__ == "__main__":
    asyncio.run(main())
