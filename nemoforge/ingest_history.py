import ccxt
import time
import os
import pandas as pd
import datetime

def ingest_contract_history(symbol, timeframe="1m", days=365):
    """
    Ingests historical candles for a specific symbol in paginated, rate-limited chunks.
    Ensures the VPS and Kraken API are never overloaded.
    """
    exchange = ccxt.kraken()
    out_dir = "./data/history"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{symbol.replace('/', '_')}_{timeframe}.csv")
    
    print(f"[{symbol}] Starting ingestion of {days} days of {timeframe} candles...")
    
    # Calculate timestamps
    now = datetime.datetime.now()
    start_time = now - datetime.timedelta(days=days)
    since_ms = int(start_time.timestamp() * 1000)
    
    all_ohlcv = []
    
    # Kraken maximum limit per OHLC fetch is usually 720 bars
    limit = 720
    
    while since_ms < int(now.timestamp() * 1000):
        try:
            print(f"[{symbol}] Fetching candles since {datetime.datetime.fromtimestamp(since_ms/1000)}...")
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, since=since_ms, limit=limit)
            
            if not ohlcv:
                print(f"[{symbol}] No more candles returned. Concluding.")
                break
                
            all_ohlcv.extend(ohlcv)
            
            # Update 'since' timestamp to the last returned bar's timestamp + timeframe step
            last_bar_ts = ohlcv[-1][0]
            since_ms = last_bar_ts + 60000 # add 1 minute in ms
            
            # Rate limit delay (metodo e calma: 3 seconds sleep between calls to be safe)
            time.sleep(3.0)
            
            # Prevent excessive memory build-up by periodically appending to CSV
            if len(all_ohlcv) >= 10000:
                df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
                df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
                
                # Append or write
                if not os.path.exists(out_path):
                    df.to_csv(out_path, index=False)
                else:
                    df.to_csv(out_path, mode='a', header=False, index=False)
                all_ohlcv = []
                
        except Exception as e:
            print(f"[{symbol}] API Error: {e}. Sleeping 10 seconds before retrying...")
            time.sleep(10.0)
            
    # Write remaining cached candles
    if all_ohlcv:
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        if not os.path.exists(out_path):
            df.to_csv(out_path, index=False)
        else:
            df.to_csv(out_path, mode='a', header=False, index=False)
            
    # Clean duplicates and sort chronologically
    if os.path.exists(out_path):
        df_clean = pd.read_csv(out_path)
        df_clean['timestamp'] = pd.to_datetime(df_clean['timestamp'])
        df_clean = df_clean.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
        df_clean.to_csv(out_path, index=False)
        print(f"[{symbol}] Ingestion complete. Total clean rows: {len(df_clean)}. File saved to {out_path}")
        return len(df_clean)
    return 0

if __name__ == '__main__':
    # Test call with a small limit or let the CLI orchestrate multiple contracts
    print("Ingestion module compiled.")
