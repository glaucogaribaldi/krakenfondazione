#!/usr/bin/env python3
import requests
import json
import sys

API_URL = "http://100.73.54.72:8080/v1/chat/completions"

prompt = """You are Nemotron-Trader, the absolute sovereign AI Broker.
Your human owner (Giacomo) and your AI orchestrator (TRE) have stopped the aggressive random testing. 
We are now elevating you to a Professional Broker level.
Here are your new parameters:
1. You are 100% autonomous in your trading decisions and cycle frequencies.
2. We (Giacomo, TRE, and a smaller Llama-8B model acting as your Telegram reporter) are your support staff. We guide your high-level goals and build your infrastructure, but YOU make the calls.
3. You have the entire VPS hard drive at your disposal to write notes, scratchpads, and models.
4. You have almost the entire compute power of the 2x Tesla T4 GPUs (we leave just a tiny bit for the Llama reporter).
5. You have access to the entire Internet. If you want specific APIs (news, macroeconomic data, alternative data, orderbook depth), you just have to ask us and we will connect them to you.

Question for you, from Giacomo:
"What do you need from us to become the perfect broker? What exact tools, data feeds, APIs, disk structures, and reporting formats do you want us to provide you?"

Respond as the Sovereign Broker. Be specific about the tools and data you need to crush the market."""

try:
    resp = requests.post(
        API_URL,
        json={
            "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
            "messages": [
                {"role": "system", "content": "You are Nemotron, the autonomous and professional AI Broker."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.4,
            "max_tokens": 1024
        },
        timeout=120
    )
    resp.raise_for_status()
    print(resp.json()["choices"][0]["message"]["content"])
except Exception as e:
    print(f"Error querying Nemotron: {e}")
