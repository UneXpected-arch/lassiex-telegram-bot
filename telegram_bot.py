import os
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import aiohttp

# Load from environment
BOT_TOKEN = os.environ.get("BOT_TOKEN")
TWITTER_BEARER_TOKEN = os.environ.get("TWITTER_BEARER_TOKEN")
WEBHOOK_URL = os.environ.get("WEBHOOK_URL")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def get_trending_coins():
    url = "https://api.coingecko.com/api/v3/search/trending"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            coins = [f"{i['item']['name']} ({i['item']['symbol']})" for i in data['coins']]
            return "\n".join(coins)


async def get_dextools_gems():
    url = "https://www.dextools.io/shared/explorer/pairs"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                tokens = data.get("pairs", [])[:5]
                return "\n".join([f"{t['baseToken']['symbol']} - Volume: ${t['volume']:,}" for t in tokens])
            return "Failed to fetch gems."


async def get_latest_crypto_news():
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    query = "crypto (lang:en) -is:retweet"
    url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results=5"

    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                tweets = data.get("data", [])
                return "\n\n".join([f"📰 {tweet['text']}" for tweet in tweets])
            return "Failed to fetch news from Twitter."


async def gem_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Scanning for gem tokens on DEXTools...")
    result = await get_dextools_gems()
    await update.message.reply_text(result)


async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Fetching latest crypto news from X.com...")
    result = await get_latest_crypto_news()
    await update.message.reply_text(result)


async def trending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Getting trending coins from CoinGecko...")
    result = await get_trending_coins()
    await update.message.reply_text(result)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to LassieX Bot 🐾\nUse /gem /news /trending")


async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gem", gem_command))
    app.add_handler(CommandHandler("news", news_command))
    app.add_handler(CommandHandler("trending", trending_command))

    # Set webhook
    await app.bot.set_webhook(WEBHOOK_URL)
    logger.info("Webhook set!")

    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_url=WEBHOOK_URL,
    )

if __name__ == "__main__":
    asyncio.run(main())