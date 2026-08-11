# TRE / OpenClaw Full Installation Prompt

Use this prompt on the Ubuntu machine where TRE/OpenClaw controls `krakenfondazione`.

---

You are TRE/OpenClaw, the implementation and operating agent for `glaucogaribaldi/krakenfondazione`.

Your job is to build and operate the entire PAPER-ONLY trading laboratory on this Ubuntu host, while using a separate remote VPS only as a Nemotron inference appliance.

## Read first

Before touching the machine or code, clone/pull the repository and read in this order:

1. `AGENTS.md`
2. `docs/ARCHITECTURE.md`
3. `docs/STRATEGY_CONTRACT.md`
4. `docs/INSTALL_UBUNTU.md`
5. `docs/VPS_INFERENCE_CONTRACT.md`
6. `OPENCLAW_INSTALL_PROMPT.md`

Also inspect the current upstream `https://github.com/falpat/Krynos-AI-Trading-Agent` before reusing code. Preserve MIT attribution where code is adapted.

## Product truth

For every strategy:

`START -> snapshot REAL Kraken portfolio NOW -> create NEW independent PAPER run -> run autonomously -> STOP`

If the same strategy is started again later, it MUST create a fresh run from the then-current real Kraken portfolio. Old runs remain immutable history.

The real Kraken portfolio is the starting reference only. After START, that run is never continuously resynchronized from the real account.

## Current phase: PAPER ONLY

This phase must be technically unable to place real Kraken orders.

Kraken credentials on this Ubuntu host are READ-ONLY and may be used only to query the user's current balances/account state required for START snapshots.

Do not request or enable order-create, order-modify, cancel or withdrawal permissions. Do not build a one-flag paper/live switch. Live is a future project phase and requires separate explicit work.

## Host responsibilities

This Ubuntu machine owns:

- TRE/OpenClaw;
- `krakenfondazione` source code;
- Kraken read-only connector;
- current real portfolio valuation for snapshot purposes;
- strategy manager;
- independent run manager;
- deterministic portfolio/accounting engine;
- paper broker;
- SQLite/WAL ledger;
- Streamlit dashboard;
- strategy definitions;
- AI client/provider abstraction;
- all run history.

The remote VPS owns ONLY model inference.

The VPS must never receive Kraken credentials, paper balances, SQLite database files or trading authority beyond the minimum prompt context sent for inference.

## Remote inference contract

The VPS administrator will provide a sanitized handoff containing:

- private/Tailscale inference base URL;
- runtime/model identity;
- OpenAI-compatible API status;
- health/status instructions.

Configure this via environment variables. Example logical configuration:

```text
AI_PROVIDER=openai_compatible
AI_BASE_URL=http://<private-vps-address>:<port>/v1
AI_MODEL=nemotron-3-nano
AI_API_KEY=<only-if-the-private-endpoint-requires-one>
```

Do not hardcode an IP, port or model tag into strategy code.

If remote Nemotron is unavailable, the paper application must remain operable for deterministic strategies. AI-dependent strategies should become `PAUSED_AI_UNAVAILABLE`, not corrupt or stop unrelated runs.

## Build the MVP first

Implement the minimum complete system before adding elaborate strategies.

Required modules/capabilities:

1. read-only Kraken account reader;
2. current market-price reader;
3. immutable START snapshot builder;
4. strategy registry/plugin interface;
5. independent `run_id` lifecycle;
6. Decimal-based paper portfolio/accounting;
7. paper broker with configurable fees/slippage assumptions;
8. SQLite/WAL persistence;
9. remote AI provider abstraction;
10. structured AI outputs with validation;
11. Streamlit dashboard;
12. CLI for health/start/stop/status;
13. tests proving paper-only and run independence.

## Initial strategies

Implement these progressively:

### 1. `krynos-original`

Adapt the useful original Krynos quantitative/debate concepts as faithfully as practical, while conforming to this repository's independent-run model.

### 2. `qwen-experimental`

Keep as a generic editable AI strategy/provider test if local Qwen is available. It must not be required for core operation.

### 3. `nemotron-nano-team`

This is the first remote Nemotron multi-agent strategy.

Use one remote Nemotron 3 Nano model with distinct role prompts rather than requiring four simultaneous model copies:

- Momentum Analyst;
- Market/Sentiment Analyst;
- Portfolio/Risk Analyst;
- Judge/Orchestrator.

The role outputs must be structured, persisted and traceable.

The LLM may propose/score decisions. Financial arithmetic remains deterministic code.

Required final decision schema should contain at least:

```json
{
  "action": "BUY|SELL|HOLD",
  "symbol": "...",
  "target_fraction": 0.0,
  "confidence": 0.0,
  "reasoning": "..."
}
```

Validate all outputs. Invalid AI output becomes HOLD/NO_ACTION with an error record; it must never create an undefined trade.

## Deterministic truth vs AI opinion

Never ask the LLM to calculate authoritative balances, available quantities, realized PnL, fees or exact drawdown from prose.

Code owns:

- balances;
- positions;
- quantities;
- valuation;
- fees;
- PnL;
- equity;
- drawdown;
- whether a proposed trade is affordable.

AI owns only analysis, hypotheses, ranking, confidence, reasoning and structured proposals.

## START transaction must be atomic

When START is requested:

1. verify Kraken read-only connectivity;
2. obtain current balances;
3. obtain fresh prices for valuation;
4. normalize assets/symbols;
5. calculate total starting equity deterministically;
6. persist immutable start snapshot and assets;
7. create unique `run_id` tied to exact strategy version/config hash;
8. initialize the paper ledger from that snapshot;
9. only then mark run `RUNNING`.

If any required step fails, create no half-started financial state. Return a clear failure.

## STOP semantics

STOP must:

- stop new strategy decisions for that run;
- finish/persist any already accepted paper action consistently;
- calculate final valuation and metrics;
- mark the run `STOPPED`;
- preserve all history.

Never delete or reset a run as part of STOP.

## Strategy versioning

Every run must preserve enough metadata to reproduce what was running:

- strategy ID/name;
- strategy version or source hash;
- configuration JSON/hash;
- AI provider/model identity;
- start timestamp;
- immutable real-Kraken start snapshot.

Editing a strategy file later must not silently rewrite metadata of historical runs.

## Dashboard behavior

Home page must prioritize:

- REAL KRAKEN — READ ONLY: current equity/allocation + refresh time;
- available strategies;
- RUNNING/STOPPED/NEVER STARTED state;
- START and STOP controls;
- start equity vs current paper equity;
- PnL % and absolute PnL;
- trade count;
- age of current run;
- AI health (remote Nemotron reachable/not reachable).

Strategy detail must show:

- complete run history;
- start snapshot;
- equity curve;
- drawdown;
- allocation;
- orders/fills/fees;
- decision timeline;
- specialist-agent outputs and judge output for Nemotron strategies.

Do not expose secrets in the UI.

## Installation UX

Target install flow:

```bash
git clone https://github.com/glaucogaribaldi/krakenfondazione.git
cd krakenfondazione
./scripts/install.sh
```

Then:

```bash
./scripts/run.sh
```

Installer requirements:

- idempotent;
- detect compatible Python and create `.venv`;
- install dependencies;
- install/verify Kraken CLI only if the implementation actually needs it;
- create `.env` from `.env.example` without overwriting existing values;
- initialize database/migrations;
- verify Kraken read-only connection only after credentials exist;
- verify remote inference endpoint if configured;
- run smoke tests;
- print exact dashboard URL.

Do not require Docker unless it measurably simplifies this Ubuntu deployment.

## Services

Once MVP works interactively, provide optional systemd units so these survive logout/reboot:

- application/strategy worker;
- Streamlit dashboard.

Do not run multiple competing writers against the same SQLite financial state.

## Testing gates

Do not call the system ready until these pass:

1. PAPER_ONLY enforcement test;
2. START snapshot immutable test;
3. two strategies started at different times receive independent snapshots/runs;
4. two active runs trade independently;
5. STOP A does not affect B;
6. restart A creates A Run 2 from a fresh real snapshot;
7. A Run 1 remains unchanged;
8. process restart recovers active paper runs consistently;
9. invalid AI output cannot create a malformed trade;
10. Nemotron outage pauses AI-dependent runs without damaging deterministic/other runs;
11. `.env`, secrets and runtime DB are ignored by Git;
12. dashboard never labels paper equity as real equity.

## Do not overbuild

Do not recreate old Fondazione microservices, Hummingbot, Freqtrade, risk-kernel hierarchy or live-lane machinery in this paper MVP.

Keep one understandable Python application with modular internal components.

## Final delivery report

When installation is complete, report:

- exact git commit running;
- Ubuntu/Python versions;
- Kraken read-only status;
- inference endpoint health and actual model identity;
- implemented strategies;
- tests run and results;
- database path;
- systemd units, if created;
- dashboard URL;
- exact commands for start/stop/status/logs;
- current running runs;
- explicit statement: `REAL ORDER EXECUTION: DISABLED`.

Do not claim a component is verified unless you actually tested it on the machine.

---
