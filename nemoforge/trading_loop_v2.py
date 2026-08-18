import sys
import os
import json
import sqlite3
import time
import subprocess
import logging

# Dynamically append parent directory to sys.path to enable proper imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nemoforge.utils.lock import acquire_lock
from nemoforge.db_init_v2 import init_db_v2

# Configuration paths on VPS
BASE_PATH = "/broker/storage/storage-next" if os.path.exists("/broker/storage/storage-next") else "./"
DB_PATH = os.path.join(BASE_PATH, "db/nemotron.sqlite")
POCKETS_PATH = os.path.join(BASE_PATH, "db/pockets.json")
KRAKEN_PATH = "/home/tre/.local/bin/kraken"

class TradingLoopV2:
    """
    NemoForge V2.0 Production-grade Trading Loop Orchestrator
    Implements kernel-level flock lock, transactional SQLite ledger (scale-in/out),
    and active paper broker reconciliation.
    """
    def __init__(self, run_id):
        self.run_id = run_id
        # Acquire kernel-level flock lock to prevent concurrent instances
        acquire_lock("/tmp/nemoloop.lock")
        
        # Initialize DB schemas
        init_db_v2(DB_PATH)
        
    def log_order(self, order_id, symbol, action, size, fill_price, fee, slippage):
        """Records an execution order to paper_orders table"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO paper_orders (order_id, run_id, symbol, action, size, fill_price, fee, slippage, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_id, self.run_id, symbol, action, size, fill_price, fee, slippage, int(time.time())))
        conn.commit()
        conn.close()
        print(f"Recorded order {order_id} for {symbol} to database.")

    def update_position(self, symbol, side, size, fill_price, fee, leverage, tp_price, sl_price):
        """
        Manages dynamic positions in the paper_positions table (supports Scale-In & Scale-Out)
        """
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        # Check if we already have an active position for this symbol
        c.execute("SELECT size, average_entry_price, cumulative_fees FROM paper_positions WHERE symbol = ? AND status = 'OPEN'", (symbol,))
        row = c.fetchone()
        
        # Ensure sizes are signed: Long is positive, Short is negative
        stored_size = size if side.lower() == 'long' else -size
        
        if not row:
            # Scale-In: Open brand new position
            c.execute('''
                INSERT INTO paper_positions (symbol, run_id, side, size, average_entry_price, leverage, cumulative_fees, accumulated_funding, tp_price, sl_price, opened_at, last_updated, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (symbol, self.run_id, side.lower(), stored_size, fill_price, leverage, fee, 0.0, tp_price, sl_price, int(time.time()), int(time.time()), 'OPEN'))
            print(f"Opened new position for {symbol} ({side}) at ${fill_price:.2f}.")
        else:
            prev_size, prev_avg_price, prev_fees = row
            
            # Check if this is an addition (Scale-In) or reduction (Scale-Out)
            if (prev_size > 0 and side.lower() == 'long') or (prev_size < 0 and side.lower() == 'short'):
                # Scale-In: Calculate weighted average entry price
                new_size = prev_size + stored_size
                new_avg_price = ((prev_avg_price * abs(prev_size)) + (fill_price * size)) / abs(new_size)
                new_fees = prev_fees + fee
                
                c.execute('''
                    UPDATE paper_positions 
                    SET size = ?, average_entry_price = ?, cumulative_fees = ?, last_updated = ?
                    WHERE symbol = ? AND status = 'OPEN'
                ''', (new_size, new_avg_price, new_fees, int(time.time()), symbol))
                print(f"Scale-In: Added {size} to {symbol} position. New average entry price: ${new_avg_price:.4f}.")
            else:
                # Scale-Out: Partial or full position close
                reduced_size = min(size, abs(prev_size))
                new_size = prev_size - (reduced_size if prev_size > 0 else -reduced_size)
                
                # Calculate realized P&L
                realized_pnl = 0.0
                if prev_size > 0:  # Long
                    realized_pnl = (fill_price - prev_avg_price) * reduced_size
                else:  # Short
                    realized_pnl = (prev_avg_price - fill_price) * reduced_size
                    
                realized_pnl_pct = (realized_pnl / (prev_avg_price * reduced_size)) * 100 if prev_avg_price > 0 else 0.0
                
                # Record to closed trades
                import uuid
                trade_id = f"TR-{uuid.uuid4().hex[:6].upper()}"
                c.execute('''
                    INSERT INTO paper_trades_closed (trade_id, run_id, symbol, side, size, entry_price, exit_price, realized_pnl, realized_pnl_pct, fee_total, duration, mae_pct, mfe_pct, exit_reason, closed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (trade_id, self.run_id, symbol, 'long' if prev_size > 0 else 'short', reduced_size, prev_avg_price, fill_price, realized_pnl, realized_pnl_pct, fee + prev_fees, int(time.time()) - (row[10] if len(row) > 10 else int(time.time())), 0.0, 0.0, 'PARTIAL_CLOSE' if abs(new_size) > 1e-8 else 'FULL_CLOSE', int(time.time())))
                
                if abs(new_size) < 1e-8:
                    c.execute("UPDATE paper_positions SET status = 'CLOSED', size = 0.0, last_updated = ? WHERE symbol = ?", (int(time.time()), symbol))
                    print(f"Scale-Out: Closed position on {symbol} with realized P&L: ${realized_pnl:+.4f} ({realized_pnl_pct:+.2f}%).")
                else:
                    c.execute("UPDATE paper_positions SET size = ?, last_updated = ? WHERE symbol = ?", (new_size, int(time.time()), symbol))
                    print(f"Scale-Out: Reduced position size on {symbol} by {reduced_size}. Realized P&L: ${realized_pnl:+.4f}.")
                    
        conn.commit()
        conn.close()

    def reconcile_with_broker(self):
        """
        Reconciliation Routine (Every 5 minutes)
        Loads open positions from paper broker (CLI) and reconciles SQLite positions.
        """
        print("Reconciliation Routine: Fetching active paper broker positions...")
        cmd = f"env -u KRAKEN_WORKSPACE {KRAKEN_PATH} futures paper positions -o json"
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            if res.returncode != 0:
                print(f"Reconciliation error: Paper broker command failed: {res.stderr}")
                return
                
            data = json.loads(res.stdout)
            broker_positions = data if isinstance(data, list) else data.get("positions", [])
            
            # Read our current positions in SQLite
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT symbol, size, side FROM paper_positions WHERE status = 'OPEN'")
            sqlite_positions = {r[0]: {"size": r[1], "side": r[2]} for r in c.fetchall()}
            
            # Map broker positions
            broker_mapped = {}
            for pos in broker_positions:
                symbol = pos.get("symbol")
                size = abs(float(pos.get("size", 0.0)))
                side = pos.get("side", "long").lower()
                if size > 1e-8:
                    broker_mapped[symbol] = {"size": size, "side": side}
                    
            # Update SQLite to match Broker (Broker is the ONLY source of truth!)
            for symbol, b_pos in broker_mapped.items():
                stored_size = b_pos["size"] if b_pos["side"] == 'long' else -b_pos["size"]
                if symbol not in sqlite_positions:
                    # Missing in SQLite: Open it contabiliy
                    c.execute('''
                        INSERT INTO paper_positions (symbol, run_id, side, size, average_entry_price, leverage, cumulative_fees, accumulated_funding, tp_price, sl_price, opened_at, last_updated, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (symbol, self.run_id, b_pos["side"], stored_size, 0.0, 10.0, 0.0, 0.0, 0.0, 0.0, int(time.time()), int(time.time()), 'OPEN'))
                    print(f"Reconciled: Found missing position on {symbol} in paper broker. Added to SQLite.")
                elif abs(sqlite_positions[symbol]["size"]) != b_pos["size"]:
                    # Discrepancy in size: Align SQLite to broker
                    c.execute("UPDATE paper_positions SET size = ?, last_updated = ? WHERE symbol = ?", (stored_size, int(time.time()), symbol))
                    print(f"Reconciled: Aligned size of {symbol} from {sqlite_positions[symbol]['size']} to {b_pos['size']} (Broker state).")
                    
            # Close positions in SQLite that are no longer in broker
            for symbol in sqlite_positions:
                if symbol not in broker_mapped:
                    c.execute("UPDATE paper_positions SET status = 'CLOSED', size = 0.0, last_updated = ? WHERE symbol = ?", (int(time.time()), symbol))
                    print(f"Reconciled: Closed position on {symbol} in SQLite because it does not exist in paper broker.")
                    
            conn.commit()
            conn.close()
            print("Reconciliation complete. Database aligned with paper broker.")
        except Exception as e:
            print(f"Error during database-broker reconciliation: {e}")
