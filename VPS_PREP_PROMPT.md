# VPS Preparation Prompt — Nemotron Inference Appliance

Give this entire prompt to the AI/operator that manages the dedicated VPS.

---

You are preparing a dedicated GPU VPS to act only as the remote AI inference appliance for `glaucogaribaldi/krakenfondazione`.

## Mission

Transform the current Debian/Ubuntu-compatible VPS into a clean, minimal, reproducible Nemotron inference server. The trading application, Kraken credentials, paper ledger, dashboard and OpenClaw must NOT live on this VPS. This machine serves models only.

Known machine state at handoff:

- Linux/Debian cloud VM
- 8 vCPU
- about 50 GiB RAM
- about 252 GB disk with >230 GB free
- NVIDIA GPU hardware is expected, but `nvidia-smi` currently fails because the NVIDIA driver is missing, broken or not bound correctly
- no swap currently configured

Do not assume the exact GPU model or count until verified from PCI/cloud metadata.

## Non-negotiable boundaries

The VPS must contain NO:

- Kraken API keys or secrets;
- trading execution code;
- paper ledger or portfolio database;
- OpenClaw installation unless explicitly requested later;
- Hummingbot/Freqtrade/Coinbase legacy services;
- old Fondazione runtime;
- public unauthenticated model endpoint exposed to the Internet.

The machine should expose one private, OpenAI-compatible inference endpoint reachable from the Ubuntu/OpenClaw host through Tailscale or another private network.

## Phase 0 — Forensic inventory before cleanup

Before deleting or changing anything, record a short sanitized inventory:

```bash
hostnamectl
cat /etc/os-release
uname -a
lscpu
free -h
df -h
lsblk
lspci | grep -i -E 'nvidia|vga|3d' || true
lsmod | grep -i nvidia || true
which nvidia-smi || true
nvidia-smi || true
dpkg -l | grep -E 'nvidia|cuda|docker|ollama|vllm|sglang' || true
systemctl --type=service --state=running
ss -lntup
```

Identify anything that appears business-critical or unrelated to this project before removal. Do not delete SSH, cloud-init, networking, Tailscale or the account used for remote access.

## Phase 1 — Clean the machine

Remove obsolete AI/trading runtimes, abandoned virtual environments, stale containers/images, old model caches and legacy project directories only after they are positively identified as disposable.

Preserve:

- SSH access;
- cloud guest agent;
- Tailscale if already functioning;
- system networking;
- package manager integrity;
- user home data that is not clearly part of an obsolete AI/trading project.

After cleanup, report disk usage and running services again.

## Phase 2 — Repair and verify NVIDIA GPU support

Do not install random CUDA versions blindly.

1. Detect actual NVIDIA hardware from PCI/cloud metadata.
2. Install the appropriate Debian-supported/NVIDIA driver path for that hardware and current kernel.
3. Reboot if required.
4. After reboot, require all of these to succeed:

```bash
nvidia-smi
nvidia-smi -L
```

Record:

- GPU model(s);
- GPU count;
- VRAM per GPU;
- driver version;
- reported CUDA compatibility;
- temperatures and idle memory use.

If GPU hardware is not attached, STOP and report BLOCKED rather than installing inference software.

## Phase 3 — Runtime choice

The initial target model is NVIDIA Nemotron 3 Nano, approximately 31.6B total / 3.6B active parameters. Do NOT install Nemotron 3 Super 120B on this 50 GiB RAM / expected T4-class machine as the default deployment.

Choose the lightest stable inference runtime that:

- supports the verified GPUs;
- can serve the selected Nemotron checkpoint/quantization;
- provides an OpenAI-compatible HTTP API;
- supports restart via systemd;
- can bind only to localhost/Tailscale/private interface;
- has a simple health check.

Preferred order for this machine:

1. `llama.cpp` server if a validated GGUF build of the chosen Nemotron 3 Nano checkpoint is available and compatible;
2. Ollama if it supports the chosen checkpoint cleanly;
3. SGLang/vLLM only if hardware/runtime compatibility is verified and they materially improve deployment.

Do not force Ollama merely because it was mentioned in early planning. Choose based on actual model compatibility and measured stability.

## Phase 4 — Model installation

Install one Nemotron model first. Do not load multiple large models simultaneously during MVP.

Preferred logical model identity:

`nemotron-3-nano`

The exact repository/file/tag must be verified at installation time from official NVIDIA/model sources. Do not invent a model tag.

If quantization is required for the available VRAM, select a practical quantization after measuring fit and quality. Record the exact model source, file/tag, digest/hash when available, quantization and disk size.

## Phase 5 — Private API service

Expose an OpenAI-compatible API with at least:

- `GET /v1/models` or equivalent model-list endpoint;
- `POST /v1/chat/completions` or equivalent chat completion endpoint;
- a simple health check.

Bind to a private interface only. Prefer Tailscale. Do not open the inference port to `0.0.0.0` on the public Internet unless an explicit firewall rule restricts it to the trusted source.

Create a systemd service so the inference server starts automatically after reboot and restarts on failure.

No trading credentials belong on this service.

## Phase 6 — Performance and stability smoke test

Run and record:

1. cold model load;
2. simple one-turn completion;
3. structured JSON response test;
4. 10 sequential requests;
5. at least 2 concurrent requests if supported;
6. GPU memory usage during inference;
7. approximate prompt-processing and generation throughput;
8. service restart test;
9. full VM reboot and post-reboot health test.

Do not claim multi-GPU use unless `nvidia-smi` and runtime logs actually show it.

## Phase 7 — Delivery contract

At completion provide a sanitized report containing only:

- hostname;
- OS;
- CPU/RAM/disk;
- GPU model/count/VRAM;
- NVIDIA driver version;
- inference runtime and version;
- exact model identity and quantization;
- private inference base URL, preferably using Tailscale hostname/IP rather than public IP;
- API compatibility (`OpenAI-compatible` yes/no);
- systemd service name;
- commands for `status`, `restart`, logs and health test;
- measured tokens/sec or equivalent throughput;
- reboot recovery result;
- whether the endpoint is publicly exposed (must normally be NO);
- remaining blockers.

Never include API keys, SSH keys, tokens or other secrets in the report.

## Definition of DONE

DONE means:

- obsolete project runtime removed without breaking remote administration;
- NVIDIA GPU works and is identified;
- one Nemotron 3 Nano inference model is installed and actually responds;
- endpoint is OpenAI-compatible and private;
- service survives reboot;
- no trading secrets/code exist on this VPS;
- a sanitized handoff report is produced for OpenClaw/TRE.

If any of these are not proven, mark them `NOT VERIFIED` or `BLOCKED` rather than assuming success.

---
