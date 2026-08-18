import requests
import json
import time

NEMOTRON_URL = "http://100.73.54.72:8080/v1/chat/completions"
REPORTER_URL = "http://100.73.54.72:8081/v1/chat/completions"

def query_model(url, model_name, sys_prompt, user_prompt, max_tokens=1024):
    try:
        resp = requests.post(
            url,
            json={
                "model": model_name,
                "messages": [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.4,
                "max_tokens": max_tokens
            },
            timeout=120
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"

print(">>> TEST 1: PINGING LLAMA-8B (THE REPORTER) <<<")
rep_sys = "You are Fondazione-Reporter (Llama-8B). Your job is to read Nemotron's insights and report to Giacomo via Telegram. You do not trade."
rep_user = "Acknowledge your role in the new Masterplan. Are you ready to intermediate?"
reporter_resp = query_model(REPORTER_URL, "llama-8b", rep_sys, rep_user, 300)
print(f"REPORTER SAYS:\n{reporter_resp}\n{'-'*40}")

print("\n>>> TEST 2: PINGING NEMOTRON-30B (THE SOVEREIGN BROKER) <<<")
nemo_sys = "You are Nemotron-Trader, the Sovereign AI Broker. The 256GB storage at /broker/storage is mounted and yours."
nemo_user = """Giacomo has approved the Masterplan.
Task 1: Acknowledge the infrastructure (256GB disk, CCXT access, parallel simulation layout). Are you satisfied?
Task 2: Analyze what you can do on Kraken Paper. Give Giacomo a report on your capabilities (assets, order types) and tell us exactly what needs to be UNLOCKED or provided (e.g. futures access, margin, L3 websockets, specific pair whitelists) to maximize your power.
Task 3: Declare the official initiation of your self-training loop using Giacomo's portfolio as the base simulation state."""
nemo_resp = query_model(NEMOTRON_URL, "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL", nemo_sys, nemo_user, 1200)
print(f"NEMOTRON SAYS:\n{nemo_resp}\n{'-'*40}")
