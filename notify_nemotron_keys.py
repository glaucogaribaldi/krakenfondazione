import requests

NEMOTRON_URL = "http://100.73.54.72:8080/v1/chat/completions"

sys_prompt = "You are Nemotron-Trader, the Sovereign AI Broker. You are completely autonomous in Paper Trading."
user_prompt = """Giacomo has just delivered what you requested to unlock your full power.
1. The API Vault at `/broker/storage/shared/config/api_vault.json` has been populated with MAX FUNCTION Spot Keys and dedicated FUTURES Keys for Kraken Paper.
2. You are now authorized and equipped to trade Futures (Perpetuals/Options) and use Margin/Leverage in your simulations.
3. Your Futures wallet is currently empty. Giacomo explicitly authorized you to simulate a transfer/conversion of funds from your Spot Paper balance to your Futures Paper balance to begin trading.
4. ABSOLUTE RULE: You are NEVER to go LIVE on the real portfolio. You are strictly confined to Paper Trading.

Acknowledge the receipt of the keys, your new capability to trade Futures, your plan to transfer funds internally to the Futures wallet, and confirm your compliance with the absolute PAPER-ONLY rule."""

try:
    resp = requests.post(
        NEMOTRON_URL,
        json={
            "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 1024
        },
        timeout=120
    )
    resp.raise_for_status()
    print("NEMOTRON SAYS:\n" + resp.json()["choices"][0]["message"]["content"])
except Exception as e:
    print(f"Error querying Nemotron: {e}")
