# Ubuntu Installation Target

This document defines what OpenClaw must make true. It is an installation contract, not a claim that the implementation already exists.

## Desired user experience

```bash
git clone https://github.com/glaucogaribaldi/krakenfondazione.git
cd krakenfondazione
./scripts/install.sh
./scripts/run.sh
```

Then open the Streamlit dashboard printed by the launcher, normally on localhost.

## Installer responsibilities

`scripts/install.sh` should be idempotent where practical and should:

1. Detect Ubuntu and architecture.
2. Verify Python 3.10+ compatible with actual dependencies.
3. Install missing OS packages required by the project.
4. Create `.venv` and upgrade pip tooling.
5. Install Python dependencies.
6. Install or verify official Kraken CLI.
7. Verify `kraken status` and a public ticker request.
8. Install or verify Ollama.
9. Verify that a configured Qwen model exists; if absent, clearly offer/pull the configured model.
10. Copy `.env.example` to `.env` only when `.env` does not exist.
11. Initialize/migrate SQLite.
12. Run unit/smoke tests.
13. Print exactly what remains for the user: add read-only Kraken credentials if missing, then run the application.

Never overwrite an existing `.env` or expose credentials in logs.

## Environment variables

At minimum support:

```text
PAPER_ONLY=true
KRAKEN_API_KEY=
KRAKEN_API_SECRET=
AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
OLLAMA_MODEL=qwen3:8b
DATABASE_URL=sqlite:///data/krakenfondazione.db
DASHBOARD_HOST=127.0.0.1
DASHBOARD_PORT=8501
```

The actual Qwen model is configurable. Do not assume `qwen3:8b` is installed.

## Kraken key

During the paper phase use an API key limited to account/query/read permissions. Do not require permissions for:

- creating or modifying orders;
- cancelling orders;
- withdrawals/transfers.

The application should fail closed if its configuration indicates live execution is requested during the paper-only milestone.

## Launcher

`scripts/run.sh` should start the minimal required processes and print status. Prefer a simple local Python/Streamlit deployment over Docker/microservices for the MVP.

A later systemd installer may be added after the interactive MVP works.

## Smoke test

Installation is considered useful only when a smoke test proves:

- Python imports work;
- SQLite is writable;
- Kraken public market data works;
- configured read-only account access works when credentials are present;
- Ollama endpoint responds;
- configured model can produce a minimal response;
- the dashboard can start;
- live execution remains disabled.
