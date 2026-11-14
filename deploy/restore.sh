#!/usr/bin/env bash
# Restore a backup made by backup.sh.
# Usage: ./deploy/restore.sh 20261114-050000
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
STAMP="${1:?usage: restore.sh <stamp> e.g. 20261114-050000}"
DB="backups/health-${STAMP}.db"
SESSION="backups/mifit-session-${STAMP}.tgz"

if [[ -n "${BACKUP_PASSPHRASE:-}" ]]; then
  for f in "$DB" "$SESSION"; do
    if [[ -f "$f.enc" ]]; then
      openssl enc -d -aes-256-cbc -pbkdf2 -pass env:BACKUP_PASSPHRASE -in "$f.enc" -out "$f"
    fi
  done
fi

[[ -f "$DB" ]] || { echo "missing $DB" >&2; exit 1; }
[[ -f "$SESSION" ]] || { echo "missing $SESSION" >&2; exit 1; }

echo "[restore] stopping services"
docker compose stop bridge sync

echo "[restore] database"
docker run --rm --user 1000:1000 \
  -v health_data:/data \
  -v "$PWD/backups":/backup:ro \
  alpine:3.20 sh -c "rm -f /data/health.db /data/health.db-wal /data/health.db-shm; cp /backup/health-${STAMP}.db /data/health.db"

echo "[restore] mifit session"
docker run --rm --user 1000:1000 \
  -v mifit_session:/dst \
  -v "$PWD/backups":/backup:ro \
  alpine:3.20 sh -c "rm -rf /dst/* /dst/.[!.]* 2>/dev/null || true; tar xzf /backup/mifit-session-${STAMP}.tgz -C /dst"

echo "[restore] starting services"
docker compose start bridge sync

echo "[restore] done; check /healthz and /v1/status"
