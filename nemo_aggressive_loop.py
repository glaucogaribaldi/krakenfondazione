#!/usr/bin/env python3
import subprocess
import json
import time
import datetime
import requests

WORKSPACE = "fondazione-agentic"
PAIRS = ["BTCEUR", "ETHEUR", "SOLEUR", "DOGEEUR", "XXRPZEUR"]
DURATION_HOURS = 2
API_URL = "http://100.73.54.72:8080/v1/chat/completions"

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def get_status():
    out = run_cmd(f"kraken paper status -o json --workspace {WORKSPACE}")
    try:
        return json.loads(out)
    except Exception:
        return {}

def get_tickers():
    # Fetch valid asset pairs from Kraken (MATIC is now POL)
    out = run_cmd(f"kraken ticker -o json BTCEUR ETHEUR SOLEUR DOGEEUR ADAEUR POLEUR DOTEUR")
    try:
        return json.loads(out)
    except Exception:
        return {}

def prompt_nemotron(status, tickers):
    prompt = f"""
You are Nemotron-Trader, the absolute sovereign AI trader.
Objective: Aggressive paper trading to achieve +5% profit in 1 hour. You are encouraged to perform high-frequency micro-trading.
Constraint: You manage your own trading cycles. You are authorized to trade ANY of the pairs listed in the current market prices.

Current Portfolio Status:
{json.dumps(status, indent=2)}

Current Market Prices (Tickers):
{json.dumps(tickers, indent=2)}

Decide your next moves. Respond ONLY with a valid JSON object in this exact format (no markdown, no quotes outside the braces):
{{
  "trades": [
    {{ "action": "buy", "pair": "SOLEUR", "volume": 0.5 }},
    {{ "action": "sell", "pair": "BTCEUR", "volume": 0.001 }}
  ],
  "wait_seconds": 15,
  "reasoning": "brief explanation"
}}
If no trades are needed right now, pass an empty list for "trades". "wait_seconds" tells the system when to wake you up next (e.g. 5, 15, 30).
"""
    print(f"[{datetime.datetime.now()}] Requesting decision from Nemotron (30B) via {API_URL}...")
    try:
        resp = requests.post(
            API_URL,
            json={
                "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 800
            },
            timeout=300
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return content
    except Exception as e:
        print(f"[{datetime.datetime.now()}] API Error: {e}")
        return ""

def parse_llm_response(text):
    import re
    try:
        text = text.strip()
        # Remove thinking block if present
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()
        
        parsed = json.loads(text)
        return parsed
    except Exception as e:
        print(f"[{datetime.datetime.now()}] Failed to parse Nemotron response: {e}\nRaw output: {text}")
        return None

def execute_trades(trades):
    if not trades:
        print(f"[{datetime.datetime.now()}] No trades to execute.")
        return
    for t in trades:
        try:
            action = t.get("action", "").lower()
            pair = t.get("pair")
            volume = t.get("volume")
            print(f"[{datetime.datetime.now()}] Executing: {action} {volume} {pair}")
            if action in ["buy", "sell"] and pair and volume:
                res = run_cmd(f"kraken paper {action} {pair} {volume} --workspace {WORKSPACE}")
                print(f"Result: {res}")
        except Exception as e:
            print(f"[{datetime.datetime.now()}] Error executing trade {t}: {e}")

def main():
    start_time = time.time()
    end_time = start_time + (DURATION_HOURS * 3600)
    print(f"[{datetime.datetime.now()}] Starting Nemotron Aggressive Loop for {DURATION_HOURS} hours.")
    
    while time.time() < end_time:
        status = get_status()
        tickers = get_tickers()
        
        raw_response = prompt_nemotron(status, tickers)
        decision = parse_llm_response(raw_response)
        
        wait_time = 60 # Default fallback
        
        if decision:
            print(f"[{datetime.datetime.now()}] Reasoning: {decision.get('reasoning', 'none')}")
            trades = decision.get("trades", [])
            execute_trades(trades)
            wait_time = decision.get("wait_seconds", 60)
            if wait_time > 600: wait_time = 600
            if wait_time < 10: wait_time = 10
        else:
            print(f"[{datetime.datetime.now()}] Invalid decision, defaulting to 60s wait.")
            
        print(f"[{datetime.datetime.now()}] Waiting {wait_time} seconds before next cycle...")
        time.sleep(wait_time)
        
    print(f"[{datetime.datetime.now()}] Loop completed after {DURATION_HOURS} hours.")

if __name__ == "__main__":
    main()
