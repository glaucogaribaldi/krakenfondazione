# Kraken Fondazione

A lightweight, Kraken-centered paper-trading laboratory derived conceptually from Krynos AI Trading Agent.

## Goal

Run multiple independent paper strategies against the user's **real Kraken portfolio state at the instant each strategy is started**.

Kraken is read-only during the paper phase. A strategy START creates an immutable snapshot of the current Kraken balances and market valuation. From that moment the strategy evolves only in its own paper ledger until STOP.

If the same strategy is started again later, it creates a **new run** from a fresh snapshot of the then-current Kraken portfolio. Old runs remain immutable history.

## Core rule

`START -> REAL KRAKEN SNAPSHOT -> INDEPENDENT PAPER RUN -> STOP`

There is no global reset and no continuous synchronization of paper balances back to the real account.

## Current phase

**PAPER ONLY. LIVE TRADING IS OUT OF SCOPE AND MUST NOT BE ENABLED.**

## Physical architecture

The system is intentionally split into two simple roles:

```text
Ubuntu / TRE OpenClaw
  - krakenfondazione application
  - Kraken read-only snapshot reader
  - strategy manager
  - paper broker and deterministic accounting
  - SQLite ledger
  - Streamlit dashboard
  - run history
          |
          | private/Tailscale OpenAI-compatible API
          v
GPU VPS
  - Nemotron inference only
  - no Kraken credentials
  - no trading execution
  - no authoritative ledger
```

The GPU VPS is replaceable. Model/runtime changes must not require rewriting portfolio or strategy infrastructure.

Initial remote AI target is **NVIDIA Nemotron 3 Nano**. Nemotron 3 Super is not required for the MVP and may be benchmarked later on suitable hardware.

## Reference project

The implementation may reuse/adapt the MIT-licensed architecture and code of:

- https://github.com/falpat/Krynos-AI-Trading-Agent

Krynos already provides Kraken CLI integration, quantitative signals, Bull/Bear/Judge AI debate, SQLite persistence and Streamlit dashboard concepts. This repository changes the portfolio/run model to be Kraken-balance-centric and multi-strategy.

## Start here for TRE / OpenClaw

TRE/OpenClaw must read, in this order:

1. `AGENTS.md`
2. `docs/ARCHITECTURE.md`
3. `docs/STRATEGY_CONTRACT.md`
4. `docs/INSTALL_UBUNTU.md`
5. `docs/VPS_INFERENCE_CONTRACT.md`
6. `OPENCLAW_INSTALL_PROMPT.md`

For preparing the dedicated GPU VPS, use `VPS_PREP_PROMPT.md` with the separate VPS AI/operator.

## First milestone

Build the smallest complete system first:

- install quickly on Ubuntu;
- connect Kraken read-only;
- create immutable START snapshots;
- support multiple independent runs;
- persist all paper state in SQLite;
- expose START/STOP/history in Streamlit;
- connect to the private remote Nemotron endpoint;
- implement `krynos-original`, a simple experimental strategy and `nemotron-nano-team`;
- prove with tests that restarting a stopped strategy creates a new run from the current real Kraken snapshot while preserving all old runs.
