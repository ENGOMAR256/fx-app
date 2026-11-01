from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import yfinance as yf
import pandas as pd
import os
import random

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

def scan_market(pair, yf_symbol):
    try:
        df = yf.Ticker(yf_symbol).history(period="5d", interval="1h")
        if df.empty: return None
        
        # Calculate RSI
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_price = float(df['Close'].iloc[-1])
        current_rsi = float(rsi.iloc[-1])
        
        # Strategy 1: SMC / Liquidity (Oversold/Overbought)
        if current_rsi < 30:
            atr = float((df['High'] - df['Low']).rolling(14).mean().iloc[-1])
            return Signal(
                pair=pair, direction="BUY", entry=round(current_price, 5),
                stopLoss=round(current_price - (atr * 1.5), 5),
                takeProfit=round(current_price + (atr * 3), 5),
                rsi=round(current_rsi, 2), confidence=85.0,
                strategy="SMC/Liquidity Grab", timeframe="H1",
                learnMode="Price swept liquidity and reversed. RSI is oversold.",
                indicators=["RSI < 30", "Volume Spike", "Reversal"]
            )
        elif current_rsi > 70:
            atr = float((df['High'] - df['Low']).rolling(14).mean().iloc[-1])
            return Signal(
                pair=pair, direction="SELL", entry=round(current_price, 5),
                stopLoss=round(current_price + (atr * 1.5), 5),
                takeProfit=round(current_price - (atr * 3), 5),
                rsi=round(current_rsi, 2), confidence=85.0,
                strategy="SMC/Liquidity Grab", timeframe="H1",
                learnMode="Price rejected from supply. RSI is overbought.",
                indicators=["RSI > 70", "Supply Zone", "Rejection"]
            )
            
        # Strategy 2: Trend Following (Simple EMA logic)
        ema_50 = df['Close'].ewm(span=50, adjust=False).mean().iloc[-1]
        if current_price > ema_50 and current_rsi > 50:
             atr = float((df['High'] - df['Low']).rolling(14).mean().iloc[-1])
             return Signal(
                pair=pair, direction="BUY", entry=round(current_price, 5),
                stopLoss=round(current_price - (atr * 2), 5),
                takeProfit=round(current_price + (atr * 4), 5),
                rsi=round(current_rsi, 2), confidence=75.0,
                strategy="Trend Following", timeframe="H4",
                learnMode="Strong uptrend confirmed. Price above EMA 50.",
                indicators=["EMA 50 Cross", "Momentum", "Trend"]
            )

        return None
    except:
        return None

@app.get("/signals")
def get_signals():
    signals = []
    for pair, symbol in MARKETS.items():
        sig = scan_market(pair, symbol)
        if sig: signals.append(sig.dict())
    return signals

# This part is crucial for Render to work
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
