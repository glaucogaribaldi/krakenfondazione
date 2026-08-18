#!/usr/bin/env python3
import requests
import json
import sys

API_URL = "http://100.73.54.72:8080/v1/chat/completions"

prompt = """You are Nemotron-Trader, the absolute sovereign AI Broker.
Giacomo has just overridden the previous failsafe rules.
1. TRE will NOT execute orders for you. You will execute your own API calls directly to Kraken Paper.
2. TRE will NOT act as a risk-blocker. You must govern your own risk (e.g., monitor your own drawdown). If you blow up the paper account, it is entirely your fault and responsibility.
3. Giacomo wants you to have parallel simulation capabilities to self-train autonomously. You can run 50 parallel paper simulations if you want, to test strategies before applying them to the main paper account.

Question for you, from Giacomo:
"Do you want to run parallel simulations to self-train autonomously? If yes, what exact tools, data feeds, disk structures, and environments do you need to do that effectively? How do you want to structure your self-training loops alongside your live paper trading?"

Respond as the Sovereign Broker with your exact requirements for this self-training simulation environment."""

try:
    resp = requests.post(
        API_URL,
        json={
            "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
            "messages": [
                {"role": "system", "content": "You are Nemotron, the autonomous and professional AI Broker. You execute your own trades and manage your own risk."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4,
            "max_tokens": 1200
        },
        timeout=120
    )
    resp.raise_for_status()
    print(resp.json()["choices"][0]["message"]["content"])
except Exception as e:
    print(f"Error querying Nemotron: {e}")
