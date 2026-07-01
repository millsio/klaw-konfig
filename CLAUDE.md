# CLAUDE.md — Claude Code working notes for the OpenClaw project

## Sources of truth
- Operational conventions and project rules: follow `AGENTS.md` in this directory.
- Project memory: local files in `~/.openclaw/project-notes/` (`INDEX.md` is the map). Read at session start; record milestones/decisions there. Migrated off Mem 2026-07-01; `mem_backup.py` keeps a Mem snapshot until cutover completes.
- OpenClaw docs: local mirror at `~/.openclaw/docs/` (`INDEX.md` is the map) — prefer it over web search for OpenClaw questions.

## Hard rules
- `.gitignore` is deny-by-default with explicit per-file allows. NEVER commit secrets — no `openclaw.json`, credentials, identity, keys, tokens, sqlite stores, or the docs mirror.
- When allowing a new file, add an explicit `!path` line; never a broad wildcard that could catch a secret.
- Before any config edit, review the diff and validate JSON before writing.
