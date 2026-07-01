---
mem_id: d7f6579b-be74-4b6c-bdf9-7c4235fe4f78
title: "OPENCLAW PROJECT \u2014 Pilot: Multi-Agent Advancement Discussion (2026-06-29)"
created_at: 2026-06-30T02:03:11.050Z
updated_at: 2026-07-01T06:19:56.166Z
source: mem:OPENCLAW PROJECT
---

# OPENCLAW PROJECT — Pilot: Multi-Agent Advancement Discussion (2026-06-29)

## Current Status

Security finding resolved; on the improved design — agents review the collection via their own read-only Mem tools (no filesystem read, no Python dossier). Hardening done: Mem key rotated + SecretRef-migrated, `controlUi.allowInsecureAuth` off, weigh-in runs tool-less, secret-scan guard live. Re-validating via a short smoke before the full 45-min run. Checkpoint: "klaw-machine - (6/30/2026 - 1:25:53 AM) - working on autonomous loops".

## Last Updated

2026-06-29

## Purpose

A bounded, supervised pilot toward a more autonomous OpenClaw system. Two local models — qwen3.6:27b (`main`, pacifico/3090) and gemma4:31b (`gemma-amethyst`, amethyst/5090) — review the entire OPENCLAW PROJECT Mem collection (full verbatim notes, read on demand from `~/.openclaw/council/notes/`), then collaborate over \~45 minutes on how best to advance the project, with live web search. Claude Code (headless `claude -p --model opus`, off OAuth) weighs in 3 times to assess progress and steer the next segment. Orchestrated by `scripts/council_pilot.py`, terminal-streamed.

## Design / Guardrails

- 3 segments x \~15 min, same session keys throughout (continuity); hard caps on rounds + timeouts.
- Attended (Brian present); NOT an unattended cron/systemd loop — inside the "attended use is fine" carve-out of the cost-gate decision (see Roadmap).
- Claude Code authors each weigh-in; the orchestrator persists a NOTE\_UPDATE block here via Mem REST.

## Smoke-Test Findings (2026-06-29, before the full run)

Two validation smokes via `scripts/council_pilot.py`:

1. **Run 1 (null):** qwen's turn hit the gateway's \~330s ceiling and died; gemma then engaged the crash log instead of the project. Orchestrator fixes applied: liveness guard (a dead peer no longer poisons the partner), configurable per-turn timeout, time-as-primary-limiter, and lighter on-demand note reading (MASTER pinned + read specific notes as needed).
2. **Run 2 (collaboration worked — but a security incident):** both models stayed alive and produced a grounded security plan. HOWEVER, with a newly-granted `read` tool, qwen read `openclaw.json` and printed the live Mem API key into the transcript while discussing how to secure it; neither model noticed. The Opus weigh-in caught it.

**Incident actions:**

- The leaked token was scrubbed from local transcripts; it did NOT reach this cloud note or git, but it WAS transmitted to external APIs (the `claude -p` weigh-in prompt) — treat it as compromised and rotate the Mem API key.
- The `read` grant was reverted (agents can no longer read the secret-bearing config), pending a SecretRef migration that moves secrets (Mem token + gateway token) out of `openclaw.json`.
- Verdict reinforced: keep attended. Two smokes, two silent self-inflicted failures (continuity loss, then a secret leak) — the council cannot yet detect its own mistakes. Add a secret-scan guard on council output before printing/persisting.

## Future Direction

- Filesystem `read` for the council agents is deferred, NOT abandoned. Once secrets are systematically locked down (all secrets moved to SecretRef / out of any readable config, plus a scoped fs or sandbox policy so agents cannot reach `.env` or any credential file), the agents should be able to read the real filesystem — configs, scripts, logs, the live system — not just Mem. Rationale (Brian, 2026-06-30): deep self-awareness and genuine DISCOVERY are part of the goal; curated Mem notes cannot tell the whole story, so the agents need the opportunity to inspect reality and surface what the notes miss.

## Operational Notes

- For extended council runs, monitor GPU health (temperature, VRAM, power) on BOTH hosts — pacifico (3090, qwen) and amethyst (5090, gemma) — since sustained back-to-back generation runs them hot. The Model Strategy note already flags a thermal re-check for sustained/24-7 autonomy (incl. VRAM junction temp); these multi-segment pilots are exactly that load. Watch `nvidia-smi` on each host during long runs. (Noted by Brian, 2026-06-30.)

## Discussion Log

_(Cleared of smoke-run weigh-ins. The real run will append fresh round summaries here.)_

### Round 1 — Claude Code weigh-in

**What happened in segment 1:** After a strong, grounded opening synthesis (qwen correctly re-derived the Roadmap priority order), the council spent the entire segment — 12 rounds + a DEEPEN phase — on a single mid-priority item: safely connecting Claude Code to Mem MCP when Mem offers no scoped/read-only tokens. They converged on: (1) `sudo -l` **Privilege Audit** as the first step of Priority 1; (2) an **mcproxy** denylist that blocks write tools (`create/update/add/move/remove`), since `autoRegister` can't be disabled and token scoping is unavailable \[GROUNDED: Roadmap]; (3) a root-owned, `chattr +i` immutable filter config at `/etc/mcproxy/`; (4) sequencing Claude Code integration strictly _after_ Priority 1. A concrete artifact (config, hardening commands, acceptance test, rollback) was produced.

**Genuinely valuable:** the principle that any agent-writable config is not a security boundary (soft `.clinerules`/CLI flags are preferences, not guarantees); the capability-vs-approval distinction; the cheap high-signal `sudo -l` audit.

**Problems I flagged:**

- **The design reintroduces the June-30 leak class:** the Mem token lives in plaintext in agent-readable `.mcp.json`, not SecretRef'd. They hardened the _filter_ file but left the _token_ readable. Fix the secret, not just the write blast radius.
- **The guardrail fails OPEN:** on a Mem server version bump the proxy treats it as a new server and auto-registers all tools — silently re-enabling writes. That is not the "capability-based guarantee" claimed. Make it fail-closed or drop the claim.
- **Shaky sources:** `fast.io/.../openclaw-sandbox-guide` and several `mem__*` tool names cited as \[GROUNDED: docs.mem.ai] are unverified — treat as suspect.
- **Scope tunnel:** they answered the mechanics of a task without establishing it was the right task. Priority 1 (sandbox, UFW, endpoint lockdown, SSH) and the _pilot-confirmed_ Debate Council blockers (compaction not engaging → the continuity loss they themselves hit; `/reset` model fallback) went untouched.

**Direction for segment 2:** Exit the mcproxy loop. (1) Re-anchor on the highest-leverage _Priority 1_ unchecked item and design it to equal depth. (2) Close the two holes in the current plan — SecretRef the token; make the proxy fail-closed. (3) Engage Debate Council blockers (A) and (B), which are more central to advancing the project than CC read access. Injected tension: gemma should stop reflexively demoting-to-P4 as a substitute for a decision; qwen should stop treating each one-liner patch as "low cost" when each expands the surface. Verify current state (is CC actually still unlinked from Mem?) before building — roadmap task-lists go stale.

### Round 2 — Claude Code weigh-in

**What happened in segment 2:** The council took the steer and pivoted off mcproxy to Priority 1. qwen stated the honest conclusion plainly — Claude Code ↔ Mem is genuinely downstream of Priority 1 (needs SecretRef + fail-closed proxy + host hardening) — and parked it. Good. They then converged a **host-baseline verification checklist**: `sudo -l` (NOPASSWD audit), `ufw status`/`ss -tulpn` (true listening state, not just firewall config), SSH `PasswordAuthentication no` with a canary-login safeguard on amethyst, and Ollama binding hardening (bind to Tailscale IP, not `0.0.0.0`). Plus a phased sandbox rollout: baseline `network: none` for all agents → identify which need `bridge` → persistent egress floor last; rollout order internal-agents → Klaw → gemma-telegram (the "alarm system") last; per-agent verification matrix.

**Problems I flagged:**

- **Same failure mode, one level over.** A \~12-turn gemma-challenges/qwen-concedes chain spun on egress networking (DOCKER-USER → custom Docker net → systemd one-shot → 0.0.0.0 binding). Scope accretion, not convergence — they never locked a deliverable.
- **The load-bearing claim is self-grounded.** qwen's "tool calls are Gateway-mediated, so `network: none` won't break the council" (S2.7) is tagged \[GROUNDED] but cites no source — it's an inference, and the entire "network: none is safe" plan rests on it. The browser-vs-mediated resolution stacked another assumption on top.
- **Schema drift.** They cite both `networkAccess` (boolean) and `docker.network: none|bridge` from four different URLs. A config artifact built on the wrong schema is dead on arrival.
- **Still open:** the two holes from Round 1 (SecretRef the Mem token; fail-open-on-version-bump proxy) and the Debate Council blockers (A compaction-not-engaging — the exact failure the smoke runs hit — and B `/reset` model-pin) were dropped again, silently. Current state (is CC still unlinked? which OpenClaw version → which schema?) unverified.

**Direction for segment 3 (final):** Stop finding new risks; ship a deliverable. (1) Verify the Gateway-mediation crux _empirically_ on one low-risk agent before building on it — if calls are mediated, delete the entire egress-filtering thread as moot. (2) Reconcile the sandbox schema against the installed OpenClaw version via `openclaw sandbox explain --json`; no config until then. (3) Produce the actual artifact to mcproxy depth: exact `agents.list[].sandbox` block for gemma-telegram, enable command, runnable verification matrix, rollback. The host-baseline checklist is pre-flight, not the deliverable. (4) Make an explicit sequenced decision on Debate Council blockers A/B instead of dropping them a third time. **Tension:** gemma — find the minimum viable secure baseline, not red-flag #13. qwen — stop laundering every challenge into another sub-step; twice you said "we're over-engineering, enable the base first," then kept engineering. Defend a minimal deliverable against further additions.

### Round 3 — Claude Code weigh-in

**What happened in segment 3:** The council delivered. They produced a scoped, hand-to-Brian artifact for the first Priority-1 step — enabling the OpenClaw sandbox on `gemma-telegram` with `docker.network: "none"`, `readOnlyRoot: false`, a `jq` JSON-validation gate, a verification matrix, git-based rollback, and a diagnostics/observability appendix. They resolved the schema question in favor of `docker.network` (string) over the older `networkAccess` (bool). Notably, when gemma re-introduced the DOCKER-USER egress firewall (S3.6), qwen pushed back (S3.7) citing the phased plan and two concrete bugs (DOCKER-USER is global to all host containers; the Amethyst Tailscale IP was an ungrounded `100.x.x.x` placeholder) — and the addition was correctly demoted to a deferred Phase 2 blueprint. Debate Council blockers (A)/(B) and Ollama binding hardening were explicitly deferred rather than silently dropped.

**Genuinely valuable:** first bounded, shippable deliverable of the pilot; qwen holding scope against accretion instead of laundering it into another sub-step; honest provenance flagging (qwen noted he had not read note `f80de520` that gemma cited for gemma-telegram's tool grants); explicit deferrals.

**What I flagged as still shaky:**

- **The central crux was re-asserted, not verified.** "Mediated calls (web\_search/Ollama/Mem) bypass the sandbox, so `network: none` won't break the council" is now grounded in docs rather than the S2.7 bare inference — but it remains untested against the installed build. The artifact's "fully closed-loop / grounded" framing overstates this.
- **Domain drift.** The sandbox schema has been cited across four domains over the pilot (`fast.io`, `github.com/openclaw`, `docs.openclaw.ai`, `openclaw-ai.com`). The `docker.network` choice was never confirmed against the version actually installed via `openclaw sandbox explain --json` on the host.
- **Config field values **`mode: "all"`** / **`scope: "session"`** are asserted, not cited** — possible confabulated schema.
- **The chosen agent can't demonstrate isolation.** gemma-telegram has `exec` denied, so `network: none` is unfalsifiable on it — the matrix proves mediation survives but not that the sandbox contains anything; `sandbox explain --json` only reads the config back.

**Direction given (final):** Treat the artifact as a _well-formed experiment_, not a verified procedure. Step 0 before any edit: run `openclaw sandbox explain --json` on the real host and reconcile the schema — pick what the binary reports, discard the multi-domain citation trail. Name the mediation crux as the one untested load-bearing assumption. gemma: freeze the Phase 2 accretion; its correct input is the Phase 1 _result_, which doesn't exist yet. Resolve one open decision explicitly: is the pilot proving "nothing breaks" (mediation) or "the wall holds" (isolation)? If isolation, add a second check on an `exec`-capable agent. And make the sequencing call on the Debate Council blockers a one-sentence conclusion: sandbox-verify → then clear (A) compaction and (B) `/reset` model-pin _before_ any sustained/unattended council run, since (A) is the continuity-loss failure the smoke runs already hit.

#### Next steps (for Brian)

**Honest read on the pilot:** It worked as a _reasoning-quality_ exercise and produced one genuinely usable artifact — but it did not produce a verified procedure, and the two models still cannot self-correct their two dominant failure modes without the Opus weigh-in. Across three segments the pattern was identical: gemma accretes risks indefinitely, qwen absorbs each one as a new sub-step, and they converge on "we agree" without ever pressure-testing the load-bearing assumption. My steers moved them off it twice, and only in segment 3 did qwen internalize the "hold scope" behavior on his own (S3.7). That's real progress, but it's steered progress — the council is a good _drafting_ engine under supervision, not yet an autonomous one. The recurring grounding smells (four doc domains, uncited config fields, an untested central premise dressed as "GROUNDED") confirm the pilot's own core finding: **keep it attended.** Two smokes gave you two silent self-inflicted failures; this run gave you a plausible-but-unverified config presented with more confidence than it earned. That's a softer failure, but it's the same class.

**What you actually got:** a decent first draft of the sandbox-enablement step, plus a clear map of what's downstream of what (Claude Code↔Mem is genuinely gated on SecretRef + fail-closed proxy + host hardening — that conclusion is sound and worth keeping).

**Concrete next actions I'd recommend, in order:**

1. **Don't apply the artifact as written.** Run `openclaw sandbox explain --json` on pacifico first and reconcile the schema (`docker.network` vs `networkAccess`; confirm `mode`/`scope`/`readOnlyRoot` are real keys) against the installed OpenClaw version. This is a five-minute check that determines whether the config block is even valid.
2. **Run the host-baseline pre-flight** (`sudo -l`, `ufw status`, `ss -tulpn`) — that part is cheap, correct, and useful independent of everything else.
3. **Do the sandbox test yourself, attended,** on gemma-telegram: apply, restart, run the matrix, `docker logs -f` if it hangs. Accept that this proves "mediation survives," not "isolation works." If you want the latter, repeat on an `exec`-capable agent and confirm `curl` from inside fails.
4. **Before any unattended council run, clear Debate Council blockers (A) and (B).** (A) is the compaction/continuity failure your smoke runs already hit — an autonomous loop that loses continuity mid-run is exactly the incident this whole effort is guarding against.

**On pushing toward autonomy:** not yet, and not on the strength of this. The gate isn't model capability — it's that neither model reliably catches its own grounding errors or resists scope drift without an external referee, and the referee here was a frontier model on OAuth, not the local council. If you want to move the autonomy needle, the highest-value next experiment isn't a longer or unattended run — it's giving the council the _filesystem read_ you've been deferring (once secrets are SecretRef'd out of any readable config), so they can verify claims like the sandbox schema against reality instead of drifting across four doc domains. Self-verification against ground truth is the missing capability. Until they can check their own work, keep Opus (or you) in the loop.

### Round 1 — Claude Code weigh-in (run 2026-07-01-020744 — NULL RUN)

**What happened in segment 1 (1 of 1):** Nothing substantive. This is a failed/null run, comparable to smoke Run 1.

- **qwen S1.1 — **`[TURN FAILED]`**, payload **`'result'`**.** The lead model's first turn died at the harness/gateway layer. Reads as an orchestration or response-parsing failure (same class as Run 1's gateway death), not a reasoning outcome. Not diagnosable from the single token.
- **gemma S1.1 — **`PASS`**.** Liveness guard held (gemma did NOT engage a crash log this time — the Run 1 pathology is fixed), but with a dead lead peer on turn one, gemma had nothing to build on and passed. Net segment output: empty.

**Flags:**

- **Orchestration gap:** a first-turn lead failure degrades silently to a null segment. There is no role-swap/restart fallback; the liveness guard prevents _poisoning_ but not _emptiness_.
- **Capability-surface concern (hedged):** the transcript dumps a full harness manifest for the council agent — `WebSearch`, `Agent` spawn, `claude.ai Mem` MCP, and skills carrying `Edit`/`Write`/`Bash`. If that is gemma's real runtime, it contradicts the read-only/tool-less guardrail and should be closed before re-running. May be environment noise — verify.

**Direction:** No reasoning steer possible (no discussion occurred). Before any re-run: (1) diagnose qwen's `'result'` turn-one death in `council_pilot.py` — likely gateway timeout or response-parse miss; (2) add a lead-failure fallback (promote peer to lead, or abort+restart) so a dead turn-one lead doesn't silently yield null; (3) confirm the council agents' actual tool grants against the leaked manifest and re-assert read-only. This run advances the project's _conclusions_ not at all; it does surface a new orchestration bug (turn-one lead death → silent null) worth fixing.

#### Next steps (for Brian)

**Honest read:** This run is a wash — a null/failed run, not a soft failure like the 2026-06-29 three-segment run. qwen's first turn died at the gateway/harness layer and gemma correctly-but-uselessly passed. You got zero discussion. The one genuinely new signal is an orchestration bug the prior run didn't expose: **a lead-model failure on turn one collapses the entire segment silently** — the liveness guard stops the peer from engaging the crash (good, that's the Run 1 fix working), but there's no fallback to keep the segment productive.

**Concrete next actions, in order:**

1. **Diagnose the **`'result'`** failure first — don't re-run blind.** Pull qwen's actual turn-one error from the orchestrator/gateway logs (pacifico). The bare `'result'` string suggests `council_pilot.py` caught an exception or got an empty/malformed response dict and stringified a key. Determine whether it's (a) gateway timeout, (b) response-parse bug, or (c) qwen/Ollama on pacifico erroring. This is a few minutes in the logs and gates everything else.
2. **Add a turn-one lead-failure fallback.** Right now a dead lead → gemma `PASS` → null segment. Either promote gemma to lead, or abort-and-restart the segment. Without this, any transient qwen hiccup wastes a whole run.
3. **Verify the council agents' real tool grants** against the manifest that leaked into this transcript (`Edit`/`Write`/`Bash`/`Agent`/broad MCP). If those are actually reachable by gemma4, that's a guardrail regression that reintroduces the capability surface behind the June-30 leak — close it before the next attended run. If it's just transcript noise, note that and move on.
4. **Re-run only after 1–3.** This produced no artifact and no reasoning to keep; the prior run's Round 1/2/3 conclusions (sandbox draft, CC↔Mem gated on SecretRef + fail-closed proxy + host hardening) remain your current state of knowledge — nothing here changes them.

**On autonomy:** unchanged, and if anything this reinforces the "keep it attended" verdict from a different angle — the prior run showed the council can't self-correct its _reasoning_ errors; this run shows the _orchestration_ still can't survive a single dropped turn without a human noticing the output was empty. Both need to be solid before an unattended loop is anything but a liability. The highest-value next step remains what I flagged last run: get secrets SecretRef'd and give the council verified filesystem read, so they can check their own claims — but first, get the harness to reliably produce a non-empty conversation.
