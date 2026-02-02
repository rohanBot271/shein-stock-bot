import asyncio
import os
import requests
from datetime import datetime
from telegram import Bot

# ========================
# CONFIG
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")  # Set this in Railway Variables
CHAT_ID = "1234416602"

# Mobile backend endpoint (2026 working)
API_URL = "https://api-service.shein.com/galaxy/marketing/v1/category/list"

PAGE_LINK = "https://www.sheinindia.in/c/sverse-5939-37961"

CHECK_INTERVAL = 10  # seconds (fast + safe)

if not BOT_TOKEN:
    raise Exception("❌ BOT_TOKEN is not set in environment variables")

bot = Bot(token=BOT_TOKEN)

last_men = None
last_women = None

# ========================
# FETCH STOCK COUNTS
# ========================
def get_stock_counts():
    headers = {
        "User-Agent": "SHEIN/9.7.2 (Android 13)",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": "https://www.sheinindia.in",
        "Referer": "https://www.sheinindia.in"
    }

    payload = {
        "country": "IN",
        "language": "en",
        "scene": "category"
    }

    response = requests.post(API_URL, json=payload, headers=headers, timeout=15)
    response.raise_for_status()

    data = response.json()

    men = 0
    women = 0

    # Walk category list
    for cat in data.get("info", {}).get("categories", []):
        name = str(cat.get("name", "")).lower()
        count = int(cat.get("goods_count", 0))

        if "men" in name:
            men = count
        if "women" in name:
            women = count

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
{PAGE_LINK}
"""

    await bot.send_message(chat_id=CHAT_ID, text=message)

# ========================
# MAIN LOOP
# ========================
async def main():
    global last_men, last_women

    print("🤖 Shein Bot running (Mobile API mode)...")

    while True:
        try:
            men, women = get_stock_counts()

            # First run = just store values
            if last_men is None or last_women is None:
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
