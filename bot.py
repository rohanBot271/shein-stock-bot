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
    raise Exception("BOT_TOKEN not set in Railway / Render Environment Variables")

if not CHAT_ID:
    raise Exception("CHAT_ID not set in Railway / Render Environment Variables")

# SHEIN GLOBAL API (WORKING)
CATEGORY_API = "https://api-service.shein.com/galaxy/marketing/v1/category/goods"

# CATEGORY SETTINGS
CAT_ID = "37961"
SPU_CATE_ID = "5939"
COUNTRY = "IN"

CHECK_INTERVAL = 20

HEADERS = {
    "User-Agent": "SHEIN/9.1.0 (Android 13)",
    "Accept": "application/json",
    "Origin": "https://www.shein.com",
    "Referer": "https://www.shein.com/",
    "x-platform": "mobile",
    "x-country": COUNTRY
}

bot = Bot(token=BOT_TOKEN)
last_stock = None

# ======================
# FETCH STOCK
# ======================

def get_stock():
    payload = {
        "catId": CAT_ID,
        "spuCateId": SPU_CATE_ID,
        "page": 1,
        "pageSize": 1,
        "country": COUNTRY,
        "language": "en"
    }

    r = requests.post(CATEGORY_API, headers=HEADERS, json=payload, timeout=15)
    r.raise_for_status()

    data = r.json()

    # Path used by SHEIN mobile apps
    total = (
        data.get("data", {})
            .get("pageInfo", {})
            .get("total", 0)
    )

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

    print("🤖 Shein Stock Bot running (Global API mode)...")

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
                    f"{emoji} STOCK CHANGED\n\n"
                    f"Previous: {last_stock}\n"
                    f"Current: {current}\n"
                    f"Change: {diff:+}\n\n"
                    f"🔗 https://www.sheinindia.in/c/sverse-5939-37961"
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
