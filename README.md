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

## Reference project

The implementation may reuse/adapt the MIT-licensed architecture and code of:

- https://github.com/falpat/Krynos-AI-Trading-Agent

Krynos already provides Kraken CLI integration, quantitative signals, Bull/Bear/Judge AI debate, SQLite persistence and Streamlit dashboard concepts. This repository changes the portfolio/run model to be Kraken-balance-centric and multi-strategy.

## Start here for OpenClaw

OpenClaw or any coding agent must read, in this order:

1. `AGENTS.md`
2. `docs/ARCHITECTURE.md`
3. `docs/STRATEGY_CONTRACT.md`
4. `docs/INSTALL_UBUNTU.md`

The first implementation milestone is deliberately small: install on Ubuntu, connect Kraken read-only, connect local Qwen via Ollama, create two strategies, support independent START/STOP/new-run behavior, persist to SQLite, and expose a Streamlit dashboard.
