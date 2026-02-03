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
CHAT_IDS = ["1234416602"]

SHEIN_URL = "https://www.sheinindia.in/c/sverse-5939-37961"
CHECK_INTERVAL = 45

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.sheinindia.in/",
    "sec-ch-ua-mobile": "?1",
    "sec-ch-ua-platform": "Android"
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
    session = requests.Session()
    session.headers.update(HEADERS)

    r = session.get(SHEIN_URL, timeout=20)

    if r.status_code != 200:
        raise Exception(f"HTTP {r.status_code}")

    html = r.text

    # Extract NextJS JSON
    match = re.search(r'__NEXT_DATA__" type="application/json">(.*?)</script>', html, re.S)

    if not match:
        raise Exception("NEXT_DATA block not found")

    data = json.loads(match.group(1))

    state = json.dumps(
        data.get("props", {})
            .get("pageProps", {})
            .get("initialState", {})
    )

    men_match = re.search(r'Men\s*\((\d+)\)', state, re.I)
    women_match = re.search(r'Women\s*\((\d+)\)', state, re.I)

    if not men_match or not women_match:
        raise Exception("Stock numbers not found")

    return int(men_match.group(1)), int(women_match.group(1))

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

    msg = f"""{title}

{men_line}
{women_line}

⏰ {now}
🔗 {SHEIN_URL}
"""

    for chat_id in CHAT_IDS:
        await bot.send_message(chat_id=chat_id, text=msg)

# =====================
# MAIN LOOP
# =====================
async def main():
    global last_men, last_women

    print("🤖 Shein Bot running (Mobile Emulation Mode)...")

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
