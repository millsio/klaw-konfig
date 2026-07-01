---
mem_id: 6f816675-d9a2-498e-b844-2fd8fe25bf02
title: "OPENCLAW PROJECT \u2014 Configuration & Models"
created_at: 2026-06-13T04:56:25.782Z
updated_at: 2026-06-15T04:16:27.955Z
source: mem:OPENCLAW PROJECT
---

# OPENCLAW PROJECT — Configuration & Models

## Current Status

Active. **Primary model changed to qwen3.6:27b (dense) on 2026-06-14, applied and VRAM-verified.** Running with flash attention + q8\_0 KV cache (global Ollama host env vars) and a pinned 110K context. See the Model Strategy & Orchestration note for the full decision rationale and the longer-term orchestration design.

## Last Updated

2026-06-15

## Key Decisions

- **Primary model: ollama/qwen3.6:27b** (dense), replacing mistral-small3.2:24b. Chosen for agentic tool-calling, robustness, and quantization-tolerance on the 24GB card. Full reasoning in the Model Strategy & Orchestration note.
- **Flash attention ON + q8\_0 KV cache.** These are GLOBAL Ollama-host environment variables (OLLAMA\_FLASH\_ATTENTION=1, OLLAMA\_KV\_CACHE\_TYPE=q8\_0), set on the Windows host and applied to ALL models Ollama serves — they cannot be set per-model or via Modelfile. Do NOT use q4\_0 (degrades Qwen's long-doc + tool-calling).
- **Context pinned at 110000**, aligned across both layers: OpenClaw `contextWindow: 110000` (compaction budget) AND `params.num_ctx: 110000` (forwarded to Ollama). Both must match so OpenClaw's compaction fires before the physical cache overflows.
- The earlier note that "Gemma is NOT in the verified inventory" is now OBSOLETE — gemma4:31b and gemma4:26b are both installed (and gemma4:31b was tool-tested and VRAM-tested). Inventory table updated below.
- mistral-small3.2:24b is retained as the prior/fallback model, no longer primary.
- tools.profile is FULL (set during Mem MCP integration); bundle-mcp in tools.allow exposes Mem tools. Gateway restart required after profile/model/context changes.
- Named sessions preferred; always `openclaw chat --session <name>`.

## Summary

This note contains verified configuration facts. The primary model is **qwen3.6:27b** (dense), accessed via the Ollama provider at 10.10.10.1:11434 from the VM, running flash attention + q8\_0 cache at a pinned 110K context. Mem MCP is integrated and operational. Model-selection rationale and orchestration strategy live in the Model Strategy & Orchestration note.

***

## OpenClaw Version

- OpenClaw: 2026.6.5
- Gateway: 2026.6.5

***

## Agent Defaults

`agents.defaults.model` = `"ollama/qwen3.6:27b"` (plain string form; was previously an object with `primary: ollama/mistral-small3.2:24b`).

Other defaults (unchanged): workspace `/home/klaw/.openclaw/workspace`, maxConcurrent 4, subagents {maxConcurrent 8, archiveAfterMinutes 60}.

Test agent retained in `agents.list`: `gemma-test` (model `ollama/gemma4:31b`, workspace `~/.openclaw/workspace-gemma-test`) — isolated, does not affect the default agent.

***

## Ollama Provider Configuration

Source: `models.providers.ollama` in openclaw\.json

- Base URL: <http://10.10.10.1:11434> (from the VM via OllamaSwitch)
- **contextWindow: 110000** (OpenClaw's prompt/compaction budget)
- Model entry: `{ id: "qwen3.6:27b", name: "qwen3.6:27b", params: { num_ctx: 110000, keep_alive: "30m" } }`
- **Host-side global env vars (Windows):** OLLAMA\_FLASH\_ATTENTION=1, OLLAMA\_KV\_CACHE\_TYPE=q8\_0. Set via `setx`, require full Ollama restart (tray → Quit → relaunch) to take effect. Confirmed live via server.log (`flash_attn = enabled`, `K/V (q8_0)`).
- Prior config had OLLAMA\_KEEP\_ALIVE -1 for the resident mistral model; qwen now uses per-model keep\_alive 30m.

### VRAM verification (2026-06-14/15) — qwen3.6:27b at 110K

- `nvidia-smi`: \~21,034 MiB / 24,564 MiB used, **100% GPU, \~3.5GB headroom**.
- Held FLAT at \~21GB while filling context to \~96K under live use — no creep, no spill, no host RAM/disk molasses (the opposite of gemma4:31b's behavior). Pre-allocation confirmed: cache reserved at load, filling it does not grow VRAM.
- `ollama ps` showed CONTEXT 110000 at 100% GPU (but note: `ollama ps`/`ollama run` "100% GPU" is NOT a reliable saturation signal — use `nvidia-smi` for true VRAM).
- GPU core temp spiked to \~73-79°C at \~440W / 95-100% util during generation, idling \~41°C. Safe for a 3090 Ti (throttle \~83-88°C), but these were bursty human-paced tests; sustained 24/7 autonomy should be thermally re-checked (incl. VRAM junction temp, not shown by nvidia-smi).
- Contrast: gemma4:31b at 32K measured 23,346/24,564 MiB (\~1.2GB headroom, redline) and spilled to host RAM/disk under load — a key reason it was not chosen.

***

## Verified Installed Models (inventory as of 2026-06-14)

From `ollama list` (weights size; context = model max unless pinned):

| Model                 | Size   | Notes                                                                             |
| --------------------- | ------ | --------------------------------------------------------------------------------- |
| **qwen3.6:27b**       | 17 GB  | **PRIMARY.** Dense. Pinned to 110K ctx (model max \~256K). Flash attn + q8\_0.    |
| qwen3-coder:30b       | 18 GB  | Coding specialist (future coding subagent / on-demand).                           |
| deepseek-coder:33b    | 18 GB  | Coding specialist (on-demand).                                                    |
| qwq:32b               | 19 GB  | Reasoning specialist (on-demand).                                                 |
| gemma4:31b            | 19 GB  | Tool-tested OK; rides VRAM redline at 32K — not chosen. gemma-test agent uses it. |
| gemma4:26b            | 17 GB  | MoE (A4B). Most quant-sensitive model tested (avoid q8\_0 cache with it).         |
| mistral-small3.2:24b  | 15 GB  | Prior primary / fallback. Context max 131072.                                     |
| qwen2.5:14b           | 9.0 GB | Lightweight option.                                                               |
| llama3.3:latest       | 42 GB  | Too large to run on 24GB (would heavily spill).                                   |
| llama3:8b             | 4.7 GB | Lightweight/legacy.                                                               |
| embeddinggemma:latest | 621 MB | Embeddings for RAG/vector; tiny, can co-reside.                                   |

(Cloud-only models like glm/minimax/kimi/deepseek-v4 are not local and not in scope for VRAM planning.)

***

## Tools Configuration

```json
{
  "profile": "full",
  "allow": ["bundle-mcp"],
  "web": { "search": { "enabled": true, "provider": "parallel-free" } }
}
```

### Profile Notes

- tools.profile=full is current (changed from minimal during Mem MCP integration).
- bundle-mcp in tools.allow exposes Mem MCP tools across profiles.
- tools.profile=coding adds \~11k token baseline and caused \~65s response times — avoid.
- tools.profile=minimal hides MCP tools even with bundle-mcp in allow list.
- Gateway restart required after any profile/model/context change.

***

## Mem MCP Server

- Server name: mem
- URL: <https://mcp.mem.ai/mcp>
- Transport: streamable-http
- Auth: Bearer token (literal header — doctor warning exists, acceptable for now; secrets-hygiene item open)
- Timeouts: connect=10000ms, request=30000ms
- Tool filter (include only): search\_notes, get\_note, create\_note, update\_note, list\_notes, list\_collections, get\_collection, search\_collections, add\_note\_to\_collection, find\_related\_notes, move\_note

Verify with: `openclaw mcp status --verbose`

***

## Session Configuration

### Interactive Terminal Session Command

```bash
openclaw chat --session <name>
```

Target a specific agent with `--session agent:<id>:<key>` (e.g. `agent:gemma-test:main`). The bare default agent is `agent:main:<key>`. Always use a named session.

### Session Hygiene Rules

- Fresh sessions start at \~8-11k tokens (full profile with Mem).
- Historically, sessions degraded above \~20-25k tokens on mistral — Klaw lost tool awareness and hallucinated. (To re-evaluate on qwen3.6:27b, which has far more usable context.)
- Start a new named session when behavior becomes erratic.
- `openclaw sessions cleanup --fix-missing --enforce` removes stale index entries after manual file deletion.

### Session Storage Location

`~/.openclaw/agents/<agentId>/sessions/`

***

## Gateway Configuration

- Port: 18789
- Bind: 127.0.0.1 (loopback only)
- Dashboard: <http://127.0.0.1:18789/>
- Auth token: enabled
- Tailscale exposure: disabled

***

## openclaw docs CLI

`openclaw docs <query>` searches the live docs index (CLI-only, not an agent tool yet). `https://docs.openclaw.ai/llms.txt` is the full index; append `.md` to any page URL for clean Markdown. (Local mirror of this lives at `~/.openclaw/docs/` — see Documentation & Knowledge Management note.)

***

## Workspace

- Path: /home/klaw/.openclaw/workspace
- Scripts: \~/.openclaw/scripts/ (mirror script lives here)
- Docs mirror: \~/.openclaw/docs/ (operational, 684 pages)

***

## Agent Identity

- Agent name: Klaw
- User name: Brian
- Style preference: practical and concise

***

## Recent Updates

- 2026-06-13: Configuration note created from legacy consolidation; Mem MCP integrated; tools.profile=full; session hygiene documented; openclaw docs CLI documented.
- 2026-06-14/15: **Primary model switched to qwen3.6:27b (dense)** from mistral-small3.2:24b. Enabled flash attention + q8\_0 KV cache (global host env vars, confirmed via server.log). Pinned context to 110000 aligned across contextWindow + params.num\_ctx. VRAM-verified: \~21GB/24GB, 100% GPU, flat under load to \~96K fill, \~3.5GB headroom — stable, no spill. Updated the installed-models inventory (Gemma is installed; qwen3.6/gemma4/coders/embeddinggemma added). gemma-test agent retained. Decision rationale + orchestration design captured in the new Model Strategy & Orchestration note.
