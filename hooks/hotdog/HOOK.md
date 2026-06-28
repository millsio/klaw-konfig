---
name: hotdog
description: "Run a local-model debate/compete/collab/judge from a /hotdog Telegram message"
homepage: https://docs.openclaw.ai/automation/hooks
metadata:
  {
    "openclaw":
      {
        "emoji": "🌭",
        "events": ["message:received"],
        "requires": { "bins": ["bash"] },
      },
  }
---

# Hotdog Hook

When an inbound message starts with `/hotdog`, this hook deterministically runs
`~/.openclaw/scripts/hotdog.sh` (no local model interpreting the request) and
streams the result to Brian's Telegram.

## Subcommands

```
/hotdog debate  <statement>
/hotdog compete <task>
/hotdog collab  <goal>
/hotdog judge
/hotdog stop | drop | roll | help
```

The hook only ACTS on messages beginning with `/hotdog`; everything else passes
through untouched. The heavy logic lives in `scripts/hotdog.sh` (testable from a
terminal). Results are delivered with `hotdog.sh --tg` (Brian's DM).

## Enable / disable

```bash
openclaw hooks enable hotdog
openclaw hooks disable hotdog
```
