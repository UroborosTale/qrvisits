#!/bin/sh
set -eu
umask 077
cd "$(dirname "$0")/.."
project="${COMPOSE_PROJECT_NAME:-kmz-cards}"
base="${BACKUP_DIR:-./backups}"
mkdir -p "$base"
destination="$base/$(date -u +%Y%m%dT%H%M%SZ)"
mkdir "$destination"
# Pause writers for a consistent database + photos snapshot.
docker compose -p "$project" stop nginx app
trap 'docker compose -p "$project" start app nginx >/dev/null' EXIT HUP INT TERM
docker compose -p "$project" exec -T db sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc' > "$destination/database.dump"
docker compose -p "$project" run --rm --no-deps -T --entrypoint tar app -C /app/media -czf - . > "$destination/photos.tar.gz"
(cd "$destination" && sha256sum database.dump photos.tar.gz > SHA256SUMS)
printf '%s\n' 'Backup complete. Keep these files private and copy them off-server.' > "$destination/COMPLETE"
printf 'Backup: %s\n' "$destination"
