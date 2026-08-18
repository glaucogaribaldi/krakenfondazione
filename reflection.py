import requests
import json
from db_manager import DatabaseManager

LLAMA_URL = "http://100.73.54.72:8081/v1/chat/completions"

sys_prompt = "You are Reflection-Agent. Read the T1 Outcome. Produce a JSON belief: {'statement': '...', 'confidence': 0.8}"

def reflect_on_outcome(t0, t1):
    prompt = f"T0: {json.dumps(t0)}\nT1: {json.dumps(t1)}\nReflect and generate belief JSON."
    try:
        resp = requests.post(LLAMA_URL, json={
            "model": "llama-8b",
            "messages": [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 300
        }, timeout=120)
        content = resp.json()["choices"][0]["message"]["content"]
        import re
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip()
        content = content.replace('```json','').replace('```','').strip()
        return json.loads(content)
    except Exception as e:
        print(f"Error in reflection: {e}")
        return {}

if __name__ == "__main__":
    t0_mock = {"action": "buy", "pair": "ETH/EUR"}
    t1_mock = {"pnl_pct": -2.4, "exit_reason": "stop_loss"}
    belief = reflect_on_outcome(t0_mock, t1_mock)
    print("Generated Belief:", belief)
