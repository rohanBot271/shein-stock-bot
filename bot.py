import asyncio
import os
import requests
from datetime import datetime
from telegram import Bot

# ========================
# CONFIG
# ========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

CATEGORY_API = "https://m.sheinindia.in/api/category/get_goods_list"

CATEGORY_ID = "37961"
SUB_CATEGORY_ID = "5939"

CHECK_INTERVAL = 10

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not set in Railway Variables")

if not CHAT_ID:
    raise Exception("CHAT_ID not set in Railway Variables")

bot = Bot(token=BOT_TOKEN)

last_men = None
last_women = None

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; Mobile)",
    "Accept": "application/json",
    "Referer": "https://m.sheinindia.in/"
}

# ========================
# FETCH STOCK COUNTS
# ========================
def get_stock_counts():
    params = {
        "cat_id": CATEGORY_ID,
        "spu_cate_id": SUB_CATEGORY_ID,
        "page": 1,
        "limit": 200
    }

    r = requests.get(CATEGORY_API, headers=HEADERS, params=params, timeout=15)

    if r.status_code != 200:
        raise Exception(f"API status {r.status_code}")

    data = r.json()

    goods = data.get("info", {}).get("goods_list", [])

    men = 0
    women = 0

    for item in goods:
        gender = str(item.get("gender", "")).lower()
        stock = int(item.get("stock", 0))

        if "men" in gender or "male" in gender:
            men += stock
        elif "women" in gender or "female" in gender:
            women += stock

    if men == 0 and women == 0:
        raise Exception("Stock data not found in API response")

    return men, women

# ========================
# TELEGRAM MESSAGE
# ========================
async def send_update(men, women, men_diff, women_diff, change_type):
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")

    arrow_up = "⬆️"
    arrow_down = "⬇️"

    men_arrow = arrow_up if men_diff > 0 else arrow_down if men_diff < 0 else ""
    women_arrow = arrow_up if women_diff > 0 else arrow_down if women_diff < 0 else ""

    men_line = f"👨 Men → {men} {men_arrow} {abs(men_diff)}" if men_diff != 0 else f"👨 Men → {men}"
    women_line = f"👩 Women → {women} {women_arrow} {abs(women_diff)}" if women_diff != 0 else f"👩 Women → {women}"

    title = "🛒 Shein Stock Added" if change_type == "up" else "🛒 Shein Stock Removed"

    message = f"""
{title}

{men_line}
{women_line}

⏰ {now}

Direct Link:
https://www.sheinindia.in/c/sverse-5939-37961
"""

    await bot.send_message(chat_id=CHAT_ID, text=message)

# ========================
# MAIN LOOP
# ========================
async def main():
    global last_men, last_women

    print("🤖 Shein Bot running on Railway (Mobile API mode)...")

    while True:
        try:
            men, women = get_stock_counts()

            if last_men is None:
                last_men = men
                last_women = women
                print("Initial stock:", men, women)
            else:
                men_diff = men - last_men
                women_diff = women - last_women

                print("Checked:", men, women)

                if men_diff != 0 or women_diff != 0:
                    change_type = "up" if (men_diff > 0 or women_diff > 0) else "down"
                    await send_update(men, women, men_diff, women_diff, change_type)

                last_men = men
                last_women = women

        except Exception as e:
            print("Error:", e)

        await asyncio.sleep(CHECK_INTERVAL)

# ========================
# START
# ========================
asyncio.run(main())
