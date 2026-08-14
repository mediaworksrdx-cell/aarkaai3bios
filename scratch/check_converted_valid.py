import subprocess

KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
USER = "ec2-user"

script = """
import gguf
try:
    reader = gguf.GGUFReader('/workspace/aarkaai3b/aarkaa-3b-f32.gguf')
    print("GGUF is VALID!")
    print("Architecture:", reader.fields.get('general.architecture'))
    print("Parameters count:", len(reader.tensors))
except Exception as e:
    print("Error reading GGUF:", e)
"""

cmd = [
    "ssh",
    "-i", KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    f"python3.13 -c \\\"{script}\\\""
]

res = subprocess.run(cmd, capture_output=True, text=True)
print("STDOUT:")
print(res.stdout)
print("STDERR:")
print(res.stderr)
