#!/bin/sh
set -eu

script_dir="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
backup_dir="${BACKUP_DIR:-$script_dir/backups}"

mkdir -p "$backup_dir"

POSTGRES_USER="${POSTGRES_USER:-$(grep '^POSTGRES_USER=' "$script_dir/.env" | cut -d '=' -f 2-)}"
POSTGRES_DB="${POSTGRES_DB:-$(grep '^POSTGRES_DB=' "$script_dir/.env" | cut -d '=' -f 2-)}"

docker compose -f "$script_dir/docker-compose.yml" --env-file "$script_dir/.env" \
  exec -T db pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
  > "$backup_dir/postgres-$timestamp.sql"
