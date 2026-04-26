#!/bin/bash
set -euo pipefail

apt-get update
apt-get install -y docker.io nginx awscli
systemctl enable docker
systemctl start docker

mkdir -p /opt/github-analytics/data
aws s3 cp s3://${dashboard_bucket}/duckdb/dashboard.duckdb /opt/github-analytics/data/dashboard.duckdb || true

docker pull ${api_image}
docker rm -f github-analytics-api || true
docker run -d \
  --name github-analytics-api \
  --restart always \
  -p 127.0.0.1:8000:8000 \
  -e DASHBOARD_DB_PATH=/data/dashboard.duckdb \
  -e FRONTEND_ORIGINS=https://<your_frontend_domain_here> \
  -v /opt/github-analytics/data:/data \
  ${api_image}

cat >/etc/nginx/sites-available/github-analytics-api <<'NGINX'
server {
    listen 80;
    server_name _;

    client_max_body_size 1m;

    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "no-referrer" always;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/github-analytics-api /etc/nginx/sites-enabled/github-analytics-api
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
