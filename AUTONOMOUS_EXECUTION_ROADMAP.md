# AUTONOMOUS EXECUTION ROADMAP: NEMOTRON V3.1
**Master Implementation Plan for Autonomous Development**

This document serves as the exact sequence of autonomous goals that TRE will execute to build Nemotron V3.1. It is frozen and approved. No code will be written until this roadmap is strictly followed phase by phase.

## OPINION & PHILOSOPHY (The Architect's Thoughts)
The transition to V3.1 is the most sophisticated and robust approach to LLM-based algorithmic trading I have ever seen designed for constrained hardware (2x Tesla T4). 
By abandoning raw Reinforcement Learning on neural weights in favor of **Conceptual Verbal Reinforcement (CVRF)** and **Structured Agent Disagreement**, we transform the system from a "black box gambler" into a transparent, scientific, and measurable cognitive engine. The separation between the *Fast Deterministic Loop* (Python/Math) and the *Slow Cognitive Loop* (LLM/Reasoning) guarantees that Nemotron won't hallucinate math, while the *T0 Immutability* vs *T1 Outcome* boundary fundamentally kills hindsight bias. This is exactly how institutional prop-trading desks are built, translated into an LLM ecosystem.

---

## 🚀 PHASE 1: DECISION FOUNDATION (Data & Schemas)
**Objective:** Build the immutable foundation where every choice is recorded mathematically before execution.
1. **Define JSON Contracts:** Create the Python schemas for `GlobalStrategicIntent`, `MarketSnapshot`, `T0_DecisionRecord`, and `T1_OutcomeRecord`.
2. **Setup SQLite Database:** Initialize `/broker/storage/db/nemotron.sqlite` with tables for `episodic_memory`, `beliefs`, and `scorecards`.
3. **Database Interface:** Write the Python CRUD logic to reliably insert T0 records and subsequently update them with T1 outcomes.
*Gate: Verify that a mock T0 can be saved and cannot be mutated by a T1 update (only appended).*

## 🚀 PHASE 2: MARKET STATE ENGINE (The Deterministic Fast Loop)
**Objective:** Replace LLM "guessing" with hard math and reactive triggers.
1. **Kraken Ingestion:** Write the script that pulls real-time tickers and portfolio balances (Read-Only) using CCXT or REST/WebSocket.
2. **Feature Engine:** Implement Pandas/Numpy logic to compute OHLCV, ATR, VWAP deviation, and Volume Anomalies.
3. **State Change Detector:** Write the trigger logic. Nemotron wakes up *only* if `ΔVol > threshold` or `Price Displacement > threshold`, killing the cron-loop.
*Gate: Verify that the Python engine can generate a valid `MarketSnapshot` JSON without any LLM intervention.*

## 🚀 PHASE 3: THE SOVEREIGN TRADER (Baseline Nemotron)
**Objective:** Connect Nemotron-30B to the Fast Loop.
1. **Prompt Engineering:** Create the strict system prompt for the `Trader` persona, enforcing the JSON output contract.
2. **Inference Integration:** Write the API call to `llama.cpp` port 8080.
3. **Execution Link:** Connect Nemotron's JSON output (e.g., `{"action": "buy", "pair": "SOLEUR", "volume": 0.5}`) to the Kraken Paper API via CCXT.
4. **Integration:** Combine Phase 1 + 2 + 3: Trigger -> T0 Snapshot -> Nemotron Decision -> Save T0 -> Execute -> Save T1.
*Gate: Verify Nemotron can execute a complete, logged trade on the Paper environment based on a State Change trigger.*

## 🚀 PHASE 4: EPISODIC MEMORY & THE MENTOR
**Objective:** Give the system a past.
1. **LanceDB Setup:** Initialize the vector database in `/broker/storage/vectordb/` for semantic similarity.
2. **Retrieval Algorithm:** Write the hybrid search (SQLite deterministic filter + LanceDB semantic distance) to find the Top 5 similar past trades.
3. **Mentor Implementation:** Create the `Mentor` persona prompt. Feed it the retrieved episodes and ask for `Advice JSON`.
4. **Agent Disagreement Logging:** Update the Trader prompt to ingest Mentor Advice. Ensure the Trader logs whether it agrees or disagrees with the Mentor in the T0 record.
*Gate: Verify that before a trade, the Mentor successfully retrieves a past mock-episode and the Trader acknowledges or overrides the advice.*

## 🚀 PHASE 5: POST-TRADE REFLECTION & BELIEFS (The Slow Loop)
**Objective:** The system learns without updating neural weights.
1. **Reflection Engine:** Write the prompt that takes a T1 outcome and extracts `FACT -> OBSERVATION -> INTERPRETATION`.
2. **Belief State Machine:** Write the Python logic that converts an Interpretation into a `CANDIDATE` belief.
3. **Belief Validator:** Write the statistical engine that scans SQLite to count supporting vs. contradicting trades, moving beliefs to `ACTIVE` or `RETIRED`.
*Gate: Verify that a closed trade generates a Belief, and the Python engine correctly queries the DB to validate its confidence score.*

## 🚀 PHASE 6: SCORECARDS, METRICS & STRATEGY LAB (The Meta-Loop)
**Objective:** The system judges itself.
1. **Scorecards Engine:** Write the Python script that runs periodically to evaluate the `accuracy_rate` of the Mentor vs the Trader across different regimes.
2. **Strategist Implementation:** Introduce the `Strategist` persona to classify market regimes based on the Feature Engine, adjusting Mentor/Trader weights based on Scorecards.
3. **Strategy Lab (MVP):** Create the offline loop where Nemotron proposes a new conceptual hypothesis (e.g., "Filter by Open Interest") based on failed beliefs.
*Gate: Verify that the system generates a dynamic Scorecard and demotes an Agent/Belief if its accuracy drops below the threshold.*
