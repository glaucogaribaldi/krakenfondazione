import sys
import os

# Aggiungiamo dinamicamente il parent directory a sys.path per sbloccare l'importazione del package nemoforge ovunque venga eseguito
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import ccxt
import time
import subprocess

from nemoforge.ingest_history import ingest_contract_history

def run_bulk():
    print("NemoForge - Initializing bulk history ingestion...")
    exchange = ccxt.kraken()
    
    try:
        # Load active futures contracts dynamically from Kraken
        print("Fetching active futures markets from Kraken...")
        markets = exchange.load_markets()
        futures_symbols = [symbol for symbol, market in markets.items() if market.get('linear') or market.get('inverse')]
        
        # We only keep unique active contracts (e.g. perpetuals ending in USD or EUR)
        active_perps = [x for x in futures_symbols if 'USD' in x or 'EUR' in x]
        print(f"Detected {len(active_perps)} active perpetual contracts: {active_perps}")
        
        print("\nStarting ingestion in sequential, rate-limited background mode (con metodo e calma)...")
        for symbol in active_perps:
            try:
                # Ingest 365 days of 1-minute candles calmly
                ingest_contract_history(symbol, timeframe="1m", days=365)
                
                # Settle delay between symbols (10 seconds sleep)
                print(f"Sleeping 10 seconds before next symbol to let API cooldown...")
                time.sleep(10.0)
            except Exception as e:
                print(f"Error ingesting symbol {symbol}: {e}. Skipping to next...")
                
    except Exception as e:
        print(f"Bulk Ingestion Error: {e}")

if __name__ == '__main__':
    run_bulk()
