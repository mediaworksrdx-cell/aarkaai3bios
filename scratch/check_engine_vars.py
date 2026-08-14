import sys
sys.path.insert(0, '/workspace/aarkaai3b')
import modules.aarkaa_engine as ae
print("_is_stub status:", ae._is_stub)
print("gguf_file_path:", ae._gguf_file_path, "exists:", ae._gguf_file_path.exists())
print("gguf_coder_path:", ae._gguf_coder_path, "exists:", ae._gguf_coder_path.exists())
