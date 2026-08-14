import subprocess

PEM_KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
PORT = 22
USER = "ec2-user"

cmd = [
    "ssh",
    "-p", str(PORT),
    "-i", PEM_KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    "cd /workspace/aarkaai3b && python3.13 -c \"from modules.gamma_pdf import compile_gamma_pdf; compile_gamma_pdf('Kasi Temple', 'kasi_temple.pdf', template='indigo')\""
]

print("Running remote compile...")
res = subprocess.run(cmd, capture_output=True, text=True)
print("Stdout:", res.stdout)
print("Stderr:", res.stderr)
print("Exit Code:", res.returncode)
