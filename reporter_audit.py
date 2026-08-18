import requests
import json

LLAMA_URL = "http://100.73.54.72:8081/v1/chat/completions"

prompt = """Sei Llama-8B (Il Reporter).
Nemotron ha terminato l'ora di test e l'addestramento parallelo. 
Dati: 38 trades. PnL: -1.55%. Il portafoglio è bloccato quasi tutto su SOL (4.47 SOL) ed è rimasto pochissimo liquido (0.79 EUR). 
Fornisci un bollettino di chiusura per Giacomo (massimo 3 righe), avvertendolo dello sbilanciamento."""

try:
    resp = requests.post(
        LLAMA_URL,
        json={"model": "llama-8b", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3, "max_tokens": 300},
        timeout=120
    )
    print(resp.json()["choices"][0]["message"]["content"])
except Exception as e:
    print(e)
