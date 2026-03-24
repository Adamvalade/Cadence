#!/bin/sh
set -e

if [ -n "${POSTGRES_PASSWORD_FILE:-}" ] && [ -r "$POSTGRES_PASSWORD_FILE" ]; then
  export PGPASSWORD="$(tr -d '\n\r' < "$POSTGRES_PASSWORD_FILE")"
elif [ -n "${POSTGRES_PASSWORD:-}" ]; then
  export PGPASSWORD="$POSTGRES_PASSWORD"
else
  echo "pg-backup: set POSTGRES_PASSWORD or POSTGRES_PASSWORD_FILE (e.g. in .env)." >&2
  exit 1
fi

mkdir -p /backups

while true; do
  ts="$(date +%Y%m%d-%H%M%S)"
  if pg_dump -h db -U cadence cadence | gzip >"/backups/cadence-${ts}.sql.gz"; then
    find /backups -name 'cadence-*.sql.gz' -mtime +14 -delete 2>/dev/null || true
  fi
  sleep 86400
done
