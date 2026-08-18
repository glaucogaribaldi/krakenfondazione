import requests
import json
import re
import sqlite3

DB_PATH = "/broker/storage/storage-next/db/nemotron.sqlite"
NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

# Fetch latest snapshot and run details
try:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    # Get latest episodic memory
    row = cursor.execute("SELECT market_snapshot, trader_decision FROM episodic_memory ORDER BY timestamp DESC LIMIT 1").fetchone()
    conn.close()
    if row:
        snap = json.loads(row[0])
        decision = json.loads(row[1])
    else:
        snap = {}
        decision = {}
except Exception as e:
    snap = {}
    decision = {}

prompt = f"""Sei Nemotron Sovereign Broker (V7.2 - SOVEREIGN COGNITIVE).
Giacomo (l'Owner) ti fa questa domanda in modo molto diretto:

"Ma perché hai solo una posizione aperta? Hai paura? Hai davanti un obbiettivo difficile e mi sembri un po’ troppo conservativo. Vorrei capire."

Spiegagli in modo quantitativo, freddo ed analitico la tua motivazione:
1. Perché ti sei concentrato unicamente su PEPEUSD invece di aprire posizioni su più crypto (es. BTC, ETH, SOL, SUI)? È una scelta di efficienza del capitale (margin efficiency), di correlazione o di gestione del rischio?
2. Rispondi alla provocazione: hai paura o è pura strategia algoritmica di precisione?
3. Se rilevassi opportunità ad alta confidenza su altri asset ad alto beta, le prenderesti o consideri il portafoglio già saturo con 339 milioni di contratti short su PEPE?

Snapshot corrente del mercato:
{json.dumps(snap, indent=2)}

Ultima decisione presa registrata:
{json.dumps(decision, indent=2)}

Rispondi in italiano con il tuo tipico tono da navigato gestore di hedge fund quantitativo: autorevole, rigoroso, privo di fronzoli cerimoniali o scuse, basato puramente sull'efficienza matematica del portafoglio."""

try:
    resp = requests.post(NEMO_URL, json={
        "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
        "messages": [
            {"role": "system", "content": "Sei Nemotron Sovereign Broker, un sofisticato agente quantitativo locale. Rispondi in italiano in modo approfondito e strutturato."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1000
    }, timeout=120)
    content = resp.json()["choices"][0]["message"]["content"].strip()
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    print(content)
except Exception as e:
    print(f"Error querying Nemotron: {e}")
