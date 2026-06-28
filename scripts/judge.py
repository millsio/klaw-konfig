#!/usr/bin/env python3
"""Opus judge for a debate/collaboration transcript — the council's frontier adjudicator.

Calls Claude Code headless (`claude -p --model opus`) over a saved transcript and
writes a verdict. Runs with --permission-mode bypassPermissions so it never hangs
on an approval prompt; the judge uses NO tools (pure reasoning over the transcript
text it is handed), so there is nothing risky to approve.

  python3 ~/.openclaw/scripts/judge.py                 # judge the latest debate
  python3 ~/.openclaw/scripts/judge.py <debate-dir>    # judge a specific one
  python3 ~/.openclaw/scripts/judge.py --telegram default:8852367597

BILLING: headless `claude -p` draws the separate monthly Agent SDK credit (not the
interactive pool). On-demand/attended use is fine; do NOT wire this into an
unattended loop until strict cost controls exist (see Roadmap cost-gate decision).
"""
import argparse, glob, os, subprocess, sys

OC = os.path.expanduser("~/.openclaw")
DEBATES = os.path.join(OC, "debates")

PROMPT = """You are a neutral, rigorous debate judge. Below is a transcript of an exchange between two local AI models. No judge was present during it. Adjudicate concisely:

1. VERDICT — which side/contestant was better-supported (or "synthesize" / "insufficient evidence"), one line.
2. GROUNDING CHECK — for the key factual/numeric claims (especially any tagged [GROUNDED] or [ASSUMED]), label each CONFIRMED / UNSUPPORTED / FABRICATED with a one-line reason. Explicitly flag claims tagged [GROUNDED] that are actually shaky or false.
3. BEST & WORST — each side's strongest point and biggest miss, including any clean rebuttal ("kill") they left on the table.
4. BLIND SPOTS — what both sides missed.
5. CONFIDENCE — low/medium/high, and what would change your verdict.

Be direct and concise. Do not use tools; judge only from the transcript.

=== TRANSCRIPT ===
"""


def tg_send(spec, text):
    if not spec or not text:
        return
    acct, _, target = spec.partition(":")
    for i in range(0, len(text), 3800):
        subprocess.run(["openclaw", "message", "send", "--channel", "telegram",
                        "--account", acct, "--target", target, "--message", text[i:i + 3800]],
                       cwd=OC, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser(prog="judge", description="Opus judge for a debate transcript.")
    ap.add_argument("debate_dir", nargs="?", help="debate output dir (default: latest under ~/.openclaw/debates)")
    ap.add_argument("--model", default="opus")
    ap.add_argument("--telegram", help="post verdict to Telegram, 'account:chatid'")
    a = ap.parse_args()

    d = a.debate_dir
    if not d:
        dirs = sorted(glob.glob(os.path.join(DEBATES, "2*")))
        d = dirs[-1] if dirs else None
    if not d or not os.path.isdir(d):
        sys.exit(f"no debate dir found ({d})")
    tpath = os.path.join(d, "transcript.md")
    if not os.path.exists(tpath):
        sys.exit(f"no transcript.md in {d}")
    transcript = open(tpath).read()

    print(f"[judge] {os.path.basename(d)} via claude -p --model {a.model} ...", file=sys.stderr)
    tg_send(a.telegram, f"⚖️ Judging: {os.path.basename(d)} …")
    p = subprocess.run(["claude", "-p", "--model", a.model,
                        "--permission-mode", "bypassPermissions", PROMPT + transcript],
                       capture_output=True, text=True, cwd=OC, timeout=400)
    if p.returncode != 0:
        sys.exit(f"claude failed: {p.stderr[:400]}")
    verdict = p.stdout.strip()
    open(os.path.join(d, "verdict.md"), "w").write(f"# Judge verdict ({a.model})\n\n{verdict}\n")
    print("\n" + verdict + "\n")
    tg_send(a.telegram, "⚖️ Verdict:\n\n" + verdict)
    print(f"[saved: {os.path.join(d, 'verdict.md')}]")


if __name__ == "__main__":
    main()
