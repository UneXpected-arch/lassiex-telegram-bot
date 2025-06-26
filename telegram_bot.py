from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests
import os
import json
from datetime import time as dtime
import random
from load_env import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL", "https://lassiex-backend.up.railway.app/predict")
SUBSCRIBERS_FILE = "subscribers.json"

LASSIEX_MESSAGES = [
    "🐶 LassieX sniffs out rugs before you get rekt!",
    "📉 Meme coins go down, but LassieX sees it coming.",
    "🚨 AI BUY SIGNAL ACTIVE — powered by loyalty.",
    "💡 Smarter trading starts with LassieX.ai",
    "🤖 $LASSIE: Not just a meme. An intelligent companion.",
    "🔎 Lassie is scanning... Alpha incoming!"
]

def load_subscribers():
    if not os.path.exists(SUBSCRIBERS_FILE):
        return {}
    with open(SUBSCRIBERS_FILE, "r") as f:
        return json.load(f)

def save_subscribers(subs):
    with open(SUBSCRIBERS_FILE, "w") as f:
        json.dump(subs, f)

def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🐕 Welcome to LassieX Bot!\n"
        "Type /predict BTC to get the latest AI crypto insight.\n"
        "Use /subscribe BTC to get daily updates.\n"
        "Use /unsubscribe to stop them."
    )

def predict(update: Update, context: CallbackContext):
    if not context.args:
        update.message.reply_text("Please provide a coin symbol. Example: /predict BTC")
        return

    symbol = context.args[0].upper() + "-USD"
    try:
        response = requests.post(API_URL, json={"symbol": symbol, "days_back": 7})
        data = response.json()
        msg = (
            f"📊 *{data['symbol']} Prediction:*\n"
            f"🔹 Price: ${data['latest_price']}\n"
            f"📈 Trend: {data['trend_prediction']}\n"
            f"🧠 Sentiment: {data['social_sentiment']}\n"
            f"💬 Tweets analyzed: {data['tweet_sample_size']}"
        )
        update.message.reply_text(msg, parse_mode="Markdown")
    except Exception as e:
        update.message.reply_text(f"⚠️ Error fetching data: {e}")

def subscribe(update: Update, context: CallbackContext):
    user_id = str(update.effective_chat.id)
    symbol = context.args[0].upper() + "-USD" if context.args else "BTC-USD"
    subs = load_subscribers()
    subs[user_id] = symbol
    save_subscribers(subs)
    update.message.reply_text(f"✅ Subscribed! You'll get daily LassieX updates for {symbol}.")

def unsubscribe(update: Update, context: CallbackContext):
    user_id = str(update.effective_chat.id)
    subs = load_subscribers()
    if user_id in subs:
        del subs[user_id]
        save_subscribers(subs)
        update.message.reply_text("❌ Unsubscribed from daily updates.")
    else:
        update.message.reply_text("You're not subscribed.")

def send_daily(context: CallbackContext):
    subs = load_subscribers()
    for user_id, symbol in subs.items():
        try:
            response = requests.post(API_URL, json={"symbol": symbol, "days_back": 7})
            data = response.json()
            msg = (
                f"{random.choice(LASSIEX_MESSAGES)}\n\n"
                f"📊 Daily Update: {data['symbol']}\n"
                f"🔹 Price: ${data['latest_price']}\n"
                f"📈 Trend: {data['trend_prediction']}\n"
                f"🧠 Sentiment: {data['social_sentiment']}\n"
                f"💬 Tweets analyzed: {data['tweet_sample_size']}\n\n"
                f"👉 Join the Pack: https://lassiex.ai"
            )
            context.bot.send_message(chat_id=int(user_id), text=msg)
        except Exception as e:
            print(f"Error sending to {user_id}: {e}")

def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("predict", predict))
    dp.add_handler(CommandHandler("subscribe", subscribe))
    dp.add_handler(CommandHandler("unsubscribe", unsubscribe))
    updater.job_queue.run_daily(send_daily, time=dtime(hour=9))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
