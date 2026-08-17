import asyncio
import time
import uuid
import json
import logging
import requests
import subprocess
import os
import random
os.environ["HOME"] = "/broker/storage/storage-next"
os.environ["KRAKEN_WORKSPACE"] = "fondazione-agentic-next"
from db_manager import DatabaseManager
from scanner_ledger import UnifiedLedgerAndScanner

def run_futures_cmd(cmd, capture=False):
    # Forziamo l'esclusione di KRAKEN_WORKSPACE direttamente a inizio comando shell per sbloccare i futures paper
    clean_cmd = f"env -u KRAKEN_WORKSPACE {cmd}"
    return subprocess.run(clean_cmd, shell=True, capture_output=capture, text=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler("/broker/storage/storage-next/logs/24h_mission.log"), logging.StreamHandler()]
)

WORKSPACE = "fondazione-agentic-next"
NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"
MENTOR_URL = "http://100.73.54.72:8080/v1/chat/completions"
KRAKEN_PATH = "/home/tre/.local/bin/kraken"
POCKETS_PATH = "/broker/storage/storage-next/db/pockets.json"
ACTIVE_TRADES_PATH = "/broker/storage/storage-next/db/active_trades.json"

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

HOW TO TRADE FUTURES:
Simply output any standard pair (e.g. "BTC/EUR", "SUI/EUR", "AVAX/USD", "PEPE/EUR", "AAVE/EUR", "NVDA/USD") and set market_type to "futures". To SHORT, set "action" to "sell". To LONG, set "action" to "buy". The execution engine will dynamically map it to the correct Kraken perpetual contract in real-time.

Output strictly JSON: 
{
  "action": "buy|sell|hold", 
  "pair": "SUI/EUR", 
  "market_type": "spot|futures", 
  "size_pct": 0.05, // Calibrated based on the active executive_regime
  "leverage": 20, // Select leverage from 1 to 50, strictly following risk guidelines
  "take_profit_pct": 3.5, // Target profit percentage from entry price (e.g. 2.0 to 10.0)
  "stop_loss_pct": 1.5, // Stop-loss threshold percentage from entry price (e.g. 1.0 to 5.0)
  "override_mentor": false, 
  "reason": "...",
  "shadow_decisions": [
     {"action": "sell", "pair": "PEPE/EUR", "market_type": "futures", "size_pct": 0.05, "leverage": 20, "take_profit_pct": 3.5, "stop_loss_pct": 1.5, "reason": "alternative momentum short"}
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
        res = subprocess.run(f"{KRAKEN_PATH} paper status -o json --workspace fondazione-agentic-next", shell=True, capture_output=True, text=True)
        data = json.loads(res.stdout)
        return float(data.get("current_value", 149.18))
    except Exception as e:
        logging.error(f"Error fetching paper spot equity: {e}")
        return 149.18

def get_paper_equity_futures():
    try:
        res = run_futures_cmd(f"{KRAKEN_PATH} futures paper status -o json", capture=True)
        data = json.loads(res.stdout)
        return float(data.get("equity", data.get("collateral", 148.50)))
    except Exception as e:
        logging.error(f"Error fetching paper futures equity: {e}")
        return 148.50

def get_asset_balance_spot(asset):
    try:
        res = subprocess.run(f"{KRAKEN_PATH} paper balance -o json --workspace fondazione-agentic-next", shell=True, capture_output=True, text=True)
        data = json.loads(res.stdout)
        balances = data.get("balances", {})
        asset_data = balances.get(asset, {})
        return float(asset_data.get("total", 0.0))
    except Exception as e:
        logging.error(f"Error fetching spot balance for {asset}: {e}")
        return 0.0

def get_asset_balance_futures(symbol):
    try:
        res = run_futures_cmd(f"{KRAKEN_PATH} futures paper positions -o json", capture=True)
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
        res = subprocess.run(f"{KRAKEN_PATH} paper balance -o json --workspace fondazione-agentic-next", shell=True, capture_output=True, text=True)
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
        res = run_futures_cmd(f"{KRAKEN_PATH} futures paper positions -o json", capture=True)
        data = json.loads(res.stdout)
        positions_list = data.get("positions", [])
        for pos in positions_list:
            size = float(pos.get("size", 0.0))
            symbol = pos.get("symbol")
            side = pos.get("side", "long").lower()
            if abs(size) > 0.0001:
                # Per chiudere un LONG (side == "long"), vendiamo ("sell")
                # Per chiudere uno SHORT (side == "short"), compriamo ("buy")
                action = "sell" if side == "long" else "buy"
                logging.info(f"Force liquidating Futures position: {action} {abs(size)} {symbol} ({side})...")
                run_futures_cmd(f"{KRAKEN_PATH} futures paper {action} {symbol} {abs(size)} --type market --leverage 20")
    except Exception as e:
        logging.error(f"Error during Futures flattening: {e}")
        
    logging.info("All open positions liquidated. Spot & Futures converted to EUR. Paper account is flat.")

def check_and_trigger_tp_sl():
    try:
        if not os.path.exists(ACTIVE_TRADES_PATH):
            return
            
        # 1. Fetch current active positions from the paper broker
        res = run_futures_cmd(f"{KRAKEN_PATH} futures paper positions -o json", capture=True)
        data = json.loads(res.stdout)
        open_positions = data if isinstance(data, list) else data.get("positions", [])
        
        # 2. Load our custom TP/SL registry
        with open(ACTIVE_TRADES_PATH) as f:
            active_trades = json.load(f)
            
        if not active_trades:
            return
            
        # 3. For each open position, check if TP/SL is triggered
        updated_trades = {}
        for pos in open_positions:
            symbol = pos.get("symbol")
            size = abs(float(pos.get("size", 0.0)))
            if size < 0.00001:
                continue
                
            entry_price = float(pos.get("entry", 0.0))
            mark_price = float(pos.get("mark", 0.0))
            side = pos.get("side", "long").lower()
            
            # Check if we have this symbol in our custom TP/SL registry
            trade_config = active_trades.get(symbol, {})
            if not trade_config:
                # If we don't have it, let's keep it in ports without TP/SL or create a default
                updated_trades[symbol] = {
                    "entry_price": entry_price,
                    "side": side,
                    "size": size,
                    "take_profit_pct": 5.0,
                    "stop_loss_pct": 2.0,
                    "decision_id": f"DEC-AUTO-{uuid.uuid4().hex[:6].upper()}"
                }
                continue
                
            tp_pct = float(trade_config.get("take_profit_pct", 5.0))
            sl_pct = float(trade_config.get("stop_loss_pct", 2.0))
            
            triggered = False
            trigger_reason = ""
            pnl_pct = 0.0
            
            if side == "long":
                pnl_pct = (mark_price - entry_price) / entry_price * 100
                if pnl_pct >= tp_pct:
                    triggered = True
                    trigger_reason = f"TAKE_PROFIT (+{pnl_pct:.2f}% >= +{tp_pct:.2f}%)"
                elif pnl_pct <= -sl_pct:
                    triggered = True
                    trigger_reason = f"STOP_LOSS ({pnl_pct:.2f}% <= -{sl_pct:.2f}%)"
            elif side == "short":
                pnl_pct = (entry_price - mark_price) / entry_price * 100
                if pnl_pct >= tp_pct:
                    triggered = True
                    trigger_reason = f"TAKE_PROFIT (+{pnl_pct:.2f}% >= +{tp_pct:.2f}%)"
                elif pnl_pct <= -sl_pct:
                    triggered = True
                    trigger_reason = f"STOP_LOSS ({pnl_pct:.2f}% <= -{sl_pct:.2f}%)"
                    
            if triggered:
                logging.info(f"💥 [LOCAL TP/SL TRIGGERED] {symbol} ({side}) hit {trigger_reason}! Executing immediate close...")
                # Close position
                close_action = "sell" if side == "long" else "buy"
                cmd = f"{KRAKEN_PATH} futures paper {close_action} {symbol} {size} --type market"
                close_res = run_futures_cmd(cmd, capture=True)
                logging.info(f"Closed Position Output: {close_res.stdout.strip()}")
                
                # Save database record T1 for the closed trade
                dec_id = trade_config.get("decision_id")
                if dec_id:
                    db.update_t1(dec_id, {
                        "exit_timestamp": int(time.time()),
                        "pnl_pct": pnl_pct,
                        "exit_reason": f"triggered_{trigger_reason.lower().split()[0]}"
                    })
            else:
                # Keep in our registry
                updated_trades[symbol] = trade_config
                
        # Save updated active trades list
        with open(ACTIVE_TRADES_PATH, "w") as f:
            json.dump(updated_trades, f, indent=2)
    except Exception as e:
        logging.error(f"Error checking local TP/SL: {e}")

_last_mentor_advice = None
_last_mentor_update_time = 0
MENTOR_CACHE_TTL = 900  # Cache TTL di 15 minuti per evitare sovraccarico concorrenza Llama.cpp

def query_risk_mentor(snapshot):
    global _last_mentor_advice, _last_mentor_update_time
    
    current_time = time.time()
    
    # Se abbiamo un consiglio valido memorizzato in cache (TTL non scaduto), lo riutilizziamo direttamente
    if _last_mentor_advice and (current_time - _last_mentor_update_time < MENTOR_CACHE_TTL):
        logging.info("Riutilizzo consiglio Risk Mentor valido recuperato dalla cache locale.")
        return {"advice": _last_mentor_advice}
        
    prompt = f"""You are the local Risk Mentor Agent of the Nemotron Sovereign Broker ecosystem.
Your job is to analyze the current market snapshot, account balances, and volatility, and provide clear, strict, mathematically sound risk-management advice to the Sovereign Trader.

Guidelines:
1. Advise on maximum size percentage (size_pct) to use (e.g. recommend 0.05 to 0.20 depending on volatility, do not recommend going all-in).
2. Recommend conservative leverage caps. High leverage (like 30x-50x) on highly volatile altcoins is suicidal because any tiny 1-2% retracement triggers liquidation. Recommend safer levels (e.g. 5x to 15x max for volatile alts, 15x to 25x for BTC/ETH).
3. Suggest clear safety stop-losses or parameters.

Market Snapshot: {json.dumps(snapshot)}

Provide your advice concisely in Italian. Be direct, authoritative, and strict! No markdown wrappers other than plain paragraphs."""
    
    max_retries = 3
    base_delay = 3.0
    
    for attempt in range(max_retries):
        try:
            if attempt > 0:
                sleep_time = (base_delay ** attempt) + (random.random() * 2)
                logging.info(f"Tentativo {attempt + 1}/{max_retries} al Risk Mentor dopo un ritardo di {sleep_time:.2f}s...")
                time.sleep(sleep_time)
                
            resp = requests.post(MENTOR_URL, json={
                "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
                "messages": [
                    {"role": "system", "content": "You are the local Risk Mentor Agent of the Nemotron Sovereign Broker ecosystem. Speak in Italian."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 400
            }, timeout=90)  # Timeout sintonizzato a 90s per V6.3
            
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"].strip()
            
            # Aggiornamento cache
            _last_mentor_advice = content
            _last_mentor_update_time = current_time
            return {"advice": content}
            
        except Exception as e:
            logging.error(f"Errore query Risk Mentor (Tentativo {attempt + 1}/{max_retries}): {e}")
            
    # Se tutti i tentativi falliscono ma abbiamo un consiglio in cache (anche se scaduto!), ripristiniamo quello
    if _last_mentor_advice:
        logging.warning("Query Risk Mentor fallita. Ripristino consiglio precedente valido memorizzato in cache.")
        return {"advice": _last_mentor_advice}
        
    return {"advice": "Procedere con cautela. Limitare la leva su altcoin volatili a massimo 10x-15x, size contenuta."}

def get_recent_trades_context(db_path, limit=5):
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT timestamp, action_taken, outcome_pnl_pct, exit_reason 
            FROM episodic_memory 
            WHERE exit_reason IS NOT NULL AND exit_reason != ''
            ORDER BY timestamp DESC LIMIT ?
        """, (limit,))
        rows = c.fetchall()
        conn.close()
        
        if not rows:
            return "MEMORIA EPISODICA RECENTE:\nNessun trade precedente registrato. Procedi con le regole base.\n"
            
        context = "MEMORIA EPISODICA RECENTE (STORICO RECENTE DEI TUOI TRADE CON ESITI):\n"
        for r in rows:
            try:
                act = json.loads(r["action_taken"])
                pnl = r["outcome_pnl_pct"]
                reason = r["exit_reason"]
                context += f"- Trade su {act.get('pair')}: {act.get('action').upper()} ({act.get('market_type')}) con Leva {act.get('leverage', 'N/A')}. Esito: PnL {pnl}% (Chiusura per: {reason}). Rationale iniziale: {act.get('reason')}\n"
            except Exception:
                continue
        return context + "\n"
    except Exception as e:
        logging.error(f"Errore caricamento memoria episodica: {e}")
        return "MEMORIA EPISODICA RECENTE: Errore caricamento.\n"

def run_self_reflection(db_path):
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("""
            SELECT timestamp, action_taken, outcome_pnl_pct, exit_reason 
            FROM episodic_memory 
            WHERE exit_reason IS NOT NULL AND exit_reason != ''
            ORDER BY timestamp DESC LIMIT 10
        """)
        rows = c.fetchall()
        conn.close()
        
        if not rows or len(rows) < 3:
            logging.info("Nessun trade sufficiente per far partire la Self-Reflection (richiesti almeno 3 trade).")
            return
            
        history = []
        for r in rows:
            try:
                act = json.loads(r["action_taken"])
                history.append({
                    "pair": act.get("pair"),
                    "action": act.get("action"),
                    "leverage": act.get("leverage"),
                    "pnl_pct": r["outcome_pnl_pct"],
                    "exit_reason": r["exit_reason"]
                })
            except Exception:
                continue
                
        prompt = f"""You are the Self-Reflection Engine of our AI Trading System.
Analyze our recent trade performance history:
{json.dumps(history, indent=2)}

Identify mistakes (such as overleveraging, poor timing, or repetitive losses on volatile alts) and wins.
Write exactly 3 strict, direct, and actionable trading guardrails in Italian for our Sovereign Trader to follow to avoid losses.
Be concise. Do not write markdown, headers, or any fluff. Just output the 3 rules."""
        
        resp = requests.post(NEMO_URL, json={
            "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
            "messages": [
                {"role": "system", "content": "You are a quantitative risk and self-reflection agent. Speak in Italian."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 400
        }, timeout=60)
        
        content = resp.json()["choices"][0]["message"]["content"].strip()
        import re
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        
        guardrails_path = "/broker/storage/storage-next/db/dynamic_guardrails.txt"
        with open(guardrails_path, "w") as f:
            f.write(content)
            
        logging.info(f"Riflessione periodica eseguita. Nuovi Guardrails Dinamici salvati:\n{content}")
    except Exception as e:
        logging.error(f"Errore durante l'esecuzione della Self-Reflection: {e}")

def load_dynamic_guardrails():
    path = "/broker/storage/storage-next/db/dynamic_guardrails.txt"
    try:
        if os.path.exists(path):
            with open(path) as f:
                content = f.read().strip()
                if content:
                    return f"GUARDRAILS DINAMICI (GENERATI DA AUTO-RIFLESSIONE SUI TRADE PRECEDENTI):\n{content}\n\n"
        return "GUARDRAILS DINAMICI:\nNessuna riflessione precedente disponibile. Opera con prudenza.\n\n"
    except Exception:
        return "GUARDRAILS DINAMICI:\nNessuna riflessione precedente disponibile. Opera con prudenza.\n\n"

def get_mentor_reliability(db_path):
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute("SELECT accuracy_rate FROM scorecards WHERE entity_id = 'mentor' LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row and row[0] is not None:
            return float(row[0])
        return 0.8  # Default se mancano record
    except Exception:
        return 0.8

def query_trader(snapshot, mentor_advice, db_path, allow_spot=True):
    # Pilastro 1: Memoria Episodica SQL
    episodic_context = get_recent_trades_context(db_path, limit=5)
    
    # Pilastro 2: Guardrails Dinamici caricati da file
    dynamic_guardrails = load_dynamic_guardrails()
    
    # Pilastro 3: Affidabilità storica Mentore
    reliability = get_mentor_reliability(db_path)
    mentor_reliability_str = f"AFFIDABILITÀ STORICA RISK MENTOR: {reliability * 100:.1f}%\n"
    
    # V6.2: Restrizione hardware sul budget Spot
    spot_restriction_str = ""
    if not allow_spot:
        spot_restriction_str = "⚠️ RESTRIZIONE HARDWARE CRITICA: Lo Spot Wallet ha BUDGET ZERO ed è completamente DISABILITATO. Non sei autorizzato a compiere alcuna operazione di tipo 'spot' (buy/sell). Puoi operare ESCLUSIVAMENTE sui Futures perpetui. Imposta sempre 'market_type': 'futures'.\n\n"
        
    prompt = f"""{spot_restriction_str}{episodic_context}
{dynamic_guardrails}
{mentor_reliability_str}
Market Snapshot (Target-Aware): {json.dumps(snapshot)}
Risk Mentor Advice (Istruzioni Vincolanti di Rischio): {json.dumps(mentor_advice)}

Decide Action."""
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
    
    # V6.2: Leggiamo l'esatto pockets iniziale registrato in pockets.json (cassa reale caricata dal bootstrapper via API)
    initial_pockets = load_pockets()
    initial_spot = float(initial_pockets.get("spot_pocket", 0.0))
    initial_futures = float(initial_pockets.get("futures_pocket", 0.0))
    
    # Blocco hardware a monte se la cassa iniziale è zero
    allow_spot = initial_spot > 0.0
    allow_futures = initial_futures > 0.0
    
    logging.info(f"V6.2 Budget Alignment - Spot Abilitato: {allow_spot} (Cassa Iniziale: €{initial_spot:.2f}) | Futures Abilitato: {allow_futures} (Cassa Iniziale: €{initial_futures:.2f})")
    
    loop_counter = 0
    while time.time() < flat_time:
        try:
            try:
                # Eseguiamo l'auto-riflessione periodica ogni 10 cicli (circa ogni 20 minuti) per sintonizzare i guardrails (Pilastro 2)
                if loop_counter % 10 == 0:
                    run_self_reflection(db.db_path)
                loop_counter += 1
                
                # Se un mercato ha cassa zero, l'equity corrente è forzatamente a zero (V6.2)
                spot_equity = get_paper_equity_spot() if allow_spot else 0.0
                futures_equity = get_paper_equity_futures() if allow_futures else 0.0
                current_equity = spot_equity + futures_equity
                
                # V7.0 Safety Stop-Out (Autoliquidation) check
                stop_out_threshold = initial * 0.80  # Max 20% drawdown of the run
                if current_equity < stop_out_threshold:
                    logging.critical(f"🚨 [SAFETY STOP-OUT TRIGGERED] Unified equity €{current_equity:.2f} fell below stop-out threshold €{stop_out_threshold:.2f} (-20% from initial €{initial:.2f})! INITIATING EMERGENCY TOTAL LIQUIDATION!")
                    flatten_portfolio()
                    # Mark the run as STOPPED in the DB
                    import sqlite3
                    conn = sqlite3.connect(db.db_path)
                    conn.execute("UPDATE runs SET status = 'STOPPED' WHERE run_id = ?", (run_id,))
                    conn.commit()
                    conn.close()
                    logging.info("System is flat and safe. Stopping loop.")
                    break
                    
                # V7.0 Local TP/SL Monitoring Check
                if allow_futures:
                    check_and_trigger_tp_sl()
                    # Recalculate futures equity and current equity after potential closures
                    futures_equity = get_paper_equity_futures()
                    current_equity = spot_equity + futures_equity
                
                # Aggiorniamo pockets mantenendo lo Spot a zero se non finanziato
                pockets = load_pockets()
                pockets["spot_pocket"] = spot_equity
                pockets["futures_pocket"] = futures_equity
                save_pockets(pockets)
                
                snap = scanner.get_unified_snapshot(current_equity)
                if snap:
                    # Calcolo dinamico della distanza percentuale dal target per il regime strategico (V6.1)
                    distance_pct = (target - current_equity) / target * 100
                    
                    if distance_pct > 10.0 or current_equity < initial:
                        regime = "ACCUMULATION (Aggressività: Estrema | Obiettivo: Incremento rapido del capitale | Leva Consigliata: 20x-35x | Size Consigliata: 10-15% | Azioni: Cerca forti breakout di momentum, sia Long che Short)"
                    elif distance_pct >= 2.0:
                        regime = "CONSOLIDATION (Aggressività: Moderata | Obiettivo: Mantenimento e crescita controllata | Leva Consigliata: 10x-15x | Size Consigliata: 5-10% | Azioni: Scommesse bilanciate a basso rischio)"
                    else:
                        regime = "LOCK-IN (Aggressività: Conservativa | Obiettivo: Blindatura del profitto per tagliare il traguardo X | Leva Consigliata: 3x-5x | Size Consigliata: 2-5% | Azioni: Minimizza l'esposizione, chiudi posizioni rischiose e consolida l'EUR)"
                    
                    snap["executive_regime"] = regime
                    logging.info(f"Regime Strategico V6.1 Corrente: {regime}")
                    logging.info(f"Target Gap: €{snap['mission_metrics']['gap_to_target_eur']} | Time Left: {snap['mission_metrics']['hours_to_flattening']}h")
                    logging.info(f"Current Unified Equity: €{current_equity:.2f} | Spot Pocket: €{spot_equity:.2f} | Futures Pocket: €{futures_equity:.2f}")
                    
                    # 1. Query the local Risk Mentor on 8081
                    mentor_advice = query_risk_mentor(snap)
                    logging.info(f"Risk Mentor Local Advice: {mentor_advice.get('advice')}")
                    
                    # 2. Query Nemotron Trader on 8080 with Mentor Advice and local context (Pilastri 1, 2, 3) (V6.2 - con restrizione Spot)
                    decision = query_trader(snap, mentor_advice, db.db_path, allow_spot=allow_spot)
                    
                    # Blocco d'autorità hardware basato sull'accuratezza storica (Pilastro 3)
                    mentor_reliability = get_mentor_reliability(db.db_path)
                    logging.info(f"Affidabilità storica del Risk Mentor registrata a database: {mentor_reliability*100:.1f}%")
                    
                    if mentor_reliability > 0.75 and decision.get("override_mentor", False):
                        logging.warning("ATTENZIONE: L'affidabilità storica del Risk Mentor è alta (>75%). Disattivato d'autorità il tentativo del Trader di fare l'override del mentore per salvaguardare il capitale.")
                        decision["override_mentor"] = False
                        
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
                                
                                cmd = f"{KRAKEN_PATH} futures paper {action} {symbol_futures} {vol} --type market --leverage {leverage_val}"
                                res = run_futures_cmd(cmd, capture=True)
                                logging.info(f"Futures Execution: {res.stdout.strip()} | Error (if any): {res.stderr.strip()}")
                                
                                # V7.0: Record active trade config if the order filled/succeeded
                                if "filled" in res.stdout.lower() or "order id" in res.stdout.lower():
                                    try:
                                        active_trades = {}
                                        if os.path.exists(ACTIVE_TRADES_PATH):
                                            with open(ACTIVE_TRADES_PATH) as f:
                                                active_trades = json.load(f)
                                        
                                        # Parse custom TP/SL from Nemotron's JSON
                                        tp_val = float(decision.get("take_profit_pct", 5.0))
                                        sl_val = float(decision.get("stop_loss_pct", 2.0))
                                        
                                        active_trades[symbol_futures] = {
                                            "entry_price": current_price,
                                            "side": action,
                                            "size": vol,
                                            "take_profit_pct": tp_val,
                                            "stop_loss_pct": sl_val,
                                            "decision_id": dec_id,
                                            "timestamp": int(time.time())
                                        }
                                        with open(ACTIVE_TRADES_PATH, "w") as f:
                                            json.dump(active_trades, f, indent=2)
                                        logging.info(f"📝 [V7.0 REGISTERED TRADE] {symbol_futures} ({action}) @ {current_price} | TP: {tp_val}% | SL: {sl_val}%")
                                    except Exception as ex:
                                        logging.error(f"Error registering trade to active_trades.json: {ex}")
                                
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
