import asyncio
import re
import os
import subprocess
from datetime import datetime
from telegram import Bot
from playwright.async_api import async_playwright

# ========================
# AUTO-INSTALL PLAYWRIGHT BROWSER
# ========================
def ensure_browser():
    try:
        print("🔍 Ensuring Playwright browser is installed...")
        subprocess.run(
            ["playwright", "install", "chromium"],
            check=True
        )
        print("✅ Playwright browser ready")
    except Exception as e:
        print("⚠️ Browser install error:", e)

ensure_browser()

# ========================
# CONFIG
# ========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "1234416602"

SHEIN_URL = "https://www.sheinindia.in/c/sverse-5939-37961"
CHECK_INTERVAL = 15  # seconds

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN is not set")

bot = Bot(token=BOT_TOKEN)

last_men = 0
last_women = 0

# ========================
# SCRAPER
# ========================
async def get_stock_counts(page):
    await page.goto(SHEIN_URL, wait_until="networkidle")

    labels = await page.locator("label").all()

    men = None
    women = None

    for label in labels:
        text = (await label.inner_text()).lower().strip()

        if text.startswith("women"):
            match = re.search(r"\((\d+)\)", text)
            if match:
                women = int(match.group(1))

        if text.startswith("men"):
            match = re.search(r"\((\d+)\)", text)
            if match:
                men = int(match.group(1))

    if men is None or women is None:
        raise Exception("Could not find Men/Women counts")

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
{SHEIN_URL}
"""

    await bot.send_message(chat_id=CHAT_ID, text=message)

# ========================
# MAIN LOOP
# ========================
async def main():
    global last_men, last_women

    print("🤖 Shein Bot running (Playwright, cloud-safe)...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        while True:
            try:
                men, women = await get_stock_counts(page)

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
