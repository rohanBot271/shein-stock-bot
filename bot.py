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

# SHEIN GLOBAL MOBILE API
CATEGORY_API = "https://api-service.shein.com/h5/category/get_goods_list"

# PRODUCT CATEGORY SETTINGS
CAT_ID = "37961"
SPU_CATE_ID = "5939"
COUNTRY = "IN"

CHECK_INTERVAL = 20  # seconds (FAST)

HEADERS = {
    "User-Agent": "SHEIN/8.9.2 (Android 12)",
    "Accept": "application/json",
    "Origin": "https://www.shein.com",
    "Referer": "https://www.shein.com/",
    "x-platform": "mobile"
}

# ======================
# BOT
# ======================

bot = Bot(token=BOT_TOKEN)

last_stock = None


def get_stock():
    params = {
        "cat_id": CAT_ID,
        "spu_cate_id": SPU_CATE_ID,
        "page": 1,
        "limit": 1,
        "country": COUNTRY,
        "language": "en",
        "currency": "INR"
    }

    r = requests.get(CATEGORY_API, headers=HEADERS, params=params, timeout=15)
    r.raise_for_status()

    data = r.json()

    total = data.get("info", {}).get("total", 0)
    return int(total)


async def send(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg)


# ======================
# MAIN LOOP
# ======================

async def main():
    global last_stock

    print("🤖 Shein Stock Bot running (API mode)...")

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

                if diff > 0:
                    emoji = "📈"
                    change = f"+{diff}"
                else:
                    emoji = "📉"
                    change = f"{diff}"

                msg = (
                    f"{emoji} STOCK CHANGED\n\n"
                    f"Previous: {last_stock}\n"
                    f"Current: {current}\n"
                    f"Change: {change}"
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
