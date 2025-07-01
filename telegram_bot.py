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

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TWITTER_BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
COINGECKO_API = os.getenv("COINGECKO_API", "https://api.coingecko.com/api/v3")
DEXTOOLS_BASE = os.getenv("DEXTOOLS_BASE", "https://www.dextools.io")
CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")
VOLUME_SPIKE_THRESHOLD = float(os.getenv("VOLUME_SPIKE_THRESHOLD", 2.5))

nest_asyncio.apply()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("LassieX")

# --- Feature: Get Trending Pairs from DexTools ---
async def get_trending_from_geckoterminal():
    url = "https://api.geckoterminal.com/api/v2/networks/eth/trending_pools"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return [f"❌ GeckoTerminal error: {resp.status}"]
                data = await resp.json()
                trending = []

                for item in data.get("data", [])[:5]:
                    attr = item["attributes"]
                    symbol = attr["base_token"]["symbol"]
                    name = attr["base_token"]["name"]
                    link = f"https://www.geckoterminal.com/eth/pools/{item['id'].split('_')[-1]}"
                    trending.append(f"🔹 {name} ({symbol}) - [Pool]({link})")
                return trending or ["❌ No trending tokens found."]
    except Exception as e:
        return [f"❌ Error fetching from GeckoTerminal: {e}"]


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
    url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&tweet.fields=public_metrics,author_id&expansions=author_id&user.fields=username&max_results=50"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            result = await resp.json()
            tweets = result.get("data", [])
            users = {u["id"]: u["username"] for u in result.get("includes", {}).get("users", [])}

            gems = []
            for tweet in tweets:
                text = tweet["text"]
                metrics = tweet["public_metrics"]
                username = users.get(tweet["author_id"], "unknown")

                engagement = metrics["like_count"] + metrics["retweet_count"]
                if engagement < 30:
                    continue

                symbols = re.findall(r"\$[A-Z]{2,10}", text)
                cas = re.findall(r"0x[a-fA-F0-9]{40}", text)
                tweet_url = f"https://x.com/{username}/status/{tweet['id']}"

                if symbols:
                    sym = symbols[0]
                    ca_part = f"\nCA: `{cas[0]}`" if cas else ""
                    gems.append(f"🔥 {sym} — {text[:80]}...\n🔗 [Tweet]({tweet_url}){ca_part}")

            return gems[:5]

# --- Telegram Command: /gem ---
async def gem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info("Received /gem command")
    try:
        gems = await search_x_for_gems()
        if not gems:
            gems = ["No fresh gems from X.com right now."]
        spikes = await detect_volume_spikes()
        message = "\n".join(gems + ["\n📈 Volume Spikes:"] + spikes if spikes else gems)
        await update.message.reply_text(message, disable_web_page_preview=True)
    except Exception as e:
        error_msg = f"⚠️ Error during /gem:\n{e}"
        logger.error(error_msg)
        await update.message.reply_text(error_msg)

# --- Telegram Command: /alerts ---
async def alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    spikes = await detect_volume_spikes()
    await update.message.reply_text("\n".join(spikes) or "No volume spikes detected.")

# --- Telegram Command: /dextools ---
async def dextools(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pairs = await get_dextools_trending()
    await update.message.reply_text("🔥 Trending Pairs:\n" + "\n".join(pairs))

# --- Telegram Command: /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to LassieX Bot!\n\n"
        "Use /gem to find fresh gem tokens from X.com\n"
        "Use /alerts to check real-time volume spikes\n"
        "Use /dextools for trending crypto pairs\n\n"
        "Stay degen. Stay early. 🚀"
    )

# --- Telegram Command: /help ---
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/gem - Find real-time gem tokens from X.com\n"
        "/alerts - Show tokens with volume spikes\n"
        "/dextools - Get trending pairs from DexTools\n"
        "/start - Welcome message\n"
        "/help - Show this help message"
    )

# --- Scheduled Job: Volume Spike Alerts to Channel ---
async def volume_spike_alert_job(app):
    spikes = await detect_volume_spikes()
    if spikes:
        await app.bot.send_message(chat_id=CHANNEL_ID, text="\n".join(["🛁 Volume Spike Alert"] + spikes))

# --- Webhook Entry Point ---
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register all bot commands
    app.add_handler(CommandHandler("gem", gem))
    app.add_handler(CommandHandler("alerts", alerts))
    app.add_handler(CommandHandler("dextools", dextools))
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("trending", trending))  # ✅ <-- Add it here

    # Schedule volume alert job
    app.job_queue.run_repeating(lambda ctx: volume_spike_alert_job(app), interval=600, first=10)

    # Set webhook
    await app.bot.set_webhook(url=WEBHOOK_URL + "/webhook")

    # Start the webhook server
    await app.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 10000)),
        webhook_url=WEBHOOK_URL + "/webhook"
    )

if __name__ == "__main__":
    asyncio.run(main())
