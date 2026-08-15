import ccxt
import sqlite3
import json
import time
import uuid
import os
os.environ["KRAKEN_WORKSPACE"] = "fondazione-agentic-next"
import requests

DB_PATH = "/broker/storage/storage-next/db/nemotron.sqlite"
VAULT_PATH = "/broker/storage/storage-next/shared/config/api_vault.json"

def init_run_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY,
            start_time INTEGER,
            end_time INTEGER,
            flattening_time INTEGER,
            initial_equity_eur REAL,
            target_equity_eur REAL,
            intent JSON,
            status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_live_equity():
    try:
        with open(VAULT_PATH) as f:
            vault = json.load(f)
        
        # 1. Fetch Real Spot Balance
        spot = ccxt.kraken({
            'apiKey': vault['KRAKEN_PAPER_SPOT_KEY'],
            'secret': vault['KRAKEN_PAPER_SPOT_SECRET'],
        })
        spot_bal = spot.fetch_balance()
        spot_total = float(spot_bal.get('EUR', {}).get('total', 149.18))
        
        # 2. Fetch Real Futures Balance
        futures = ccxt.krakenfutures({
            'apiKey': vault['KRAKEN_PAPER_FUTURES_KEY'],
            'secret': vault['KRAKEN_PAPER_FUTURES_SECRET'],
        })
        fut_bal = futures.fetch_balance()
        fut_total = float(fut_bal.get('EUR', {}).get('total', 148.50))
        
        combined = spot_total + fut_total
        print(f"Loaded Real-Time Balances - Spot: €{spot_total:.2f} | Futures: €{fut_total:.2f} | Combined: €{combined:.2f}")
        
        # Save pockets on boot to database or state json so loop can read it
        pockets = {
            "spot_pocket": spot_total,
            "futures_pocket": fut_total,
            "timestamp": int(time.time())
        }
        with open("/broker/storage/db/pockets.json", "w") as pf:
            json.dump(pockets, pf, indent=2)
            
        return combined
    except Exception as e:
        print(f"Failed to fetch live equity dynamically: {e}. Falling back to €297.68")
        # Fallback pockets
        pockets = {
            "spot_pocket": 149.18,
            "futures_pocket": 148.50,
            "timestamp": int(time.time())
        }
        with open("/broker/storage/db/pockets.json", "w") as pf:
            json.dump(pockets, pf, indent=2)
        return 297.68

def start_new_run():
    init_run_db()
    
    run_id = f"RUN-24H-{uuid.uuid4().hex[:6].upper()}"
    start_time = int(time.time())
    end_time = start_time + (24 * 3600)
    flattening_time = end_time - (15 * 60) # 15 minutes before end
    
    initial_equity = get_live_equity()
    target_equity = initial_equity * 1.05 # +5% Target
    
    intent = {
        "directive": "EXTREME_AGGRESSION_24H",
        "allow_futures": True,
        "allow_spot": True,
        "target_profit_pct": 5.0,
        "shadow_lanes_enabled": True
    }
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Mark old runs as COMPLETED/ABORTED
    c.execute("UPDATE runs SET status = 'ABORTED' WHERE status = 'ACTIVE'")
    
    c.execute('''
        INSERT INTO runs (run_id, start_time, end_time, flattening_time, initial_equity_eur, target_equity_eur, intent, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (run_id, start_time, end_time, flattening_time, initial_equity, target_equity, json.dumps(intent), 'ACTIVE'))
    
    conn.commit()
    conn.close()
    
    print(f"Mission {run_id} Initialized.")
    print(f"Base Equity: €{initial_equity:.2f} | Target: €{target_equity:.2f} (+5%)")
    print(f"Flattening Deadline (Kill Switch): {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(flattening_time))}")
    return run_id

if __name__ == "__main__":
    start_new_run()
