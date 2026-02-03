import asyncio
import requests
import re
from datetime import datetime
from telegram import Bot

# ========================
# CONFIG
# ========================

BOT_TOKEN = "7961340106:AAGHpgBVEY2RUXxzbEf-M0k2t-D9ewPvnd8"

# YOUR CHAT ID
CHAT_IDS = ["1234416602"]

SHEIN_URL = "https://www.sheinindia.in/c/sverse-5939-37961"

CHECK_INTERVAL = 15  # seconds (safe for cloud)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 12)",
    "Accept": "text/html"
}

if not BOT_TOKEN or "PUT_YOUR_BOT_TOKEN_HERE" in BOT_TOKEN:
    raise Exception("❌ Set your BOT_TOKEN before running this bot")

# ========================
# TELEGRAM
# ========================
bot = Bot(token=BOT_TOKEN)

last_men = None
last_women = None

# ========================
# SCRAPER
# ========================
def get_stock_counts():
    response = requests.get(SHEIN_URL, headers=HEADERS, timeout=15)
    response.raise_for_status()
    html = response.text

    # Find text like: Men (23) and Women (177)
    men_match = re.search(r"Men\s*\((\d+)\)", html, re.IGNORECASE)
    women_match = re.search(r"Women\s*\((\d+)\)", html, re.IGNORECASE)

    if not men_match or not women_match:
        raise Exception("Stock data not found in page")

    men = int(men_match.group(1))
    women = int(women_match.group(1))

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

    men_line = f"👨 Men → {men} {men_arrow} {abs(men_diff)}" if men_diff else f"👨 Men → {men}"
    women_line = f"👩 Women → {women} {women_arrow} {abs(women_diff)}" if women_diff else f"👩 Women → {women}"

    title = "🛒 Shein Stock Added" if change_type == "up" else "🛒 Shein Stock Removed"

    message = f"""
{title}

{men_line}
{women_line}

⏰ {now}

Direct Link:
{SHEIN_URL}
"""

    for chat_id in CHAT_IDS:
        await bot.send_message(chat_id=chat_id, text=message)

# ========================
# MAIN LOOP
# ========================
async def main():
    global last_men, last_women

    print("🤖 Shein Bot running (Cloud-safe HTML mode)...")

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

                if men_diff or women_diff:
                    change_type = "up" if (men_diff > 0 or women_diff > 0) else "down"
                    await send_update(men, women, men_diff, women_diff, change_type)

                last_men = men
                last_women = women

        except Exception as e:
            print("Error:", e)

        await asyncio.sleep(CHECK_INTERVAL)

# ========================
# START BOT
# ========================
asyncio.run(main())
