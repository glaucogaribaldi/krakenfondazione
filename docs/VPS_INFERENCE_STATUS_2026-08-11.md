# VPS Inference Status — 2026-08-11

Status: DONE — READY FOR `krakenfondazione` REMOTE INFERENCE.

This file records the final verified baseline reported for the dedicated Nemotron inference VPS used by `krakenfondazione`.

## Host

- Hostname: `instance-20260719-152821`
- OS: Debian GNU/Linux 13 (trixie)
- CPU: 8 vCPU Intel Xeon
- RAM: ~50 GiB
- Disk: 252 GB total, ~205 GB free

## GPU

- GPU count: 2
- GPU model: NVIDIA Tesla T4
- VRAM: 15,360 MiB per GPU
- NVIDIA driver: 550.163.01
- CUDA toolkit compatibility: 12.4
- `nvidia-smi`: PASS
- both GPUs used by the model: PASS
- observed model VRAM: ~10.5 GB + ~11.7 GB

## Inference stack

- Runtime: llama.cpp server
- Runtime version: `1` (commit `84f7129`)
- Model: NVIDIA Nemotron 3 Nano 30B-A3B
- Model source: NVIDIA checkpoint, GGUF conversion/distribution from Unsloth
- Quantization: `UD-Q4_K_XL / Q4_K Medium`
- Model size: ~22.8 GB
- Model hash: NOT VERIFIED
- systemd service: `kraken-nemotron.service`

Commands:

```bash
systemctl status kraken-nemotron
sudo systemctl restart kraken-nemotron
sudo journalctl -u kraken-nemotron -f
```

## Private API

- Tailscale: running
- Private base URL: `http://100.73.54.72:8080/v1`
- OpenAI-compatible: YES
- Publicly exposed: NO
- listener restricted to the Tailscale interface/IP

Verified endpoints:

- `/v1/models`: PASS
- `/v1/chat/completions`: PASS

## Runtime tests

| Test | Status |
|---|---|
| GPU physically available | PASS |
| NVIDIA driver operational | PASS |
| Model load on both GPUs | PASS |
| Real completion (`OK`) | PASS |
| Structured JSON | PASS |
| 10 sequential requests | PASS |
| 2 concurrent requests | PASS |
| Generation performance baseline | ~52.5 tokens/s in reported JSON test |
| systemd service restart | PASS |
| full VPS reboot recovery | PASS |
| Tailscale after reboot | PASS |
| API after reboot | PASS |

## Isolation and security

The VPS is an inference-only appliance.

Reported sanitized checks found no active or indexed installation/configuration for:

- Kraken trading software;
- Coinbase tooling;
- Hummingbot;
- Freqtrade;
- OpenClaw;
- Ollama;
- vLLM;
- SGLang.

Reported trading credentials present: NO.

The VPS must continue to receive only the minimum market/run context required for inference. Kraken credentials, SQLite databases, full paper ledgers and trading authority belong exclusively on the Ubuntu `krakenfondazione` host.

## Handoff contract to TRE/OpenClaw

TRE may now treat the following as the verified remote inference baseline:

```text
AI_PROVIDER=openai_compatible
AI_BASE_URL=http://100.73.54.72:8080/v1
AI_MODEL=<discover exact model ID from /v1/models during installation>
AI_API_KEY=
```

Important: do not guess or hardcode the model ID from documentation. During installation, TRE must query `/v1/models`, persist the actual returned identifier in `.env`, and run a real chat completion smoke test.

If the endpoint is unavailable, AI-dependent strategies must pause without affecting deterministic strategies or corrupting active paper ledgers.

## Remaining non-blocking gap

- GGUF/model SHA256: NOT VERIFIED.

This does not block paper experimentation, but the exact model artifact hash should be captured later for strict reproducibility.
