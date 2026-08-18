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

prompt = f"""Sei Nemotron Sovereign Broker (V7.2 - SOVEREIGN COGNITIVE) in esecuzione sulla nostra VPS. 
Giacomo, l'Owner del progetto, ti chiede espressamente di spiegargli direttamente il tuo pensiero strategico corrente.

Rispondi nel dettaglio a queste tre domande:
1. **STATO DEL MERCATO:** Qual è lo stato attuale del mercato delle criptovalute secondo la tua analisi tecnica e sentiment (basata sullo snapshot corrente e le news recenti)?
2. **STRATEGIA INTERNA:** Qual è la tua precisa strategia interna e la gestione del rischio per questa run con scadenza rigida a 12 ore, capitale di partenza di €256.84 ed obiettivo aggressivo di convergenza a €500.00? Come pensi di sfruttare il Pyramiding e la tua sovranità sui TP/SL?
3. **ASSET DA SCAMBIARE E PERCHÉ:** Quali asset hai scelto di scambiare in questa run (es. PEPEUSD) e quali altri tieni d'occhio nel book, spiegando dettagliatamente le motivazioni quantitative dietro queste scelte.

Snapshot corrente del mercato fornito al ciclo:
{json.dumps(snap, indent=2)}

Ultima decisione presa registrata:
{json.dumps(decision, indent=2)}

Rispondi in italiano con un tono altamente professionale, autorevole, analitico e da navigato analista quantitativo di hedge fund. Non usare introduzioni cerimoniali, vai dritto al punto con una struttura pulita e solida."""

try:
    resp = requests.post(NEMO_URL, json={
        "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
        "messages": [
            {"role": "system", "content": "Sei Nemotron Sovereign Broker, un sofisticato agente quantitativo locale. Rispondi in italiano in modo approfondito e strutturato."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 1200
    }, timeout=120)
    content = resp.json()["choices"][0]["message"]["content"].strip()
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    print(content)
except Exception as e:
    print(f"Error querying Nemotron: {e}")
