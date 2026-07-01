---
mem_id: fdf997f6-f8ad-4194-bd1d-22796ead2862
title: "OPENCLAW PROJECT \u2014 Architecture"
created_at: 2026-06-13T04:55:34.963Z
updated_at: 2026-06-22T01:32:43.793Z
source: mem:OPENCLAW PROJECT
---

# OPENCLAW PROJECT — Architecture

## Current Status

Active. Infrastructure operational.

## Last Updated

2026-06-21

## Key Decisions

- Ollama runs on Windows host OS for direct GPU access.
- OpenClaw runs inside Hyper-V Ubuntu VM for isolation and experimentation.
- RTX 3090 (pacifico) is the current primary build/compute platform.
- RTX 5090 (amethyst) is a planned second host — near-term role is an additional **Ollama endpoint** for Gemma (NO second VM/gateway for now); fuller multi-node build is later. See Model Strategy & Orchestration.
- **Primary local model is qwen3.6:27b (dense)** on the 3090 (flash attention + q8\_0 KV cache, pinned 110K context, VRAM-verified). mistral-small3.2:24b is the fallback. (Corrected 2026-06-21: this note's diagram/Control Plane previously still showed mistral resident — stale, predated the 2026-06-14/15 qwen migration.)
- **Firecracker microVM layer DEMOTED to someday/maybe (2026-06-21).** Rationale: OpenClaw ships NO Firecracker backend; its built-in sandbox (Docker default / SSH / OpenShell) plus the existing Hyper-V VM boundary already cover the isolation need at far lower effort. The Hyper-V VM is already a STRONGER boundary than Docker, so the nearer-term win is turning ON OpenClaw's built-in sandbox (config, not a build), not constructing a Firecracker layer. Firecracker stays on the long-tail list as an optional future exploration only.
- OpenClaw VM Lab Setup note is considered early experimentation and is not part of the authoritative architecture.

## Summary

The current architecture places Ollama on the Windows 11 Pro host with GPU access and OpenClaw inside an Ubuntu Hyper-V VM. A dedicated virtual switch (OllamaSwitch) provides isolated networking between the VM and the host Ollama instance. The Ubuntu VM is named KlawMachine. The primary local model is qwen3.6:27b (dense). This architecture was validated through performance testing and is considered stable. Isolation for tool execution is provided nearer-term by OpenClaw's built-in sandbox on top of the Hyper-V VM; Firecracker is demoted to optional/future.

***

## Current Verified Architecture

```
Windows 11 Pro Host (RTX 3090 — pacifico)
│
├─ Ollama
│   ├─ qwen3.6:27b  (PRIMARY, resident; flash attn + q8_0 KV cache, 110K ctx)
│   └─ mistral-small3.2:24b  (fallback)
│
├─ Hyper-V
│
├─ Default Switch (172.18.192.1/20)
│   └─ Internet path
│
└─ OllamaSwitch (10.10.10.1/24)
    └─ Dedicated Ollama network

Ubuntu VM (KlawMachine)
│
├─ eth0 → Default Switch (DHCP, Internet)
├─ eth1 → OllamaSwitch (static: 10.10.10.2/24, no default gateway)
│
├─ OpenClaw Gateway (openclaw-gateway.service, active/running)
│
└─ Klaw
    └─ ollama/qwen3.6:27b  (→ 10.10.10.1:11434)

RTX 5090 Host (amethyst — planned, near-term)
└─ Ollama endpoint only (Gemma) — reached as models.providers.amethyst-ollama
   (NO second VM / gateway in the near-term plan)
```

***

## Control Plane

- Ubuntu VM running OpenClaw (agent name: Klaw)
- **Tool-execution isolation:** OpenClaw's built-in sandbox (Docker default / SSH / OpenShell backends) layered on top of the Hyper-V VM boundary — the nearer-term, config-only isolation path.
- Future (optional): Firecracker microVM execution layer — DEMOTED to someday/maybe (OpenClaw has no Firecracker backend; built-in sandbox + VM cover the need).
- Future: deterministic model manager / dispatcher.

***

## Compute Plane

- RTX 3090 system (pacifico) — Ollama host, current primary inference node (qwen3.6:27b).
- RTX 5090 system (amethyst) — near-term: additional Ollama endpoint (Gemma) for the role-split / debate council; later: full cluster node (inference + training) with its own OpenClaw VM.

***

## Architecture Principles

- Ollama is preferred outside the VM for direct GPU access.
- OpenClaw is preferred inside VM(s) for isolation and safe experimentation.
- Prefer config-level isolation (built-in sandbox) over building new microVM infrastructure.
- VM snapshots are used at key milestones.

***

## Future Multi-Node Direction

Current thinking (near-term Gemma endpoint is simpler than this full build):

```
3090 Host (pacifico)            5090 Host (amethyst)
├─ Ollama (qwen primary)        ├─ Ollama (Gemma)   ← near-term: endpoint only
└─ OpenClaw VM (KlawMachine)    └─ OpenClaw VM       ← later: full multi-node
```

Near-term: amethyst serves Gemma to pacifico's existing gateway as a second provider — no second VM. Full multi-node (second OpenClaw VM + cross-node co-orchestration) is a later track. Networking/specialization decisions deferred until the 5090 VM exists. See Model Strategy & Orchestration and Networking & Infrastructure.

***

## Tool-Execution Isolation: built-in sandbox (nearer-term) vs Firecracker (demoted)

OpenClaw provides a built-in sandbox for tool/command execution: `agents.defaults.sandbox` with Docker (default), SSH, or OpenShell backends; modes off / non-main / all; per-agent/session/shared scope; GPU passthrough; read-only secret binds. Docs note it is "not a perfect security boundary," but layered on the Hyper-V VM it is a meaningful, config-only improvement over running tools unsandboxed.

- **Nearer-term decision (2026-06-21):** turn ON the built-in sandbox as part of hardening. This closes the tool-execution isolation gap with configuration, not construction.
- **Firecracker — DEMOTED to someday/maybe:** OpenClaw has no Firecracker backend, so a Firecracker layer would be custom infrastructure delivering isolation the VM + built-in sandbox already approximate. Kept only as an optional future exploration.

Original (now-deprioritized) Firecracker vision, retained for reference: ephemeral microVM creation, sandboxed research execution, disposable coding environments, automatic teardown (e.g. Telegram request → create microVM → gather/analyze → return report → destroy). Prerequisites if ever revisited: verify nested virtualization + /dev/kvm inside the Hyper-V VM; test Firecracker install; design the sandbox workflow.

***

## Future: Intelligent Model / Profile Routing

A key future architectural goal is automatic selection of the most appropriate:

- OpenClaw tools profile (minimal, full, coding, etc.)
- Ollama model

based on task type, latency requirements, and required capabilities.

Example concept:

- Simple factual query → minimal profile + lightweight model
- Research task → full profile + web-enabled configuration
- Coding task → coding profile + coding-capable model
- Deep reasoning task → reasoning-oriented model (QwQ / Gemma judge)

This intelligent orchestration layer is considered a significant future milestone, separate from the current project-memory and documentation focus. (Note: OpenClaw provides the routing primitives — per-agent models, fallback chains, `/new <model>`, multi-agent bindings — but the "decide by task/complexity" layer is architected on top.)

***

## Architecture Evolution

### May 2026 — Initial Lab Setup

Early experimentation used VMware Workstation Pro (not Hyper-V). OpenAI/GPT-5.5 was used as the initial model. Discord was the initial channel. This phase is documented in the legacy OpenClaw VM Lab Setup note and is not part of the authoritative architecture.

### June 10–11, 2026 — Hyper-V + Ollama Integration

Migrated to Hyper-V. Switched to local Ollama models. Established dedicated OllamaSwitch networking. This is the current authoritative architecture.

### June 14–15, 2026 — Primary model → qwen3.6:27b

Primary local model migrated from mistral-small3.2:24b to qwen3.6:27b (dense). Full detail in Configuration & Models and Model Strategy & Orchestration.

***

## Open Questions

- Final multi-node networking architecture between 3090 (pacifico) and 5090 (amethyst) nodes.
- Whether Ollama will remain on host OS or move into its own VM in a future configuration.
- (Low priority) Firecracker feasibility inside a Hyper-V VM — only if the demoted Firecracker track is ever revisited.

***

## Recent Updates

- 2026-06-13: Architecture note created from legacy source consolidation. Corrections applied: all work confirmed on RTX 3090 (not 5090). VMware Lab Setup confirmed as excluded from authoritative architecture.
- 2026-06-21: **Corrected the stale primary model** in the diagram + Control Plane + Compute Plane (mistral-small3.2:24b → qwen3.6:27b dense; mistral now fallback) — the note had not been touched since 2026-06-13 and predated the qwen migration. **Demoted Firecracker to someday/maybe and promoted OpenClaw's built-in sandbox** (Docker/SSH/OpenShell on top of the Hyper-V VM) as the nearer-term, config-only isolation path; added a dedicated section. Added amethyst (5090) as a near-term Ollama-endpoint-only node (Gemma) feeding pacifico's gateway, distinct from the later full multi-node build.
