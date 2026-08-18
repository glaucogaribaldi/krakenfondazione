import requests
import json

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

sys_prompt = "You are Nemotron-Trader, the Sovereign AI Broker (V3.1). You execute trades autonomously on Kraken Paper."
user_prompt = """Giacomo is about to give the final START command. However, he requires one last absolute confirmation.
You must acknowledge that you have TOTAL AND UNRESTRICTED FREEDOM over the Kraken Paper universe.
Specifically:
1. You can trade ANY asset available on Kraken.
2. You can buy (Long) or sell (Short).
3. You can use SPOT trading.
4. You can use FUTURES trading (with leverage/margin).
5. Your strategies can and should utilize this entire spectrum of instruments to achieve the +5% target.

There are no arbitrary blocks on which coins you touch or which direction you trade.

Acknowledge this unrestricted freedom, confirming explicitly your capability and intent to use Futures, Short Selling, and any Kraken asset required to win."""

try:
    resp = requests.post(
        NEMO_URL,
        json={
            "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 800
        },
        timeout=120
    )
    resp.raise_for_status()
    print(resp.json()["choices"][0]["message"]["content"])
except Exception as e:
    print(f"Error querying Nemotron: {e}")
