import subprocess
import requests
import json
import re

TELEGRAM_TARGET = "655481675"
LLAMA_URL = "http://100.73.54.72:8081/v1/chat/completions"

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip()

def get_status():
    try:
        return json.loads(run_cmd("kraken paper status -o json --workspace fondazione-agentic"))
    except:
        return {}

def get_recent_trades():
    cmd = "ssh tre@100.73.54.72 \"sqlite3 /broker/storage/db/nemotron.sqlite 'SELECT trader_decision FROM episodic_memory ORDER BY timestamp DESC LIMIT 5;'\""
    out = run_cmd(cmd)
    trades = []
    for line in out.split('\n'):
        if line.strip():
            try:
                trades.append(json.loads(line))
            except:
                pass
    return trades

def send_telegram(msg):
    with open("/tmp/tg_msg_report.txt", "w") as f:
        f.write(msg)
    run_cmd(f'openclaw message send --channel telegram --account nemofondazione --target {TELEGRAM_TARGET} --message "$(cat /tmp/tg_msg_report.txt)"')
    print(f"Sent TG: {msg[:50]}...")

def main():
    print("Gathering data for immediate report...")
    status = get_status()
    trades = get_recent_trades()
    
    prompt = f"""
    Sei Fondazione-Reporter (Llama 8B).
    Genera un report di 3-4 righe in italiano per Giacomo sull'andamento del test V3.1 di Nemotron (dall'inizio del test).
    
    Dati Finanziari Attuali (Kraken): 
    {json.dumps(status)}
    
    Ultime 5 decisioni prese dal Sovereign Broker (Estratte dal Database SQLite sulla VPS): 
    {json.dumps(trades)}
    
    Sii professionale. Metti in evidenza il PnL, la direzione strategica, e se le operazioni hanno senso.
    """
    try:
        resp = requests.post(LLAMA_URL, json={
            "model": "llama-8b",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 300
        }, timeout=120)
        
        summary = resp.json()["choices"][0]["message"]["content"]
        summary_clean = re.sub(r'<think>.*?</think>', '', summary, flags=re.DOTALL).strip()
        
        send_telegram(f"📊 REPORT DI AGGIORNAMENTO\n{summary_clean}")
    except Exception as e:
        print(f"Reporter error: {e}")
        send_telegram(f"⚠️ Errore durante la generazione del report: {e}")

if __name__ == "__main__":
    main()
