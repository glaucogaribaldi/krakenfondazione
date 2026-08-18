import ccxt
import time
import pandas as pd
import json
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

class MarketEngine:
    def __init__(self):
        self.exchange = ccxt.kraken()
        self.pairs = ['BTC/EUR', 'ETH/EUR', 'SOL/EUR', 'DOGE/EUR']
        self.last_state = {}
        
    def fetch_snapshot(self):
        tickers = self.exchange.fetch_tickers(self.pairs)
        snapshot = {}
        for pair, data in tickers.items():
            snapshot[pair] = {
                "price": data['last'],
                "vol_24h": data['quoteVolume']
            }
        return snapshot
        
    def detect_state_change(self, current_snapshot):
        if not self.last_state:
            self.last_state = current_snapshot
            return True, "INITIAL_BOOT"
            
        for pair, data in current_snapshot.items():
            last_price = self.last_state[pair]["price"]
            # Trigger on 1% price change
            if last_price and abs(data["price"] - last_price) / last_price > 0.01:
                return True, f"PRICE_DISPLACEMENT_{pair}"
                
        self.last_state = current_snapshot
        return False, "STABLE"

if __name__ == "__main__":
    engine = MarketEngine()
    snap = engine.fetch_snapshot()
    print("Snapshot fetched:", json.dumps(snap, indent=2))
    change, reason = engine.detect_state_change(snap)
    print("State Change:", change, "| Reason:", reason)
