import sys
import os
import sqlite3
import unittest
import json
import time
import subprocess

# Append parent directory to sys.path to enable proper imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nemoforge.utils.lock import acquire_lock
from nemoforge.db_init_v2 import init_db_v2
from nemoforge.trading_loop_v2 import TradingLoopV2

# Test paths
TEST_DB_PATH = "/tmp/test_nemotron.sqlite"

class TestNemoForgeV2(unittest.TestCase):
    
    def setUp(self):
        # Initialize test database schema
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
        init_db_v2(TEST_DB_PATH)
        self.loop = TradingLoopV2("RUN-TEST-123")
        # Override the database path inside the loop instance
        import nemoforge.trading_loop_v2
        nemoforge.trading_loop_v2.DB_PATH = TEST_DB_PATH
        
    def tearDown(self):
        # Clean up test database
        if os.path.exists(TEST_DB_PATH):
            os.remove(TEST_DB_PATH)
            
    def test_double_start_lock(self):
        """Test Case 1: Doppio Avvio (Kernel-level fcntl flock exclusive non-blocking)"""
        print("\n[TEST] Running Test Case 1: Double-Start Lock (flock)...")
        # Our setUp already called acquire_lock on /tmp/nemoloop.lock.
        # Spawning a separate subprocess with the virtualenv Python must fail!
        python_bin = "/broker/storage/storage-next/venv/bin/python3" if os.path.exists("/broker/storage/storage-next/venv/bin/python3") else "python3"
        cmd = f"export PYTHONPATH=/broker/storage/storage-next && {python_bin} -c 'import sys, os; sys.path.append(\"/broker/storage/storage-next\"); from nemoforge.utils.lock import acquire_lock; acquire_lock(\"/tmp/nemoloop.lock\")'"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        self.assertEqual(res.returncode, 1)
        self.assertIn("ERROR: Another instance of the loop is already running", res.stdout + res.stderr)
        print("[TEST] Success: Double-start lock successfully verified across separate processes!")

    def test_database_schema(self):
        """Test Case 2: Database Schema Check"""
        print("\n[TEST] Running Test Case 2: Database Schema Check...")
        conn = sqlite3.connect(TEST_DB_PATH)
        c = conn.cursor()
        
        # Verify paper_orders columns
        c.execute("PRAGMA table_info(paper_orders)")
        cols_orders = [x[1] for x in c.fetchall()]
        self.assertIn("order_id", cols_orders)
        self.assertIn("run_id", cols_orders)
        self.assertIn("fill_price", cols_orders)
        
        # Verify paper_positions columns
        c.execute("PRAGMA table_info(paper_positions)")
        cols_pos = [x[1] for x in c.fetchall()]
        self.assertIn("symbol", cols_pos)
        self.assertIn("average_entry_price", cols_pos)
        self.assertIn("cumulative_fees", cols_pos)
        
        # Verify paper_trades_closed columns
        c.execute("PRAGMA table_info(paper_trades_closed)")
        cols_trades = [x[1] for x in c.fetchall()]
        self.assertIn("trade_id", cols_trades)
        self.assertIn("realized_pnl_pct", cols_trades)
        
        conn.close()
        print("[TEST] Success: Database schema V2.0 verified successfully!")

    def test_scale_in_out_math(self):
        """Test Case 3: Position Scale-In and Scale-Out realized P&L math"""
        print("\n[TEST] Running Test Case 3: Scale-In & Scale-Out Math...")
        
        # 1. Open new position (Scale-In)
        # symbol, side, size, fill_price, fee, leverage, tp_price, sl_price
        self.loop.update_position("PF_PEPEUSD", "short", 1000.0, 2.5e-6, 0.05, 10.0, 2.0e-6, 3.0e-6)
        
        # Query DB to check if opened correctly
        conn = sqlite3.connect(TEST_DB_PATH)
        c = conn.cursor()
        c.execute("SELECT size, average_entry_price, cumulative_fees FROM paper_positions WHERE symbol='PF_PEPEUSD'")
        row = c.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], -1000.0) # short is negative size
        self.assertAlmostEqual(row[1], 2.5e-6, places=12)
        self.assertEqual(row[2], 0.05)
        
        # 2. Add to position (Scale-In / Addition)
        self.loop.update_position("PF_PEPEUSD", "short", 1000.0, 2.3e-6, 0.05, 10.0, 2.0e-6, 3.0e-6)
        c.execute("SELECT size, average_entry_price, cumulative_fees FROM paper_positions WHERE symbol='PF_PEPEUSD'")
        row = c.fetchone()
        self.assertEqual(row[0], -2000.0)
        # Weighted average entry price: ((2.5e-6 * 1000) + (2.3e-6 * 1000)) / 2000 = 2.4e-6
        self.assertAlmostEqual(row[1], 2.4e-6, places=12)
        self.assertEqual(row[2], 0.10)
        
        # 3. Reduce position partially (Scale-Out / Partial Close)
        # We execute a market buy (long) of 500.0 units at exit price 2.0e-6 (in profit since we are short!)
        self.loop.update_position("PF_PEPEUSD", "long", 500.0, 2.0e-6, 0.02, 10.0, 2.0e-6, 3.0e-6)
        c.execute("SELECT size FROM paper_positions WHERE symbol='PF_PEPEUSD'")
        row = c.fetchone()
        self.assertEqual(row[0], -1500.0) # size reduced from -2000 to -1500
        
        # Verify realized P&L of partial close in paper_trades_closed
        c.execute("SELECT realized_pnl, realized_pnl_pct, exit_reason FROM paper_trades_closed")
        trade = c.fetchone()
        self.assertIsNotNone(trade)
        # Realized P&L: (avg_entry - exit) * size = (2.4e-6 - 2.0e-6) * 500 = 0.4e-6 * 500 = 0.0002
        self.assertAlmostEqual(trade[0], 0.0002, places=6)
        # P&L Pct: (realized_pnl / (entry_price * size)) * 100 = 16.66%
        self.assertAlmostEqual(trade[1], 16.6667, places=3)
        self.assertEqual(trade[2], "PARTIAL_CLOSE")
        
        conn.close()
        print("[TEST] Success: Scale-In weighted price and Scale-Out realized P&L computed perfectly!")

if __name__ == '__main__':
    unittest.main()
