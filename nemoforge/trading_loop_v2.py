import sys
import os
import json
import sqlite3
import time
import subprocess
import logging
import uuid

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
    NemoForge V2.1 Production-grade Transactional Trading Ledger
    Ensures complete, atomic database writes for fills, orders, and positions.
    Reconciles directly with the paper broker as the single source of truth.
    """
    def __init__(self, run_id, lock_path="/tmp/nemoloop.lock"):
        self.run_id = run_id
        # Acquire kernel-level flock lock to prevent concurrent instances
        acquire_lock(lock_path)
        
        # Ensure database is migrated and initialized
        init_db_v2(DB_PATH)
        
    def execute_transactional_fill(self, order_id, symbol, action, size, fill_price, fee, slippage, leverage, tp_price, sl_price):
        """
        ATOMIC TRANSACTION: Order + Position + Trade Closed
        Executes a single transactional commit to SQLite to guarantee digit-exact
        consistency between the broker fill and ledger tables.
        """
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        try:
            # Start explicit, atomic database transaction
            c.execute("BEGIN TRANSACTION")
            
            # 1. Write to paper_orders
            c.execute('''
                INSERT INTO paper_orders (order_id, run_id, symbol, action, size, fill_price, fee, slippage, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (order_id, self.run_id, symbol, action, size, fill_price, fee, slippage, int(time.time())))
            
            # 2. Check and manage active positions (using unique position_id)
            c.execute("SELECT position_id, size, average_entry_price, cumulative_fees, opened_at FROM paper_positions WHERE symbol = ? AND status = 'OPEN'", (symbol,))
            row = c.fetchone()
            
            stored_size = size if action.lower() in ['buy', 'long'] else -size
            
            if not row:
                # Open a brand new position (Scale-In / Entry)
                pos_id = f"POS-{uuid.uuid4().hex[:6].upper()}"
                c.execute('''
                    INSERT INTO paper_positions (position_id, run_id, symbol, side, size, average_entry_price, leverage, cumulative_fees, accumulated_funding, tp_price, sl_price, opened_at, last_updated, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (pos_id, self.run_id, symbol, "long" if action.lower() in ['buy', 'long'] else "short", stored_size, fill_price, leverage, fee, 0.0, tp_price, sl_price, int(time.time()), int(time.time()), 'OPEN'))
                print(f"[{symbol}] Atomic Ledger: Opened new position {pos_id} (${fill_price:.2f})")
            else:
                pos_id, prev_size, prev_avg_price, prev_fees, opened_at = row
                
                # Check if this is an addition (Scale-In) or reduction (Scale-Out)
                is_addition = (prev_size > 0 and action.lower() in ['buy', 'long']) or (prev_size < 0 and action.lower() in ['sell', 'short'])
                
                if is_addition:
                    # Scale-In: Calculate weighted average entry price
                    new_size = prev_size + stored_size
                    new_avg_price = ((prev_avg_price * abs(prev_size)) + (fill_price * size)) / abs(new_size)
                    new_fees = prev_fees + fee
                    
                    c.execute('''
                        UPDATE paper_positions 
                        SET size = ?, average_entry_price = ?, cumulative_fees = ?, last_updated = ?
                        WHERE position_id = ?
                    ''', (new_size, new_avg_price, new_fees, int(time.time()), pos_id))
                    print(f"[{symbol}] Atomic Ledger: Scale-In position {pos_id}. New Average Entry Price: ${new_avg_price:.4f}")
                else:
                    # Scale-Out: Partial or full position close
                    reduced_size = min(size, abs(prev_size))
                    new_size = prev_size - (reduced_size if prev_size > 0 else -reduced_size)
                    
                    # 1. PROPORTIONAL FEE ALLOCATION: Deduct proportional fees from current closure
                    # This completely avoids double-counting fees in remaining positions!
                    fraction_closed = reduced_size / abs(prev_size)
                    allocated_entry_fee = prev_fees * fraction_closed
                    remaining_fees = prev_fees - allocated_entry_fee
                    
                    # Total fees for this closed trade = entry fee allocated + exit execution fee
                    total_trade_fees = allocated_entry_fee + fee
                    
                    # 2. CALCULATE REALIZED P&L (Gross & Net)
                    gross_pnl = 0.0
                    if prev_size > 0:  # Long
                        gross_pnl = (fill_price - prev_avg_price) * reduced_size
                    else:  # Short
                        gross_pnl = (prev_avg_price - fill_price) * reduced_size
                        
                    # Net Realized P&L = Gross P&L - Total Trade Fees
                    net_pnl = gross_pnl - total_trade_fees
                    net_pnl_pct = (net_pnl / (prev_avg_price * reduced_size)) * 100 if prev_avg_price > 0 else 0.0
                    
                    # 3. Record trade to paper_trades_closed (using original position_id)
                    trade_id = f"TR-{uuid.uuid4().hex[:6].upper()}"
                    c.execute('''
                        INSERT INTO paper_trades_closed (trade_id, run_id, symbol, side, size, entry_price, exit_price, realized_pnl, realized_pnl_pct, fee_total, duration, mae_pct, mfe_pct, exit_reason, closed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (trade_id, self.run_id, symbol, 'long' if prev_size > 0 else 'short', reduced_size, prev_avg_price, fill_price, net_pnl, net_pnl_pct, total_trade_fees, int(time.time()) - opened_at, 0.0, 0.0, 'PARTIAL_CLOSE' if abs(new_size) > 1e-8 else 'FULL_CLOSE', int(time.time())))
                    
                    if abs(new_size) < 1e-8:
                        # Full Close: Mark status as CLOSED and reset size
                        c.execute("UPDATE paper_positions SET status = 'CLOSED', size = 0.0, cumulative_fees = 0.0, last_updated = ? WHERE position_id = ?", (int(time.time()), pos_id))
                        print(f"[{symbol}] Atomic Ledger: Closed position {pos_id}. Net P&L: ${net_pnl:+.4f} ({net_pnl_pct:+.2f}%)")
                    else:
                        # Partial Close: Update remaining size and remaining entry fees
                        c.execute("UPDATE paper_positions SET size = ?, cumulative_fees = ?, last_updated = ? WHERE position_id = ?", (new_size, remaining_fees, int(time.time()), pos_id))
                        print(f"[{symbol}] Atomic Ledger: Partial scale-out on {pos_id}. Remaining size: {new_size} | Remaining entry fees: ${remaining_fees:.4f}")
            
            # Commit transaction safely and atomically
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"CRITICAL: Failed transactional ledger write. Executing SQL ROLLBACK. Error: {e}")
            conn.rollback()
            conn.close()
            return False

    def log_order(self, order_id, symbol, action, size, fill_price, fee, slippage):
        """Legacy standalone wrapper for simple order logging (migrated to transactional fill)"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''
            INSERT INTO paper_orders (order_id, run_id, symbol, action, size, fill_price, fee, slippage, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (order_id, self.run_id, symbol, action, size, fill_price, fee, slippage, int(time.time())))
        conn.commit()
        conn.close()

    def update_position(self, symbol, side, size, fill_price, fee, leverage, tp_price, sl_price):
        """Legacy standalone wrapper for simple position updating (migrated to transactional fill)"""
        self.execute_transactional_fill(f"E2E-{int(time.time())}", symbol, side, size, fill_price, fee, 0.001, leverage, tp_price, sl_price)

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
            c.execute("SELECT symbol, size, side, position_id FROM paper_positions WHERE status = 'OPEN'")
            sqlite_positions = {r[0]: {"size": r[1], "side": r[2], "position_id": r[3]} for r in c.fetchall()}
            
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
                    # Point 4: Found unaccounted position. Mark as UNATTRIBUTED and halt operations!
                    pos_id = f"POS-UNATTRIBUTED-{uuid.uuid4().hex[:4].upper()}"
                    c.execute('''
                        INSERT INTO paper_positions (position_id, run_id, symbol, side, size, average_entry_price, leverage, cumulative_fees, accumulated_funding, tp_price, sl_price, opened_at, last_updated, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (pos_id, self.run_id, symbol, b_pos["side"], stored_size, 0.0, 10.0, 0.0, 0.0, 0.0, 0.0, int(time.time()), int(time.time()), 'UNATTRIBUTED'))
                    logging.critical(f"🛡️ [RECONCILIATION EXCEPTION] Found unattributed paper position on symbol '{symbol}' in broker! Marked as UNATTRIBUTED. New orders on this asset are blocked until manual resolution.")
                elif abs(sqlite_positions[symbol]["size"]) != b_pos["size"]:
                    # Discrepancy in size: Align SQLite to broker
                    c.execute("UPDATE paper_positions SET size = ?, last_updated = ? WHERE position_id = ?", (stored_size, int(time.time()), sqlite_positions[symbol]["position_id"]))
                    print(f"Reconciled: Aligned size of {symbol} from {sqlite_positions[symbol]['size']} to {b_pos['size']} (Broker state).")
                    
            # Close positions in SQLite that are no longer in broker
            for symbol, s_pos in sqlite_positions.items():
                if symbol not in broker_mapped:
                    c.execute("UPDATE paper_positions SET status = 'CLOSED', size = 0.0, last_updated = ? WHERE position_id = ?", (int(time.time()), s_pos["position_id"]))
                    print(f"Reconciled: Closed position {s_pos['position_id']} on {symbol} in SQLite because it does not exist in paper broker.")
                    
            conn.commit()
            conn.close()
            print("Reconciliation complete. Database aligned with paper broker.")
        except Exception as e:
            print(f"Error during database-broker reconciliation: {e}")
