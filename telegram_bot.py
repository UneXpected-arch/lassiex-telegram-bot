import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes
)
from flask import Flask, request

# Telegram bot token and webhook domain from environment
7949461968:AAHRt77aCJ_5xBAckfK1LWDw8JZ4sU7Jam8 = os.getenv("7949461968:AAHRt77aCJ_5xBAckfK1LWDw8JZ4sU7Jam8")
https://lassiex-telegram-bot-1i6z.onrender.com = os.getenv("https://lassiex-telegram-bot-1i6z.onrender.com")  # e.g. https://your-app.onrender.com

# Create Flask app
flask_app = Flask(__name__)
telegram_app = ApplicationBuilder().token(7949461968:AAHRt77aCJ_5xBAckfK1LWDw8JZ4sU7Jam8).build()

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome to LassieX — sniffing alpha in real-time!")

telegram_app.add_handler(CommandHandler("start", start))

# Flask route for Telegram webhook
@flask_app.post("/webhook")
async def webhook():
    if request.method == "POST":
        await telegram_app.update_queue.put(Update.de_json(request.json, telegram_app.bot))
        return "OK"

# Set webhook on startup
@flask_app.before_first_request
def set_webhook():
    webhook_url = f"{https://lassiex-telegram-bot-1i6z.onrender.com}/webhook"
    telegram_app.bot.set_webhook(url=webhook_url)

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))