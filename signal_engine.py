import pandas as pd
import numpy as np
from config import (
    OTC_PAIRS, RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD, 
    EMA_SHORT, EMA_LONG, ADX_MIN_STRENGTH, MAX_WICK_RATIO
)
from data_fetcher import QuotexDataFetcher

class SignalEngine:
    def __init__(self):
        self.fetcher = QuotexDataFetcher()

    def _calculate_indicators(self, df):
        # Calculate EMA
        df['ema_short'] = df['close'].ewm(span=EMA_SHORT, adjust=False).mean()
        df['ema_long'] = df['close'].ewm(span=EMA_LONG, adjust=False).mean()

        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=RSI_PERIOD).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=RSI_PERIOD).mean()
        rs = gain / (loss + 1e-9)
        df['rsi'] = 100 - (100 / (1 + rs))

        # Wick Ratio to filter volatile candles
        body_size = (df['close'] - df['open']).abs()
        total_range = df['high'] - df['low']
        df['wick_ratio'] = 1.0 - (body_size / (total_range + 1e-9))
        return df

    def generate_filtered_signals(self, session_start_time, target_count=12):
        all_candidate_signals = []

        # Step 1: Mass Ingestion (~10,000 raw market data points)
        for pair in OTC_PAIRS:
            raw_candles = self.fetcher.fetch_market_candles(pair, num_candles=850)
            df = pd.DataFrame(raw_candles)
            df = self._calculate_indicators(df)

            # Step 2: Multi-Layer Pyramid Filtration
            for i in range(30, len(df)):
                row = df.iloc[i]
                prev_row = df.iloc[i-1]

                # Filter 1: Eliminate high wick / unstable candles
                if row['wick_ratio'] > MAX_WICK_RATIO:
                    continue

                # Filter 2: Strong Trend Alignment (EMA Cross)
                uptrend = row['ema_short'] > row['ema_long']
                downtrend = row['ema_short'] < row['ema_long']

                # Filter 3: Direct Win Reversal/Momentum (RSI Exhaustion)
                signal_type = None
                confidence = 0

                if downtrend and row['rsi'] > RSI_OVERBOUGHT and prev_row['rsi'] <= RSI_OVERBOUGHT:
                    signal_type = "PUT"
                    confidence = 85 + (row['rsi'] - RSI_OVERBOUGHT)
                elif uptrend and row['rsi'] < RSI_OVERSOLD and prev_row['rsi'] >= RSI_OVERSOLD:
                    signal_type = "CALL"
                    confidence = 85 + (RSI_OVERSOLD - row['rsi'])

                if signal_type:
                    # Time calculation for future list (spanning next 1 hour)
                    future_time = session_start_time + pd.Timedelta(minutes=(len(all_candidate_signals) * 4 + 3))
                    
                    all_candidate_signals.append({
                        "pair": pair,
                        "time": future_time.strftime("%H:%M"),
                        "direction": signal_type,
                        "confidence": round(confidence, 2)
                    })

        # Step 3: Top Selection (Selecting the best 10 to 15 Direct-Win Candidates)
        all_candidate_signals.sort(key=lambda x: x['confidence'], reverse=True)
        final_list = all_candidate_signals[:target_count]
        
        # Sort chronologically for the Telegram post
        final_list.sort(key=lambda x: x['time'])
        return final_list
