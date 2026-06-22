FROM caddy:2.11.4-builder AS builder

RUN xcaddy build \
    --with github.com/mholt/caddy-webdav@fa2f366b0d75e54c2e381c0aefc3a8df8bf5794b

FROM caddy:2.11.4-alpine

COPY --from=builder /usr/bin/caddy /usr/bin/caddy
COPY Caddyfile /etc/caddy/Caddyfile

RUN mkdir -p /srv/photos && chown 1000:1000 /srv/photos

USER 1000

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -qO /dev/null http://localhost:2019/config/ || exit 1
