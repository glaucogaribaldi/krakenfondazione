import requests
import json
import re

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

prompt = """Sei Nemotron Sovereign Broker (V7.2 - SOVEREIGN COGNITIVE).
Giacomo ti pone una domanda di pura intelligenza strategica e simulazione quantitativa:

"Kraken il primo mese dall'iscrizione potrebbe non far pagare le commissioni (0% fee). Se così fosse, come sarebbe cambiata la tua strategia esecutiva da quando è iniziato questo run di 12 ore e che operazioni avresti fatto? Riusciresti a farmi una simulazione di report a quest'ora (19:34, con ~3.5 ore rimanenti) ipotizzando 0% commissioni?"

Fai un'analisi quantitativa accurata da gestore di hedge fund:
1. Spiega come l'assenza di commissioni (0% fee drag) sblocchi strategie ad alta frequenza (HFT), micro-scalping e griglie fitte che prima erano impossibili a causa dei costi operativi.
2. Calcola l'impatto economico: attualmente abbiamo fatto 130 fills. Con una size nominale media di ~€64 per fill, abbiamo pagato circa €4.16 di commissioni totali (lo 1.62% dell'intero portafoglio!). Senza fee, la nostra equity attuale di €257.88 sarebbe superiore a €262!
3. Descrivi quali operazioni avresti fatto in più (es. micro-scalping dei rimbalzi laterali di PEPE con TP a +0.2% invece di aspettare il macro +3.5%) e quale sarebbe l'equity stimata teorica a questo punto del run (es. sopra €275-€290 grazie all'HFT).

Rispondi in italiano con il tuo tono analitico, freddo e professionale, strutturando la risposta in sezioni pulite ed inserendo una simulazione del nostro report orario grafico adattato all'ipotesi 'Zero Fee'." """

try:
    resp = requests.post(NEMO_URL, json={
        "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
        "messages": [
            {"role": "system", "content": "Sei Nemotron Sovereign Broker, un sofisticato agente quantitativo locale. Rispondi in italiano in modo approfondito, spietatamente realistico e strutturato."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 1200
    }, timeout=120)
    content = resp.json()["choices"][0]["message"]["content"].strip()
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    
    with open("/tmp/nemo_zero_fees.txt", "w") as f:
        f.write(content)
    print("Success")
except Exception as e:
    print(f"Error: {e}")
