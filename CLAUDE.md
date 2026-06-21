# CLAUDE.md — Claude Code working notes for the OpenClaw project

## Sources of truth
- Operational conventions and project rules: follow `AGENTS.md` in this directory.
- Cross-tool project memory: the Mem collection "OPENCLAW PROJECT" (id `82bba4f9-6724-4874-bbcf-1f9ab525b873`). Read it at session start; record milestones/decisions there.
- OpenClaw docs: local mirror at `~/.openclaw/docs/` (`INDEX.md` is the map) — prefer it over web search for OpenClaw questions.

## Hard rules
- `.gitignore` is deny-by-default with explicit per-file allows. NEVER commit secrets — no `openclaw.json`, credentials, identity, keys, tokens, sqlite stores, or the docs mirror.
- When allowing a new file, add an explicit `!path` line; never a broad wildcard that could catch a secret.
- Before any config edit, review the diff and validate JSON before writing.
