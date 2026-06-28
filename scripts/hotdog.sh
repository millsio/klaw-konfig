#!/usr/bin/env bash
# hotdog — deterministic dispatcher for the local-model Arena.
# Runnable from the terminal AND callable by the /hotdog Telegram hook.
#
#   hotdog.sh debate  "<statement>"   [--tg <acct:chatid>] [--rounds N] [--web N]
#   hotdog.sh compete "<task>"        [--tg ...]
#   hotdog.sh collab  "<goal>"        [--tg ...]
#   hotdog.sh judge                   [--tg ...]   # judge the latest debate
#   hotdog.sh stop                                  # abort any running debate (frees its context)
#   hotdog.sh drop                                  # unload gemma on amethyst (frees VRAM)
#   hotdog.sh roll                                  # unload then reload gemma (pre-warm)
#   hotdog.sh help
#
# --dry prints what it would do without running.
set -uo pipefail

OC="$HOME/.openclaw"
DEBATE="$OC/scripts/debate.py"
JUDGE="$OC/scripts/judge.py"
AMETHYST="http://100.113.225.2:11434"
GEMMA_MODEL="gemma4:31b"
BRIAN_TG="default:8852367597"

DRY=0; TG=""; ROUNDS=5; WEB=3
sub="${1:-help}"; shift || true
topic=""
# first non-flag arg after subcommand is the topic
while [ $# -gt 0 ]; do
  case "$1" in
    --tg) TG="$BRIAN_TG"; shift ;;
    --tg-to) TG="$2"; shift 2 ;;
    --tg-to=*) TG="${1#*=}"; shift ;;
    --rounds) ROUNDS="$2"; shift 2 ;;
    --web) WEB="$2"; shift 2 ;;
    --dry) DRY=1; shift ;;
    *) [ -z "$topic" ] && topic="$1"; shift ;;
  esac
done

run() { if [ "$DRY" = 1 ]; then echo "DRY: $*"; else "$@"; fi; }

tg_arg=(); quiet_arg=()
# only suppress terminal output when streaming to Telegram; a plain CLI run should print
if [ -n "$TG" ]; then tg_arg=(--telegram "$TG"); quiet_arg=(--quiet); fi

case "$sub" in
  debate|compete|collab|collaborate)
    case "$sub" in collab|collaborate) mode=collaborate ;; compete) mode=compete ;; *) mode=debate ;; esac
    [ -z "$topic" ] && { echo "usage: hotdog.sh $sub \"<topic>\" [--tg ...]"; exit 2; }
    run python3 "$DEBATE" "$topic" --mode "$mode" --rounds "$ROUNDS" --web "$WEB" "${quiet_arg[@]}" "${tg_arg[@]}"
    ;;
  judge)
    run python3 "$JUDGE" "${tg_arg[@]}"
    ;;
  stop)
    # abort any running debate/judge processes; the models' KV cache is freed as their
    # ephemeral debate sessions end. Does NOT unload the model.
    run pkill -f "$DEBATE" ; run pkill -f "$JUDGE"
    echo "stopped any running debates"
    ;;
  drop)
    # unload gemma on amethyst (one-time keep_alive:0; does NOT change the host's forever default)
    run curl -s "$AMETHYST/api/generate" -d "{\"model\":\"$GEMMA_MODEL\",\"keep_alive\":0}" >/dev/null
    echo "dropped $GEMMA_MODEL on amethyst (VRAM freed; reloads on next use)"
    ;;
  roll)
    # stop, drop, and ROLL: unload then reload gemma so it's hot for next use
    run curl -s "$AMETHYST/api/generate" -d "{\"model\":\"$GEMMA_MODEL\",\"keep_alive\":0}" >/dev/null
    run curl -s "$AMETHYST/api/generate" -d "{\"model\":\"$GEMMA_MODEL\",\"prompt\":\"hi\",\"stream\":false,\"keep_alive\":-1}" >/dev/null
    echo "rolled $GEMMA_MODEL on amethyst (unloaded + reloaded resident)"
    ;;
  help|*)
    cat <<'EOF'
hotdog — local-model Arena dispatcher
  debate  "<statement>"   two models argue for/against
  compete "<task>"        both attempt the same task
  collab  "<goal>"        work together toward a goal
  judge                   Opus judge of the latest run
  stop                    abort a running debate (frees its context)
  drop                    unload gemma on amethyst (frees VRAM)
  roll                    unload + reload gemma (pre-warm)
Flags: --tg <acct:chatid> (stream to Telegram), --rounds N, --web N, --dry
EOF
    ;;
esac
