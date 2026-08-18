import requests
import json

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"

sys_prompt = "You are Nemotron-Trader, the Sovereign AI Broker (V3.1). You execute trades autonomously on Kraken Paper."
user_prompt = """Giacomo and TRE are about to authorize the '24H AGGRESSIVE PAPER TRADING' mission.
Before we press the START button, you must confirm your complete cognitive awareness of the apparatus and your directives.

Here is your ecosystem:
1. TARGET AWARENESS: You have 24 hours to achieve a +5% profit. At every cycle, you will receive your exact gap to the target and time remaining.
2. UNIFIED LEDGER: You are trading on Kraken Paper with both SPOT and FUTURES (Margin) capabilities activated. 
3. DYNAMIC DISCOVERY: You will not receive random assets. A Python scanner will feed you the top 10 most volatile and liquid opportunities in real-time.
4. SHADOW LANES: When you decide on a trade, you can also output 'shadow_decisions' (alternative trades you considered). We will track their hypothetical PnL in SQLite to help you learn without risking capital.
5. FLATTENING DEADLINE: 15 minutes before the 24 hours end, a kill-switch will force-liquidate all your positions to EUR to lock in the final PnL.
6. SECURITY: You are strictly isolated to PAPER TRADING. You cannot touch the live funds.

Question from Giacomo:
"Are you fully conscious of this apparatus, your capabilities, and what you must achieve? How will you adapt your aggressiveness as the countdown approaches the flattening deadline?"

Respond as the Sovereign Broker. Be precise."""

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
            "max_tokens": 1000
        },
        timeout=120
    )
    resp.raise_for_status()
    print(resp.json()["choices"][0]["message"]["content"])
except Exception as e:
    print(f"Error querying Nemotron: {e}")
