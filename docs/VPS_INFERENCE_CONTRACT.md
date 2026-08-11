# Remote VPS Inference Contract

## Purpose

The remote GPU VPS is a replaceable inference appliance for `krakenfondazione`. It is not part of the financial state boundary.

## Responsibilities

The VPS MAY:

- host one or more AI inference models;
- expose a private OpenAI-compatible API;
- receive bounded prompt context from strategy workers;
- return structured model outputs;
- log sanitized runtime/performance metrics.

The VPS MUST NOT:

- hold Kraken API credentials;
- query the user's Kraken account directly;
- store the authoritative paper ledger;
- own run lifecycle state;
- decide whether a paper trade is financially possible;
- execute real trades;
- receive withdrawal/trading credentials;
- become the only place where strategy definitions exist.

## Initial model

Initial target: NVIDIA Nemotron 3 Nano (31.6B total / 3.6B active family specification).

The exact checkpoint, runtime and quantization are deployment details and must be discovered/verified on the VPS. `krakenfondazione` refers to a logical model identity through configuration rather than hardcoding one vendor tag.

Nemotron 3 Super is not required for the MVP. It may be benchmarked later as a stronger judge/orchestrator if suitable hardware is available.

## Network contract

Preferred connectivity:

`Ubuntu/OpenClaw host -> private/Tailscale network -> VPS OpenAI-compatible endpoint`

Configuration belongs in `.env`, for example:

```text
AI_PROVIDER=openai_compatible
AI_BASE_URL=http://private-host:port/v1
AI_MODEL=nemotron-3-nano
AI_API_KEY=
```

No public unauthenticated endpoint is required.

## Minimum API behavior

The client should be able to:

- check endpoint/model health;
- submit chat completion requests;
- request structured JSON outputs;
- enforce request timeouts;
- distinguish transport/model failure from a valid HOLD decision.

## Failure semantics

Remote AI outage is not database corruption.

When the inference endpoint is unavailable:

- deterministic strategies continue;
- AI-dependent strategies enter `PAUSED_AI_UNAVAILABLE` or equivalent safe state;
- no synthetic decision is invented;
- historical runs remain intact;
- the dashboard exposes AI health clearly.

## Privacy

Send only context needed by the active strategy. Avoid sending API keys, private credentials or unrelated user data in prompts.

## Swapability

The application must make it possible to replace the VPS, inference runtime or model by changing configuration rather than rewriting strategy/accounting code.
