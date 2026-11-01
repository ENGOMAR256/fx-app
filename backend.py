from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
import yfinance as yf
import pandas as pd
import os
import time
from datetime import datetime, timedelta

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Expanded Markets
MARKETS = {
    # Forex
    "EURUSD": "EURUSD=X", "GBPUSD": "GBPUSD=X", "USDJPY": "JPY=X", 
    "AUDUSD": "AUDUSD=X", "USDCAD": "CAD=X", "NZDUSD": "NZDUSD=X",
    # Crypto
    "BTCUSD": "BTC-USD", "ETHUSD": "ETH-USD", "SOLUSD": "SOL-USD",
    # Indices
    "NAS100": "^NDX", "US30": "^DJI", "SPX500": "^GSPC",
    # Commodities
    "XAUUSD": "GC=F", "XAGUSD": "SI=F", "USOIL": "CL=F"
}

TIMEFRAMES = ["15m", "1h", "4h"]

class TimeframeSetup(BaseModel):
    timeframe: str
    direction: str
    rsi: float

class Signal(BaseModel):
    pair: str
    main_direction: str
    entry: float
    stopLoss: float
    takeProfit: float
    strategy: str
    setups: List[TimeframeSetup]
    created_at: str
    expires_at: str
    learnMode: str

def get_signal(pair, symbol, tf):
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
        
        if current_rsi < 30:
            return {"tf": tf.upper(), "dir": "BUY", "rsi": round(current_rsi, 1), "price": current_price, "atr": atr}
        elif current_rsi > 70:
            return {"tf": tf.upper(), "dir": "SELL", "rsi": round(current_rsi, 1), "price": current_price, "atr": atr}
        return None
    except:
        return None

@app.get("/signals")
def get_signals():
    raw_signals = {}
    
    # 1. Scan all markets
    for pair, symbol in MARKETS.items():
        pair_setups = []
        for tf in TIMEFRAMES:
            res = get_signal(pair, symbol, tf)
            if res:
                pair_setups.append(res)
            time.sleep(0.1) # Prevent rate limits
            
        if pair_setups:
            raw_signals[pair] = pair_setups

    # 2. Group and Format
    final_signals = []
    now = datetime.utcnow()
    expire_time = now + timedelta(minutes=15) # 15 Minute Expiration
    
    for pair, setups in raw_signals.items():
        # Find the most common direction
        directions = [s['dir'] for s in setups]
        main_dir = max(set(directions), key=directions.count)
        
        # Use the H1 or H4 price for the main entry
        main_setup = next((s for s in setups if s['tf'] in ['1H', '4H']), setups[0])
        price = main_setup['price']
        atr = main_setup['atr']
        
        sl = round(price - (atr * 1.5), 5) if main_dir == "BUY" else round(price + (atr * 1.5), 5)
        tp = round(price + (atr * 3), 5) if main_dir == "BUY" else round(price - (atr * 3), 5)
        
        # Format setups for the UI
        tf_list = [TimeframeSetup(timeframe=s['tf'], direction=s['dir'], rsi=s['rsi']) for s in setups]
        
        final_signals.append(Signal(
            pair=pair,
            main_direction=main_dir,
            entry=round(price, 5),
            stopLoss=sl,
            takeProfit=tp,
            strategy="Multi-Timeframe Confluence",
            setups=tf_list,
            created_at=now.strftime("%H:%M:%S"),
            expires_at=expire_time.strftime("%H:%M:%S"),
            learnMode=f"Confluence detected across {len(setups)} timeframes. Main trend is {main_dir}."
        ))
        
    return final_signals

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
