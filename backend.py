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
    strategy_name: str
    strategy_logic: str

class Signal(BaseModel):
    pair: str
    setups: List[Setup]

def calculate_indicators(df):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    df['EMA_50'] = df['Close'].ewm(span=50, adjust=False).mean()
    df['EMA_200'] = df['Close'].ewm(span=200, adjust=False).mean()
    
    high_low = df['High'] - df['Low']
    high_close = (df['High'] - df['Close'].shift()).abs()
    low_close = (df['Low'] - df['Close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    df['ATR'] = tr.rolling(14).mean()
    
    df['Vol_SMA'] = df['Volume'].rolling(20).mean()
    df['High_20'] = df['High'].rolling(20).max()
    df['Low_20'] = df['Low'].rolling(20).min()
    
    # For Supply/Demand: Calculate average body size to find imbalances
    df['Body_Size'] = (df['Close'] - df['Open']).abs()
    df['Avg_Body'] = df['Body_Size'].rolling(20).mean()
    
    return df

def get_setups(pair, symbol, tf):
    try:
        df = yf.Ticker(symbol).history(period="3mo", interval=tf)
        if df.empty or len(df) < 200: return []
        
        df = calculate_indicators(df)
        
        last = df.iloc[-2] 
        prev = df.iloc[-3]
        
        current_rsi = last['RSI']
        current_price = last['Close']
        atr = last['ATR']
        decimals = 5 if current_price < 10 else 2
        
        setups = []
        
        # ==========================================
        # 1. SMC / Liquidity Grab
        # ==========================================
        if current_rsi < 30:
            setups.append(Setup(timeframe=tf.upper(), direction="BUY", entry=round(current_price, decimals),
                stopLoss=round(current_price - (atr * 1.5), decimals), takeProfit=round(current_price + (atr * 3), decimals),
                rsi=round(current_rsi, 1), strategy_name="SMC / Liquidity Grab",
                strategy_logic="RSI < 30. Price swept liquidity and is oversold. Expecting a sharp bounce."))
        elif current_rsi > 70:
            setups.append(Setup(timeframe=tf.upper(), direction="SELL", entry=round(current_price, decimals),
                stopLoss=round(current_price + (atr * 1.5), decimals), takeProfit=round(current_price - (atr * 3), decimals),
                rsi=round(current_rsi, 1), strategy_name="SMC / Liquidity Grab",
                strategy_logic="RSI > 70. Price rejected from supply and is overbought. Expecting a pullback."))

        # ==========================================
        # 2. Trend Following (EMA Pullback)
        # ==========================================
        if last['EMA_50'] > last['EMA_200'] and current_price > last['EMA_50'] and last['Low'] <= last['EMA_50'] * 1.002:
            setups.append(Setup(timeframe=tf.upper(), direction="BUY", entry=round(current_price, decimals),
                stopLoss=round(last['EMA_200'], decimals), takeProfit=round(current_price + (atr * 2), decimals),
                rsi=round(current_rsi, 1), strategy_name="Trend Following",
                strategy_logic="Strong Uptrend. Price pulled back to the 50 EMA dynamic support."))
        elif last['EMA_50'] < last['EMA_200'] and current_price < last['EMA_50'] and last['High'] >= last['EMA_50'] * 0.998:
            setups.append(Setup(timeframe=tf.upper(), direction="SELL", entry=round(current_price, decimals),
                stopLoss=round(last['EMA_200'], decimals), takeProfit=round(current_price - (atr * 2), decimals),
                rsi=round(current_rsi, 1), strategy_name="Trend Following",
                strategy_logic="Strong Downtrend. Price pulled back to the 50 EMA dynamic resistance."))

        # ==========================================
        # 3. Momentum Breakout
        # ==========================================
        if current_price > prev['High_20'] and last['Volume'] > last['Vol_SMA'] * 1.2:
            setups.append(Setup(timeframe=tf.upper(), direction="BUY", entry=round(current_price, decimals),
                stopLoss=round(current_price - (atr * 1.5), decimals), takeProfit=round(current_price + (atr * 3), decimals),
                rsi=round(current_rsi, 1), strategy_name="Momentum Breakout",
                strategy_logic="Price broke 20-period high with high volume. Strong bullish momentum."))
        elif current_price < prev['Low_20'] and last['Volume'] > last['Vol_SMA'] * 1.2:
            setups.append(Setup(timeframe=tf.upper(), direction="SELL", entry=round(current_price, decimals),
                stopLoss=round(current_price + (atr * 1.5), decimals), takeProfit=round(current_price - (atr * 3), decimals),
                rsi=round(current_rsi, 1), strategy_name="Momentum Breakout",
                strategy_logic="Price broke 20-period low with high volume. Strong bearish momentum."))

        # ==========================================
        # 4. Supply & Demand Zones (Imbalance Retest)
        # ==========================================
        # Bullish Demand Zone Retest
        if prev['Body_Size'] > prev['Avg_Body'] * 1.5 and prev['Close'] > prev['Open']:
            demand_zone_top = prev['Close']
            demand_zone_bottom = prev['Open']
            if current_price >= demand_zone_bottom and current_price <= demand_zone_top * 1.002:
                setups.append(Setup(timeframe=tf.upper(), direction="BUY", entry=round(current_price, decimals),
                    stopLoss=round(demand_zone_bottom - (atr * 0.5), decimals), takeProfit=round(current_price + (atr * 2.5), decimals),
                    rsi=round(current_rsi, 1), strategy_name="Supply & Demand",
                    strategy_logic="Price returned to a high-volume Demand Zone (imbalance). Expecting institutional buying."))
        # Bearish Supply Zone Retest
        elif prev['Body_Size'] > prev['Avg_Body'] * 1.5 and prev['Close'] < prev['Open']:
            supply_zone_bottom = prev['Close']
            supply_zone_top = prev['Open']
            if current_price <= supply_zone_top and current_price >= supply_zone_bottom * 0.998:
                setups.append(Setup(timeframe=tf.upper(), direction="SELL", entry=round(current_price, decimals),
                    stopLoss=round(supply_zone_top + (atr * 0.5), decimals), takeProfit=round(current_price - (atr * 2.5), decimals),
                    rsi=round(current_rsi, 1), strategy_name="Supply & Demand",
                    strategy_logic="Price returned to a high-volume Supply Zone (imbalance). Expecting institutional selling."))

        # ==========================================
        # 5. Support/Resistance Rejection
        # ==========================================
        # Resistance Rejection
        if last['High'] >= last['High_20'] and last['Close'] < last['High_20'] and last['High'] > last['Close']:
            setups.append(Setup(timeframe=tf.upper(), direction="SELL", entry=round(current_price, decimals),
                stopLoss=round(last['High'] + (atr * 0.5), decimals), takeProfit=round(current_price - (atr * 2), decimals),
                rsi=round(current_rsi, 1), strategy_name="S/R Rejection",
                strategy_logic="Price hit local Resistance (20-period high) and rejected. Sellers defending the level."))
        # Support Rejection
        elif last['Low'] <= last['Low_20'] and last['Close'] > last['Low_20'] and last['Low'] < last['Close']:
            setups.append(Setup(timeframe=tf.upper(), direction="BUY", entry=round(current_price, decimals),
                stopLoss=round(last['Low'] - (atr * 0.5), decimals), takeProfit=round(current_price + (atr * 2), decimals),
                rsi=round(current_rsi, 1), strategy_name="S/R Rejection",
                strategy_logic="Price hit local Support (20-period low) and rejected. Buyers defending the level."))

        # ==========================================
        # 6. Price Action (Pin Bar / Wick Rejection)
        # ==========================================
        candle_range = last['High'] - last['Low']
        if candle_range > 0:
            upper_wick = last['High'] - max(last['Open'], last['Close'])
            lower_wick = min(last['Open'], last['Close']) - last['Low']
            
            # Bullish Pin Bar (Long lower wick)
            if lower_wick > candle_range * 0.6 and last['Close'] > last['Open']:
                setups.append(Setup(timeframe=tf.upper(), direction="BUY", entry=round(current_price, decimals),
                    stopLoss=round(last['Low'] - (atr * 0.5), decimals), takeProfit=round(current_price + (atr * 2), decimals),
                    rsi=round(current_rsi, 1), strategy_name="Price Action (Pin Bar)",
                    strategy_logic="Bullish Pin Bar formed. Long lower wick shows strong buyer rejection at lower prices."))
            # Bearish Pin Bar (Long upper wick)
            elif upper_wick > candle_range * 0.6 and last['Close'] < last['Open']:
                setups.append(Setup(timeframe=tf.upper(), direction="SELL", entry=round(current_price, decimals),
                    stopLoss=round(last['High'] + (atr * 0.5), decimals), takeProfit=round(current_price - (atr * 2), decimals),
                    rsi=round(current_rsi, 1), strategy_name="Price Action (Pin Bar)",
                    strategy_logic="Bearish Pin Bar formed. Long upper wick shows strong seller rejection at higher prices."))

        return setups
    except Exception as e:
        print(f"Error scanning {pair} {tf}: {e}")
        return []

@app.get("/signals")
def get_signals():
    final_signals = []
    for pair, symbol in MARKETS.items():
        pair_setups = []
        for tf in TIMEFRAMES:
            setups = get_setups(pair, symbol, tf)
            pair_setups.extend(setups)
            time.sleep(0.2) 
        if pair_setups:
            final_signals.append(Signal(pair=pair, setups=pair_setups))
    return final_signals

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
