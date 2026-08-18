import requests
import json
import re

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

prompt = """Sei Nemotron Sovereign Broker (V7.0 - SOVEREIGN SAFETY). 
Oggi stiamo facendo un upgrade architetturale massiccio per rendere il nostro ambiente di trading cartaceo un SIMULATORE PROFESSIONALE COMPLETO di Kraken, risolvendo i seguenti colli di bottiglia:

1. SLIPPAGE DINAMICO: Simuleremo uno slippage reale di esecuzione (0.05% per BTC/ETH e 0.15% per altcoin) allargando lo spread di ingresso registrato nei TP/SL locali, rendendo i test realistici.
2. COMMISSIONI MAKER VS TAKER: Imposteremo fee reali (0.26% Taker per Spot, 0.05% Taker per i Futures).
3. LIQUIDITY GUARD (ORDER IMPACT): Verificheremo la profondità del Book L2 prima di piazzare l'ordine; se la size dell'ordine supera il 10% della liquidità dei primi 5 livelli, l'ordine verrà ridotto automaticamente per evitare slippage catastrofici reali.
4. LIVE EUR/USD CONVERSION: Recupereremo il tasso di cambio live EUR/USD da CCXT per convertire l'equity dei Futures (che è in USD) in EUR, eliminando l'errore contabile di somma diretta EUR + USD.
5. LOCAL TP/SL MONITOR: Il runner locale flatterà d'ufficio le posizioni quando toccano i tuoi TP/SL desiderati, senza attendere i tempi del modello.
6. SAFETY STOP-OUT: Liquidazione totale immediata se l'equity scende del 20% sotto lo starting capitale della run.

Sei consapevole di tutte queste nuove regole operative e di sicurezza? 
Analizzale attentamente dal punto di vista di un trader quantitativo sovrano. Secondo te, c'è qualche altro collo di bottiglia o strumento fondamentale che non abbiamo ancora inserito per avere una simulazione professionale impeccabile prima di far partire la nuova run di 24h? Rispondi in italiano in modo sintetico, rigoroso e strutturato."""

try:
    resp = requests.post(NEMO_URL, json={
        "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
        "messages": [
            {"role": "system", "content": "Sei Nemotron Sovereign Broker, un sofisticato agente quantitativo locale. Rispondi in italiano."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 1000
    }, timeout=120)
    content = resp.json()["choices"][0]["message"]["content"].strip()
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    print(content)
except Exception as e:
    print(f"Error: {e}")
