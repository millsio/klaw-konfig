#!/usr/bin/env python3
"""
mirror_openclaw_docs.py

Mirror the OpenClaw documentation site to a local directory as clean Markdown,
so a local agent (Klaw) can read the docs offline without hitting the web.

What it does:
  - Fetches llms.txt to discover all documentation pages.
  - Downloads each page as clean Markdown via its `.md` URL endpoint.
  - Skips non-English language paths.
  - Uses ETag / If-None-Match on subsequent runs (only re-fetches changed pages).
  - Stores each page's ETag in a sidecar <page>.md.etag file next to the page.
  - Writes <output>/INDEX.md  — a single file Klaw can read to find any page.
  - Logs activity to <output>/.mirror_log.txt
  - Polite delay between requests.

Standard library only (urllib) — no pip install required on the VM.

Usage:
  python3 mirror_openclaw_docs.py --dry-run   # discover + report, download nothing
  python3 mirror_openclaw_docs.py             # full mirror
"""

import argparse
import os
import re
import sys
import time
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ---------------------------------------------------------------------------
# Configuration — adjust here if the docs domain or layout turns out different.
# ---------------------------------------------------------------------------
BASE_URL   = "https://docs.openclaw.ai"
LLMS_TXT   = BASE_URL + "/llms.txt"
OUTPUT_DIR = os.path.expanduser("~/.openclaw/docs")
LOG_FILE   = os.path.join(OUTPUT_DIR, ".mirror_log.txt")
INDEX_FILE = os.path.join(OUTPUT_DIR, "INDEX.md")
USER_AGENT = "openclaw-docs-mirror/1.0 (local agent doc cache)"
REQUEST_DELAY = 0.3      # seconds between page requests (be polite)
TIMEOUT = 30             # per-request timeout, seconds

# English-only filter: keep a page if its first path segment is 'en'
# or if it has no language-code prefix at all. Skip other language codes.
ENGLISH_CODES = {"en"}
LANG_CODE_RE = re.compile(r"^[a-z]{2}(?:-[a-z]{2})?$", re.IGNORECASE)

# Markdown link extractor: [text](url)
LINK_RE = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")

# Asset/non-page extensions we never mirror as docs.
SKIP_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico",
    ".css", ".js", ".zip", ".pdf", ".webp", ".woff", ".woff2",
    ".xml", ".txt",
}

_dry_run = False
_log_lines = []


def log(msg):
    """Print to stdout and buffer for the on-disk log (unless dry-run)."""
    line = "%s  %s" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg)
    print(msg)
    _log_lines.append(line)


def flush_log():
    if _dry_run or not _log_lines:
        return
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as fh:
        fh.write("\n".join(_log_lines) + "\n")


def http_get(url, etag=None):
    """
    GET a URL. Returns (status, etag_str, body_bytes).
    On 304 Not Modified returns (304, None, None).
    Raises on hard failures (caller is expected to catch).
    """
    headers = {"User-Agent": USER_AGENT}
    if etag:
        headers["If-None-Match"] = etag
    req = Request(url, headers=headers)
    try:
        with urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.headers.get("ETag"), resp.read()
    except HTTPError as e:
        if e.code == 304:
            return 304, None, None
        raise


def to_md_url(url):
    """Normalize a discovered URL to its `.md` endpoint."""
    parsed = urlparse(url)
    path = parsed.path
    if path.endswith(".md"):
        return url
    # strip a trailing slash, then append .md
    path = path.rstrip("/")
    if not path:
        return parsed._replace(path="/index.md").geturl()
    new = parsed._replace(path=path + ".md")
    return new.geturl()


def first_path_segment(path):
    parts = [p for p in path.split("/") if p]
    return parts[0] if parts else ""


def is_english(path):
    """True if path is English or has no language prefix."""
    seg = first_path_segment(path)
    if LANG_CODE_RE.match(seg) and seg.lower() not in ENGLISH_CODES:
        return False
    return True


def local_path_for(md_url):
    """Map a doc URL to a local file path under OUTPUT_DIR, preserving structure."""
    path = urlparse(md_url).path.lstrip("/")
    if not path:
        path = "index.md"
    if not path.endswith(".md"):
        path += ".md"
    return os.path.join(OUTPUT_DIR, path)


def discover_pages():
    """
    Fetch llms.txt, parse out doc links, normalize to .md URLs, filter to
    same-host English pages. Returns a list of (title, md_url, local_path),
    de-duplicated and sorted.
    """
    log("Fetching index: %s" % LLMS_TXT)
    _, _, body = http_get(LLMS_TXT)
    text = body.decode("utf-8", errors="replace")

    base_host = urlparse(BASE_URL).netloc
    seen = set()
    pages = []
    skipped_lang = 0

    for title, raw in LINK_RE.findall(text):
        url = urljoin(BASE_URL, raw.strip())
        parsed = urlparse(url)

        # same host only; no anchors / mailto / external
        if parsed.scheme not in ("http", "https"):
            continue
        if parsed.netloc and parsed.netloc != base_host:
            continue

        _, ext = os.path.splitext(parsed.path)
        if ext.lower() in SKIP_EXTENSIONS:
            continue
        # don't re-mirror the index file itself
        if parsed.path.rstrip("/").endswith("llms.txt"):
            continue

        if not is_english(parsed.path):
            skipped_lang += 1
            continue

        md_url = to_md_url(url)
        if md_url in seen:
            continue
        seen.add(md_url)
        pages.append((title.strip(), md_url, local_path_for(md_url)))

    pages.sort(key=lambda p: p[2])
    log("Discovered %d English doc pages (%d non-English paths skipped)."
        % (len(pages), skipped_lang))
    return pages


def mirror_page(title, md_url, dest):
    """
    Fetch one page with ETag-based conditional GET. Returns one of:
    'fetched', 'unchanged', 'error'.
    """
    sidecar = dest + ".etag"
    stored_etag = None
    if os.path.exists(sidecar):
        with open(sidecar, "r", encoding="utf-8") as fh:
            stored_etag = fh.read().strip() or None

    try:
        status, new_etag, body = http_get(md_url, etag=stored_etag)
    except (HTTPError, URLError) as e:
        log("  ERROR  %s  (%s)" % (md_url, e))
        return "error"
    except Exception as e:  # noqa: BLE001 - never let one page kill the run
        log("  ERROR  %s  (%s)" % (md_url, e))
        return "error"

    if status == 304:
        return "unchanged"

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "wb") as fh:
        fh.write(body)
    if new_etag:
        with open(sidecar, "w", encoding="utf-8") as fh:
            fh.write(new_etag)
    log("  fetched %s" % os.path.relpath(dest, OUTPUT_DIR))
    return "fetched"


def write_index(pages):
    """Write INDEX.md: one entry per mirrored page, relative links for Klaw."""
    lines = [
        "# OpenClaw Documentation — Local Mirror Index",
        "",
        "Generated %s by mirror_openclaw_docs.py" % time.strftime("%Y-%m-%d %H:%M:%S"),
        "",
        "Source: %s" % BASE_URL,
        "",
        "%d pages mirrored. Each link is a local relative path." % len(pages),
        "",
    ]
    for title, _md_url, dest in pages:
        rel = os.path.relpath(dest, OUTPUT_DIR)
        label = title if title else rel
        lines.append("- [%s](%s)" % (label, rel))
    with open(INDEX_FILE, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    log("Wrote index: %s" % INDEX_FILE)


def main():
    global _dry_run
    parser = argparse.ArgumentParser(description="Mirror OpenClaw docs locally.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Discover pages and report; download nothing.")
    args = parser.parse_args()
    _dry_run = args.dry_run

    log("=== OpenClaw docs mirror %s ==="
        % ("(DRY RUN)" if _dry_run else "(full run)"))

    try:
        pages = discover_pages()
    except (HTTPError, URLError) as e:
        log("FATAL: could not fetch %s (%s)" % (LLMS_TXT, e))
        flush_log()
        sys.exit(1)

    if _dry_run:
        print("\nWould mirror the following pages:\n")
        for _title, md_url, dest in pages:
            print("  %s\n    <- %s" % (os.path.relpath(dest, OUTPUT_DIR), md_url))
        print("\n%d pages total. No files written." % len(pages))
        return

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    stats = {"fetched": 0, "unchanged": 0, "error": 0}
    for i, (title, md_url, dest) in enumerate(pages):
        result = mirror_page(title, md_url, dest)
        stats[result] += 1
        if i < len(pages) - 1:
            time.sleep(REQUEST_DELAY)

    write_index(pages)
    log("Done. fetched=%(fetched)d unchanged=%(unchanged)d errors=%(error)d"
        % stats)
    flush_log()


if __name__ == "__main__":
    main()
