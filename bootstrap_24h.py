import ccxt
import sqlite3
import json
import time
import uuid
import os
os.environ["HOME"] = "/broker/storage/storage-next"
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
        with open("/broker/storage/storage-next/db/pockets.json", "w") as pf:
            json.dump(pockets, pf, indent=2)
            
        # V7.0: Dynamic Workspace Reset on startup to completely solve the Ghost Drawdown!
        import subprocess
        KRAKEN_PATH = "/home/tre/.local/bin/kraken"
        
        # 1. Reset Spot paper workspace only if spot_total is positive! (V7.1: With 0.26% Spot Fee & 0.15% Spot Slippage)
        if spot_total > 0.0:
            try:
                print(f"Resetting Spot paper workspace 'fondazione-agentic-next' to €{spot_total:.2f} (Fee: 0.26%, Slippage: 0.15%)...")
                cmd_spot = f"{KRAKEN_PATH} workspace reset --capital {spot_total:.2f} --fee-rate 0.0026 --slippage-rate 0.0015 fondazione-agentic-next --yes"
                subprocess.run(cmd_spot, shell=True)
            except Exception as e:
                print(f"Error resetting Spot workspace: {e}")
        else:
            print("Spot total is €0.00, skipping Spot paper workspace reset (disabled).")
            
        # 2. Reset Futures paper account (V7.1: With 0.05% Futures Fee)
        try:
            print(f"Resetting Futures paper account to €{fut_total:.2f} (Fee: 0.05%)...")
            cmd_fut = f"env -u KRAKEN_WORKSPACE {KRAKEN_PATH} futures paper reset --balance {fut_total:.2f} --fee-rate 0.0005 --yes"
            subprocess.run(cmd_fut, shell=True)
        except Exception as e:
            print(f"Error resetting Futures account: {e}")
            
        return combined
    except Exception as e:
        print(f"Failed to fetch live equity dynamically: {e}. Falling back to €297.68")
        # Fallback pockets
        pockets = {
            "spot_pocket": 149.18,
            "futures_pocket": 148.50,
            "timestamp": int(time.time())
        }
        with open("/broker/storage/storage-next/db/pockets.json", "w") as pf:
            json.dump(pockets, pf, indent=2)
            
        # V7.0 Fallback Resets
        import subprocess
        KRAKEN_PATH = "/home/tre/.local/bin/kraken"
        try:
            print("Resetting Spot paper workspace 'fondazione-agentic-next' to €149.18 (fallback)...")
            subprocess.run(f"{KRAKEN_PATH} workspace reset --name fondazione-agentic-next --capital 149.18 --acknowledged", shell=True)
            print("Resetting Futures paper account to €148.50 (fallback)...")
            subprocess.run(f"env -u KRAKEN_WORKSPACE {KRAKEN_PATH} futures paper reset --balance 148.50 --yes", shell=True)
        except Exception as ex:
            print(f"Error executing fallback resets: {ex}")
            
        return 297.68

def start_new_run():
    init_run_db()
    
    # NEW V7.2: Load run_config.json if it exists (Dynamic Parametrization)
    CONFIG_PATH = "/broker/storage/storage-next/db/run_config.json"
    target_equity_eur = None
    duration_hours = 24.0
    max_capital_pct = 100.0
    
    try:
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH) as f:
                cfg = json.load(f)
                target_equity_eur = float(cfg.get("target_equity_eur", 500.0))
                duration_hours = float(cfg.get("duration_hours", 24.0))
                max_capital_pct = float(cfg.get("max_capital_allocation_pct", 100.0))
            print(f"Loaded Custom Config: Target €{target_equity_eur:.2f} | Hours: {duration_hours} | Max Capital: {max_capital_pct}%")
    except Exception as e:
        print(f"No custom config or error loading: {e}. Using defaults.")

    run_id = f"RUN-24H-{uuid.uuid4().hex[:6].upper()}"
    start_time = int(time.time())
    
    # Calculate end_time based on custom hours
    end_time = start_time + int(duration_hours * 3600)
    flattening_time = end_time - (15 * 60) # 15 minutes before end
    
    initial_equity = get_live_equity()
    
    # Use custom target if provided, else fallback to +5%
    if target_equity_eur is None:
        target_equity = initial_equity * 1.05
    else:
        target_equity = target_equity_eur
        
    intent = {
        "directive": "EXTREME_AGGRESSION_24H",
        "allow_futures": True,
        "allow_spot": True,
        "target_profit_pct": ((target_equity - initial_equity) / initial_equity * 100) if initial_equity > 0 else 5.0,
        "shadow_lanes_enabled": True,
        "max_capital_allocation_pct": max_capital_pct,
        "duration_hours": duration_hours
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
