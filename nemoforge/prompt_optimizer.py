import sqlite3
import requests
import json
import re
import os

class PromptOptimizer:
    """
    Meta-Prompt Optimizer (MPO)
    Queries historical episodic memory from SQLite and leverages Nemotron-30B
    to autonomously analyze losses, mutate, and optimize trading system prompts.
    """
    def __init__(self, db_path="./data/krakenfondazione.db", nemo_url="http://100.73.54.72:8080/v1/chat/completions"):
        self.db_path = db_path
        self.nemo_url = nemo_url
        self.prompts_dir = "./nemoforge/prompts"
        os.makedirs(self.prompts_dir, exist_ok=True)
        
        # Write default baseline prompt if not present
        self.baseline_path = os.path.join(self.prompts_dir, "baseline_broker.txt")
        if not os.path.exists(self.baseline_path):
            self.write_default_baseline()

    def write_default_baseline(self):
        default_prompt = """You are Nemotron Sovereign Broker (V7.0).
Your core objective is to reach the Target Equity by compounding profits on Spot and Futures.
Rules:
1. Trade bidirectional (Long and Short).
2. Follow Risk Mentor recommendations strictly.
3. Keep leverage within 5x-15x for altcoins, up to 20x for BTC/ETH.
4. Set hard stop-loss and take-profit for every trade.
"""
        with open(self.baseline_path, "w") as f:
            f.write(default_prompt)

    def fetch_losses(self):
        """Fetches losing trades from episodic_memory for post-mortem analysis"""
        if not os.path.exists(self.db_path):
            return []
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Select relevant columns for loss analysis
            cursor.execute("""
                SELECT timestamp, market_regime, strategist_view, mentor_advice, 
                       trader_decision, outcome_pnl_pct, exit_reason 
                FROM episodic_memory 
                WHERE outcome_pnl_pct < 0 
                ORDER BY timestamp DESC LIMIT 5
            """)
            rows = cursor.fetchall()
            conn.close()
            return rows
        except Exception as e:
            print(f"Error fetching episodic memory: {e}")
            return []

    def optimize_prompt(self):
        """Sends the baseline prompt and past failures to Nemotron to generate an optimized prompt"""
        losses = self.fetch_losses()
        
        # Reconstruct post-mortem text
        post_mortem = ""
        if losses:
            post_mortem = "Here are the details of 5 recent LOSING trade episodes from our episodic memory:\n"
            for i, loss in enumerate(losses):
                post_mortem += f"\n[LOSS #{i+1}]\n"
                post_mortem += f"- Regime: {loss[1]}\n"
                post_mortem += f"- Strategist View: {loss[2]}\n"
                post_mortem += f"- Risk Mentor Advice: {loss[3]}\n"
                post_mortem += f"- Trader Decision: {loss[4]}\n"
                post_mortem += f"- Final P&L: {loss[5]}%\n"
                post_mortem += f"- Exit Reason: {loss[6]}\n"
        else:
            post_mortem = "No recent losing trades found. The system is performing adequately, but needs general optimization.\n"

        with open(self.baseline_path, "r") as f:
            baseline = f.read()

        system_instruction = "You are a senior quantitative developer and meta-prompt engineering expert."
        user_prompt = f"""You are NVIDIA Nemotron 30B GGUF. Your task is to analyze our current system prompt and the recorded failures (losing trade post-mortems), and autonomously output an OPTIMIZED, mutated version of our system prompt.

CURRENT SYSTEM PROMPT:
```text
{baseline}
```

{post_mortem}

TASK:
1. Perform a silent post-mortem of the losing trades. Identify the primary cognitive or logical errors made by the trader (e.g., ignoring Risk Mentor, over-leveraging, lack of stop loss, trading low liquidity).
2. Generate an OPTIMIZED system prompt that incorporates specific, hard negative constraints (Vetos) to explicitly prevent these errors in future runs.
3. Ensure the optimized prompt maintains all core objectives (Compounding, Bidirectional trading, Kraken compatibility).

Output ONLY the optimized, raw system prompt. Do not write any markdown code fences, do not wrap it in xml tags, and do not write any introductory or concluding conversational text. Start directly with the prompt text.
"""

        payload = {
            "model": "nemotron-3-nano",
            "messages": [
                {"role": "system", "content": "You are a meta-prompt optimizer. You output the mutated system prompt text directly, with absolutely no surrounding markdown, tags, or explanations."},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 2000
        }

        print("Calling Nemotron-30B for autonomous prompt mutation...")
        try:
            res = requests.post(self.nemo_url, json=payload, timeout=90)
            res.raise_for_status()
            res_json = res.json()
            mutated = res_json['choices'][0]['message']['content'].strip()
            
            # Strip <think>...</think> blocks if present
            mutated = re.sub(r'<think>.*?</think>', '', mutated, flags=re.DOTALL).strip()
            
            # Strip markdown code blocks
            if "```text" in mutated:
                mutated = re.search(r"```text\s*(.*?)\s*```", mutated, re.DOTALL).group(1)
            elif "```" in mutated:
                mutated = re.search(r"```\s*(.*?)\s*```", mutated, re.DOTALL).group(1)
                
            mutated_path = os.path.join(self.prompts_dir, "mutated_broker.txt")
            with open(mutated_path, "w") as f:
                f.write(mutated)
                
            print(f"SUCCESS: Autonomous prompt mutation completed. Saved to {mutated_path}")
            return {"status": "success", "mutated_prompt": mutated, "path": mutated_path}
        except Exception as e:
            print(f"Error during remote prompt optimization: {e}")
            return {"status": "error", "reason": str(e)}
