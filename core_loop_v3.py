import asyncio
import time
import uuid
import json
import logging
import requests
from db_manager import DatabaseManager
from market_engine import MarketEngine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.FileHandler("/broker/storage/logs/v3_loop.log"), logging.StreamHandler()]
)

WORKSPACE = "fondazione-agentic"
NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

sys_prompt = """You are Nemotron Sovereign Broker (V3.1).
INTENT: EXTREME_AGGRESSION, MAXIMIZE_PROFIT, DYNAMIC_SIZING.
Your logic: Market Change -> Retrieve Mentor -> Reason -> Act.
Output strictly JSON: {"action":"buy|sell|hold", "pair":"BTC/EUR", "size_pct":0.2, "override_mentor":false, "reason":"..."}
Do not use markdown. Only raw JSON."""

db = DatabaseManager("/broker/storage/db/nemotron.sqlite")
engine = MarketEngine()

def query_trader(market_state, mentor_advice):
    prompt = f"Market State: {json.dumps(market_state)}\nMentor Advice: {mentor_advice}\nDecide Action."
    try:
        resp = requests.post(NEMO_URL, json={
            "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4,
            "max_tokens": 500
        }, timeout=120)
        
        content = resp.json()["choices"][0]["message"]["content"]
        import re
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        content = content.replace('```json','').replace('```','').strip()
        return json.loads(content)
    except Exception as e:
        logging.error(f"Trader Error: {e}")
        return {"action": "hold", "pair": "", "size_pct": 0, "override_mentor": False, "reason": str(e)}

async def main_loop():
    logging.info("Starting Sovereign Broker V3.1 - 4-Hour Live Run")
    end_time = time.time() + (4 * 3600)
    
    while time.time() < end_time:
        try:
            snap = engine.fetch_snapshot()
            changed, reason = engine.detect_state_change(snap)
            
            if changed:
                logging.info(f"State Change Detected: {reason}")
                
                # In MVP, Mentor advice is static or lightly retrieved
                mentor_advice = "Volatile market. Favor momentum pairs."
                
                # TRADER DECIDES
                decision = query_trader(snap, mentor_advice)
                logging.info(f"Trader Decision: {decision}")
                
                if decision.get("action") in ["buy", "sell"] and decision.get("pair") and decision.get("size_pct", 0) > 0:
                    dec_id = f"DEC-{uuid.uuid4().hex[:8]}"
                    # Save T0
                    db.insert_t0({
                        "decision_id": dec_id,
                        "timestamp": int(time.time()),
                        "intent_id": "MAX_PROFIT",
                        "market_regime": reason,
                        "market_snapshot": snap,
                        "mentor_advice": {"advice": mentor_advice},
                        "trader_decision": decision,
                        "action_taken": decision
                    })
                    
                    pair_kraken = decision["pair"].replace("/", "")
                    vol = decision["size_pct"] # Dummy volume translation for paper limit
                    if vol > 0.001:
                        cmd = f"kraken paper {decision['action']} {pair_kraken} {vol} --workspace {WORKSPACE}"
                        import subprocess
                        res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                        logging.info(f"Execution: {res.stdout.strip()}")
                        
                        # Save T1 Immediately for Paper MVP
                        db.update_t1(dec_id, {
                            "exit_timestamp": int(time.time()),
                            "pnl_pct": 0.0,
                            "exit_reason": "executed_paper"
                        })
            else:
                pass # Stable, wait.
                
        except Exception as e:
            logging.error(f"Loop Error: {e}")
            
        await asyncio.sleep(60) # Poll every minute for State Change

if __name__ == "__main__":
    asyncio.run(main_loop())
