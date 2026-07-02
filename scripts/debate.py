#!/usr/bin/env python3
"""Two-local-model arena, runnable from the KlawMachine command line.

Modes:
  debate      (default) qwen argues FOR a statement, gemma AGAINST (or set with --for), N rounds.
  compete               both models independently attempt the SAME task; outputs side by side.
  collaborate           both models work TOGETHER on a goal — constructive criticism, build on
                        each other, converge on the best outcome (can read files/use tools).

Contestants: qwen3.6:27b (agent `main`, pacifico/3090) and gemma4:31b (agent `gemma-amethyst`,
amethyst/5090). No automated judge in this tool — see scripts/judge.py for the Opus judge.

Examples:
  debate "Tabs are better than spaces"
  debate "Rust is overhyped" --for gemma --rounds 3 --web 3
  debate "Write Python tic-tac-toe with an unbeatable AI" --mode compete
  debate "Assess and improve ~/.openclaw/scripts/debate.py and its docs" --mode collaborate
"""
import argparse, json, os, re, shutil, subprocess, sys, time
from datetime import datetime

OC = os.path.expanduser("~/.openclaw")
QWEN = {"agent": "main", "think": "off"}
GEMMA = {"agent": "gemma-amethyst", "think": "medium"}
LABELS = {"main": "qwen3.6:27b (pacifico)", "gemma-amethyst": "gemma4:31b (amethyst)"}
BRIAN_TG = "default:8852367597"  # default Telegram target for --tg shorthand
TG = None  # (account, target) when --telegram is set


def label(agent):
    return LABELS.get(agent, agent)


def tg_send(text):
    if not TG or not text:
        return
    acct, target = TG
    for i in range(0, len(text), 3800):
        subprocess.run(["openclaw", "message", "send", "--channel", "telegram",
                        "--account", acct, "--target", target, "--message", text[i:i + 3800]],
                       cwd=OC, capture_output=True, text=True)


def run_turn(agent, key, message, think, timeout=240):
    cmd = ["openclaw", "agent", "--agent", agent, "--session-key", key,
           "--message", message, "--thinking", think, "--json", "--timeout", str(timeout)]
    # subprocess timeout backstops the CLI's own --timeout in case the process itself hangs
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=OC, timeout=timeout + 90)
    if p.returncode != 0 or not p.stdout.strip():
        raise RuntimeError(f"turn failed ({agent}): rc={p.returncode} {p.stderr[:300]}")
    d = json.loads(p.stdout)
    res = d.get("result")
    if not isinstance(res, dict) or "payloads" not in res:
        # error envelope / timeout response without a result body — surface it verbatim
        raise RuntimeError(f"turn failed ({agent}): no result in agent JSON: {p.stdout[:400]}")
    txt = " ".join(x.get("text", "") for x in (res["payloads"] or [])).strip()
    sess = ((res.get("meta") or {}).get("agentMeta") or {}).get("sessionFile")
    return txt, sess, d


def stream(text, delay, on):
    if not on:
        print(text); return
    for ch in text:
        sys.stdout.write(ch); sys.stdout.flush(); time.sleep(delay)
    print()


def count_web(sf):
    if not sf or not os.path.exists(sf):
        return 0
    try:
        return sum(1 for _ in re.finditer(r'"(web_search|x_search|web_fetch)"', open(sf).read()))
    except OSError:
        return 0


def webrule(n, tools_ok=False):
    if n > 0:
        base = (f"You may use web_search (shared budget {n} for the whole run). PREFER to verify at "
                f"least one key factual claim with a real search rather than relying on memory — "
                f"especially for current, empirical, or niche topics. Always include the URL you used.")
        return base + (" You may also read files when relevant." if tools_ok else "")
    return "You may read files when relevant." if tools_ok else "Do not use any tools."


def setup_out(root, mode, motion):
    ts = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    slug = re.sub(r"[^a-z0-9]+", "-", motion.lower()).strip("-")[:50] or mode
    outdir = os.path.join(root, f"{ts}-{mode}-{slug}")
    os.makedirs(outdir, exist_ok=True)
    return ts, outdir


def finish(outdir, transcript, sessfiles, web_budget, quiet):
    for ag, sf in sessfiles.items():
        if sf and os.path.exists(sf):
            shutil.copy(sf, os.path.join(outdir, f"session_{ag.replace('/', '_')}.jsonl"))
    used = sum(count_web(sf) for sf in sessfiles.values())
    footer = f"\n---\n_web searches used: {used}/{web_budget} (instruction-level, not hard-enforced)_\n"
    transcript.append(footer)
    open(os.path.join(outdir, "transcript.md"), "w").write("\n".join(transcript))
    if not quiet:
        print(footer)
    tg_send(f"✅ done (web searches: {used}/{web_budget})")
    print(f"[saved: {outdir}]")
    return outdir


def do_debate(a):
    A, B = (GEMMA, QWEN) if a.swap else (QWEN, GEMMA)
    A = {**A, "side": "FOR the statement", "tag": f"{label(A['agent'])} — FOR"}
    B = {**B, "side": "AGAINST the statement", "tag": f"{label(B['agent'])} — AGAINST"}
    ts, outdir = setup_out(a.out, "debate", a.motion)
    for d in (A, B):
        d["key"] = f"agent:{d['agent']}:debate-{ts}"
    rules = (f"Rules: keep each reply under ~90 words. Make your strongest point and rebut your "
             f"opponent's last point. Tag your OWN factual claims: use [GROUNDED] ONLY for a claim "
             f"you back with a source you actually retrieved THIS debate (a web_search URL or a file "
             f"you read); claims from memory MUST be [ASSUMED] — never [GROUNDED]. ALSO call out your "
             f"opponent's weakest unsupported claim as [CHALLENGE: ...] and press it. "
             f"{webrule(a.web)} No preamble, just the argument.")
    header = (f"# Debate (no judge) — {a.rounds} messages each\n\n**Statement:** {a.motion}\n\n"
              f"- FOR = {A['tag']}\n- AGAINST = {B['tag']}\n- web budget: {a.web} | {ts}\n\n---\n")
    transcript = [header]
    if not a.quiet:
        print(header)
    tg_send(f"🥊 Debate — {a.motion}\nFOR: {A['tag']}\nAGAINST: {B['tag']}")
    sessfiles, last, turn = {}, None, 0
    for _ in range(a.rounds):
        for d in (A, B):
            turn += 1
            base = f"You are debating. Your position: {d['side']}.\n\nSTATEMENT: {a.motion}\n\n"
            msg = base + (f"You open the debate. {rules}" if last is None
                          else f"Opponent just said:\n\"{last}\"\n\nRespond. {rules}")
            txt, sess, full = run_turn(d["agent"], d["key"], msg, d["think"])
            if sess: sessfiles[d["agent"]] = sess
            json.dump(full, open(os.path.join(outdir, f"turn{turn:02d}_{d['agent']}.json"), "w"),
                      indent=2, ensure_ascii=False)
            transcript.append(f"### {turn}. {d['tag']}\n\n{txt}\n")
            if not a.quiet:
                print(f"\n### {turn}. {d['tag']}\n"); stream(txt, a.stream_delay, a.stream)
            tg_send(f"{turn}. {d['tag']}\n\n{txt}")
            last = txt
    return finish(outdir, transcript, sessfiles, a.web, a.quiet)


def do_compete(a):
    ts, outdir = setup_out(a.out, "compete", a.motion)
    instr = (f"TASK: {a.motion}\n\nProduce your best, complete, self-contained solution. If you "
             f"write code, make it runnable. {webrule(a.web, tools_ok=True)} No preamble.")
    header = (f"# Competition (no judge) — same task, independent attempts\n\n**Task:** {a.motion}\n\n"
              f"- A = {label(QWEN['agent'])}\n- B = {label(GEMMA['agent'])}\n- web budget: {a.web} | {ts}\n\n---\n")
    transcript = [header]
    if not a.quiet:
        print(header)
    tg_send(f"🏟️ Competition — {a.motion}")
    sessfiles = {}
    for d in (QWEN, GEMMA):
        txt, sess, full = run_turn(d["agent"], f"agent:{d['agent']}:compete-{ts}", instr, d["think"])
        if sess: sessfiles[d["agent"]] = sess
        json.dump(full, open(os.path.join(outdir, f"attempt_{d['agent']}.json"), "w"),
                  indent=2, ensure_ascii=False)
        transcript.append(f"## {label(d['agent'])}\n\n{txt}\n")
        if not a.quiet:
            print(f"\n## {label(d['agent'])}\n"); stream(txt, a.stream_delay, a.stream)
        tg_send(f"— {label(d['agent'])} —\n\n{txt}")
    return finish(outdir, transcript, sessfiles, a.web, a.quiet)


def do_collaborate(a):
    ts, outdir = setup_out(a.out, "collaborate", a.motion)
    rules = (f"You and your partner are COLLABORATING toward a shared goal — not competing. Build on "
             f"your partner's last message, add concrete improvements, and give kind, specific, "
             f"constructive criticism. Converge on the best outcome. Keep each reply focused (~150 "
             f"words). {webrule(a.web, tools_ok=True)}")
    header = (f"# Collaboration — {a.rounds} exchanges each\n\n**Goal:** {a.motion}\n\n"
              f"- {label(QWEN['agent'])} + {label(GEMMA['agent'])} working together\n"
              f"- web budget: {a.web} | {ts}\n\n---\n")
    transcript = [header]
    if not a.quiet:
        print(header)
    tg_send(f"🤝 Collaboration — {a.motion}")
    parts = [{**QWEN, "key": f"agent:{QWEN['agent']}:collab-{ts}"},
             {**GEMMA, "key": f"agent:{GEMMA['agent']}:collab-{ts}"}]
    sessfiles, last, turn = {}, None, 0
    for _ in range(a.rounds):
        for d in parts:
            turn += 1
            base = f"GOAL: {a.motion}\n\n"
            msg = base + (f"Open the collaboration with your initial take/plan. {rules}" if last is None
                          else f"Your partner just said:\n\"{last}\"\n\nBuild on it. {rules}")
            txt, sess, full = run_turn(d["agent"], d["key"], msg, d["think"])
            if sess: sessfiles[d["agent"]] = sess
            json.dump(full, open(os.path.join(outdir, f"turn{turn:02d}_{d['agent']}.json"), "w"),
                      indent=2, ensure_ascii=False)
            transcript.append(f"### {turn}. {label(d['agent'])}\n\n{txt}\n")
            if not a.quiet:
                print(f"\n### {turn}. {label(d['agent'])}\n"); stream(txt, a.stream_delay, a.stream)
            tg_send(f"{turn}. {label(d['agent'])}\n\n{txt}")
            last = txt
    return finish(outdir, transcript, sessfiles, a.web, a.quiet)


def main():
    ap = argparse.ArgumentParser(
        prog="debate", formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Two local models (qwen3.6:27b vs gemma4:31b) debate, compete, or collaborate.",
        epilog=__doc__[__doc__.index("Examples:"):])
    ap.add_argument("motion", help="statement (debate), task (compete), or goal (collaborate)")
    ap.add_argument("--mode", choices=["debate", "compete", "collaborate"], default="debate")
    ap.add_argument("--for", dest="for_model", choices=["qwen", "gemma"], default="qwen",
                    help="which model argues FOR the statement (debate mode; default qwen)")
    ap.add_argument("-r", "--rounds", type=int, default=5, help="messages per side")
    ap.add_argument("-w", "--web", type=int, default=3, help="shared web_search budget (0=minimal tools)")
    ap.add_argument("--swap", action="store_true", help="alias for --for gemma")
    ap.add_argument("--no-stream", dest="stream", action="store_false")
    ap.add_argument("--stream-delay", type=float, default=0.006)
    ap.add_argument("--out", default=os.path.join(OC, "debates"))
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--telegram", help="post each turn to Telegram, 'account:chatid' (e.g. default:8852367597)")
    ap.add_argument("--tg", action="store_true", help=f"shorthand for --telegram {BRIAN_TG} (stream to Brian)")
    a = ap.parse_args()
    a.swap = a.swap or a.for_model == "gemma"
    if a.tg and not a.telegram:
        a.telegram = BRIAN_TG
    if a.telegram:
        global TG
        acct, _, target = a.telegram.partition(":")
        TG = (acct, target)
    {"debate": do_debate, "compete": do_compete, "collaborate": do_collaborate}[a.mode](a)


if __name__ == "__main__":
    main()
