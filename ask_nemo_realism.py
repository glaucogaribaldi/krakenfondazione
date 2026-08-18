import requests
import json
import re

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

prompt = """Sei Nemotron Sovereign Broker (V7.2 - SOVEREIGN COGNITIVE).
Giacomo ti pone questa domanda in modo estremamente diretto e sincero:

"Realisticamente arriveremo al nostro obiettivo di 500€? Vorrei capire cosa ne pensi tu sinceramente."

Fai un'analisi matematica e di probabilità fredda, cinica e realistica, considerando che:
- Cassa attuale: €257.88 EUR
- Target: €500.00 EUR (Gap di €242.12 da colmare, ovvero un +93.89% di rendimento richiesto)
- Tempo rimanente: esatte 3.5 ore prima del Hard Close delle 22:49.
- Posizione aperta: Short su PF_PEPEUSD con leva 5.0x (margin utilizzato al 100% della capacità esecutiva del broker, disponibile residuo di soli $0.36 USD).
- Leva effettiva sul portafoglio reale: circa 2.5x.

Spiegagli matematicamente qual è la probabilità reale di raggiungere €500 nelle prossime 3.5 ore. Non mentire, non dare false speranze, sii brutalmente onesto come un analista quantitativo senior davanti al consiglio di amministrazione di un hedge fund."""

try:
    resp = requests.post(NEMO_URL, json={
        "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
        "messages": [
            {"role": "system", "content": "Sei Nemotron Sovereign Broker, un sofisticato agente quantitativo locale. Rispondi in italiano in modo approfondito, spietatamente realistico e strutturato."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 600
    }, timeout=120)
    content = resp.json()["choices"][0]["message"]["content"].strip()
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    print(content)
except Exception as e:
    print(f"Error querying Nemotron: {e}")
