import requests
import json
from datetime import datetime
import pytz

NEMO_URL = "http://100.73.54.72:8080/v1/chat/completions"
rome_tz = pytz.timezone('Europe/Rome')
current_time = datetime.now(rome_tz).strftime('%Y-%m-%d %H:%M:%S')

sys_prompt = "You are Nemotron-Trader, the Sovereign AI Broker."
user_prompt = f"""Giacomo requires a final check before launch.
The current exact time in the Italian timezone (Europe/Rome) provided by the system clock is: {current_time}.
Acknowledge this exact time to prove your temporal awareness for the 24H mission."""

try:
    resp = requests.post(
        NEMO_URL,
        json={
            "model": "unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL",
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 200
        },
        timeout=60
    )
    resp.raise_for_status()
    
    content = resp.json()["choices"][0]["message"]["content"]
    import re
    content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
    print(content)
except Exception as e:
    print(f"Error: {e}")
