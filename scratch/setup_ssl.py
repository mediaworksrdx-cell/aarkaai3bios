import subprocess

KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
USER = "ec2-user"

setup_ssl_cmds = """
# Install certbot using pip for Python 3.13 (globally / with sudo)
sudo python3.13 -m pip install --break-system-packages certbot certbot-nginx || sudo pip3 install --break-system-packages certbot certbot-nginx

# Try running certbot to automatically configure Nginx with SSL certificate
sudo ~/.local/bin/certbot --nginx -d synthetixanalytics.com -d www.synthetixanalytics.com --non-interactive --agree-tos -m testadmin@aarkaai.com || \
sudo /usr/local/bin/certbot --nginx -d synthetixanalytics.com -d www.synthetixanalytics.com --non-interactive --agree-tos -m testadmin@aarkaai.com || \
sudo certbot --nginx -d synthetixanalytics.com -d www.synthetixanalytics.com --non-interactive --agree-tos -m testadmin@aarkaai.com
"""

cmd = [
    "ssh",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    setup_ssl_cmds
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
