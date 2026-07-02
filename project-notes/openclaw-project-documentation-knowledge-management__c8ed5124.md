---
mem_id: c8ed5124-c0c6-4f21-aaf1-b32baaacdeb8
title: "OPENCLAW PROJECT \u2014 Documentation & Knowledge Management"
created_at: 2026-06-13T04:57:29.174Z
updated_at: 2026-06-28T02:55:13.991Z
source: mem:OPENCLAW PROJECT
---

# OPENCLAW PROJECT — Documentation & Knowledge Management

## Current Status

Active. **2026-07-01: project memory migrated OFF Mem to local git-tracked markdown at `~/.openclaw/project-notes/`; agents severed from Mem; Mem-specific sections below are retained as history and annotated where superseded. The initial whole-corpus docs digest is IN FLIGHT (chunked via `digest_chunk.sh`; see the Digest section + Roadmap).** Governance model complete. Documentation mirror DEPLOYED and operational (ETag-based incremental). The previously-pending close-out items (private GitHub remote, committed mirror script + nightly wrapper, daily system-crontab cron, both agents pointed at the mirror) were all done 2026-06-20. **As of 2026-06-21 the docs-mirror track is FULLY CLOSED:** the 3:15 AM cron is confirmed firing unattended, and the ETag conditional caching is verified working (back-to-back run → 687 unchanged). Closed ≠ unmonitored — see "Mirror — Ongoing Monitoring." Corpus \~689 discovered pages (was 684). **Next workstream on this note: the Documentation Digest (whole-corpus distillation), planned as a WEEKLY Claude-Code/Opus process — see that section below.**

## Last Updated

2026-07-01

## Key Decisions

- Hybrid documentation strategy: openclaw docs command for fast lookups, English-only mirror for deep research.
- OpenClaw must not search all Mem notes — memory scope restricted to OPENCLAW PROJECT collection only.
- Daily incremental updates preferred for documentation mirror due to rapid OpenClaw development pace.
- English-only mirror — previous mirror attempts downloaded all language variants, wasting storage.
- Conditional caching uses ETag / If-None-Match, NOT If-Modified-Since. The docs server (CDN) returns an ETag but no Last-Modified header, so date-based conditional requests never produced 304s. ETag-based requests do.
- Mirror output (`~/.openclaw/docs/`) is regenerable and should be git-ignored; only the script (`mirror_openclaw_docs.py`) is version-controlled.
- Agents do not consult the mirror automatically — they must be pointed at it: Klaw via AGENTS.md, Claude Code via a CLAUDE.md in `~/.openclaw`.
- Legacy notes are kept and marked \[LEGACY NOTE - CONSOLIDATED], not deleted.
- **Git repository strategy (decided 2026-06-20) — see the dedicated section below. One-line version: the **`klaw-konfig`** repo is for AUTHORED TEXT only (configs, scripts, docs you write); generated/large/binary content (the docs mirror, model weights, VHDX images, datasets, logs) NEVER goes in git; each real application gets its OWN repo.**
- **Mirror left AS-IS re: full re-fetches after a redeploy (decided 2026-06-21).** Redeploys appear to rotate the CDN's ETags, forcing an occasional near-full re-fetch even when content is unchanged. This is harmless (git-ignored output, errors=0, \~6 min overnight). Levers considered and explicitly deferred: content-hash sidecar, gzip request encoding, concurrency/lower delay. Not worth the effort for now.
- **Docs mirror is closed but NOT forgotten (2026-06-21).** Keep a light periodic check-in on mirror health — see "Mirror — Ongoing Monitoring." Closed means feature-complete, not unattended.
- **Digest production runs on a FRONTIER model via Claude Code, NOT a local model (2026-06-21).** Brian wants frontier-grade reasoning (Opus) for the distillation and analysis. The subscription-covered path is Claude Code headless (`claude -p --model opus`) authenticated with the subscription OAuth token; OpenClaw's own `anthropic/claude-opus` provider can NOT use the subscription (ToS restricts OAuth auth to Claude Code / Claude.ai), so that route would require a pay-as-you-go API key. Cadence: WEEKLY. Full mechanism + billing caveat in the Digest section.
- **Two-layer memory model (decided 2026-06-21).** OpenClaw's native memory and Mem (mem.ai) are NOT competing — they do different jobs. (1) **OpenClaw native memory** (workspace Markdown — `MEMORY.md`, `memory/YYYY-MM-DD.md`, `memory_search`/`memory_get`) = the agent's OPERATIONAL recall: local, fast, no network round-trip, per-agent, and INTRINSICALLY scoped (it physically can't leak other projects). (2) **Mem via MCP** = the curated, cross-tool, durable PROJECT KNOWLEDGE BASE: readable/writable by Claude Code + Klaw + ChatGPT + claude.ai chat, with collections/versioning/semantic search/human UI, and it SURVIVES VM rebuild/reseed (cloud-hosted) — which native workspace memory does not. Using Mem for the curated KB is the right call, NOT a disservice. The thing to verify: Klaw should actually USE native memory for operational recall rather than routing every recall through Mem MCP (which adds tokens/latency and inherits the cross-contamination problem). The memory-scope-restriction requirement (below) is intrinsic to Mem because it's a shared store; native per-agent memory needs no scoping. Full reasoning context lives in this conversation's analysis.

## Summary

The knowledge management system uses a structured collection in Mem with subject notes under the OPENCLAW PROJECT — prefix. The governance model, naming convention, lifecycle rules, and update rules were designed in June 2026. The migration from legacy source notes to subject notes was completed on June 13, 2026. The English-only documentation mirror was implemented and verified on June 13, 2026, put under git version control with a private GitHub remote and a nightly auto-refresh cron on June 20, 2026, and fully verified (cron + caching) on June 21, 2026. It is operational. The next documentation workstream is the whole-corpus Documentation Digest (weekly, Claude Code + Opus). Memory is treated as two layers: OpenClaw native (operational) + Mem (curated cross-tool KB).

***

## Memory Architecture

### Collection

Name: OPENCLAW PROJECT\
Purpose: All OpenClaw project notes. Excluded from general Mem searches that OpenClaw performs for other purposes.

### Note Naming Convention

All project notes use the prefix: `OPENCLAW PROJECT —`

### Note Structure

```
MASTER
│
├─ Architecture
├─ Networking & Infrastructure
├─ Configuration & Models
├─ Performance Investigations
├─ Documentation & Knowledge Management  ← this note
├─ Roadmap & Future Development
├─ Model Strategy & Orchestration
├─ Checkpoints & Change Log
│
└─ Archives (future)
```

### Two Layers: native OpenClaw memory vs the curated KB (decided 2026-06-21; layer 2 re-homed 2026-07-01)

**UPDATE 2026-07-01: layer 2 (the curated cross-tool KB) moved from Mem to local git-tracked markdown at `~/.openclaw/project-notes/`.** The two-layer MODEL stands — operational agent memory vs curated project KB remain distinct jobs — but the KB's Mem-specific properties changed: cross-tool access is now "anything that can read the filesystem" (Claude Code natively; local agents once the fs-read grant lands; claude.ai chat NO LONGER has direct access — it lost read/write when Mem was severed); versioning is now git (better than Mem's); semantic search is gone (grep/structure instead); "survives VM rebuild" is now covered by the GitHub push, not cloud hosting. The scoping problem intrinsic to Mem's shared store is eliminated. Original reasoning below retained as history:

Two distinct memory systems with different jobs — keep them straight:

- **OpenClaw native memory** = plain Markdown in the agent workspace (`MEMORY.md` long-term, `memory/YYYY-MM-DD.md` daily notes, optional `DREAMS.md`), indexed for `memory_search`/`memory_get`, agent-managed (the agent distills daily notes into MEMORY.md, e.g. via the heartbeat flow). Properties: **local, fast, zero network round-trip, per-agent, intrinsically scoped** (it cannot leak other projects because it's just that agent's files). Pluggable backends exist (exclusive memory slot: memory-builtin / memory-lancedb (vector) / memory-wiki / honcho / qmd / Cortex knowledge-graph). This is the right home for the agent's OPERATIONAL recall.
- **Mem (mem.ai) via MCP** = this collection — the curated, durable PROJECT KNOWLEDGE BASE. Advantages native memory can't match: **cross-tool** (Claude Code on the VM, Klaw, ChatGPT, and claude.ai chat all read/write the same store), structured collections, versioning, semantic search, a human UI, and it **survives VM rebuild/reseed** because it's cloud-hosted (relevant to the 5090 golden-image plan). This is the right home for the curated KB.
- **Not a disservice to use Mem** — they're complementary. The disservice would be using Mem to REPLACE operational memory (latency/tokens/API dependency per recall, plus cross-contamination exposure). Open verification: confirm Klaw is actually writing/reading native memory for operational recall, not leaning 100% on Mem MCP.
- Note: OpenClaw memory is action-policy-aware (docs: "Memory can preserve approval context, but it does not enforce policy. Use approval settings, sandboxing, and scheduled tasks for hard operational controls.") — i.e. don't treat a memory note as an enforcement mechanism.

***

## Knowledge Lifecycle

### Tier 1 — Current State

Contains current architecture, configuration, decisions. Read first.

### Tier 2 — Decision Record

Contains why decisions were made, alternatives considered.

### Tier 3 — Archive

Contains historical investigations, old configurations, superseded approaches. Read only when needed.

***

## Governance Rules

### Update Rules

**Minor updates** (may be automatic, must be logged):

- Model changes
- Version changes
- Verified configuration changes

**Major updates** (must be proposed first, require approval):

- Architecture changes
- Governance changes
- Restructuring
- Deletions

### New Subject Creation

Currently: proposal only. OpenClaw may propose a new subject note (e.g., OPENCLAW PROJECT — Firecracker Research), but human approval is required before creation.

### Active Note Hygiene

Every active note should contain a Recent Updates section.

When active notes become too large:

1. Preserve current state and decisions.
2. Move historical details to archive note.
3. Update summary.
4. Add checkpoint if significant.

### Archive Strategy

Archive notes are separate from active notes:

- `OPENCLAW PROJECT — Architecture`
- `OPENCLAW PROJECT — Architecture Archive`

Archive structure: Summary + Detailed Historical Information.

### Legacy Note Strategy

Legacy notes are kept. Mark with: `[LEGACY NOTE - CONSOLIDATED]`. Do not delete. Review for retirement later.

***

## Git Repository Strategy (decided 2026-06-20)

The standing convention for what goes in version control and how repos are organized.

### The repo

- `klaw-konfig` — PRIVATE GitHub repo (`git@github.com:millsio/klaw-konfig.git`), the operational source-of-truth for the OpenClaw setup on KlawMachine. Local working tree is `~/.openclaw`.
- Access from KlawMachine uses a **repo-scoped deploy key** (`~/.ssh/openclaw_deploy`, write access), reached via an SSH host alias `github-openclaw` in `~/.ssh/config` — so the git remote URL is `git@github-openclaw:millsio/klaw-konfig.git`, NOT `git@github.com:...`. A deploy key is scoped to this one repo, so a KlawMachine compromise can't reach the rest of the GitHub account. GitHub auth (adding the deploy key) is done by Brian in the browser, never by an agent.
- Tracked files (deny-by-default `.gitignore` with explicit per-file allows): `.gitignore`, `scripts/mirror_openclaw_docs.py`, `scripts/nightly.sh`, `AGENTS.md`, `CLAUDE.md`. Initial commit `4e844d2`; agents-files + nightly-wrapper commit `afb0d8b`.

### What goes in git vs not (the rule)

- **In git:** authored text only — configs you write, scripts, docs you author, and (optionally, future) a REDACTED config template (`openclaw.json.example` with all secrets stripped).
- **NEVER in git:** anything generated, large, or binary — the docs mirror output (`~/.openclaw/docs/`, regenerable), model weights, VHDX images, datasets, logs, debate transcripts/digests (generated), and all secrets (`openclaw.json`, `credentials/`, `identity/`, sqlite stores).
- Rationale + limits: GitHub HARD-blocks any single file >100MB (warns at 50MB); a repo should stay under \~1GB; git history is PERMANENT. Keeping heavy/binary content out entirely avoids all of this.

### Repo-per-project

- The dividing line is "is this a distinct project with its own lifecycle/dependencies/release cycle?" — NOT "is this a different topic."
- Infrastructure glue (configs, deploy scripts, cron) = the single `klaw-konfig` ops repo.
- Each real application (trading-assist tooling, a RAG/vector pipeline, a custom agent/service, the digest pipeline, the debate-council driver) = its OWN new repo, created the day that work starts. Generated OUTPUT (digest, debate transcripts) stays git-ignored.

### .gitignore discipline

- Deny-by-default: starts with `*` then allows specific paths with `!path`. NEVER a broad wildcard allow.
- Before any commit: `git add -A; git status` (confirm only intended files staged) and `git check-ignore -v openclaw.json credentials identity`.

***

## Nightly Auto-Refresh + Push (deployed 2026-06-20)

### Wrapper script

- `~/.openclaw/scripts/nightly.sh` (tracked, `chmod +x`). Refresh the docs mirror (logging to `docs/.mirror_log.txt`), then `git add -A`, and commit + push ONLY if a tracked file changed (`git diff --cached --quiet` gate). Push uses inline `GIT_SSH_COMMAND="ssh -i ~/.ssh/openclaw_deploy -o IdentitiesOnly=yes"` so cron's stripped environment finds the deploy key.
- Because the mirror is git-ignored, a normal night where only mirror content changed produces NO commit — correct, not a failure.

### Cron

- SYSTEM crontab: `15 3 * * * /home/klaw/.openclaw/scripts/nightly.sh` (3:15 AM daily). Chose plain crontab over `openclaw cron` (simpler, no gateway dependency). NOTE: `openclaw cron` is actually richer than first assumed (persistent SQLite jobs, run history, isolated agent-turn execution, chat delivery) and is the better home for AGENT-TURN jobs like the heartbeat doc task — but the mirror is a plain script, so system cron is right for it.
- Hand-tested 2026-06-20: exit 0; \~6 min full pass; no tracked change → no commit. A full pass logs only to file, so the terminal looks idle — normal, not a hang.

### Cron — CONFIRMED unattended (2026-06-21)

- `crontab -l` shows the line. `.mirror_log.txt` has a full run 2026-06-21 03:15:01 → 03:21:04 (fetched=684 unchanged=5 errors=0). Nobody runs it by hand at 3:15 AM → proves cron fires unattended and the cron-stripped env resolves `python3` + the deploy-key path.

***

## ETag Conditional Caching — verified working (2026-06-21)

- Back-to-back run produced fetched=2 / unchanged=687 — proves the script's `.etag` sidecar read/write + conditional requests work.
- `cli.md` ETag (`b0b6c370738badd70e1c78f8f4c40774`) stable across requests, matched the sidecar.
- High fetch counts on gap-runs = upstream churn + apparent ETag rotation on docs-site redeploys — NOT a bug. errors=0 throughout.
- Open low-priority question: content-derived vs build-derived ETag. Test = note an ETag, re-check after a confirmed docs deploy.
- Decision: keep the mirror as-is.

***

## Mirror — Ongoing Monitoring (closed, not forgotten) — 2026-06-21

Light periodic check-in so silent failures don't accumulate:

- Tail `~/.openclaw/docs/.mirror_log.txt`: confirm a recent \~03:15 entry and `errors=0`.
- Watch the discovered-page count for a sudden DROP (would suggest `llms.txt`/structure changed and the mirror is under-fetching).
- After any OpenClaw docs-site redesign, re-confirm the `.md` endpoint + `llms.txt` index still work.
- Natural candidate for the planned Heartbeat Documentation Task (automate the check via `openclaw cron`).

***

## Documentation Strategy

### Fast Path: openclaw docs command

Advantages: current, no maintenance, fast targeted lookups. Limitations: retrieval may miss adjacent concepts; "doesn't know what it doesn't know."

### Deep Research Path: English-only documentation mirror

Mirror target: docs.openclaw\.ai. English only. Daily incremental (cron, 3:15 AM). Advantages: full corpus for local search/indexing; better for architectural understanding; supports RAG/indexing/digest workflows. Status: OPERATIONAL since 2026-06-13; auto-refreshing nightly since 2026-06-20; cron + caching verified 2026-06-21. \~689 pages.

***

## Documentation Mirror — Operational Details (2026-06-13; updated 2026-06-21)

### Script

- Path: `~/.openclaw/scripts/mirror_openclaw_docs.py`. Stdlib-only Python 3 (urllib), no pip deps. Written 2026-06-13 via Claude Code, validated against the live site. Version-controlled in `klaw-konfig`.

### What it does

- Fetches `docs.openclaw.ai/llms.txt` to discover pages (`[title](url)`).
- Downloads each page as Markdown via the `.md` endpoint.
- Skips non-English paths and asset/non-page extensions (incl. `.xml`/`.txt`).
- Resolves site root to `index.md`.
- ETag / If-None-Match caching via `page.md.etag` sidecars; 304 = unchanged.
- Writes `INDEX.md` (titles + local paths). Logs to `.mirror_log.txt`. 300 ms politeness delay.

### Output

- `~/.openclaw/docs/` — `.md` pages mirroring site structure + `.etag` sidecars + `INDEX.md`. \~689 pages (was 684 on 2026-06-13).

### Verified runs

- 2026-06-13 first: fetched=684, unchanged=0, errors=0.
- 2026-06-13 second: fetched=1, unchanged=683, errors=0.
- 2026-06-20 (nightly wrapper, hand-tested): discovered=689, fetched=686, unchanged=3, errors=0.
- 2026-06-21 cron (unattended, 03:15): discovered=689, fetched=684, unchanged=5, errors=0.
- 2026-06-21 back-to-back: run A 677/12, run B 2/687 — caching confirmed.

### NOTE — OpenClaw ships its own agents-file templates

Mirror includes `reference/templates/CLAUDE.md` and `reference/AGENTS.default.md`. Worth aligning our hand-written AGENTS.md/CLAUDE.md to their structure later.

### Bugs found and fixed during validation (2026-06-13)

- `robots.txt`/`sitemap.xml` got `.md` appended → fixed (skip `.xml`/`.txt`).
- Bare root fetched HTML → fixed (resolve root to `/index.md`).
- Last-Modified/If-Modified-Since never worked (no Last-Modified header) → switched to ETag.

### How it is consumed

- Claude Code: runs in `~/.openclaw`, reads `docs/` + `INDEX.md`; pointed via `CLAUDE.md`.
- Klaw: reads same files; AGENTS.md carries a "Local Documentation Mirror" pointer.

***

## Future: Documentation Digest (whole-corpus distillation) — PLANNED (weekly)

Goal: periodically distill the mirror into a **dense but detail-rich** version of the entire docs that Klaw/Claude Code can **load entirely into context** for a comprehensive whole-corpus view (yields insights ad-hoc section queries miss). Distinct from RAG (chunked retrieval) and the mirror (full fidelity) — whole-corpus comprehension via compression.

### Target format (from the prototype)

- Dense **\~5:1** digest of the combined corpus (\~690 pages / \~164k lines / \~7 MB → tens of KB).
- Preserves: config keys, defaults, file paths, CLI commands, tool/hook names, edge cases. Drops: prose, repeated examples, marketing.
- Built section-by-section in index order. \~149 `plugins/reference/*` stubs collapsed into one catalog table.
- Companion artifacts: a master-index map + a SAMPLE digest (concepts/memory cluster). Prototype files in a Claude chat project: `openclaw-digest-FULL.md` (in progress — only plugins batch 1 of 10/690 done), `openclaw-docs-combined.md` (7 MB source).

### Cadence (decided 2026-06-21)

- WEEKLY, off the already-mirrored content (no extra fetching).

### Production engine (decided 2026-06-21)

- Frontier (Opus), NOT local. Vehicle = Claude Code headless (`claude -p --model opus`), subscription-OAuth-authenticated, NOT OpenClaw's anthropic provider (ToS). Ensure `ANTHROPIC_API_KEY` is unset in that env (else pay-as-you-go).
- BILLING CAVEAT (verify against current policy — flip-flopped in 2026): as of 2026-06-15, headless `claude -p` draws from a separate monthly Agent SDK credit (Max 20x = $200/mo at API rates), not the interactive pool; stops when exhausted unless overflow enabled. Weekly low-frequency should fit.
- Chunked production is mandatory (corpus >1M tokens won't fit one context); analysis below is single-pass.

### Companion artifact: Digest Analysis / Insights reference (added 2026-06-21)

- A SECOND reference: an ANALYSIS of the finished digest — cross-cutting insights/patterns/gotchas only visible whole-corpus. Cheap: the finished digest fits one Opus context → single-pass. Generate right after each weekly build. Output git-ignored.

### Open design questions (remaining)

- Section-by-section loop orchestration + where the driver lives (candidate for its own repo).
- Runtime consumption: file pointer short-term; longer-term a `registerContextEngine` plugin could inject digest + master-index as first-class context.
- Snapshot/version successive weekly digests (week-over-week diff) vs overwrite.

***

## Desired OpenClaw Knowledge Workflow

```
Question
→ Read OPENCLAW PROJECT notes at ~/.openclaw/project-notes/ (INDEX.md → MASTER → subject notes)
→ Search OpenClaw documentation (docs command or local mirror; whole-corpus digest when it exists)
→ Check live system state when needed
→ Answer
→ Update project notes when appropriate
```

_(Updated 2026-07-01: was "Search OPENCLAW PROJECT notes in Mem" pre-migration.)_

***

## Memory Scope Requirement — ✅ RESOLVED BY MIGRATION (2026-07-01)

**The problem class was eliminated on 2026-07-01: agents were fully severed from Mem (no Mem tools, no token), so there is nothing left to scope.** The successor concern is scoping the planned filesystem-read grant for local agents (secrets locked down first — see the Pilot note and Roadmap). Original requirement and the Fix A/Fix B history retained below:

OpenClaw must not search all Mem notes by default.

Desired behavior:

- Restrict memory searches to OPENCLAW PROJECT collection notes only.
- Exclude personal notes, financial notes, travel notes, and other projects.

This is an MCP-FILTERING requirement (the Mem API supports `filter_by_collection_ids`), NOT a re-architecture: make Klaw's Mem tool calls always pass the OPENCLAW PROJECT collection filter (via AGENTS.md/system-prompt instruction or a thin wrapper). It is intrinsic to Mem because Mem is a shared store (it also holds personal/financial/travel notes); OpenClaw native per-agent memory does not have this problem. Not yet implemented at the OpenClaw level.

**UPDATE 2026-06-27 — Fix A (policy layer) IMPLEMENTED; Fix B pending.** A per-agent write-permission gate now lives in each agent's workspace AGENTS.md: reads are scoped to the OPENCLAW PROJECT collection and there are NO Mem writes without Brian's explicit per-update approval (drafts go to a local `mem-pending.md` when Brian is unavailable). `main` (Klaw) and `gemma-telegram` (Kettle) carry the gate; `gemma-amethyst` (Debater-B) is set to never write. This is a soft (instruction-level) guard. Token-level scoping was investigated and appears UNAVAILABLE in mem.ai's API (only account-wide Bearer auth is documented); the hard backstop — a collection-filtering MCP proxy or a dedicated Mem account — is on the Roadmap as a defense-in-depth enhancement.

***

## Future: Local Indexing / RAG

Local indexing of the mirror may be explored after the mirror is operational ✓ and memory-scope restriction is implemented. Not a current priority. (The Documentation Digest is a separate, higher-interest direction — whole-corpus distillation rather than chunked retrieval.)

***

## Agent Workspace Hygiene, Mem Write Governance & Local Backup (2026-06-27)

Findings and changes from a Claude Code working session.

### Agent bootstrap ritual (confirmed real)

A brand-new empty workspace causes OpenClaw to seed `BOOTSTRAP.md` — a one-time first-run identity ritual, auto-injected alongside the other bootstrap basenames (`AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `HEARTBEAT.md`, `MEMORY.md`, `TOOLS.md`). It is kept in Project Context until the ritual completes, then self-deletes; a state-dir attestation marker prevents silent re-seeding.

- **Mem pollution risk from the ritual:** Kettle's ritual created two **uncollected** Mem notes ("Identity - Copper Kettle", "User - Brian") at Mem root — outside OPENCLAW PROJECT (curated KB not polluted, but it shows the scope gap is about WRITES, not just searches). Both were trashed.
- **Debater-B (gemma-amethyst) was contaminated:** it had run the same ritual and carried a persona, with `BOOTSTRAP.md` still present. Cleaned: `BOOTSTRAP.md` removed; `SOUL.md`/`IDENTITY.md` replaced with the neutral "rigorous peer reviewer" stance from the Debate Council design.
- **Stray bootstrap artifact:** a blank, never-completed `~/.openclaw/workspace/main/` subdirectory was removed (Klaw's real workspace is `~/.openclaw/workspace`).
- **Local-model tool-discipline issues on gemma4 (Kettle):** degenerate/empty `web_search` queries; emoji byte-escape artifacts; a brief language leak; reasoning/tool narration in the visible channel; and attempting to EXECUTE a pasted shell one-liner (a live tool-safety illustration). Mitigation: exec/runtime tools denied for Kettle (see Model Strategy note). `/stop` aborts an in-progress run from the channel.

### Honesty directive

A standing anti-confabulation directive was added to `SOUL.md` for `main` and `gemma-telegram`. Honest caveat: a prompt directive reduces but does not eliminate confabulation on a Q4 local model — the durable lever is grounding (forced lookup + citation), not instruction alone.

### Local Mem backup — RETIRED 2026-07-01

`scripts/mem_backup.py` (weekly cron, keep-last-10 snapshots to `~/.openclaw/mem-backups/`) was the point-in-time safety net for the Mem-hosted collection. Retired with the Mem→local cutover: the notes are now local files under git, pushed to the private remote — continuous version history, no snapshot script needed. Script, cron, and `mem-backups/` all removed 2026-07-01.

***

## Recent Updates

- 2026-06-13: Note created. Legacy → subject-note migration completed.
- 2026-06-13: Mirror implemented and verified via Claude Code (684 pages; second run 683 unchanged). Two bugs fixed; switched to ETag caching. OPERATIONAL. Cron/git/pointers pending.
- 2026-06-20: Closed out pending docs-mirror items — private GitHub remote via deploy key + `github-openclaw` alias (`4e844d2` → `afb0d8b`); wrote+committed AGENTS.md/CLAUDE.md; wrote `nightly.sh` + system crontab at 3:15 AM; hand-tested green. Recorded Git Repository Strategy. \~689 pages.
- 2026-06-21: **Docs-mirror track fully closed.** Cron CONFIRMED unattended; ETag caching CONFIRMED (back-to-back run B = 2/687); gap-run re-fetches = churn + redeploy ETag rotation, not a bug. Mirror left AS-IS. Logged the Documentation Digest workstream.
- 2026-06-21 (cont.): Mirror closed-but-monitored (added Ongoing Monitoring); Digest cadence WEEKLY; production = frontier Opus via Claude Code headless (with billing/ToS caveats), chunked production / single-pass analysis; added Digest Analysis companion artifact.
- 2026-06-21 (cont. 2): Added the **two-layer memory model** decision + a "Two Layers" section — OpenClaw native memory (operational, local, fast, intrinsically scoped) vs Mem via MCP (curated, cross-tool, durable KB); using Mem for the curated KB is correct, not a disservice; open item is to confirm Klaw uses native memory for operational recall. Reframed the Memory Scope Requirement as an MCP-filtering task (Mem `filter_by_collection_ids`), intrinsic to Mem's shared-store nature.
- 2026-06-27: Recorded a Claude Code session — agent bootstrap-ritual findings + Mem write-pollution cleanup; the honesty directive (main + Kettle SOUL.md); the per-agent Mem write-permission gate (Fix A, see Memory Scope Requirement update) with Fix B (token/MCP-proxy scoping) deferred to Roadmap; and a new local Mem backup system (`scripts/mem_backup.py`, weekly, keep-last-10). Added the "Agent Workspace Hygiene, Mem Write Governance & Local Backup" section.
- 2026-07-01: **Post-migration reconciliation (Claude Code).** Annotated this note for the Mem→local cutover: curated-KB layer re-homed to `~/.openclaw/project-notes/` (two-layer model stands, layer-2 properties updated — git versioning, no semantic search, claude.ai chat loses direct access); Memory Scope Requirement marked RESOLVED BY MIGRATION (agents severed; successor concern = scoping the future fs-read grant); Desired Knowledge Workflow repointed at local notes; `mem_backup.py` marked retired. Digest status: initial whole-corpus build in flight (see Roadmap).
