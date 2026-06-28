#!/usr/bin/env python3
"""Local backup of the OPENCLAW PROJECT Mem collection.

Pulls every note in the collection (with full markdown) via the Mem REST API
and writes a timestamped snapshot to ~/.openclaw/mem-backups/YYYY-MM-DD/.
Keeps the most recent KEEP snapshots and prunes older ones.

- Stdlib only (urllib); no pip deps.
- Reads the Mem bearer token from openclaw.json at runtime, so this tracked
  script contains no secret.
- Scoped to the OPENCLAW PROJECT collection only (never touches personal notes).

This is a point-in-time safety net, NOT a transactional backup: edits made
between runs can still be lost. It converts "lose everything" into
"lose at most one interval".
"""

import json
import os
import re
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# --- config ---
COLLECTION_ID = "82bba4f9-6724-4874-bbcf-1f9ab525b873"  # OPENCLAW PROJECT
API_BASE = "https://api.mem.ai/v2/notes"
CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")
BACKUP_ROOT = os.path.expanduser("~/.openclaw/mem-backups")
KEEP = 10                # number of snapshots to retain (e.g. 10 weekly = ~10 weeks)
PAGE_LIMIT = 100         # max per Mem API page
TIMEOUT = 30


def log(msg):
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"{stamp} {msg}"
    print(line)
    try:
        os.makedirs(BACKUP_ROOT, exist_ok=True)
        with open(os.path.join(BACKUP_ROOT, ".backup_log.txt"), "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


def read_auth_header():
    """Pull the 'Bearer ...' value from openclaw.json mcp.servers.mem headers."""
    with open(CONFIG_PATH) as f:
        cfg = json.load(f)
    headers = cfg["mcp"]["servers"]["mem"]["headers"]
    # Header key casing may vary; match case-insensitively.
    for k, v in headers.items():
        if k.lower() == "authorization":
            return v
    raise KeyError("Authorization header not found in mcp.servers.mem.headers")


def fetch_all_notes(auth):
    """Return list of note dicts (with content) across all pages."""
    notes = []
    page = None
    while True:
        params = {
            "collection_id": COLLECTION_ID,
            "include_note_content": "true",
            "limit": str(PAGE_LIMIT),
            "order_by": "updated_at",
        }
        if page:
            params["page"] = page
        url = API_BASE + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"Authorization": auth})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        notes.extend(data.get("results", []))
        page = data.get("next_page")
        if not page:
            break
    return notes


def slugify(title, note_id):
    base = re.sub(r"[^A-Za-z0-9]+", "-", (title or "untitled")).strip("-").lower()
    base = base[:60] or "untitled"
    return f"{base}__{note_id[:8]}"


def write_snapshot(notes):
    day = datetime.now().strftime("%Y-%m-%d")
    out_dir = os.path.join(BACKUP_ROOT, day)
    os.makedirs(out_dir, exist_ok=True)

    # Raw API payload for full fidelity.
    with open(os.path.join(out_dir, "manifest.json"), "w") as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)

    index_lines = [f"# Mem backup — OPENCLAW PROJECT — {day}", "",
                   f"{len(notes)} notes.", ""]
    for n in sorted(notes, key=lambda x: x.get("title", "")):
        nid = n.get("id", "unknown")
        title = n.get("title", "untitled")
        fname = slugify(title, nid) + ".md"
        front = (
            f"---\nid: {nid}\ntitle: {json.dumps(title)}\n"
            f"created_at: {n.get('created_at','')}\n"
            f"updated_at: {n.get('updated_at','')}\n---\n\n"
        )
        with open(os.path.join(out_dir, fname), "w") as f:
            f.write(front + (n.get("content") or ""))
        index_lines.append(f"- [{title}]({fname})")
    with open(os.path.join(out_dir, "INDEX.md"), "w") as f:
        f.write("\n".join(index_lines) + "\n")
    return out_dir


def prune():
    if not os.path.isdir(BACKUP_ROOT):
        return
    dirs = [d for d in os.listdir(BACKUP_ROOT)
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", d)
            and os.path.isdir(os.path.join(BACKUP_ROOT, d))]
    dirs.sort()  # date strings sort chronologically
    for old in dirs[:-KEEP]:
        shutil.rmtree(os.path.join(BACKUP_ROOT, old))
        log(f"pruned old snapshot {old}")


def main():
    try:
        auth = read_auth_header()
        notes = fetch_all_notes(auth)
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, KeyError, ValueError) as e:
        log(f"ERROR: {type(e).__name__}: {e}")
        sys.exit(1)
    if not notes:
        log("ERROR: 0 notes returned — refusing to write an empty snapshot")
        sys.exit(1)
    out_dir = write_snapshot(notes)
    prune()
    log(f"backup OK: {len(notes)} notes -> {out_dir} (keep last {KEEP})")


if __name__ == "__main__":
    main()
