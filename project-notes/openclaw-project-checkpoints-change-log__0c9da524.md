---
mem_id: 0c9da524-00ee-48c8-8285-9c4f1141ea50
title: "OPENCLAW PROJECT \u2014 Checkpoints & Change Log"
created_at: 2026-06-13T02:47:56.919Z
updated_at: 2026-06-30T05:31:33.570Z
source: mem:OPENCLAW PROJECT
---

# OPENCLAW PROJECT — Checkpoints & Change Log

## Current Status

Active.

## Last Updated

2026-06-28

## Key Decisions

- Checkpoints should not generally become standalone notes.
- Project history should be maintained in a centralized checkpoint and change-log note.
- Major milestones, discoveries, architecture changes, and validated findings should be summarized here.
- Terminology: "checkpoint" refers specifically to Hyper-V VM snapshots. Change-log entries in this note are "milestone entries," not checkpoints.
- This note has two parts: the **VM Snapshot Registry** (the canonical, authoritative ledger of every Hyper-V checkpoint) and the **Milestone History** (the narrative change log). The registry is the single source of truth for snapshots; record every new snapshot there.

## Summary

This note serves as the historical record for the OpenClaw project, in two parts:

1. **VM Snapshot Registry** — the canonical ledger of all Hyper-V checkpoints (VM snapshots), each with its name, date, and the state it captures. This was the note's original, exclusive purpose; the registry restores it explicitly after milestone prose had diluted it.
2. **Milestone History** — a concise narrative timeline of milestones, decisions, and project evolution.

The objective is to let a human or agent quickly understand both the recoverable VM states available and how the project reached its current state, without searching every technical note.

***

## VM Snapshot Registry

Canonical, authoritative list of all Hyper-V checkpoints (VM snapshots) for klaw-machine. Record every new snapshot here by name, date, and captured state. Listed oldest first.

**"Automatic Checkpoint - klaw-machine - (6/5/2026 - 8:36:00 PM)"**

- Date: 2026-06-05, \~8:36:00 PM
- Added retroactively from the Hyper-V checkpoint tree on 2026-06-28; no captured-state detail on record (the name is the documentation).
- Hyper-V automatic checkpoint (auto-generated).

**"klaw-machine - (6/5/2026 - 8:37:25 PM)"**

- Date: 2026-06-05, \~8:37:25 PM
- Added retroactively from the Hyper-V checkpoint tree on 2026-06-28; no captured-state detail on record (the name is the documentation).

**"Fresh Ubuntu"**

- Date: not recorded (between 2026-06-05 and 2026-06-11 per checkpoint-tree position).
- Added retroactively from the Hyper-V checkpoint tree on 2026-06-28; no captured-state detail on record (the name is the documentation).

**"Working-Ollama-Network"**

- Date: not recorded (between 2026-06-05 and 2026-06-11 per checkpoint-tree position).
- Added retroactively from the Hyper-V checkpoint tree on 2026-06-28; no captured-state detail on record (the name is the documentation).

**"OpenClaw-Working"**

- Date: not recorded (between 2026-06-05 and 2026-06-11 per checkpoint-tree position).
- Added retroactively from the Hyper-V checkpoint tree on 2026-06-28; no captured-state detail on record (the name is the documentation).

**"klaw-machine - (6/11/2026 - 1:00:10 AM)"**

- Date: 2026-06-11, ~~1:00:10 AM (~~1 minute before "Solved Openclaw Performance Issue - 6/11/2026 1:01 AM EDT").
- Added retroactively from the Hyper-V checkpoint tree on 2026-06-28; no captured-state detail on record (the name is the documentation).

**"Solved Openclaw Performance Issue - 6/11/2026 1:01 AM EDT"**

- Date: 2026-06-11, \~1:01 AM EDT
- Captures: known-good rollback point established after the latency root cause was resolved. Performance baseline at this state — coding profile \~65s / \~11k tokens; minimal profile \~1–2s / \~6.2k tokens; direct Ollama \~1.7s.
- Note: this snapshot is also mentioned in the Networking & Infrastructure note (VM Administration section). This registry is the canonical record; that mention should be treated as a secondary reference.

**"OpenClaw + Telegram + Web Search Working"**

- Date: not recorded (between 2026-06-11 and 2026-06-13 per checkpoint-tree position; likely the June 11 Telegram + Web Search milestone — see Milestone History).
- Added retroactively from the Hyper-V checkpoint tree on 2026-06-28; no captured-state detail on record (the name is the documentation).

**"Mem Integrated"**

- Date: 2026-06-13
- Captures: state after Mem MCP integration completed — Mem server registered (`mcp.mem.ai/mcp`), safe tool subset filtered, AGENTS.md updated with the Project Memory section, Klaw confirmed reading and writing Mem notes from fresh named sessions.

**"Claude Code installed"**

- Date: 2026-06-13
- Captures: state after Claude Code native install (v2.1.177, linux-x64) and claude.ai-subscription authentication on klaw-machine, with the credential confirmed persisting across SSH sessions. Captured by Brian.
- Note: taken before the documentation-mirror deployment and the interactive-auth resolution that followed (see Milestone History, 2026-06-13).

**"Docs Mirror Operational - Basic"**

- Date: 2026-06-13 (late; taken after the documentation mirror was deployed and verified)
- Captures: documentation mirror operational — `mirror_openclaw_docs.py` validated against the live site, 684 pages mirrored to `~/.openclaw/docs/` with INDEX.md, ETag / If-None-Match incremental caching verified (second run = 683 unchanged / 1 fetched / 0 errors).
- "Basic" qualifier: this state is PRE-git-commit and PRE-cron. The script is not yet under version control and the daily cron is not yet scheduled.
- Captured by Brian.

**"Mid Git Setup"**

- Date: 2026-06-14 (Sunday)
- Captures: partial state during the git close-out. A git repo has been initialized in `~/.openclaw` with a deny-by-default `.gitignore`, and the initial commit (`4e844d2`) has been made — tracking only `.gitignore` and `scripts/mirror_openclaw_docs.py`, with all secrets/config/runtime/docs confirmed ignored. Repo-local git identity set (klaw / <bmills85@gmail.com>), not global.
- Taken mid-task while on tangential discussions (planned private GitHub remote; personal password-manager replacement). Not an end-of-milestone snapshot.
- Still pending at this state: push to a planned private GitHub remote, daily cron, and the AGENTS.md + CLAUDE.md pointers.
- Captured by Brian.

**"Qwen Set Up - Context Limit Configured"**

- Date: 2026-06-15
- Captures: the qwen3.6:27b primary-model configuration on the **default agent** — flash attention + q8\_0 KV cache + a VRAM-verified 110K context (\~21,034 / 24,564 MiB, \~3.5GB headroom, held flat with no spill). This is the FIRST recoverable state that includes qwen as primary; the prior snapshot ("Mid Git Setup") predates the entire model migration. Corresponds to the June 14–15 Primary Model Migration milestone (see Milestone History below).
- Captured by Brian.
- Note: **this snapshot PREDATES the cleanup** (now confirmed). At this state both migration loose ends are still present: (1) the Telegram routing trap is UNFIXED — with no bindings, Telegram falls through to the `gemma-test` agent (the only `agents.list` entry, acting as the catch-all default) and loads gemma4:31b, evicting qwen; (2) the qwen model entry's `keep_alive` is still `"30m"` (not resident `-1`); and (3) the qwen entry's `contextWindow` is still `200000` (not yet aligned to the 110K cache). This is therefore the explicit **pre-cleanup rollback point**, superseded by "Qwen-Only - Gemma Removed, 110k Resident" below.

**"Qwen-Only - Gemma Removed, 110k Resident"**

- Date: 2026-06-15
- Captures: the clean, post-cleanup baseline. Single agent (default → `main` → `ollama/qwen3.6:27b`); the `gemma-test` agent plus its workspace and on-disk store fully removed; Telegram now routes to qwen with no gemma load/evict; qwen resident (`keep_alive: -1`, host `ollama ps` UNTIL "Forever"); `num_ctx 110000` and `contextWindow 110000` aligned (host `ollama ps` CONTEXT 110000, \~20GB, 100% GPU); `models[]` trimmed to qwen + mistral fallback (gemma4, qwen2.5:14b, qwq:32b, llama3:8b, llama3.3:latest removed). Supersedes "Qwen Set Up - Context Limit Configured".
- Captured by Brian.
- Note: 6 stale `agent:main:*` sessions were intentionally left in place (inert JSON rows, not loaded, \~15MB). OpenClaw has no per-session delete command (confirmed against the binary help and canonical docs); session removal is policy-driven via `session.maintenance` (defaults `pruneAfter: 30d` / `maxEntries: 500`), under which none of them qualified yet. Two entanglements are why a hand-delete was avoided: `agent:main:main` and `agent:main:qwen-test` SHARE one transcript (`sessionId 75f1400a`, \~10MB), and the live telegram session's `usageFamilySessionIds` reference `b72c27fa`/`29623def` (on disk as `.reset` archives) as compaction ancestry. A telegram session created before the contextWindow patch showed `/200k`; only sessions created after the patch show `/110k`.

**"klaw-machine - (6/21/2026 - 1:06:54 AM) - Github and Docs integration Launched"**

- Date: 2026-06-21, \~1:06:54 AM
- Captures: the GitHub-remote + documentation-integration milestone — the close-out of the documentation-mirror track that had been pending since "Mid Git Setup." Per the checkpoint name, this state reflects the docs mirror wired end-to-end: the private GitHub remote integrated for `~/.openclaw`, and the docs mirror made available to the agents via the `CLAUDE.md` / `AGENTS.md` pointers. Corroborated by a concurrent live Claude Code session at this time (Claude Code v2.1.179, Sonnet 4.6, running from `~/.openclaw/docs`, a 12-line `CLAUDE.md` present, a `claude-api` skill loading, and confirmed running on the claude.ai OAuth subscription with no `ANTHROPIC_API_KEY` set). Supersedes "Mid Git Setup" as the docs/GitHub rollback point.
- Captured by Brian; recorded in this registry via claude.ai chat at Brian's direction. Confirm the precise closed items (remote push, daily mirror cron, AGENTS.md + CLAUDE.md pointers) against the Roadmap note's "Close Out the Documentation Mirror" checklist.

**"klaw-machine - (6/27/2026 - 7:18:40 PM) - Copper Kettle up and other stuff"**

- Date: 2026-06-27, \~7:18:40 PM ET
- Captures: state AFTER the second Telegram bot "Copper Kettle" (`gemma-telegram` → `amethyst-ollama/gemma4:31b`, @CopperKettleBot) was built and verified. PREDATES the subsequent Claude Code session that added the honesty directive, the per-agent Mem write-permission gate, the Kettle exec/runtime tool-deny (gateway-restarted to apply), the Debater-B workspace cleanup, and the local Mem backup system. Captured by Brian.
- Note: the post-snapshot config changes were applied AFTER this checkpoint, so a fresh snapshot would be needed to capture the hardened state.

**"klaw-machine - (6/30/2026 - 1:25:53 AM) - working on autonomous loops"**

- Date: 2026-06-30, \~1:25:53 AM
- Captures: mid-build of the multi-agent "council" autonomy pilot plus a security-hardening pass. At this checkpoint: the Mem API key was rotated and migrated to a SecretRef (`${MEM_API_KEY}` in `~/.openclaw/.env`; plaintext purged from `openclaw.json` and all config backups), `gateway.controlUi.allowInsecureAuth` was disabled, the agents' filesystem `read` tool is deliberately OFF, and `scripts/council_pilot.py` is built — two local models (qwen `main`/pacifico, gemma `gemma-amethyst`/amethyst) review the OPENCLAW PROJECT collection via their own read-only Mem tools and collaborate with periodic headless tool-less `claude -p` weigh-ins, with a runtime secret-scan guard redacting secrets from all output. Pilot validated by two smoke tests but not yet run end-to-end. Captured by Brian.

***

## Milestone History

### May 2026 — Initial OpenClaw Exploration

Summary:

- Early experimentation with OpenClaw.
- VM-based isolation approach adopted.
- Focus on safe experimentation and reversibility.

### June 10–11, 2026 — Hyper-V + Ollama Integration

Summary:

- OpenClaw running in Ubuntu VM.
- Ollama running on Windows host.
- Dedicated networking established.
- Host-to-VM communication validated.

Key Outcome:

- Preferred architecture became Ollama on host OS and OpenClaw inside VM.

### June 11, 2026 — Performance Investigation

Summary:

- Severe latency investigated.
- Direct Ollama performance validated.
- Legacy sessions identified as a significant contributor.
- Gateway restart procedures validated.

Key Outcome:

- Infrastructure confirmed healthy.
- Project continued without major redesign.
- Related VM snapshot: "Solved Openclaw Performance Issue - 6/11/2026 1:01 AM EDT" (see registry above).

### June 11, 2026 — Telegram + Web Search Milestone

Summary:

- Telegram integration functioning.
- Web search functioning.
- Remote access to OpenClaw demonstrated.

Key Outcome:

- First practical remote-access milestone achieved.

### June 12, 2026 — Knowledge Management Initiative

Summary:

- Decision made to consolidate project memory.
- Dedicated OpenClaw project collection established.
- Master note created.
- Documentation strategy formalized.

Key Outcome:

- Shift from infrastructure building toward structured project memory and documentation management.

### June 13, 2026 — Mem MCP Integration Complete

Summary:

- Mem MCP server registered in OpenClaw (`mcp.mem.ai/mcp`, streamable-http).
- Tool filter applied — safe subset of Mem tools exposed to Klaw.
- `bundle-mcp` allowed through minimal profile.
- AGENTS.md updated with Project Memory section: memory scope rules, session startup workflow, subject note index, update rules.
- All legacy test sessions cleared. One active session retained (Telegram).
- `openclaw chat` confirmed as interactive terminal session command.
- Klaw verified capable of reading OPENCLAW PROJECT MASTER note via Mem MCP.
- All six subject notes populated from legacy source migration.

Key Outcome:

- Klaw now has persistent project memory via Mem.
- Project knowledge survives session restarts.
- Foundation established for OpenClaw self-managing its own project documentation.
- Related VM snapshot: "Mem Integrated" (see registry above).

### June 13, 2026 — Claude Code Installed on VM (Development Surface)

Summary:

- Claude Code installed on klaw-machine via the native installer (v2.1.177, linux-x64, binary at `~/.local/bin/claude`).
- PATH updated in `~/.bashrc`. `claude doctor` reports a healthy install: native method, bundled search OK, auto-updates enabled on the `latest` channel.
- Authenticated with the claude.ai subscription via `claude auth login` run from the Ubuntu GUI (browser OAuth, localhost callback). Login successful — plan qualifies for Claude Code.
- The remaining `tengu_ccr_bridge` / Remote Control feature-flag warning is benign: Remote Control is a separate opt-in feature (status: disabled) and is not required for local CLI use.
- `mirror_openclaw_docs.py` was actually written this session (stdlib-only, urllib). Correction to the prior Roadmap entry which had recorded it as "written" when it had only been spec'd.

Key Outcome:

- Claude Code is now the execution and configuration surface on the VM, replacing the chat-and-paste loop for VM-bound work.
- Continuity strategy clarified: the Mem OPENCLAW PROJECT collection is the cross-tool memory layer; claude.ai chat history is NOT accessible to Claude Code.
- Related VM snapshot: "Claude Code installed" (see registry above).

### June 13, 2026 — Claude Code Auth Resolved (Interactive vs Token)

Summary:

- An earlier assumption that `CLAUDE_CODE_OAUTH_TOKEN` would enable interactive login was wrong. Setting it in the interactive shell actually broke interactive login (kept forcing the OAuth login screen) — a known interaction where the token env var interferes with interactive mode.
- Resolution: commented out the `~/.claude_env` auto-load in `.bashrc`, logged in via plain OAuth (`claude` → option 1 → browser), and confirmed the credential persists across fresh SSH sessions on its own — no token needed for interactive use.
- A token was briefly exposed in an uploaded screenshot and was REVOKED; a fresh one was generated and stored in `~/.claude_env` (chmod 600), reserved strictly for non-interactive automation (cron, `claude -p`).

Key Outcome:

- Durable rule established: interactive Claude Code = plain OAuth (persists); automation = `CLAUDE_CODE_OAUTH_TOKEN`, never loaded in interactive shells.
- Lesson logged: never screenshot/paste a live token; treat exposure as compromise and revoke immediately.

### June 13, 2026 — Documentation Mirror Deployed & Verified

Summary:

- `mirror_openclaw_docs.py` transferred to `~/.openclaw/scripts/` (scp from host) and run via Claude Code — the first real Claude-Code-driven task on the VM, closing the chat-and-paste loop for execution.
- Dry-run validated against the live `docs.openclaw.ai/llms.txt`. Core assumptions confirmed (`.md` endpoint, `[title](url)` link format, 686 pages). Two bugs found and fixed: `robots.txt`/`sitemap.xml` getting `.md` appended (added `.xml`/`.txt` to skip set), and the bare root not resolving to `index.md`. Count corrected to 684.
- Discovered the docs server returns an ETag but no Last-Modified header, so the original If-Modified-Since caching could never work. Rewrote conditional GET to ETag / If-None-Match with per-page `.etag` sidecars.
- Verified: run 1 = fetched 684 / unchanged 0 / errors 0; run 2 = fetched 1 / unchanged 683 / errors 0 (the single re-fetch, `channels/whatsapp.md`, had genuinely changed). INDEX.md confirmed at 684 entries (sidecars excluded).

Key Outcome:

- Documentation mirror is OPERATIONAL with working incremental caching. Full operational detail in the Documentation & Knowledge Management note.
- Remaining to close the track: commit the validated script to git (output git-ignored), schedule the daily cron, and point both Klaw (AGENTS.md) and Claude Code (CLAUDE.md) at the mirror.
- Related VM snapshot: "Docs Mirror Operational - Basic" (see registry above), captured at this state.

### June 14, 2026 — Git Version Control Initialized

Summary:

- git repo initialized in `~/.openclaw`. Repo-local identity set (klaw / <bmills85@gmail.com>), not global.
- Deny-by-default `.gitignore`: `*` then allowlist (`!.gitignore`, `!scripts/`, `!scripts/mirror_openclaw_docs.py`).
- Verified via `git status` + `git check-ignore -v` that all sensitive/runtime paths are ignored: `openclaw.json` (plus `.bak` / `.last-good` backups, which hold live keys), `credentials/`, `identity/`, `docs/` (mirror + `.etag` + `.mirror_log.txt`), `memory/*.sqlite`, `state/*.sqlite`, `tui/`, `scripts/__pycache__`, runtime handoff JSON. Staged list confirmed = only the two safe files.
- Initial commit `4e844d2` created (2 files).
- Paste/terminal issue resolved en route: the classic Windows PowerShell console doesn't paste into Claude Code's TUI; the fix is to use the Windows Terminal app (not the blue PowerShell console). Also unbound ctrl+v from image-paste in `~/.claude/keybindings.json` (harmless to keep). Root cause of "worked yesterday" was being in different terminal apps (Windows Terminal vs classic console), with admin-elevation likely disrupting the default-terminal handoff.

Key Outcome:

- The validated script is now under durable local version control; keys never entered git history.
- Decision: add a PRIVATE GitHub remote (user has a GitHub account). GitHub authentication (SSH key or PAT) to be performed by the user directly, NOT via the agent. Push deferred — local commit already satisfies the version-history goal.
- Remaining on the docs track: push to private remote, daily cron, and AGENTS.md + CLAUDE.md pointers.
- Related VM snapshot: "Mid Git Setup" (see registry above).

### June 14–15, 2026 — Primary Model Migration: mistral-small3.2:24b → qwen3.6:27b (Major)

This was the session's main work — a deep model-selection investigation, the switch itself, and live VRAM/behavior verification. Full reasoning and the longer-term orchestration design live in the **Model Strategy & Orchestration** note; the per-model config facts live in the updated **Configuration & Models** note. Summary of what happened and why:

**Trigger and investigation.** Brian wanted to move Klaw off mistral-small3.2:24b (initially toward gemma4:31b). This opened a substantial research effort comparing Mistral vs Gemma 4 vs Qwen for an agentic, tool-calling, autonomy-bound workload on the single 24GB card (RTX 3090 Ti). Key findings:

- Mistral Small 3.2 actually beats Gemma _3_, but Gemma _4_ (released Apr 2026) is a real generational leap — its headline fix is tool-calling (τ2-bench agentic 6.6% → 86.4%). (Correction logged: an assistant claim that Gemma 4 might not exist was wrong; Brian was right.)
- Qwen is the open-weight function-calling leader (tops BFCL). qwen3.6:27b is the recommended agentic daily-driver size; dense, so robust and quantization-tolerant.
- A gemma-test agent was set up (isolated, `model: ollama/gemma4:31b`, own workspace) and gemma4:31b passed a live tool test (read a Mem note verbatim) — so Gemma's tool-calling works; it was rejected on VRAM-fit/quant-sensitivity/speed, not capability.

**The VRAM lesson (carried over and reconfirmed).** `ollama ps` reporting "100% GPU" is NOT a saturation signal — `nvidia-smi` is the truthful gauge. gemma4:31b at 32K measured \~23,346/24,564 MiB (\~1.2GB headroom, redline) and spilled to host RAM/disk under load (the "molasses" pause). The real constraint is VRAM headroom for the KV cache, not system RAM (RAM exhaustion was a downstream symptom of VRAM saturation).

**KV-cache quantization — the deciding detail.** Benchmark data (run on the same 3090/24GB/32GB rig) showed q8\_0 cache is virtually lossless on Qwen (KL < 0.04), while q4\_0 is NOT — it concentrates damage in long documents (KL 0.581) and tool calling, "will break your tool calls." Those are exactly Klaw's core uses, so q4\_0 was rejected. Gemma 4 (esp. the 26B MoE) is unusually quantization-sensitive, a further strike against it. Also clarified: MoE saves compute (speed), not memory — all experts stay VRAM-resident — and dense wins quality-per-VRAM-GB; the dense qwen3.6:27b avoids MoE's routing/robustness/quant-sensitivity issues.

**Decision: qwen3.6:27b (dense) as primary local workhorse.** mistral retained as fallback. Longer-term orchestration design (resident workhorse + tiny co-resident embedder + sparing frontier-API tier (VRAM-free) + on-demand heavy local specialists, with confidence-gated escalation and an AI council) captured in the Model Strategy note — design only, not built.

**Execution and verification (all completed and confirmed):**

- Brian pulled qwen3.6:27b (17GB).
- Set GLOBAL host env vars (Windows, via `setx`): `OLLAMA_FLASH_ATTENTION=1`, `OLLAMA_KV_CACHE_TYPE=q8_0`. These are global-only (cannot be per-model or Modelfile) and require a FULL Ollama restart (tray Quit → relaunch) — initially missed (echo came back blank because `setx` doesn't affect the running process), then done correctly. Confirmed live in server.log: `flash_attn = enabled`, `K/V (q8_0)`, 1088 MiB cache at 32K.
- Edited `openclaw.json` via Claude Code (deny-by-default care, diff reviewed before write, JSON validated; the inline-python edit display was truncated by terminal copy/paste but the diff confirmed correctness): `agents.defaults.model` → `"ollama/qwen3.6:27b"` (plain string, replacing the old `{primary: ...}` object); under `models.providers.ollama` set `contextWindow: 110000` and a model entry `{id, name: qwen3.6:27b, params:{num_ctx:110000, keep_alive:"30m"}}`. gemma-test left intact. Confirmed the per-model context key via the local docs mirror (`docs/providers/ollama.md`): `params.num_ctx` is what's forwarded to Ollama; `contextWindow` is OpenClaw's compaction budget — set both equal to avoid the perceived-vs-actual mismatch.
- **VRAM VERIFIED** (host `nvidia-smi`): qwen3.6:27b at 110K context = \~21,034 MiB / 24,564 MiB, 100% GPU, \~3.5GB headroom. Held FLAT at \~21GB while the session filled to \~96K under live use — no creep, no spill, no molasses (pre-allocation confirmed: the cache is reserved at load, so filling it does not grow VRAM). `ollama ps` showed CONTEXT 110000. Temps 73–79°C at \~440W under generation, idle \~41°C — safe for a 3090 Ti (throttle \~83–88°C) but bursty/human-paced; sustained 24/7 autonomy warrants a thermal re-check (incl. VRAM junction temp).
- **Compaction OBSERVED firing**: mid-session the token count rolled \~96k → \~48k as it approached the 110K budget — confirming OpenClaw's compaction (summarize/prune/memory-flush) triggers before the physical cache overflows. The contextWindow↔num\_ctx alignment works. Caveat: compaction discards oldest-first, so the threshold may need tuning if Klaw forgets the start of long autonomous tasks.

**Decision on context size:** keep the 110K pin rather than maxing it. Even with \~3.5GB free, the headroom is banked for safety, the future co-resident embedder, compute buffers, and thermal/autonomy margin — and OpenClaw's compaction means a session rarely reaches 110K anyway, so a higher pin would buy little usable context.

**OPEN ISSUE discovered at session end — Telegram routing.** Messaging Klaw via Telegram loaded gemma4:31b and EVICTED qwen3.6:27b (only one big model fits 24GB). Telegram is bound to the gemma-test agent OR a stale Telegram session predating the change. Diagnose with `/status` in Telegram; fix next session (rebind Telegram to the default/qwen agent, or set the bound agent's model to qwen / remove its override, or remove gemma-test entirely). Tracked in the "Open Issues / Next Session (2026-06-15)" note. Matters before autonomy — the remote interface is currently running the wrong model and thrashing the VRAM swap each message.

**Also noted (to reconcile):** the qwen model entry was written with `keep_alive: "30m"`, but Brian indicates the intent is for the workhorse to stay resident ("forever" / `-1`). Reconcile next session so the model doesn't unload between uses on a 24/7 box.

Key Outcome:

- qwen3.6:27b is the verified primary on the **default agent**, with flash attention + q8\_0 + a stable, VRAM-verified 110K context — a \~3.4× jump over the 32K redline that was crashing the host, with real headroom and no spill. Mem notes updated: new Model Strategy & Orchestration note; Configuration & Models rewritten to current; this milestone entry.
- VM snapshot "Qwen Set Up - Context Limit Configured" (2026-06-15) captures this state — see the VM Snapshot Registry above. (The caveats noted at snapshot time — Telegram-fix status and the 30m keep\_alive — are now RESOLVED in the June 15 post-migration cleanup below; that snapshot is now the pre-cleanup rollback point.)

### June 15, 2026 — Post-Migration Cleanup: Gemma Removed, Routing Fixed, qwen Resident

Follow-up session that closed the open issues the migration left. All changes verified via `openclaw status` and host `ollama ps`.

**Telegram routing root cause (corrected).** The earlier hypothesis of an explicit telegram→gemma-test binding was wrong. `openclaw agents bindings` returned "No routing bindings," and `channels.telegram` had no agent key. Per OpenClaw's documented routing precedence, when no binding matches the default agent is "`agents.list[].default`, else first list entry, fallback to main" — and `gemma-test` was the only entry in `agents.list`, so it was silently acting as the catch-all default for all unbound inbound. That is why Telegram loaded gemma4 with no visible binding. The `openclaw doctor` "message tool unavailable for gemma-test" warning was the same root cause seen from the tool-availability side.

**Actions taken:**

- `openclaw agents delete gemma-test` — removed the agent, its workspace (`workspace-gemma-test`), and its store. A leftover empty `~/.openclaw/agents/gemma-test/` directory survived the delete and was removed manually; a gateway restart was then needed to flush stale state (status had still shown `Agents: 2` and a gemma-test heartbeat until restart + dir removal). With the list empty, routing falls back to `main` → qwen. Verified: live telegram session runs `qwen3.6:27b`.
- `openclaw config patch --file ... --replace-path models.providers.ollama.models` — set qwen `contextWindow` 200000→110000 (aligned to the cache; the rollover was already keying off `num_ctx`, so this was confirmation rather than a behavior change), set `keep_alive` "30m"→`-1` (resident; verified `ollama ps` UNTIL "Forever"), and trimmed the model registry from 7 entries to qwen + mistral. The array-removal guard required `--replace-path` (`config set --replace` does not exist on 2026.6.5; the correct flag is `--replace-path <dot.path>`).
- Backups taken before edits: `~/.openclaw/openclaw.json.manual-bak` and a recursive copy of the sessions dir (`sessions.bak`). Safe to delete once this snapshot is verified.

**Sessions — investigated, intentionally NOT pruned.** The goal was a tidy session list, but OpenClaw has no per-session delete command. (A Google AI Overview claiming `openclaw sessions rm <key>` exists was wrong; verified false against both the binary help and the canonical docs.) `cleanup` is retention-policy-driven: a `--dry-run` planned `remove 0` because the stalest session (2d) is far under the default `pruneAfter: 30d` and 7 entries is under `maxEntries: 500`. Removing the old sessions would require either lowering `pruneAfter` into a standing policy (an age threshold can't selectively keep a 7m session and drop a 1h one) or hand-editing `sessions.json` with the gateway stopped. Given the sessions are inert (\~15MB, not loaded) and two are entangled — `agent:main:main` and `agent:main:qwen-test` share the \~10MB `75f1400a` transcript, and the live telegram session references `b72c27fa`/`29623def` `.reset` files as compaction ancestry — the deliberate decision was to leave them. Option for later: set a sane standing retention (e.g. `pruneAfter: 7d`, `maxEntries: 50`) and let them age out automatically.

**Declined for now (deliberately):** the `openclaw doctor` per-model num\_ctx "repair" (it wants to push qwen 110000→131072, back toward the redline), the `chmod 700 ~/.openclaw` prompt (sensible hardening, but to be done as its own deliberate step), and the `bundle-mcp` allowlist warning (Mem MCP works; the entry name may be stale — confirm against the mirror later).

Key Outcome:

- Clean qwen-only baseline: one agent, Telegram→qwen, 110k cache+budget aligned, resident, model registry trimmed. VM snapshot "Qwen-Only - Gemma Removed, 110k Resident" (2026-06-15) captures this state — see the VM Snapshot Registry above. The prior "Qwen Set Up - Context Limit Configured" is now the explicit pre-cleanup rollback point (gemma present, first-list-entry routing trap, 30m keep\_alive, 200k contextWindow).

### June 16, 2026 — Remote Access Established: Tailscale Mesh + SSH (VM verified), RDP Planned

Full detail in the **Networking & Infrastructure** note's new Remote Access section. Summary:

- Stood up Tailscale as the remote-access network layer across three nodes on account `bmills85@`: VM `klaw-virtual-machine` (100.93.74.11, Tailscale v1.98.4, Tailscale SSH via `tailscale up --ssh`); Windows 3090 host `desktop-3vs1n08` (100.93.186.114); phone `pixel-9` (100.71.126.47).
- **VERIFIED:** SSH from the phone into the VM landed in bash with no password — tailnet identity authenticated.
- Windows host prepared as an SSH node: OpenSSH Server installed, `sshd` Running + StartupType Automatic, DefaultShell registry set to PowerShell, firewall rule `OpenSSH-Server-In-TCP` present. Reachable over the tailnet; the phone→host connection was not yet confirmed at end of session.
- Decision: run native protocols over Tailscale (SSH for shells, native RDP for desktops); no third-party remote-desktop relay/account. RustDesk considered but not chosen (redundant over Tailscale). **\[NOTE 2026-06-20: this RDP decision was later REVERSED — see the June 20 entry. RustDesk became the chosen desktop layer; native RDP was abandoned and disabled.]**
- RDP is PLANNED, not yet enabled or tested anywhere: Windows built-in RDP (needs Pro); Ubuntu 24.04 via gnome-remote-desktop (GUI "Remote Login" mode for klaw-machine, or `grdctl --system rdp …`), port 3389; expect the mstsc↔GNOME "authentication error / More data is available" negotiation gotcha (use Windows App/Remmina, or force the RDP security layer).
- Windows licensing logged: Hyper-V and RDP-hosting both require Pro. 3090 = Pro; Surface Go 2 (refurb, arriving \~2026-06-17) = Pro (intended as client only); personal PC edition TBD; 5090 likely Home → needs a Home→Pro upgrade for its intended host role. OEM licenses are locked to the board (non-transferable), so the Surface Go's Pro cannot be moved to the 5090. **\[NOTE 2026-06-20: the 5090 (**`amethyst`**) is now confirmed Pro, so the Home→Pro question for it is moot.]**
- Multi-node 3090↔5090 networking discussed, no decisions made: direct cable vs gigabit switch vs Tailscale; VM-to-VM bridging (Tailscale inside each VM, or host subnet routing) is the genuine open item.
- Noted the VM Tailscale DNS health warning ("can't reach the configured DNS servers"), likely tied to eth1's no-gateway static config; mitigate with `100.x` IPs or `--accept-dns=false`.

Key Outcome:

- Second practical remote-access milestone (after Telegram): genuine shell access from the phone to the VM, verified, over an encrypted private mesh — and an SSH-ready Windows host. No VM snapshot was captured for this state; the only VM-side change is the Tailscale package + `tailscale up --ssh` (host- and phone-side changes are outside the VM image). A snapshot could be taken if a clean post-remote-access rollback point is wanted.

### June 20, 2026 — Remote Desktop Switched to RustDesk; RDP Disabled; 5090 on the Tailnet

Full detail in the **Networking & Infrastructure** note (Remote Access → "Remote Desktop — RustDesk over Tailscale"). Summary:

**Trigger.** pacifico (the 3090 host) went unreachable remotely after a Windows RDP session was closed; physically it was powered on (fans/GPU lit) but sending no video to the monitor, would not wake from a power-button tap or the reset button, and required a forced power-button hold + cold start to recover (HDMI on the motherboard showed it sitting at BIOS). This is what prompted abandoning native RDP.

**Decision (reverses the June 16 native-RDP plan).** Remote-desktop layer switched to **RustDesk over Tailscale**. Rationale: Windows RDP spins up a separate virtual session and on disconnect tears it down, handing the console back to the GPU — which on this box failed to re-drive video (the wedge). RustDesk attaches to the EXISTING console session with no teardown, so it sidesteps that failure mode, and had been used repeatedly without issue. Over the tailnet RustDesk connects P2P (no dependence on its public relay).

**Windows RDP teardown on pacifico (DONE + VERIFIED).** `fDenyTSConnections=1`; `Disable-NetFirewallRule -DisplayGroup "Remote Desktop"`; reset RD `RemoteAddress` to `Any`; `Set-Service TermService -StartupType Disabled`. Verified: fDenyTSConnections=1, all RD rules disabled, nothing listening on 3389, TermService disabled. OpenSSH and NLA deliberately left untouched.

**RustDesk lockdown on pacifico (DONE + VERIFIED).** Direct-IP access enabled on port 21118 (`netstat` confirms LISTENING on `0.0.0.0:21118` AND `[::]:21118`, PID 8460). The two inbound `RustDesk Service` firewall rules (program-allow, Protocol/Port Any) scoped to the 6 tailnet IPv4 addresses (`$tailnet`); outbound left `Any` so relay fallback survives. Verified all six addresses landed on both inbound rules.

**Two PowerShell gotchas logged:**

- `Get-NetFirewallRule -DisplayName X -Direction Inbound` → `AmbiguousParameterSet` (those two params are in different parameter sets); filter direction with `Where-Object { $_.Direction -eq 'Inbound' }` instead.
- **The silent one:** `$tailnet` was empty across a fresh PowerShell session (`$tailnet.Count` = 0), and `Set-NetFirewallRule -RemoteAddress $null` does NOT error — it silently resolves to `Any`. So earlier "successful" scoping commands were silent no-ops that left the rules wide open. Fix: define `$tailnet` in the same session and guard with `if ($tailnet.Count -lt 6) { throw }` before any scoping.

**Known gap:** firewall allow-list is IPv4-only while the listener is also on IPv6 `[::]:21118` (Tailscale also assigns `fd7a:115c:a1e0::/48`). Acceptable for now (RustDesk dials the typed IPv4); close later by adding `fd7a:` addresses or disabling RustDesk IPv6 binding.

**Sleep ruled out (not the cause).** Idle sleep was checked and excluded (power plan = Never on AC), and the Event 42 "Application API" sleep log entries were benign (each followed immediately by a clean resume). No action needed there; not the source of the remote-wedge incident.

**Node identities CONFIRMED** (resolves the long-standing laptop-vs-NUC TBC): `amethyst` (100.113.225.2) = the **5090** system, Windows 11 Pro, now on the tailnet — supersedes the earlier "5090 = OEM Home" assumption; `rincon` (100.102.221.40) = the **NUC** (personal daily-driver PC); `wren` (100.71.149.44) = the **Surface Go 2** (client terminal); `pacifico` = 3090 host; `bovinius` = phone; `klaw-machine` = the VM.

Key Outcome:

- RustDesk-over-Tailscale is the live remote-desktop layer on pacifico; Windows RDP is off, removing the RDP-disconnect GPU-wedge mode. The **smart-plug remote-recovery backstop** (BIOS "Restore on AC Power Loss → Power On") remains recommended as the only remote way out of any future hard hang — not yet implemented.
- The **5090 (**`amethyst`**) is now on the tailnet and confirmed Windows 11 Pro** — a real step toward the second OpenClaw node. amethyst/rincon/wren still need RustDesk direct-IP + firewall scoping (to be done remotely over the relay).
- No VM snapshot — all changes are host-side (pacifico), outside the klaw-machine VM image.

### June 21, 2026 — GitHub Remote + Docs Integration Launched

Summary:

- Documentation-mirror track closed out end-to-end: per the checkpoint name, the `~/.openclaw` git repo's private GitHub remote is integrated, and the docs mirror is wired into the tooling via the `CLAUDE.md` (and AGENTS.md) pointers so Claude Code and Klaw read from `~/.openclaw/docs`.
- Corroborated by a concurrent live Claude Code session: Claude Code v2.1.179, Sonnet 4.6, running from `~/.openclaw/docs`, a 12-line `CLAUDE.md` present, a `claude-api` skill loading, and confirmed running on the claude.ai OAuth subscription with no `ANTHROPIC_API_KEY` set (subscription path, not API billing).

Key Outcome:

- The documentation mirror is now integrated across mirror + git + private remote + agent pointers — the close-out of the track that had been pending since "Mid Git Setup."
- Related VM snapshot: "klaw-machine - (6/21/2026 - 1:06:54 AM) - Github and Docs integration Launched" (see registry above).
- Note: this entry was recorded via claude.ai chat at Brian's direction; the precise closed items (remote push, daily mirror cron, AGENTS.md + CLAUDE.md pointers) should be confirmed against the Roadmap note's "Close Out the Documentation Mirror" checklist.

### June 27, 2026 — Second Telegram Bot (Copper Kettle) + Agent Hygiene, Mem Governance & Local Backup

Two-part session. First, the Copper Kettle build (full detail in Model Strategy & Orchestration): a second Telegram bot `gemma-telegram` (@CopperKettleBot) pinned to `amethyst-ollama/gemma4:31b`, via a dedicated `telegram:gemma` account + binding; per-account token key is `botToken` (SecretRef from `~/.openclaw/.env`); a new `.env` var needs a full gateway restart. VM snapshot "klaw-machine - (6/27/2026 - 7:18:40 PM) - Copper Kettle up and other stuff" captures this state (see registry).

Then a Claude Code session migrating active work off claude.ai chat:

- **Honesty directive** added to `main`/Kettle `SOUL.md` (anti-confabulation; grounding over instruction).
- **Mem write-permission gate (Fix A)** across all agents' AGENTS.md: reads scoped to OPENCLAW PROJECT, no writes without Brian's per-update approval (drafts to `mem-pending.md` when away); Debater-B set to never write. Token-level scoping found unavailable in mem.ai's API; collection-filtering MCP proxy deferred to Roadmap (Fix B).
- **Kettle exec gating:** `agents.list[].tools.deny: ["group:runtime"]` (blocks exec/process/code\_execution; it had tried to run a pasted shell snippet). Gateway restarted to apply.
- **Agent hygiene:** removed a stray blank `workspace/main/` bootstrap artifact; cleaned the contaminated Debater-B workspace.
- **Local Mem backup:** `scripts/mem_backup.py` (stdlib, tracked), weekly cron (Sun 3:30 AM), keeps last 10 snapshots of the collection to `~/.openclaw/mem-backups/`; git-ignored output. Detail in the Documentation note.
- **Roadmap additions:** Mem Collection Integrity/Synthesis check (CC+Opus, cost-gated) and the Mem-scope MCP filtering proxy; plus a standing decision: no unattended Claude Code automation until strict cost controls exist.

Key Outcome: Kettle is live and exec-gated; project memory has a soft write-governance layer + a local backup floor; this session's facts folded into the canonical notes.

***

## Future Entries

When a milestone is reached, add a concise entry to **Milestone History** whenever:

- major architecture changes occur
- major discoveries are made
- milestones are reached
- project direction changes
- significant issues are resolved

When a Hyper-V checkpoint (VM snapshot) is captured, add it to the **VM Snapshot Registry** with its name, date, and captured state — and cross-reference it from the related milestone entry.
