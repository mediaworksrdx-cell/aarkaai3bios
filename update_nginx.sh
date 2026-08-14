#!/usr/bin/env bash
set -ex

# Write the new Nginx configuration file using sudo tee
sudo tee /etc/nginx/conf.d/synthetix.conf > /dev/null << 'EOF'
server {
    server_name synthetixanalytics.com www.synthetixanalytics.com;

    # Backend Download Endpoint
    location /download/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Frontend Next.js site
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    listen 443 ssl; # managed by Certbot
    ssl_certificate /etc/letsencrypt/live/synthetixanalytics.com/fullchain.pem; # managed by Certbot
    ssl_certificate_key /etc/letsencrypt/live/synthetixanalytics.com/privkey.pem; # managed by Certbot
    include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
}

server {
    if ($host = www.synthetixanalytics.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

    if ($host = synthetixanalytics.com) {
        return 301 https://$host$request_uri;
    } # managed by Certbot

    listen 80;
    server_name synthetixanalytics.com www.synthetixanalytics.com;
    return 404; # managed by Certbot
}
EOF

# Test Nginx configuration and reload
sudo nginx -t
sudo systemctl reload nginx
echo "Nginx reloaded successfully with /download proxy route."
