import subprocess

KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
USER = "ec2-user"

nginx_conf = """
server {
    listen 80;
    server_name synthetixanalytics.com www.synthetixanalytics.com;

    # Frontend Next.js site
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
"""

setup_commands = f"""
sudo dnf install -y nginx
sudo tee /etc/nginx/conf.d/synthetix.conf << 'EOF'
{nginx_conf}
EOF
sudo systemctl enable nginx
sudo systemctl restart nginx
sudo nginx -t
"""

cmd = [
    "ssh",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    setup_commands
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
