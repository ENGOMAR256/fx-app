from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import yfinance as yf
import pandas as pd
import os
import time

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Expanded Markets
MARKETS = {
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "JPY=X", 
    "AUDUSD": "AUDUSD=X", "USDCAD": "CAD=X", "NZDUSD": "NZDUSD=X",
    "BTCUSD": "BTC-USD", "ETHUSD": "ETH-USD", "SOLUSD": "SOL-USD",
    "NAS100": "^NDX", "US30": "^DJI", "SPX500": "^GSPC",
    "XAUUSD": "GC=F", "XAGUSD": "SI=F", "USOIL": "CL=F"
}

TIMEFRAMES = ["15m", "1h", "4h"]

class Setup(BaseModel):
    timeframe: str
    direction: str
    entry: float
    stopLoss: float
    takeProfit: float
    rsi: float

class Signal(BaseModel):
    pair: str
    setups: List[Setup]

def get_setup(pair, symbol, tf):
    try:
        df = yf.Ticker(symbol).history(period="5d", interval=tf)
        if df.empty: return None
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_price = float(df['Close'].iloc[-1])
        current_rsi = float(rsi.iloc[-1])
        atr = float((df['High'] - df['Low']).rolling(14).mean().iloc[-1])
        
        # Determine decimals based on price
        decimals = 5 if current_price < 10 else 2
        
        if current_rsi < 30:
            return Setup(
                timeframe=tf.upper(), direction="BUY", 
                entry=round(current_price, decimals),
                stopLoss=round(current_price - (atr * 1.5), decimals),
                takeProfit=round(current_price + (atr * 3), decimals),
                rsi=round(current_rsi, 1)
            )
        elif current_rsi > 70:
            return Setup(
                timeframe=tf.upper(), direction="SELL", 
                entry=round(current_price, decimals),
                stopLoss=round(current_price + (atr * 1.5), decimals),
                takeProfit=round(current_price - (atr * 3), decimals),
                rsi=round(current_rsi, 1)
            )
        return None
    except:
        return None

@app.get("/signals")
def get_signals():
    final_signals = []
    
    for pair, symbol in MARKETS.items():
        pair_setups = []
        for tf in TIMEFRAMES:
            setup = get_setup(pair, symbol, tf)
            if setup:
                pair_setups.append(setup)
            time.sleep(0.1) # Prevent rate limits
            
        if pair_setups:
            final_signals.append(Signal(pair=pair, setups=pair_setups))
            
    return final_signals

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
