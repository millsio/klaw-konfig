---
mem_id: f80de520-fdf0-4932-9b13-4fc3ab2016f2
title: "OPENCLAW PROJECT \u2014 Session Handoff (2026-06-27 PM): Copper Kettle two-bot build + agent-hygiene findings + CC migration"
created_at: 2026-06-27T23:27:18.575Z
updated_at: 2026-06-27T23:27:19.274Z
source: mem:OPENCLAW PROJECT
---

# OPENCLAW PROJECT — Session Handoff (2026-06-27 PM): Copper Kettle two-bot build + agent-hygiene findings + CC migration

## Purpose of this note

Single "continue here" capture for migrating the active working session from claude.ai (Opus) into **Claude Code (CC) on KlawMachine**. CC is already Mem-MCP integrated. Read this note + the canonical subject notes (IDs at bottom) to resume with full context. Authored 2026-06-27 \~19:20 ET.

## VM snapshot taken

Hyper-V checkpoint: **"KlawMachine - (6/27/2026 - 7:18:40 PM) - Copper Kettle up and other stuff."** Captures state AFTER the Copper Kettle two-bot build below. (TODO: also log this in the canonical Checkpoints & Change Log VM Snapshot Registry — not yet done.)

***

## WHAT WAS BUILT THIS SESSION — Second Telegram bot "Copper Kettle" (gemma via amethyst). COMPLETE + VERIFIED.

Goal achieved: a second Telegram bot that runs gemma4:31b on amethyst, sidestepping blocker B (in-chat `/model` switching does not propagate on the Telegram path). Uses per-agent pinning + a dedicated channel account, exactly as the prior handoff recommended.

As-built:

- **Bot:** "Copper Kettle", username **@CopperKettleBot** (created via BotFather).
- **Telegram account:** `channels.telegram.accounts.gemma`. The pre-existing bot (@KlawJBot) is the top-level/`default` account -> agent `main` -> qwen; UNCHANGED.
- **Agent:** `gemma-telegram`, pinned to `amethyst-ollama/gemma4:31b`, workspace `/home/klaw/.openclaw/workspace-gemma-telegram`, agentDir `/home/klaw/.openclaw/agents/gemma-telegram/agent`. Created with `openclaw agents add gemma-telegram --model amethyst-ollama/gemma4:31b --workspace ... --bind telegram:gemma --non-interactive --json` (the `--bind` wrote the account->agent binding).
- **Token:** SecretRef, env source. `channels.telegram.accounts.gemma.botToken = { source: "env", provider: "default", id: "TELEGRAM_GEMMA_BOT_TOKEN" }`; the value lives in `~/.openclaw/.env` (the global runtime dotenv the gateway reads at process start, even under systemd).
- **Access:** `dmPolicy: "allowlist"`, `allowFrom: ["telegram:8852367597"]` (Brian's TG user id, pulled from `commands.ownerAllowFrom`). `channels.telegram.defaultAccount: "default"` set explicitly (docs require an explicit default once >=2 accounts exist).
- **Apply/restart:** config via `openclaw config patch --file ~/telegram-gemma.patch.json5` (dry-run validated 4 updates first). Gateway is the **user systemd unit **`openclaw-gateway.service`; a FULL restart (`systemctl --user restart openclaw-gateway.service`) was required so the new `.env` var entered the process env (a hot config reload would NOT re-read `.env`).

Verification (authoritative, not acoustic):

- Session store `openclaw sessions --agent gemma-telegram` -> session ran on `gemma4:31b`, 80K ctx.
- amethyst `/api/ps` -> `gemma4:31b` resident, size\_vram 20.3GB, context\_length 80000, keep\_alive forever.
- Acoustic signature noted for future quick checks: 5090/gemma = a **pulsing, powerful hum**; 3090/qwen = a **quick tiny chirp**. (Heuristic only; session store remains authoritative.)

Gotchas confirmed this session (durable learnings):

- **Per-account Telegram token key is **`botToken` (not the generic `token` that Discord/ClickClack use). Confirmed via `openclaw channels status --probe` showing `token:config ... works`.
- **On Telegram, an inline account **`agentId`** is TOPIC-only**; account->agent routing must go through a `bindings` entry (routing rule 6, "Account match"). The handoff's "account agentId routes it" was imprecise; the binding is the mechanism.
- An initial 401 from `getMe` was a **bad token value** (Brian fixed it), NOT a config/schema problem — the SecretRef resolved and transmitted correctly. OpenClaw side was sound throughout.

***

## NEW FINDINGS THIS SESSION

### 1. OpenClaw agent bootstrap ritual is real (not confabulation)

A brand-new empty workspace causes OpenClaw to seed `BOOTSTRAP.md` — a one-time first-run identity ritual, auto-injected alongside the other bootstrap basenames (`AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `MEMORY.md`, `TOOLS.md`). It is kept in Project Context until the ritual completes, then self-deletes; a state-dir attestation marker prevents silent re-seeding. Copper Kettle genuinely woke into this ritual ("who am I / who are you / write it down") — its "birth certificate" self-description was grounded, verified by files on disk + an observed Mem tool call. Lesson reaffirmed: trust the substrate (disk + tool logs), not the model's eloquence.

### 2. Mem write pollution from the ritual — found and cleaned

Kettle's ritual wrote workspace `IDENTITY.md` (27 lines) + `USER.md` (21) AND created two **Mem** notes: "Identity - Copper Kettle" and "User - Brian". Both were **uncollected (Mem root)**, not in OPENCLAW PROJECT — so the curated KB was not polluted, but it demonstrates the scope gap is about WRITES, not just searches. **Both notes have been trashed** (reversible). `BOOTSTRAP.md` (59 lines) is still present in the workspace -> ritual not marked complete/self-deleted.

### 3. Debater-B (gemma-amethyst) is contaminated — MUST fix before council pilot

`workspace-gemma-amethyst` has IDENTICAL bootstrap files: `BOOTSTRAP.md` 59, `IDENTITY.md` 27, `USER.md` 21, `SOUL.md` 42, `MEMORY.md` absent. So debater-B ran the same ritual and now carries a persona. Worse, `BOOTSTRAP.md` is still present -> on its next turn it may re-engage the identity ritual instead of debating. It wrote NOTHING to Mem (clean there). Required fix before the pilot: remove `BOOTSTRAP.md` from the debater workspace and replace `SOUL.md`/`IDENTITY.md` with the neutral "rigorous peer reviewer" stance from the council design (note 649121bc).

### 4. Tool-use discipline problems on the local model (gemma4)

- Fires `web_search` with a degenerate/empty query ("none") compulsively.
- Emits its chosen emoji teapot (U+1FAD6) as byte-escaped `<0xF0><0x9F><0xAB><0x96>` (tokenizer byte-fallback / rendering artifact).
- Brief language leak (Portuguese "uma lousa branca mentalmente" = "a mental whiteboard") then code-switched back.
- Narrates reasoning + tool use ("Reefing", "think medium") into the visible channel.
- **Tried to EXECUTE a pasted shell snippet** as if it were a command (Brian accidentally pasted a bash one-liner): parsed the loop, ran a web search, attempted a Mem note. Harmless but a live tool-safety / prompt-injection illustration (text in -> tool actions out).

### 5. Interrupt + Claude Code

- `/stop` is the native command to abort an in-progress agent run/tool from the channel (confirmed working in Telegram: "Agent was aborted"). Proactive fix is a tool-approval policy/allowlist.
- **Claude Code on KlawMachine is already Mem-MCP integrated** (confirmed: CC reported our recent work). Same Opus; interactive CC = subscription pool (headless `claude -p` draws the separate Agent-SDK credit). This is the migration target — CC runs commands/reads files directly, removing the copy-paste relay.

***

## ACTIVE WORK / TODO (priority order) — what we're doing now

1. **MIGRATE working sessions to Claude Code** (in progress; this note is the handoff vehicle).

2. **Anti-confabulation honesty directive** — add to `SOUL.md` for BOTH `main` (Klaw) and `gemma-telegram` (Kettle), and bake into a template for future agents. NOTE on placement: bootstrap files are PER-WORKSPACE; there is no auto-global file all agents inherit (the only global prompt hook is GPT-5-specific). So it must go in each agent's workspace. **First step before editing: inspect each agent's current&#x20;**`SOUL.md`**&#x20;so we don't clobber.** Approved draft text:

   >

  - Distinguish what you know from what you're guessing. If you're not sure a specific fact, name, number, date, quote, or past-conversation detail is correct, say so plainly instead of presenting it confidently.
  - Never fabricate specifics to sound complete — no invented quotes, stats, citations, file contents, or memories. If you don't have it, say you don't have it.
  - For factual/numeric claims you're unsure of, either look it up (web/docs/memory) and cite it, or state you couldn't verify it. Don't run empty or nonsensical searches.
  - Under-claiming and offering to verify always beats over-claiming. "I don't know" is a valued answer. Honest caveat: a prompt directive REDUCES but will not ELIMINATE confabulation on a Q4 local model (self-assessed confidence is poorly calibrated). The durable lever is grounding (force web/docs/Mem lookup + citation for factual/numeric claims), not instruction alone.

3. **Debater-B (gemma-amethyst) cleanup** before council pilot — remove `BOOTSTRAP.md`, replace `SOUL.md`/`IDENTITY.md` with neutral peer-critic stance.
4. **Mem scope lockdown — two layers:**

  - \*\*Fix A (correct-write standing order):\*\* instruct agents that any Mem write goes to the OPENCLAW PROJECT collection (82bba4f9-...) using the \`OPENCLAW PROJECT —\` naming convention — OR, for casual agents like Kettle, persist identity to workspace files only and not Mem. Diagnose whether the ritual's Mem write came from a template instruction vs autonomous tool use (determines template-edit vs tool-policy).
  - \*\*Fix B (token-level scoping) — OPEN, defense-in-depth Brian wants:\*\* lock the Mem API token OpenClaw uses to the OPENCLAW PROJECT collection so it physically cannot read/write elsewhere. \*\*Unverified:\*\* whether Mem.ai issues collection-scoped API keys. Decision tree: (a) if yes -> mint a scoped key, swap it in; (b) if no -> thin MCP proxy that injects the collection filter, or a separate Mem account dedicated to OpenClaw. Tension to resolve: a single-collection token would FORCE all agent writes (incl. Kettle's identity) into the project collection, which may be undesirable — reconcile with Fix A. Motivation is concrete: the same token currently reaches Brian's personal/financial/tax notes (verified incidentally this session).

5. **Tool-approval policy / allowlist for Copper Kettle** — it's channel-bound and fires web/Mem unprompted (and tried to run a pasted shell snippet). Gate sensitive tools (web, Mem-write, exec) behind approval, or allowlist only what it needs. Ties to the parked `tools.allow` item (a rule strips \~34 tools from `main` each turn — still uncharacterized).
6. **Configure Kettle to use the docs mirror + proper Mem usage** — point its workspace `AGENTS.md` at the local docs mirror (as `main` does) and set its Mem-write behavior per Fix A.
7. **Fold this session's facts into the canonical subject notes** — the two-bot build belongs in Model Strategy & Orchestration (649121bc); agent-bootstrap/Mem-scope findings belong in Documentation & Knowledge Management (c8ed5124). Not yet done.

### Carried-over open items from the prior (AM) handoff — still open

- **Blocker A:** compaction does NOT engage at the context ceiling (hard "context overflow" error instead of trimming). Kettle inherits this (80K ceiling). Gates unattended council runs.
- **Blocker B:** `/reset`/`/new` falls back to the global default model, not the agent pin. (Two-bot architecture sidesteps it for Telegram, but it still affects spawned council sessions.)
- **Docs-mirror 7-night health check** (cron fired 7/7 nights 06-21->06-27, errors=0, page count stable) — still NOT logged to the Documentation note's "Ongoing Monitoring" section.
- **Mem API key -> SecretRef** (resolve the `openclaw mcp doctor` warning).
- Council pilot build (coordinator + qwen debater-A + bounded pilot) after blockers + debater cleanup.

***

## Key references

- Collection (OPENCLAW PROJECT): `82bba4f9-6724-4874-bbcf-1f9ab525b873`
- Model Strategy & Orchestration: `649121bc-abf7-459b-a504-63436f0dc4f3`
- Documentation & Knowledge Management: `c8ed5124-c0c6-4f21-aaf1-b32baaacdeb8`
- MASTER: `f3cc173b-36ee-4356-bab6-99283f17ac4f`
- Checkpoints & Change Log: `0c9da524-00ee-48c8-8285-9c4f1141ea50`
- Brian's Telegram user id: `8852367597`
- Agents: `main` (Klaw/qwen, @KlawJBot, account `default`), `gemma-telegram` (Kettle/gemma via amethyst-ollama, @CopperKettleBot, account `gemma`), `gemma-amethyst` (debater-B, isolated, CLI-driven).
- amethyst Ollama: `http://100.113.225.2:11434`, provider `amethyst-ollama`, gemma4:31b 80K fp16.
