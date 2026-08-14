import subprocess

KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
USER = "ec2-user"

script_content = """
import gguf
try:
    reader = gguf.GGUFReader('/workspace/aarkaai3b/aarkaa-3b-f32.gguf')
    print("GGUF is VALID!")
    print("Architecture:", reader.fields.get('general.architecture'))
    print("Tensor count:", len(reader.tensors))
except Exception as e:
    print("Error reading GGUF:", e)
"""

with open("scratch/verify_gguf.py", "w", newline="\n") as f:
    f.write(script_content)

# Upload the script
scp_cmd = [
    "scp",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    "scratch/verify_gguf.py",
    f"{USER}@{HOST}:/workspace/aarkaai3b/verify_gguf.py"
]
subprocess.run(scp_cmd)

# Run it
ssh_cmd = [
    "ssh",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    "python3.13 /workspace/aarkaai3b/verify_gguf.py"
]

res = subprocess.run(ssh_cmd, capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
