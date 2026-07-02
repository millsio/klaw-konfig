# OpenClaw Docs Digest

_Generated 2026-07-01 from the local mirror via claude -p (opus) — FULL._

# OpenClaw — Whole-Corpus Documentation Digest

*One synthesized map of OpenClaw, reconciled from the full documentation set. Organized by theme, not by file. Real config keys, commands, and defaults are preserved throughout. Where a default or path is cited, treat it as documented-at-capture-time and re-verify a specific flag with `openclaw config schema` / `openclaw doctor` before acting on it.*

---

## 0. The one-sentence model

OpenClaw is a **self-hosted AI-agent gateway**: a single long-lived **Gateway** daemon that hosts one or more **agents**, connects them to ~30–45 chat channels and ~60 model providers, gives them tools (shell, files, browser, web, media, messaging), and exposes a WebSocket + HTTP control plane on **one port (default `18789`)**. Everything else — the CLI, Control UI/Dashboard, TUI, WebChat, mobile/desktop apps, and paired "nodes" — is a *client* of that one process. Configuration is **one JSON5 file** (`~/.openclaw/openclaw.json`); durable state lives under **one state dir** (`~/.openclaw/`), increasingly in **SQLite**.

The whole system is legible once you internalize four invariants that recur in every subsystem:

1. **One Gateway, many clients.** The Gateway owns all channel connections, sessions, routing, pairing, cron, and tool execution. Routing (channel-in → same-channel-out) is deterministic and Gateway-owned — *not* a model decision.
2. **Fail closed.** Missing config block, unresolved secret, non-loopback bind without auth, empty allowlist, invalid config → the guard *stops* or *denies* rather than degrading quietly. "Missing config = broken, not a shortcut."
3. **Layered, non-overriding gates.** Access control, tool policy, and auth are stacks of independent gates composed by "stricter-of"; lower/later layers can only *narrow*, never grant back. A permissive setting in one layer never silently opens another.
4. **`openclaw doctor --fix` is the universal reconciler.** It migrates legacy config shapes and JSON→SQLite stores across essentially every subsystem. Startup deliberately does *no* legacy migration — that job belongs to doctor alone.

---

## 1. Architecture & runtime topology

```
Channels (Discord, WhatsApp, Slack, Telegram, iMessage…)      Nodes (mac/iOS/Android/headless)
        │  inbound event                                              │  node.invoke (exec, camera, canvas…)
        ▼                                                             ▼
  ┌──────────────────────────── GATEWAY  (:18789, loopback) ────────────────────────────┐
  │  auth · routing · sessions · pairing · queue · cron · hooks · MCP · plugin registry  │
  │  Agent turn:  harness → model → tools → reply       (one serialized run per sessionKey)│
  │  WS control plane + HTTP (OpenAI-compat, /tools/invoke, hooks, Control UI, health)     │
  └───────────────────────────────────────────────────────────────────────────────────────┘
        ▲                         ▲                          ▲
   CLI / Control UI / TUI    model providers (HTTP/CLI)   Sandbox (Docker/ssh/openshell) or Host
```

- **Gateway** (`openclaw gateway`) — must run with `gateway.mode: "local"` or it refuses to start (`--allow-unconfigured` is the dev/bootstrap escape hatch only). Default bind **loopback**, port **18789**. Always-on is required for cron, heartbeats, and channel delivery.
- **Agents run three ways:** the **embedded runtime** (default, in-Gateway loop: `openclaw`), **CLI backends** (shell out to a local AI CLI — `claude-cli`, `google-gemini-cli`), and **agent harnesses** with native session daemons (**Codex** app-server for OpenAI, **Copilot**). External coding agents attach via **ACP** (`acpx`).
- **Nodes** are paired devices (not gateways) that lend capabilities back to the Gateway (`system.run`, `canvas.*`, `camera.*`, `screen.*`, `location.get`, `stt/tts`) over the WS via `node.invoke`.
- **Plugins** implement nearly every capability — providers, channels, memory, tools, hooks. The core is a thin trusted orchestrator; **understanding the plugin model is understanding OpenClaw.**

**Runtime requirement:** Node ≥ 22.19 (Node 24 recommended). **Bun is discouraged for the Gateway** (WhatsApp/Telegram bugs); it's CLI-only. pnpm for source builds.

**Health/liveness split:** `/healthz` (or `/health` → `{"ok":true,"status":"live"}`) = liveness; `/readyz` = readiness (waits on plugin sidecars/channels/hooks; reports **unhealthy during restart drain** to keep traffic off a draining gateway). **Uptime-monitor pitfall:** ping `/health`, never `/v1/chat/completions` (the latter spins a full agent session per ping → store bloat).

**Restart/supervision:** `SIGUSR1` = in-process restart (gated by `commands.restart`); `gateway restart --safe` drains up to `gateway.reload.deferralTimeoutMs` (default 5 min). Per-OS: macOS launchd `ai.openclaw.gateway`, Linux systemd-user `openclaw-gateway.service` (`loginctl enable-linger` for post-logout), Windows Scheduled Task. Profiles suffix all of these. Single-instance enforced by a lock file + port probe (`GatewayLockError`; systemd duplicate exits **78** to match `RestartPreventExitStatus`).

---

## 2. The configuration surface

**One file:** `~/.openclaw/openclaw.json`, **JSON5** (comments, trailing commas, unquoted keys). Overridable via `OPENCLAW_CONFIG_PATH` — **must be a regular file, no symlinks** for OpenClaw-owned writes. Missing file → safe defaults.

### The namespace map (knowing which namespace owns a feature is half of operating OpenClaw)

| Namespace | Governs |
|---|---|
| `agents.defaults.*` / `agents.list[].*` | model, workspace, sandbox, tools, thinking, streaming, timeouts, heartbeat, memory search, compaction, media-gen defaults, bootstrap |
| `models.providers.<id>.*` / `models.pricing.*` | endpoints, catalogs, compat, timeouts, request-trust, `cost` (USD/1M) |
| `auth.*` | `auth.order.<provider>` (probe ordering), `auth.profiles` (metadata only, **no secrets**), `auth.cooldowns.*` |
| `gateway.*` | bind, port, TLS, `auth.{mode,token,password}`, tailscale, `controlUi`, `nodes`, `remote`, `reload` |
| `channels.<channel>.*` (+ `.accounts.<id>.*`) | per-channel caps, allowlists, policies, streaming, markdown, `commands`, `execApprovals`, `threadBindings`, `tts` |
| `messages.*` | queue/debounce, group behavior, silent replies, ack reactions, usage footer, `messages.tts.*` |
| `tools.*` | `profile`, `allow`/`deny`/`alsoAllow`, `byProvider`, `exec.*`, `web.*`, `fs.*`, `media.*`, `elevated.*`, `sandbox.*`, `subagents.*`, `codeMode`, `loopDetection` |
| `plugins.*` | `enabled`, `allow`/`deny`, `load.paths`, `slots.{memory,contextEngine}`, `entries.<id>.{enabled,config,hooks}` |
| `skills.*` | `load`, `install`, `entries.<key>`, `allowBundled`, `workshop` |
| `session.*` | `dmScope`, `mainKey`, `reset`, `resetTriggers`, `threadBindings`, `identityLinks`, `maintenance`, `writeLock` |
| `security.installPolicy.*` | trusted-command gate for skill/plugin installs |
| `approvals.exec.*` / `approvals.plugin.*` | approval *routing* to chat (independent of each other and of host policy) |
| `cron.*`, `hooks.*`, `commitments.*`, `discovery.*`, `proxy.*`, `browser.*`, `acp.*`, `mcp.servers`, `diagnostics.*`, `logging.*` | subsystem-specific |

### Config truths that hold everywhere

- **Strict validation, deny-by-default.** Unknown keys / bad types → **gateway refuses to start** (only `$schema` exempt). Native plugins ship an `openclaw.plugin.json` with a strict `configSchema` validated *before plugin code loads* — adding an undeclared config key fails validation.
- **Write safety.** The *full* post-change config is validated before commit; rejected writes saved as `openclaw.json.rejected.*` / doctor-repaired external edits as `.clobbered.*` (32 rotated). `config.apply` = **full replace** (omitted keys deleted) — prefer `openclaw config set` (small edits) or `config.patch` (RPC merge). Promotion to last-known-good is skipped if the candidate contains redacted `***` placeholders.
- **Protected map paths** refuse silent entry-drops: assigning a plain object to `agents.defaults.models`, `models.providers[.<id>.models]`, `plugins.entries`, or `auth.profiles` is **rejected** unless you pass `--merge` or `--replace`.
- **The universal parameter merge order:** `agents.defaults.params` → `agents.defaults.models["provider/model"].params` → `agents.list[].params` (agent match wins). Governs `cacheRetention`, `thinking`, `serviceTier`, per-model overrides.
- **The override cascade is universal:** defaults → per-agent → per-channel → per-session → inline; every field overrides per-field, and every *filtering* layer can only further restrict.
- **`$include`** replaces (single file) or deep-merges (array); paths must stay inside the config dir (widen via `OPENCLAW_INCLUDE_ROOTS`); only single-file includes get write-through.
- **Env & substitution.** `${VAR}` string interpolation (uppercase only; missing → load error; escape `$${VAR}`) is distinct from **SecretRef objects** (`{source:"env"|"file"|"exec", provider, id}`) — the real credential surface. `.env` precedence: process env > CWD `.env` (**provider creds blocklisted here**) > global `~/.openclaw/.env` (recommended home for keys) > config `env` block (fills gaps only) > optional `env.shellEnv` login-shell import. **No layer ever overrides an existing value.**
- **Nix mode (`OPENCLAW_NIX_MODE=1`)** makes the entire mutation surface refuse — config writers, plugin lifecycle, `doctor --fix`, `update`, setup. Edit the Nix source. A parallel universe every automation must branch on.
- **`oc-path`** (optional plugin, `oc://FILE/SECTION/ITEM/FIELD` addressing) surgically reads/edits config-family files (md/jsonc/jsonl/yaml) preserving comments, with a `__OPENCLAW_REDACTED__` sentinel that refuses to write secrets back.

---

## 3. The state root — everything hangs off `~/.openclaw/`

`$OPENCLAW_STATE_DIR` (default `~/.openclaw`; path root remappable via `OPENCLAW_HOME`). **Keep it off cloud-synced folders** — iCloud/Dropbox latency corrupts sessions (`doctor` warns).

| Path | Contents |
|---|---|
| `openclaw.json` | The config (JSON5) |
| `workspace/` (`agents.defaults.workspace`, default here) | Agent workspace: `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `BOOTSTRAP.md` (once), `MEMORY.md`, `memory/YYYY-MM-DD.md`, `skills/` |
| `agents/<agentId>/agent/auth-profiles.json` | Canonical OAuth/API-key profiles (per agent) |
| `agents/<agentId>/agent/openclaw-agent.sqlite` | Per-agent secrets + session metadata + transcript stream + memory index |
| `agents/<agentId>/sessions/` | `{sessionId}.jsonl` transcripts + `sessions.json` metadata |
| `credentials/` | Channel/provider state (`whatsapp/<accountId>/creds.json`), `<channel>-pairing.json` / `-allowFrom.json`, legacy `oauth.json` (import only) |
| `state/openclaw.sqlite` | Global control-plane DB (~90 tables: discovery, pairing, tasks/flows, plugin index, scheduler, credentials, backup meta) |
| `exec-approvals.json` + `.sock` | Host-local exec approval policy + IPC socket |
| `secrets.json` | Optional file-backed SecretRef payload |
| `devices/`, `paired.json` | Node device tokens (sensitive) |
| `hooks/`, `skills/`, `~/.agents/skills/` | Managed hooks; managed/personal skills |
| `/tmp/openclaw/openclaw-YYYY-MM-DD.log` | Logs (rotate at 100MB, keep 5) |

**Per-agent isolation is the recurring shape:** each agent has its own `agentDir`, auth store, workspace, sessions. **Never reuse an `agentDir` across agents** (auth/session collisions). Secondary agents get **read-through inheritance** from the default/main store, but **OAuth refresh tokens are never cloned** — only portable `api_key`/static `token` profiles (unless `copyToAgents:false`); `oauth` profiles are non-portable by default (refresh-rotation sensitivity). The **triad to copy on any migration:** `openclaw.json` + `auth-profiles.json` + `.env` + workspace — copying only the config misses auth and credentials.

### The storage direction: config file-backed, everything else SQLite
Two-level SQLite (`node:sqlite`, Node 22+): **global DB** (control plane) + **per-agent DB** (data plane). Config stays file-backed *deliberately* so it's hand-editable. Hard invariants define much of the codebase discipline: session rows are metadata-only (no transcript locators); transcript identity is always `{agentId, sessionId}` (the string `sqlite-transcript://` is **banned even as a handle**); hot paths read typed columns, never parse `session_key` substrings or mine `*_json` shadows; `dual-read` bridge code forbidden except in doctor; schema pinned `user_version=1`. Backups use `VACUUM INTO` snapshots (WAL omitted) + `PRAGMA integrity_check`. A repo guard fails any new pairing of a legacy store name with a write-style FS API.

---

## 4. Sessions, routing & the agent loop

**Identity primitives:** `AgentId` (isolated workspace + session store — a "brain") · `AccountId` (per-channel instance) · `SessionKey` (context + concurrency bucket).

**Session-key grammar (uniform):**
- DMs collapse to main by default (`session.dmScope: "main"`): `agent:<agentId>:<mainKey>` (default `agent:main:main`).
- Groups: `agent:<agentId>:<channel>:group:<id>`; channels/rooms: `…:channel:<id>` / `…:room:<id>`; threads append `:thread:<id>`; Telegram/Feishu topics embed `:topic:<id>`; cron `cron:<jobId>`; hooks `hook:<uuid>`; subagents `…:subagent:<uuid>`.
- **Hard rule:** session-key substrings are *routing vocabulary, not identity/authorization* — never decode them for chat-type classification.

**`session.dmScope`** (`main` | `per-channel-peer` | `per-peer` | `per-account-channel-peer`) is the pivot for multi-user bots and the **cross-user-leak footgun escape** — set `per-channel-peer` whenever >1 person can DM (local CLI onboarding now writes this by default). Channel-specific dmScope beats global (formally verified). `session.identityLinks` deliberately merge one person across channels (also what channel docking rides on). It drives **Feishu dynamic agent creation** (`feishu-{open_id}` agents from templates). Workspace isolation is a *messaging-context* boundary, **not** a hostile-co-tenant security boundary (process/host env shared).

**Agent routing precedence (first/most-specific wins):** exact peer → parent peer (thread inheritance) → guild+roles (Discord) → guild → team (Slack) → account → channel (`accountId:"*"`) → default agent. A multi-field binding requires *all* to match. Bindings live in top-level `bindings[]`; `type:"acp"` durably pins a DM/room/thread to an ACP session.

**The agent loop:** intake → context assembly → inference → tool execution → streaming → persistence, **one serialized run per session key** (`agents.defaults.maxConcurrent`, default 4 across sessions). `agent` RPC returns `{runId, acceptedAt}` immediately; `agent.wait` blocks (default 30s, wait-only — doesn't stop the run). Runtime default timeout is a striking `agents.defaults.timeoutSeconds` = **172800s (48h)**; the short timeouts you feel come from `agent.wait` (30s), model idle (~120s), and diagnostics abort thresholds.

**Reset lifecycle:** `/new` / `/reset` (configurable `session.resetTriggers`; sent alone → ack without invoking the model). `session.reset.{mode:daily|idle, atHour (default 4 AM local), idleMinutes}` — earliest wins. **`sessionStartedAt` drives daily reset, `lastInteractionAt` drives idle reset; background writes (heartbeat/cron/exec) mutate the row but don't extend freshness.** Maintenance: `pruneAfter` 30d, `maxEntries` 500, disk high-water 80%. Write lock: process-aware, file-based, non-reentrant, `session.writeLock.acquireTimeoutMs` 60000.

**Queueing / steering** (`messages.queue`): `main` lane concurrency **4**, `subagent` lane **8**, others 1. Modes: `steer` (default — injects mid-run at model boundaries, never interrupts in-flight tools) | `followup` | `collect` (coalesce after debounce) | `interrupt` (abort). Precedence: inline `/queue` → `byChannel` → global → default. Native Codex uses its own `turn/steer`.

**Sub-agents** (`sessions_spawn`): non-blocking, return `runId` + `childSessionKey`, announce on completion. Caps: `maxConcurrent` 8, `maxSpawnDepth` 1 (set 2 for orchestrators), `maxChildrenPerAgent` 5, `archiveAfterMinutes` 60, `runTimeoutSeconds` 0. `context: isolated` (default) vs `fork`; leaf sub-agents get no session tools unless `maxSpawnDepth ≥ 2`, and only `AGENTS.md`+`TOOLS.md` injected. `/stop` cascades to all children.

---

## 5. Context management — three distinct mechanisms (don't conflate)

The **system prompt is OpenClaw-owned** (no provider default), assembled with a **cache boundary**: stable prefix (tool defs, skills block, bootstrap workspace files) *above*, volatile sections (Runtime, Messaging, Group Context, `HEARTBEAT.md`, timestamps) *below* for prefix-cache reuse. Unexpected `cacheWrite` spikes → something changed above the boundary. Bootstrap injection caps: `bootstrapMaxChars` 20000/file, `bootstrapTotalMaxChars` 60000 (inspect via `/context`). Under native Codex, `AGENTS.md` loads through Codex's own project-doc discovery; `MEMORY.md` becomes a *pointer* to `memory_search`/`memory_get` rather than being pasted.

1. **Compaction** (`agents.defaults.compaction`) — summarizes old turns, **persisted to transcript**, whole-conversation scope. On by default; triggers near-limit (`contextTokens > contextWindow - reserveTokens`, floor 20000) or on provider overflow signatures (`request_too_large`, "context length exceeded"). Keeps tool-call/result pairs together across chunks. `mode: default|safeguard`, `identifierPolicy: strict`, plus `qualityGuard`, `midTurnPrecheck`, `memoryFlush`. **Context-overflow errors STOP failover** — they belong to compaction.
2. **Pruning** (`agents.defaults.contextPruning`) — trims old tool results **in-memory only**, never written, per-request. Matters for Anthropic prompt-cache economics; smart-defaults on for Anthropic profiles only. Image blocks never pruned.
3. **Context engine** (`plugins.slots.contextEngine`, default `legacy`) — pluggable subsystem owning assemble/compact/subagent lifecycle. `ownsCompaction:true` disables built-in auto-compaction. Broken non-legacy engines are quarantined → downgrade to `legacy`.

**Pre-compaction memory flush** (`compaction.memoryFlush`, on by default) — a silent turn reminds the agent to persist memory before context is summarized; assistant output of exactly `NO_REPLY` suppresses delivery (silent housekeeping). Skipped when workspace is read-only.

---

## 6. Models, providers, auth & failover

### Selection & aliases
`agents.defaults.model` = string or `{primary, fallbacks}`, format `provider/model` **split on the first `/`** (OpenRouter nested ids: `openrouter/moonshotai/kimi-k2`). **A bare `model`/`{primary}` is strict no-fallback** — add `fallbacks` (or `fallbacks:[]` for explicit strict). Separate slots: `imageModel`/`pdfModel` (understand) vs `imageGenerationModel`/`videoGenerationModel`/`musicGenerationModel` (create) — a deliberate analysis-vs-generation split. Built-in alias shorthands resolve only if the model is in `agents.defaults.models`: `opus`→`anthropic/claude-opus-4-8`, `sonnet`→`…sonnet-4-6`, `gpt`→`openai/gpt-5.5`, `gemini`→`google/gemini-3.1-pro-preview`, etc.; user aliases override built-ins.

**Selection-source semantics** (the key distinction): **auto fallback** → `modelOverrideSource:"auto"`, temporary, re-probed every 5 min, cleared on `/new`/`/reset`; **user override** (`/model`, picker) → `"user"`, **strict — fails visibly, no fallthrough** (so you always know what ran). Changing `model.primary` does **not** rewrite pinned sessions.

### Agent runtimes (`agentRuntime.id`)
`auto | openclaw | <harness plugin id> | <CLI backend alias>`. **Selection is per-`provider/model`, not per-agent/session** — whole-agent/whole-session runtime pins are **legacy and ignored** (`OPENCLAW_AGENT_RUNTIME`, session `agentHarnessId`, `agents.defaults.agentRuntime`; `doctor --fix` strips them). **OpenAI is special:** `openai/gpt-*` defaults to the native **Codex app-server**; add `agentRuntime.id:"openclaw"` to force the built-in. Copilot's runtime (`@openclaw/copilot`) is external and never auto-selected. Explicit plugin runtimes **fail closed** — no silent fallback on error. `pi` is a deprecated alias for `openclaw`.

### The failover engine (two stages, elaborate and precise)
**Stage 1: auth-profile rotation within a provider** (exponential-backoff cooldowns) → **Stage 2: model fallback** to the next in `fallbacks`. It **persists the fallback override to the session *before* retrying** (prevents a stale-state race where reconciliation snaps back). Cooldowns are model-scoped (**1m → 5m → 25m → 1h cap**); **billing failures disable a profile** (5h → doubling → 24h cap) rather than cooldown. Error routing is enumerated:
- **Rate-limit bucket** (rotate/backoff): plain 429, "Too many concurrent requests", "ThrottlingException", "resource exhausted", "weekly/monthly limit reached", retryable usage-window 402s.
- **Billing lane** (kept separate): explicit billing text on 401/403.
- **Context-overflow** → compaction, **NOT fallback**.
- **Transient-server** (specific): Anthropic bare "unknown error occurred", OpenRouter "Provider returned error"/"520", "ModelNotReadyException"; generic "LLM request failed" stays conservative.

SDK `retry-after` capped 60s (`OPENCLAW_SDK_RETRY_MAX_WAIT_SECONDS`). Retries: `agents.defaults.runRetries` (embedded only). Removing auth mid-run aborts with `stopReason:"auth-revoked"`.

### Auth storage & OAuth
Secrets live in per-agent SQLite (`openclaw-agent.sqlite`) — `auth.profiles`/`auth.order` are **metadata/routing only**. `auth-profiles.json` is the canonical OAuth store; profile IDs `provider:default` / `provider:<email>` / custom. Rotation default: OAuth before API keys, oldest-used first. **Session stickiness:** a profile is pinned per session until `/new`/`/reset`, compaction, or cooldown. **OAuth token-sink hazard:** logging into OpenClaw and Claude Code/Codex CLI for the same account can invalidate each other's refresh tokens. Anthropic **Claude CLI reuse** (`claude -p`) is currently sanctioned; production still favors API keys. Codex OAuth does **not** grant embeddings (relevant to memory search). Probe reason codes (`openclaw models status --probe`): `ok`, `excluded_by_auth_order`, `missing_credential`, `invalid_expires`, `expired`, `unresolved_ref`, `no_model`. Key-rotation env priority: `OPENCLAW_LIVE_<P>_KEY` > `<P>_API_KEYS` > `<P>_API_KEY` > numbered.

### The provider zoo — sprawl that collapses to five axes
~60 providers reduce to **{transport family} × {native vs proxy} × {thinking model} × {regional split} × {bundled vs installed}**. Internalize these and any provider doc is predictable.

- **Native vs proxy — the most consequential axis.** Native routes (`api.openai.com`, `api.anthropic.com`, native Codex, DashScope, Bedrock) get the full treatment: strict tool schemas, attribution headers, `service_tier`, Responses `store`, prompt-cache hints, `reasoning.effort`, reasoning replay. **Proxy routes** (OpenRouter, LiteLLM, vLLM/SGLang custom base URLs, most OpenAI-compatible endpoints) get **none of it** — but gain `extra_body`/`chat_template_kwargs` passthrough. This single distinction explains most "why doesn't reasoning/caching work" reports.
- **Transport families** (model `api` field): `openai-completions`, `anthropic-messages`, `google-generative-ai`, `bedrock-converse-stream`, `ollama` (**use native `/api/chat`, never `/v1` for remote Ollama — breaks tool calling**).
- **Thinking** (`/think off|minimal|low|medium|high|xhigh|adaptive|max`; resolution inline → session → per-agent → global → provider default): heavily per-provider. Always-on (can't disable): Fable 5, Kimi K2-Code, Nemotron, DeepSeek R1 distills. Off by default: Opus 4.8 (effort values on `high+`). Binary (`enable_thinking`): DashScope/Qwen, Ollama. Replay-required (`reasoning_content` backfilled): DeepSeek, MiniMax M3. **Temperature traps:** Mistral Medium 3.5 & DeepSeek reject `reasoning_effort:high`+`temperature:0` (400); leave temperature unset when reasoning is on.
- **Fast mode** (`/fast auto|on|off`, `params.fastMode`, 60s cutoff): OpenAI/Codex → `service_tier:priority`; Anthropic → `service_tier:auto`; MiniMax rewrites to `-highspeed`.
- **Prompt caching** (`cacheRetention: none|short|long`): Anthropic direct short=5min/long=1hr (auto-seeded for API key); OpenAI direct automatic (`long`→24h); Bedrock non-Anthropic **forced none**; OpenRouter injects `cache_control` only on verified routes; Gemini auto-`cachedContents`.
- **Regional/plan splits** (two provider ids from one key): Volcengine/`-plan`, StepFun/`-plan`, MiniMax (API-key) / minimax-portal (OAuth), Moonshot/kimi, Xiaomi/`-token-plan`, Qwen/qwen-oauth. **China key ↔ `.com`/`.cn`, global key ↔ `.ai`/`-intl`** — mismatch = auth failure.
- **Custom/proxy providers:** `models.providers.<id>` is required for custom base URLs; `agents.defaults.models["p/m"]` only controls **visibility/aliases** — you must *also* add `models.providers.<p>.models[]` to register a runtime model. **Configuring a custom `baseUrl` is itself the SSRF trust decision** for that origin; other private origins need `request.allowPrivateNetwork:true`.

---

## 7. Memory

Memory (persisted to disk) is architecturally separate from context (the window). Exclusive slot `plugins.slots.memory` (default `memory-core`) + non-exclusive companions.

**Files (workspace):** `MEMORY.md` (curated durable facts, loaded every DM session start, **never decayed**), `memory/YYYY-MM-DD.md` (today+yesterday auto-loaded), `DREAMS.md` (human-only diary).

**Backends:** builtin (per-agent SQLite, FTS5/BM25 + optional vector; CJK trigrams; optional sqlite-vec) · **QMD** (external BM25+vector+rerank sidecar) · **Honcho** (cross-session AI-native) · **memory-lancedb** (vector DB) · **llama-cpp** (local GGUF embeddings for `memorySearch.provider:"local"`).

**Search** (`agents.defaults.memorySearch`): hybrid vector 0.7 / text 0.3 weighted merge; temporal decay (30-day half-life, `MEMORY.md` evergreen); MMR diversity. Providers: openai (default; needs a real API key — **OAuth is not valid embeddings auth**), bedrock, gemini, copilot, mistral, voyage, ollama/lmstudio, `local`. **Critical gotcha:** changing provider/model/dimensions/sources/chunking **invalidates the vector index** — OpenClaw pauses vector search + warns (doesn't silently re-embed); rebuild with `openclaw memory index --force`. **Explicit remote providers fail closed** (no silent FTS fallback); only unset/`auto`/`none` fall back.

**Dreaming** (opt-in, off by default; `memory-core.config.dreaming`, cron `0 3 * * *`) — background consolidation, phases **light → REM → deep** (only *deep* promotes durable facts to `MEMORY.md`, gated by `minScore=0.8`, `minRecallCount=3`, `minUniqueQueries=3`); writes `memory/.dreams/` + `DREAMS.md`. Rides the heartbeat; "Dreaming status: blocked" = blocked heartbeat.

**Companions:** **active-memory** (a *blocking* recall sub-agent that runs *before* the main reply, bounded worst-case budget) · **memory-wiki** (structured claims/evidence/contradiction vault beside the active backend; `bridge`/`isolated`/`unsafe-local` modes; `memory_search corpus=all` spans both).

---

## 8. Tools, exec, sandbox & elevated — the four orthogonal controls

The clearest expression of OpenClaw's philosophy: **system-prompt/SOUL/AGENTS guardrails are advisory only. Real enforcement is tool policy, exec approvals, sandboxing, and channel allowlists.** Memory ≠ policy.

Four controls that must not be conflated (`openclaw sandbox explain` debugs them together):
1. **Sandbox** = **WHERE** tools run.
2. **Tool policy** = **WHICH** tools exist.
3. **Elevated** = exec-only **escape hatch** to run *outside* the sandbox.
4. **Exec approvals** = the durable **allow/ask** gate on shell/file exec.

### 8.1 Tool policy (each layer can only narrow; deny always wins)
`tools.profile` (`minimal` | `messaging` | `coding` (new local default) | `full`) → `tools.byProvider` → global `allow`/`deny` → per-provider allow/deny → per-agent → `tools.sandbox.tools` (second gate for sandboxed sessions) → `tools.subagents.tools`. **A non-empty `allow` blocks everything else; if any step empties the callable set, OpenClaw fails loud before submitting** (never degrades to text-only). `tools.alsoAllow` adds back only at the *profile* stage (e.g. `browser`, absent from `coding`); later layers can't re-add. Groups (`group:runtime|fs|sessions|memory|web|ui|automation|messaging|nodes|agents|media|plugins`). Per-sender `toolsBySender` (key prefixes `channel:`/`id:`/`e164:`/`username:`/`name:`/`*`). Public-channel hardening pattern: deny `group:runtime`, `group:fs`, `group:ui`, `gateway`, `nodes`, `cron`, `browser`.

**Three warnings that are the same mistake in different clothes:** *exec ≠ read-only* (denying `write`/`edit`/`apply_patch` leaves `exec` free to write — for real read-only deny `exec` **and** `process`, or `workspaceAccess: ro|none`; note `apply_patch` is distinct from `write`) · *allowlist ≠ authorization boundary* (allowlists are discovery/prompt/UI filters; an agent with `exec` reaches host files regardless) · *host env ≠ sandbox env* (`skills.entries.*.env`/`apiKey` inject into the **host process per-turn only**). All three come from conflating a discovery/UI filter with an execution boundary.

**The MCP-in-sandbox trap:** MCP/plugin tools need an explicit `tools.sandbox.tools` entry (`bundle-mcp`, `group:plugins`, or server glob) or they load then get silently filtered before the provider request; `doctor` catches this only for `mcp.servers`-declared servers.

### 8.2 Exec authorization stack (five layers, "stricter-of")
1. Tool policy (is `exec`/`process` allowed at all?).
2. **Sandbox** — `tools.exec.host: auto|sandbox|gateway|node` (`auto` = sandbox if active else gateway; `host=sandbox` **fails closed** with no sandbox — set `gateway` explicitly for real host exec).
3. **Elevated** (`/elevated on|full|off`) — only meaningful for *sandboxed* agents; breaks out to host. Gated by ALL of: `tools.elevated.enabled` + `allowFrom.<channel>` + per-agent overrides. Cannot override a tool-policy denial of `exec`. **`tools.elevated` is global/sender-based, not per-agent** (use per-agent `tools.deny`).
4. **Exec approvals** — the **host approvals file is the enforceable source of truth** (`$OPENCLAW_STATE_DIR/exec-approvals.json` + `.sock`); `tools.exec.*` config expresses intent that can narrow/broaden but the effective result = **stricter-of** config and host file. Per-agent allowlists (binary-path or bare-name globs + `argPattern` regex). Pending approvals expire **30 min**. `openclaw exec-policy` is *local-only* (does not push to gateway/node hosts).
5. **Mode** (`tools.exec.mode`, normalized): `deny` → `allowlist` → `ask` (human on miss) → **`auto`** (allowlist → auto-review → human; recommended) → `full` (no prompts). Maps to Codex Guardian and ACPX `permissionMode`.

**"YOLO" needs BOTH layers explicitly:** `tools.exec.security:full` + `ask:off` **and** host `askFallback:full` (omitted `askFallback` defaults to **deny**). Shortcut `openclaw exec-policy preset yolo` (local only); session-only `/exec security=full ask=off`. **Safe-bins fast-path** (`tools.exec.safeBins`: `cut uniq head tail tr wc` — *not* `grep`/`sort`): stdin-only, literal argv, no interpreters, must resolve from `safeBinTrustedDirs` (`/bin`,`/usr/bin`; PATH never auto-trusted). `strictInlineEval:true` forces approval for `python -c`/`node -e` even when allowlisted; shell chaining requires every segment to pass; command substitution rejected.

**Approval routing** (independent tracks that don't configure each other): `approvals.exec` (routes exec prompts to chat) · `channels.<ch>.execApprovals` (makes a channel a native approval *client* — Discord buttons 30-min TTL, iMessage 👍/👎, Matrix ✅/❌/♾️, Slack/Telegram/Signal/QQ) · `approvals.plugin` (plugin permission requests) · Codex-native review · MCP elicitations. All resolve via chat buttons + `/approve <id> allow-once|allow-always|deny`. **`allow-always` is only durable if the plugin persists it** (generic hooks don't auto-remember); fingerprints are per (provider/session/tool-input/cwd) for a bounded window. Approver lists are distinct from chat allowlists.

### 8.3 Sandbox (`agents.defaults.sandbox`, per-agent per-field override)
- `mode: off | non-main | all`; `backend: docker (default) | ssh | openshell`; `scope: session | agent (default) | shared`; `workspaceAccess: none (default) | ro | rw`.
- **The `non-main` surprise:** it keys off `session.mainKey`, **not agent id** — group/channel sessions are non-main → sandboxed, while your main DM isn't. For guaranteed-never-sandboxed set `mode:"off"`.
- **Ordering rule everywhere:** tool policy applies *before* sandbox — sandboxing never restores a denied tool, and `/exec` can't override a denied `exec`.
- Docker knobs: `network:"none"` default (`host` blocked; `container:<id>` gated by `dangerouslyAllowContainerNamespaceJoin`); `setupCommand` (once, needs net+root+writable root); `binds` blocks `docker.sock`/`/etc`/`/proc`/`~/.ssh`/`~/.aws` (symlink-parent escapes resolved). Default image `openclaw-sandbox:bookworm-slim` (no Node — bake it; needs `python3` for write/edit helpers). Auto-prune after 24h idle (so regular agents keep stale runtime config until `sandbox recreate`). **Destructive gotcha:** `sandbox recreate` for ssh/openshell **deletes the canonical remote workspace** (re-seeded from local).
- **Never mount host `docker.sock` into an agent sandbox.** AppArmor (Linux) `workspace-write` without an active sandbox can hit `bwrap: setting up uid map: Permission denied` — fix via `openclaw doctor`, not the host-wide sledgehammer.

### 8.4 Code Mode (`tools.codeMode.enabled`) — the strongest sandbox statement
The model sees only `exec` + `wait`; `exec` runs model-generated JS/TS in a **QuickJS-WASI worker** treated as hostile (no fs/net/subprocess/module-import/env; memory+interrupt limits; narrow JSON bridge; host errors converted to plain guest errors). Hidden tools reached via `ALL_TOOLS`/`tools`/`MCP.<server>.<tool>()` globals through the *same* executor/policy/approval/hook path as normal calls. **Supersedes Tool Search and fails closed** if the runtime can't load. Tool Search (`tool_search`/`tool_describe`/`tool_call` proxies; also `localModelLean:true`) is the lighter alternative to keep small-model prompts lean. Both are *views*, not separate execution engines — one policy/approval/hook pipeline underlies every tool call.

---

## 9. Channels & messaging — one shape, ~30–45 implementations

The largest part of the corpus, with a strikingly uniform contract. Learn it once. **One shared `message` tool, owned by core** — channel plugins never implement send/edit/react; they own config, security (DM policy/allowlists), pairing, session grammar, outbound send, threading. Each channel is documented in up to three places (`channels/<name>.md`, `plugins/reference/<name>.md`, `gateway/config-channels.md`) — check all.

### 9.1 The universal access-control skeleton (`channels.<channel>`)

| Concern | Keys | Default |
|---|---|---|
| DM gate | `dmPolicy: pairing\|allowlist\|open\|disabled` + `allowFrom` | **`pairing`** |
| Group gate | `groupPolicy: open\|allowlist\|disabled` + `groupAllowFrom` / `groups.<id>` | **`allowlist`** |
| Mention gate | `requireMention` (per-group / `groups."*"`) | **`true`** |
| Media/text | `mediaMaxMb`, `textChunkLimit`, `chunkMode` | varies |
| History | `historyLimit` / `dmHistoryLimit` (falls back to `messages.groupChat.historyLimit`; `0` disables) | often 50 |

**The two rules repeated across every channel:**
1. **Fail-closed by absence.** A missing `channels.<provider>` block forces `groupPolicy="allowlist"` regardless of `channels.defaults`. Discord: a bare `DISCORD_BOT_TOKEN` with no block silently becomes `allowlist` even if defaults say `open`.
2. **`open` still needs a literal `"*"`.** `dmPolicy:"open"` is public only if effective `allowFrom` contains `"*"`; pairing approvals never widen `open`.

**Gates are independent and layered, not substitutable:** DM pairing ≠ group authorization (separate stores) · allowlisting a sender ≠ disabling mention gating · reply-to-bot satisfies *mention* but not *sender* auth · trigger authorization ≠ **context visibility** (`contextVisibility: all (default)|allowlist|allowlist_quote`).

**The #1 recurring footgun — two-gate group registries (iMessage, by pattern others):** under `groupPolicy:"allowlist"` you must satisfy *both* `groupAllowFrom` *and* a `groups` registry (`groups:{"*":{...}}` or per-`chat_id`). Operators copy the allowlist but skip `groups` → silent drops (warn-level lines at `inbound-processing.ts:199/512`).

**Name-matching is break-glass everywhere:** channels prefer stable numeric/opaque IDs and refuse display-name/username matching unless `dangerouslyAllowNameMatching:true` (flagged by `security audit`). Slack's sharp version: `channels.slack.channels` keys **must be `C…` IDs, not `#name`** (name keys silently fail under `allowlist`, confusingly work under `open`).

**Access groups:** `accessGroups.<name>: {type:"message.senders", members:{<channel>:[ids]}}` (`"*"` shared), referenced as `accessGroup:<name>` anywhere an allowlist appears. No cross-channel ID translation; **missing group name authorizes nobody** (fails closed). Discord adds dynamic `discord.channelAudience` (live `ViewChannel` permission; needs Server Members Intent). **Never precompute effective allowlists — the resolver derives from raw inputs**; raw sender/allowlist values are input-only, never in decisions/diagnostics (redacted opaque ids only).

### 9.2 Per-channel defaults worth memorizing

| Channel | `mediaMaxMb` | `textChunkLimit` | Transport | Notable |
|---|---|---|---|---|
| Telegram | 100 | 4000 | long-poll | one poller/token or 409 |
| WhatsApp | 50 | 4000 | Baileys/QR | **Node only (Bun incompatible)** |
| Discord | 100 | — | gateway WS | Components v2, voice |
| Slack | 20 | 4000 (`newline`) | Socket/HTTP | **ID-only channel keys** |
| Signal | 8 | 4000 | signal-cli HTTP | dedicated bot number |
| iMessage | **16** | 4000 | `imsg` JSON-RPC | two-gate footgun |
| Feishu | 30 | 2000 | WebSocket | dynamic per-user agents |
| LINE | 10 | 5000 | webhook | HMAC on raw body |
| Google Chat | 20 | — | webhook only | bearer + audience |
| SMS (Twilio) | — | — | webhook | signature validation |

### 9.3 Presentation & delivery
- **Streaming has two layers** (no true token-delta streaming to channels): **block streaming** (`agents.defaults.blockStreaming*`, off by default; non-Telegram needs explicit `*.blockStreaming:true`) and **preview streaming** (`channels.<ch>.streaming.mode: off|partial|block|progress` or Matrix `off|partial|quiet` — send-then-edit). **Progress drafts** after ≥5s of proven work, with a crab-themed label pool (Working/Shelling/Scuttling/Clawing/Molting…). Legacy `streamMode`/boolean aliases rewritten by `doctor --fix`.
- **Markdown pipeline:** parse → IR (style/link spans, UTF-16 offsets) → chunk IR (so formatting never splits) → per-channel render (Slack mrkdwn, Telegram HTML, Signal ranges). Tables per `markdown.tables` (`code`/`bullets`/`off`).
- **Rich output** = portable `MessagePresentation` (`interactive-runtime`): text/context/divider/buttons/select/card — rendered natively (Discord Components, Slack Block Kit, Telegram keyboards, Teams Adaptive Cards, Feishu) and **degrades to text** when unsupported. `delivery.pin.required:true` is the one exception that reports failure instead of degrading.
- **Reply threading:** `[[reply_to_current]]`/`[[reply_to:<id>]]` + `replyToMode: off|first|all|batched`.
- **Ack reactions** resolve through a ladder: `accounts.<id>.ackReaction` → `channels.<ch>.ackReaction` → `messages.ackReaction` → identity emoji → default (👀/`eyes`). **`messages.ackReactionScope` defaults to `group-mentions` — excludes DMs** (repeated gotcha); read only at startup (restart to change).
- **Silent replies:** `NO_REPLY`/`no_reply`/`ANNOUNCE_SKIP` suppress the visible reply but still deliver pending tool media (e.g. TTS). Direct chats never get silence guidance. **Cron never infers reply language** — state it in the prompt.
- **Bot-loop protection:** shared sliding window (`channels.defaults.botLoopProtection`: `maxEventsPerWindow:20`, `windowSeconds:60`, `cooldownSeconds:60`), opt-in per channel with reliable bot identity.
- **Retry** is per-HTTP-request, not per-flow (default 3, 30s cap, 10% jitter). Multi-account everywhere via `channels.<ch>.accounts.<id>` (env tokens = `default` account only; `doctor --fix` promotes top-level → `accounts.default`).
- **Ambient/broadcast:** `unmentionedInbound:"room_event"` + `visibleReplies:"message_tool"` feed quiet context (agent must `message(action=send)` to speak). `broadcast` (WhatsApp-only, experimental) fans one message to multiple agents (`strategy: parallel|sequential`), evaluated *after* allowlists, loses to exclusive ACP bindings.
- **Mention-gating silent-failure:** `messages.visibleReplies: automatic` (posts final text) vs `message_tool` (agent must call `message(action=send)`, else the reply stays private — symptom: typing indicator then silence, `queuedFinal=false, replies=0`).

---

## 10. Automation — seven mechanisms, one decision table

| Need | Mechanism | Creates task? | State |
|---|---|---|---|
| Exact timing / reminders | **Cron** | yes | SQLite in Gateway |
| Periodic context-aware checks | **Heartbeat** (default 30m) | **no** | — |
| Inspect detached work | **Tasks** (ledger, not scheduler) | — | `tasks/runs.sqlite` |
| Durable multi-step flows | **Task Flow** | — | SQLite + bounded WAL |
| Lifecycle side-effects | **Hooks** (internal) / **Webhooks** (external) | — | — |
| Persistent authority | **Standing Orders** (`AGENTS.md`) | — | — |
| Natural follow-up memory | **Inferred Commitments** (opt-in) | — | commitments store |

**Cron** (`openclaw cron`) runs *inside* the Gateway. Two job kinds: **agent jobs** (through a session — `main`/`isolated`/`current`/`session:<id>`; `isolated` inherits only safe prefs, *not* routing/elevation/origin/ACP binding) and **command jobs** (`--command`, deterministic shell, require **`operator.admin`** — not `tools.exec`). Schedule kinds `at`/`every`/`cron` (5/6-field + `--tz`); **croner DOM+DOW is OR logic** — use `+` (`0 9 15 * +1`) to require both; top-of-hour auto-staggers ≤5min unless `--exact`. Model precedence: Gmail hook override → per-job payload `model` → stored session override → agent default; per-job overriding only `primary` still inherits default fallbacks unless `fallbacks:[]`. **Local-provider preflight** records `skipped` (cached 5min) when ollama/vLLM loopback is down. Config: `maxConcurrentRuns:8`, `retry.{maxAttempts:3, backoffMs:[60k,120k,300k]}` (recurring: 30s→1m→5m→15m→60m), `sessionRetention:"24h"`. One-shots (`--at`) self-delete after success. Delivery (`announce`/`webhook`/`none`) is separate from `failureDestination`. **Use cron for wait-loops/reminders — never `sleep` in `exec`.**

**Tasks** = a *ledger for detached work* (ACP/subagent/isolated-cron/CLI/media), never a scheduler. Lifecycle `queued→running→{succeeded|failed|timed_out|cancelled|lost}` (`lost` = backing state gone after 5-min grace). Push-driven completion (direct delivery or wake-next-heartbeat); default notify varies (`done_only` for ACP/subagent, `silent` for cron/CLI/media). 60-second sweeper reconciles; **7-day retention, no config**.

**Heartbeat** — a periodic **main-session** agent turn (default 30m; **1h under Anthropic OAuth/token/Claude-CLI**; `0m` disables). Prompt: read `HEARTBEAT.md`, reply `HEARTBEAT_OK` (or `heartbeat_respond`). **If *any* agent defines a `heartbeat` block, only those agents run heartbeats.** Skipped if `HEARTBEAT.md` is effectively empty (a *missing* file still runs). Cost levers: `isolatedSession:true` (~100K→2–5K tokens), `lightContext:true`, cheaper model, `activeHours`. **Gotcha: heartbeats are full turns — shorter interval = more token burn;** if one ran on a small local model, reset the session runtime model before the next main turn or overflow. Skip reasons in logs: `quiet-hours`, `lanes-busy`, `empty-heartbeat-file`, `no-tasks-due`, `dm-blocked`. Drives **commitments** and **dreaming**.

**Internal hooks** (`HOOK.md` + `handler.ts` default export) fire on lifecycle events (`command:*`, `session:compact:*`, `agent:bootstrap`, `gateway:startup/shutdown/pre-restart`, `message:*`); gated until enabled (`openclaw hooks enable <name>`). Precedence: bundled < plugin < managed (`~/.openclaw/hooks/`) < workspace (off by default). Bundled: `session-memory`, `bootstrap-extra-files`, `command-logger`, `compaction-notifier`, `boot-md`. **The split:** file-based side-effects → internal hooks; prompt-rewrite/tool-block/message-cancel → typed *plugin* hooks (`api.on(...)`); `command:stop` is observation-only — use plugin hook `before_agent_finalize` to gate finalization.

**Webhooks** (`/hooks`, shared-secret **header-only** bearer, loopback/tailnet/trusted-proxy only): `/hooks/wake`, `/hooks/agent`, mapped `/hooks/<name>`. Token must differ from gateway token (`security audit` critical, `doctor --fix` rotates); `path` can't be `/`; transforms confined to `~/.openclaw/hooks/transforms`. **Gmail PubSub** (`hooks.gmail`) auto-starts a watcher on boot (opt out `OPENCLAW_SKIP_GMAIL_WATCHER=1`). Treat payloads as untrusted; keep `allowUnsafeExternalContent` off.

**Standing Orders** live in auto-injected bootstrap files (only the fixed basenames — `AGENTS.md`, `SOUL.md`, `TOOLS.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `BOOTSTRAP.md`, `MEMORY.md`; not arbitrary subdir files). Pattern: **Execute-Verify-Report** ("I'll do that" ≠ execution; retry once, max 3, then escalate). Without a cron trigger, standing orders are "mere suggestions."

**Other orchestration:** **Workboard** (bundled-but-disabled Kanban, relational SQLite, claim-token-guarded, ≤3 workers/pass) · **OpenProse** (`/prose`, markdown multi-agent workflows over `sessions_spawn`/`read`/`write`/`web_fetch`; transitive remote `use` imports need explicit `approve remote prose imports`) · **MCP** (`mcp.servers`, stdio or `streamable-http`/`sse`, `sessionIdleTtlMs` 10min, `toolFilter`, `auth:"oauth"`; **env safety filter** blocks interpreter-startup keys — `NODE_OPTIONS`/`PYTHONPATH`/`LD_PRELOAD`-class — even inside a server's `env` block; ordinary creds pass).

---

## 11. The plugin & extension system — the load-bearing wall

### Distribution tiers (one registry)
- **Core npm bundled** (~59): anthropic, openai, google, codex, memory-core, telegram, browser, canvas, policy, oc-path… (no install).
- **Official external** (~68): discord, slack, whatsapp, matrix, signal, most extra providers, memory-lancedb, voice-call, copilot… (`openclaw plugins install @openclaw/<name>` + **restart**).
- **Source-checkout-only** (3): `qa-channel`, `qa-lab`, `qa-matrix`.

Install sources: `clawhub:` / `npm:` / `git:` / `npm-pack:` / local / `--link` / `<plugin>@<marketplace>` (bare specs resolve bundled → official → npm). **Gateway restart required to activate.** Verify **live** registration with `openclaw plugins inspect <id> --runtime --json` (cold `list` does *not* prove the Gateway imported it). Install metadata lives in shared SQLite (`installed_plugin_index`), not config. Dependency work happens **only at install/update time** (`npm install --omit=dev --ignore-scripts`); runtime never runs a package manager.

### Manifest vs runtime; control-plane freshness
- **Manifest** (`openclaw.plugin.json`) = control-plane truth: id, strict `configSchema`, `providers`/`channels`/`cliBackends` ownership, `contracts.*` (incl. `contracts.tools` — tells OpenClaw which plugin owns each tool *without loading code*), `activation.*` hints. Stale manifests → tools missing from discovery. Build with `openclaw plugins build --entry ./dist/index.js` (`--check` in CI).
- `activation.*` is **planner metadata only** — narrows which plugins load, doesn't register behavior. Set `activation.onStartup` explicitly.
- **`register(api)`** is the only thing that wires runtime surfaces in.
- **The deepest invariant: control-plane answers are never wall-clock cached.** "Who owns this provider?" is computed fresh from an explicitly-passed snapshot (`PluginMetadataSnapshot`, rebuilt+replaced on change, never mutated in place). Only the *data plane* (module loading, Jiti caches, manifest file-signature cache keyed by path+inode+size+mtime) persists. This is why manifests are separable from code — config/UI/validation must work without running plugin code.

### The `api` contract & ownership model
`OpenClawPluginApi` is one typed object; capability registration is a flat table: `registerProvider` (HTTP inference), `registerCliBackend`, `registerAgentHarness` (trusted-only), `registerChannel`, `registerEmbeddingProvider`, `registerSpeechProvider`/`registerRealtimeVoiceProvider`, `registerMediaUnderstandingProvider`, `registerImage/Video/MusicGenerationProvider`, `registerWebFetch/SearchProvider`, `registerGatewayDiscoveryService`; infra: `registerTool`, `registerHook`, `registerHttpRoute`, `registerGatewayMethod`, `registerCli`, `registerService`, `registerContextEngine`, `registerMemoryCapability`, `registerTrustedToolPolicy`. Runtime helpers `api.runtime.*` (`.tts`, `.mediaUnderstanding`, `.webSearch`, `.subagent`, `.llm`, `.agent`, `.nodes`, `.tasks`, `.config`, `.state`, `.channel`) give host-owned services without reimplementation.

**The rule enforced by contract tests + boundary-report CI:** *plugin = ownership boundary* for a company/feature; *capability = shared core contract*. Never wire a vendor directly into a channel/tool — define core contract → expose via SDK → wire consumers through the runtime helper → let vendors register implementations. A PR hardcoding vendor behavior into a channel gets sent back. Three strict layers: **Core** (orchestration/policy/fallback/config-merge/contracts) / **Vendor plugin** (APIs/auth/catalogs) / **Channel-or-feature plugin** (integration).

### Plugin hooks (where policy is enforced)
Two systems: **plugin hooks** (`api.on(...)`, in-process, sequential by descending `priority`, timeouts `hooks.timeouts.<name>` > `hooks.timeoutMs`, max 600000ms) and **internal hooks** (§10). Catalog spans the turn: `before_model_resolve`/`before_prompt_build`/`before_agent_run`/`before_agent_finalize`/`agent_end`; `before_tool_call`/`after_tool_call`/`resolve_exec_env`/`tool_result_persist`; message (`inbound_claim`/`message_sending`/`before_dispatch`); session/compaction/subagent; lifecycle (`gateway_start`/`gateway_stop`/`cron_changed`/`before_install`). Semantics: `{block:true}`/`{cancel:true}` terminal; `false` variants no-op (don't clear a prior block). `before_tool_call` can return `requireApproval{...}`. **New plugins use `before_model_resolve`+`before_prompt_build`, not deprecated `before_agent_start`.** Non-bundled plugins need `plugins.entries.<id>.hooks.allowConversationAccess:true` for raw conversation; `registerTrustedToolPolicy` requires declared ids in `contracts.trustedToolPolicies`.

### SDK import discipline (mid-migration)
Always import narrow subpaths (`openclaw/plugin-sdk/plugin-entry`, `/channel-core`, `/channel-outbound`, `/config-mutation`, `/interactive-runtime`, `/security-runtime`…), **never** the root barrel `openclaw/plugin-sdk` (deprecated) or another plugin's `src/*`. A large dated deprecation layer exists (`compat`, `infra-runtime`, branded seams like `plugin-sdk/discord`) — CI rejects new bundled production imports from it. Vocabulary shifts: `turn`→inbound/outbound; `activate`→`register`; `deactivate`→`gateway_stop` (removal after **2026-08-16**); memory calls collapsed to `registerMemoryCapability`; talk consolidating onto `talk.session.*`/`talk.client.*`.

### Skills (instructions, not code)
ClawHub or `git:`/local; `SKILL.md` required at root (**no npm/zip**, unlike plugins). Load precedence (high→low): workspace `skills/` → `.agents/skills` → `~/.agents/skills` → managed `~/.openclaw/skills` → bundled → `extraDirs`; same name → highest wins. System prompt injects a compact `<available_skills>` list (metadata only, content-hash versioned); full `SKILL.md` read on demand. Frontmatter (`metadata.openclaw`): `requires.{env,bins,anyBins,config,os}`, `install[]` (`brew`/`node`/`go`/`uv`), `always`; `command-dispatch:"tool"` routes a slash command straight to a tool. **Skill Workshop** governs writes: agents never edit `SKILL.md` directly — **propose → apply** (`skill_workshop` tool; hash-bound proposals go `stale` if the target changes; `maxPending:50`, `maxSkillBytes:40000`; **sandboxed sessions cannot construct this tool**). **Skill token cost formula:** `195 + Σ(97 + len(name)+len(description)+len(filepath))` — keep descriptions short.

---

## 12. The Codex harness — the stress test of every subsystem at once

The bundled `codex` plugin runs turns through the **Codex app-server** (`0.125.0`+, stable-only). Codex owns the native thread, model loop, tool continuation, and compaction; OpenClaw owns channel routing, session files, dynamic tools, approvals, media, transcript mirror. Model refs `openai/gpt-5.5` (not legacy `codex/gpt-*`). Config under `plugins.entries.codex.config.appServer.*`:
- **Two presets:** `mode:"yolo"` (default → `approvalPolicy:"never"`, `sandbox:"danger-full-access"`) vs `mode:"guardian"` (→ `on-request`, `workspace-write`, `auto_review`). An **active OpenClaw sandbox narrows full-access → workspace-write** automatically.
- **Gotcha:** `tools.exec.mode:"auto"` *forces* guardian approvals — use `tools.exec.mode:"full"` for intentional no-approval.
- **Env isolation:** `CODEX_HOME` per-agent; `HOME` deliberately *not* rewritten (so `gh`/`git`/cloud CLIs see the real home); ChatGPT-subscription auth strips `CODEX_API_KEY`/`OPENAI_API_KEY` from the child to prevent accidental API billing.
- **Dynamic tools** with Codex-native equivalents (`read`/`write`/`edit`/`exec`/`apply_patch`/`process`/`update_plan`) are excluded from Codex context; integration tools load via tool-search under `openclaw`.
- Native hooks (`PreToolUse`/`PostToolUse`/`PermissionRequest`/`Stop`) relay into OpenClaw hooks; **V1 is block-only** (no arg rewriting, mirror-only transcript, no compaction veto). **Copilot** mirrors the pattern (`@openclaw/copilot`, +260MB) — permissions enforced inside the tool wrapper (`before_tool_call`), not the SDK callback.

Reading the Codex integration is the fastest way to see how harness selection, env isolation, dynamic-tool routing, native-hook relay, three approval gates, sandbox narrowing, transcript mirroring, and media pass-through compose.

---

## 13. Nodes, pairing & device control

### Two distinct pairing surfaces
- **DM pairing** (who can chat): 8-char codes (no ambiguous chars), **expire 1h**, **max 3 pending/channel**. First-ever approval with no `commands.ownerAllowFrom` **auto-bootstraps that sender as owner** (once; later approvals don't expand it — `doctor` prints the fix). Stored in `credentials/<channel>-pairing.json`. `openclaw pairing approve --channel <ch> <code>`.
- **Node device pairing** (which devices join): connect `role:node` → pending (**expires 5 min**) → `openclaw devices approve <id>` → device token (rotated on re-pair). Bootstrap tokens grant `node` + bounded `operator` (approvals/read/write) — **never `operator.admin`/`operator.pairing`**. Every `connect` signs a challenge nonce; signature `v3` binds platform/deviceFamily. Plaintext `ws://` setup accepted only for loopback/LAN/`.local`; public/tailnet fail closed (need `wss://`/Tailscale, or env `OPENCLAW_ALLOW_INSECURE_PRIVATE_WS=1` for plaintext LAN). Opt-in `gateway.nodes.pairing.autoApproveCidrs` covers *first-time* `role:node` only (any forwarded header disqualifies a loopback claim). **Breaking change 2026.3.31+:** node commands disabled until node pairing approved (device pairing alone insufficient); commands queued before approval are **dropped, not deferred**. Loopback browser connections auto-approve.

### Node execution — three independent gates (mirrors exec)
1. **Device pairing** — can the node connect?
2. **Gateway command policy** (`gateway.nodes.allowCommands`/`denyCommands` — deny wins, exact command-ID match, no shell-text inspection; dangerous commands `camera.snap`/`clip`/`screen.record` require explicit `allowCommands`).
3. **Exec approvals** — `system.run` gated per-node at `~/.openclaw/exec-approvals.json`, binding an exact canonical `systemRunPlan` (any mutation before forwarding rejected). Node hosts strip `PATH` overrides and dangerous env (`DYLD_*`/`LD_*`/`NODE_OPTIONS`).

Approval scope escalates by class: commandless → `operator.pairing`; non-exec → `+write`; `system.run` → `+admin`. `system.run`/`system.which` are **blocked** via `nodes invoke` — use the `exec` tool with `host=node`. Remote exec: `openclaw node run --host <gw>`, `tools.exec.host:"node"` + `security:"allowlist"` + `node:"<id>"`. Foreground-only surfaces (`canvas.*`/`camera.*`/`screen.*`) return `NODE_BACKGROUND_UNAVAILABLE` when backgrounded; clips clamp ≤60s.

### Desktop/media control (macOS)
Three deliberately-not-unified paths: **PeekabooBridge** (OpenClaw.app hosts a local UDS socket `0600`+token+peer-UID+HMAC+short TTL, `peekaboo` CLI is the client, uses the app's TCC grants), **Codex Computer Use** (native MCP after app-server prep), **direct `cua-driver` MCP**. **macOS TCC is its own security subsystem:** grants bind to code-signature + bundle-id + on-disk path (fixed `dist/OpenClaw.app`, stable bundle id, real signature required); **never grant Accessibility to the generic `node` binary** (every JS package inherits GUI automation); TeamID allowlists validated everywhere. **Canvas** = agent-controlled `WKWebView`/WinUI panel served via `openclaw-canvas://<session>/…` (traversal-blocked), hosting A2UI **v0.8 only**.

---

## 14. Voice & media stack

Media routing is uniform regardless of harness. Inbound media is **pre-digested** before the reply pipeline, but the **original is always still delivered to the model**: collect → select per capability → pick model by size+capability+auth → fallback → insert `[Image]`/`[Audio]`/`[Video]` block (`{{Transcript}}` for audio; skipped if the primary image model is natively vision-capable). Size caps: image 10MB, audio 20MB, video 50MB (`tools.media.<cap>.maxBytes`). **Mention preflight:** with `requireMention:true`, audio is transcribed *before* the mention check (`disableAudioPreflight` to opt out). Auto-detect fallback chains are explicit per modality (Audio → OpenAI→Groq→xAI→Deepgram→…; Image → OpenAI→Anthropic→Google→…; Video → Google→Qwen→Moonshot); local CLIs (`whisper-cli`) tried before providers for audio.

- **TTS** (`messages.tts.*`, ~14 providers; plugin `tts` deep-merges over it): precedence global → agent → channel → account → local `/tts` → inline `[[tts:...]]`; **personas** (stable spoken identity, `fallbackPolicy`). Output auto-selected by surface: MP3/WAV files, **Opus/OGG voice bubbles** (Feishu/Telegram/Matrix/WhatsApp, 48kHz via ffmpeg), **PCM/μ-law 8kHz telephony** (Microsoft TTS ignored for calls — no telephony PCM).
- **Batch STT** (`tools.media.audio.models[]`): Deepgram, ElevenLabs Scribe, Mistral Voxtral, OpenAI, Groq, xAI, SenseAudio.
- **Realtime voice** (full-duplex, separate from streaming STT, mutually exclusive per call): Gemini Live + OpenAI. **OpenAI Realtime requires Platform credits — NOT covered by Codex/ChatGPT subscription, API-key only.** Talk contract `realtime|stt-tts|transcription`, mid-migration onto unified `talk.session.*`/`talk.client.*`.
- **Image/video/music gen** → `image_generate`/`video_generate`/`music_generate` tools (async: submit → task → session wakes → deliver, with idempotent direct fallback; states `queued`/`running`/`succeeded`/`failed` via `openclaw tasks`). **Reference media for most video providers must be remote http(s) URLs — local paths rejected** (alibaba/qwen Wan, vydra Kling). Capability knobs widely accepted but silently ignored by many (Sora ignores all but `size`). New providers declare typed **capability schemas** — the fallback layer skips a candidate that can't satisfy audio/duration/options (first skip `warn`, rest `debug`).
- **Voice Call plugin** (richest single subsystem): Twilio/Telnyx/Plivo/mock, **public-webhook required** (fails on loopback/private), per-number routing, `sessionScope: per-phone|per-call`, `openclaw_agent_consult` tool (`toolPolicy: safe-read-only|owner|none`), full CLI. Google Meet dial-in rides on it (consumes realtime STT/TTS/voice; BlackHole+SoX deps, macOS-only, un-bundled for licensing).

---

## 15. Web tools trio & search providers

| Tool | What it is | Cache | Notes |
|---|---|---|---|
| `web_fetch` | Plain HTTP GET + Readability. **No JS.** | 15 min | On by default, no config. Blocks private/internal hosts, re-checks on redirect; `maxChars` 50k clamped, body cap `maxResponseBytes` 2MB. Use Browser tool for JS/login. |
| `web_search` | HTTP search API (not browser automation). | 15 min/query | 15 providers; native OpenAI/Codex paths. |
| `x_search` | X/Twitter posts via xAI. | 15 min | Per-post stats need the exact status ID. |

**The tool/plugin credential split (the single most important config pattern):** the tool is configured under `tools.*` (`tools.web.search.*`), but its provider's **API key lives at `plugins.entries.<plugin>.config.*`** (`plugins.entries.firecrawl.config.webFetch.*`, `plugins.entries.xai.config.xSearch.*`). **Provider selection is validated against manifest IDs — typos fail config validation, no silent auto-detect rescue.**

**`web_search` auto-detection (when `provider` unset):** API-backed priority order (Brave 10 → MiniMax 15 → Gemini 20 → Grok 30 → Kimi 40 → Perplexity 50 → Firecrawl 60 → Exa 65 → Tavily 70 → Parallel 75 → SearXNG 200); **key-free providers (Parallel-Free, DuckDuckGo, Ollama, Codex) are never silently auto-picked.** **Native exception:** direct OpenAI Responses + Codex app-server self-provision hosted search unless overridden. Most providers must be selected explicitly. **SSRF nuance:** managed-search fake-IP DNS allowances are scoped to that provider hostname and **do not extend to `web_fetch`** — each tool's egress trust is independent.

---

## 16. The security model — the spine through everything

Security is a *posture*, not a section. Layered network-in to tool-out.

### The trust model & threat model
OpenClaw's stated default is **single-trusted-operator** — explicitly **not** hostile-multi-tenant-safe. Real isolation = separate gateways under separate OS users/hosts. `sessionKey` is routing, not authorization. Native plugins run **in-process, unsandboxed — same trust boundary as core** (a malicious native plugin is arbitrary code execution in the Gateway). Threat model (MITRE ATLAS-based, `/security/THREAT-MODEL-ATLAS`): P0 = **direct prompt injection (detection-only)**, **malicious skill install (no sandboxing)**, **skills run with agent privileges**. Formal verification: TLA+/TLC models cover gateway exposure, node exec + tokenized approvals, pairing TTL/cap, mention-gating, routing/session isolation + dmScope precedence — an "attacker-driven regression suite," not a proof.

### The five/six auth boundaries (conflating them is the #1 source of confusion)
"Auth" means at least five unrelated things:
1. **Gateway connection auth** (`gateway.auth.mode: none|token|password|trusted-proxy`). **Non-loopback bind requires auth; loopback now enforces a runtime token by default too.** Both token+password with unset mode → **blocks** until mode chosen. `trusted-proxy` delegates to a reverse proxy injecting an identity header (checked against `gateway.trustedProxies`; **mutually exclusive with token**; requires *overwriting* `X-Forwarded-For`, not appending; `security audit` flags it critical by design). Rate limit `gateway.auth.rateLimit` (10/60s, loopback exempt). **Tailscale Serve identity** (`allowTailscale`) covers Control-UI/WS only — never HTTP API.
2. **The critical "HTTP = full operator" boundary.** `/v1/chat/completions`, `/v1/responses`, `/tools/invoke` are **full operator surfaces, not per-user scoped**. **Shared-secret auth (token/password) ignores narrower `x-openclaw-scopes` headers and restores full operator defaults** and treats the caller as owner. Only identity-bearing modes (trusted-proxy, `none` private-ingress) honor scopes. **Keep these on loopback/tailnet — never public.** All HTTP endpoints off by default except `/tools/invoke` (always on, with a **hard default deny list** regardless of session policy: `exec, spawn, shell, fs_write, fs_delete, fs_move, apply_patch, sessions_spawn, sessions_send, cron, gateway, nodes, whatsapp_login`; `gateway.tools.allow` is an *exposure* override, not a scope upgrade).
3. **Operator scopes** (control-plane RBAC): `operator.read ⊂ write ⊂ admin`, plus `pairing`/`approvals`/`talk.secrets`; `node` role. Method scope is the *first* gate; handlers apply stricter approval-time checks. Reserved prefixes (`config.*`, `exec.approvals.*`, `wizard.*`, `update.*`, `operator.admin.*`) always require `admin`.
4. **Model-provider auth** (§6) — separate, per-agent SQLite.
5. **SecretRef resolution** — additive layer.

A question like "is my key secure?" touches four of these, and shared-secret HTTP silently escalates to full operator.

### SecretRefs
`{source: env|file|exec, provider, id}` — the real credential surface. Resolved **eagerly at activation** into an in-memory snapshot; **unresolvable active ref → fail-fast startup** (only *effectively active* surfaces validated; `SECRETS_REF_IGNORED_INACTIVE_SURFACE`); reload = atomic swap keeping last-known-good. **Crucial boundary: SecretRef is NOT process isolation** — if plaintext lands in an agent-readable file, the agent's file/shell tools read it regardless of API redaction. Scope: in = user-supplied creds OpenClaw doesn't mint (provider keys, channel tokens, `gateway.auth`, `cron.webhookToken`); out = minted/rotated/OAuth-refreshed/session-bearing (WhatsApp creds, Discord webhook tokens, `auth-profiles.oauth.*`, `hooks.token`). **SecretRef + OAuth for the same profile fails fast.** `openclaw secrets` lifecycle: `audit` (`PLAINTEXT_FOUND`/`REF_UNRESOLVED`/`REF_SHADOWED`/`LEGACY_RESIDUE`) → `configure` → `apply` (`--dry-run` first; scrub is **one-way**) → `reload` (atomic, last-known-good on failure). Ref+plaintext → ref wins (`SECRETS_REF_OVERRIDES_PLAINTEXT`). Migration "done" only when audit is clean *and* legacy plaintext scrubbed. **Plaintext-by-default, SecretRef-opt-in** is the honest posture: optimize single-operator ergonomics, expose a hardened path at every secret-bearing surface, and the threat model openly rates plaintext token storage in `credentials/` as **High**.

### Prompt-injection defenses (first-class threat)
Applies even to trusted single-sender setups **the moment the bot reads untrusted external content** (web/browser/email/attachments). Mitigations recur: `contextVisibility` filters quoted/thread context; `strictInlineEval` forces approval for inline eval; shell approval rejects unquoted param-expansion in heredocs; a sanitizer strips chat-template special tokens (Qwen/ChatML/Llama/Gemma/Mistral/Phi) before the model; external content wrapped in `<<<EXTERNAL_UNTRUSTED_CONTENT id="…">>>` markers. **Small/quantized local models raise injection risk** — use the largest model, keep tool surface narrow, prefer the reader-agent pattern (an agent with no tools).

### Network egress / SSRF (default-on)
Built-in classifier (`packages/net-policy`): DNS pinning + IP blocking across loopback/RFC1918/link-local/**cloud metadata `169.254.169.254`/`metadata.google.internal`**/CGNAT/NAT64/IPv4-mapped. Break-glass: `request.allowPrivateNetwork`, `browser.ssrfPolicy.dangerouslyAllowPrivateNetwork`, `hostnameAllowlist`. Optional operator **forward proxy** (`proxy.enabled`, `proxy.loopbackMode: gateway-only|proxy|block`) routes egress through yours; `enabled:true`+no valid URL → protected commands fail startup; **IRC is raw TCP/TLS — not proxied.** `openclaw doctor` / `security audit` (`--deep`) codify the safe baseline; `--fix` flips `groupPolicy:"open"→"allowlist"` and tightens perms but **never** rotates secrets, disables tools, or changes bind/auth. File perms baseline: `openclaw.json` → `600`, `~/.openclaw` → `700`.

### The three auditors
- **`security audit`** (`--deep|--fix|--json`) — broadest: shared-DM, small-model-unsandboxed-with-web-tools, webhook token reuse, mutable-name allowlists, `auth.mode:"none"`, dangerous Docker network modes, `dangerous*` flags.
- **`doctor`** (`--fix`, `--lint` for CI) — health + guided repairs + the huge migration surface (cron→SQLite, `codex-*`→`openai/*`, sandbox registries, Talk config, bridge removal, owner bootstrap) + a **split-brain guard** (config stamped `meta.lastTouchedVersion`; an older binary refuses destructive actions on newer-written config; override `OPENCLAW_ALLOW_OLDER_BINARY_DESTRUCTIVE_ACTIONS=1`).
- **`policy`** (bundled plugin, `policy.jsonc`, ~40 check-ids via `doctor --lint`) — enterprise conformance *over* config (config-conformance only, no live inspection); strict; scoped overlays can only make rules stricter.

**The unifying browser-side principle (Control UI):** insecure-context (plain HTTP) blocks WebCrypto → no device identity → connections blocked. CSP is non-negotiable (`img-src` same-origin/`data:`/local `blob:`; **remote avatar URLs from channel metadata stripped + replaced with the built-in logo**). Tokens prefer URL **fragment** over query, stripped after load. Every relaxation is a scary-named, minimally-scoped key (`dangerously*`, `allowInsecure*`) that fails closed.

---

## 17. Deployment, distribution & lifecycle

**Every deploy target reduces to: bind mode + auth + persistent state dir + workspace + (optionally) Docker.** Cross-cutting invariants: `--allow-unconfigured` is bootstrap-only (never a substitute for `gateway.auth` + `mode:local`); **in Docker, bake binaries at image-build time** (anything installed in a running container is lost on restart); containers reach the host via `host.docker.internal` not `127.0.0.1`; memory floor ≥2GB for Docker builds (1GB OOM-kills `pnpm install`, exit 137); on small/ARM VMs wire `NODE_COMPILE_CACHE` + `OPENCLAW_NO_RESPAWN=1` into systemd. Targets: bare install (`install.sh`/`install.ps1`), Docker (GHCR `ghcr.io/openclaw/openclaw:latest`, `tini` PID 1), Podman (rootless, `--quadlet`, host CLI creds NOT mounted), Ansible (UFW+Tailscale+systemd hardening; gateway on host, Docker only for sandboxing), Fly/GCP/Hetzner/Azure/DO/Oracle/RPi, Kubernetes (Kustomize, `kubectl port-forward`), Nix (immutable config), managed one-clicks (Volume at `/data`, port env must match proxy). macOS VM (Lume) only for iMessage or strict isolation.

**ClawHub** (clawhub.ai) — public registry, three surfaces: **Skills** (versioned `SKILL.md` bundles, ≤50MB, **MIT-0, no paid skills**), **code plugins**, **bundle plugins**. Two CLIs: `openclaw` (installs into OpenClaw, tracks provenance) and `clawhub` (auth/publish/moderation). Resolution prefixes `clawhub:`/`npm:`. Publishing is open-but-gated: GitHub-account-age gate, automated scans (SkillSpector + VirusTotal + ClawScan on an **OWASP Agentic Skills Top 10** lens), moderator action; audit status `Pass`/`Review`/`Warn`/`Malicious`/`Pending`/`Error` + separate risk level. **Trusted publishing** = GitHub Actions OIDC (`workflow_dispatch` secretless with `id-token:write`; tag-push needs `CLAWHUB_TOKEN`). Plugin `package.json` must declare `openclaw.compat.pluginApi` + `openclaw.build.openclawVersion` (top-level `version` is *not* a fallback). **HTTP API v1** (Bearer `clh_…`): canonical install-decision surfaces are `GET /packages/{name}/versions/{version}/security` (gate on `trust.blockedFromDownload`) and `GET /skills/{slug}/verify` (Skill Card). Rate limits read 3000/min, write 300/min. **Compatible bundles** (Codex/Claude/Cursor content packs) are the *safer* tier — no in-process code, boundary-checked. The May 2026 perf sweep extracted many former-core deps (Bedrock, Slack, Matrix, WhatsApp, OpenShell) into plugins — tarball 43.3MB→17.9MB, cold-turn latency ~5×.

**Migration** (`openclaw migrate`): Claude Code/Desktop/Hermes importers preview → redact secrets → back up → apply; import content live (CLAUDE.md→AGENTS.md, MCP, skills) but **archive-only** the risky bits (hooks, tool allowlists, opaque OAuth) — OpenClaw refuses to auto-execute hooks or trust allowlists. `--include-secrets` required for secrets. Hermes memory import *appends*, never overwrites.

**Release lanes:** **stable** (`YYYY.M.PATCH` — since June 2026 PATCH is a *sequential monthly train number*, not a calendar day; npm versions immutable), **beta** (`-beta.N`), **dev** (moving `main`). Switch via `openclaw update --channel` (persists); `--tag` is a non-persistent one-off. Auto-updater off by default (`update.auto.enabled`). Updates install to a temp prefix, verify, then swap (never overlay-on-stale); managed installs use a detached handoff (Gateway exits, CLI takes over). Compat is *governed*: a compat registry + doctor-migration registry track every shim with owner/dates/replacement/tests (removal ≤3 months out); real removal dates appear in docs (WhatsApp flat→nested envelope removal **2026-08-30**; `deactivate`→`gateway_stop` after **2026-08-16**). The governing rule: **`doctor --fix` owns legacy repair — no new hidden startup migrations**; prove compatibility via upgrade-survivor tests.

**Maturity — read skeptically:** the scorecard reports **overall 67% (Alpha)** but **coverage 4%**, and **coverage is not an input to the maturity score** — a surface can be M4/Stable with ~0% QA coverage (e.g. macOS Gateway host). "Stable" = human-reviewed quality + completeness, *not* well-tested. M4 today: CLI, Gateway runtime, Linux/macOS hosts, Discord. Most surfaces held below Stable by **upstream volatility** (WhatsApp/Baileys, provider churn), not doc gaps.

---

## 18. Web surfaces, CLI & operations

**Web surfaces** all speak the Gateway WS on `:18789`:

| | Control UI / Dashboard | TUI | WebChat |
|---|---|---|---|
| Tech | Vite+Lit SPA at `/` | Terminal | SwiftUI (mac/iOS) |
| Connection | Gateway WS | Gateway *or* local embedded | Gateway WS |
| Role | Full admin | Chat + ops + local `!` shell | Chat only |
| Expose publicly? | **No** — loopback/Tailscale/SSH | n/a | n/a |

Shared RPC vocabulary: `chat.*`, `talk.*`, `sessions.*`, `config.get/set/apply/schema`, `cron.*`, `skills.*`, `node.list`, `exec.approvals.*`, `doctor.memory.*` (Dreams), debug (`status`/`health`/`logs.tail`/`update.run`). **Chat sends are non-blocking + idempotent** (`chat.send` acks `{runId,status:"started"}`; same `idempotencyKey` → `in_flight` then `ok`). **Transcript ≠ delivery** (load-bearing distinction): the session **JSONL** is durable model/runtime truth; **`ReplyPayload` events** are the live delivery projection (streaming/directives/media/TTS). `chat.history` returns stored transcript + display projection, strips display-only directives (`[[reply_to_*]]`, `[[audio_as_voice]]`) and sentinel-only entries (`NO_REPLY`/`HEARTBEAT_OK`). TUI/WebChat are *inbound* surfaces, not reusable outbound channels (TUI delivery off by default, `/deliver on`; WebChat replies route deterministically back without inheriting `lastChannel`). Local-first identity (names/avatars/themes/text-size) is **browser-local, not server-synced**; scripted equivalent is `ui.assistant.avatar`. PWA push: VAPID keys auto-generate (`push/vapid-keys.json`); post-update "Protocol mismatch" = stale service worker (reopen via `openclaw dashboard` + hard refresh).

**The CLI** (`openclaw`, a thin RPC client sharing `--url`/`--token`/`--password`/`--timeout`/`--json`/`--plain`; **`--url` explicitly disables config/env credential fallback** — a universal trap). Setup ladder: `setup`/`onboard` → `--baseline` → `configure` → `channels add`. Onboarding QuickStart defaults: loopback :18789, **token auth even on loopback**, `tools.profile:"coding"`, `session.dmScope:"per-channel-peer"`, Tailscale off, DM allowlist; re-running never wipes unless `--reset` (uses trash, never `rm`); non-interactive needs explicit `--non-interactive`; `BOOTSTRAP.md` self-deletes after first run; **bootstrapping always runs on the gateway host**. Global flags `--dev` (`~/.openclaw-dev`, shifted ports), `--profile`, `--container`. Command groups: `config`, `doctor`, `backup` (state dir + config + external `credentials/` + workspaces; skips volatile transcripts/logs/queues, reports `skippedVolatileCount`), `security`, `secrets`, `channels`, `agents`, `acp`, `mcp`, `tasks`/`cron`/`hooks`/`webhooks`, `nodes`/`devices`, `approvals`/`exec-policy`, `browser`, `models`, `sandbox`, `commitments`, `memory`. **`openclaw agent`** runs one turn via Gateway (or `--local` embedded; Gateway mode falls back to embedded on failure — `meta.transport:"embedded"`, `meta.fallbackReason:"gateway_timeout"`); `deliveryStatus`: `sent`/`suppressed`/`partial_failed`/`failed`; recommend external backstop `timeout -k 60 600 openclaw agent …`.

**Slash commands** split three ways: **commands** (standalone `/status`,`/config`,`/mcp`,`/plugins`,`/debug` — owner-only writes disabled by default, `commands.ownerAllowFrom`), **directives** (`/think`,`/fast`,`/exec`,`/model`,`/elevated`,`/queue` — stripped before the model), **inline** (`/help`,`/status`,`/verbose`,`/trace`). `!`/`/bash` needs both `tools.elevated` and `commands.bash`. `/steer` injects into an active run; `/btw` runs an ephemeral side-question (`chat.side_result`, never persisted). `/goal` manages one durable objective per session. `/context list|detail|map|json`, `/usage off|tokens|full|cost|reset`. **Health-signal gotcha:** `sessions`/`sessions.list` reflect stored rows, *not* live provider state — use `channels status --probe`.

**Observability:** JSONL logs (`logging.level` = file, `consoleLevel` = console; `--verbose` affects **console only**; `OPENCLAW_LOG_LEVEL` beats config). **Redaction is a safety boundary:** `redactSensitive:"tools"` default; tool-call events / `sessions_history` / diagnostics exports / exec-approval displays / WS logs stay redacted **regardless of `redactSensitive:"off"`**; `redactPatterns` can only add. Diagnostics: `diagnostics.flags` / `OPENCLAW_DIAGNOSTICS` (targeted, wildcards, timeline JSONL); default-on stability recorder; `gateway diagnostics export` (redacted zip); stuck-session states `long_running → stalled → stuck` (only `stuck` force-releases a lane; `diagnostics.stuckSessionWarnMs`/`AbortMs`). **OpenTelemetry** (`diagnostics-otel`, OTLP/HTTP, traces+metrics on/logs off, anti-spoof `traceparent`) + **Prometheus** (`diagnostics-prometheus`, `GET /api/diagnostics/prometheus` under operator auth — never unauthenticated, 2048-series cap). Channel health monitor: `channelHealthCheckMinutes` 5, `channelStaleEventThresholdMinutes` 30, `channelMaxRestartsPerHour` 10.

**The universal triage ladder** (recurs verbatim): `openclaw status → status --all → gateway status → gateway probe → doctor → channels status --probe → logs --follow → health --json`. Log signatures map to causes: `refusing to bind gateway … without auth`, `EADDRINUSE`/`GatewayLockError`, `pairing request`, `drop guild message (mention required)`, `AUTH_TOKEN_MISMATCH`, `SYSTEM_RUN_DENIED`, `NODE_BACKGROUND_UNAVAILABLE`, `heartbeat skipped reason=…`.

**Transcript hygiene** exists purely to keep provider APIs happy: provider-specific fixes applied **in-memory** before building context (a separate pass repairs stored JSONL atomically). Global rules: runtime/system context kept out of the transcript; images downscaled to `imageMaxDimensionPx` (1200); malformed tool calls dropped; incomplete reasoning-only turns omitted from replay. Per-provider matrix handles OpenAI/Codex (`call_id`/`fc_*` pairing), Google (strict ids, alternation), Anthropic/MiniMax/Bedrock (**pre-compaction thinking-signature stripping** — signatures are cryptographically bound to the conversation prefix), Mistral (strict9 ids).

---

## 19. Testing & dev

`pnpm` for source checkouts. Routine: `test:changed` → `test <path>` → `test`. **Local PR gate:** `check:changed` → `check` → `check:test-types` → `build` → `test` → `check:docs`. Coverage thresholds 70% lines/functions/statements, 55% branches. Extensive Docker E2E harness, upgrade-survivor tests, live-provider tests (`OPENCLAW_LIVE_TEST=1` / `LIVE=1`, real providers, not CI-stable, two-layer model matrix + CLI backends + ACP + Codex + media). A **Convex credential broker** shares channel creds across CI. **Mantis** = live-transport *visual* verification (before/after evidence on real Discord/Slack → PR-comment artifacts). QA-only surfaces (`qa-channel`, `qa-lab`) are source-checkout-only. Formal models reproduced via `make <target>` (Java 11+). Repo guards: `check:database-first-legacy-stores`, config-docs baseline hash, SDK-export lint. Known bug: **Node 25 + tsx crashes at startup** (`__name is not a function`, esbuild `keepNames`) — dev scripts use Bun. `release:prep`/`release:check` align plugin versions + config schema + SDK exports + config-docs; dist-tag mutation lives in an OIDC-isolated `openclaw/releases` repo.

---

## 20. What you only see with the whole map in view

1. **One config file, one state root, one daemon.** The entire platform is `~/.openclaw/openclaw.json` + `~/.openclaw/` + the Gateway on `:18789`. The config is deliberately file-backed while *everything else* moves to SQLite — that split is load-bearing (it's why `openclaw.json` is hand-editable and why `sqlite-transcript://` is banned even as a handle).

2. **The override cascade and "narrow-only" filtering are the universal grammar.** Defaults → per-agent → per-channel → per-session → inline, and every allowlist step can only *remove* capability. It's why "add it back later" fails unless you add at the earliest stage (`tools.alsoAllow`, not `subagents.tools.allow`).

3. **Security is a stack, not a switch, and every gate fails closed.** Tool policy, sandbox, elevated, exec approvals, and mode are independent gates composed by "stricter-of"; "YOLO" requires deliberately opening two of them explicitly. The same three-gate pattern recurs in exec, nodes, and approvals — non-collapsible by design so a permissive layer can't silently open another.

4. **"Auth" means at least five unrelated things,** and shared-secret HTTP silently escalates to full operator. HTTP surfaces are categorically more dangerous than WS/channel surfaces — the entire "keep on loopback" refrain follows from this one fact.

5. **Three warnings are the same mistake in different clothes:** *exec ≠ read-only*, *allowlist ≠ authorization boundary*, *host env ≠ sandbox env* — all conflate a discovery/UI filter with an execution boundary. And two footgun classes to check on any new channel: does `groupPolicy:"allowlist"` also need a `groups` registry? and are your allowlist keys stable IDs (with `dangerouslyAllowNameMatching` off)?

6. **Enforcement lives in mechanism, never in prose.** SOUL/AGENTS/system-prompt guardrails are advisory; the real controls are tool policy, exec approvals, sandboxing, allowlists, SecretRef scoping — checked by the three auditors (`security audit`, `doctor`, `policy`).

7. **Trust is a property of code identity + install provenance, verified fresh, never cached.** The same three-tier trust model appears in plugin execution, auth modes, approval gates, macOS TeamID, and provider-catalog authority. Control-plane freshness is a first principle — it's why manifests are separable from code and why cold `list` deliberately can't answer "is it running."

8. **Capability contracts absorb sprawl.** ~60 providers, ~45 channels, 16 video providers, 15 search providers all resolve through *declared capabilities* and fallback chains that skip gracefully — which is why an unfamiliar provider's doc is predictable (one point in {transport} × {native vs proxy} × {thinking} × {regional} × {bundled}) and most gotchas reduce to "set the provider/mode explicitly — don't rely on the default."

9. **Async + idempotency + the tool/plugin credential split are house styles.** Background media, `chat.send`, media re-delivery all use submit-ack-wake-with-idempotent-fallback; tools declare behavior under `tools.*` while providers declare credentials under `plugins.entries.*.config.*`.

10. **The system prefers a loud failure to a silent wrong-thing, and `doctor --fix` is the connective tissue.** Session-selected models fail visibly, empty tool sets abort, approvals bind exact argv/cwd, unresolved secrets stop startup, health separates liveness from readiness, and the whole surface is visibly mid-migration with dated removals — with doctor as the single, explicitly-decreed owner of legacy repair.

---

*For any specific value — a provider's exact catalog, the full SecretRef allowlist, the SQLite table inventory, a channel's ingress budget — descend into the corresponding source doc (`docs/**`, many with `summary`/`read_when` frontmatter) or run `openclaw config schema` / `openclaw doctor` / `security audit` against your own install. This is the map, not the territory.*
