import ccxt
import json

with open('/broker/storage/shared/config/api_vault.json') as f:
    vault = json.load(f)

print("Checking CCXT Spot and Futures balances...")

# Spot
try:
    spot = ccxt.kraken({
        'apiKey': vault['KRAKEN_PAPER_SPOT_KEY'],
        'secret': vault['KRAKEN_PAPER_SPOT_SECRET'],
    })
    # spot.set_sandbox_mode(True)
    spot_bal = spot.fetch_balance()
    print("Spot EUR Balance:", spot_bal.get('EUR', {}).get('total', 0.0))
except Exception as e:
    print("Spot balance error:", e)

# Futures
try:
    futures = ccxt.krakenfutures({
        'apiKey': vault['KRAKEN_PAPER_FUTURES_KEY'],
        'secret': vault['KRAKEN_PAPER_FUTURES_SECRET'],
    })
    # futures.set_sandbox_mode(True)
    fut_bal = futures.fetch_balance()
    print("Futures EUR Balance:", fut_bal.get('EUR', {}).get('total', 0.0))
    print("Full Futures balance keys:", list(fut_bal.keys()) if fut_bal else "None")
except Exception as e:
    print("Futures balance error:", e)
