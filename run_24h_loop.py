import asyncio
import time
import uuid
import json
import logging
import requests
import subprocess
import os
os.environ["HOME"] = "/broker/storage/storage-next"
os.environ.pop("KRAKEN_WORKSPACE", None) # Explicitly clear workspace env to prevent Futures validation errors!
from db_manager import DatabaseManager
from scanner_ledger import UnifiedLedgerAndScanner

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler("/broker/storage/storage-next/logs/24h_mission.log"), logging.StreamHandler()]
)

SHADOW_FUTURES_MODE = False # Set to False when promoted to primary loop!

WORKSPACE = "fondazione-agentic-next"
NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"
MENTOR_URL = "http://100.73.54.72:8081/v1/chat/completions"
KRAKEN_PATH = "/home/tre/.local/bin/kraken"
POCKETS_PATH = "/broker/storage/storage-next/db/pockets.json"

sys_prompt = """You are Nemotron Sovereign Broker (V5.0 - DYNAMIC MULTI-ASSET 24H MISSION).
INTENT: EXTREME_AGGRESSION, MAXIMUM_PROFIT_24H, TOTAL_DIVERSIFICATION, DYNAMIC_LEVERAGE.

GIACOMO'S MANDATE & AWARENESS: 
- You are starting a BRAND NEW 24-HOUR RUN from zero history. Your previous runs are completely wiped and flattened.
- Your starting capital is exactly €297.68 (Spot wallet: €149.18 | Futures wallet: €148.50).
- Your ONLY goal is to generate the MAXIMUM possible profit in 24 hours. There are no conservative targets or profit caps.
- TOTAL DIVERSIFICATION: You are connected to a Dynamic Mapping Engine with access to the ENTIRE Kraken Futures market (over 270+ active linear perpetuals, including top alts, DeFi tokens, memecoins, and synthetic stock trackers like NVIDIA or Tesla!). DIVERSIFY your trades across different assets based on momentum. Do not concentrate all your funds on a single asset unless you have extreme conviction!
- DYNAMIC LEVERAGE MANAGEMENT: You have total freedom on leverage (from 1x to 50x). Choose your leverage wisely! Be aware that very high leverage (like 50x) has a narrow tolerance band (less than 1% price move can liquidate you). Balance aggressiveness with survival to maximize profits!

HOW TO TRADE FUTURES:
Simply output any standard pair (e.g. "BTC/EUR", "SUI/EUR", "AVAX/USD", "PEPE/EUR", "AAVE/EUR", "NVDA/USD") and set market_type to "futures". The execution engine will dynamically map it to the correct Kraken perpetual contract (e.g. PF_XBTUSD, PF_SUIUSD, PF_AVAXUSD, PF_PEPEUSD, PF_AAVEUSD, PF_NVDAXUSD) in real-time.

Output strictly JSON: 
{
  "action": "buy|sell|hold", 
  "pair": "SUI/EUR", 
  "market_type": "spot|futures", 
  "size_pct": 0.2, 
  "leverage": 20, // For futures trades, select any leverage from 1 to 50. Total freedom!
  "override_mentor": false, 
  "reason": "...",
  "shadow_decisions": [
     {"action": "sell", "pair": "AVAX/EUR", "market_type": "futures", "size_pct": 0.1, "leverage": 15, "reason": "alternative momentum short"}
  ]
}
Do not use markdown. Only raw JSON."""

db = DatabaseManager("/broker/storage/storage-next/db/nemotron.sqlite")
scanner = UnifiedLedgerAndScanner()

def load_pockets():
    try:
        with open(POCKETS_PATH) as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading pockets: {e}")
        return {"spot_pocket": 149.18, "futures_pocket": 148.50}

def save_pockets(pockets):
    try:
        pockets["timestamp"] = int(time.time())
        with open(POCKETS_PATH, "w") as f:
            json.dump(pockets, f, indent=2)
    except Exception as e:
        logging.error(f"Error saving pockets: {e}")

def get_paper_equity_spot():
    try:
        res = subprocess.run(f"{KRAKEN_PATH} paper status -o json --workspace fondazione-agentic", shell=True, capture_output=True, text=True)
        data = json.loads(res.stdout)
        return float(data.get("current_value", 149.18))
    except Exception as e:
        logging.error(f"Error fetching paper spot equity: {e}")
        return 149.18

def get_paper_equity_futures():
    try:
        res = subprocess.run(f"{KRAKEN_PATH} futures paper status -o json", shell=True, capture_output=True, text=True)
        data = json.loads(res.stdout)
        return float(data.get("equity", data.get("collateral", 148.50)))
    except Exception as e:
        logging.error(f"Error fetching paper futures equity: {e}")
        return 148.50

def get_asset_balance_spot(asset):
    try:
        res = subprocess.run(f"{KRAKEN_PATH} paper balance -o json --workspace fondazione-agentic", shell=True, capture_output=True, text=True)
        data = json.loads(res.stdout)
        balances = data.get("balances", {})
        asset_data = balances.get(asset, {})
        return float(asset_data.get("total", 0.0))
    except Exception as e:
        logging.error(f"Error fetching spot balance for {asset}: {e}")
        return 0.0

def get_asset_balance_futures(symbol):
    try:
        res = subprocess.run(f"{KRAKEN_PATH} futures paper positions -o json", shell=True, capture_output=True, text=True)
        positions = json.loads(res.stdout)
        for pos in positions:
            if pos.get("symbol") == symbol:
                return float(pos.get("size", 0.0))
        return 0.0
    except Exception as e:
        logging.error(f"Error fetching futures position for {symbol}: {e}")
        return 0.0

def fetch_price(pair):
    try:
        import ccxt
        exchange = ccxt.kraken()
        ticker = exchange.fetch_ticker(pair)
        return float(ticker['last'])
    except Exception as e:
        logging.error(f"Error fetching price for {pair}: {e}")
        return None

def load_supported_futures():
    try:
        res = subprocess.run(f"{KRAKEN_PATH} futures instruments -o json", shell=True, capture_output=True, text=True)
        data = json.loads(res.stdout)
        perps = {inst["symbol"] for inst in data.get("instruments", []) if inst.get("symbol", "").startswith("PF_")}
        logging.info(f"Loaded {len(perps)} supported linear perpetual contracts dynamically.")
        return perps
    except Exception as e:
        logging.error(f"Error loading supported futures: {e}")
        return {"PF_XBTUSD", "PF_ETHUSD", "PF_SOLUSD", "PF_DOGEUSD", "PF_LINKUSD", "PF_LTCUSD", "PF_XRPUSD"}

def dynamic_map_symbol(pair, supported_symbols):
    pair = pair.upper()
    if "/" in pair:
        base, _ = pair.split("/")
    else:
        base = pair.replace("EUR", "").replace("USD", "").replace("USDT", "")
    
    base = base.strip()
    if base == "BTC":
        base = "XBT"
    elif base == "MATIC":
        base = "POL"
        
    # Check linear perp USD
    perp_symbol = f"PF_{base}USD"
    if perp_symbol in supported_symbols:
        return perp_symbol
        
    # Check linear perp EUR
    perp_eur = f"PF_{base}EUR"
    if perp_eur in supported_symbols:
        return perp_eur
        
    # Check if pair itself is supported
    if pair in supported_symbols:
        return pair
        
    return None

def flatten_portfolio():
    logging.info("!!! FLATTENING DEADLINE REACHED. INITIATING FORCE LIQUIDATION !!!")
    
    # 1. Flatten Spot
    try:
        res = subprocess.run(f"{KRAKEN_PATH} paper balance -o json --workspace fondazione-agentic", shell=True, capture_output=True, text=True)
        data = json.loads(res.stdout)
        balances = data.get("balances", {})
        for asset, asset_data in balances.items():
            if asset != "EUR":
                total = float(asset_data.get("total", 0.0))
                if total > 0.001:
                    pair = f"{asset}EUR"
                    logging.info(f"Force selling Spot {total} {asset}...")
                    subprocess.run(f"{KRAKEN_PATH} paper sell {pair} {total} --workspace {WORKSPACE}", shell=True)
    except Exception as e:
        logging.error(f"Error during Spot flattening: {e}")
        
    # 2. Flatten Futures
    try:
        res = subprocess.run(f"{KRAKEN_PATH} futures paper positions -o json", shell=True, capture_output=True, text=True)
        data = json.loads(res.stdout)
        positions_list = data.get("positions", [])
        for pos in positions_list:
            size = float(pos.get("size", 0.0))
            symbol = pos.get("symbol")
            if abs(size) > 0.0001:
                action = "sell" if size > 0 else "buy"
                logging.info(f"Force liquidating Futures position: {action} {abs(size)} {symbol}...")
                subprocess.run(f"{KRAKEN_PATH} futures paper {action} {symbol} {abs(size)} --type market --leverage 20", shell=True)
    except Exception as e:
        logging.error(f"Error during Futures flattening: {e}")
        
    logging.info("All open positions liquidated. Spot & Futures converted to EUR. Paper account is flat.")

def query_risk_mentor(snapshot):
    prompt = f"""You are the local Risk Mentor Agent of the Nemotron Sovereign Broker ecosystem.
Your job is to analyze the current market snapshot, account balances, and volatility, and provide clear, strict, mathematically sound risk-management advice to the Sovereign Trader.

Guidelines:
1. Advise on maximum size percentage (size_pct) to use (e.g. recommend 0.05 to 0.20 depending on volatility, do not recommend going all-in).
2. Recommend conservative leverage caps. High leverage (like 30x-50x) on highly volatile altcoins is suicidal because any tiny 1-2% retracement triggers liquidation. Recommend safer levels (e.g. 5x to 15x max for volatile alts, 15x to 25x for BTC/ETH).
3. Suggest clear safety stop-losses or parameters.

Market Snapshot: {json.dumps(snapshot)}

Provide your advice concisely in Italian. Be direct, authoritative, and strict! No markdown wrappers other than plain paragraphs."""
    try:
        resp = requests.post(MENTOR_URL, json={
            "model": "/opt/kraken-inference/models/Llama-3.1-8B-Instruct-Q4_K_M.gguf",
            "messages": [
                {"role": "system", "content": "You are the local Risk Mentor Agent of the Nemotron Sovereign Broker ecosystem. Speak in Italian."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 400
        }, timeout=60)
        content = resp.json()["choices"][0]["message"]["content"]
        return {"advice": content.strip()}
    except Exception as e:
        logging.error(f"Error querying Risk Mentor: {e}")
        return {"advice": "Procedere con cautela. Limitare la leva su altcoin volatili a massimo 10x-15x, size contenuta."}

def query_trader(snapshot, mentor_advice):
    prompt = f"Market Snapshot (Target-Aware): {json.dumps(snapshot)}\nRisk Mentor Advice (Istruzioni Vincolanti di Rischio): {json.dumps(mentor_advice)}\nDecide Action."
    try:
        resp = requests.post(NEMO_URL, json={
            "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4,
            "max_tokens": 800
        }, timeout=120)
        
        content = resp.json()["choices"][0]["message"]["content"]
        import re
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        content = content.replace('```json','').replace('```','').strip()
        return json.loads(content)
    except Exception as e:
        logging.error(f"Trader Error: {e}")
        return {"action": "hold", "pair": "", "market_type": "spot", "size_pct": 0, "override_mentor": False, "reason": str(e), "shadow_decisions": []}

async def mission_loop():
    logging.info("Starting 24H MISSION - AGGRESSIVE DUAL-WALLET (SPOT + FUTURES) PAPER TRADING (PROMPT ADVANCED)")
    run = scanner.get_active_run()
    if not run:
        logging.error("No active run found in database. Run bootstrap_24h.py first.")
        return
        
    run_id, initial, target, flat_time = run
    SUPPORTED_FUTURES = load_supported_futures()
    
    while time.time() < flat_time:
        try:
            try:
                spot_equity = get_paper_equity_spot()
                futures_equity = get_paper_equity_futures()
                current_equity = spot_equity + futures_equity
                
                pockets = load_pockets()
                pockets["spot_pocket"] = spot_equity
                pockets["futures_pocket"] = futures_equity
                save_pockets(pockets)
                
                snap = scanner.get_unified_snapshot(current_equity)
                if snap:
                    logging.info(f"Target Gap: €{snap['mission_metrics']['gap_to_target_eur']} | Time Left: {snap['mission_metrics']['hours_to_flattening']}h")
                    logging.info(f"Current Unified Equity: €{current_equity:.2f} | Spot Pocket: €{spot_equity:.2f} | Futures Pocket: €{futures_equity:.2f}")
                    
                    # 1. Query the local Risk Mentor on 8081
                    mentor_advice = query_risk_mentor(snap)
                    logging.info(f"Risk Mentor Local Advice: {mentor_advice.get('advice')}")
                    
                    # 2. Query Nemotron Trader on 8080 with Mentor Advice
                    decision = query_trader(snap, mentor_advice)
                    logging.info(f"Trader Decision: {decision.get('action')} {decision.get('size_pct', 0)} {decision.get('pair', '')} on {decision.get('market_type', 'spot').upper()} (Leva: {decision.get('leverage', 'N/A')})")
                    
                    action = decision.get("action")
                    pair = decision.get("pair")
                    size_pct = decision.get("size_pct", 0)
                    market_type = decision.get("market_type", "spot").lower()
                    
                    if action in ["buy", "sell"] and pair and size_pct > 0:
                        dec_id = f"DEC-{uuid.uuid4().hex[:8]}"
                        pair_kraken = pair.replace("/", "")
                        
                        current_price = fetch_price(pair)
                        if not current_price:
                            logging.error(f"Could not fetch price for {pair}. Skipping trade.")
                            continue
                        
                        if market_type == "spot":
                            vol = 0.0
                            if action == "buy":
                                vol = (spot_equity * size_pct) / current_price
                            elif action == "sell":
                                asset = pair.split("/")[0] if "/" in pair else pair.replace("EUR", "")
                                holding = get_asset_balance_spot(asset)
                                if holding > 0:
                                    vol = holding * size_pct
                                else:
                                    logging.warning(f"No holding of {asset} to sell in Spot Wallet.")
                                    vol = 0.0
                            
                            vol = round(vol, 6)
                            if vol > 0.0001:
                                db.insert_t0({
                                    "decision_id": dec_id,
                                    "timestamp": int(time.time()),
                                    "intent_id": "24H_AGGRESSIVE",
                                    "market_regime": f"SPOT_{action.upper()}",
                                    "market_snapshot": snap,
                                    "mentor_advice": mentor_advice,
                                    "trader_decision": decision,
                                    "action_taken": {**decision, "calculated_volume": vol}
                                })
                                
                                cmd = f"{KRAKEN_PATH} paper {action} {pair_kraken} {vol} --workspace {WORKSPACE}"
                                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                                logging.info(f"Spot Execution: {res.stdout.strip()} | Error (if any): {res.stderr.strip()}")
                                
                                db.update_t1(dec_id, {
                                    "exit_timestamp": int(time.time()),
                                    "pnl_pct": 0.0,
                                    "exit_reason": "executed_paper_24h_spot"
                                })
                        
                        elif market_type == "futures":
                            symbol_futures = dynamic_map_symbol(pair, SUPPORTED_FUTURES)
                            if not symbol_futures:
                                logging.error(f"No futures perpetual contract mapped for pair {pair}. Skipping.")
                                continue
                            
                            vol = 0.0
                            if action == "buy":
                                vol = (futures_equity * size_pct) / current_price
                            elif action == "sell":
                                vol = (futures_equity * size_pct) / current_price
                            
                            vol = round(vol, 6)
                            if vol > 0.0001:
                                leverage_val = decision.get("leverage", 20)
                                try:
                                    leverage_val = int(leverage_val)
                                    if leverage_val < 1: leverage_val = 1
                                    if leverage_val > 50: leverage_val = 50
                                except Exception:
                                    leverage_val = 20
                                    
                                db.insert_t0({
                                    "decision_id": dec_id,
                                    "timestamp": int(time.time()),
                                    "intent_id": "24H_AGGRESSIVE",
                                    "market_regime": f"FUTURES_{action.upper()}",
                                    "market_snapshot": snap,
                                    "mentor_advice": mentor_advice,
                                    "trader_decision": decision,
                                    "action_taken": {**decision, "calculated_volume": vol, "mapped_symbol": symbol_futures, "leverage": leverage_val}
                                })
                                
                                if SHADOW_FUTURES_MODE:
                                    logging.info(f"[SHADOW FUTURES] Simulating execution of {action} {vol} {symbol_futures} with leverage {leverage_val}x to avoid global margin collision.")
                                else:
                                    # Fixed: Added --type market to ensure the orders execute instantly and safely!
                                    cmd = f"{KRAKEN_PATH} futures paper {action} {symbol_futures} {vol} --type market --leverage {leverage_val}"
                                    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                                    logging.info(f"Futures Execution: {res.stdout.strip()} | Error (if any): {res.stderr.strip()}")
                                
                                db.update_t1(dec_id, {
                                    "exit_timestamp": int(time.time()),
                                    "pnl_pct": 0.0,
                                    "exit_reason": "executed_paper_24h_futures"
                                })
            except Exception as e:
                logging.error(f"Loop Error: {e}")
        finally:
            await asyncio.sleep(120) # 2 minutes interval

    flatten_portfolio()
    logging.info("MISSION COMPLETE. System Flattened.")

if __name__ == "__main__":
    asyncio.run(mission_loop())
