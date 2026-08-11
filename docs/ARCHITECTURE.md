# Architecture — Kraken Fondazione

## Principle

Kraken is the source of the user's real portfolio state **only at strategy START** and the source of current market data during the run.

Each strategy run becomes independent immediately after START.

```text
REAL KRAKEN (read only)
        |
        | START strategy
        v
immutable start snapshot
        |
        v
independent paper portfolio
        |
        +--> strategy logic
        +--> optional Qwen Bull/Bear/Judge
        +--> paper broker
        +--> SQLite ledger
        |
        v
STOP -> frozen run history
```

## Run lifecycle

States:

- `CREATED`
- `RUNNING`
- `STOPPING`
- `STOPPED`
- `ERROR`

A stopped run is historical and immutable except for safe metadata annotations. Restarting a strategy creates a new run.

## START transaction

START should be treated as one logical transaction:

1. Generate `run_id`.
2. Fetch real Kraken balances using read-only authentication.
3. Normalize supported assets.
4. Fetch prices required for valuation.
5. Choose/report the configured valuation currency.
6. Persist account snapshot timestamp.
7. Persist every asset balance and price used.
8. Calculate total starting equity.
9. Clone balances into the run's paper portfolio.
10. Mark the run RUNNING only after persistence succeeds.

If the snapshot is incomplete or cannot be valued, fail START rather than silently substituting invented values.

## During a run

Real Kraken account changes are informational only and must not mutate existing paper balances.

The runner supplies each strategy with current market state and its own run-local portfolio. Decisions pass through the paper broker, which updates only that run's ledger.

Multiple strategies can run concurrently. They share market-data infrastructure if convenient, but never financial state.

## STOP

STOP must be scoped by `run_id`.

Stopping one run must not affect:

- other strategies;
- other runs of the same strategy;
- real Kraken state;
- historical records.

Persist final equity and basic performance metrics before marking STOPPED.

## Comparison model

Runs may begin at different timestamps and with different real starting portfolios. Therefore the dashboard must not rank them only by absolute final equity.

Show at least:

- start timestamp;
- start equity;
- current/final equity;
- percentage return;
- realized/unrealized PnL;
- max drawdown;
- fees;
- trade count;
- runtime duration.

A later enhancement should include a passive `START_SNAPSHOT_HOLD` benchmark for each run: what the same starting portfolio would be worth if it had simply been held.

## Kraken credentials

Paper phase credentials are for observation, not execution.

Expected permissions are query/read permissions required to read balances and account information. Do not request order creation, cancellation or withdrawal permissions in this phase.

## Market data

Prefer Kraken/official Kraken CLI for Kraken-native price/market information. External sentiment or cross-exchange data may be used by strategies but must not become the source of account truth.

## AI

AI is a strategy component, not infrastructure authority.

Default local provider: Ollama with configurable Qwen model.

The system should expose an AI interface usable by:

- Bull agent;
- Bear agent;
- Judge agent;
- future direct-strategy reasoning.

AI failures should degrade to HOLD/skip according to strategy policy rather than corrupting the paper ledger.

## Live future

Live trading is intentionally not implemented/enabled in the first phase.

When live is designed later, it must be a separate execution mode with explicit configuration and permissions. Do not make paper-to-live a one-line flag that can accidentally execute real orders.
