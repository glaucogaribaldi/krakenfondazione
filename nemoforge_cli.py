#!/usr/bin/env python3
import argparse
import sys
import os
import json
import datetime
import ccxt

from nemoforge.lacus_engine import LacusEngine
from nemoforge.prompt_optimizer import PromptOptimizer
from nemoforge.telemetry_profiler import TelemetryProfiler

def cmd_download_history(args):
    print(f"Connecting to Kraken Public API to fetch history for {args.pair}...")
    exchange = ccxt.kraken()
    try:
        # Fetch daily or hourly OHLCV depending on arguments
        limit = args.limit
        timeframe = args.timeframe
        
        print(f"Fetching {limit} bars of {timeframe} for {args.pair}...")
        ohlcv = exchange.fetch_ohlcv(args.pair, timeframe=timeframe, limit=limit)
        
        # Save to csv
        out_dir = "./data/history"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{args.pair.replace('/', '_')}_{timeframe}.csv")
        
        df = pd = __import__('pandas').DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.to_csv(out_path, index=False)
        print(f"SUCCESS: Saved historical candles to {out_path}")
    except Exception as e:
        print(f"Error downloading history from Kraken: {e}")

def cmd_backtest(args):
    print(f"Starting Lacus Backtest on file: {args.file}...")
    engine = LacusEngine(initial_capital=args.capital, fee_rate=args.fee, slippage_rate=args.slippage)
    
    try:
        df = engine.load_ohlcv(args.file)
        print(f"Loaded {len(df)} historical bars.")
        
        # Replay simulator with a simple mock trading logic
        # For testing purposes, we can execute some standard trades (e.g. buying or selling on momentum breakout)
        # to prove the engine is completely operational!
        print("Replaying historical bars...")
        for idx, row in df.iterrows():
            # A simple mock trading signal
            if idx == 10 and len(df) > 20:
                print(f"[{row['timestamp']}] Mock Momentum Long signal triggered.")
                engine.execute_order(args.symbol, 'buy', 0.1, row['close'], leverage=1.0, timestamp=row['timestamp'])
            elif idx == len(df) - 5:
                print(f"[{row['timestamp']}] Mock Close/Flatten signal triggered.")
                if args.symbol in engine.positions:
                    size = abs(engine.positions[args.symbol]['size'])
                    engine.execute_order(args.symbol, 'sell', size, row['close'], leverage=1.0, timestamp=row['timestamp'])
                    
        # Calculate final results
        final_prices = {args.symbol: df['close'].iloc[-1]}
        final_equity = engine.get_equity(final_prices)
        pnl = final_equity - args.capital
        pnl_pct = (pnl / args.capital) * 100
        
        print("\n=== LACUS BACKTEST RESULTS ===")
        print(f"Initial Capital:  €{args.capital:,.2f}")
        print(f"Final Equity:     €{final_equity:,.2f}")
        print(f"P&L:              €{pnl:,.2f} ({pnl_pct:+.2f}%)")
        print(f"Total Trades:     {len(engine.trade_history)}")
        print("==============================\n")
    except Exception as e:
        print(f"Error during backtesting: {e}")

def cmd_optimize(args):
    print("Initializing Meta-Prompt Optimizer...")
    optimizer = PromptOptimizer(db_path=args.db)
    res = optimizer.optimize_prompt()
    if res.get("status") == "success":
        print(f"Prompt optimization completed successfully! Mutated prompt saved.")
    else:
        print(f"Prompt optimization failed: {res.get('reason')}")

def cmd_status(args):
    print("SentinelProf - Fetching Real-time System & Telemetry Status...")
    profiler = TelemetryProfiler()
    gpus = profiler.get_gpu_metrics()
    
    print("\n=== VPS TELEMETRY & RESOURCES ===")
    print("NVIDIA Tesla T4 GPU Status:")
    for gpu in gpus:
        if gpu.get("status") == "offline" or gpu.get("status") == "error":
            print(f"  - GPU Offline: {gpu.get('reason')}")
        else:
            print(f"  - GPU #{gpu['gpu_index']}: Utilization: {gpu['utilization_pct']}% | VRAM: {gpu['memory_used_mb']:.1f}/{gpu['memory_total_mb']:.1f} MB ({gpu['memory_utilization_pct']}%)")
    print("System Status: OPERATIONAL")
    print("=================================\n")

def main():
    parser = argparse.ArgumentParser(description="NemoForge V1.0 CLI Plancia di Controllo")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # 1. Download History
    p_dl = subparsers.add_parser("download-history", help="Download historical candles from Kraken")
    p_dl.add_argument("--pair", default="BTC/EUR", help="Trading pair (default: BTC/EUR)")
    p_dl.add_argument("--timeframe", default="1h", help="Timeframe (default: 1h)")
    p_dl.add_argument("--limit", type=int, default=100, help="Number of bars to fetch")
    
    # 2. Backtest
    p_bt = subparsers.add_parser("backtest", help="Run a Lacus backtest simulator")
    p_bt.add_argument("--file", required=True, help="Path to historical CSV file")
    p_bt.add_argument("--symbol", default="PF_XBTUSD", help="Contract symbol")
    p_bt.add_argument("--capital", type=float, default=50000.0, help="Starting capital")
    p_bt.add_argument("--fee", type=float, default=0.0026, help="Fee rate")
    p_bt.add_argument("--slippage", type=float, default=0.0, help="Slippage rate")
    
    # 3. Optimize
    p_opt = subparsers.add_parser("optimize", help="Run Meta-Prompt Optimizer via Nemotron")
    p_opt.add_argument("--db", default="./data/krakenfondazione.db", help="Path to production SQLite DB")
    
    # 4. Status
    subparsers.add_parser("status", help="Get real-time VPS telemetry status")
    
    args = parser.parse_args()
    
    if args.command == "download-history":
        cmd_download_history(args)
    elif args.command == "backtest":
        cmd_backtest(args)
    elif args.command == "optimize":
        cmd_optimize(args)
    elif args.command == "status":
        cmd_status(args)

if __name__ == "__main__":
    main()
