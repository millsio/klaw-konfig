#!/usr/bin/env python3
"""Docs Digest — map-reduce the local OpenClaw docs mirror into a single comprehensive
digest (~/.openclaw/docs-digest.md) so agents get a WHOLE-CORPUS view: cross-cutting
insight you can't get from piecemeal lookups. Uses claude -p (Opus) off OAuth.

  docs_digest.py                 # TEST slice (first 8 files) — cheap, validates the pipeline
  docs_digest.py --full          # the whole mirror (~689 files) — real token spend
  docs_digest.py --limit 20      # a bigger slice

Map: batch files -> dense structured summary each. Reduce: synthesize a single digest.
Cron-able (the Roadmap's weekly digest). claude -p runs tool-less over piped text only.
"""
import argparse, glob, hashlib, os, subprocess, time

DOCS = os.path.expanduser("~/.openclaw/docs")
OUT = os.path.expanduser("~/.openclaw/docs-digest.md")
CACHE = os.path.expanduser("~/.openclaw/.digest-cache")  # per-batch map summaries, keyed by content hash
SKIP = {"CLAUDE.md", "INDEX.md"}

MAP_PROMPT = (
    "You are digesting a slice of the OpenClaw documentation. For the files below, produce a DENSE, "
    "structured markdown summary capturing: key concepts; important config keys with valid values and "
    "defaults; commands; gotchas/caveats; and cross-references to other areas. Be specific — real key "
    "names, real defaults, no fluff. Use NO tools; summarize only the text below.\n\n=== FILES ===\n"
)
REDUCE_PROMPT = (
    "You are producing a single comprehensive DIGEST of the OpenClaw documentation from the per-section "
    "summaries below. Synthesize a coherent whole-corpus overview that surfaces CROSS-CUTTING insight — "
    "the config surface, the tool/agent/sandbox/security model, how the pieces fit, and things you'd only "
    "notice by seeing everything at once. Organize by theme, stay specific (keep real config keys, "
    "commands, defaults), and be the map someone reads to understand OpenClaw as a whole. Use NO tools. "
    "Output a well-structured markdown document.\n\n=== SECTION SUMMARIES ===\n"
)


def claude(prompt, model, timeout=900):
    # Prompt goes via stdin, not argv: large map batches (~150k chars) blow past
    # ARG_MAX as a single CLI argument (OSError: Argument list too long).
    p = subprocess.run(["claude", "-p", "--model", model, "--permission-mode", "bypassPermissions"],
                       input=prompt, capture_output=True, text=True, timeout=timeout)
    if p.returncode != 0:
        raise RuntimeError(p.stderr[:400])
    return p.stdout.strip()


def collect():
    return sorted(f for f in glob.glob(os.path.join(DOCS, "**", "*.md"), recursive=True)
                  if os.path.basename(f) not in SKIP)


def batches(files, max_chars):
    batch, size = [], 0
    for f in files:
        c = open(f, encoding="utf-8", errors="replace").read()
        if batch and size + len(c) > max_chars:
            yield batch
            batch, size = [], 0
        batch.append((f, c))
        size += len(c)
    if batch:
        yield batch


def reduce_tree(summaries, model, group=8):
    """Merge summaries in groups until one digest remains (keeps each reduce prompt bounded)."""
    level = 0
    while len(summaries) > 1:
        level += 1
        nxt = []
        for i in range(0, len(summaries), group):
            chunk = summaries[i:i + group]
            print(f"[reduce L{level}] merging {len(chunk)} of {len(summaries)} ...")
            nxt.append(claude(REDUCE_PROMPT + "\n\n---\n\n".join(chunk), model))
        summaries = nxt
    return summaries[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=8, help="max files in TEST mode")
    ap.add_argument("--full", action="store_true", help="digest the entire mirror (~694 files)")
    ap.add_argument("--model", default="opus", help="model for the REDUCE/synthesis step")
    ap.add_argument("--map-model", default="claude-sonnet-5", help="model for per-batch summaries (cheaper is fine)")
    ap.add_argument("--max-chars", type=int, default=150000, help="chars per map batch")
    ap.add_argument("--max-new", type=int, default=0,
                    help="max NEW (uncached) map batches to run this invocation (0=all); for window-chunked runs")
    a = ap.parse_args()

    files = collect()
    print(f"[digest] {len(files)} docs files in mirror")
    if not a.full:
        files = files[:a.limit]
        print(f"[digest] TEST mode: {len(files)} files (use --full for all)")

    os.makedirs(CACHE, exist_ok=True)
    t0, summaries = time.time(), []
    new_done, remaining = 0, 0
    b = list(batches(files, a.max_chars))
    for i, batch in enumerate(b, 1):
        blob = "\n\n".join(f"### FILE: {os.path.relpath(f, DOCS)}\n\n{c}" for f, c in batch)
        # Cache each map summary by (model, content) hash so a crash or a window-bounded run resumes
        # cheaply: completed batches load from disk, only uncached ones are (re-)billed.
        key = hashlib.sha256((a.map_model + "\n" + blob).encode("utf-8")).hexdigest()
        cpath = os.path.join(CACHE, key + ".md")
        if os.path.exists(cpath):
            summaries.append(open(cpath, encoding="utf-8").read())
            continue
        if a.max_new and new_done >= a.max_new:  # per-run budget spent; leave the rest for the next window
            remaining += 1
            continue
        print(f"[map {i}/{len(b)}] {len(batch)} files, {len(blob)} chars -> claude -p ({a.map_model}) ...", flush=True)
        try:
            s = claude(MAP_PROMPT + blob, a.map_model)
        except Exception as e:
            print(f"[map {i}/{len(b)} FAILED] {type(e).__name__}: {str(e)[:200]}\n"
                  f"[digest] {new_done} new batch(es) mapped this run; re-run to resume (cached ones skip).", flush=True)
            raise SystemExit(1)
        open(cpath, "w", encoding="utf-8").write(s)
        summaries.append(s)
        new_done += 1
    if remaining:
        print(f"[digest] chunk complete: {new_done} newly mapped, {remaining} remaining "
              f"({len(b) - remaining}/{len(b)} cached). Re-run to continue; reduce runs once all are cached.", flush=True)
        raise SystemExit(0)
    print(f"[reduce] synthesizing {len(summaries)} section summaries ...", flush=True)
    digest = reduce_tree(summaries, a.model)

    tag = "FULL" if a.full else f"TEST slice ({len(files)} files)"
    header = (f"# OpenClaw Docs Digest\n\n_Generated {time.strftime('%Y-%m-%d')} from the local mirror via "
              f"claude -p ({a.model}) — {tag}._\n\n")
    open(OUT, "w").write(header + digest + "\n")
    print(f"[digest] wrote {OUT} ({len(digest)} chars) in {int(time.time() - t0)}s")


if __name__ == "__main__":
    main()
