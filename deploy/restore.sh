#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
project="${COMPOSE_PROJECT_NAME:?Set a NEW COMPOSE_PROJECT_NAME for the empty recovery environment}"
if [ "$#" -ne 2 ] || [ "$2" != "--confirm-empty-target=$project" ]; then
    printf 'Usage: COMPOSE_PROJECT_NAME=new-project sh deploy/restore.sh /absolute/backup --confirm-empty-target=new-project\n' >&2
    exit 2
fi
source_dir="$(cd "$1" && pwd)"
test -f "$source_dir/COMPLETE"
(cd "$source_dir" && sha256sum -c SHA256SUMS)
docker compose -p "$project" up -d --wait db
# Refuse any existing public tables or files. This script never drops data.
tables="$(docker compose -p "$project" exec -T db sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "SELECT count(*) FROM information_schema.tables WHERE table_schema=current_schema()"')"
if [ "$tables" != "0" ]; then
    printf 'Target database is not empty; refusing restore.\n' >&2
    exit 3
fi
docker compose -p "$project" run --rm --no-deps -T --entrypoint python app -c 'from pathlib import Path; import sys; sys.exit(3 if any(Path("/app/media").iterdir()) else 0)'
docker compose -p "$project" exec -T db sh -c 'exec pg_restore --exit-on-error --no-owner --no-acl -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < "$source_dir/database.dump"
docker compose -p "$project" run --rm --no-deps -T --entrypoint tar app -C /app/media --no-same-owner --no-same-permissions -xzf - < "$source_dir/photos.tar.gz"
printf 'Restored into project %s. Inspect it before starting app/nginx.\n' "$project"
