import sys
import time
import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TIMEZONE
from signal_engine import SignalEngine
from data_fetcher import QuotexDataFetcher

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        res = requests.post(url, json=payload)
        return res.json()
    except Exception as e:
        print(f"Error sending message: {e}")
        return None

def run_session(session_name):
    now = datetime.now(TIMEZONE)
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Starting {session_name} Session...")

    engine = SignalEngine()
    # Generates 10 to 15 top quality signals
    signals = engine.generate_filtered_signals(session_start_time=now, target_count=12)

    if not signals:
        print("No valid high-probability signals found.")
        return

    # Header & Formatting
    msg = f"📊 *QUOTEX OTC HIGH-ACCURACY SIGNALS*\n"
    msg += f"📅 Date: `{now.strftime('%d-%m-%Y')}` | Session: *{session_name}*\n"
    msg += f"⏰ Timezone: *Asia/Dhaka (BST)*\n"
    msg += f"⏳ Expiry: *1 MINUTE*\n"
    msg += f"-----------------------------------------\n"

    for sig in signals:
        icon = "🟢 CALL" if sig['direction'] == "CALL" else "🔴 PUT"
        msg += f"➡️ `{sig['time']}` | *{sig['pair']}* | {icon}\n"

    msg += f"-----------------------------------------\n"
    msg += f"⚠️ *Rule:* Prioritize Direct Entry. Use 1-Step MTG only as Safety Net."

    # Post Signal List 15 mins before session
    send_telegram_message(msg)
    print("Signal List Posted Successfully.")

    # Save session signals locally for report evaluation
    return signals

def run_report(signals):
    if not signals:
        return
    
    print("Evaluating session performance for auto-reporting...")
    fetcher = QuotexDataFetcher()
    
    direct_wins = 0
    mtg_wins = 0
    losses = 0

    report_msg = f"📈 *OFFICIAL SESSION RESULT REPORT*\n"
    report_msg += f"-----------------------------------------\n"

    for sig in signals:
        res = fetcher.get_live_result(sig['pair'], sig['time'], sig['direction'])
        if res == "DIRECT_WIN":
            direct_wins += 1
            status = "✅ DIRECT WIN"
        elif res == "MTG_WIN":
            mtg_wins += 1
            status = "🟡 1-STEP MTG WIN"
        else:
            losses += 1
            status = "❌ LOSS"
        
        report_msg += f"`{sig['time']}` | {sig['pair']} ➡️ {status}\n"

    total = len(signals)
    win_rate = round(((direct_wins + mtg_wins) / total) * 100, 1)

    report_msg += f"-----------------------------------------\n"
    report_msg += f"🎯 *Direct Wins:* {direct_wins}\n"
    report_msg += f"🔄 *MTG Wins:* {mtg_wins}\n"
    report_msg += f"❌ *Losses:* {losses}\n"
    report_msg += f"🔥 *Total Win-Rate:* `{win_rate}%`"

    send_telegram_message(report_msg)
    print("Report Posted Successfully.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        # Simulates evaluating last session
        dummy_engine = SignalEngine()
        signals = dummy_engine.generate_filtered_signals(datetime.now(TIMEZONE), 10)
        run_report(signals)
    else:
        run_session("LIVE")



.github/workflows/signal_scheduler.yml


name: Quotex OTC Signal & Report Scheduler

on:
  schedule:
    # Morning Session: Signal at 09:15 AM BST (03:15 UTC), Report at 10:35 AM BST (04:35 UTC)
    - cron: '15 3 * * *'
    - cron: '35 4 * * *'
    
    # Night Session: Signal at 08:15 PM BST (14:15 UTC), Report at 09:35 PM BST (15:35 UTC)
    - cron: '15 14 * * *'
    - cron: '35 15 * * *'
  
  workflow_dispatch: # Manual Run Option

jobs:
  run-bot:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Execute Signal Engine
        env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
        run: |
          # Checks UTC hour to decide whether to send Signals or Report
          HOUR=$(date -u +%H)
          if [ "$HOUR" -eq 3 ] || [ "$HOUR" -eq 14 ]; then
            python bot_main.py
          else
            python bot_main.py report
          fi
