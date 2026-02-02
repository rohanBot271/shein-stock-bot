import asyncio
import os
import requests
from datetime import datetime
from telegram import Bot

# ========================
# CONFIG
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "1234416602"

# This is Shein's category API (used by their app)
API_URL = "https://api-service.shein.com/v2/category/tree"
print("USING API:", API_URL)
# Category params (these match your SheinVerse page)
BASE_PARAMS = {
    "cat_id": "37961",
    "spu_cate_id": "5939",
    "page": 1,
    "limit": 1,
    "country": "IN",
    "language": "en",
    "currency": "INR"
}

CHECK_INTERVAL = 10  # seconds (FAST + SAFE)

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN is not set")

bot = Bot(token=BOT_TOKEN)

last_men = 0
last_women = 0

# ========================
# API FETCH
# ========================
def get_stock_counts():
    headers = {
        "User-Agent": "SHEIN/9.6.0 (iPhone; iOS 16.0)",
        "Accept": "application/json",
        "Referer": "https://www.sheinindia.in/",
        "Origin": "https://www.sheinindia.in"
    }

    params = {
        "country": "IN",
        "language": "en"
    }

    response = requests.get(API_URL, params=params, headers=headers, timeout=10)
    response.raise_for_status()

    data = response.json()

    men = 0
    women = 0

    # Walk category tree
    def walk(categories):
        nonlocal men, women
        for cat in categories:
            name = cat.get("name", "").lower()
            count = cat.get("goods_count", 0)

            if "men" in name:
                men = int(count)
            if "women" in name:
                women = int(count)

            if "children" in cat:
                walk(cat["children"])

    walk(data["info"]["categories"])

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

    print("🤖 Shein Bot running (API mode)...")

    while True:
        try:
            men, women = get_stock_counts()

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
