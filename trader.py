import requests
import json
import uuid
import time
from db_manager import DatabaseManager
from market_engine import MarketEngine

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

sys_prompt = """You are Nemotron-Trader, Sovereign AI Broker.
INTENT: EXTREME_AGGRESSION.
You output strictly JSON: {"action":"buy|sell|hold", "pair":"...", "size_pct":0.1, "reason":"..."}"""

def query_nemotron(market_state):
    user_prompt = f"Market State: {json.dumps(market_state)}\nDecide action."
    try:
        resp = requests.post(NEMO_URL, json={
            "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 500
        }, timeout=120)
        content = resp.json()["choices"][0]["message"]["content"]
        
        # Clean think tags
        import re
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        content = content.replace('```json','').replace('```','').strip()
        return json.loads(content)
    except Exception as e:
        print(f"Error querying Nemotron: {e}")
        return {"action": "hold", "pair": "", "size_pct": 0, "reason": "error"}

if __name__ == "__main__":
    db = DatabaseManager("/broker/storage/db/nemotron.sqlite")
    engine = MarketEngine()
    snap = engine.fetch_snapshot()
    
    decision = query_nemotron(snap)
    print("Nemotron Decision:", decision)
    
    # Save T0
    decision_id = f"DEC-{uuid.uuid4().hex[:8]}"
    t0_record = {
        "decision_id": decision_id,
        "timestamp": int(time.time()),
        "intent_id": "INT-AGGRESSIVE",
        "market_snapshot": snap,
        "trader_decision": decision,
        "action_taken": decision
    }
    db.insert_t0(t0_record)
    print(f"T0 Saved: {decision_id}")
    
    # Mock execution and T1 save
    t1_record = {
        "exit_timestamp": int(time.time()) + 60,
        "pnl_pct": 0.0,
        "exit_reason": "mock_execution"
    }
    db.update_t1(decision_id, t1_record)
    print(f"T1 Saved: {decision_id}")
