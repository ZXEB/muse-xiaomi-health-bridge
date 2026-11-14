#!/usr/bin/env bash
# One-shot TLS setup for the bridge behind the existing Nginx (BT Panel layout).
# Usage: ./deploy/bootstrap_tls.sh health.xp6.top you@example.com
set -euo pipefail

DOMAIN="${1:?usage: bootstrap_tls.sh <domain> [email]}"
EMAIL="${2:-admin@${DOMAIN}}"
EXPECTED_IP="${EXPECTED_IP:-38.76.201.208}"
WEBROOT="/www/wwwroot/${DOMAIN}"
CONF_DIR="/www/server/panel/vhost/nginx"
CONF="${CONF_DIR}/${DOMAIN}.conf"
LIVE="/etc/letsencrypt/live/${DOMAIN}"

resolved="$(getent hosts "${DOMAIN}" | awk '{print $1}' | head -1 || true)"
if [[ "${resolved}" != "${EXPECTED_IP}" ]]; then
  echo "DNS mismatch: ${DOMAIN} -> ${resolved:-none}, expected ${EXPECTED_IP}" >&2
  exit 1
fi

mkdir -p "${WEBROOT}/.well-known/acme-challenge"
chown -R www:www "${WEBROOT}" 2>/dev/null || true
mkdir -p "${CONF_DIR}"

echo "[tls] writing HTTP-only vhost for ACME"
cat > "${CONF}" <<EOF
server {
    listen 80;
    server_name ${DOMAIN};
    root ${WEBROOT};

    location /.well-known/acme-challenge/ {
        root ${WEBROOT};
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}
EOF

nginx -t
nginx -s reload

if [[ ! -f "${LIVE}/fullchain.pem" ]]; then
  echo "[tls] requesting certificate"
  docker run --rm \
    -v "${WEBROOT}:/var/www" \
    -v /etc/letsencrypt:/etc/letsencrypt \
    certbot/certbot certonly --webroot -w /var/www \
    -d "${DOMAIN}" --email "${EMAIL}" --agree-tos --non-interactive
fi

echo "[tls] writing HTTPS vhost"
cat > "${CONF}" <<EOF
server {
    listen 80;
    server_name ${DOMAIN};

    location /.well-known/acme-challenge/ {
        root ${WEBROOT};
    }

    location / {
        return 301 https://\$host\$request_uri;
    }
}

server {
    listen 443 ssl;
    http2 on;
    server_name ${DOMAIN};

    ssl_certificate     ${LIVE}/fullchain.pem;
    ssl_certificate_key ${LIVE}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    add_header Strict-Transport-Security "max-age=31536000" always;

    client_max_body_size 4m;

    location /mcp {
        proxy_pass http://127.0.0.1:8789;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }

    location / {
        proxy_pass http://127.0.0.1:8787;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }
}
EOF

nginx -t
nginx -s reload

echo "[tls] renewal cron"
cat > /etc/cron.d/health-bridge-tls <<EOF
# Renew the health bridge certificate weekly and reload Nginx.
17 4 * * 1 root docker run --rm -v /etc/letsencrypt:/etc/letsencrypt -v ${WEBROOT}:/var/www certbot/certbot renew --webroot -w /var/www --quiet && nginx -s reload
EOF
chmod 644 /etc/cron.d/health-bridge-tls

echo "[tls] done; checking https://${DOMAIN}/healthz"
curl -fsS "https://${DOMAIN}/healthz" && echo
