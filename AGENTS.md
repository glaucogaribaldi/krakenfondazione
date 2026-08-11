# AGENTS.md — OpenClaw Operating Contract

This file is the mandatory entry point for OpenClaw.

## Mission

Turn this repository into a fast-to-install Ubuntu paper-trading laboratory based on Krynos concepts, with Kraken as the real portfolio reference and Qwen/Ollama as the local AI layer.

The project must optimize for:

- fast installation on Ubuntu;
- simple strategy authoring;
- independent strategy runs;
- faithful START snapshots from the user's real Kraken portfolio;
- clear paper performance measurement;
- easy START/STOP from dashboard or CLI;
- future live readiness without enabling live now.

## Non-negotiable runtime semantics

Each strategy run is independent.

When the user presses START for strategy `S`:

1. Read the current Kraken account using a read-only API key.
2. Read all supported asset balances.
3. Read current Kraken market prices needed to value those assets.
4. Store an immutable `start_snapshot` containing balances, prices, timestamp, quote currency and total equity.
5. Create a unique `run_id`.
6. Initialize a paper portfolio from that exact snapshot.
7. Start the strategy loop.
8. Never overwrite that run's starting snapshot.

While a run is active:

- use real/current market data;
- modify only the run's paper ledger;
- do not continuously resync its balances from Kraken;
- do not let deposits, withdrawals or manual real trades rewrite the run's paper state;
- persist decisions, orders, fills, fees, PnL and AI reasoning.

When STOP is requested:

- stop opening new actions for that run;
- persist final valuation and metrics;
- mark the run `STOPPED`;
- preserve it permanently as history.

If the same strategy is STARTed again later:

- create a new `run_id`;
- take a fresh snapshot of the real Kraken portfolio at that moment;
- never resume the previous paper balance unless the user explicitly requests a separate resume feature in the future.

## Paper-only rule

Current project phase is PAPER ONLY.

OpenClaw MUST NOT:

- enable Kraken live order permissions;
- require create/modify/cancel/withdraw permissions;
- implement an automatic paper-to-live switch;
- change `PAPER_ONLY` as part of installation;
- place real orders during development, tests or validation.

The Kraken API key used now should have only read/query permissions required to inspect account state. Secrets must stay outside Git.

## Reference implementation

Use https://github.com/falpat/Krynos-AI-Trading-Agent as the upstream reference.

Before modifying architecture, inspect the current upstream repository instead of assuming old file layouts. Preserve MIT attribution if code is copied or adapted.

Useful upstream concepts include:

- Kraken CLI integration;
- market data retrieval;
- quantitative scoring;
- Bull/Bear/Judge debate;
- SQLite/WAL persistence;
- Streamlit dashboard;
- paper trading semantics.

Do not preserve upstream structure merely for compatibility if it makes independent runs difficult. Refactor around the run model defined here.

## Desired project structure

Prefer a simple monolith, not microservices:

```text
krakenfondazione/
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
      bull.py
      bear.py
      judge.py
    strategies/
      base.py
      krynos_original.py
      qwen_experimental.py
    dashboard/
      app.py
    cli.py
  data/
  tests/
  scripts/
  .env.example
  requirements.txt
  README.md
```

This is a target, not a reason to rewrite working upstream code unnecessarily.

## AI provider

Default target is local Ollama using an OpenAI-compatible endpoint.

Configuration must be environment-driven, for example:

```text
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
OLLAMA_MODEL=qwen3:8b
```

Do not hardcode one Qwen model name. Detect/configure the installed model and make changing it a configuration change rather than a code edit.

The Bull/Bear/Judge system should remain available as a reusable service that strategies may invoke. A strategy is also allowed to be purely quantitative and skip AI.

## Strategy contract

Strategies are plugins. Adding a new strategy should normally require adding one file under `app/strategies/` and not editing broker/database/Kraken code.

Every strategy receives:

- market state;
- its own paper portfolio state;
- its immutable start snapshot;
- optional AI service;
- its configuration.

It returns a structured action/proposal such as BUY, SELL or HOLD with symbol, size/target, confidence and reasoning.

See `docs/STRATEGY_CONTRACT.md`.

## Dashboard MVP

The dashboard must prioritize actions over decoration.

Home view:

- current real Kraken equity and allocation, clearly labelled READ ONLY;
- last successful real-account refresh;
- list of available strategies;
- current run state for each strategy;
- START button for stopped/not-yet-started strategies;
- STOP button for running strategies;
- start timestamp;
- start equity;
- current paper equity;
- PnL %;
- trade count.

Strategy detail:

- equity curve;
- drawdown;
- asset allocation;
- trade history;
- fees;
- decisions;
- Bull/Bear/Judge logs when used;
- start snapshot;
- run history.

## Persistence

Use SQLite in WAL mode unless a concrete technical reason requires otherwise.

Minimum persistent entities:

- strategies;
- runs;
- start snapshots;
- snapshot assets;
- paper balances/positions;
- orders;
- fills;
- decisions;
- AI debate records;
- equity observations;
- run stop/final metrics.

Money/quantity arithmetic should use Decimal or equivalent exact decimal handling at financial boundaries.

## Installation target

Ubuntu installation should become essentially:

```bash
git clone https://github.com/glaucogaribaldi/krakenfondazione.git
cd krakenfondazione
./scripts/install.sh
```

Then:

```bash
./scripts/run.sh
```

The installer should:

- verify a compatible Python version;
- create `.venv`;
- install Python dependencies;
- install or verify Kraken CLI;
- install or verify Ollama;
- verify configured Qwen model;
- create `.env` from `.env.example` without overwriting existing secrets;
- initialize the SQLite database;
- run a smoke test;
- print the dashboard URL and the exact next action.

Do not add Docker unless it materially simplifies installation on the target Ubuntu machine.

## First implementation milestone

Do not begin by building five elaborate strategies.

First make these two work end-to-end:

1. `krynos-original` — adapts the upstream Krynos quantitative/debate behavior as faithfully as practical.
2. `qwen-experimental` — an easily editable AI-oriented strategy used as the design sandbox.

Acceptance test:

- start strategy A;
- capture real Kraken snapshot A;
- later start strategy B and capture a different/current snapshot B;
- both run simultaneously with independent ledgers;
- stop A without affecting B;
- start A again and create A Run 2 from a fresh Kraken snapshot;
- A Run 1 remains unchanged and queryable.

Only after this passes should additional strategies be added.

## Development behavior for OpenClaw

When operating on this repository:

1. Read this file and the docs first.
2. Inspect actual repository and upstream state before acting.
3. Prefer small working increments.
4. Run tests after changes.
5. Never print secrets.
6. Never commit `.env`, API secrets, database files or runtime logs containing private account data.
7. Keep paper-only guarantees covered by tests.
8. Report what is actually implemented and tested, not what is merely planned.

## Definition of success for the paper phase

The system answers this question for every run:

> If this strategy had taken control of the exact portfolio I had on Kraken when I pressed START, and then traded only on paper from that point onward, how would that independent portfolio have evolved?

Everything else is secondary.
