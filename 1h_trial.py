#!/usr/bin/env python3
import subprocess
import json
import time
import requests
import re

WORKSPACE = "fondazione-agentic"
TELEGRAM_TARGET = "655481675"
NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"
LLAMA_URL = "http://100.73.54.72:8081/v1/chat/completions"
DURATION = 3600
REPORT_INTERVAL = 600

def run_cmd(cmd):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.stdout.strip()

def get_status():
    try:
        return json.loads(run_cmd(f"kraken paper status -o json --workspace {WORKSPACE}"))
    except: 
        return {}

def get_tickers():
    try:
        return json.loads(run_cmd("kraken ticker -o json BTCEUR ETHEUR SOLEUR DOGEEUR ADAEUR POLEUR DOTEUR"))
    except: 
        return {}

def send_telegram(msg):
    # Dobbiamo scappare le virgolette per passarlo via riga di comando
    safe_msg = msg.replace('"', '\\"')
    run_cmd(f'openclaw message send --channel telegram --account nemofondazione --target {TELEGRAM_TARGET} --message "{safe_msg}"')
    print(f"Inviato messaggio TG: {msg}")

def main():
    start_time = time.time()
    last_report_time = start_time
    insights_buffer = []
    
    send_telegram("🚀 [INIZIO TEST 1 ORA] Nemotron è sceso sul mercato. Obiettivo: Max profit & Self-training. Riceverai un report ogni 10 minuti dal desk.")
    
    while time.time() - start_time < DURATION:
        status = get_status()
        tickers = get_tickers()
        
        # 1. TRADING STEP (NEMOTRON)
        nemo_prompt = f"""
        You are Nemotron Sovereign Broker. 1-hour aggressive paper trial. Maximize profit.
        Status: {json.dumps(status)}
        Tickers: {json.dumps(tickers)}
        Respond ONLY with JSON format (no markdown): {{"trades": [{{"action":"buy","pair":"SOLEUR","volume":0.5}}], "wait_seconds": 15, "reasoning": "why"}}
        """
        try:
            resp = requests.post(NEMO_URL, json={
                "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL", 
                "messages": [{"role":"user", "content": nemo_prompt}], 
                "temperature": 0.4, 
                "max_tokens": 500
            }, timeout=120)
            nemo_res = resp.json()["choices"][0]["message"]["content"]
            
            nemo_res_clean = re.sub(r'<think>.*?</think>', '', nemo_res, flags=re.DOTALL).strip()
            nemo_res_clean = nemo_res_clean.replace('```json','').replace('```','').strip()
            decision = json.loads(nemo_res_clean)
            
            trades = decision.get("trades", [])
            reasoning = decision.get("reasoning", "No reasoning provided.")
            wait_time = max(10, min(600, decision.get("wait_seconds", 30)))
            
            insights_buffer.append(f"Azioni: {trades} | Logica: {reasoning}")
            
            for t in trades:
                if t.get("action") and t.get("pair") and t.get("volume"):
                    run_cmd(f"kraken paper {t['action']} {t['pair']} {t['volume']} --workspace {WORKSPACE}")
        except Exception as e:
            insights_buffer.append(f"Errore ciclo Nemotron: {e}")
            wait_time = 30
            
        # 2. REPORTING STEP (LLAMA)
        if time.time() - last_report_time >= REPORT_INTERVAL:
            llama_prompt = f"""
            Sei Fondazione-Reporter. Riassumi le ultime operazioni di Nemotron per Giacomo in un messaggio Telegram (in Italiano, max 3-4 righe, tono professionale).
            Stato Attuale Portafoglio: {json.dumps(status)}
            Log Recenti di Nemotron: {' | '.join(insights_buffer[-5:])}
            """
            try:
                rep_resp = requests.post(LLAMA_URL, json={
                    "model": "llama-8b", 
                    "messages": [{"role":"user", "content": llama_prompt}], 
                    "temperature": 0.3, 
                    "max_tokens": 300
                }, timeout=120)
                summary = rep_resp.json()["choices"][0]["message"]["content"]
                
                # Rimuovi eventuali tag <think> che Llama potrebbe generare
                summary_clean = re.sub(r'<think>.*?</think>', '', summary, flags=re.DOTALL).strip()
                
                send_telegram(f"📊 REPORT 10 MINUTI\n{summary_clean}")
                insights_buffer.clear()
                last_report_time = time.time()
            except Exception as e:
                print(f"Error generating report: {e}")
        
        time.sleep(wait_time)
        
    send_telegram("🏁 [FINE TEST 1 ORA] Sessione completata con successo. Attendo ordini.")

if __name__ == "__main__":
    main()
