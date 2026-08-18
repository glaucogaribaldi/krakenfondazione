# MASTER IMPLEMENTATION PLAN: NEMOTRON V3.1 + 24H AGGRESSIVE RUN
*Integration of "V3.1 Architecture" with the "24H Target-Aware Protocol"*

## PHILOSOPHY & OBJECTIVE
We are merging the cognitive persistence of the V3.1 Architecture (CVRF, Disagreement Logging, HMARL, T0 Immutable Database) with a hyper-focused, target-driven experiment (The 24H Aggressive Run). 
This requires building a system that doesn't just "trade" but structurally navigates toward a `+5% Target` using adaptive time horizons, dynamic universe discovery, and a strict isolation boundary between the Real Portfolio (Baseline) and the Paper Ledger (Execution).

---

## 🚀 PHASE 1: THE START PROCEDURE (Bootstrap & Discovery)
**Goal:** Initialize the 24H experiment autonomously.
1. **Real Portfolio Snapshot (Read-Only):**
   - Connect via CCXT to Kraken (Live API, strict Read-Only).
   - Fetch Spot + Fiat + Derivatives balances.
   - Calculate `TOTAL INITIAL EQUITY` normalized in EUR. Save as `paper_initial_equity`.
2. **Dynamic Discovery (Tradeable Universe):**
   - Query Kraken to fetch all available and liquid instruments (Spot & Futures).
   - Generate the initial `Market Scanner` target list, dumping illiquid garbage.
3. **Run Isolation:**
   - Generate a unique `run_id`.
   - Freeze `start_timestamp`, compute `end_timestamp` (+24h), and define the `flattening_window` (e.g., +23h45m).
   - Inject the `Global Strategic Intent` (EXTREME_AGGRESSION, ALLOW_FUTURES, +5% TARGET).

## 🚀 PHASE 2: UNIFIED LEDGER & TARGET-AWARE STATE
**Goal:** The Trader must see a single paper portfolio and its exact distance from the goal.
1. **Unified Ledger Engine:**
   - Build a Python module that tracks the total `current_equity` across simulated Spot and Futures.
   - Calculate `target_gap` (distance to +5%) and `time_remaining`.
2. **Market Snapshot V2 (T0 Injection):**
   - Expand the JSON snapshot. Every time the LLM is queried, it MUST receive the `Target-Awareness` block:
     ```json
     { "time_remaining_hours": 7.4, "current_pnl_pct": 2.1, "target_gap_pct": 2.9 }
     ```

## 🚀 PHASE 3: FAST LOOP & OPPORTUNITY SCANNER
**Goal:** Wake Nemotron only when mathematically justified.
1. **Scanner Implementation:**
   - Python processes the `Tradeable Universe` and outputs `Top 5 Opportunity Candidates` based on Momentum, Volatility, or Spread.
2. **State Change Detector:**
   - Trigger Nemotron NOT on a cron, but if: a new top opportunity appears, a position breaches invalidation limits, or portfolio equity drops by X%.

## 🚀 PHASE 4: THE MULTI-AGENT DEBATE (Strategist, Mentor, Trader)
**Goal:** Implement the V3.1 HMARL sequence with Disagreement tracking.
1. **Strategist:** Defines the Macro/Micro Regime.
2. **Mentor:** Pulls from `LanceDB/SQLite` checking previous 24H runs or past session decisions. Checks `Session Beliefs` (e.g., "SOL breaks failed twice today").
3. **Trader:** Receives Intent, Targets, Scanner Candidates, and Mentor Advice. Makes the final JSON call. Logs explicit agreement/disagreement with the Mentor.

## 🚀 PHASE 5: SHADOW LANES & INTRA-SESSION LEARNING
**Goal:** Test without bleeding capital.
1. **Shadow Simulations:**
   - The Trader JSON contract includes an array for `shadow_decisions` (Alternative routes it considered but didn't take).
   - Python saves these to a separate SQLite table to track counterfactual PnL.
2. **Intra-Run Beliefs:**
   - The Reflection Engine runs immediately post-trade. If a trade fails, it can generate a `SESSION_BELIEF` that instantly warns the Mentor for the remaining hours of the 24H run.

## 🚀 PHASE 6: TERMINAL CONDITION & FLATTENING (The Kill Switch)
**Goal:** End the experiment surgically.
1. **Flattening Watchdog:**
   - A background thread monitoring `time_remaining`.
   - At the `flattening_window`, it overrides the Intent to `FORCE_LIQUIDATION_MARKET`.
   - CCXT closes all open simulated futures, cancels pending orders, and converts Spot to EUR.
2. **Final Report Generation:**
   - Extracts PnL, Target Hit/Miss, Win/Loss ratio, Mentor vs Trader Scorecards.
   - Pushes the final audit to Telegram via the local Llama-8B daemon.

---
**STATUS:** `APPROVED_AND_READY`. 
*Waiting for Giacomo to trigger goal formulation for active Python implementation.*