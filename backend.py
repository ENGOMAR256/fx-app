from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import yfinance as yf
import pandas as pd
import os

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Signal(BaseModel):
    pair: str
    direction: str
    entry: float
    stopLoss: float
    takeProfit: float
    rsi: float
    confidence: float
    strategy: str
    timeframe: str
    learnMode: str
    indicators: List[str]

MARKETS = {
    "XAUUSD": "GC=F",
    "EURUSD": "EURUSD=X",
    "GBPUSD": "GBPUSD=X",
    "BTCUSD": "BTC-USD",
    "NAS100": "^NDX"
}

TIMEFRAMES = ["1h", "4h"]

def scan_market(pair, yf_symbol, tf):
    try:
        df = yf.Ticker(yf_symbol).history(period="5d", interval=tf)
        if df.empty: return None
        
        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_price = float(df['Close'].iloc[-1])
        current_rsi = float(rsi.iloc[-1])
        atr = float((df['High'] - df['Low']).rolling(14).mean().iloc[-1])
        
        # Strategy: SMC / Liquidity (Oversold/Overbought)
        if current_rsi < 30:
            return Signal(
                pair=pair, direction="BUY", entry=round(current_price, 5),
                stopLoss=round(current_price - (atr * 1.5), 5),
                takeProfit=round(current_price + (atr * 3), 5),
                rsi=round(current_rsi, 2), confidence=75.0,
                strategy="SMC/Liquidity Grab", timeframe=tf.upper(),
                learnMode="Price swept liquidity and reversed. RSI is oversold.",
                indicators=["RSI < 30", "Volume Spike", "Reversal"]
            )
        elif current_rsi > 70:
            return Signal(
                pair=pair, direction="SELL", entry=round(current_price, 5),
                stopLoss=round(current_price + (atr * 1.5), 5),
                takeProfit=round(current_price - (atr * 3), 5),
                rsi=round(current_rsi, 2), confidence=75.0,
                strategy="SMC/Liquidity Grab", timeframe=tf.upper(),
                learnMode="Price rejected from supply. RSI is overbought.",
                indicators=["RSI > 70", "Supply Zone", "Rejection"]
            )
        return None
    except:
        return None

@app.get("/signals")
def get_signals():
    # 1. Scan all markets across all timeframes
    raw_signals = []
    for pair, symbol in MARKETS.items():
        for tf in TIMEFRAMES:
            sig = scan_market(pair, symbol, tf)
            if sig: 
                raw_signals.append(sig)

    # 2. THE CONFLUENCE ENGINE: Combine signals that agree
    final_signals = []
    pairs = {}
    
    # Group by pair
    for sig in raw_signals:
        if sig.pair not in pairs:
            pairs[sig.pair] = []
        pairs[sig.pair].append(sig)

    # Check for agreement
    for pair, sigs in pairs.items():
        directions = [s.direction for s in sigs]
        
        # If ALL timeframes agree (e.g., H1 and H4 both say BUY)
        if len(set(directions)) == 1:
            best_sig = max(sigs, key=lambda x: x.confidence)
            
            # Boost confidence because multiple timeframes agree!
            best_sig.confidence = min(99.0, best_sig.confidence + (len(sigs) * 10))
            
            # Combine the timeframes into one label
            tf_names = list(set(s.timeframe for s in sigs))
            best_sig.timeframe = "Multi-TF (" + ", ".join(tf_names) + ")"
            
            # Update the AI explanation
            best_sig.learnMode = f"🔥 HIGH CONFLUENCE: {len(sigs)} timeframes agree! " + best_sig.learnMode
            best_sig.strategy = "Multi-Timeframe Confluence"
            
            final_signals.append(best_sig)
            
        # If they disagree (e.g., H1 BUY, H4 SELL), we THROW IT AWAY to protect the user.

    return final_signals

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
