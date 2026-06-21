#!/usr/bin/env bash
set -euo pipefail
cd "$HOME/.openclaw"
python3 scripts/mirror_openclaw_docs.py >> "$HOME/.openclaw/docs/.mirror_log.txt" 2>&1 || true
git add -A
if ! git diff --cached --quiet; then
  git commit -m "nightly: $(date -Iseconds)"
  GIT_SSH_COMMAND="ssh -i $HOME/.ssh/openclaw_deploy -o IdentitiesOnly=yes" git push origin main
fi
