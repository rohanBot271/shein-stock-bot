import asyncio
import requests
import json
import re
from datetime import datetime
from telegram import Bot

# =====================
# CONFIG
# =====================
BOT_TOKEN = "7961340106:AAGHpgBVEY2RUXxzbEf-M0k2t-D9ewPvnd8"
CHAT_IDS = ["1234416602"]  # add more like ["123", "456"]

SHEIN_URL = "https://www.sheinindia.in/c/sverse-5939-37961"
CHECK_INTERVAL = 30  # seconds

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9"
}

# =====================
# TELEGRAM
# =====================
bot = Bot(token=BOT_TOKEN)

last_men = 0
last_women = 0

# =====================
# SHEIN SCRAPER
# =====================
def get_stock_counts():
    res = requests.get(SHEIN_URL, headers=HEADERS, timeout=20)

    if res.status_code != 200:
        raise Exception(f"HTTP {res.status_code}")

    html = res.text

    # Find Next.js JSON block
    match = re.search(r'__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)

    if not match:
        raise Exception("NEXT_DATA block not found")

    data = json.loads(match.group(1))

    # Navigate SHEIN data tree safely
    props = data.get("props", {})
    page = props.get("pageProps", {})
    initial = page.get("initialState", {})

    raw = json.dumps(initial)

    # Find numbers like "Men (23)" and "Women (177)"
    men_match = re.search(r'Men\s*\((\d+)\)', raw, re.I)
    women_match = re.search(r'Women\s*\((\d+)\)', raw, re.I)

    if not men_match or not women_match:
        raise Exception("Stock numbers not found in JSON")

    men = int(men_match.group(1))
    women = int(women_match.group(1))

    return men, women

# =====================
# TELEGRAM MESSAGE
# =====================
async def send_update(men, women, men_diff, women_diff, change_type):
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")

    arrow_up = "⬆️"
    arrow_down = "⬇️"

    men_arrow = arrow_up if men_diff > 0 else arrow_down if men_diff < 0 else ""
    women_arrow = arrow_up if women_diff > 0 else arrow_down if women_diff < 0 else ""

    men_line = f"👨 Men → {men} {men_arrow} {abs(men_diff)}" if men_diff else f"👨 Men → {men}"
    women_line = f"👩 Women → {women} {women_arrow} {abs(women_diff)}" if women_diff else f"👩 Women → {women}"

    title = "🛒 Shein Stock Added" if change_type == "up" else "🛒 Shein Stock Removed"

    message = f"""{title}

{men_line}
{women_line}

⏰ {now}
🔗 {SHEIN_URL}
"""

    for chat_id in CHAT_IDS:
        await bot.send_message(chat_id=chat_id, text=message)

# =====================
# MAIN LOOP
# =====================
async def main():
    global last_men, last_women

    print("🤖 Shein Bot running (Cloud-safe JSON mode)...")

    while True:
        try:
            men, women = get_stock_counts()

            men_diff = men - last_men
            women_diff = women - last_women

            print("Checked:", men, women)

            if men_diff or women_diff:
                change_type = "up" if (men_diff > 0 or women_diff > 0) else "down"
                await send_update(men, women, men_diff, women_diff, change_type)

            last_men = men
            last_women = women

        except Exception as e:
            print("Error:", e)

        await asyncio.sleep(CHECK_INTERVAL)

# =====================
# START
# =====================
asyncio.run(main())
