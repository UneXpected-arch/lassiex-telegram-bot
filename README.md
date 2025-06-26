# LassieX Telegram Bot 🤖🐶

A smart Telegram bot powered by LassieX AI to deliver real-time crypto predictions, sentiment analysis, and daily updates for subscribers.

## Features
- `/predict BTC` – Get real-time prediction, sentiment & trend
- `/subscribe ETH` – Daily updates for a selected coin
- `/unsubscribe` – Stop updates anytime
- Auto-sends LassieX marketing messages + call-to-actions

## Setup

1. **Clone the repo**:
```bash
git clone https://github.com/yourusername/lassiex-telegram-bot.git
cd lassiex-telegram-bot
```

2. **Create `.env` file**:
```
BOT_TOKEN=your_telegram_token
TWITTER_BEARER_TOKEN=your_twitter_api_token
API_URL=https://your-deployed-backend.onrender.com/predict
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Run the bot**:
```bash
python telegram_bot.py
```

## Deploying to Render

- Create a new **Background Worker** service
- Set Root Directory to this repo
- Add these environment variables:
  - `BOT_TOKEN`
  - `TWITTER_BEARER_TOKEN`
  - `API_URL`
- Use `Procfile` as the start command:  
  `worker: python telegram_bot.py`

---

Built for the LassieX AI crypto community 🧠🚀  
Learn more at [https://lassiex.ai](https://lassiex.ai)
