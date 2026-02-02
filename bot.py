import asyncio
import os
import requests
import re
import json
from datetime import datetime
from telegram import Bot

# ========================
# CONFIG
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "1234416602"

PAGE_URL = "https://www.sheinindia.in/c/sverse-5939-37961"
CHECK_INTERVAL = 10  # seconds

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN is not set")

bot = Bot(token=BOT_TOKEN)

last_men = 0
last_women = 0

# ========================
# FETCH + PARSE
# ========================
def get_stock_counts():
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "text/html",
        "Referer": "https://www.sheinindia.in/"
    }

    html = requests.get(PAGE_URL, headers=headers, timeout=15).text

    # Next.js embedded JSON
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html,
        re.S
    )

    if not match:
        raise Exception("NEXT_DATA block not found")

    data = json.loads(match.group(1))

    men = 0
    women = 0

    # Recursively walk the JSON tree
    def walk(obj):
        nonlocal men, women
        if isinstance(obj, dict):
            name = str(obj.get("name", "")).lower()
            count = obj.get("goods_count")

            if count is not None:
                if "men" in name:
                    men = int(count)
                if "women" in name:
                    women = int(count)

            for v in obj.values():
                walk(v)

        elif isinstance(obj, list):
            for item in obj:
                walk(item)

    walk(data)

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

    print("🤖 Shein Bot running (HTML JSON mode)...")

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
