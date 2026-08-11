# Strategy Contract

A strategy is a plugin. The infrastructure must not need to be rewritten to add a strategy.

## Required identity

Each strategy has a stable ID and human-readable name.

Example:

```python
STRATEGY_ID = "qwen-experimental"
DISPLAY_NAME = "Qwen Experimental"
```

## Inputs

A strategy receives a context containing at least:

- `run_id`
- immutable `start_snapshot`
- current paper portfolio
- current market data
- recent market history required by the strategy
- strategy configuration
- optional AI provider/debate service

A strategy must never read or mutate another run's portfolio.

## Output

Return a structured proposal, for example:

```python
Decision(
    action="BUY",        # BUY | SELL | HOLD
    symbol="BTC/USD",
    quantity=None,
    notional=25.0,
    confidence=0.71,
    reason="EMA crossover confirmed by momentum",
    metadata={}
)
```

The exact implementation may use dataclasses/Pydantic and Decimal values. Avoid free-form strings as the execution contract.

## Independence

Strategy code proposes actions. The paper broker is responsible for applying fills, fees, balances and portfolio accounting.

A strategy must not directly write fake fills or balances into SQLite.

## Versioning

Persist a strategy version or code/config hash with every run so historical results remain attributable to the logic that produced them.

Changing strategy logic must not retroactively change old runs.

## AI usage

Strategies may be:

- purely quantitative;
- quantitative + Bull/Bear/Judge;
- AI-led with deterministic validation;
- experimental.

AI output must be recorded when it contributes to a decision.

AI failure should normally result in HOLD/SKIP for that cycle, not ledger corruption.

## Initial strategies

### krynos-original

Adapt the upstream Krynos approach as faithfully as practical:

- EMA crossover;
- RSI;
- MACD;
- Bollinger Bands;
- sentiment/context where available;
- Bull/Bear debate;
- Judge decision.

### qwen-experimental

A deliberately easy-to-edit sandbox strategy for rapid experimentation with local Qwen.

Keep its configuration external so OpenClaw can quickly change prompt, indicators, time horizon, confidence threshold and sizing rules without touching core infrastructure.

## Adding strategies

Target workflow:

1. Create one file in `app/strategies/`.
2. Implement/register the strategy interface.
3. Add tests.
4. Restart/reload the application if required.
5. Strategy appears in dashboard with START.

The eventual strategy count is not limited to five.
