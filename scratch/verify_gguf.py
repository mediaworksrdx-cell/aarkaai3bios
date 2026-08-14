import gguf
try:
    reader = gguf.GGUFReader('/workspace/aarkaai3b/aarkaa-3b-f16.gguf')
    print("GGUF is VALID!")
    print("Architecture:", reader.fields.get('general.architecture'))
    print("Tensor count:", len(reader.tensors))
except Exception as e:
    print("Error reading GGUF:", e)
