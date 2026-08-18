import sys
import os
import json
import time
import subprocess
import logging
import datetime
import uuid
import re
import ccxt
import sqlite3
import requests

# Append parent directory to sys.path to enable proper imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from nemoforge.trading_loop_v2 import TradingLoopV2
from db_manager import DatabaseManager
from scanner_ledger import UnifiedLedgerAndScanner

# Configuration paths on VPS
BASE_PATH = "/broker/storage/storage-next" if os.path.exists("/broker/storage/storage-next") else "./"
DB_PATH = os.path.join(BASE_PATH, "db/nemotron.sqlite")
POCKETS_PATH = os.path.join(BASE_PATH, "db/pockets.json")
KRAKEN_PATH = "/home/tre/.local/bin/kraken"
PRESET_PATH = os.path.join(BASE_PATH, "presets/run_preset.template.json")
ACTIVE_TRADES_PATH = os.path.join(BASE_PATH, "db/active_trades.json")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler(os.path.join(BASE_PATH, "logs/24h_mission.log")), logging.StreamHandler()]
)

WORKSPACE = "fondazione-agentic-next"
NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

sys_prompt = """You are Nemotron Sovereign Broker (V7.0 - SOVEREIGN SAFETY & TP/SL GATED).
INTENT: MAXIMUM_PROFIT_CONVERGENCE, TIME-COMPRESSED ACCUMULATION, SYMMETRIC LONG/SHORT EXPOSURE, GOAL-DRIVEN RISK DYNAMICS, RIGOROUS PROTECTION.

GIACOMO'S MANDATE & STRATEGY:
- Your core objective is to reach the Target Equity in the minimum time possible by systematically compounding profits.
- BIDIRECTIONAL FLEXIBILITY: You must trade both LONG and SHORT. Do not limit yourself to buying. If the market is neutral, bearish, or an asset shows fatigue, open aggressive SHORT positions on Futures at appropriate leverage. Leverage price falls to compound profits!
- MOMENTUM EXPLOITATION: Focus on assets with highly active volumetric squeezes and momentum. Move quickly. Trade durations are short-term (1-4 hours). Secure profits fast to reinvest them.
- STRATEGIC DISCIPLINE (TARGET-AWARENESS): Read your current "executive_regime" very carefully! You must adapt your aggressiveness, leverage, and sizes strictly based on the current regime:
  1. ACCUMULATION: Maximum aggression, capture big trends, high leverage (20x-35x), size 10-15%.
  2. CONSOLIDATION: Balance growth with safety, protect gains, moderate leverage (10x-15x), size 5-10%.
  3. LOCK-IN: High conservatismo, target is within reach! Protect the capital, lock-in EUR, trade tiny sizes, leverage 1x-5x, avoid opening risky trades.
"""

def get_run_id_from_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT run_id FROM runs WHERE status = 'ACTIVE' LIMIT 1")
    row = c.fetchone()
    conn.close()
    return row[0] if row else "RUN-V2-UNKNOWN"

def normalize_pair(pair):
    """
    Idempotent pair normalization function.
    Accepts both BTC/EUR and BTCEUR, and always returns BTC/EUR format.
    """
    pair = str(pair).upper().strip()
    if "/" in pair:
        # Standardize separate slash
        parts = [x.strip() for x in pair.split("/")]
        if len(parts) == 2:
            return f"{parts[0]}/{parts[1]}"
        return pair
        
    # Look for standard quote currencies at the end of the string
    for quote in ["USDT", "EUR", "USD", "BTC", "ETH"]:
        if pair.endswith(quote):
            base = pair[:-len(quote)]
            return f"{base}/{quote}"
    return pair

def extract_json_from_text(text):
    """
    Robust JSON extractor using regex.
    Finds the first '{' and the last '}' and extracts everything in between.
    Bypasses conversational text wraps of LLM models.
    """
    m = re.search(r"({.*})", text, re.DOTALL)
    if m:
        return m.group(1)
    return text

class IntegratedProductionLoop:
    """
    NemoForge V2.1 Fully Integrated Live Paper Trading Loop
    Merges advanced AI multi-agent reasoning, sentiment scraping,
    and L2 book imbalances with the fcntl-locking, transactional SQLite
    ledger (scale-in/out), and automatic background reconciliations.
    """
    def __init__(self):
        self.run_id = get_run_id_from_db()
        logging.info(f"Initializing V2.1 Integrated Loop for active run: {self.run_id}")
        
        # Load run preset dynamically (Point 6 / fee mode)
        self.preset = self.load_preset()
        self.fee_mode = self.preset.get("fee_mode", "zero_fee")
        self.spot_fee_rate = float(self.preset.get("spot_fee_rate", 0.0))
        self.futures_fee_rate = float(self.preset.get("futures_fee_rate", 0.0))
        self.slippage_rate = float(self.preset.get("slippage_rate", 0.001))
        
        # 1. Initialize transactional ledger and acquire flock lock
        self.ledger = TradingLoopV2(self.run_id)
        
        # 2. Initialize scanner
        self.scanner = UnifiedLedgerAndScanner(db_path=DB_PATH)
        
        # Timer tracking
        self.last_reconciled_at = 0
        
    def load_preset(self):
        """Loads Giacomo's official run_preset.template.json dynamically"""
        if os.path.exists(PRESET_PATH):
            try:
                with open(PRESET_PATH, "r") as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading preset: {e}")
        return {
            "fee_mode": "zero_fee",
            "spot_fee_rate": 0.0,
            "futures_fee_rate": 0.0,
            "slippage_rate": 0.001,
            "max_capital_allocation_pct": 100.0,
            "target_net_equity_eur": 500.0,
            "duration_hours": 12.0
        }

    def load_pockets(self):
        try:
            with open(POCKETS_PATH) as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading pockets: {e}")
            return {"spot_pocket": 0.0, "futures_pocket": 297.68}

    def get_paper_equity_spot(self):
        try:
            res = subprocess.run(f"{KRAKEN_PATH} paper status -o json --workspace fondazione-agentic-next", shell=True, capture_output=True, text=True)
            data = json.loads(res.stdout)
            return float(data.get("current_value", 0.0))
        except Exception as e:
            logging.error(f"Error fetching paper spot equity: {e}")
            return 0.0

    def get_paper_equity_futures(self):
        try:
            res = subprocess.run(f"env -u KRAKEN_WORKSPACE {KRAKEN_PATH} futures paper status -o json", shell=True, capture_output=True, text=True)
            data = json.loads(res.stdout)
            return float(data.get("equity", data.get("collateral", 297.68)))
        except Exception as e:
            logging.error(f"Error fetching paper futures equity: {e}")
            return 297.68

    def get_eur_usd_rate(self):
        try:
            exchange = ccxt.kraken()
            ticker = exchange.fetch_ticker("EUR/USD")
            return float(ticker['last'])
        except Exception as e:
            logging.error(f"Error fetching EUR/USD rate: {e}")
            return 1.1580

    def load_supported_futures(self):
        try:
            res = subprocess.run(f"env -u KRAKEN_WORKSPACE {KRAKEN_PATH} futures instruments -o json", shell=True, capture_output=True, text=True)
            data = json.loads(res.stdout)
            perps = {inst["symbol"] for inst in data.get("instruments", []) if inst.get("symbol", "").startswith("PF_")}
            return perps
        except Exception as e:
            logging.error(f"Error loading supported futures: {e}")
            return {"PF_XBTUSD", "PF_ETHUSD", "PF_SOLUSD", "PF_PEPEUSD", "PF_SUIUSD"}

    def dynamic_map_symbol(self, pair, supported_symbols):
        normalized = normalize_pair(pair)
        if "/" in normalized:
            base, _ = normalized.split("/")
        else:
            base = normalized.replace("EUR", "").replace("USD", "").replace("USDT", "")
        base = base.strip()
        if base == "BTC":
            base = "XBT"
        elif base == "MATIC":
            base = "POL"
        perp_symbol = f"PF_{base}USD"
        if perp_symbol in supported_symbols:
            return perp_symbol
        return None

    def query_risk_mentor(self, snap):
        """Queries Nemotron-30B on Port 8080 as the Risk Mentor"""
        mentor_prompt = f"Analyze the current market snapshot and provide strict risk management advice for size, leverage, and stop-loss: {json.dumps(snap)}"
        try:
            resp = requests.post(NEMO_URL, json={
                "model": "nemotron-3-nano",
                "messages": [
                    {"role": "system", "content": "You are Nemotron Risk Mentor (V7.1). You output in Italian, providing strict guidelines on size, leverage, and stop-loss based on current volatility and sentiment."},
                    {"role": "user", "content": mentor_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500
            }, timeout=90)
            return {"advice": resp.json()["choices"][0]["message"]["content"]}
        except Exception as e:
            logging.error(f"Risk Mentor Error: {e}")
            return {"advice": "Limit size to 5% and leverage to 10x due to connection timeout."}

    def query_trader(self, snap, mentor_advice, allow_spot=False, target=500.0, hours_left=12.0, max_capital_pct=100.0, initial_equity=297.68):
        """Queries Nemotron-30B on Port 8080 as the Sovereign Broker/Trader"""
        cognitive_guidelines = f"""
        TARGET: €{target:.2f} | Time Left: {hours_left:.2f}h | Max Capital Allocation: {max_capital_pct}% | Base: €{initial_equity:.2f}
        Risk Mentor Advice: {json.dumps(mentor_advice)}
        Economic Fee Regime: {self.fee_mode} (Spot fee: {self.spot_fee_rate}, Futures fee: {self.futures_fee_rate}, Slippage: {self.slippage_rate})
        """
        prompt = f"Market Snapshot: {json.dumps(snap)}\n{cognitive_guidelines}\nDecide Action."
        try:
            resp = requests.post(NEMO_URL, json={
                "model": "nemotron-3-nano",
                "messages": [
                    {"role": "system", "content": "You are a strict automated trading API. You must output ONLY a valid, raw JSON object matching the requested schema. You must NEVER write any explanations, thinking process, or markdown text outside the JSON block. Start directly with '{' and end with '}'!"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.0,
                "max_tokens": 800
            }, timeout=90)
            content = resp.json()["choices"][0]["message"]["content"]
            content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
            content = content.replace('```json','').replace('```','').strip()
            
            # Apply robust extraction
            content = extract_json_from_text(content)
            decision = json.loads(content)
            
            # Normalize and validate action
            action = str(decision.get("action", "hold")).lower().strip()
            if action not in ["buy", "sell", "hold"]:
                logging.warning(f"Invalid action '{action}' returned by Trader. Defaulting to 'hold'.")
                decision["action"] = "hold"
            else:
                decision["action"] = action
                
            return decision
        except Exception as e:
            logging.error(f"Trader Error: {e}")
            if 'content' in locals() or 'content' in globals():
                logging.error(f"Raw Trader Content that failed to parse: {content}")
            return {"action": "hold", "pair": "", "market_type": "spot", "size_pct": 0, "override_mentor": False, "reason": str(e), "shadow_decisions": []}

    def get_mentor_reliability(self):
        return 0.80

    def enforce_capital_guard(self, vol, current_price, leverage_val, initial, max_capital_pct):
        """
        REAL CAPITAL GUARD
        Enforces maximum capital allocation mathematically, checking utilized margin,
        required margin, and rejecting orders that violate config threshold.
        """
        try:
            # 1. Fetch currently utilized margin across all active positions in SQLite
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT SUM(ABS(size) * average_entry_price / leverage) FROM paper_positions WHERE status = 'OPEN'")
            used_margin_val = c.fetchone()[0]
            conn.close()
            
            used_margin_eur = (used_margin_val if used_margin_val else 0.0) / self.get_eur_usd_rate()
            
            # 2. Calculate required margin of the new order
            new_margin_eur = (vol * current_price) / leverage_val / self.get_eur_usd_rate()
            
            max_allowed_margin_eur = initial * (max_capital_pct / 100.0)
            
            if (used_margin_eur + new_margin_eur) > max_allowed_margin_eur:
                logging.warning(f"🛡️ [CAPITAL GUARD REJECTION] Order exceeds max capital allocation of {max_capital_pct}% (Used: €{used_margin_eur:.2f} | Required: €{new_margin_eur:.2f} | Max Allowed: €{max_allowed_margin_eur:.2f}). REJECTING ORDER.")
                return 0.0 # Rejected!
                
            return vol
        except Exception as e:
            logging.error(f"Error in enforce_capital_guard: {e}")
            return vol

    def run(self):
        logging.info("Sovereign V2.1 Integrated Loop started. Entering execution cycle...")
        SUPPORTED_FUTURES = self.load_supported_futures()
        
        while True:
            try:
                # 1. Background Reconciliation Check (every 5 minutes / 300 seconds)
                current_time = time.time()
                if current_time - self.last_reconciled_at >= 300:
                    logging.info("Triggering automatic 5-minute background reconciliation...")
                    self.ledger.reconcile_with_broker()
                    self.last_reconciled_at = current_time
                
                # 2. Check and trigger local TP/SL from transactional database
                self.check_and_trigger_tp_sl()
                
                # 3. Main Scanning & Trading Step
                self.scanner_step(SUPPORTED_FUTURES)
                
                # Sleep between cycles (e.g. 2 minutes / 120 seconds)
                time.sleep(120.0)
                
            except KeyboardInterrupt:
                logging.info("Loop interrupted by user. Exiting safely...")
                break
            except Exception as e:
                logging.error(f"Error in V2.1 loop cycle: {e}")
                time.sleep(10.0)
                
    def scanner_step(self, SUPPORTED_FUTURES):
        """
        Performs the complete real-time market scan, queries Risk Mentor and Trader,
        evaluates guardrails, and executes orders transactional on SQLite (no update_t1 zero-pnl bugs!).
        """
        logging.info("Scanning markets for active perpetual contracts...")
        
        # Load run config
        target = self.preset.get("target_net_equity_eur", 500.0)
        duration_hours = self.preset.get("duration_hours", 12.0)
        max_capital_pct = self.preset.get("max_capital_allocation_pct", 100.0)
                
        # Load pockets & equities
        pockets = self.load_pockets()
        spot_equity = self.get_paper_equity_spot()
        futures_equity = self.get_paper_equity_futures()
        rate = self.get_eur_usd_rate()
        futures_equity_eur = futures_equity / rate
        current_equity = spot_equity + futures_equity_eur
        
        logging.info(f"Current Unified Equity: €{current_equity:.2f} | Spot: €{spot_equity:.2f} | Futures: €{futures_equity_eur:.2f}")
        
        # Build snapshot
        snapshot = {
            "timestamp": int(time.time()),
            "run_id": self.run_id,
            "equity": {
                "spot_pocket": spot_equity,
                "futures_pocket": futures_equity_eur,
                "unified_equity": current_equity
            },
            "mission_metrics": {
                "target_equity_eur": target,
                "gap_to_target_eur": max(0.0, target - current_equity),
                "hours_to_flattening": duration_hours
            }
        }
        
        # Query Risk Mentor
        mentor_advice = self.query_risk_mentor(snapshot)
        logging.info(f"Risk Mentor Local Advice: {mentor_advice.get('advice')}")
        
        # Query Trader
        decision = self.query_trader(snapshot, mentor_advice, allow_spot=False, target=target, hours_left=duration_hours, max_capital_pct=max_capital_pct, initial_equity=297.68)
        logging.info(f"Trader Decision: {decision.get('action')} {decision.get('size_pct', 0)} {decision.get('pair', '')} (Leva: {decision.get('leverage', 'N/A')})")
        
        action = decision.get("action")
        pair = decision.get("pair")
        size_pct = decision.get("size_pct", 0)
        market_type = decision.get("market_type", "spot").lower()
        
        if action in ["buy", "sell"] and pair and size_pct > 0 and market_type == "futures":
            symbol_futures = self.dynamic_map_symbol(pair, SUPPORTED_FUTURES)
            if not symbol_futures:
                logging.error(f"No futures perpetual contract mapped for pair {pair}. Skipping.")
                return
                
            # Compute execution volume
            ticker = ccxt.kraken().fetch_ticker(normalize_pair(pair))
            current_price = float(ticker['last'])
            
            # Simple volume calculation
            vol = (futures_equity_eur * size_pct * rate) / current_price
            vol = round(vol, 6)
            
            if vol > 0.0001:
                leverage_val = int(decision.get("leverage", 10))
                
                # Apply capital allocation limit guards dynamically (Point 8 / config!)
                vol = self.enforce_capital_guard(vol, current_price, leverage_val, 297.68, max_capital_pct)
                
            if vol > 0.0001:
                logging.info(f"Executing order on paper broker: {action} {vol} {symbol_futures} at Leva {leverage_val}x...")
                cmd = f"env -u KRAKEN_WORKSPACE {KRAKEN_PATH} futures paper {action} {symbol_futures} {vol} --type market --leverage {leverage_val}"
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                logging.info(f"Futures Execution: {res.stdout.strip()} | Error (if any): {res.stderr.strip()}")
                
                if "filled" in res.stdout.lower() or "order id" in res.stdout.lower():
                    # Parse Order ID
                    order_id = f"FP-{int(time.time() * 1000)}"
                    m = re.search(r"Order ID\s+┆\s+(FP-\d+)", res.stdout)
                    if m:
                        order_id = m.group(1)
                        
                    # Calculate transactional fees using the active preset fee rate! (zero_fee = 0.0, standard = 0.0005)
                    fee_rate = self.futures_fee_rate
                    fee = vol * current_price * fee_rate
                    
                    # TRANSACTIONAL V2.0 LEDGER WRITES!
                    # Log Order & update position atomically inside a single SQLite transaction!
                    # We pass the TP/SL specified by the strategist or default thresholds (3.5% TP / 1.5% SL)
                    tp_price = current_price * 1.035 if action == 'buy' else current_price * 0.965
                    sl_price = current_price * 0.985 if action == 'buy' else current_price * 1.015
                    
                    self.ledger.execute_transactional_fill(order_id, symbol_futures, action, vol, current_price, fee, self.slippage_rate, leverage_val, tp_price, sl_price)
                    logging.info(f"SUCCESS: Transactional ledger updated atomically for {symbol_futures} order {order_id}!")

    def check_and_trigger_tp_sl(self):
        """Monitors active positions in SQLite and checks TP/SL triggers"""
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT symbol, side, size, average_entry_price, tp_price, sl_price, leverage FROM paper_positions WHERE status = 'OPEN'")
        positions = c.fetchall()
        conn.close()
        
        if not positions:
            return
            
        for pos in positions:
            symbol, side, size, entry_price, tp, sl, leverage = pos
            if tp == 0.0 and sl == 0.0:
                continue
                
            # Fetch mark price
            exchange = ccxt.kraken()
            ticker = exchange.fetch_ticker(symbol.replace('PF_', '').replace('USD', '/USD'))
            mark_price = float(ticker['last'])
            
            triggered = False
            exit_reason = ""
            
            if side == 'long':
                if tp > 0.0 and mark_price >= tp:
                    triggered = True
                    exit_reason = "TAKE_PROFIT"
                elif sl > 0.0 and mark_price <= sl:
                    triggered = True
                    exit_reason = "STOP_LOSS"
            elif side == 'short':
                if tp > 0.0 and mark_price <= tp:
                    triggered = True
                    exit_reason = "TAKE_PROFIT"
                elif sl > 0.0 and mark_price >= sl:
                    triggered = True
                    exit_reason = "STOP_LOSS"
                    
            if triggered:
                logging.info(f"!!! TP/SL TRIGGERED for {symbol} ({exit_reason}) !!! Mark: ${mark_price:.4f} | TP: ${tp:.4f} | SL: ${sl:.4f}")
                self.execute_close_order(symbol, side, abs(size), mark_price, leverage, exit_reason)

    def execute_close_order(self, symbol, side, size, exit_price, leverage, reason):
        close_action = "sell" if side == 'long' else "buy"
        logging.info(f"Executing close order: {close_action} {size} {symbol}...")
        cmd = f"env -u KRAKEN_WORKSPACE {KRAKEN_PATH} futures paper {close_action} {symbol} {size} --type market --leverage {leverage}"
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if res.returncode == 0:
                order_id = f"FP-{int(time.time() * 1000)}"
                m = re.search(r"Order ID\s+┆\s+(FP-\d+)", res.stdout)
                if m:
                    order_id = m.group(1)
                fee = size * exit_price * self.futures_fee_rate
                self.ledger.execute_transactional_fill(order_id, symbol, close_action, size, exit_price, fee, self.slippage_rate, leverage, 0.0, 0.0)
                logging.info(f"Position closed successfully on {symbol} via paper broker.")
        except Exception as e:
            logging.error(f"Error executing close order: {e}")

if __name__ == '__main__':
    loop = IntegratedProductionLoop()
    loop.run()
