---
mem_id: 7a46ff6e-2a77-4c4b-aea6-0c859cffd894
title: "OPENCLAW PROJECT \u2014 Performance Investigations"
created_at: 2026-06-13T04:56:57.770Z
updated_at: 2026-06-13T04:56:58.408Z
source: mem:OPENCLAW PROJECT
---

# OPENCLAW PROJECT — Performance Investigations

## Current Status

Active. Performance issue resolved. System stable.

## Last Updated

2026-06-13

## Key Decisions

- tools.profile=coding was confirmed as a root cause of severe latency on fresh sessions.
- Gateway restart after profile changes is a required operational step.
- Named sessions should always be used instead of relying on agent:main:main.
- The legacy main session should not be used for testing.

## Summary

A severe latency investigation was conducted on June 11, 2026. Direct Ollama performance was confirmed healthy (\~1.7 seconds from VM). The root cause of 30–90 second response times was isolated to tools.profile=coding, which injects significantly more context at session start. A secondary contributor was the legacy main session with a 5.0 MB trajectory file. The system is currently stable under the minimal profile.

***

## Investigation: OpenClaw Latency (June 11, 2026)

### Environment

- OpenClaw 2026.6.5
- Ubuntu VM (KlawMachine)
- Ollama on Windows host (10.10.10.1:11434)
- Primary model: mistral-small3.2:24b (context: 131072)

### Symptoms

- OpenClaw taking 30–90 seconds to answer trivial questions.
- Direct Ollama API calls answered in \~1.7 seconds.
- Existing main session showed context overflow errors, aborted status, and strange replay behavior.

### Diagnostics Performed

**Direct Ollama test:**

- curl to Ollama host with prompt "What is 2+2?"
- Response in \~1.7 seconds
- Confirmed networking and Ollama performance were not the bottleneck

**Session inspection:**

- agent:main:main: 19k tokens, aborted status
- Fresh sessions started around 6.2k tokens

**Fresh session test:**

- Session "fresh-test" responded in \~1 second at \~6.2k/131k tokens
- Demonstrated the old main session was abnormal

**Profile investigation:**

- Discovered tools.profile=coding was active
- Changed to minimal: `openclaw config set tools.profile minimal`
- Gateway restart required

**Minimal profile test:**

- "minimal-test" session responded in \~1–2 seconds
- Token baseline \~6.2–6.3k, stable behavior

**Coding profile controlled retest:**

1. Switched back to coding profile
2. Restarted gateway
3. Created fresh session "coding-retest"
4. Asked "What is 6 + 4?"
5. Response took \~65 seconds
6. Session baseline \~11k tokens

This reproduced the original slowdown on a completely fresh session, confirming the profile — not the legacy session — was the primary cause.

### Findings

| Configuration   | Session Baseline  | Response Time |
| --------------- | ----------------- | ------------- |
| coding profile  | \~11k tokens      | \~65 seconds  |
| minimal profile | \~6.2–6.3k tokens | \~1–2 seconds |
| Direct Ollama   | N/A               | \~1.7 seconds |

### Root Cause

Primary: tools.profile=coding injects significantly more tools, skills, schemas, workspace context, and agent instructions at session start, dramatically increasing prompt size and processing overhead.

Secondary: The legacy main session (agent:main:main) had accumulated 5.0 MB trajectory file, 60 KB JSONL, \~19k token context, and aborted status. While not the primary cause, it was a real contributor to abnormal behavior.

### Resolution

- Switched to tools.profile=minimal
- Restarted gateway
- Created named sessions for ongoing use
- Avoided using legacy main session

### Lessons Learned

- Profile selection has a very large impact on latency — larger than initially assumed.
- A fresh session under a high-overhead profile is still slow (coding profile, fresh session = 65 seconds).
- The coding profile overhead appears to be structural, not session-state-related.
- Gateway restart is mandatory after profile changes.
- Named sessions provide cleaner baselines for testing and investigation.

***

## Investigation: Session Persistence and Context Growth (June 11, 2026)

### Key Findings

- OpenClaw sessions persist trajectory and JSONL files in \~/.openclaw/agents/main/sessions/
- Main session trajectory: \~5.0 MB (abnormally large)
- Test session trajectories: dramatically smaller
- Main session ID: cb2a6408-6a26-46e3-8511-65ea969d80ff

### Context Injection Sources

Main session metadata showed large workspace injections from: AGENTS.md, SOUL.md, TOOLS.md, IDENTITY.md, USER.md, HEARTBEAT.md

### Recommendation

Monitor session history growth as a potential latency predictor. Consider pruning or retiring the legacy main session. Do not use agent:main:main for performance testing or benchmarking.

***

## Hyper-V Checkpoint

Checkpoint created at time of resolution:

Name: "Solved Openclaw Performance Issue - 6/11/2026 1:01 AM EDT"

State at checkpoint:

- OpenClaw operational
- Gateway restart procedure verified
- Host ↔ VM connectivity verified
- Ollama performance verified healthy
- Performance issue reproduced and isolated

***

## Recent Updates

- 2026-06-13: Performance Investigations note created from legacy source consolidation.
