FROM caddy:2.11.4-builder AS builder

RUN xcaddy build \
    --with github.com/mholt/caddy-webdav@fa2f366b0d75e54c2e381c0aefc3a8df8bf5794b

FROM caddy:2.11.4-alpine

RUN apk add --no-cache su-exec

COPY --from=builder /usr/bin/caddy /usr/bin/caddy
COPY Caddyfile /etc/caddy/Caddyfile
COPY entrypoint.sh /entrypoint.sh

RUN mkdir -p /srv/photos

ENTRYPOINT ["/entrypoint.sh"]

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget -qO /dev/null http://localhost:2019/config/ || exit 1
