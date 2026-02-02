import asyncio
import os
from datetime import datetime

from telegram import Bot
from playwright.async_api import async_playwright

# =====================
# CONFIG
# =====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = "1234416602"

URL = "https://www.sheinindia.in/c/sverse-5939-37961"
CHECK_INTERVAL = 10  # seconds

if not BOT_TOKEN:
    raise Exception("BOT_TOKEN not set in Render Environment Variables")

bot = Bot(token=BOT_TOKEN)

last_men = None
last_women = None

# =====================
# SCRAPE FUNCTION
# =====================
async def get_stock_counts(page):
    await page.goto(URL, timeout=60000)
    await page.wait_for_timeout(5000)

    text = await page.inner_text("body")

    men = 0
    women = 0

    # Simple but reliable parsing
    for line in text.splitlines():
        l = line.lower()
        if "men" in l and any(c.isdigit() for c in l):
            nums = [int(s) for s in l.split() if s.isdigit()]
            if nums:
                men = nums[0]
        if "women" in l and any(c.isdigit() for c in l):
            nums = [int(s) for s in l.split() if s.isdigit()]
            if nums:
                women = nums[0]

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

    message = f"""
{title}

{men_line}
{women_line}

⏰ {now}

Direct Link:
{URL}
"""

    await bot.send_message(chat_id=CHAT_ID, text=message)

# =====================
# MAIN LOOP
# =====================
async def main():
    global last_men, last_women

    print("🤖 Shein Bot running (Render + Browser Mode)...")

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )

        page = await browser.new_page()

        while True:
            try:
                men, women = await get_stock_counts(page)

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

# =====================
# START
# =====================
asyncio.run(main())
