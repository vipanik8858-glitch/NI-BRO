import sys
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
    signals = engine.generate_filtered_signals(session_start_time=now, target_count=10)

    is_otc = engine.is_otc_market(now)
    market_type = "OTC MARKET" if is_otc else "REAL MARKET"

    msg = f"📊 *QUOTEX {market_type} HIGH-ACCURACY SIGNALS*\n"
    msg += f"📅 Date: `{now.strftime('%d-%m-%Y')}` | Session: *{session_name}*\n"
    msg += f"⏰ Timezone: *Asia/Dhaka (BST)*\n"
    msg += f"⏳ Expiry: *1 MINUTE*\n"
    msg += f"-----------------------------------------\n"

    for sig in signals:
        icon = "🟢 CALL" if sig['direction'] == "CALL" else "🔴 PUT"
        msg += f"➡️ `{sig['time']}` | *{sig['pair']}* | {icon}\n"

    msg += f"-----------------------------------------\n"
    msg += f"⚠️ *Rule:* Prioritize Direct Entry. Use 1-Step MTG only as Safety Net."

    send_telegram_message(msg)
    print("Signal List Posted Successfully.")

def run_report():
    engine = SignalEngine()
    signals = engine.load_saved_signals()
    
    if not signals:
        print("No saved signals found for reporting.")
        return

    print("Evaluating saved session performance for auto-reporting...")
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
        run_report()
    else:
        run_session("LIVE")
