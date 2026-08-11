# AGENTS.md — TRE / OpenClaw Operating Contract

This is the mandatory entry point for any coding/operating agent working on `glaucogaribaldi/krakenfondazione`.

## Mission

Build a fast-to-install Ubuntu PAPER-ONLY trading laboratory centered on the user's real Kraken portfolio at the instant each strategy starts.

The system must optimize for:

- quick Ubuntu installation;
- simple strategy authoring;
- independent strategy runs;
- faithful START snapshots from the user's real Kraken portfolio;
- deterministic paper accounting;
- easy START/STOP/history from dashboard and CLI;
- replaceable remote AI inference;
- future live readiness without enabling live now.

## Product invariant

For every strategy:

`START -> REAL KRAKEN SNAPSHOT NOW -> NEW INDEPENDENT PAPER RUN -> STOP`

When START is requested:

1. read the current Kraken account using READ-ONLY credentials;
2. read all supported balances;
3. obtain fresh market prices needed to value them;
4. persist an immutable start snapshot with timestamp, balances, prices, quote currency and total equity;
5. create a unique `run_id` bound to the strategy/config version;
6. initialize that run's paper ledger from the exact snapshot;
7. only then mark the run RUNNING.

While RUNNING:

- use current market data;
- mutate only that run's paper state;
- never continuously resync its balances from Kraken;
- deposits, withdrawals or manual real trades must not rewrite the run;
- persist decisions, paper orders/fills, fees, PnL, equity and AI reasoning.

When STOP is requested:

- stop new decisions/actions for that run;
- finalize/persist valuation and metrics consistently;
- mark the run STOPPED;
- preserve it permanently.

Starting the same strategy later creates a new run from a fresh then-current real Kraken snapshot. Never silently resume an old paper balance.

## PAPER ONLY

Current phase is PAPER ONLY and must be technically incapable of real execution.

OpenClaw MUST NOT:

- require Kraken create/modify/cancel/withdraw permissions;
- place or test real orders;
- add a one-flag paper-to-live switch;
- enable live as part of installation;
- store secrets in Git/logs/dashboard.

Kraken credentials are used only to query the real account state required for START snapshots.

## Physical architecture

### Ubuntu host — authoritative application

Owns:

- TRE/OpenClaw;
- repository/source code;
- Kraken read-only connector;
- market/snapshot logic;
- strategy registry;
- run lifecycle;
- deterministic portfolio/accounting engine;
- paper broker;
- SQLite/WAL ledger;
- dashboard/CLI;
- run history;
- AI client abstraction.

### Remote GPU VPS — inference appliance only

Owns:

- AI model runtime;
- private OpenAI-compatible inference endpoint;
- inference runtime logs/health.

The VPS MUST NOT own Kraken credentials, authoritative paper balances, SQLite financial state, strategy lifecycle or real execution authority.

See `docs/VPS_INFERENCE_CONTRACT.md` and `VPS_PREP_PROMPT.md`.

## AI architecture

Default target is a private remote inference endpoint, initially NVIDIA Nemotron 3 Nano.

Configuration must be external/environment-driven. Do not hardcode server IPs, ports or vendor-specific model tags in strategy code.

Logical variables:

```text
AI_PROVIDER=openai_compatible
AI_BASE_URL=http://<private-host>:<port>/v1
AI_MODEL=nemotron-3-nano
```

Local Ollama/Qwen may remain an optional experimental provider, not a core dependency.

If remote AI fails:

- deterministic strategies continue;
- AI-dependent runs enter a visible paused/unavailable state;
- no fake decision is generated;
- financial state remains consistent.

## Nemotron multi-agent strategy

Implement `nemotron-nano-team` using one remote Nemotron 3 Nano model with role-separated prompts:

1. Momentum Analyst;
2. Market/Sentiment Analyst;
3. Portfolio/Risk Analyst;
4. Judge/Orchestrator.

Do not require four separately loaded copies of the model. Persist role outputs and final judge output.

AI output is a proposal, not accounting truth. Validate structured outputs before paper execution. Invalid output becomes HOLD/NO_ACTION plus an error record.

Financial arithmetic is deterministic code: balances, quantities, available funds, fees, valuation, PnL, equity and drawdown must never be authoritative LLM calculations.

## Reference implementation

Inspect the current upstream project before adaptation:

`https://github.com/falpat/Krynos-AI-Trading-Agent`

Reuse/adapt MIT-licensed code where useful and preserve attribution.

Useful concepts include Kraken integration, quantitative signals, Bull/Bear/Judge debate, SQLite/WAL persistence, Streamlit dashboard and paper behavior. Do not preserve upstream structure if it conflicts with independent-run semantics.

## Preferred internal structure

Keep a simple modular monolith, not a microservice fleet:

```text
app/
  core/
    kraken_reader.py
    snapshot.py
    portfolio.py
    paper_broker.py
    database.py
    runner.py
  ai/
    provider.py
    roles.py
    judge.py
  strategies/
    base.py
    krynos_original.py
    qwen_experimental.py
    nemotron_nano_team.py
  dashboard/
    app.py
  cli.py
scripts/
tests/
data/
```

Adding a normal strategy should primarily mean adding one strategy module, not modifying Kraken/database/broker code.

## Strategy contract

Every strategy receives:

- current market state;
- its own paper portfolio;
- immutable start snapshot;
- strategy configuration;
- optional AI provider.

It returns a validated proposal such as BUY/SELL/HOLD with symbol, target/size, confidence and reasoning.

See `docs/STRATEGY_CONTRACT.md`.

## Persistence

Use SQLite in WAL mode unless a proven technical reason requires otherwise.

Persist at minimum:

- strategies and versions;
- runs;
- immutable start snapshots/assets;
- paper balances/positions;
- orders/fills/fees;
- decisions;
- AI role/debate records;
- equity observations;
- stop/final metrics.

Use Decimal/equivalent exact decimal handling at financial boundaries.

## Dashboard MVP

Home:

- current REAL KRAKEN equity/allocation, clearly labelled READ ONLY;
- refresh timestamp;
- AI inference health;
- strategies and RUNNING/STOPPED/NEVER STARTED state;
- START/STOP controls;
- current run start time/equity;
- current paper equity;
- PnL absolute/%;
- trade count.

Detail:

- run history;
- immutable start snapshot;
- equity curve/drawdown/allocation;
- orders/fills/fees;
- decision timeline;
- AI specialist and judge outputs where applicable.

Never label paper equity as real equity.

## Installation target

Desired Ubuntu experience:

```bash
git clone https://github.com/glaucogaribaldi/krakenfondazione.git
cd krakenfondazione
./scripts/install.sh
./scripts/run.sh
```

Installer must be idempotent, create `.venv`, install dependencies, initialize DB, create `.env` without overwriting secrets, verify Kraken read-only connectivity when configured, verify remote inference when configured, run smoke tests and print the dashboard URL.

Do not add Docker unless it materially simplifies this deployment.

## Initial implementation order

1. end-to-end core and independent run lifecycle;
2. `krynos-original`;
3. editable experimental strategy/provider path;
4. `nemotron-nano-team`;
5. only then additional strategies.

Acceptance scenario:

- Start A -> snapshot A;
- later Start B -> current snapshot B;
- A and B run independently;
- Stop A without affecting B;
- Start A again -> A Run 2 from current Kraken state;
- A Run 1 remains immutable/queryable.

## Required tests before READY

At minimum prove:

- real execution is disabled;
- START snapshot is immutable;
- independent runs never share financial state;
- STOP of one run does not stop others;
- restart of a strategy creates a new run/current snapshot;
- process restart recovers paper state consistently;
- malformed AI output cannot generate malformed trade state;
- AI outage does not corrupt runs;
- secrets/runtime DB are excluded from Git.

## Do not overbuild

Do not recreate old Fondazione microservices, Hummingbot, Freqtrade, live-lane/risk-kernel machinery or VPS-side trading logic for this MVP.

## Definition of success

For every run the system can answer:

> If this strategy had taken control of the exact portfolio I had on Kraken when I pressed START, and then traded only on paper from that point onward, how would that independent portfolio have evolved?

All implementation/reporting must distinguish planned, implemented and actually tested behavior.
