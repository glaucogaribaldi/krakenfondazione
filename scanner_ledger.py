import os
os.environ["KRAKEN_WORKSPACE"] = "fondazione-agentic-next"
import ccxt
import time
import json
import sqlite3
import logging

class UnifiedLedgerAndScanner:
    def __init__(self, db_path="/broker/storage/storage-next/db/nemotron.sqlite"):
        self.db_path = db_path
        self.kraken = ccxt.kraken()
        
    def get_active_run(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT run_id, initial_equity_eur, target_equity_eur, flattening_time FROM runs WHERE status = 'ACTIVE' LIMIT 1")
        row = c.fetchone()
        conn.close()
        return row
        
    def get_order_book_imbalance(self, symbol):
        try:
            kf = ccxt.krakenfutures()
            base = symbol.split('/')[0]
            if base == "BTC":
                base = "XBT"
            elif base == "MATIC":
                base = "POL"
            perp = f"PF_{base}USD"
            
            ob = kf.fetch_l2_order_book(perp, limit=5)
            bids = ob.get("bids", [])
            asks = ob.get("asks", [])
            
            total_bid_vol = sum(b[1] for b in bids)
            total_ask_vol = sum(a[1] for a in asks)
            
            if total_bid_vol + total_ask_vol > 0:
                imbalance = (total_bid_vol - total_ask_vol) / (total_bid_vol + total_ask_vol)
                return round(imbalance, 3)
            return 0.0
        except Exception:
            return 0.0

    def scan_opportunities(self):
        """Dynamic Discovery of Top 10 Active/Volatile Futures Perpetual Contracts with L2 Order Book Imbalance"""
        try:
            kf = ccxt.krakenfutures()
            tickers = kf.fetch_tickers()
            
            candidates = []
            for symbol, data in tickers.items():
                if symbol.endswith(':USD') and '/USD' in symbol:
                    base = symbol.split('/')[0]
                    if base in ["USDT", "USDC", "EUR", "USD", "SUSD"]:
                        continue
                    
                    candidates.append({
                        "symbol": f"{base}/EUR",
                        "price": data.get('last', 0),
                        "volume_usd": data.get('quoteVolume', 0),
                        "change_pct": data.get('percentage', 0)
                    })
            
            # Sort by absolute percentage change (volatility) and pick Top 10
            top_candidates = sorted(candidates, key=lambda x: abs(x.get('change_pct', 0)), reverse=True)[:10]
            
            # Calculate LOB imbalance for each of the top candidates
            for c in top_candidates:
                c["lob_imbalance"] = self.get_order_book_imbalance(c["symbol"])
                
            return top_candidates
        except Exception as e:
            print(f"Discovery Error: {e}")
            return []

    def get_unified_snapshot(self, current_paper_equity):
        run = self.get_active_run()
        if not run:
            return None
            
        run_id, initial, target, flat_time = run
        
        # Calculate target gaps
        current_pnl_eur = current_paper_equity - initial
        current_pnl_pct = (current_pnl_eur / initial) * 100 if initial > 0 else 0
        gap_to_target_eur = target - current_paper_equity
        
        time_remaining_sec = flat_time - time.time()
        time_remaining_hours = round(time_remaining_sec / 3600.0, 2)
        
        # Run Scanner
        top_opportunities = self.scan_opportunities()
        
        # Fetch RSS news sentiment
        try:
            import sys
            # Add storage-next to sys.path so we can import sentiment_rss
            if "/broker/storage/storage-next" not in sys.path:
                sys.path.append("/broker/storage/storage-next")
            import sentiment_rss
            news_sentiment = sentiment_rss.get_market_sentiment()
        except Exception as e:
            news_sentiment = {"score": 0.0, "reason": f"Errore caricamento sentiment locale: {e}", "headlines": []}
            
        snapshot = {
            "run_id": run_id,
            "unified_equity_eur": current_paper_equity,
            "mission_metrics": {
                "target_eur": target,
                "current_pnl_pct": round(current_pnl_pct, 2),
                "gap_to_target_eur": round(gap_to_target_eur, 2),
                "hours_to_flattening": time_remaining_hours
            },
            "news_sentiment": news_sentiment,
            "discovery_candidates": top_opportunities
        }
        return snapshot

if __name__ == "__main__":
    scanner = UnifiedLedgerAndScanner()
    # Mocking current paper equity as 295.00
    snap = scanner.get_unified_snapshot(295.00)
    print(json.dumps(snap, indent=2))
