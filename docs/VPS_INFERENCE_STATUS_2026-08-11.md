# VPS Inference Status — 2026-08-11

Status: IN PROGRESS — not DONE.

This file records the verified baseline reported for the dedicated Nemotron inference VPS used by `krakenfondazione`.

## Verified host state

- Hostname: `instance-20260719-152821`
- OS: Debian GNU/Linux 13 (trixie)
- Kernel: `6.12.101+deb13-cloud-amd64`
- CPU: 8 vCPU Intel Xeon
- RAM: ~50 GiB
- Disk: 252 GB total, ~226 GB free
- Swap: absent

## Verified GPU state

- GPU count: 2
- GPU model: NVIDIA Tesla T4
- VRAM: 15,360 MiB per GPU (~30 GiB aggregate)
- NVIDIA driver: 550.163.01
- CUDA toolkit: 12.4
- Idle VRAM: ~1 MiB per GPU
- Temperature: ~51–53 C
- `nvidia-smi`: PASS
- `nvidia-smi -L`: PASS

## Network and isolation

- Tailscale: running
- Tailscale IP: `100.73.54.72`
- Public inference exposure: none yet

The VPS remains an inference-only appliance. It must not hold Kraken credentials, trading ledgers, OpenClaw, broker execution code, or financial state.

## Planned inference stack

- Runtime target: `llama.cpp` with CUDA
- Model target: NVIDIA Nemotron 3 Nano 30B-A3B
- Planned format: GGUF Q4-class quantization suitable for T4 hardware
- Proposed artifact at this stage: `Unsloth/Nemotron-3-Nano-30B-A3B-GGUF:UD-Q4_K_XL`

The exact downloaded artifact is NOT VERIFIED until successfully fetched, hashed/identified and loaded.

## Current runtime state

- CUDA compiler: verified
- CMake: verified
- llama.cpp source: downloaded
- llama.cpp release: `b10359`
- CUDA architecture target: 7.5
- `llama-server`: NOT BUILT / NOT VERIFIED
- Nemotron model: NOT DOWNLOADED
- API: NOT CONFIGURED
- systemd service: NOT CONFIGURED

The first CUDA build did not produce the expected binary. It reportedly reached ~13 GB RAM usage before termination. Root cause is NOT VERIFIED.

## Test matrix

| Test | Status |
|---|---|
| GPU physically available | PASS |
| NVIDIA driver operational | PASS |
| GPU survives reboot | PASS |
| Tailscale survives reboot | PASS |
| llama-server build | NOT VERIFIED |
| Nemotron model load | NOT VERIFIED |
| OpenAI-compatible API | NOT VERIFIED |
| Structured JSON | NOT VERIFIED |
| Concurrent requests | NOT VERIFIED |
| Performance measurement | NOT VERIFIED |
| systemd restart recovery | NOT VERIFIED |
| full reboot inference recovery | NOT VERIFIED |
| complete trading-credential audit | NOT VERIFIED |

## Current blocker

`BLOCKED: llama.cpp CUDA has not yet produced a working llama-server binary.`

Next required work:

1. recover the exact build log / exit condition;
2. rebuild with constrained parallelism if memory pressure is involved;
3. verify `llama-server` before downloading the model;
4. download one GGUF only;
5. run an actual GPU model load;
6. expose the API only on the private/Tailscale interface;
7. validate `/v1/models` and `/v1/chat/completions` or equivalent;
8. test structured output, sequential and concurrent requests;
9. create a persistent systemd service;
10. perform restart and full reboot recovery tests;
11. complete a sanitized audit proving no trading credentials are present.

Do not mark the VPS inference service as READY in `krakenfondazione` until all required tests above pass and a concrete private base URL plus model identifier are provided.
