import os
import pytz

# Timezone Configuration
TIMEZONE = pytz.timezone('Asia/Dhaka')

# Telegram Credentials (Fetched from GitHub Secrets)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# Supported OTC Pairs
OTC_PAIRS = [
    "EUR/USD OTC", "GBP/USD OTC", "USD/JPY OTC", "AUD/USD OTC",
    "EUR/GBP OTC", "USD/CAD OTC", "EUR/JPY OTC", "GBP/JPY OTC",
    "USD/CHF OTC", "AUD/CAD OTC", "NZD/USD OTC", "EUR/CAD OTC"
]

# Technical Thresholds for High Direct-Win Probability
MIN_PAYOUT = 85           # Payout percentage threshold
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
EMA_SHORT = 9
EMA_LONG = 21
ADX_MIN_STRENGTH = 25     # Rejects sideways/noisy markets
MAX_WICK_RATIO = 0.35     # Rejects volatile candles with long wicks
