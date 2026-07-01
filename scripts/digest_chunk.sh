#!/usr/bin/env bash
# Window-chunked driver for building the INITIAL docs digest across several 5-hour usage windows.
# Fired by dated cron lines (one per window); each run does a bounded number of NEW map batches
# (--max-new N) and resumes from ~/.openclaw/.digest-cache. The final run (N=0) maps the remainder
# and runs the Opus reduce, writing ~/.openclaw/docs-digest.md.
#
# TEMPORARY: once the digest lands (header shows "— FULL._"), each subsequent fire no-ops. Remove the
# dated cron lines after completion. Steady-state weekly refresh will be the incremental digest (roadmap).
set -uo pipefail
export PATH=/home/klaw/.local/bin:/usr/bin:/bin
export HOME=/home/klaw
cd /home/klaw/.openclaw || exit 1
OUT=/home/klaw/.openclaw/docs-digest.md
N="${1:-0}"
ts() { date '+%Y-%m-%d %H:%M:%S %Z'; }
cleanup_cron() {  # once the digest is FULL, self-remove the temporary chunk cron lines (no manual step)
  crontab -l 2>/dev/null | grep -v 'digest_chunk.sh' | grep -v 'TEMP: initial docs-digest' | crontab - 2>/dev/null \
    && echo "[$(ts)] removed temporary digest_chunk cron lines"
}
if grep -q 'FULL\._' "$OUT" 2>/dev/null; then
  echo "[$(ts)] digest already FULL — skip (max-new=$N)"
  cleanup_cron
  exit 0
fi
echo "[$(ts)] digest_chunk START --max-new=$N"
python3 -u scripts/docs_digest.py --full --max-new "$N"
rc=$?
echo "[$(ts)] digest_chunk END rc=$rc"
if grep -q 'FULL\._' "$OUT" 2>/dev/null; then
  echo "[$(ts)] digest is FULL"
  cleanup_cron
fi
exit $rc
