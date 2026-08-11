# TRE START HERE — Kraken Fondazione

This is the final bootstrap entry point for TRE/OpenClaw on the Ubuntu application host.

## Mission

Install and operate `krakenfondazione` as a fast, simple, PAPER-ONLY strategy laboratory.

Core semantics:

`START strategy -> snapshot REAL Kraken portfolio NOW -> create NEW independent PAPER run -> evolve independently -> STOP`

Starting the same strategy later creates a NEW run from a fresh real-Kraken snapshot. Historical runs are immutable.

## Verified remote AI appliance

The dedicated Nemotron inference VPS is READY.

Verified handoff:

```text
Base URL: http://100.73.54.72:8080/v1
Transport: Tailscale/private only
Runtime: llama.cpp server
Model family: NVIDIA Nemotron 3 Nano 30B-A3B
Quantization: UD-Q4_K_XL / Q4_K Medium
2x NVIDIA Tesla T4
Generation baseline reported: ~52.5 token/s
10 sequential requests: PASS
2 concurrent requests: PASS
service restart: PASS
full reboot recovery: PASS
public exposure: NO
```

Do NOT assume the model ID string. Query it from `/v1/models` during installation and save the actual returned ID in local `.env`.

The VPS is inference-only. NEVER send Kraken credentials, the SQLite DB, raw secrets, or trading authority to it.

## Read in this order

1. `TRE_START_HERE.md`
2. `AGENTS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/STRATEGY_CONTRACT.md`
5. `docs/INSTALL_UBUNTU.md`
6. `docs/VPS_INFERENCE_CONTRACT.md`
7. `docs/VPS_INFERENCE_STATUS_2026-08-11.md`
8. `OPENCLAW_INSTALL_PROMPT.md`

Also inspect the current upstream project before adapting code:

`https://github.com/falpat/Krynos-AI-Trading-Agent`

Preserve MIT attribution for copied/adapted code.

## Immediate target

Do not overbuild. Get to a usable dashboard and first independent paper runs as quickly as possible.

The first usable version must provide:

- Kraken READ-ONLY connectivity;
- current real Kraken balance/allocation display;
- atomic START snapshot;
- independent run IDs and paper ledgers;
- STOP without affecting other runs;
- restart of a strategy as a NEW run from the then-current real Kraken snapshot;
- SQLite/WAL persistence;
- deterministic portfolio accounting;
- remote Nemotron client;
- strategy plugin registry;
- Streamlit dashboard;
- CLI/status tools;
- tests protecting paper-only and run isolation.

## Install target

On Ubuntu:

```bash
git clone https://github.com/glaucogaribaldi/krakenfondazione.git
cd krakenfondazione
```

Inspect the host before installing:

```bash
uname -a
cat /etc/os-release
python3 --version
free -h
df -h
tailscale status || true
```

Verify private connectivity to the Nemotron VPS:

```bash
curl --fail --silent http://100.73.54.72:8080/v1/models
```

If unreachable, diagnose Tailscale/networking. Do not expose the VPS publicly as a workaround.

## Environment setup

Create local configuration from `.env.remote.example` without committing it:

```bash
cp .env.remote.example .env
```

Populate:

- Kraken API key with READ-ONLY query permissions only;
- Kraken API secret;
- actual `AI_MODEL` returned by `/v1/models`.

Keep:

```text
PAPER_ONLY=true
AI_PROVIDER=openai_compatible
AI_BASE_URL=http://100.73.54.72:8080/v1
```

No trade/create/cancel/withdraw Kraken permissions are required or allowed in this phase.

## AI smoke test before strategy work

Query `/v1/models`, capture the actual model ID, then send a real `/v1/chat/completions` request.

Require:

- HTTP success;
- valid response;
- structured JSON test;
- no credentials embedded in prompts.

If AI is unavailable, deterministic strategies must still work. AI strategies become paused/unavailable, not fatal to the application.

## Application architecture

Keep one understandable Python application, not microservices.

Target internal shape:

```text
app/
  core/
    kraken_reader.py
    market_data.py
    snapshot.py
    portfolio.py
    paper_broker.py
    database.py
    runner.py
  ai/
    provider.py
    schemas.py
    nemotron.py
  strategies/
    base.py
    krynos_original.py
    nemotron_nano_team.py
    experimental.py
  dashboard/
    app.py
  cli.py
```

Use existing upstream Krynos code when it materially speeds implementation, but refactor where necessary to enforce independent runs.

## START is the key transaction

START must be atomic.

For strategy `S`:

1. verify Kraken read-only connectivity;
2. read current balances;
3. obtain fresh market prices for all supported held assets;
4. normalize assets/symbols;
5. calculate total equity with deterministic Decimal arithmetic;
6. persist immutable start snapshot, timestamp, asset balances and valuation prices;
7. create unique `run_id`;
8. persist strategy version/source hash and configuration hash;
9. initialize a new paper ledger from that exact snapshot;
10. mark run `RUNNING` only after all required writes succeed.

A failed START must not leave a partially initialized financial run.

After START, never continuously resync that run's balances from real Kraken.

Real Kraken remains a benchmark/current reference; the run follows only its own simulated actions and live market prices.

## STOP

STOP affects only the selected run.

It must:

- stop new decisions;
- persist consistent final state;
- calculate final valuation/metrics;
- mark the run `STOPPED`;
- preserve it permanently.

Do not delete/reset historical data.

## Initial strategies

### `krynos-original`

Adapt the useful upstream Krynos quantitative + debate behavior into the independent-run contract.

### `nemotron-nano-team`

Use the one remote Nemotron model with separate role prompts:

1. Momentum Analyst
2. Market/Sentiment Analyst
3. Portfolio/Risk Analyst
4. Judge/Orchestrator

These are roles, not four copies of the model.

Persist each specialist output and the final judge result.

Financial truth remains deterministic code.

Required final proposal schema:

```json
{
  "action": "BUY|SELL|HOLD",
  "symbol": "BTC/USD",
  "target_fraction": 0.0,
  "confidence": 0.0,
  "reasoning": "..."
}
```

Validate outputs strictly. Invalid/missing AI output => `HOLD/NO_ACTION` plus error record.

### `experimental`

Keep one simple strategy file designed to be edited quickly when Giacomo wants to invent/test a new strategy.

Adding a strategy should normally mean adding one file and registering metadata, not editing Kraken/database/broker infrastructure.

## Deterministic accounting

The LLM does NOT authoritatively calculate:

- balances;
- quantities;
- current equity;
- fees;
- realized/unrealized PnL;
- drawdown;
- affordability.

Python/Decimal code calculates these. The AI supplies analysis and proposals only.

## Paper broker

Implement configurable, explicit simulation assumptions for:

- fees;
- slippage;
- market/limit behavior if supported;
- valuation.

Store these assumptions with each run/config so results are interpretable later.

Do not pretend the simulator perfectly reproduces live Kraken execution.

## Dashboard MVP

Home screen should immediately answer:

### REAL KRAKEN — READ ONLY

- current total equity;
- asset allocation;
- last refresh timestamp.

### STRATEGIES

For each strategy:

- NEVER STARTED / RUNNING / STOPPED;
- START or STOP action;
- run start time;
- starting equity;
- current paper equity;
- absolute PnL;
- PnL %;
- trade count;
- run age;
- AI status if applicable.

Strategy detail:

- complete run history;
- immutable start snapshot;
- equity curve;
- drawdown;
- allocation;
- trades/orders/fills/fees;
- decision timeline;
- Nemotron specialist/judge reasoning.

Never visually confuse real Kraken balances with paper balances.

## Required run acceptance scenario

Before declaring the application ready, perform this exact scenario:

1. START Strategy A -> Snapshot A / Run A1.
2. Wait or refresh real Kraken state.
3. START Strategy B -> Snapshot B / Run B1.
4. Verify A1 and B1 are separate and can run concurrently.
5. STOP A1.
6. Verify B1 continues unchanged.
7. START Strategy A again -> NEW Snapshot / Run A2 from real Kraken at that moment.
8. Verify A1 remains immutable and queryable.
9. Restart application processes.
10. Verify active runs and historical runs recover consistently.

## Mandatory paper-only tests

At minimum test:

- no real order execution code path enabled;
- Kraken credentials used are query-only by intended configuration;
- START snapshot immutability;
- independent run ledgers;
- STOP isolation;
- NEW run semantics after restart of same strategy;
- invalid AI output produces no malformed trade;
- AI endpoint outage does not corrupt ledgers;
- SQLite survives process restart;
- `.env` and DB are ignored by Git;
- UI distinguishes REAL and PAPER values.

## Installation scripts

Create/finish:

```text
scripts/install.sh
scripts/run.sh
scripts/status.sh
scripts/stop.sh
scripts/smoke_test.sh
```

`install.sh` must be idempotent and should:

- verify compatible Python;
- create `.venv`;
- install requirements;
- initialize DB/migrations;
- preserve existing `.env`;
- verify Tailscale/private AI endpoint;
- discover actual model ID;
- verify Kraken only after credentials are configured;
- run tests/smoke tests;
- print exact next steps.

Do not add Docker unless there is a concrete technical need.

## Runtime services

After interactive validation, optionally configure systemd for:

- application/strategy worker;
- dashboard.

Ensure a single financial writer pattern for SQLite.

## Git discipline

Never commit:

- `.env`;
- API credentials;
- DB files;
- raw account exports;
- logs containing private portfolio data;
- model prompts containing secrets.

Commit source, tests, docs and safe examples.

## Completion report to Giacomo

When complete, report only verified facts:

```text
STATUS:
GIT COMMIT:
UBUNTU VERSION:
PYTHON VERSION:

KRAKEN READ-ONLY: PASS/FAIL
CURRENT REAL PORTFOLIO READ: PASS/FAIL

NEMOTRON BASE URL: http://100.73.54.72:8080/v1
ACTUAL MODEL ID:
NEMOTRON HEALTH: PASS/FAIL
STRUCTURED OUTPUT: PASS/FAIL

DATABASE:
DASHBOARD URL:

STRATEGIES AVAILABLE:
- ...

START/STOP/NEW-RUN ACCEPTANCE: PASS/FAIL
PROCESS RESTART RECOVERY: PASS/FAIL
TESTS: x passed / y failed

REAL ORDER EXECUTION: DISABLED

COMMANDS:
install:
run:
status:
stop:
logs:

BLOCKERS:
```

Do not call the system READY if START/STOP/new-run isolation has not actually been demonstrated.

## Final principle

The product is not "an AI that trades".

It is a laboratory that answers, for each independently started strategy:

> If this strategy had taken control of the exact Kraken portfolio I owned when I pressed START, and then evolved only through simulated trades from that moment, what would have happened?

Optimize everything around making that experiment fast to start, easy to understand and difficult to contaminate.
