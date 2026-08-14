import urllib.request
try:
    req = urllib.request.Request("http://169.254.169.254/latest/api/token")
    req.add_header("X-aws-ec2-metadata-token-ttl-seconds", "60")
    req.method = "PUT"
    token = urllib.request.urlopen(req).read().decode()
    
    req2 = urllib.request.Request("http://169.254.169.254/latest/meta-data/instance-id")
    req2.add_header("X-aws-ec2-metadata-token", token)
    iid = urllib.request.urlopen(req2).read().decode()
    
    req3 = urllib.request.Request("http://169.254.169.254/latest/meta-data/placement/region")
    req3.add_header("X-aws-ec2-metadata-token", token)
    reg = urllib.request.urlopen(req3).read().decode()
    
    print(f"IID:{iid} REG:{reg}")
except Exception as e:
    print("Error:", e)
