#!/usr/bin/env bash
# Sync this repo's documentation into the partner-facing docs repo and push.
#
#   scripts/sync-docs.sh                    # uses ../ashfordbriggs-docs (clone it first)
#   DOCS_REPO=/path/to/clone scripts/sync-docs.sh
#   NO_PUSH=1 scripts/sync-docs.sh          # commit in the docs repo, do not push
#
# Source of truth is docs/ (plus deploy/ubuntu/) in THIS repo. The docs repo's
# paladin-website/ folder is replaced wholesale on every sync, so never edit
# it there. Runs on Git Bash (Windows), macOS and Linux.
set -euo pipefail

HERE="$(cd "$(dirname "$0")/.." && pwd)"
DOCS_REPO="${DOCS_REPO:-$HERE/../ashfordbriggs-docs}"
TARGET="$DOCS_REPO/paladin-website"

if [ ! -d "$DOCS_REPO/.git" ]; then
  echo "docs repo not found at $DOCS_REPO" >&2
  echo "clone it first:  git clone https://github.com/Vybecode-LTD/ashfordbriggs-docs.git \"$DOCS_REPO\"" >&2
  exit 1
fi

# Safety net: refuse to publish anything that looks like a secret.
if grep -rEl "sk-ant-api|BEGIN (RSA|OPENSSH|EC) PRIVATE|AKIA[0-9A-Z]{16}" "$HERE/docs" "$HERE/deploy/ubuntu" 2>/dev/null; then
  echo "refusing to sync: the files above contain what looks like a secret" >&2
  exit 1
fi

SRC_COMMIT="$(git -C "$HERE" rev-parse --short HEAD)"

rm -rf "$TARGET"
mkdir -p "$TARGET/deploy/ubuntu"
cp -r "$HERE/docs/." "$TARGET/"
# The worker units are included because DEPLOY-UBUNTU.md section 5.5 tells the
# reader to install them; a runbook that points at files the docs repo does not
# carry is a dead end for whoever is following it.
cp "$HERE/deploy/ubuntu/docker-compose.yml" "$HERE/deploy/ubuntu/Caddyfile" \
   "$HERE/deploy/ubuntu/.env.example" \
   "$HERE/deploy/ubuntu/paladin-worker.service" "$HERE/deploy/ubuntu/paladin-worker.timer" \
   "$TARGET/deploy/ubuntu/"
find "$TARGET" -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null || true

cd "$DOCS_REPO"
git add -A paladin-website
if git diff --cached --quiet; then
  echo "docs repo already matches Paladin@$SRC_COMMIT"
  exit 0
fi
git commit -q -m "paladin-website: sync docs from Vybecode-LTD/Paladin@$SRC_COMMIT"
if [ -z "${NO_PUSH:-}" ]; then
  git push -q origin HEAD
fi
echo "synced Paladin@$SRC_COMMIT -> $DOCS_REPO ($(git rev-parse --short HEAD))"
