---
mem_id: f3cc173b-36ee-4356-bab6-99283f17ac4f
title: "OPENCLAW PROJECT \u2014 MASTER"
created_at: 2026-06-13T02:46:10.897Z
updated_at: 2026-07-01T23:59:00.000Z
source: mem:OPENCLAW PROJECT
---

# OPENCLAW PROJECT — MASTER

## PURPOSE

This is the authoritative entry point and coordination document for the OpenClaw project.

All OpenClaw project knowledge should ultimately be organized through this note and the subject notes referenced by it.

The objective is to create a project memory system that can be used consistently by:

- Brian
- Klaw (this agent)
- ChatGPT
- Claude
- Future agents and subagents

while preventing cross-contamination with unrelated notes and projects.

***

## AGENT IDENTITY

- **Agent Name:** Klaw
- **User Name:** Brian
- **Confirmed:** 2026-06-15

***

## MEMORY GOVERNANCE RULES

### Scope

This collection is exclusively for the OpenClaw project.

Included:

- Architecture
- Networking
- Configuration
- Performance investigations
- Documentation strategy
- Memory integration
- Security hardening
- Agent development
- Model/profile orchestration
- Checkpoints
- Roadmaps
- Findings and lessons learned

Excluded:

- Personal notes
- Financial planning
- Travel projects
- Trading projects not directly related to OpenClaw development
- General workstation planning

### Note Naming Convention

Every note in this collection should begin with: `OPENCLAW PROJECT —`

### Master Note First Rule

When working on the OpenClaw project:

1. Read this Master Note first.
2. Identify relevant subject notes.
3. Read subject notes as needed.
4. Update both the subject note and this Master Note when major changes occur.

This rule applies to all agents working the project, including Claude Code on the VM.

### New Subject Rule

If a new major project area emerges:

1. Create a dedicated subject note.
2. Add it to this Master Note.
3. Add a summary section here.
4. Keep summaries synchronized.

### Summary Maintenance Rule

Every subject note should begin with: Current Status, Last Updated, Key Decisions, Summary.

The Master Note should contain a current summary of every active subject note.

### Terminology

"Checkpoint" refers specifically to Hyper-V VM snapshots. Timeline entries in the Checkpoints & Change Log note are "milestone entries," not checkpoints.

Also note: OpenClaw "nodes" = peripheral companion devices (phone/laptop camera/canvas/screen), NOT compute hosts. The 5090 box (amethyst) is a separate GATEWAY/host, not a "node" in OpenClaw's sense. Don't run `openclaw nodes` expecting cluster management. (Detail in Model Strategy & Orchestration.)

### Tooling & Continuity

- Claude Code (on klaw-machine) is the execution/configuration surface for VM-bound work, replacing the chat-and-paste loop.
- claude.ai chat history is NOT accessible to Claude Code. The cross-tool continuity layer is this local notes directory (`~/.openclaw/project-notes/`, git-tracked) — migrated off Mem 2026-07-01. Durable project state must live here so any agent can resume from it.
- Claude Code auth: interactive use relies on plain OAuth login (persists across SSH); the `CLAUDE_CODE_OAUTH_TOKEN` in `~/.claude_env` is for non-interactive automation only and must NOT be loaded in interactive shells (it breaks interactive login).
- Agents must be pointed at the local docs mirror to use it: Klaw via AGENTS.md, Claude Code via a CLAUDE.md in `~/.openclaw`. Neither consults it automatically.
- Version-control layers: git = durable history of script/config; Claude Code `/rewind` = 30-day undo of its own file-tool edits (not bash output); Hyper-V snapshots = whole-VM rollback.

***

## CURRENT PROJECT STATUS

Last Updated: 2026-07-01

Project Phase: Infrastructure operational; knowledge structure complete; Claude Code is the dev/execution surface; documentation mirror **fully closed out** (git + nightly cron confirmed + agent pointers, cron & caching verified 2026-06-21); remote access established (Tailscale + SSH). **Project memory migrated OFF Mem to local git-tracked markdown at `~/.openclaw/project-notes/` (2026-07-01); agents severed from Mem.** **In flight: the whole-corpus docs digest** (chunked across usage windows; reduce runs once all map batches are cached). Then: Fable 5 whole-system eval (promo through Jul 7); security hardening continues (OS/host + OpenClaw-application layers). (Live priorities + roadmap detail live in the Roadmap & Future Development note.)

Current Working Components:

- Ollama on RTX 3090 host — **primary model qwen3.6:27b (dense), flash attn + q8\_0 KV cache, pinned 110K context, VRAM-verified \~21GB/24GB** (mistral-small3.2:24b retained as fallback)
- OpenClaw 2026.6.5 in Hyper-V Ubuntu VM (klaw-machine); Gateway on systemd, port 18789, loopback-only
- Dedicated OllamaSwitch networking (VM → 10.10.10.1:11434)
- Remote access: Tailscale mesh + SSH (VM passwordless via Tailscale SSH; Windows hosts via OpenSSH)
- Telegram integration (operational); web search (operational)
- `tools.profile=full` (Mem severed 2026-07-01: `bundle-mcp` removed from `tools.allow`, `mcp.servers.mem` removed from `openclaw.json`)
- Project notes local at `~/.openclaw/project-notes/` (13 notes, git-tracked, pushed to `klaw-konfig`); all subject notes created and populated
- Claude Code installed and authenticated on klaw-machine (v2.1.177; interactive OAuth persists over SSH)
- Documentation mirror operational and auto-refreshing nightly (\~689 pages at `~/.openclaw/docs/`, ETag-based incremental; cron + caching verified). Under git on a private GitHub remote (`millsio/klaw-konfig`).

In flight / not yet done:

- Docs digest: initial whole-corpus build in progress (map batches chunked across usage windows on cron; reduce pending).
- Security hardening (Windows-host SSH keys → disable password auth, UFW, OpenClaw-layer hardening — see Roadmap).
- Agent read access: filesystem `read` is globally allowed (`tools.allow: ["group:web", "read"]`, granted with the 7/1 migration so agents can self-serve the local notes). Verified 2026-07-01 via gateway log: `tools.allow` is a strict whitelist — effective agent surface is read + web only (no exec/write; this also explains the old "~34 tools stripped" mystery). **Secrets hardening (2026-07-01, same session): `openclaw.json` now holds ZERO plaintext secrets — gateway auth token and the default Telegram botToken migrated to env SecretRefs (`GATEWAY_AUTH_TOKEN`, `TELEGRAM_BOT_TOKEN` in `.env`); stale `MEM_API_KEY` removed. REMAINING GAP: `.env` itself is still readable by the `read` tool — the durable fix is the sandbox/scoped-fs work (Priority-1); until then exposure is bounded by no-exec/no-write, Brian-only DMs, and the council's redaction guard.**

***

## SUBJECT NOTE INDEX

All subject notes are active and populated as of 2026-06-13, with updates through 2026-06-21.

### OPENCLAW PROJECT — Architecture

Current verified architecture: Ollama on Windows 11 Pro host (primary model qwen3.6:27b dense; mistral fallback), OpenClaw in Hyper-V Ubuntu VM (klaw-machine), dedicated OllamaSwitch network. RTX 3090 (pacifico) is the current compute node. RTX 5090 (amethyst) is a future second host — near-term an Ollama endpoint only (Gemma). Tool-execution isolation handled nearer-term by OpenClaw's built-in sandbox (Docker/SSH/OpenShell) on top of the VM; **Firecracker demoted to someday/maybe** (OpenClaw has no Firecracker backend). Intelligent model/profile routing remains a future milestone.

### OPENCLAW PROJECT — Networking & Infrastructure

Two-interface VM networking (eth0 internet, eth1 OllamaSwitch static). Remote access via Tailscale mesh + SSH (VM keyless via Tailscale SSH; Windows hosts via OpenSSH, key-hardening pending). OpenClaw Gateway on systemd (port 18789, loopback only). Telegram operational. VM allocation static mem / fixed disk. 5090 second node to be seeded from a klaw-machine golden VHDX. Security hardening in progress.

### OPENCLAW PROJECT — Configuration & Models

OpenClaw 2026.6.5. **Primary model: qwen3.6:27b (dense)** — flash attention + q8\_0 KV cache (global Ollama host env vars), pinned 110K context, VRAM-verified (\~21GB/24GB, \~3.5GB headroom). mistral-small3.2:24b retained as fallback. Installed inventory includes qwen3.6:27b, qwen3-coder:30b, deepseek-coder:33b, qwq:32b, gemma4:31b + gemma4:26b (installed; gemma4:26b is MoE/quant-sensitive), mistral-small3.2:24b, qwen2.5:14b, embeddinggemma. `tools.profile=full` with `bundle-mcp` exposing Mem tools. Named sessions in use. Gateway loopback :18789, auth token enabled, Tailscale exposure disabled. Mem MCP integrated and operational.

### OPENCLAW PROJECT — Performance Investigations

Latency investigation June 11, 2026. Root cause: tools.profile=coding injects \~11k token baseline vs \~6.2k for minimal. Secondary: legacy main session (5.0 MB trajectory). Resolution: lean profile + named sessions + gateway restart after profile changes. System stable.

### OPENCLAW PROJECT — Documentation & Knowledge Management

Hybrid strategy: openclaw docs command (fast path) + English-only mirror of docs.openclaw\.ai (deep research). Mirror is OPERATIONAL and FULLY CLOSED OUT: `mirror_openclaw_docs.py` in `~/.openclaw/scripts/`, \~689 pages mirrored to `~/.openclaw/docs/` with INDEX.md, ETag/If-None-Match caching verified, nightly cron at 3:15 AM confirmed firing unattended, both agents pointed at it (AGENTS.md / CLAUDE.md), under git. Next workstream: the whole-corpus Documentation Digest (weekly, Claude Code + Opus) plus a digest analysis artifact. Two-layer memory model recorded (native OpenClaw operational memory vs Mem curated KB). Memory-scope restriction to the collection still required but not implemented at OpenClaw level (an MCP-filtering task). Governance rules documented here.

### OPENCLAW PROJECT — Roadmap & Future Development

Completed: VM setup, Hyper-V migration, performance resolution, Telegram + web search, knowledge management, Mem MCP integration, Claude Code install + auth, documentation mirror (closed out + verified), qwen migration, remote access (Tailscale + SSH). Current priorities, in order: (1) security hardening (ACTIVE — OS/host + OpenClaw-application layers); (2) link Claude Code to Mem MCP; (3) controlled system actions framework; (4) secrets hygiene. Future: Documentation Digest, Debate Council, Alpaca integration, autonomous research, multi-agent architecture, intelligent model/profile routing, 5090 second node + cross-node co-orchestration. Firecracker demoted to someday/maybe.

### OPENCLAW PROJECT — Checkpoints & Change Log

Two parts: a VM Snapshot Registry (canonical ledger of Hyper-V snapshots — "Solved Openclaw Performance Issue", "Mem Integrated", "Claude Code installed", "Docs Mirror Operational - Basic", "Mid Git Setup") and a Milestone History (narrative timeline). The "Docs Mirror Operational - Basic" snapshot is PRE-git/PRE-cron; a fresh snapshot should capture the post-git/post-cron/post-hardening state.

### OPENCLAW PROJECT — Model Strategy & Orchestration

Documents the model-selection decision (qwen3.6:27b dense, with the KV-cache/VRAM evidence), the per-model configuration recipe, the planned qwen-workhorse / Gemma-judge role split on the future 5090, the cross-host resource-sharing model (GPU-as-service vs CPU-as-relocated-workload), the Debate Council (adversarial qwen-vs-Gemma review with an Opus judge), the longer-term multi-model orchestration design (tiering, confidence-gated escalation to frontier APIs, AI council), and the multi-node (3090 + 5090) co-orchestration design (VHDX seeding, cross-host `Save-VM`/`Resume-VM` resource yielding, chain-of-command requirement).

***

## CURRENT PRIORITIES

1. **Finish the initial docs digest** (map batches on cron across usage windows; then the full reduce).
2. **Fable 5 whole-system eval** (sweep-first, then focused passes; promo pricing through Jul 7).
3. **Security hardening (ACTIVE).** Windows-host SSH keys → disable password auth; UFW; OpenClaw-layer hardening (`openclaw security audit`, sandbox mode, tool policy, approval/elevated gates, plugin allowlists); lock down amethyst's Ollama endpoint when it comes online; service startup persistence; owner account + execution-approval policies.
4. Agent read access to project notes: grant local agents filesystem read for discovery once secrets are systematically locked down (replaces the retired Mem memory-scope-restriction task).
5. Controlled system actions framework (file ops, script execution, approval gating).
6. Secrets hygiene (Claude Code automation token stays chmod-600, git-ignored; audit whether the now-unused `MEM_API_KEY` in `.env` can be removed).

(Full task breakdown, near-term roadmap, and long-term vision live in the Roadmap & Future Development note.)

***

## RECENT UPDATES

- 2026-07-01: **Mem→local migration complete.** The OPENCLAW PROJECT collection now lives as local git-tracked markdown at `~/.openclaw/project-notes/` (13 notes + 2 PII-scrubbed AI-trading notes), pushed to the private `klaw-konfig` remote. Agents fully severed from Mem (`bundle-mcp` out of `tools.allow`, `mcp.servers.mem` block removed; gateway restarted); `council_pilot.py` repointed to a local discussion log; `mem_backup.py` + weekly cron + `mem-backups/` retired. The whole-corpus docs digest (`docs_digest.py`; map = Sonnet 5, reduce = Opus 4.8) is being built chunked across usage windows via `digest_chunk.sh` + cron. Checkpoint "klaw-machine - (7/1/2026 - 5:13:08 PM) - mid openclaw docs digest - mem to local" captures this state. This MASTER note refreshed to post-migration reality (continuity layer, components, priorities).
- 2026-06-30: Security-hardening + autonomy-pilot session (Claude Code). Rotated the Mem API key — the prior key was exposed during a council smoke when a local model read `openclaw.json` and printed a (as it turned out, CONFABULATED) token; the real key likely reached Anthropic via the `claude -p` weigh-in — and migrated it to a SecretRef (`${MEM_API_KEY}` in `.env`; plaintext purged from config and all backups). Disabled `controlUi.allowInsecureAuth`. Built the multi-agent "council" pilot (`scripts/council_pilot.py`): qwen + gemma review the collection via their own read-only Mem tools and collaborate with periodic tool-less `claude -p` weigh-ins; filesystem `read` kept OFF; runtime secret-scan guard. Verdict from two smokes: collaboration works, but keep it ATTENDED (the models silently self-inflicted failures twice — continuity loss, then a confabulated-secret print). Gateway-token SecretRef deferred (loopback-only, low value). Checkpoint "klaw-machine - (6/30/2026 - 1:25:53 AM) - working on autonomous loops" captures this state. Detail in the Pilot + Checkpoints notes.
- 2026-06-28: Machine naming unified to `klaw-machine` across all surfaces — Linux hostname (`klaw-Virtual-Machine` -> `klaw-machine`; `/etc/hosts` updated, sudo resolves cleanly), the Hyper-V VM display name (`KlawMachine` -> `klaw-machine`), and Tailscale (already `klaw-machine`, undisturbed). Generic prose references in the Networking & Infrastructure and Checkpoints & Change Log notes were updated to match, and the host-restart PowerShell runbook now uses `-Name "klaw-machine"`. Hyper-V checkpoints were also renamed (manually, by Brian) from "KlawMachine - (...)" to "klaw-machine - (...)", and the Checkpoints & Change Log note's snapshot-name references were updated to match. The only "old name" mentions intentionally preserved are the node's original Tailscale auto-name `klaw-virtual-machine` (the "(Was klaw-virtual-machine.)" table notes and the June 16 remote-access entry), kept as genuine history. Done via Claude Code.
- 2026-06-28: Major "Arena" session via Claude Code — built the two-local-model debate/compete/collaborate harness (`scripts/debate.py`), an Opus judge (`scripts/judge.py`), a deterministic `/hotdog` Telegram trigger (message:received hook + `scripts/hotdog.sh`; verbs stop/drop/roll), per-turn Telegram delivery + a watcher service, a weekly local Mem backup (`scripts/mem_backup.py`), and a reusable Mem editor (`scripts/mem_edit.py`). Hardened Kettle (exec + Mem-write denied) and tightened the debate `[GROUNDED]` tag to require real retrieval. Several issues remain to triage next session (specifics TBD from Brian); full detail + open items in the Roadmap note. _(2026-07-01: this entry and the naming entry above had been spliced together by an edit error; reconstructed from the Roadmap note's clean copies.)_
- 2026-06-27: Claude Code session — stood up the second Telegram bot "Copper Kettle" (`gemma-telegram` → gemma4:31b via amethyst; @CopperKettleBot); added an anti-confabulation honesty directive to `main`/Kettle `SOUL.md`; implemented the Mem write-permission gate across agents (Fix A — reads scoped to this collection, no writes without approval; token-level/MCP-proxy scoping deferred to Roadmap); denied exec/runtime tools for Kettle; cleaned the contaminated Debater-B workspace; and added a local Mem backup (`scripts/mem_backup.py`, weekly, keep-last-10). Detail in Model Strategy, Documentation, Roadmap, and Checkpoints notes.
- 2026-06-21: Reconciled stale model facts in this MASTER note — primary model corrected from mistral-small3.2:24b to **qwen3.6:27b** (flash attn + q8\_0, 110K ctx; mistral now fallback), `tools.profile` corrected minimal → full, and the "Gemma not in inventory" line corrected (gemma4 models are installed). Refreshed Current Project Status, the subject-note summaries, and Current Priorities to reflect: docs-mirror track fully closed (cron + caching verified), remote access established, and security hardening now the active task. (Detailed model rationale: Model Strategy & Orchestration note; live priorities: Roadmap note.)
- 2026-06-21 (cont.): Synced the Architecture and Model Strategy subject-summaries to current state — **Firecracker demoted to someday/maybe** (built-in sandbox is the nearer-term isolation path); added the Gemma role-split, cross-host resource-sharing, and Debate Council to the Model Strategy summary; noted the OpenClaw "nodes" = companion-devices terminology trap under Terminology.
- 2026-06-15: Agent identity confirmed as **Klaw**. Master note updated to reflect this.
- 2026-06-13: Mem MCP server integrated and operational. Configuration & Models note updated.
- 2026-06-13: Documentation mirror deployed and verified (684 pages). Checkpoint taken.
- 2026-06-13: All subject notes consolidated; MASTER note created as authoritative entry point.

***

## MAINTENANCE INSTRUCTION

Future OpenClaw project notes should be consolidated into the structured subject-note system whenever practical.

Avoid creating isolated standalone project notes when the information belongs in an existing subject area.

Legacy source notes have been marked \[LEGACY NOTE - CONSOLIDATED] and retained.
