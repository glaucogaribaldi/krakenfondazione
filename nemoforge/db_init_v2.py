import sqlite3
import os
import sys

def init_db_v2(db_path="/broker/storage/storage-next/db/nemotron.sqlite"):
    """
    Initializes the NemoForge V2.0 transational database schema in SQLite.
    Creates tables for:
    - paper_orders (for every raw order sent)
    - paper_positions (exact transactional copy of active open positions, with scale-in average price, cumulative fees)
    - paper_trades_closed (for final closed trades with realized P&L, fee totals, MAE, MFE, durations)
    """
    print(f"Initializing NemoForge V2.0 database schema at {db_path}...")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 1. paper_orders Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS paper_orders (
            order_id TEXT PRIMARY KEY,
            run_id TEXT,
            symbol TEXT,
            action TEXT,
            size REAL,
            fill_price REAL,
            fee REAL,
            slippage REAL,
            timestamp INTEGER
        )
    ''')
    
    # 2. paper_positions Table (One active row per symbol)
    c.execute('''
        CREATE TABLE IF NOT EXISTS paper_positions (
            symbol TEXT PRIMARY KEY,
            run_id TEXT,
            side TEXT,
            size REAL,
            average_entry_price REAL,
            leverage REAL,
            cumulative_fees REAL,
            accumulated_funding REAL,
            tp_price REAL,
            sl_price REAL,
            opened_at INTEGER,
            last_updated INTEGER,
            status TEXT
        )
    ''')
    
    # 3. paper_trades_closed Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS paper_trades_closed (
            trade_id TEXT PRIMARY KEY,
            run_id TEXT,
            symbol TEXT,
            side TEXT,
            size REAL,
            entry_price REAL,
            exit_price REAL,
            realized_pnl REAL,
            realized_pnl_pct REAL,
            fee_total REAL,
            duration INTEGER,
            mae_pct REAL,
            mfe_pct REAL,
            exit_reason TEXT,
            closed_at INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    print("SUCCESS: Database schema V2.0 initialized successfully!")

if __name__ == '__main__':
    db = "/broker/storage/storage-next/db/nemotron.sqlite" if len(sys.argv) < 2 else sys.argv[1]
    init_db_v2(db)
