import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
import aiohttp
from bs4 import BeautifulSoup

BOT_TOKEN = os.environ["BOT_TOKEN"]
TWITTER_BEARER_TOKEN = os.environ["TWITTER_BEARER_TOKEN"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
PORT = int(os.environ.get("PORT", 10000))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper to fetch trending coins from CoinGecko
async def fetch_trending_coingecko():
    url = "https://api.coingecko.com/api/v3/search/trending"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            return [coin['item']['name'] for coin in data['coins']]

# Helper to scrape trending tokens from DexTools
async def fetch_trending_dextools():
    url = "https://www.dextools.io/app/en/ether/trending"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')
            titles = soup.find_all("h6")
            return [title.get_text(strip=True) for title in titles[:5]]

# Fake volume spike detector (mockup)
async def detect_volume_spikes():
    return ["TokenX - Volume +320%", "TokenY - Volume +240%"]

# Command: /gem
async def gem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cg = await fetch_trending_coingecko()
    dt = await fetch_trending_dextools()
    message = "\ud83d\udcca CoinGecko Trending:\n" + "\n".join(cg[:5])
    message += "\n\n\ud83d\ude80 DEXTools Trending:\n" + "\n".join(dt)
    await update.message.reply_text(message)

# Command: /news
async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    spikes = await detect_volume_spikes()
    await update.message.reply_text("\u26a1 Volume Spikes Detected:\n" + "\n".join(spikes))

# Webhook entry
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("gem", gem_command))
    app.add_handler(CommandHandler("news", news_command))

    await app.initialize()
    await app.start()
    await app.bot.set_webhook(url=WEBHOOK_URL)
    await app.updater.start_webhook(listen="0.0.0.0", port=PORT, url_path="", webhook_url=WEBHOOK_URL)
    await app.updater.idle()

if __name__ == "__main__":
    asyncio.run(main())
