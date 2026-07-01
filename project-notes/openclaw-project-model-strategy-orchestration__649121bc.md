---
mem_id: 649121bc-abf7-459b-a504-63436f0dc4f3
title: "OPENCLAW PROJECT \u2014 Model Strategy & Orchestration"
created_at: 2026-06-15T02:58:12.112Z
updated_at: 2026-06-28T03:37:04.749Z
source: mem:OPENCLAW PROJECT
---

# OPENCLAW PROJECT — Model Strategy & Orchestration

## Current Status

Active. Primary local model is **qwen3.6:27b (dense)** on the 3090 (pacifico), applied + VRAM-verified (see Configuration & Models / Checkpoints). 2026-06-16: added Multi-Node Co-Orchestration design. 2026-06-21: added the qwen-workhorse / Gemma role-split, cross-host resource-sharing, the Debate Council, nodes-vs-gateways terminology. 2026-06-22: Debate Council design finalized (debaters locked, symmetric peer-critic roles, self-assessed ripeness gate, Opus judge with leashed web search + hard cap, full persistence, two-clock cadence); fp16 KV-cache baseline corrected; Gemma debater target 80K fp16. 2026-06-22 (late session): added PROPOSED-but-not-yet-crystallized refinements — a prep/case-construction phase, the long-many-cycle local-debate economic rationale + cost reframe, Opus as agenda-setter (the flywheel), and operational caveats for long sustained runs. **2026-06-22 (build session): NEXT ACTION COMPLETE — amethyst's gemma4:31b is registered, authed, and live as the **`amethyst-ollama`** provider on pacifico's gateway; routed via the **`gemma-amethyst`** agent; 80K fp16 VRAM-verified flat under fill (27,788 MiB from load through 50K real context). Debater-B endpoint is operational. Stress test also surfaced two NEW open items: compaction did NOT fire at the context ceiling (errored instead), and **`/reset`**/**`/new`\*\* falls back to the global default model not the agent pin. See the Recipe addendum and Open Follow-ups.\*\*

## Last Updated

2026-06-27

## Key Decisions

- **Primary local model: qwen3.6:27b (DENSE).** Chosen over gemma4:31b, gemma4:26b, and mistral-small3.2:24b for an agentic, tool-calling, autonomy-bound workload on a single 24GB GPU.
- **Run it with flash attention ON + **`q8_0`** KV cache.** Do NOT use `q4_0` cache (reason below).
- **Pin **`num_ctx`** to a tested-fitting value** (100K target, confirm with nvidia-smi) and **align OpenClaw's context limit to that pin** so compaction triggers before the cache overflows. **(CAVEAT 2026-06-23: alignment alone did NOT produce graceful compaction for the gemma-amethyst agent — it hit a hard "context overflow" error at the ceiling instead of trimming. See Model/Context/Session section + Open Follow-ups.)**
- The real constraint is VRAM (24GB), specifically leaving KV-cache headroom — NOT system RAM.
- `ollama ps` "100% GPU" is NOT a safety signal — use nvidia-smi for true VRAM usage.
- **Model role-split (direction set 2026-06-21; debaters locked 2026-06-22; debater-B endpoint BUILT 2026-06-22):**
  - **qwen3.6:27b stays the agentic workhorse on pacifico (3090)** — big context (110K, `q8_0` cache), tool-calling, routed/automation work. Also debater A in the council.
  - **gemma4:31b DENSE on amethyst (5090, 32GB)** — debater B. Run with **fp16 KV cache** (Gemma is cache-quant-sensitive — `q8_0` cache measured KL 0.377; do NOT quantize Gemma's cache), `num_ctx` **80K — now VRAM-VERIFIED FLAT UNDER FILL** (27,788 MiB / 32GB, 4.7 GiB headroom; held identical from load through 50K real context — KV pre-allocation confirmed; better than the 28.5–30.5 GiB estimate, likely because flash-attn was on, unlike the fp16 32K baseline). amethyst runs its OWN Ollama, so it sets fp16 host-side independently of pacifico's global `q8_0` — no conflict.
  - Trigger for souring on qwen for the knowledge role: Brian found qwen gave a confidently-wrong, self-chosen "mind-blowing fact" with botched objective math; judges Gemma stronger on general world-knowledge. Caveats: one sample of a known failure genre; qwen was selected for tool-calling, not casual chat. Not the `q8_0` cache (Qwen tolerates it); if anything the 4-bit weights and/or role mismatch. **(2026-06-23: gemma4:31b showed the SAME failure genre — confabulated the JFK inaugural verbatim into a hallucination spiral, and confabulated session contents ("gasoline engine essay" that never happened) under heavy context. Confirms BOTH local mid-models fabricate on verbatim-recall / self-report; reinforces the council's grounding rubric + fact-check judge. Verbatim recall is near-worst-case for a Q4 local model — never trust either to quote sources or self-report from memory; pull from the docs mirror / web instead.)**
- **Routing ≠ swapping.** qwen resident on pacifico, gemma resident on amethyst → OpenClaw "switches" by ROUTING to a different provider endpoint; no unload/reload tax; both big models stay hot. `models.providers.amethyst-ollama.baseUrl: http://100.113.225.2:11434` (BUILT). NO second VM / gateway / OpenClaw instance needed.
- **Context-cache handling.** Two config-fixable failure modes: TRUNCATION (Ollama drops oldest tokens past `num_ctx` — avoided by OpenClaw compaction when contextWindow ≤ `num_ctx`) and THRASHING (`num_ctx` > VRAM → spill to host; what gemma hit at 32K on the 3090 — fixed by pinning `num_ctx` to fit WITH headroom). For Gemma on the 5090: 80K fp16 with headroom, contextWindow aligned. **(2026-06-23: a THIRD failure mode observed — when compaction does NOT engage, the session hits a hard "context overflow: prompt too large" error at the ceiling and requires **`/reset`**. This is what gemma-amethyst did during the fill test; compaction did not save it. Open item.)**

## Summary

This note records the model-selection decision, the evidence behind it, the per-model configuration recipe, the cross-host resource-sharing model, the longer-term multi-model orchestration architecture, the Debate Council design (finalized core + proposed refinements), and the multi-node (3090 + 5090) co-orchestration design.

***

## The Decision: qwen3.6:27b (dense)

### Why Qwen, why 27b, why dense

- **Tool-calling pedigree.** Qwen leads open-weight function-calling. Klaw is an agent; reliable native tool-calling is foundational. qwen3.6:27b is the commonly recommended daily-driver size.
- **Dense = robust + quant-tolerant + high quality-per-VRAM-GB.** Avoids MoE's routing imbalance, fragility, and higher quantization sensitivity.
- **Fits 24GB with real headroom** once cache is handled (see recipe).
- Caveat (2026-06-21): qwen's casual-chat / open-ended world-knowledge may be weaker than Gemma's; tool-calling fitness and conversational fitness are different axes.

### Evidence: Mistral vs Gemma vs Qwen (researched 2026-06-14)

- Mistral Small 3.2 24B beats Gemma 3 27B on most benchmarks — but that's Gemma 3.
- Gemma 4 (Apr 2026) is a generational leap; headline fix is tool-calling (Gemma 3 scored 6.6% on τ2-bench agentic tool use, Gemma 4 31B scored 86.4%). Strong reasoning (AIME 89.2, GPQA Diamond 84.3). BUT thinking mode is slow (1m39s per tool cycle reported) and one tracker rates its agentic index only "moderate (48.2)."
- Qwen 3.5/3.6 27B edges Gemma 4 31B on GPQA (85.8 vs 84.3) and Qwen is the function-calling leader.
- gemma4:31b correctly fired a Mem tool live — Gemma 4 tool-calling works. The decision against it was VRAM/quant-fit and speed, NOT tool-calling capability. (Why the 5090 changes Gemma's calculus.)

### KV cache quantization — the deciding technical detail

Benchmark (localbench, KL divergence, Gemma 4 + Qwen 3.6, on an RTX 3090/24GB rig):

- `q8_0`**#x20;cache on Qwen: virtually lossless** (KL < 0.04). USE IT.
- `q4_0`**#x20;cache on Qwen: NOT lossless where it matters** — long documents (KL 0.581), tool calling (0.086). Rejected.
- Gemma 4 is unusually quantization-SENSITIVE (the 26B A4B MoE is the most quant-sensitive model tested; `q8_0` cache KL 0.377). So **run Gemma with fp16 cache.**

### Context-space math (24GB, qwen3.6:27b 17GB weights → 6-7GB for cache)

- `q8_0` ≈ half of FP16 cache; `q4_0` ≈ a quarter. `q8_0` alone gives **120K virtually-lossless context** on qwen.

### What was learned about VRAM mechanics (the stress test)

- KV cache is pre-allocated at load, sized by `num_ctx`; chatting WITHIN `num_ctx` does not grow VRAM. VRAM only grows if `num_ctx` itself is increased (model reload). **(CONFIRMED 2026-06-23 on amethyst/gemma: 27,788 MiB identical at 19K and 50K fill — flat across a 30K-token swing, the pre-allocation signature.)**
- gemma4:31b at 32K measured 23,346 / 24,564 MiB on the 3090 — riding the redline; overflow spilled to host RAM/disk while `ollama ps` falsely reported "100% GPU." **This measurement was at fp16 cache** (the global `q8_0` env var was set later, right before the qwen migration — confirmed by Brian 2026-06-22). So it is the fp16 baseline.
- Lesson: size model + pinned context to leave genuine VRAM headroom; prerequisite for safe autonomy.
- **(2026-06-23 instrumentation caveat) The TUI live token counter and the model's own session self-summary both proved UNRELIABLE as fill gauges — the TUI froze at 54K then went to\&#x20;**`?`**, the model confabulated session contents, and the persisted store (**`openclaw sessions --agent <id>`**\&#x20;reading\&#x20;**`sessions.json`**) showed a different, lower number (35–36K) that climbed slowly (dedup of repeated identical pastes likely). For true context state, trust the persisted store, not the TUI or the model. nvidia-smi remained the one solid instrument throughout.**

***

## Configuration Recipe (qwen3.6:27b)

1. Pull: `ollama pull qwen3.6:27b` (APPLIED 2026-06-15).
2. Flash attention ON.
3. `q8_0` KV cache (virtually lossless on Qwen; 2× context vs FP16).
4. Pin `num_ctx` to a tested value (100K target; verify via nvidia-smi). (Applied at 110K, VRAM-verified.)
5. Flash-attn + `q8_0` cache are GLOBAL Ollama host env vars (`OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`) on the PACIFICO host; per-model `num_ctx` + contextWindow set in openclawjson. (amethyst is a separate host — see Gemma addendum.)
6. Set the model in openclawjson (`agents.defaults.model = "ollama/qwen3.6:27b"`). Restart the gateway.
7. **Align OpenClaw's context limit** to the pinned `num_ctx`. (Done: `num_ctx` 110000 + contextWindow 110000 aligned.)

### Recipe addendum — gemma4:31b dense on amethyst (5090), as council debater B — AS-BUILT 2026-06-22

**STATUS: BUILT + VERIFIED.** The endpoint is live, leashed, authed, discovered, routable, resident-forever, and 80K-VRAM-verified (flat under fill). Step-by-step as-built record (supersedes the earlier plan-only version of this addendum):

**Host env on amethyst (Windows,\&#x20;**`setx`**\&#x20;→ persisted to user env; tray-app Ollama reads it at launch):**

- `OLLAMA_FLASH_ATTENTION=1`
- `OLLAMA_KV_CACHE_TYPE=f16` (explicit fp16 — NOT pacifico's `q8_0`; Gemma is cache-quant-sensitive)
- `OLLAMA_HOST=0.0.0.0:11434` (default is 127.0.0.1; this binds off-loopback so the VM can reach it — listens on `[::]:11434`, dual-stack, accepts IPv4)
- `OLLAMA_KEEP_ALIVE=-1` (keep resident forever; logs as `2562047h47m...` = MaxInt64 ns, the `-1` sentinel — correct, not a bug)
- **GOTCHA — restart mechanics:** `setx` only affects FUTURE processes. The tray-app Ollama launched at boot from a STALE environment; reconnecting SSH refreshes only the shell, not the tray app. A clean **reboot** of amethyst is the reliable way to relaunch the tray app with the new env (explorer re-reads the registry). Confirm via `server.log`: `flash_attn:true`, `OLLAMA_HOST:http://0.0.0.0:11434`, `OLLAMA_KV_CACHE_TYPE:f16`, `OLLAMA_KEEP_ALIVE:-1`. The `AMD driver too old` WARN is the integrated Radeon (dropped on next line); inference is on CUDA0 = the 5090.

**Firewall leash (amethyst, admin PowerShell):**

- `New-NetFirewallRule -DisplayName "Ollama 11434 (tailnet only)" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 11434 -RemoteAddress $tailnet` (reuse the verbatim 6-element `$tailnet` array from the Networking note; the `if ($tailnet.Count -lt 6){throw}` guard prevents the silent-widen-to-Any bug). Created OK, `Enabled:True`, `Profile:Any`.
- Open item (acknowledged, not blocking): the rule is IPv4-only while the listener is also on `[::]:11434` — same IPv4/IPv6 seam as RustDesk. Fine while the VM dials the typed IPv4.

**Reachability (from KlawMachine VM):**

- `curl http://100.113.225.2:11434/api/tags` returned the model list — firewall admits the VM, IPv4-dial-vs-`[::]`-listener seam is a non-issue in practice.
- `tailscale ping amethyst` → **direct, not DERP**: `pong ... via 192.168.0.29:41641` (amethyst's LAN IP — Tailscale negotiated a LAN-direct path automatically; the low-latency path the "use direct LAN IP for same-LAN hosts" rule wanted, achieved for free). Config still uses the stable `100.x` tailnet IP for durability behind the VM's NAT switch.

**openclawjson provider block (**`models.providers.amethyst-ollama`**):**

- `baseUrl: http://100.113.225.2:11434`, `api: "ollama"`, `apiKey: "ollama-local"`, `contextWindow: 80000`; model entry `{ id/name gemma4:31b, params.num_ctx 80000, reasoning:true, input:["text","image"], contextWindow 80000, maxTokens 8192, compat.supportsTools:true, api "ollama" }`. (No per-model `keep_alive` — host pins `-1` globally.)
- **AUTH GOTCHA (the big one this session):** a custom Ollama provider id needs `apiKey: "ollama-local"` (the local marker) — the literal string `OLLAMA_API_KEY` resolves as "find a real credential" → `effective=missing:missing`. The `100.x` Tailscale address is NOT auto-classified as local (docs: auto-marker covers loopback/private/`.local`/bare-hostname only; `models list` shows `Local: no`), so the marker must be set explicitly. **AND** the marker in config is necessary but NOT sufficient — there must also be a resolved auth PROFILE: `openclaw models auth paste-api-key --provider amethyst-ollama --profile-id amethyst-ollama:default` (paste value `ollama-local`). Only after BOTH did `openclaw models` flip to `effective=profiles:...`.

**Routing (the\&#x20;**`/model`**\&#x20;quirk):**

- `/new <model>` does NOT exist; the slash command is `/model` — and in the TUI it opens an interactive PICKER (filter + arrow + enter), not a `provider/model` argument. The picker's text filter did not match on "ame"/"g" — frustrating and unreliable.
- `openclaw models set <model>` is GLOBAL-only (would move Klaw off qwen — rejected). `openclaw chat` has NO `--model` flag. `openclaw message` is a CHANNEL/messaging admin command (send to phone, ban, pin, react) — NOT a chat-to-agent one-shot; do not use it for this.
- **The clean route = a dedicated agent** (also the debater-B foundation): `openclaw agents add gemma-amethyst --model amethyst-ollama/gemma4:31b --workspace /home/klaw/.openclaw/workspace-gemma-amethyst --non-interactive --json`. No `--bind` → isolated, off all channels, does not touch Klaw's Telegram routing or the default agent. Drive it with `openclaw chat --session agent:gemma-amethyst:main --message "..."`.
- Note: `openclaw models auth paste-api-key` does NOT accept `--agent`; the `gemma-amethyst` agent resolves the `amethyst-ollama` profile out of `main`'s auth store (`effective=profiles:.../agents/main/agent/...`). Works; whether that shared-store fallback is durable under stricter isolation is untested — flagged, not blocking.

**Verification (the part that matters):**

- Live generation routed to amethyst: status line `agent gemma-amethyst | amethyst-ollama/gemma4:31b | think medium | tokens 12k/80k`, gemma answered.
- amethyst `ollama ps`: `gemma4:31b ... 100% GPU CONTEXT 80000 UNTIL Forever`.
- `nvidia-smi`**: 27,788 MiB / 32,607 MiB used = 27.1 GiB, 4.7 GiB headroom — and IDENTICAL at 19K and 50K fill, confirming KV is pre-allocated at load and does not grow as context fills.** 80K STANDS — 64K fallback not needed.

- **FOOTGUN (still true):** pacifico ALSO has gemma4:31b locally (`ollama/gemma4:31b` → the 3090, which redlines). The council debater MUST route via `amethyst-ollama/gemma4:31b`. The `gemma-amethyst` agent is pinned to the correct provider, so use that agent rather than a bare model switch. (Earlier notes referenced a `gemma-test` agent — that agent does NOT exist in this build; only `main` and now `gemma-amethyst`. Corrected 2026-06-22.)
- **WEIGHT-QUANT REALITY CHECK:** `ollama show gemma4:31b` on amethyst confirms `Q4_K_M`, 31.3B, context length 262144, capabilities completion/vision/tools/thinking. fp16 weights (62GB) and q8 weights (33GB) don't fit 32GB; `Q4_K_M` (19GB) is the operating point.

***

## Second Telegram bot — "Copper Kettle" (gemma-telegram) — AS-BUILT 2026-06-27

A second Telegram bot running gemma4:31b via amethyst, standing up the gemma endpoint as a live channel agent (and sidestepping blocker B: in-chat `/model` switching does not propagate on the Telegram path). Uses per-agent pinning + a dedicated channel account.

- **Bot:** "Copper Kettle", @CopperKettleBot. **Telegram account:** `channels.telegram.accounts.gemma`. The pre-existing @KlawJBot stays the `default` account → agent `main` → qwen, UNCHANGED. `channels.telegram.defaultAccount: "default"` set explicitly (required once ≥2 accounts exist).
- **Agent:** `gemma-telegram`, pinned to `amethyst-ollama/gemma4:31b`, workspace `~/.openclaw/workspace-gemma-telegram`. Created via `openclaw agents add gemma-telegram --model amethyst-ollama/gemma4:31b --workspace ... --bind telegram:gemma` (the `--bind` wrote the account→agent binding).
- **Token:** the per-account key is `botToken` (NOT the generic `token` Discord/ClickClack use). SecretRef, env source: `{ source: "env", provider: "default", id: "TELEGRAM_GEMMA_BOT_TOKEN" }`, value in `~/.openclaw/.env`.
- **Access:** `dmPolicy: "allowlist"`, `allowFrom: ["telegram:8852367597"]` (Brian only).
- **Routing gotcha:** on Telegram an inline account `agentId` is TOPIC-only; account→agent routing MUST go through a `bindings` entry (routing rule 6, "Account match"). The handoff's "account agentId routes it" was imprecise.
- **Restart gotcha:** a NEW `.env` var requires a FULL gateway restart (`systemctl --user restart openclaw-gateway.service`); a hot config reload does NOT re-read `.env`. (An initial 401 from `getMe` was a bad token VALUE, not a config/schema problem.)
- **Verified (authoritative, not acoustic):** `openclaw sessions --agent gemma-telegram` showed the run on `gemma4:31b` 80K; amethyst `/api/ps` showed `gemma4:31b` resident (size\_vram 20.3GB, ctx 80000, keep\_alive forever). Acoustic heuristic: 5090/gemma = pulsing hum; 3090/qwen = quick chirp (heuristic only; session store is authoritative).
- **Tool gating (2026-06-27):** `agents.list[].tools.deny: ["group:runtime"]` set for `gemma-telegram` — blocks `exec`/`process`/`code_execution` (it had tried to execute a pasted shell snippet). Mem-write and web search left to AGENTS.md soft instructions (no native per-call approval for non-exec/MCP tools — gating is allow/deny only). Identity/persona lives in workspace files, not Mem.

***

## KV-cache / VRAM budget on the 5090 (32GB)

CORRECTED 2026-06-22: the 3090's gemma4:31b @ 32K = 23.3GB measurement was at **fp16** (`q8_0` was enabled later, right before qwen). So fp16 is the known baseline, 100–145 KB/token (single data point; weight-unit + fixed-overhead caveats — confirm with two nvidia-smi readings at different `num_ctx`, the slope = true per-token cost).

- **Budget frame:** 32GB − 2-3GB headroom. (As-built: nvidia-smi reports `available` 30.3 GiB at idle — Windows/desktop holds 1.5 GiB, so 30.3 is the real ceiling, not 31.8.)
- **gemma4:31b dense,#x20;**`Q4_K_M`**#x20;weights 19GB, fp16 cache:**
  - @ 32K: 23.3GB (measured on 3090, fp16, NO flash-attn).
  - **@ 80K (DEBATER TARGET — VERIFIED 2026-06-22/23): 27,788 MiB ≈ 27.1 GiB used / 32,607 MiB, 4.7 GiB headroom WITH flash-attn on, FLAT from load through 50K real fill.** Came in UNDER the 28.5–30.5GB estimate — flash attention (absent from the 32K baseline) is the likely reason. Comfortable; 64K fallback NOT needed.
  - @ 110K fp16: 32GB = no headroom (redline) at best, possibly over — REJECTED. (110K parity with qwen would force `q8_0` cache on Gemma, which defeats the fp16 requirement.)
- **gemma4:31b q8 weights 33GB:** doesn't fit before cache. Off the table.
- **gemma4:26b MoE q4 17GB:** similar footprint (MoE saves COMPUTE not MEMORY — all params resident); faster but most quant-sensitive on both axes. Not the debater of choice.
- **Takeaway:** gemma4:31b dense, `Q4_K_M` weights + fp16 cache, `num_ctx` 80K with headroom — BUILT + VERIFIED. A debater needs enough to hold a full debate (motion + evidence pack + rounds), not 110K. Pre-judging is done by the debaters themselves (no extra model — see Debate Council), so the headroom doesn't need to host a co-resident model.

***

## Cross-Host Resource Sharing (clarified 2026-06-21)

"Outsourcing the GPU" and "outsourcing the CPU" are DIFFERENT operations:

- **GPU = accessed as a network service, not relocated.** Ollama exposes the GPU over HTTP; point a provider's baseUrl at amethyst's Ollama and route agents there. Bandwidth tiny (prompt in, tokens out); weights never move. Not network-bound on a LAN/fast tailnet. (CONFIRMED in practice 2026-06-22 — the VM routes to amethyst's Ollama over a LAN-direct Tailscale path.)
- **CPU = the workload must RUN where the CPU is.** Levers: SSH sandbox backend (tool/exec runs on amethyst, workspace seeded once) or a second gateway (heavier; not pursued).
- **Save-VM/Resume-VM is a THIRD, separate lever** (multi-node section): suspend amethyst's VM to give its HOST resources back for a big local GPU/ML job. Don't conflate.
- **Governing rule: move compute to the data, not data to compute.** Use the direct LAN IP for same-LAN hosts (avoid forcing on-LAN traffic through a Tailscale relay). Note: for the VM (behind pacifico's NAT switch), the `100.x` tailnet IP is the practical path and Tailscale already negotiates LAN-direct under the hood.

***

## Debate Council (adversarial multi-agent design review) — CORE FINALIZED 2026-06-22

Goal: an autonomous adversarial peer-review loop that shakes out architectural/design decisions. Two local models debate; a frontier judge (Opus via Claude Code) adjudicates ripe debates; everything is persisted for iterative improvement.

### Honest framing (read first)

The council is NOT expected to out-decide Opus-in-direct-chat — a frontier model in dialogue with Brian is the highest decision-QUALITY method available, and the council's local debaters won't out-reason it. Its distinct value: (1) AUTONOMY — runs without Brian present; (2) BREADTH — two models with different failure modes + web search surface angles a single thread won't prompt; (3) reusable INFRASTRUCTURE (amethyst, remote-Ollama, Claude-Code-Opus pipeline, persistence) shared with the digest/orchestration; (4) it COMPOUNDS via Mem write-back. The cost asymmetry (see Proposed refinement #2) STRENGTHENS this case: cheap local exploration buys breadth/depth that's uneconomical on frontier. Treat its output as INPUT to Brian's/Opus's judgment, not as authoritative decisions. Validate with a discrete pilot; kill it if pilots just echo what Opus-chat already produces.

### Debaters (LOCKED)

- **qwen3.6:27b on pacifico** (currently-configured workhorse, `q8_0`, 110K) — debater A.
- **gemma4:31b dense on amethyst** (5090) — debater B. fp16 cache, `num_ctx` 80K. **ENDPOINT BUILT + VERIFIED 2026-06-22** (provider `amethyst-ollama`, agent `gemma-amethyst`).
- **SYMMETRIC PEER-CRITIC roles, NOT fixed advocate/skeptic.** Each advances and defends its own reading AND attacks the weak points in the other's, every round. Stance prompt: _"rigorous peer reviewer — concede well-grounded points, attack unsupported/assumed ones; do not manufacture disagreement, do not rubber-stamp."_ Rotate who opens each motion (no first-mover bias). Targets adversarial-ish WITHOUT agreement-collapse or contrarianism-for-its-own-sake.

### Ripeness gate — the debaters self-assess (REPLACES a separate pre-judge model)

No third model, no swap — both debaters already resident. After each round, EACH debater runs a SHORT ripeness assessment in a FRESH session (`sessions_spawn`, fed ONLY the transcript — "amnesic" to having argued, so it reads as an outsider; the debate sessions stay intact).

- **"Ripe" = further LOCAL rounds won't add value** — covers BOTH convergence AND a crystallized, stable DISAGREEMENT (sharp contested core that won't resolve locally).
- **ADOPTED INTERPRETATION (2026-06-22):** escalate when the two ASSESSORS CONCUR that it is ripe (consensus on ripeness) — NOT when the two debaters agree on the motion. Rationale: triggering on debater-agreement would escalate easy cases (Opus rubber-stamps) and starve the hard deadlocked ones where a frontier judge is most valuable. (Recorded as the working interpretation, revisable.)
- **"Too agreeable" guard = an OBJECTIVE co-signal:** track whether positions actually MOVED since last round (no movement for N rounds → ripe/stalemate; still moving → keep debating) + a HARD round cap. Models rate ripeness; movement-delta + cap keep them honest.
- **Residual bias caveat:** a fresh session removes session memory, not the model's inherent leanings. Requiring BOTH to concur + the objective signal mitigates.
- **Net: two-tier judging** — debaters self-gate (free, both hot) → Opus adjudicates only ripe debates (metered, capped). The qwq/deepseek-r1 separate-pre-judge idea is DROPPED (only resurrect a local model if a local INTERIM VERDICT is ever wanted — different from a ripeness gate).

### Judge — Opus via Claude Code, WITH leashed web search

- Neutral adjudicator = **Opus via Claude Code** (`claude -p --model opus`, subscription OAuth; `ANTHROPIC_API_KEY` **MUST be unset** or it bills pay-as-you-go API). A debater can't be the judge.
- **Web search ALLOWED for the judge (changed 2026-06-22 per Brian — reverses the earlier "judge offline").** Same leash as debaters: allowlisted domains, capped count, content treated as DATA not instructions, and **every fetch SNAPSHOTTED into the persisted record** so verdicts stay auditable/reproducible despite live search.
- **HARD USAGE CAP (REQUIRED — Brian, to prevent overspend/waste):** a hard ceiling on Opus/Claude-Code calls — e.g. max N/day AND a per-call token cap; judge only the DELTA since the last verdict. The ripeness gate is the first throttle; the hard cap is the backstop. Never let an unattended loop call Opus unbounded. (Same Agent-SDK-credit billing reality as the digest. NOTE: agenda-setting calls — Proposed refinement #3 — share this budget but on a SEPARATE line.)

### Web search policy (debaters + judge)

Allowlist trustworthy domains (official docs, GitHub, vendor blogs, arXiv); cap searches per debate/judgment (2-3); treat retrieved content as DATA, never instructions (injection guard for an autonomous loop); SNAPSHOT every fetch into the evidence pack / persisted record. Antidote to the Mem echo-chamber (Mem is largely Claude-authored). (`tools.web.search` already enabled, provider parallel-free.)

### Round structure

- R0 Frame: coordinator sets ONE concrete motion + evidence pack = scoped Mem notes (OPENCLAW PROJECT only) + raw docs-mirror excerpts + (capped, allowlisted) web snapshots. (With Proposed refinement #1, R0 is followed by a solo prep/case-construction phase before exchanges.)
- R1..Rn: symmetric peer-critic rounds; GROUNDED / ASSUMED / WEB:url] tagging on every factual/numeric claim.
- After each round: self-assessed ripeness check + movement-delta.
- On ripe: Opus judge reads transcript + evidence pack + snapshots, applies rubric.

### Judge rubric

Verdict (better-supported side / synthesize / insufficient); GROUNDING fact-check of every factual/numeric claim incl. web-tagged ones (CONFIRMED / UNSUPPORTED / FABRICATED — the guard against confident-wrong objective claims); echo-chamber check; blind spots both missed; confidence + what would flip it; concrete ACTION ITEMS.

### Persistence (for iterative improvement — REQUIRED, Brian 2026-06-22)

Persist EVERYTHING needed to improve the process over time:

- Full transcripts of all exchanges, every round (and the prep-phase briefs, per refinement #1).
- Model THINKING / reasoning traces where exposed (gemma4 + qwen3.6 both have thinking modes — capture when available; especially valuable from the prep phase). NOTE: the `amethyst-ollama` gemma entry has `reasoning:true`; the agent shows `think medium` live, so traces are exposed.
- Per-round metadata: timestamp, model id + version/quant, `num_ctx`, each assessor's ripeness score, position-movement delta, escalate/continue decision.
- Every web search: query, allowlist hit, and a SNAPSHOT of fetched content.
- Opus calls (judgments AND agenda-setting): full output, token counts, and running cap consumption (cost/usage tracking, separate lines per call-type).
- Canonical artifact = Markdown to `~/.openclaw/debates/YYYY-MM-DD-<slug>.md` (generated → git-ignored). VERDICT SUMMARY + key metadata written back to Mem (durable, cross-tool). Raw transcripts/thinking/snapshots stay on disk (too big/churny for Mem); Mem holds the verdict + index + lessons learned.

### Cadence — two clocks (NOT weekly)

- **Debate clock: FAST and FREE** (both models hot on their own cards → routing, no swap; local compute only). Run many rounds back-to-back; no reason to wait.
- **Opus clock: THROTTLED** — gated by the ripeness gate AND the hard cap. Frequent free local debate; rationed metered judgments + agenda-setting.
- Replaces the earlier "weekly cron" plan (Brian: weekly is wildly inefficient). Run the debate loop on a tight trigger / continuously; the gate + cap decide Opus spend.

### Mechanically (no new VM)

One gateway (pacifico). Two providers: `ollama` (qwen) + `amethyst-ollama` (gemma on the 5090) — **both now live**. Debater agents route to each (`main`/default for qwen, `gemma-amethyst` for gemma); coordinator drives rounds + ripeness checks via `sessions_spawn`/`sessions_send`. Judge + agenda-setter run out-of-band via Claude Code. amethyst's Ollama endpoint is locked down (tailnet-only firewall) — DONE. **CAVEAT 2026-06-23: long debate sessions risk the "context overflow" hard error (compaction did not engage during the gemma-amethyst fill test) — resolve the compaction question before running unattended multi-round debates, or the loop will error out mid-debate. Also: a\&#x20;**`/reset`**/**`/new`**\&#x20;session falls back to the GLOBAL default model (qwen) rather than the agent's pinned gemma — the coordinator must pin the model explicitly on every spawned session, not assume the agent default carries.**

***

## Debate Council — PROPOSED REFINEMENTS (under discussion 2026-06-22 late session; NOT yet crystallized)

Brian asked to persist these in detail even though not finalized. Status: directionally agreed; exact mechanics/parameters TBD. Build the core first, layer these in.

### 1. Prep / case-construction phase BEFORE exchanges

Brian: the models should have space and time to PREPARE valuable cases, not just rattle back and forth. Adopt **prep-THEN-exchange**: before R1, each model gets a solo case-construction turn — read the evidence pack (scoped Mem + docs + leashed web), build its strongest STRUCTURED brief INDEPENDENTLY, without seeing the other's work, using extended thinking mode. Exchanges then operate on the briefs.

- Rationale: reactive ping-pong produces shallow point-scoring; independent prep forces real argument construction and depth.
- This is where the local-cost advantage pays off — prep can be long/deep/thinking-heavy because it's free. Capture the prep thinking traces (persistence).
- BOUND it with a generous-but-capped prep budget so it doesn't run away.
- Prep does NOT replace exchange — exchange still does stress-testing. Prep first, then exchange.

### 2. Long, many-cycle local debates = the core economic justification (+ cost reframe)

Brian: leverage the ability to run long, in-depth, many-cycle debates LOCALLY — uneconomical on frontier cloud. This reframes the council's value and resolves the reality-check tension: it is NOT competing with Opus-chat on quality-per-decision; it BUYS EXPLORATION VOLUME that's near-free locally but prohibitively expensive metered. Economic shape: cheap deep local exploration → occasional expensive frontier judgment + agenda-setting.

- **COST REFRAME (Brian corrected Claude 2026-06-22):** local marginal cost ≪ frontier marginal cost. Hardware is sunk; marginal cost ≈ electricity. Single-Gemma-alone is weakest on decision QUALITY but CHEAPEST; the cost asymmetry is the PREMISE of the local setup, not a downside. (Claude had wrongly filed "local-hosting cost" as a con.)
- **Plateau caveat:** more cycles ≠ linearly more insight — two mid models eventually elaborate rather than improve. The movement-delta + ripeness gate is exactly what detects the plateau and stops "long" from becoming "long and pointless."

### 3. Opus as AGENDA-SETTER, not just judge (the flywheel)

Brian's idea: in addition to judging, Opus considers Brian's PROJECT GOALS and ASSIGNS the next round(s) of debate, after a carefully-sized, cost-capped internal analysis. Assessment: higher-leverage than judging — choosing WHAT to debate against actual goals beats refereeing, and it fixes the diminishing-returns/churn risk (steers toward fresh, goal-relevant motions, away from settled ones).

- **Inputs:** project goals (Roadmap priorities, MASTER, open questions) + recent verdicts + unresolved action-items.
- **Output:** a PRIORITIZED queue of concrete motions, each tied to a goal + rationale.
- **THE FLYWHEEL:** Opus sets agenda (capped, infrequent) → local council explores deeply over many cheap cycles → ripeness gate throttles → Opus judges ripe ones (capped) → verdicts + new open-questions feed Mem → Opus re-sets agenda.
- **Guardrails:** agenda-setting is a SEPARATE Opus call with its OWN hard-budget line (logged distinctly from judging); INFREQUENT relative to debate cycles (assign a batch, grind locally a long time, then re-assign); the motion queue is REVIEWABLE by Brian before cycles are spent — especially during the pilot (don't let it fully self-direct on day one; loosen once trusted).

### 4. Operational caveats for long sustained runs (Claude flagged)

- **THERMALS:** the 3090's 73–79°C / 440W figures were BURSTY, human-paced tests; back-to-back debate cycles are a continuous load — re-check sustained temps (incl. VRAM junction temp, which nvidia-smi doesn't show) before unattended multi-hour runs. (amethyst/5090 thermals under sustained load also not yet characterized — add to the same check.)
- **OCCUPANCY / CONTENTION:** qwen on pacifico is BOTH Klaw's main workhorse AND debater A. A marathon debate ties up that model, so Klaw's foreground work contends (Ollama serializes per model unless `OLLAMA_NUM_PARALLEL` > 1, which costs VRAM). Mitigate by scheduling long debates for when Klaw is idle (off-hours), or raising `OLLAMA_NUM_PARALLEL`, or (contra the locked choice) using a different model for debater A. amethyst/Gemma (debater B) has no other duties — the contention is specifically the pacifico side.
- **COMPACTION (NEW 2026-06-23):** the fill test showed the gemma-amethyst session hit a hard "context overflow" error at the ceiling rather than compacting. If compaction does not engage, a long debate that fills context will ERROR mid-run, not degrade gracefully. Must be resolved before unattended multi-round debates. Investigate whether compaction needs explicit per-agent config (it may be off/misconfigured for the dedicated agent), and whether the contextWindow/numctx alignment is actually being honored for `amethyst-ollama`.

### 5. Position-reversed, amnesiac re-runs (control for position/model bias) — added 2026-06-27

Run each motion TWICE with the debaters' assigned positions SWAPPED, in fresh "amnesiac" sessions (no memory of the prior run). If a side wins regardless of which model argues it, that is real signal; if the winner tracks the MODEL rather than the position, that is model/position bias to discount. (Brian, 2026-06-27.) Pairs naturally with "rotate who opens." Costs 2x local rounds, but local debate is cheap — acceptable.

### 6. Opponent-claim tagging + tag visibility — NOT self-tagging alone — added 2026-06-27

Debaters should TAG/CHALLENGE the OPPONENT's claims, not merely self-tag. In a manual 2-model smoke test (qwen `main` vs gemma `gemma-amethyst`, no judge), gemma spontaneously self-tagged its own claims `[GROUNDED]`/`[ASSUMED]` per its peer-critic SOUL — useful, but self-tagging carries a PERVERSE INCENTIVE: a model that under-tags (or is simply bad at tagging) its own assumptions DENIES the opponent and a tag-reading judge the cue to pounce, which perversely benefits the weaker tagger (Brian, 2026-06-27). Therefore: (a) require each side to flag the opponent's weakest unsupported claim, e.g. `[CHALLENGE: ...]`, and press it; (b) tag visibility to the opponent is a FEATURE (it directs probing at assumed points), not a leak; (c) do NOT rely on self-tags for grounding — the neutral Opus judge's grounding fact-check (CONFIRMED / UNSUPPORTED / FABRICATED) stays the authoritative check precisely because self-tagging is gameable. (Endpoints also validated by this smoke test: both debater agents answer headless via `openclaw agent --json`; qwen's provider currently allows only `--thinking off`, so only gemma emits reasoning traces — captured in the session JSONL.)

***

## OpenClaw Model/Context/Session Management (researched 2026-06-14)

- **Compaction engine:** as a session approaches the model's limit, OpenClaw summarizes older messages, prunes transient tool outputs, flushes important facts to long-term memory before clearing. Triggers on ITS notion of the limit, which MUST be aligned to the real `num_ctx`. Works for any model as long as contextWindow is aligned to `num_ctx`. **(CONTRADICTED IN PRACTICE 2026-06-23: the gemma-amethyst session did NOT compact at the ceiling — it returned "Context overflow: prompt too large for the model. Try /reset (or /new)..." This means compaction either is not configured for this agent, is not engaging, or the alignment is not effective as assumed. OPEN ITEM — verify before sustained council runs; the design's core assumption that "alignment ⇒ graceful compaction" is unproven for the dedicated provider/agent.)**
- **Per-agent models + multi-agent routing:** multiple isolated agents in one gateway, each own workspace/model/session store; inbound routed by bindings. (CONFIRMED 2026-06-22: this is how the gemma-amethyst debater is wired — a dedicated isolated agent pinned to `amethyst-ollama/gemma4:31b`.) NOTE: the in-TUI model switch is `/model` (opens a picker), NOT `/new`; per-agent pinning via `openclaw agents add --model` is more reliable than the picker and is the mechanism the Debate Council uses. **(GOTCHA 2026-06-23: a\&#x20;**`/reset`**\&#x20;or\&#x20;**`/new`**\&#x20;inside the gemma-amethyst agent spawned a fresh session that fell back to the GLOBAL default model\&#x20;**`ollama/qwen3.6:27b`**\&#x20;— NOT the agent's pinned\&#x20;**`amethyst-ollama/gemma4:31b`**. The agent's model pin did not carry to the new session. Recovery: start a fresh named session via\&#x20;**`openclaw chat --session agent:gemma-amethyst:<key>`**, which DOES come up on gemma. The coordinator must verify/pin the model on every spawned session rather than trusting the agent default to propagate.)**
- **Multi-model-by-complexity is documented:** cheap local agent distills to disk, expensive agent reads the distilled file. Frontier models first-class (`agents.defaults.model` supports {primary, fallbacks}).
- **Honest limit:** OpenClaw provides the PRIMITIVES; "intelligently route by task/complexity" is architected on top.

## Ollama Model-Loading Economics (researched 2026-06-14)

- Model loads into VRAM on first request; stays for `keep_alive`; then unloads. `OLLAMA_MAX_LOADED_MODELS` recommend =1 for <32GB-RAM systems.
- Single 24GB card with 17-20GB model → ONE big model resident; multiple big local models can't co-reside → swap tax. **The two-host setup sidesteps it — one big model resident per card, routing between them is free.** (Now real: qwen resident on pacifico, gemma resident on amethyst with `keep_alive -1`.)
- Frontier API calls use ZERO local VRAM.

***

## Longer-Term Orchestration Architecture (design, not yet built)

1. **Resident workhorse (hot):** qwen3.6:27b on pacifico.
2. **Knowledge/debate model:** gemma4:31b on amethyst (5090). **— LIVE 2026-06-22.**
3. **Tiny co-resident specialists:** embeddinggemma (621MB) for RAG/vector.
4. **Frontier API tier (Anthropic), used SPARINGLY + CAPPED:** VRAM-free, dollar-metered; the Debate Council's Opus judge + agenda-setter. Distill-locally-then-escalate keeps cost down.
5. **On-demand heavy local specialists:** qwq:32b (reasoning), deepseek-coder:33b / qwen3-coder (coding) — loaded only when needed.

### Routing trigger = confidence/difficulty (the hard part to build)

- Something must DECIDE when to escalate: routing rules, a cheap triage/classifier, or self-assessed escalation (the ripeness gate is a concrete instance). LLM confidence poorly calibrated; levers: abstention prompts, logprobs, grounding/citations, self-verification.
- **AI council / adversarial peer review:** different models → different failure modes → cross-checking catches errors. Patterns: mixture-of-agents, generator-critic, debate-with-judge. The Debate Council is the first concrete build.
- Note: deepseek-coder:33b (installed) is a CODING model, not reasoning; the DeepSeek REASONING family is DeepSeek-R1 (not installed). qwq:32b is the installed reasoning specialist.

### MoE notes (for future model choices)

- MoE saves COMPUTE (speed), not MEMORY — all experts resident. Lower quality-per-total-param; routing imbalance; HIGHER quantization sensitivity on BOTH cache and weights (gemma4:26b A4B = most quant-sensitive tested).
- qwen3.6:35b-A3B is the "speed variant" in reserve — but MoE → more quant-sensitive.

***

## Multi-Node Co-Orchestration: 3090 + 5090 (design — not built; 5090 VM not yet created)

Captures the 2026-06-16 design for when the second node (RTX 5090 host + its own OpenClaw VM) exists. The near-term Gemma-on-amethyst plan does NOT require this — amethyst serves a Gemma Ollama endpoint to pacifico's gateway with no second VM/gateway (BUILT 2026-06-22). This section is the LATER, fuller build.

### Terminology: "nodes" vs "gateways" (clarified 2026-06-21)

- OpenClaw "**nodes**" = peripheral COMPANION DEVICES (camera/canvas/screen), NOT compute hosts. `openclaw nodes` manages those, NOT clusters.
- The 5090 box (amethyst) is a separate **GATEWAY/host**. Two OpenClaw hosts = the "**multiple gateways**" pattern (independent gateways), NOT auto-orchestrated.
- **No built-in cross-gateway orchestration / chain-of-command.** The Save-VM/Resume-VM design below is custom work on top of two independent gateways.

### Goal

Two OpenClaw VMs (3090 + 5090) that divide-and-conquer AND specialize, while each host stays free for its own heavy GPU/ML work.

### Cross-node resource yielding (mechanism — buildable now)

- One VM yields the OTHER host's compute by SUSPENDING the other node's VM (no host powered off).
- Mechanism: Hyper-V `Save-VM` (writes guest state to disk, FULLY RELEASES RAM/CPU) vs `Suspend-VM` (pauses in memory; doesn't free RAM). `Resume-VM` restores. Triggered over SSH/PowerShell.
- Hard part is POLICY (when a yield is worth it; avoiding thrash).

### Chain of command / hierarchy (the genuinely hard design problem)

- MUST have a hierarchy — no two co-equal "bosses" (deadlock risk). BUT each node needs bounded AUTONOMY.
- Resolve: clear AUTHORITY GRADIENT + BOUNDED LOCAL AUTONOMY. Open: which node coordinates (fixed/failover)? autonomy envelope? arbitration of conflicting suspends? domain-specific authority?
- OpenClaw provides no built-in cross-gateway chain-of-command; custom work on top.

### Specialization vs. homogeneity (open axis)

- Want BOTH division-of-labor AND specialization (5090 has more VRAM/compute). Axes (undecided): CAPABILITY / ROLE / homogeneous-with-load-balancing. Decide when the 5090 VM exists.

### Staging

1. Both hosts SSH-reachable + remote Save-VM/Resume-VM (3090 done). 2. Manual "yield the other node." 3. Rule-based yielding. 4. Hierarchy/arbitration. 5. Adaptive policy.

***

## Open Follow-ups (cross-referenced)

- Apply the qwen decision: DONE 2026-06-15.
- Confirm OpenClaw per-model context key via docs mirror: DONE.
- **Gemma on amethyst: DONE 2026-06-22/23.** `amethyst-ollama` provider registered on pacifico's gateway (baseUrl `http://100.113.225.2:11434`, `apiKey: ollama-local` + `amethyst-ollama:default` auth profile); amethyst Ollama exposed (`OLLAMA_HOST=0.0.0.0:11434`) + leashed (tailnet-only firewall on :11434) + flash-attn on + fp16 cache + `keep_alive -1`; `gemma-amethyst` isolated agent pinned to `amethyst-ollama/gemma4:31b`; live generation verified; **80K fp16 VRAM-verified FLAT UNDER FILL at 27,788 MiB / 4.7 GiB headroom (identical at 19K and 50K context; 64K fallback NOT needed).** Gotchas recorded in the Recipe addendum: the `ollama-local` marker + auth-profile requirement for a `100.x` (non-auto-local) endpoint; `/model` is a TUI picker not `/new`; `openclaw message` is NOT a chat command; dedicated-agent pinning beats the picker.
- **NEW open items surfaced by the 2026-06-23 stress test (investigate before sustained/unattended council runs):**
  - **(A) Compaction did NOT engage at the context ceiling** — the gemma-amethyst session returned a hard "Context overflow: prompt too large" error and demanded `/reset`, instead of summarizing/pruning. The design assumption "align contextWindow to numctx ⇒ graceful compaction" is UNPROVEN here. A long debate would error mid-run. Verify whether compaction needs explicit per-agent config and whether alignment is honored for the provider.
  - **(B)\&#x20;**`/reset`**\&#x20;/\&#x20;**`/new`**\&#x20;falls back to the GLOBAL default model** (`ollama/qwen3.6:27b`) rather than the agent's pinned `amethyst-ollama/gemma4:31b`. The model pin did not carry to the new session. The coordinator must explicitly pin/verify the model on every spawned session. Recovery path that works: `openclaw chat --session agent:gemma-amethyst:<key>` comes up on gemma correctly.
  - **(C) Instrumentation unreliability:** the TUI token counter and the model's own session self-summary both diverged from reality (TUI froze at 54K then `?`; model confabulated session contents). Trust the persisted store (`openclaw sessions --agent <id>`) for context state, and nvidia-smi for VRAM — not the TUI or the model.
  - (Carried) the `gemma-amethyst` agent resolves auth from `main`'s store (shared-fallback) — verify durability if isolation tightens; close the IPv4/IPv6 firewall seam if desired; amethyst Ollama is the login-bound tray app — consider a Windows service for true unattended durability before the council runs sustained.
- **Debate Council — core FINALIZED 2026-06-22:** symmetric peer-critic debaters; self-assessed ripeness gate (both-concur, stable-disagreement counts, movement-delta + round-cap guard); Opus judge via Claude Code WITH leashed web search + HARD cap; full persistence to disk + verdict summary to Mem; two-clock cadence. Build as a discrete pilot; treat output as input-to-judgment; kill if it only echoes Opus-chat. **Debater-B endpoint is now built — the next concrete step is wiring the coordinator + the qwen debater-A agent and running a pilot motion. BLOCKERS to clear first: open items (A) compaction and (B) model-pin-on-spawn above, both of which would break an unattended multi-round loop.**
- **Debate Council — PROPOSED refinements (under discussion, not crystallized 2026-06-22):** (1) prep/case-construction phase before exchanges; (2) long-many-cycle local debates as the economic rationale + cost reframe; (3) Opus as agenda-setter (the flywheel) with a separate capped budget line + reviewable motion queue; (4) operational caveats for long runs (sustained thermals; qwen workhorse-vs-debater-A contention). Confirm + crystallize next session.
- `debate-council-pipeline.md` deliverable predates the 2026-06-22 finalization + refinements — regenerate to match.
- **Multi-node (5090) build track:** seed the 5090's OpenClaw VM from a KlawMachine golden image; decide specialization axis; build cross-node Save-VM yielding in stages; design chain-of-command. Pending the 5090 VM.
