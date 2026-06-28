#!/usr/bin/env python3
"""Reusable, safe, anchored editor for Mem notes (OPENCLAW PROJECT).

Fetches a note's LIVE content via the Mem REST API, applies ONE anchored edit in
code (no hand-transcription of the big body), and PATCHes it back. Dry-run by
default; pass --apply to write. Asserts the anchor matches exactly once, and an
optional --sentinel makes it idempotent.

  # insert a block after a unique anchor line
  mem_edit.py --note <id> --after "## Recent Updates" --text-file block.md --apply

  # replace an exact substring
  mem_edit.py --note <id> --replace "old text" --text "new text" --apply

  # append to the end of the note
  mem_edit.py --note <id> --append --text-file block.md --apply

Reads the Mem bearer token from openclaw.json at runtime (no secret in the file).
Use this instead of writing one-off fold scripts.
"""
import argparse, json, os, sys, urllib.request

CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
API = "https://api.mem.ai/v2/notes"


def auth():
    cfg = json.load(open(CONFIG))
    for k, v in cfg["mcp"]["servers"]["mem"]["headers"].items():
        if k.lower() == "authorization":
            return v
    sys.exit("no Mem auth header in openclaw.json")


def get(nid, a):
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(f"{API}/{nid}", headers={"Authorization": a}), timeout=30).read())


def patch(nid, content, version, a):
    body = json.dumps({"content": content, "version": version}).encode()
    return json.loads(urllib.request.urlopen(urllib.request.Request(
        f"{API}/{nid}", data=body, method="PATCH",
        headers={"Authorization": a, "Content-Type": "application/json"}), timeout=30).read())


def main():
    ap = argparse.ArgumentParser(prog="mem_edit", description="Safe anchored editor for Mem notes.")
    ap.add_argument("--note", required=True, help="note UUID")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--after", metavar="ANCHOR", help="insert text immediately after this unique string")
    g.add_argument("--before", metavar="ANCHOR", help="insert text immediately before this unique string")
    g.add_argument("--replace", metavar="OLD", help="replace this unique substring with --text")
    g.add_argument("--append", action="store_true", help="append text to end of note")
    t = ap.add_mutually_exclusive_group(required=True)
    t.add_argument("--text", help="literal text payload")
    t.add_argument("--text-file", help="read text payload from this file")
    ap.add_argument("--sentinel", help="skip if this string already in the note (idempotency)")
    ap.add_argument("--apply", action="store_true", help="actually write (default: dry-run)")
    args = ap.parse_args()

    text = open(args.text_file).read() if args.text_file else args.text
    a = auth()
    note = get(args.note, a)
    content, version, title = note["content"], note["version"], note["title"]
    if args.sentinel and args.sentinel in content:
        print(f"SKIP {title} v{version} — sentinel present"); return

    if args.append:
        new = content.rstrip("\n") + "\n" + text + "\n"
    else:
        anchor = args.after or args.before or args.replace
        n = content.count(anchor)
        if n != 1:
            sys.exit(f"ABORT: anchor matched {n} times (need exactly 1): {anchor[:70]!r}")
        if args.after:
            new = content.replace(anchor, anchor + text, 1)
        elif args.before:
            new = content.replace(anchor, text + anchor, 1)
        else:
            new = content.replace(anchor, text, 1)

    print(f"{title} v{version}: {len(content)} -> {len(new)} ({len(new)-len(content):+d} chars)")
    if args.apply:
        print(f"  PATCHED -> v{patch(args.note, new, version, a).get('version')}")
    else:
        print("  (dry-run) ok — pass --apply to write")


if __name__ == "__main__":
    main()
