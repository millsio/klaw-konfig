#!/usr/bin/env python3
"""Debate watcher — runs queued debates/competitions and streams them to Telegram.

Watches ~/.openclaw/debate-requests/ for request files dropped by an agent
(Klaw/Kettle) or by hand. For each, runs scripts/debate.py with Telegram
delivery, then moves the request to processed/ (or failed/).

This is the exec-block-respecting path: agents only WRITE a request file
(the `write` tool, which is NOT denied); this trusted service — running as the
klaw user under systemd --user — does the actual running and posting. The
agents never need exec.

Request file (any name) may be EITHER:
  - JSON: {"motion": "...", "mode": "debate"|"compete", "rounds": 3,
           "web": 3, "account": "default", "target": "8852367597"}
  - plain text: the topic on the first line; optional leading "compete:" or
    "debate:" prefix selects the mode.
"""
import json, os, shutil, subprocess, time
from datetime import datetime

OC = os.path.expanduser("~/.openclaw")
REQ = os.path.join(OC, "debate-requests")
DONE = os.path.join(REQ, "processed")
FAIL = os.path.join(REQ, "failed")
DEBATE = os.path.join(OC, "scripts", "debate.py")
DEFAULT_ACCOUNT = "default"      # @KlawJBot
DEFAULT_TARGET = "8852367597"    # Brian's Telegram id
POLL_SECONDS = 5


def parse(text, name):
    text = text.strip()
    if text.startswith("{"):
        d = json.loads(text)
    else:
        mode = "debate"
        low = text.lower()
        for m in ("compete", "collaborate", "debate"):
            if low.startswith(m + ":"):
                mode, text = m, text.split(":", 1)[1].strip()
                break
        d = {"motion": text, "mode": mode}
    if not d.get("motion"):
        raise ValueError("no motion")
    d.setdefault("mode", "debate")
    d.setdefault("rounds", 3)
    d.setdefault("web", 3)
    d.setdefault("account", DEFAULT_ACCOUNT)
    d.setdefault("target", DEFAULT_TARGET)
    return d


def run(req):
    cmd = ["/usr/bin/python3", DEBATE, req["motion"], "--mode", req["mode"],
           "--rounds", str(req["rounds"]), "--web", str(req["web"]), "--quiet",
           "--telegram", f"{req['account']}:{req['target']}"]
    subprocess.run(cmd, cwd=OC, timeout=1800)


def notify_error(req, msg):
    try:
        subprocess.run(["openclaw", "message", "send", "--channel", "telegram",
                        "--account", req.get("account", DEFAULT_ACCOUNT),
                        "--target", req.get("target", DEFAULT_TARGET),
                        "--message", f"⚠️ debate request failed: {msg[:300]}"],
                       cwd=OC, capture_output=True, text=True)
    except Exception:
        pass


def main():
    for d in (REQ, DONE, FAIL):
        os.makedirs(d, exist_ok=True)
    print(f"[debate-watcher] watching {REQ}")
    while True:
        try:
            files = sorted(f for f in os.listdir(REQ)
                           if os.path.isfile(os.path.join(REQ, f)) and not f.startswith("."))
        except OSError:
            files = []
        for fn in files:
            path = os.path.join(REQ, fn)
            stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            try:
                req = parse(open(path).read(), fn)
            except Exception as e:
                notify_error({}, f"bad request {fn}: {e}")
                shutil.move(path, os.path.join(FAIL, f"{stamp}-{fn}"))
                continue
            print(f"[debate-watcher] running: {req['mode']} — {req['motion'][:60]!r}")
            try:
                run(req)
                shutil.move(path, os.path.join(DONE, f"{stamp}-{fn}"))
            except Exception as e:
                notify_error(req, str(e))
                shutil.move(path, os.path.join(FAIL, f"{stamp}-{fn}"))
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
