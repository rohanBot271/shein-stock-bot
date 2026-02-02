import asyncio
import os
import requests
import json
import re
from datetime import datetime
from telegram import Bot

# ========================
# CONFIG (Railway Variables)
# ========================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

PAGE_URL = "https://www.sheinindia.in/c/sverse-5939-37961"
CHECK_INTERVAL = 10  # seconds

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not set in Railway Variables")

if not CHAT_ID:
    raise Exception("CHAT_ID not set in Railway Variables")

bot = Bot(token=BOT_TOKEN)

last_men = None
last_women = None

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/html",
    "Accept-Language": "en-IN,en;q=0.9"
}

# ========================
# FETCH STOCK COUNTS
# ========================
def get_stock_counts():
    response = requests.get(PAGE_URL, headers=HEADERS, timeout=15)
    html = response.text

    # Find __NEXT_DATA__ JSON
    match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)
    if not match:
        raise Exception("NEXT_DATA block not found")

    data = json.loads(match.group(1))

    # Walk JSON to find counts
    men = 0
    women = 0

    def walk(obj):
        nonlocal men, women
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    walk(v)
                if k.lower() in ["men", "male"]:
                    if isinstance(v, int):
                        men = v
                if k.lower() in ["women", "female"]:
                    if isinstance(v, int):
                        women = v
        elif isinstance(obj, list):
            for i in obj:
                walk(i)

    walk(data)

    if men == 0 and women == 0:
        raise Exception("Stock numbers not found in page data")

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
{PAGE_URL}
"""

    await bot.send_message(chat_id=CHAT_ID, text=message)

# ========================
# MAIN LOOP
# ========================
async def main():
    global last_men, last_women

    print("🤖 Shein Bot running on Railway (JSON mode)...")

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
