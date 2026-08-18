import sys
import os
import sqlite3
import unittest
import json
import time
import subprocess
import logging

# Append parent directory to sys.path to enable proper imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Dynamic Path Overrides to guarantee absolute test-process isolation!
TEST_DB_PATH = "/tmp/test_nemotron.sqlite"
TEST_LOCK_PATH = "/tmp/test_nemoloop.lock"

# Force environment overrides so that importing trading_loop_v2 or run_24h_loop_v2
# DOES NOT trigger FileHandler creation or database operations on production files.
os.environ["NEMO_TEST_MODE"] = "true"

from nemoforge.utils.lock import acquire_lock
from nemoforge.db_init_v2 import init_db_v2
from nemoforge.trading_loop_v2 import TradingLoopV2
from nemoforge.run_24h_loop_v2 import normalize_pair, IntegratedProductionLoop

class TestNemoForgeV2(unittest.TestCase):
    
    def setUp(self):
        # Initialize isolated test database schema
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except OSError:
                pass
        if os.path.exists(TEST_LOCK_PATH):
            try:
                os.remove(TEST_LOCK_PATH)
            except OSError:
                pass
            
        init_db_v2(TEST_DB_PATH)
        
        # Override module database paths at runtime to target our isolated test DB
        import nemoforge.trading_loop_v2
        import nemoforge.db_init_v2
        import nemoforge.run_24h_loop_v2
        nemoforge.trading_loop_v2.DB_PATH = TEST_DB_PATH
        nemoforge.db_init_v2.DB_PATH = TEST_DB_PATH
        nemoforge.run_24h_loop_v2.DB_PATH = TEST_DB_PATH
        
        self.loop = TradingLoopV2("RUN-TEST-123", lock_path=TEST_LOCK_PATH)
        
    def tearDown(self):
        # Clean up test database & test locks
        if os.path.exists(TEST_DB_PATH):
            try:
                os.remove(TEST_DB_PATH)
            except OSError:
                pass
        if os.path.exists(TEST_LOCK_PATH):
            try:
                os.remove(TEST_LOCK_PATH)
            except OSError:
                pass
            
    def test_double_start_lock(self):
        """Test Case 1: Doppio Avvio (Kernel-level fcntl flock exclusive non-blocking)"""
        print("\n[TEST] Running Test Case 1: Double-Start Lock (flock)...")
        # Our setUp already called TradingLoopV2 with TEST_LOCK_PATH.
        # Spawning a separate subprocess with the virtualenv Python must fail!
        python_bin = "/broker/storage/storage-next/venv/bin/python3" if os.path.exists("/broker/storage/storage-next/venv/bin/python3") else "python3"
        cmd = f"export PYTHONPATH=/broker/storage/storage-next && {python_bin} -c 'import sys, os; sys.path.append(\"/broker/storage/storage-next\"); from nemoforge.utils.lock import acquire_lock; acquire_lock(\"{TEST_LOCK_PATH}\")'"
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        self.assertEqual(res.returncode, 1)
        self.assertIn("ERROR: Another instance of the loop is already running", res.stdout + res.stderr)
        print("[TEST] Success: Double-start lock successfully verified across separate processes!")

    def test_pair_normalization(self):
        """Test Case 2: Idempotent pair normalization"""
        print("\n[TEST] Running Test Case 2: Pair Normalization...")
        self.assertEqual(normalize_pair("BTC/EUR"), "BTC/EUR")
        self.assertEqual(normalize_pair("BTCEUR"), "BTC/EUR")
        self.assertEqual(normalize_pair("BTCUSD"), "BTC/USD")
        self.assertEqual(normalize_pair("BTC/USD"), "BTC/USD")
        print("[TEST] Success: Pair normalization successfully verified!")

    def test_database_schema(self):
        """Test Case 3: Database Schema Check check"""
        print("\n[TEST] Running Test Case 3: Database Schema Check...")
        conn = sqlite3.connect(TEST_DB_PATH)
        c = conn.cursor()
        
        # Verify paper_orders columns
        c.execute("PRAGMA table_info(paper_orders)")
        cols_orders = [x[1] for x in c.fetchall()]
        self.assertIn("order_id", cols_orders)
        self.assertIn("run_id", cols_orders)
        self.assertIn("fill_price", cols_orders)
        
        # Verify paper_positions has position_id (and symbol is NOT primary key)
        c.execute("PRAGMA table_info(paper_positions)")
        cols_pos = c.fetchall()
        column_names = [col[1] for col in cols_pos]
        pk_cols = [col[1] for col in cols_pos if col[5] == 1]
        
        self.assertIn("position_id", column_names)
        self.assertIn("position_id", pk_cols)
        self.assertNotIn("symbol", pk_cols) # symbol must not be PK!
        
        conn.close()
        print("[TEST] Success: Database schema V2.0 verified successfully!")

    def test_scale_in_out_math(self):
        """Test Case 4: Position Scale-In and Scale-Out realized P&L math with proportional fees"""
        print("\n[TEST] Running Test Case 4: Scale-In & Scale-Out Math...")
        
        # 1. Open new position (Scale-In / Entry)
        # order_id, symbol, action, size, fill_price, fee, slippage, leverage, tp_price, sl_price
        self.loop.execute_transactional_fill("FP-001", "PF_ETHUSD", "buy", 0.5, 3000.0, 0.75, 0.001, 10.0, 3105.0, 2955.0)
        
        # Check that it exists in SQLite
        conn = sqlite3.connect(TEST_DB_PATH)
        c = conn.cursor()
        c.execute("SELECT position_id, size, average_entry_price, cumulative_fees FROM paper_positions WHERE symbol='PF_ETHUSD' AND status='OPEN'")
        row = c.fetchone()
        self.assertIsNotNone(row)
        pos_id, size, avg_price, fees = row
        self.assertAlmostEqual(size, 0.5)
        self.assertAlmostEqual(avg_price, 3000.0)
        self.assertAlmostEqual(fees, 0.75)
        
        # 2. Scale-In addition (add 0.5 size @ 3100.0 with 0.78 fee)
        self.loop.execute_transactional_fill("FP-002", "PF_ETHUSD", "buy", 0.5, 3100.0, 0.78, 0.001, 10.0, 3105.0, 2955.0)
        
        c.execute("SELECT size, average_entry_price, cumulative_fees FROM paper_positions WHERE position_id=?", (pos_id,))
        row = c.fetchone()
        self.assertIsNotNone(row)
        size, avg_price, fees = row
        self.assertAlmostEqual(size, 1.0)
        self.assertAlmostEqual(avg_price, 3050.0) # ((3000*0.5)+(3100*0.5))/1.0 = 3050.0
        self.assertAlmostEqual(fees, 1.53) # 0.75 + 0.78 = 1.53
        
        # 3. Scale-Out partial close (close 0.4 size @ 3200.0 with 0.64 fee)
        self.loop.execute_transactional_fill("FP-003", "PF_ETHUSD", "sell", 0.4, 3200.0, 0.64, 0.001, 10.0, 0.0, 0.0)
        
        # Verify that remaining size is updated and remaining proportional entry fee is allocated
        # Fraction closed = 0.4 / 1.0 = 40%
        # Entry fee allocated = 1.53 * 0.40 = 0.612
        # Remaining entry fee in position = 1.53 - 0.612 = 0.918
        c.execute("SELECT size, average_entry_price, cumulative_fees FROM paper_positions WHERE position_id=?", (pos_id,))
        row = c.fetchone()
        self.assertIsNotNone(row)
        size, avg_price, fees = row
        self.assertAlmostEqual(size, 0.6)
        self.assertAlmostEqual(fees, 0.918)
        
        # Verify that closed trade was recorded correctly in paper_trades_closed with exact net P&L and fees
        # Gross P&L = (3200.0 - 3050.0) * 0.4 = 60.0
        # Total fees = Entry allocated (0.612) + Exit execution fee (0.64) = 1.252
        # Net realized P&L = 60.0 - 1.252 = 58.748
        c.execute("SELECT realized_pnl, fee_total, exit_reason FROM paper_trades_closed WHERE run_id='RUN-TEST-123'")
        row_closed = c.fetchone()
        self.assertIsNotNone(row_closed)
        pnl, total_fees, reason = row_closed
        self.assertAlmostEqual(pnl, 58.748)
        self.assertAlmostEqual(total_fees, 1.252)
        self.assertEqual(reason, "PARTIAL_CLOSE")
        
        conn.close()
        print("[TEST] Success: Scale-In & Scale-Out Math verified successfully with proportional fee allocation!")

if __name__ == '__main__':
    unittest.main()
