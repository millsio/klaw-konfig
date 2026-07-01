#!/usr/bin/env python3
"""Council Pilot — two local models review the FULL OpenClaw project memory and
collaborate to advance the project, with periodic Claude Code (claude -p) weigh-ins.
Terminal-streamed, debate.py-style. Bounded & attended (a controlled autonomy pilot).

Flow:
  1. Pull every note in the OPENCLAW PROJECT Mem collection (REST) -> verbatim files
     under ~/.openclaw/council/notes/ + INDEX.md. Lossless; models read on demand.
  2. N segments (~15 min each) of qwen3.6:27b (pacifico) <-> gemma4:31b (amethyst)
     collaborating, same session keys throughout (continuity), web search enabled.
  3. After each segment, a headless `claude -p --model opus` weigh-in: assesses
     progress, gives DIRECTION (injected into the next segment) and a NOTE_UPDATE
     block (appended to a dedicated Mem note via REST). Final weigh-in emits
     NEXT_STEPS for Brian.

Reuses debate.py helpers. claude -p runs off the interactive OAuth (verified), no
Agent-SDK token needed. Hard caps: --segments, --segment-min, --max-rounds, timeouts.

  council_pilot.py                                       # real run (3x15)
  council_pilot.py --segment-min 1 --max-rounds 2 --segments 1 --smoke
"""
import argparse, json, os, re, subprocess, sys, time
from datetime import datetime

OC = os.path.expanduser("~/.openclaw")
sys.path.insert(0, os.path.join(OC, "scripts"))
from debate import run_turn, stream, webrule, count_web  # noqa: E402

CID = "82bba4f9-6724-4874-bbcf-1f9ab525b873"
COUNCIL = os.path.join(OC, "council")
NOTES = os.path.join(COUNCIL, "notes")
LOG = os.path.join(COUNCIL, "discussion-log.md")  # cumulative weigh-in log (local; replaced the Mem note)
CONFIG = os.path.expanduser("~/.openclaw/openclaw.json")
API = "https://api.mem.ai/v2/notes"
QWEN = {"agent": "main", "think": "off", "tag": "qwen3.6:27b (pacifico)"}
GEMMA = {"agent": "gemma-amethyst", "think": "medium", "tag": "gemma4:31b (amethyst)"}
MASTER_ID = "f3cc173b-36ee-4356-bab6-99283f17ac4f"
BRIAN_TG = ("default", "8852367597")
TG = None


# ---------------- Mem REST ----------------
def _load_env(path=os.path.expanduser("~/.openclaw/.env")):
    env = {}
    if os.path.exists(path):
        for line in open(path):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def auth():  # no-op after the Mem->local migration (2026-07-01); kept so callers don't break
    return ""


def _known_secrets():
    """Exact secret values to redact (loaded at runtime from config/.env, never hardcoded)."""
    vals = set()
    try:
        cfg = json.load(open(CONFIG))
        gt = cfg.get("gateway", {}).get("auth", {}).get("token")
        if gt and not str(gt).startswith("${"):
            vals.add(str(gt))
    except Exception:
        pass
    for v in _load_env().values():
        if len(v) >= 12 and not v.startswith("${"):
            vals.add(v)
    return vals


_SECRET_RE = re.compile(r"(sk-[A-Za-z0-9._-]{12,}|Bearer\s+[A-Za-z0-9._${}/+-]+|eyJ[A-Za-z0-9._-]{10,})")
_KNOWN = _known_secrets()


def redact(t):
    """Defense-in-depth: scrub secret-shaped strings + known secret values before print/persist."""
    if not t:
        return t
    for s in _KNOWN:
        if s in t:
            t = t.replace(s, "«REDACTED-SECRET»")
    return _SECRET_RE.sub("«REDACTED-SECRET»", t)


def G(url, a):
    import urllib.request
    return json.loads(urllib.request.urlopen(
        urllib.request.Request(url, headers={"Authorization": a}), timeout=30).read())


def mem_append(note_id, block, a):  # repointed to the local discussion log (note_id/a ignored)
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a") as f:
        f.write("\n\n" + block.strip() + "\n")
    return LOG


def fetch_collection(a):
    """Write every collection note verbatim to NOTES/, return (index_text, master_text)."""
    os.makedirs(NOTES, exist_ok=True)
    notes = G(f"{API}?collection_id={CID}&limit=100", a)["results"]
    index, master = ["# OpenClaw Project Memory — full note index\n"], ""
    for m in sorted(notes, key=lambda x: x["title"]):
        n = G(f"{API}/{m['id']}", a)
        slug = re.sub(r"[^a-z0-9]+", "-", n["title"].lower()).strip("-")[:60]
        path = os.path.join(NOTES, f"{slug}.md")
        open(path, "w").write(f"# {n['title']}\n\n{n['content']}\n")
        index.append(f"- `{path}` — {n['title']} ({len(n['content'])} chars)")
        if m["id"] == MASTER_ID:
            master = n["content"]
    open(os.path.join(NOTES, "INDEX.md"), "w").write("\n".join(index))
    return "\n".join(index), master


# ---------------- Telegram (optional) ----------------
def tg(text):
    if not TG or not text:
        return
    for i in range(0, len(text), 3800):
        subprocess.run(["openclaw", "message", "send", "--channel", "telegram",
                        "--account", TG[0], "--target", TG[1], "--message", text[i:i + 3800]],
                       cwd=OC, capture_output=True, text=True)


# ---------------- weigh-in (claude -p) ----------------
WEIGH = """You are Claude Code (Opus), the frontier advisor to a council of two local models \
(qwen3.6:27b and gemma4:31b) that are collaborating to advance the OpenClaw project. They have \
just finished discussion segment {idx} of {total}. They reviewed the OPENCLAW PROJECT Mem collection \
via their own Mem tools. Judge ONLY from the running discussion log and transcript provided below — \
use NO tools and read NO files (in particular, never read `.env`, `openclaw.json`, or any \
credential/secret file).

Respond in EXACTLY these markdown sections:

## PROGRESS
Crisp assessment of where their thinking actually stands — real advances vs. hand-waving, any \
unsupported or [GROUNDED]-but-shaky claims, and whether they are converging prematurely.

## DIRECTION
Concrete, pointed guidance for their NEXT segment: sharpen the most promising thread, kill weak \
ones, name specific project decisions/notes to engage, and inject tension so they don't just agree. \
Address it to both models. {final_note}

## NOTE_UPDATE
A self-contained markdown block (will be appended verbatim to the Mem discussion log). Summarize \
segment {idx}'s substance and your direction. Start it with a `### Round {idx} — Claude Code weigh-in` heading.
{final_section}
=== RUNNING DISCUSSION LOG (Mem note) ===
{note}

=== FULL TRANSCRIPT SO FAR ===
{transcript}
"""
FINAL_SECTION = ("\n## NEXT_STEPS\nFor Brian: your honest read on what this pilot produced and the "
                 "concrete next actions you recommend (including whether/how to push further toward "
                 "autonomy).\n")


def weigh_in(idx, total, transcript, note_text, a, model):
    final = idx == total
    prompt = WEIGH.format(idx=idx, total=total, note=note_text, transcript=transcript,
                          final_note=("This is the FINAL weigh-in — steer them toward concrete conclusions."
                                      if final else ""),
                          final_section=FINAL_SECTION if final else "")
    print(f"\n{'='*70}\n  CLAUDE CODE WEIGH-IN {idx}/{total}  (claude -p --model {model})\n{'='*70}\n")
    tg(f"⚖️ Claude Code weigh-in {idx}/{total} …")
    # weigh-in judges from the piped transcript only; the prompt forbids tools/file reads (no .env access)
    p = subprocess.run(["claude", "-p", "--model", model, "--permission-mode", "bypassPermissions", prompt],
                       stdin=subprocess.DEVNULL, capture_output=True, text=True, cwd=OC, timeout=600)
    if p.returncode != 0:
        print(f"[weigh-in failed: {p.stderr[:300]}]")
        return {"PROGRESS": "", "DIRECTION": "", "NOTE_UPDATE": "", "NEXT_STEPS": ""}
    out = redact(p.stdout.strip())
    print(out + "\n")
    secs = {"PROGRESS": "", "DIRECTION": "", "NOTE_UPDATE": "", "NEXT_STEPS": ""}
    cur = None
    for line in out.splitlines():
        m = re.match(r"^##\s+(PROGRESS|DIRECTION|NOTE_UPDATE|NEXT_STEPS)\s*$", line.strip())
        if m:
            cur = m.group(1); continue
        if cur:
            secs[cur] += line + "\n"
    block = (secs["NOTE_UPDATE"].strip() or f"### Round {idx} — Claude Code weigh-in\n\n{out}")
    if final and secs["NEXT_STEPS"].strip():
        block += "\n\n#### Next steps (for Brian)\n\n" + secs["NEXT_STEPS"].strip()
    try:
        mem_append(NOTE_ID, block, a)
        print(f"[discussion log appended -> {LOG}]")
    except Exception as e:
        print(f"[log append failed: {e}]")
    tg(f"⚖️ Weigh-in {idx}: {secs['PROGRESS'][:300]}")
    return secs


# ---------------- discussion ----------------
RULES = ("You and your partner are COLLABORATING to advance the OpenClaw project — cooperation toward "
         "the best outcome is the ultimate goal. Think critically: do NOT accept a claim or plan just "
         "because your partner said it. Before you agree, pressure-test it — name the weakest "
         "assumption, the unsupported claim, or the likely failure mode, and propose a concrete fix or "
         "improvement. Raise a real challenge whenever you genuinely have one (no rubber-stamping). But "
         "keep criticism CONSTRUCTIVE and in service of quality — do NOT manufacture disagreement or "
         "oppose for its own sake; if you genuinely agree after scrutiny, say so and state what you "
         "checked. Healthy skepticism serves the cooperative goal of producing quality. Every turn must "
         "add something NEW (a grounded fact, a new failure mode, a concrete specific, or a real "
         "objection); if you have nothing new, reply exactly PASS - do not pad with agreement or restate "
         "the plan. Keep each reply "
         "focused (~160 words). Tag factual claims: [GROUNDED] ONLY for something you verified this "
         "session (a file you read from the local docs mirror ~/.openclaw/docs/, a Mem note you read, "
         "or a web_search URL — PREFER the docs mirror over web search for OpenClaw facts) — memory claims are "
         "[ASSUMED]. {web} Name the Mem note you rely on when you lean on project memory.")


CONVERGE_AFTER = 2  # consecutive low-value turns that trigger the deepen gear / early end


_AGREE = ("i concur", "fully aligned", "no further changes", "standing by", "ready for brian",
          "ready for your go-ahead", "ready for approval", "total alignment", "no remaining",
          "diminishing returns", "we have converged", "plan stands", "no changes needed",
          "ready for execution", "ready to hand off", "no further refinements", "we are aligned")


def low_value(txt, prev):
    """A turn that adds nothing new: PASS/NO_REPLY, a short agreement, or a near-restatement."""
    s = (txt or "").strip()
    if s.upper() in ("PASS", "NO_REPLY") or len(s) < 60:
        return True
    low = s.lower()
    if any(p in low for p in _AGREE) and len(s) < 700:
        return True
    if prev:  # novelty vs this agent's previous turn (token overlap)
        a, b = set(low.split()), set(prev.lower().split())
        if a and len(a & b) / len(a | b) > 0.55:
            return True
    return False


DEEPEN = ("You have AGREED on the direction — STOP restating it. Use the remaining time for the harder, "
          "grounded work: turn the agreement into a CONCRETE, VERIFIED artifact — exact config keys and "
          "values, exact commands, the ACTUAL current per-agent tool grants (name them from a Mem note "
          "you read), an acceptance test + rollback for each step, and specific failure modes with "
          "mitigations. New risks or 'we should also' items go in a short Deferred list — do NOT keep "
          "expanding the artifact's scope; finish the current step first. Ground each specific against the "
          "local docs mirror (~/.openclaw/docs/, preferred "
          "for OpenClaw facts), a Mem note you read, or a web_search URL this "
          "session. Each turn must add a NEW concrete detail or a NEW grounded objection — if you truly "
          "have nothing new, reply exactly PASS. Do NOT re-summarize or say you are 'ready for Brian'. {web}")


DEEPEN_MAX = 6  # deepen turns before forcing FINALIZE (curbs scope-accretion / endless new-risk spiral)

FINALIZE = ("FINALIZE MODE — this is the closing exchange. Output the deliverable EXACTLY as it stands "
            "(the concrete artifact: config/commands, tests, rollback). Move every remaining concern or new "
            "risk into a short 'Deferred / parking-lot' list — do NOT expand the artifact or open new "
            "threads; NO new scope. If it is already complete, say so in one line and stop. {web}")


def try_turn(d, key, msg, turn_timeout, retries=1):
    """Run one turn, retrying once on failure (covers transient gateway/parse hiccups)."""
    last_err = None
    for attempt in range(retries + 1):
        try:
            return run_turn(d["agent"], key, msg, d["think"], timeout=turn_timeout)
        except Exception as e:
            last_err = e
            if attempt < retries:
                print(f"[retry {d['agent']} (attempt {attempt + 2}) after: {str(e)[:120]}]")
    raise last_err


def segment(seg_idx, segments, parts, last, direction, master, web, seg_min, max_rounds, transcript,
            stream_delay, turn_timeout):
    web_rule = webrule(web, tools_ok=False)
    if seg_idx == 1:
        intro = ("You are collaborating with another AI model to advance the OpenClaw project. Review the "
                 "project memory by reading the local files in ~/.openclaw/project-notes/ with your read "
                 "tool (INDEX.md is the map). Start with the MASTER note "
                 "(openclaw-project-master__f3cc173b.md, it indexes everything), then the Roadmap and Model "
                 "Strategy notes; read the SPECIFIC notes you need, not everything. You can ALSO read the "
                 "OpenClaw docs mirror on disk at ~/.openclaw/docs/ (INDEX.md is the map); read the SPECIFIC "
                 "file/section you need, NOT whole large files (that wastes your turn). PREFER it over web "
                 "search for any OpenClaw technical/config fact; it is the authoritative local copy. Then "
                 "propose how best to advance the project.")
    else:
        intro = ("Claude Code (your frontier advisor) reviewed the discussion and gave this DIRECTION "
                 "for this segment:\n\n" + (direction or "(none)") + "\n\nConsider it; re-read any "
                 "relevant Mem notes with your Mem tools (read-only) if useful, then continue with your partner.")
    hdr = f"\n{'#'*70}\n# SEGMENT {seg_idx}/{segments}  (~{seg_min} min, web budget {web})\n{'#'*70}\n"
    print(hdr); transcript.append(hdr); tg(f"🧠 Segment {seg_idx}/{segments} starting")
    t0, rounds = time.time(), 0
    sess, prev, phase, conv, stop = {}, {}, "converge", 0, False
    deepen_turns, final_turns = 0, 0
    while not stop and rounds < max_rounds and (time.time() - t0) < seg_min * 60:
        rounds += 1
        for d in parts:
            active = ({"deepen": DEEPEN, "finalize": FINALIZE}.get(phase, RULES)).format(web=web_rule)
            if last is None:
                msg = f"{intro}\n\n{active}"
            elif rounds == 1 and seg_idx > 1 and d is parts[0]:
                msg = f"{intro}\n\nYour partner's last message was:\n\"{last}\"\n\n{active}"
            else:
                msg = f"Your partner just said:\n\"{last}\"\n\n{active}"
            opening = last is None
            try:
                txt, sf, full = try_turn(d, d["key"], msg, turn_timeout)
            except Exception as e:
                print(f"[turn failed ({d['agent']}): {str(e)[:200]}]")
                transcript.append(f"\n### S{seg_idx}.{rounds} — {d['tag']} [TURN FAILED]\n\n{str(e)[:300]}\n")
                tg(f"⚠️ {d['tag']} turn failed (S{seg_idx}.{rounds})")
                # if the OPENER died, keep last=None so the partner opens with the full kickoff (no null
                # segment); otherwise use the liveness guard (never feed the crash text to the partner)
                if not opening:
                    last = ("(Your partner's previous turn did not complete — a transient timeout, no "
                            "content. Continue advancing the project yourself; do not reply to this notice.)")
                continue
            if sf:
                sess[d["agent"]] = sf
            txt = redact(txt)  # never let a secret a model surfaced reach the terminal/Mem
            tag = f"{d['tag']}" + (f" [{phase}]" if phase != "converge" else "")
            head = f"\n### S{seg_idx}.{rounds} — {tag}\n"
            print(head); stream(txt, stream_delay, True)
            transcript.append(f"{head}\n{txt}\n")
            tg(f"{tag} (S{seg_idx}.{rounds}):\n\n{txt}")
            # convergence tracking: consecutive low-value (agreement / PASS / restated) turns
            conv = conv + 1 if low_value(txt, prev.get(d["agent"], "")) else 0
            prev[d["agent"]] = txt
            last = ("(Your partner had nothing new to add.)"
                    if txt.strip().upper() in ("PASS", "NO_REPLY") else txt)
            if phase == "finalize":
                final_turns += 1
                if final_turns >= 2 or conv >= 1:
                    print("\n[-> finalized - ending segment]")
                    transcript.append("\n_-> finalized - ending segment._\n"); tg("-> finalized")
                    stop = True
                    break
            elif phase == "deepen":
                deepen_turns += 1
                if conv >= CONVERGE_AFTER:
                    print("\n[-> deepen exhausted - ending segment early]")
                    transcript.append("\n_-> deepen exhausted - ending segment early._\n")
                    tg("-> deepen exhausted - ending segment early")
                    stop = True
                    break
                elif deepen_turns >= DEEPEN_MAX:
                    phase, conv = "finalize", 0
                    m = "scope cap reached -> FINALIZE: ship the artifact as-is, defer open items, no new scope"
                    print(f"\n[-> {m}]"); transcript.append(f"\n_-> {m}_\n"); tg(f"-> {m}")
            elif conv >= CONVERGE_AFTER:
                phase, conv = "deepen", 0
                m = ("converged on direction -> switching to DEEPEN: ground it into a concrete, verified "
                     "artifact (exact config/commands, real tool grants, tests, rollback)")
                print(f"\n[-> {m}]"); transcript.append(f"\n_-> {m}_\n"); tg(f"-> {m}")
    used = sum(count_web(s) for s in sess.values())
    print(f"\n[segment {seg_idx}: {rounds} rounds, {int(time.time()-t0)}s, phase={phase}, web used ~{used}/{web}]")
    return last


# ---------------- main ----------------
def main():
    ap = argparse.ArgumentParser(prog="council_pilot", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--note-id", default=None, help="(deprecated; discussion log is now local at council/discussion-log.md)")
    ap.add_argument("--segments", type=int, default=3)
    ap.add_argument("--segment-min", type=float, default=15.0, help="wall-clock minutes per segment")
    ap.add_argument("--max-rounds", type=int, default=30, help="safety cap on exchanges/segment (time is the primary limiter)")
    ap.add_argument("--turn-timeout", type=int, default=280, help="per-model-turn timeout secs (keep under the gateway ~330s ceiling)")
    ap.add_argument("--web", type=int, default=6, help="web_search budget per segment")
    ap.add_argument("--model", default="opus", help="claude -p model for weigh-ins")
    ap.add_argument("--stream-delay", type=float, default=0.004)
    ap.add_argument("--tg", action="store_true", help="also stream to Brian's Telegram")
    ap.add_argument("--smoke", action="store_true", help="tiny test run (marks the note as a smoke test)")
    a = ap.parse_args()
    global TG, NOTE_ID
    NOTE_ID = a.note_id
    if a.tg:
        TG = BRIAN_TG
    auth_h = auth()
    ts = datetime.now().strftime("%Y-%m-%d-%H%M%S")
    outdir = os.path.join(COUNCIL, "runs", ts)
    os.makedirs(outdir, exist_ok=True)

    master = ""  # agents self-serve by reading ~/.openclaw/project-notes/ with their read tool (no dossier)
    print("[council] agents will review the local project-notes/ via their read tool (read-only).\n")

    parts = [{**QWEN, "key": f"agent:{QWEN['agent']}:council-{ts}"},
             {**GEMMA, "key": f"agent:{GEMMA['agent']}:council-{ts}"}]
    transcript = [f"# Council Pilot — {ts}\n\nqwen3.6:27b (pacifico) <-> gemma4:31b (amethyst), "
                  f"{a.segments} segments, weigh-ins by claude -p --model {a.model}\n"]
    tg(f"🏛️ Council Pilot starting — {a.segments} segments × ~{a.segment_min:g}m")

    last, direction = None, None
    for seg in range(1, a.segments + 1):
        last = segment(seg, a.segments, parts, last, direction, master, a.web,
                       a.segment_min, a.max_rounds, transcript, a.stream_delay, a.turn_timeout)
        open(os.path.join(outdir, "transcript.md"), "w").write("\n".join(transcript))
        prior_log = open(LOG).read() if os.path.exists(LOG) else ""
        secs = weigh_in(seg, a.segments, "\n".join(transcript), prior_log, auth_h, a.model)
        direction = secs["DIRECTION"].strip()
        transcript.append(f"\n## Claude Code weigh-in {seg}\n\n**DIRECTION:**\n{direction}\n")
        open(os.path.join(outdir, "transcript.md"), "w").write("\n".join(transcript))

    print(f"\n[council] done. transcript: {os.path.join(outdir, 'transcript.md')}")
    tg("🏛️ Council Pilot complete — see the local discussion log + next steps.")


if __name__ == "__main__":
    main()
