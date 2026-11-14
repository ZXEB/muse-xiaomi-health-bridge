#!/usr/bin/env bash
# Back up SQLite and the mifit login volume. Keep 14 days by default.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
STAMP="$(date +%Y%m%d-%H%M%S)"
KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"
mkdir -p backups
chmod 700 backups

echo "[backup] sqlite -> backups/health-${STAMP}.db"
docker compose exec -T bridge sqlite3 /data/health.db ".backup '/data/health-backup.db'"
docker compose cp bridge:/data/health-backup.db "backups/health-${STAMP}.db"
docker compose exec -T bridge rm -f /data/health-backup.db
chmod 600 "backups/health-${STAMP}.db"

echo "[backup] mifit session -> backups/mifit-session-${STAMP}.tgz"
docker run --rm \
  -v mifit_session:/src:ro \
  -v "$PWD/backups":/backup \
  alpine:3.20 tar czf "/backup/mifit-session-${STAMP}.tgz" -C /src .
chmod 600 "backups/mifit-session-${STAMP}.tgz"

if [[ -n "${BACKUP_PASSPHRASE:-}" ]]; then
  echo "[backup] encrypting with BACKUP_PASSPHRASE"
  for f in "backups/health-${STAMP}.db" "backups/mifit-session-${STAMP}.tgz"; do
    openssl enc -aes-256-cbc -pbkdf2 -salt -pass env:BACKUP_PASSPHRASE -in "$f" -out "$f.enc"
    rm -f "$f"
  done
fi

find backups -type f -mtime +"$KEEP_DAYS" -delete
echo "[backup] done; files:"
ls -lh backups | tail -n +2
