import os
import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, ContextTypes, CommandHandler,
    MessageHandler, filters
)
from telegram.ext.webhook import WebhookServer
import requests

# Load environment variables
BOT_TOKEN = os.getenv("7949461968:AAHRt77aCJ_5xBAckfK1LWDw8JZ4sU7Jam8")
API_URL = os.getenv("API_URL", "https://dummy-url.com")
WEBHOOK_URL = os.getenv("https://lassiex-telegram-bot-1i6z.onrender.com/webhook")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to the LassieX Bot! Sniffing alpha in real-time!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    try:
        if API_URL and "dummy" not in API_URL:
            response = requests.post(API_URL, json={"text": user_message}, timeout=5)
            result = response.json()
            sentiment = result.get("label", "unknown")
        else:
            sentiment = "neutral (mock)"

        await update.message.reply_text(f"Sentiment: {sentiment.capitalize()}")
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")
        await update.message.reply_text("Sorry, something went wrong while processing your message.")

async def setup_webhook(app):
    if WEBHOOK_URL:
        await app.bot.set_webhook(https://lassiex-telegram-bot-1i6z.onrender.com/webhook)
        logger.info(f"Webhook set to: {https://lassiex-telegram-bot-1i6z.onrender.com/webhook}")
    else:
        logger.warning("WEBHOOK_URL is not set. Webhook cannot be configured.")

def main():
    if not BOT_TOKEN:
        raise RuntimeError("7949461968:AAHRt77aCJ_5xBAckfK1LWDw8JZ4sU7Jam8 environment variable not set.")

    app = ApplicationBuilder().token(7949461968:AAHRt77aCJ_5xBAckfK1LWDw8JZ4sU7Jam8).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_webhook(
        listen="0.0.0.0",
        port=int(os.environ.get("PORT", 10000)),
        webhook_path="/webhook",
        on_startup=setup_webhook,
        stop_signals=None
    )

if __name__ == "__main__":
    main()
