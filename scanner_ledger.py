import ccxt
import time
import json
import sqlite3

class UnifiedLedgerAndScanner:
    def __init__(self, db_path="/broker/storage/db/nemotron.sqlite"):
        self.db_path = db_path
        self.kraken = ccxt.kraken()
        
    def get_active_run(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT run_id, initial_equity_eur, target_equity_eur, flattening_time FROM runs WHERE status = 'ACTIVE' LIMIT 1")
        row = c.fetchone()
        conn.close()
        return row
        
    def scan_opportunities(self):
        """Dynamic Discovery of Top 10 Active/Volatile Futures Perpetual Contracts"""
        try:
            kf = ccxt.krakenfutures()
            tickers = kf.fetch_tickers()
            
            candidates = []
            for symbol, data in tickers.items():
                # Filter for linear perpetual contracts ending with ':USD'
                if symbol.endswith(':USD') and '/USD' in symbol:
                    base = symbol.split('/')[0]
                    # Filter out stablecoins
                    if base in ["USDT", "USDC", "EUR", "USD", "SUSD"]:
                        continue
                    
                    # Convert price and volume to EUR if possible, or just pass USD
                    # Since we are trading EUR, let's keep it clean
                    candidates.append({
                        "symbol": f"{base}/EUR", # Represent as /EUR so Nemotron understands it
                        "price": data.get('last', 0),
                        "volume_usd": data.get('quoteVolume', 0),
                        "change_pct": data.get('percentage', 0)
                    })
            
            # Sort by absolute percentage change (volatility) and pick Top 10
            top_candidates = sorted(candidates, key=lambda x: abs(x.get('change_pct', 0)), reverse=True)[:10]
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
        
        snapshot = {
            "run_id": run_id,
            "unified_equity_eur": current_paper_equity,
            "mission_metrics": {
                "target_eur": target,
                "current_pnl_pct": round(current_pnl_pct, 2),
                "gap_to_target_eur": round(gap_to_target_eur, 2),
                "hours_to_flattening": time_remaining_hours
            },
            "discovery_candidates": top_opportunities
        }
        return snapshot

if __name__ == "__main__":
    scanner = UnifiedLedgerAndScanner()
    # Mocking current paper equity as 295.00
    snap = scanner.get_unified_snapshot(295.00)
    print(json.dumps(snap, indent=2))
