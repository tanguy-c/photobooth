#!/bin/sh
set -e

PUID=${PUID:-1000}
PGID=${PGID:-$PUID}

chown -R "$PUID:$PGID" /data /config
chown "$PUID:$PGID" /srv/photos

exec su-exec "$PUID:$PGID" caddy run --config /etc/caddy/Caddyfile --adapter caddyfile
