import sys
sys.path.insert(0, "/home/ubuntu/aarkaai3b")
from modules.aarkaa_engine import _gguf_file_path
print("RESOLVED GGUF FILE PATH:", _gguf_file_path)
print("EXISTS:", _gguf_file_path.exists())
