# telegram_bot.py — LassieX Full Bot (Webhooks + Features)

import os
import re
import json
import logging
import asyncio
from datetime import datetime, timedelta

import aiohttp
import nest_asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
)

# ✅ Load environment variables BEFORE using them
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
COINGECKO_API = os.getenv("COINGECKO_API", "https://api.coingecko.com/api/v3")
DEXTOOLS_BASE = os.getenv("DEXTOOLS_BASE", "https://www.dextools.io")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
VOLUME_SPIKE_THRESHOLD = float(os.getenv("VOLUME_SPIKE_THRESHOLD", 2.5))

# 🔁 Fix for nested async issues (Render requires this)
nest_asyncio.apply()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LassieX")

# ✅ Ensure ApplicationBuilder comes AFTER the env variables
app = ApplicationBuilder().token(BOT_TOKEN).build()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LassieX")

# --- Feature: Get Trending Pairs from DexTools ---
async def get_dextools_trending():
    url = f"{DEXTOOLS_BASE}/api/pairs/trending"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            data = await resp.json()
            trending = data.get("pairs", [])[:5]
            return [f"{p['baseToken']['symbol']} - {p['url']}" for p in trending if 'url' in p]

# --- Feature: Get 24h Volume and Compare to 7d Average ---
async def detect_volume_spikes():
    spikes = []
    url = f"{COINGECKO_API}/coins/markets?vs_currency=usd&order=volume_desc&per_page=50&page=1"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            try:
                coins = await resp.json()
            except Exception as e:
                return [f"Error parsing CoinGecko response: {e}"]

            if isinstance(coins, dict) and "error" in coins:
                return [f"CoinGecko error: {coins['error']}"]

            for coin in coins:
                if not isinstance(coin, dict) or "id" not in coin:
                    continue

                coin_id = coin["id"]
                try:
                    hist_url = f"{COINGECKO_API}/coins/{coin_id}/market_chart?vs_currency=usd&days=7"
                    async with session.get(hist_url) as hist_resp:
                        hist_data = await hist_resp.json()
                        volumes = [v[1] for v in hist_data.get("total_volumes", [])]
                        if not volumes:
                            continue

                        avg_vol = sum(volumes) / len(volumes)
                        if coin.get("total_volume", 0) > avg_vol * VOLUME_SPIKE_THRESHOLD:
                            spikes.append(
                                f"🚨 {coin['name']} ({coin['symbol'].upper()}) - 24h Vol: ${coin['total_volume']:,.0f}"
                            )
                except Exception:
                    continue
    return spikes

# --- Feature: Scrape X.com for /gem command ---
async def search_x_for_gems():
    query = "(%23100x OR %23gem OR %23microcap OR %23degen) lang:en"
    headers = {"Authorization": f"Bearer {TWITTER_BEARER_TOKEN}"}
    url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&tweet.fields=public_metrics&max_results=50"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            tweets = (await resp.json()).get("data", [])
            gems = []
            for tweet in tweets:
                text = tweet["text"]
                if re.search(r"\\$[A-Z]{2,10}", text):
                    symbol = re.findall(r"\\$[A-Z]{2,10}", text)[0]
                    engagement = tweet["public_metrics"]
                    if engagement["retweet_count"] + engagement["like_count"] > 30:
                        gems.append(f"🔥 {symbol} - {text[:80]}...")
            return gems[:5]

# --- Telegram Command: /gem ---
async def gem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text("🔍 Scanning X.com for gem tokens...")

        print("🧪 /gem triggered")

        gems = await search_x_for_gems()
        print(f"🪙 Gems found: {gems}")

        spikes = await detect_volume_spikes()
        print(f"📈 Volume spikes found: {spikes}")

        if not gems and not spikes:
            await update.message.reply_text("🤷 No promising tokens found right now. Try again later.")
            return

        message_parts = []
        if gems:
            message_parts.append("🔥 Gem Candidates from X.com:\n" + "\n".join(gems))
        if spikes:
            message_parts.append("\n📈 Volume Spikes:\n" + "\n".join(spikes))

        await update.message.reply_text("\n\n".join(message_parts))

    except Exception as e:
        error_msg = f"⚠️ Error during /gem:\n{e}"
        print(error_msg)
        await update.message.reply_text(error_msg)

# --- Telegram Command: /alerts ---
async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    spikes = await detect_volume_spikes()
    await update.message.reply_text("\n".join(spikes) or "No volume spikes detected.")

# --- Telegram Command: /dextools ---
async def dextools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pairs = await get_dextools_trending()
    await update.message.reply_text("🔥 Trending Pairs:\n" + "\n".join(pairs))

# --- Schedule Volume Spike Alert to Channel ---
async def volume_spike_alert_job(app):
    spikes = await detect_volume_spikes()
    if spikes:
        await app.bot.send_message(chat_id=CHANNEL_ID, text="\n".join(["📡 Volume Spike Alert"] + spikes))

# --- Webhook Entry Point ---
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("gem", gem))
    app.add_handler(CommandHandler("alerts", alerts))
    app.add_handler(CommandHandler("dextools", dextools))

    job_queue = app.job_queue
    job_queue.run_repeating(lambda ctx: volume_spike_alert_job(app), interval=600, first=10)

    await app.bot.set_webhook(WEBHOOK_URL)
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),
        webhook_url=WEBHOOK_URL
    )

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    import asyncio
    asyncio.get_event_loop().run_until_complete(main())
