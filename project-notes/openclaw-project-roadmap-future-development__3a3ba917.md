---
mem_id: 3a3ba917-c46a-48c1-86b6-6fe7ff2a72ad
title: "OPENCLAW PROJECT \u2014 Roadmap & Future Development"
created_at: 2026-06-13T04:58:00.636Z
updated_at: 2026-06-28T06:23:44.346Z
source: mem:OPENCLAW PROJECT
---

# OPENCLAW PROJECT — Roadmap & Future Development

## Current Status

Active. **Project memory migrated OFF Mem to local git-tracked markdown at `~/.openclaw/project-notes/` (2026-07-01); agents severed from Mem; Mem tooling retired.** Documentation mirror track FULLY CLOSED (2026-06-21): deployed and verified; under git on a PRIVATE GitHub remote (`millsio/klaw-konfig`) via a repo-scoped deploy key; nightly cron at 3:15 AM CONFIRMED firing unattended; both agents pointed at the mirror. Remote access established 2026-06-17 (Tailscale + SSH; RustDesk for desktops). **In flight: the initial whole-corpus docs digest** (chunked across usage windows via `digest_chunk.sh` + cron; reduce runs once all map batches cache). **Next: Fable 5 whole-system eval (promo through Jul 7), then security hardening continues** (OS/host + OpenClaw-application layers — see priority #5). Forward track: the 5090 second node (VHDX seeding) + multi-node co-orchestration; the Debate Council (blockers A/B gate unattended runs — see Model Strategy).

## Last Updated

2026-07-01

## Key Decisions

- Current focus is project-memory, documentation retrieval, and development workflow.
- Claude Code (on KlawMachine) is the execution and configuration surface for VM-bound work, replacing the chat-and-paste loop. claude.ai chat is retained for cross-project thinking/design only.
- Continuity layer is the local project-notes directory (`~/.openclaw/project-notes/`, git-tracked), NOT chat history — Claude Code cannot read claude.ai conversations, so durable project state must live there. (Was Mem until the 2026-07-01 migration; Mem is retired.)
- Claude Code auth on this VM: interactive login uses plain OAuth (`claude` → option 1 → browser), which persists across SSH sessions on its own. Do NOT load `CLAUDE_CODE_OAUTH_TOKEN` in interactive shells — it interferes with interactive login (known issue). The long-lived token (in `~/.claude_env`, currently commented out of `.bashrc`) is reserved for NON-interactive automation only (cron, `claude -p`).
- Terminal: run Claude Code from the Windows Terminal app, NOT the classic blue PowerShell console — the classic console does not paste into Claude Code's TUI. (ctrl+v also unbound from image-paste in `~/.claude/keybindings.json`.)
- Git: `~/.openclaw` is a repo using a deny-by-default `.gitignore` (all config/secrets/runtime/docs ignored; only authored text tracked). PRIVATE GitHub remote `millsio/klaw-konfig` was added 2026-06-20 via a repo-scoped deploy key (`~/.ssh/openclaw_deploy`) reached through the `github-openclaw` SSH alias; GitHub auth was done by Brian in the browser, never via the agent. Full standing convention in the Documentation & Knowledge Management note (Git Repository Strategy).
- Git sync cadence: prefer scheduled/batched off-hours pushes over real-time pushes. Implemented via `scripts/nightly.sh` (commits + pushes only when a TRACKED file changed, after the 3:15 AM mirror refresh).
- Version control: Claude Code's `/rewind` checkpoints only cover its own file-tool edits (not bash-command output) and expire after 30 days. Use git for durable history; Hyper-V snapshots for whole-VM rollback.
- Intelligent model/profile routing is a separate future workstream — not current focus.
- Security hardening is the highest-priority infrastructure task — now the ACTIVE task as of 2026-06-21 (docs-mirror track closed). It now explicitly spans two layers: OS/host hardening AND OpenClaw-application hardening (`openclaw security audit`, built-in sandbox, tool policy, plugin allowlists, approval gates). The OpenClaw layer was previously absent from this checklist.
- **Firecracker DEMOTED to someday/maybe (2026-06-21).** Tool-execution isolation is handled nearer-term by OpenClaw's built-in sandbox (Docker/SSH/OpenShell) on top of the Hyper-V VM — config, not a build. OpenClaw has no Firecracker backend, and the VM is already a stronger boundary than Docker. Firecracker remains only an optional future exploration. (See Architecture note.)
- **Documentation Digest will run on a FRONTIER model (Opus) via Claude Code headless, NOT a local model and NOT OpenClaw's anthropic provider (2026-06-21).** Anthropic's ToS restricts subscription OAuth auth to Claude Code / Claude.ai, so OpenClaw's own `anthropic/claude-opus` would need a pay-as-you-go API key; Claude Code (`claude -p`) is the subscription-covered path. Cadence WEEKLY. Billing caveat: as of 2026-06-15, headless `claude -p` draws from a separate monthly Agent SDK credit (Max 20x = $200/mo at API rates), not the interactive pool — verify against current policy.
- **No unattended Claude Code automation until strict cost-control protections are in place (decided 2026-06-27).** Applies to frontier-via-CC workstreams (Documentation Digest, notes integrity check). Until cost guards exist, run these manually/attended only. Ties to the standing wish for plan-usage visibility (CC has no way to read remaining Max/OAuth balance today). **SCOPED EXCEPTION (Brian, 2026-07-01): the INITIAL docs-digest build may run on temporary cron** (`digest_chunk.sh`, 7 PM + overnight chunks) — deliberate, bounded (fixed 57-batch corpus, content-hash cached, self-terminating when all batches cache), inside the Fable-promo window. The cron lines are marked TEMP and must be removed once the initial digest is FULL. This exception does NOT extend to the weekly recurring digest or any other CC automation.
- **Remote access (2026-06-17): Tailscale is the network layer; native protocols ride over it (SSH for shells, native RDP planned for desktops). VM SSH is keyless via Tailscale SSH; Windows hosts use their own OpenSSH (password for now, key-hardening planned). No third-party RD relay/account.**
- **VM resource allocation: STATIC memory + FIXED disk (not dynamic). Lean capable VM, fat host — LLMs/ML stay host-side. Detailed reasoning in the Networking & Infrastructure note.**
- **5090 second node will be SEEDED from a KlawMachine golden VHDX image (not rebuilt from scratch), then specialized. Identity-collision steps required on the clone.** (Near-term, amethyst is used only as a Gemma Ollama endpoint — no second VM yet; see Model Strategy.)
- **Cross-node co-orchestration must have a chain of command (no two co-equal bosses) plus bounded per-node autonomy — flagged as a hard design problem. Mechanism for resource yielding = Hyper-V **`Save-VM`**/**`Resume-VM`\*\* over SSH (one VM frees the other host's resources; no host ever powered off).\*\*

## Summary

The OpenClaw project has completed its initial infrastructure phase, Mem MCP integration, Claude Code install, and the documentation mirror — now fully closed out (private GitHub remote + nightly cron + agent pointers), with cron and caching verified on 2026-06-21. The current phase is security hardening (OS/host AND OpenClaw-application layers), then linking Claude Code to Mem for shared project memory, then building Klaw's ability to execute controlled system actions. Remote access (Tailscale + SSH) is established. Tool-execution isolation is handled nearer-term by OpenClaw's built-in sandbox; Firecracker is demoted to someday/maybe. Future phases include the Documentation Digest (whole-corpus distillation, weekly via Claude Code + Opus), the Debate Council, intelligent multi-agent orchestration, and the 5090 second node with cross-node co-orchestration.

***

## Completed Milestones

### May 2026 — Initial Lab Setup

- OpenClaw installed and operational in VMware VM.
- Discord integration configured.
- Conservative/isolated configuration established.

### June 10–11, 2026 — Hyper-V + Ollama Integration

- Migrated to Hyper-V.
- Dedicated OllamaSwitch networking established.
- Host ↔ VM Ollama connectivity validated.
- OpenClaw running on local models.

### June 11, 2026 — Performance Issue Resolved

- Severe latency diagnosed and isolated to tools.profile=coding.
- Gateway restart procedure validated.
- Named session practice established.
- System stable.

### June 11, 2026 — Telegram + Web Search Milestone

- Telegram bot configured and operational.
- Web search functioning via full profile.
- Remote access to OpenClaw demonstrated from phone.
- First practical remote-access milestone achieved.

### June 12–13, 2026 — Knowledge Management Initiative

- Dedicated OPENCLAW PROJECT collection established in Mem.
- Governance model designed and documented.
- MASTER note and Checkpoints note created.
- All six subject notes created and populated from legacy source migration.

### June 13, 2026 — Mem MCP Integration

- Mem MCP server registered and probed (26 tools discovered, 11 allowed via filter).
- bundle-mcp allowed through tools profile.
- AGENTS.md updated with Project Memory section.
- Klaw confirmed reading and writing Mem notes from fresh named sessions.
- Hyper-V checkpoint "Mem Integrated" created.

### June 13, 2026 — Claude Code Installed + Auth Resolved

- Native install on KlawMachine (v2.1.177). Establishes Claude Code as the local execution/config surface.
- Auth resolution: interactive = plain OAuth (persists over SSH); token env var is automation-only and breaks interactive mode. (A token was exposed in a screenshot, revoked, regenerated.)
- `mirror_openclaw_docs.py` written this session (stdlib-only).
- Hyper-V checkpoint "Claude Code installed" created.

### June 13, 2026 — Documentation Mirror Deployed & Verified

- Deployed via Claude Code (first real Claude-Code-driven task). Dry-run validated; two bugs fixed (`.xml`/`.txt` skip; root → `index.md`).
- Switched caching to ETag / If-None-Match (server sends no Last-Modified). Verified: run 1 = 684 fetched; run 2 = 683 unchanged / 1 fetched. INDEX.md = 684 entries.
- OPERATIONAL. Hyper-V checkpoint "Docs Mirror Operational - Basic" created. Full detail in Documentation & Knowledge Management note.

### June 14, 2026 — Git Version Control Initialized

- `~/.openclaw` is now a git repo with a deny-by-default `.gitignore`; verified all secrets/config/runtime/docs are ignored; only `.gitignore` + `scripts/mirror_openclaw_docs.py` tracked.
- Initial commit `4e844d2` (2 files). Repo-local identity set.
- Hyper-V checkpoint "Mid Git Setup" created (mid-task).

### June 14–15, 2026 — Primary Model Migration to qwen3.6:27b

- qwen3.6:27b (dense) applied as primary, flash attn + `q8_0` cache + 110K context (VRAM-verified). Post-migration cleanup removed gemma-test, fixed Telegram routing, made qwen resident. Full detail in Model Strategy & Orchestration and Checkpoints notes.

### June 16–17, 2026 — Remote Access Established (Tailscale + SSH)

- Tailscale mesh across VM, 3090 host, phone, laptop (+ a 5th Windows node); VM SSH passwordless via Tailscale SSH; Windows hosts via OpenSSH. RDP planned. Full detail + the Windows-username and check-mode gotchas in the Networking & Infrastructure note.

### June 20–21, 2026 — Documentation Mirror Track Closed Out & Verified

- 2026-06-20: pushed `klaw-konfig` to a PRIVATE GitHub remote via a repo-scoped deploy key + `github-openclaw` SSH alias (commits `4e844d2` → `afb0d8b`). Wrote + committed `AGENTS.md` and `CLAUDE.md` mirror pointers. Wrote `scripts/nightly.sh` (refresh mirror → commit/push only if a TRACKED file changed) and scheduled it in the SYSTEM crontab at 3:15 AM (chose plain crontab over `openclaw cron` — simpler, no gateway dependency). Recorded the standing Git Repository Strategy.
- 2026-06-21: cron CONFIRMED firing unattended (`.mirror_log.txt` run at 03:15); ETag caching CONFIRMED working (back-to-back run → fetched=2/unchanged=687). High fetch counts on gap-runs = upstream churn + apparent redeploy ETag rotation, NOT a bug. Mirror left as-is. Full detail in the Documentation & Knowledge Management note.

***

## Current Priorities

### 1. Close Out the Documentation Mirror — ✅ DONE (2026-06-21)

- [x] Script deployed, validated, and run successfully (ETag caching verified).
- [x] git init + deny-by-default `.gitignore` + initial commit (`4e844d2`). Secrets verified excluded.
- [x] PRIVATE GitHub repo added as remote and pushed — done via repo-scoped deploy key (`~/.ssh/openclaw_deploy`) + `github-openclaw` SSH alias; auth done by Brian in browser. (commits `4e844d2` → `afb0d8b`.)
- [x] Daily cron scheduled — used the SYSTEM crontab (`15 3 * * * .../nightly.sh`), NOT `openclaw cron` (the latter's syntax was unverified; plain crontab is simpler with no gateway dependency). Confirmed firing unattended 2026-06-21.
- [x] `CLAUDE.md` added in `~/.openclaw` and committed (mirror pointer + sources-of-truth + hard rules).
- [x] `AGENTS.md` updated to point Klaw at the mirror and committed.

- NOTE: closed ≠ unmonitored — see the light "Mirror — Ongoing Monitoring" practice in the Documentation note, and the Heartbeat Documentation Task below.

### 2. Git Remote & Backup Strategy (off-hours, batched) — ✅ largely DONE

- Key principle held: `git commit` is local/instant; only `git push` hits the network, so we control WHEN pushes happen.

- [x] Cadence decided + implemented: `scripts/nightly.sh` runs after the 3:15 AM mirror refresh and commits + pushes ONLY when a tracked file changed.
- [x] Push auth for unattended cron: repo-scoped deploy key (set up by Brian), used inline via `GIT_SSH_COMMAND` so cron's stripped env finds it.
- [ ] (Optional, later) Consider expanding what's backed up to GitHub beyond scripts/agents files (e.g. a redacted `openclaw.json.example`), still via deny-by-default allowlist so secrets never leave.

### 3. Phone Control of Claude Code (Remote Control) — TO-DO

- `disableRemoteControl` has been rolled back (Remote Control is enabled again as of 2026-06-14; the temporary disable was only for paste-issue debugging).

- [ ] Set up and try `/remote-control` to drive Claude Code from the phone. Brian is interested. Confirm the workflow and any pairing steps. (Note: distinct from raw SSH — now that SSH-from-phone works, Remote Control is the agentic-driving option on top.)

### 4. Link Claude Code to Mem MCP — ✅ CLOSED BY MIGRATION (2026-07-01)

- Obsolete: the OPENCLAW PROJECT collection was migrated to local markdown at `~/.openclaw/project-notes/` on 2026-07-01, which Claude Code reads natively — no MCP link needed. (Claude Code had also gained a native claude.ai Mem connector in the interim, used for the migration itself.)
- [x] The "read project notes / MASTER first" session-start convention is in `~/.openclaw/CLAUDE.md`.

### 5. Security Hardening — ← ACTIVE TASK (2026-06-21) — two layers: OS/host + OpenClaw-application

**OS / host layer:**

- [ ] Hyper-V snapshot baseline. ✓ Done (multiple snapshots exist)
- [ ] Configure SSH keys (ed25519). UPDATE 2026-06-17: remote access now rides Tailscale. VM SSH is already keyless/passwordless via Tailscale SSH (no keys needed there). The key work is now primarily for the WINDOWS hosts (to kill the password-every-time prompt and sidestep the Microsoft-account-credential issue): put the public key in `C:\ProgramData\ssh\administrators_authorized_keys` for admin accounts (strict perms) or `~/.ssh/authorized_keys` for non-admin, then `PasswordAuthentication no` + restart sshd. The LAN-side VM sshd is still password-auth (separate, pre-existing). Watch the `50-cloud-init.conf` drop-in override on the VM.
- [ ] Disable SSH password authentication after key verification.
- [ ] Enable UFW firewall (allow OpenSSH; optionally scope to the Default Switch subnet 172.18.192.0/20).
- [ ] Verify startup persistence of OpenClaw services after reboots.
- [ ] Configure OpenClaw owner account.

**OpenClaw-application layer (added 2026-06-21 — previously absent from this checklist; already reflected in MASTER priorities):**

- [ ] Run `openclaw security audit` (`--deep` / `--json`; `--fix` to apply) — application-layer hardening: allowlists, log redaction, file perms, Windows ACL resets. (Distinct from `openclaw doctor`, which is health/repair.)
- [ ] Turn ON the built-in sandbox (`agents.defaults.sandbox`): Docker backend, mode non-main or all, on top of the Hyper-V VM. (This is the Firecracker-replacement isolation path.)
- [ ] Configure tool policy / approvals: `exec.approvals.*`, `registerTrustedToolPolicy`, elevated/tool-policy model (deny-wins; `group:runtime`/`group:fs` shorthands; reserved admin namespaces). Approval-gated execution is mostly config over existing primitives.
- [ ] Plugin allowlisting: native plugins run in-process, unsandboxed, same trust as core — mitigate with allowlists + explicit load paths.
- [ ] **Lock down amethyst's Ollama endpoint** when it comes online for Gemma — bind to LAN/tailnet only; opening :11434 is new attack surface (tie-in with the Debate Council / role-split work in Model Strategy). Do it AT setup, not later.

### 6. Controlled System Actions Framework

- [ ] File creation via OpenClaw.
- [ ] File modification via OpenClaw.
- [ ] Script execution via OpenClaw (enables: openclaw docs, openclaw status, git, etc.)
- [ ] Approval-gated command execution.

### 7. Secrets Hygiene

- [x] Move Mem API key from literal header to OpenClaw secrets store (SecretRef) — DONE 2026-06-30 (key rotated after the council smoke leak + migrated to `${MEM_API_KEY}` in `.env`). NOW MOOT: Mem was severed entirely 2026-07-01 (`mcp.servers.mem` removed).
- [x] Stale `MEM_API_KEY` removed from `~/.openclaw/.env` — DONE 2026-07-01. (Optional: revoke the key in the mem.ai UI too — Brian-only action.)
- [x] **`openclaw.json` fully de-secreted — DONE 2026-07-01.** Gateway auth token → SecretRef (`GATEWAY_AUTH_TOKEN` in `.env`) — reverses the 6/30 "deferred, loopback-only, low value" call, on evidence: the global `read` grant made the config agent-readable. Default Telegram botToken (@KlawJBot) → SecretRef (`TELEGRAM_BOT_TOKEN` in `.env`), same env-object shape as the gemma account. Applied via `openclaw config patch` (dry-run validated, 6 updates); gateway restarted; both bots probe `works`; zero 40+-char literals remain in the config.
- [ ] **Residual gap: `.env` is itself readable by the agents' `read` tool.** Closing it = the Priority-1 sandbox/scoped-fs work (deny agent reads of `.env`/credential paths). Until then: no exec/write in the whitelist, Brian-only DMs, council redaction guard.
- [ ] Keep the Claude Code automation token in `~/.claude_env` (chmod 600), never cleartext in `.bashrc`; ensure git-ignored (it lives in `~`, outside the repo).

***

## Personal / Out-of-Scope (pointer only)

- Replacing 1Password 4 (Dropbox sync broke). Leaning KeePassXC + encrypted `.kdbx` on OneDrive (no API dependency; portable to Google Drive/Syncthing later). PERSONAL — kept out of this collection by scope rules. Full detail is in a separate personal Mem note ("Password Manager Replacement (Personal)").
- Windows licensing (3090/Surface Go/NUC/5090) and the 5090 Home→Pro upgrade decision are logged in the Networking & Infrastructure note (they gate Hyper-V/RDP host roles).

***

## Near-Term Future Roadmap

### Documentation Digest (whole-corpus distillation) — WEEKLY — INITIAL BUILD IN FLIGHT (2026-07-01)

- **Status 2026-07-01:** initial build running via `scripts/docs_digest.py` + `scripts/digest_chunk.sh` (map = Sonnet 5, reduce = Opus 4.8), chunked across 5-hour usage windows with a content-hash map cache; 28/57 map batches cached as of tonight; remainder on TEMP cron (see the scoped cron exception under Key Decisions); reduce fires once all batches cache. Incremental re-map roadmap (only changed docs) is the follow-on.

- Periodically distill the docs-mirror corpus into a dense (\~5:1) but detail-rich digest that Klaw / Claude Code can load ENTIRELY into context for a whole-corpus view (yields insights ad-hoc section queries miss). Distinct from RAG (retrieval) and the mirror (full fidelity). Preserves config keys/defaults/paths/CLI/tool/hook names/edge cases; drops prose/examples/marketing; built section-by-section in index order.
- **Cadence:** WEEKLY (off the already-mirrored content; no extra fetching).
- **Engine:** a frontier model (Opus) via Claude Code headless (`claude -p --model opus`), subscription-OAuth-authenticated — NOT a local model, NOT OpenClaw's anthropic provider (ToS restricts OAuth to Claude Code/Claude.ai). Ensure `ANTHROPIC_API_KEY` is unset in that env (else it bills pay-as-you-go API). Billing caveat: post-2026-06-15, headless `claude -p` draws from a separate monthly Agent SDK credit (Max 20x = $200/mo at API rates) — verify against current policy.
- **Production is chunked** (corpus >1M tokens won't fit one context); **analysis is single-pass** over the finished digest.
- **Companion artifact:** a Digest ANALYSIS / insights reference — single-pass Opus read over the finished digest capturing the cross-cutting, whole-corpus insights. This is the payoff of the whole concept.
- **GATE:** no unattended/scheduled CC automation until strict cost controls are in place (see Key Decisions, 2026-06-27) — manual/attended runs only until then.
- Working prototype + format exist in a Claude chat project (`openclaw-digest-FULL.md`, `openclaw-docs-combined.md`). Full spec + open design questions in the Documentation & Knowledge Management note.

### Project-Notes Integrity / Synthesis Check — RETARGETED 2026-07-01 (was "Mem Collection Integrity Check", added 2026-06-27)

- Sibling concept to the Documentation Digest's analysis pass, pointed at the **local project-notes corpus** (`~/.openclaw/project-notes/`; was the Mem collection pre-migration). Purpose is **validation + data integrity**, not compression: the notes are hand-curated and small enough to load whole — the value is a periodic whole-corpus synthesis/consistency pass.
- **What it does:** catch contradictions and stale facts across notes (the corpus carries several "CONTRADICTED IN PRACTICE" annotations); enforce the MASTER summary-synchronization rule (subject-note summaries vs MASTER drift); surface cross-note connections and orphaned open-items.
- **First manual pass effectively DONE 2026-07-01** (Claude Code full read-through post-migration: caught the Mem-era stale layer, the garbled MASTER entry, the digest-cron/cost-gate tension, and the repeatedly-deferred council blockers). Fold future passes into the planned Fable 5 whole-system eval, then recur.
- **Engine:** Claude Code + frontier model, single-pass. **Output = PROPOSED reconciliations for Brian's approval** (or applied live in an attended session, as on 2026-07-01).
- **HARD GATE:** same cost-control gate as the Documentation Digest — no unattended automation until cost controls exist.

### Mem Scope Enforcement — MCP Filtering Proxy — ✅ CLOSED / MOOT BY MIGRATION (2026-07-01)

- The entire problem class was eliminated by the Mem→local migration: agents are fully severed from Mem (`bundle-mcp` out of `tools.allow`, `mcp.servers.mem` block removed), so **no agent token reaches Brian's personal/financial notes anymore** — the concrete motivation is gone. Neither the filtering proxy (Fix B option b) nor a dedicated Mem account is needed.
- History retained for reference: Fix A (per-agent AGENTS.md policy gate) was the active guard 2026-06-27→07-01; token-level collection scoping (Fix B option a) was investigated and appeared unavailable in mem.ai's API.
- **Successor concern:** scoping now shifts to the planned filesystem-read grant for local agents — the gate there is "secrets systematically locked down first" (all secrets out of any agent-readable file, scoped fs/sandbox policy protecting `.env` and credential files). See the Pilot note's Future Direction.

### Debate Council (adversarial multi-agent review) — DESIGN FINALIZED 2026-06-22 (+ proposed refinements)

- **Debaters (locked):** qwen3.6:27b (pacifico) + gemma4:31b dense (amethyst, fp16, `num_ctx` 80K), as SYMMETRIC PEER-CRITICS (not fixed advocate/skeptic) — each advances its own case AND attacks the other's, rotating who opens.
- **Ripeness gate:** the debaters self-assess in fresh "amnesic" sessions (no separate pre-judge model); escalate when both assessors concur it's ripe (stable disagreement counts as ripe, not just convergence); guarded by a position-movement-delta signal + hard round cap.
- **Judge:** Opus via Claude Code, WITH leashed+snapshotted web search, under a HARD usage cap; judges only ripe debates, the delta since last verdict.
- **Cadence:** two clocks — fast/free local debate loop; Opus throttled by the gate + hard cap. (NOT weekly cron — that earlier plan is rejected as inefficient.)
- **Persistence:** full transcripts, thinking traces, per-round metadata, web snapshots, and Opus cost/usage → disk (`~/.openclaw/debates/`, git-ignored); verdict summaries → Mem.
- **PROPOSED refinements (under discussion, not crystallized):** a prep/case-construction phase before exchanges; long-many-cycle local debates as the economic rationale (cheap local exploration vs expensive frontier — the cost asymmetry is the point); Opus as AGENDA-SETTER (reads project goals → assigns the next motions; separate capped budget line; reviewable motion queue) forming a goal-driven flywheel.
- Full design + refinements + the honest "is it worth it vs Opus-chat" assessment live in the Model Strategy & Orchestration note. Forces standing up amethyst + remote-Ollama wiring + the Claude-Code-Opus pipeline (reusable infra). Harden amethyst's Ollama endpoint as part of this (see #5). Build as a discrete pilot first.

### Local Debate / Compete Arena (CLI harness) — POC BUILT 2026-06-28

A standalone command-line harness pitting the two local models against each other, built/validated this session: `~/.openclaw/scripts/debate.py` (stdlib-only, tracked in git; alias `debate`). Drives the existing debater agents headlessly via `openclaw agent --json` — no Claude Code needed.

- **Two modes:** `debate` (qwen `main` argues FOR a statement, gemma `gemma-amethyst` AGAINST, N rounds, with `[GROUNDED]`/`[ASSUMED]` self-tags + `[CHALLENGE:]` opponent-tags) and `compete` (both models independently attempt the SAME task, e.g. "code tic-tac-toe", outputs saved side by side). Flags: `--mode`, `-r/--rounds`, `-w/--web`, `--swap`, `--no-stream`, `-h`.
- **Web search as a budgeted resource:** `--web N` (default 3) tells the models they share an N-search budget; actual searches are detected from session logs and reported. INSTRUCTION-LEVEL only — no hard cap yet (same enforcement gap as Mem Fix B; a tool-policy/proxy would make it hard).
- **Streaming:** `--stream` simulates char-by-char output. Real token-by-token streaming is an ASPIRATION — `openclaw agent` returns whole turns; true streaming needs the gateway/Ollama streaming API and would bypass the agent SOUL framing.
- **No automated judge yet** (the Opus-judge layer is the full Debate Council design; this harness is the manual smoke-test substrate). Output to `~/.openclaw/debates/<ts>-<mode>-<slug>/` (git-ignored): transcript.md, per-turn JSON, session\_\*.jsonl (gemma reasoning traces; qwen's provider only allows `--thinking off`).
- **Telegram on-demand (PLANNED, exec-block-respecting):** let Klaw/Kettle stream a debate/competition to Brian by DM'ing a topic. The design AVOIDS loosening the `group:runtime` deny: the agent only WRITES a request file (`write` tool, not blocked) to a watched dir; a trusted background **debate-watcher service** (systemd --user, runs as klaw) picks it up, runs `debate.py`, and posts each turn back to Telegram as it completes (`openclaw agent --deliver` / `openclaw message`). Per-turn messages are the "streaming" experience on Telegram (true char-streaming infeasible there due to edit rate limits). To build next.

### Local Debate/Compete Arena — major update (2026-06-28, same day): collaborate mode, Opus judge, Telegram BUILT

Built out further the same session:

- **Third mode:\&#x20;**`collaborate` — the two models work TOGETHER on a goal (constructive criticism, build on each other, converge on the best outcome), and may read files/use tools. Use case: point them at real artifacts, e.g. `debate "Assess and improve ~/.openclaw/scripts/debate.py and its docs" --mode collaborate`.
- `--for {qwen,gemma}` — explicitly set which model argues FOR (debate mode); `--swap` is now an alias for `--for gemma`.
- **Friendly labels** — output and Telegram now show `qwen3.6:27b (pacifico)` and `gemma4:31b (amethyst)` instead of bare agent ids like `main`.
- **Opus judge BUILT —\&#x20;**`scripts/judge.py` (stdlib, tracked). Calls Claude Code headless (`claude -p --model opus --permission-mode bypassPermissions`) over a saved transcript and writes `verdict.md` (+ optional `--telegram`). No approval hangs — the judge uses NO tools (pure reasoning over the handed transcript), so there is nothing to approve. No-arg = judge the latest debate; pass a dir for a specific one. Validated on the Python-vs-GitHub web debate: it correctly flagged a FABRICATED "#1 since 2016" claim and a misdated 2024-URL-as-2025 citation, and named the undefined-metric blind spot. **BILLING:** older notes say `claude -p` may draw a separate Agent SDK credit, BUT a live judge run SUCCEEDED on the existing Max/OAuth auth with no SDK credit added — so it appears to use the subscription. Billing UNVERIFIED (check `/cost` / the Anthropic console). On-demand/attended use only; do NOT wire into an unattended loop until cost controls exist.

- **Telegram on-demand: BUILT + TESTED 2026-06-28** (previously "to build next"). `debate.py --telegram account:chatid` posts each turn live; `scripts/debate_watcher.py` is a systemd --user service (active + enabled) watching `~/.openclaw/debate-requests/` that runs + posts queued requests. End-to-end test passed (dropped a `.req` -> ran a compete -> posted both haikus to Telegram -> filed to processed/). Klaw + Kettle AGENTS.md tell them to drop a `.req` file on request (the `write` tool; exec stays denied). **UX caveat:** the agent-trigger depends on a Q4 local model reliably writing the request file — the terminal CLI is the deterministic path. **Cleaner future:** a first-class OpenClaw `debate` TOOL/plugin the agent calls directly, instead of writing a `.req` file by instruction.

### Off-site Backups — OneDrive (idea, 2026-06-28)

Brian has \~1 TB free on OneDrive. Idea: periodically back up beyond git. Candidates: Hyper-V VM snapshots/exports (large; host-side on Windows -> a host-side scheduled export/copy to OneDrive is the natural mechanism) and/or the small stuff (git repo, configs). Not yet designed/built — captured so it isn't forgotten. (2026-07-01: `mem-backups/` no longer a candidate — retired with the Mem cutover; project notes are now git-tracked + pushed, which covers them.)

### Voice / TTS output — "get OpenClaw to talk" (SOON, idea logged 2026-06-28)

Brian wants OpenClaw to speak (text-to-speech output) — and notes it has BUILT-IN functionality for this. Candidates: the `sag` / ElevenLabs TTS tool referenced in AGENTS.md, plus OpenClaw's own voice/media features (see docs `tools/tts.md`, media/voice-overlay). To-do: enable/configure a TTS path so agents can reply with voice; natural fun tie-in = read out a debate verdict or summary as audio. Not yet scoped/built.

### Alpaca Integration

- Connect Alpaca market data API.
- Explore market research agent capabilities.
- Watchlist monitoring.
- Daily briefing generation.

### Autonomous Research Workflows

- Telegram → OpenClaw Gateway → Research agent → Consolidated response.
- Autonomous web research and summarization.

### Heartbeat Documentation Task

- Add heartbeat task to periodically verify recent session work was documented in Mem.
- Catches cases where Klaw claims to have updated notes but did not execute the tool call.
- Natural place to also automate the docs-mirror health check (recent \~03:15 log entry, errors=0, discovered-count not collapsed) so "closed" doesn't drift into "silently broken."

### Firecracker Investigation — DEMOTED (someday/maybe, 2026-06-21)

- No longer a near-term track. Tool-execution isolation is handled by OpenClaw's built-in sandbox (Docker/SSH/OpenShell) on top of the Hyper-V VM — OpenClaw has no Firecracker backend and the VM is already a stronger boundary than Docker. Revisit only if a specific need for ephemeral, disposable microVMs emerges that the built-in sandbox can't meet. If revisited: verify nested virtualization + /dev/kvm inside Hyper-V; test Firecracker install; design ephemeral sandbox workflow.

***

## Long-Term Vision

### Multi-Agent Architecture

```
Main Agent (coordinator / router)
├─ Research Agent
├─ Market Agent
├─ News Agent
├─ Coding Agent
└─ Memory Agent
```

Primary interface: Telegram → OpenClaw Gateway → Main Agent → Specialized Subagents → Consolidated Response. (Buildable today on one gateway + config; the 5090 is added capacity, not a prerequisite.)

### Intelligent Model / Profile Routing

A deterministic or semi-deterministic orchestration layer that automatically selects agent profile and Ollama model based on task type, required tools, latency sensitivity, and model capabilities. Separate future workstream.

### Multi-Node Cluster (3090 + 5090) — design captured 2026-06-16/17

```
3090 Host                       5090 Host (future)
├─ Ollama                       ├─ Ollama
└─ OpenClaw VM (KlawMachine)    └─ OpenClaw VM (seeded from KlawMachine golden image)
```

- **Seeding:** the 5090's VM is cloned from a KlawMachine golden VHDX (shared substrate), then specialized — NOT rebuilt from scratch. Identity-collision steps required (rename host, regen SSH host keys, fresh Tailscale registration, repoint Ollama endpoint). See Networking & Infrastructure note.
- **Cross-node co-orchestration:** the two OpenClaw VMs should divide-and-conquer bulk work AND specialize (hardware is asymmetric). Resource yielding = one VM remotely `Save-VM`s the other (freeing that host's CPU/RAM for the host's own GPU/ML work) and `Resume-VM`s it after; no host is ever powered off; triggered over SSH/PowerShell. Requires a CHAIN OF COMMAND (no two co-equal bosses) plus bounded per-node autonomy — explicitly a hard design problem. NOTE: OpenClaw provides no built-in cross-gateway orchestration; this is custom work on top of independent gateways. Full design in the Model Strategy & Orchestration note (Multi-Node Co-Orchestration section).
- **VM-to-VM networking** (Tailscale-in-each-VM vs subnet routing) and the **specialization axis** (capability vs role vs homogeneous) are open decisions, deferred until the 5090 VM exists.
- NOTE: the near-term Gemma-on-amethyst plan does NOT need this full build — amethyst can serve a Gemma Ollama endpoint to pacifico's gateway with no second VM.

### OpenClaw Project Self-Management

Goal: Klaw participates directly in maintaining its own project notes and can run CLI tools (openclaw docs, openclaw status, etc.) via approval-gated execution.

***

## Recent Updates

- 2026-06-13: Roadmap note created from legacy source consolidation.
- 2026-06-13: Mem MCP integration completion + docs mirror design recorded.
- 2026-06-13: Claude Code installed and authenticated; docs-mirror script status corrected.
- 2026-06-13: Documentation mirror deployed and VERIFIED via Claude Code (684 pages, ETag caching). Recorded the interactive-vs-token auth resolution and version-control layering.
- 2026-06-14: Git version control initialized (deny-by-default .gitignore, commit `4e844d2`). Resolved the Windows-Terminal-vs-classic-console paste issue. Added: private GitHub remote plan, a Git Remote & Backup Strategy item (off-hours batched pushes), and a Phone Control / Remote Control to-do (disableRemoteControl rolled back). Personal password-manager research moved to its own note outside this collection.
- 2026-06-17: Recorded remote-access milestone (Tailscale + SSH) and folded in its implications: updated the SSH-keys hardening item (VM is keyless via Tailscale; key work is now for the Windows hosts), expanded the Multi-Node Cluster vision into a concrete design (VHDX golden-image seeding + cross-node `Save-VM` resource yielding + chain-of-command requirement), and added VM-allocation (static mem / fixed disk) and 5090 licensing as decisions/pointers. Detailed designs live in the Networking & Infrastructure and Model Strategy & Orchestration notes. Added the qwen migration + remote-access entries to Completed Milestones.
- 2026-06-21: **Docs-mirror track marked fully closed.** Checked off priority #1 (all done — private remote via deploy key, system-crontab cron confirmed firing unattended, AGENTS.md/CLAUDE.md pointers) and priority #2 (nightly push implemented). Promoted **security hardening to the ACTIVE task**. Added a June 20–21 Completed Milestone (close-out + cron/caching verification). Added the **Documentation Digest** (whole-corpus distillation) as a near-term future workstream; full spec lives in the Documentation & Knowledge Management note.
- 2026-06-21 (cont.): Refined the Digest plan per Brian — cadence WEEKLY; engine = frontier Opus via Claude Code headless (`claude -p --model opus`), subscription-OAuth path (not local, not OpenClaw's anthropic provider), with the June-15 Agent-SDK-credit billing caveat noted; production chunked / analysis single-pass; added a companion **Digest Analysis / insights** artifact. Also recorded that the closed mirror stays under light ongoing monitoring (folded a mirror-health check into the Heartbeat Documentation Task).
- 2026-06-21 (cont. 2): **Synced the Security Hardening section to MASTER** — added the OpenClaw-application layer (security audit, built-in sandbox, tool policy/approvals, plugin allowlists, lock down amethyst's Ollama) that was previously absent here. **Demoted Firecracker to someday/maybe** and added the **Debate Council** as a near-term future workstream (pointer; full design in Model Strategy).
- 2026-06-22: **Synced the Debate Council pointer to its finalized design** (Model Strategy note) — symmetric peer-critic debaters (qwen + gemma4:31b dense), self-assessed ripeness gate, Opus judge with leashed web search + hard cap, full persistence, and the **two-clock cadence replacing the old "weekly via openclaw cron"** plan. Added the proposed-but-not-crystallized refinements (prep phase, long-cycle economic rationale, Opus agenda-setter flywheel). Full detail + the honest worth-it assessment in the Model Strategy & Orchestration note.
- 2026-06-27: Added two near-term future workstreams from a Claude Code session: (1) **Mem Collection Integrity / Synthesis Check** — a scheduled whole-collection validation/data-integrity/synthesis pass (CC + Opus, single-pass, proposes reconciliations for approval); (2) **Mem Scope Enforcement — MCP Filtering Proxy** (defense-in-depth) — recording that the Fix A per-agent permission gate was implemented this session, that token-level collection scoping appears unavailable in mem.ai's API, and that a collection-filtering MCP proxy (or dedicated Mem account) is the backstop path. Added a standing **cost-control gate**: no unattended Claude Code automation (Digest OR integrity check) until strict cost protections exist. Bumped Last Updated to 2026-06-27.
- 2026-06-28: Built a local Debate/Compete Arena CLI (`scripts/debate.py`, alias `debate`) — headless via `openclaw agent`, debate + compete modes, instruction-level web-search budget, simulated streaming (real streaming = aspiration). Ran two manual debates (exec-autonomy; local-vs-cloud) validating both debater endpoints + the peer-critic SOUL tagging. Added Debate Council refinements #5 (position-reversed amnesiac re-runs) and #6 (opponent-claim tagging; self-tagging is gameable) to the Model Strategy note. Designed (not yet built) Telegram on-demand debate via a watcher-queue that respects the Kettle exec deny.
- 2026-06-28 (cont.): Arena expanded — added `collaborate` mode, `--for` positions, and friendly model labels; BUILT the Opus judge (`scripts/judge.py` via `claude -p`, writes verdict.md, validated on the web debate); Telegram on-demand BUILT + TESTED (watcher systemd service + per-turn delivery + agent `.req` trigger in AGENTS.md). Noted a future first-class `debate` tool/plugin to replace the `.req`-by-instruction UX, and an idea to back up to OneDrive (\~1 TB free).
- 2026-06-28 (cont. 2): Tested the Telegram agent-trigger (DM Kettle "compete: ...") — FAILED as predicted. gemma improvised mkdir/exec (correctly denied) and fired stray UNCOLLECTED Mem notes instead of writing one `.req` (4 stray notes trashed; exec deny held; no `.req` ever written). FIXES: (1) hard-denied Kettle's Mem-WRITE tools (`mem__create_note`/`update_note`/`add_note_to_collection`/`move_note`) on top of `group:runtime` — Kettle now READS Mem but cannot write (approved notes go via `mem-pending.md`); this reverses the earlier "don't block Kettle" call, on evidence. (2) Tightened the debate `[GROUNDED]` tag to REQUIRE a source actually retrieved that turn (web URL or file read) — memory claims must be `[ASSUMED]`; qwen had been tagging `[GROUNDED]` with ZERO searches, gutting the scheme. Strengthened the search nudge. (3) Added `--tg` shorthand (= `--telegram default:8852367597`). Diagnosed the amethyst slowness as NUM\_PARALLEL=1 CONTENTION (the Telegram-gemma bot + CLI-gemma debater share the one amethyst gemma4 endpoint; the aborted Telegram request queued the CLI turns). Chose the command namespace `/hotdog` for the deterministic Arena trigger — TO BUILD (a gateway-level command/plugin replacing the flaky `.req`-by-instruction UX). IDEA (logged): a CLI/Telegram way to unload/abort amethyst's Ollama to free the GPU or clear an orphaned in-flight request (e.g. `keep_alive:0` unload, `ollama stop`, or restart amethyst Ollama via SSH); openclaw has no built-in for this.
- 2026-06-28 (cont. 3): Built the DETERMINISTIC `/hotdog` Telegram trigger (namespace chosen by Brian). `scripts/hotdog.sh` = testable dispatcher (debate/compete/collab/judge + stop/drop/roll; `--tg` streams to Brian, `--dry`). A `message:received` file-hook at `~/.openclaw/hooks/hotdog/` (enabled, openclaw-managed) fires `hotdog.sh` on any `/hotdog ...` message — NO local model interprets the trigger, so it's deterministic; this replaces the flaky `.req`-by-instruction path. Verbs (Brian's "stop, drop, and roll"): `stop`=abort a running debate (frees its context, leaves model), `drop`=one-time unload gemma on amethyst (does NOT change the host's keep\_alive:-1 forever default), `roll`=unload+reload (pre-warm). Fixed a `--tg` arg-eating bug. OPEN QUESTION (verify by live DM): whether the agent ALSO replies to a `/hotdog` message — file hooks may not suppress the agent turn; if so the clean fix is a typed plugin hook (cancel) or registering `/hotdog` as a real command. Also this session: `[GROUNDED]` tightened to require an actual retrieval that turn; web-search remains instruction-level (Brian will also try prompting "use web search in your first response").
- 2026-06-28 (SESSION CLOSE): Big "Arena" session (Claude Code). BUILT: debate/compete/collaborate CLI (`scripts/debate.py`, alias `debate`); Opus judge (`scripts/judge.py`); local Mem backup (`scripts/mem_backup.py`, weekly cron, keep-10); reusable Mem editor (`scripts/mem_edit.py`); the DETERMINISTIC `/hotdog` Telegram trigger (`scripts/hotdog.sh` dispatcher + `hooks/hotdog/` message:received hook; verbs stop/drop/roll); per-turn Telegram delivery + `scripts/debate_watcher.py` systemd service. HARDENING: Kettle `exec` + Mem-write denied; debate `[GROUNDED]` tightened to require an actual retrieval that turn. VERIFIED: CLI debate/compete, judge (caught a fabricated claim), web-search (gemma cited real URLs), Telegram delivery, watcher e2e, `hotdog.sh` terminal run. OPEN / NEXT SESSION: Brian tested more and reports SOME ISSUES (not yet detailed — collect specifics first thing next session). Known opens: does the agent ALSO reply to `/hotdog` (file-hook suppression unverified); web-search is instruction-level and doesn't reliably fire; `/hotdog` use-case/value still unclear to Brian; TTS/voice to-do; candidates: auto-`--judge` flag, position-reversed re-runs, OneDrive backup, MCP scope proxy (Fix B), a typed plugin hook to cancel the agent turn on `/hotdog`.
- 2026-06-28 (cont.): Terminal command renamed `debate` -> `hotdog` (alias `hotdog` -> `scripts/hotdog.sh`, the full dispatcher) so the CLI matches the Telegram `/hotdog` namespace; old `debate` alias removed. Use e.g. `hotdog debate "..."`, `hotdog compete "..."`, `hotdog judge`, `hotdog stop|drop|roll`. (`scripts/debate.py` is still the underlying engine.)
- 2026-06-28 (cont. 3): Fixed a `hotdog.sh` bug — it passed `--quiet` unconditionally, so a terminal `hotdog debate` ran SILENTLY (no streamed turns, only the saved path). Now `--quiet` is applied ONLY when streaming to Telegram (`--tg`); plain CLI runs stream live again. BONUS observation: a CLI debate (shopping-cart ethics) confirmed WEB SEARCH now fires reliably — 6 searches; qwen pulled NEISS ER-injury data + ICR loss figures mid-debate with URLs, gemma challenged the sources. The tightened `[GROUNDED]`=must-retrieve rule worked. Caveat: used 6/3, so the web budget is still soft (not hard-enforced).
- 2026-07-01 (cont.): **Hardening + council-fix session (Claude Code, same day).** (1) SECRETS: `openclaw.json` fully de-secreted (gateway token + default botToken → env SecretRefs; stale MEM_API_KEY dropped; both bots verified `works` post-restart). (2) COMPACTION (Blocker A mitigation): explicit `agents.defaults.compaction` set — `reserveTokens`/`keepRecentTokens` 20000, `notifyUser: true`, `midTurnPrecheck.enabled: true` (guards mid-turn tool-result growth, the council's actual risk profile; the 6/23 fill-test failure is explained — giant single pastes + token-estimate undercount defeated both compaction triggers, unrepresentative of real council turns). (3) COUNCIL: null-run root cause = bare `KeyError('result')` on a result-less agent JSON envelope; `run_turn` now raises a diagnostic error + subprocess timeout backstop; stale Mem prompt text scrubbed from `council_pilot.py`; dead Mem REST code removed; opener-death fallback confirmed already in place (d09d584). (4) VERIFIED: `tools.allow` is a strict whitelist (gateway log: "removed 33 tool(s)") — effective agent surface = read + web only; resolves the old "~34 tools stripped" mystery; the null-run's "leaked manifest" was Claude Code environment noise, not gemma's grants. (5) PRE-FLIGHT findings: `openclaw security audit` = 1 critical (small models + web + sandbox off — matches the council's own sandbox plan); **xrdp listening on 3389 on ALL interfaces of the VM (open item — investigate/scope)**; UFW status unverified (sudo needs password). Blocker B mitigated for council (explicit session keys pin the model); TUI-only quirk, retest after next OpenClaw upgrade.
- 2026-07-01: **Post-migration reconciliation pass (Claude Code).** Updated this note for the Mem→local cutover: Current Status rewritten (local project-notes are the continuity layer; digest in flight; Fable 5 eval next); priority #4 (link CC to Mem MCP) CLOSED as obsolete; Mem Scope Enforcement / Fix B proxy CLOSED as moot (agents severed from Mem — the token-reaches-personal-notes risk is gone; successor concern is scoping the future filesystem-read grant); the Mem Collection Integrity Check retargeted to the local notes corpus (first manual pass effectively done via this session's full read-through); secrets-hygiene item marked done/moot with a follow-up to remove the unused `MEM_API_KEY`; recorded the **scoped cost-gate exception** for the temporary initial-digest crons (Brian, 2026-07-01).
- 2026-06-28 (cont. 4): KNOWN GAP / TO-DO (quick) — the `hotdog.sh` wrapper only forwards `--rounds`/`--web`/`--tg`/`--dry`, so `debate.py`'s `--for {qwen,gemma}` (set positions), `--swap`, `--no-stream`, and `--stream-delay` are NOT reachable via the `hotdog` command and don't show in `hotdog help`/`-h`. Fix next session: add flag passthrough in hotdog.sh + document them in its help (e.g. `hotdog debate "..." --for gemma`). The flags still work when calling `python3 scripts/debate.py` directly.
