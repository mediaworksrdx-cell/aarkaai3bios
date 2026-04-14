"""
Convert AARKAA-3B from HuggingFace safetensors to GGUF format.

Run on the server:
    pip install torch transformers gguf
    python convert_to_gguf.py
"""
import subprocess
import sys
import os

MODEL_DIR = os.path.join(os.path.dirname(__file__), "aarkaa-3b")
OUTPUT_F16 = os.path.join(os.path.dirname(__file__), "aarkaa-3b-f16.gguf")
OUTPUT_Q8 = os.path.join(os.path.dirname(__file__), "aarkaa-3b-q8.gguf")


def main():
    print("=" * 60)
    print("AARKAA-3B Model Converter (safetensors -> GGUF)")
    print("=" * 60)

    # Step 1: Clone llama.cpp if not present
    llama_dir = os.path.join(os.path.dirname(__file__), "llama.cpp")
    if not os.path.exists(llama_dir):
        print("\n[1/3] Cloning llama.cpp...")
        subprocess.run([
            "git", "clone", "--depth", "1",
            "https://github.com/ggerganov/llama.cpp",
            llama_dir,
        ], check=True)
    else:
        print("\n[1/3] llama.cpp already present")

    # Install conversion dependencies
    print("\n[2/3] Installing conversion dependencies...")
    subprocess.run([
        sys.executable, "-m", "pip", "install",
        "torch", "transformers", "gguf", "numpy", "sentencepiece",
    ], check=True)

    # Step 2: Convert to GGUF f16
    convert_script = os.path.join(llama_dir, "convert_hf_to_gguf.py")
    if not os.path.exists(OUTPUT_F16):
        print(f"\n[3/3] Converting {MODEL_DIR} -> {OUTPUT_F16}...")
        subprocess.run([
            sys.executable, convert_script,
            MODEL_DIR,
            "--outfile", OUTPUT_F16,
            "--outtype", "f16",
        ], check=True)
        print(f"Created: {OUTPUT_F16}")
    else:
        print(f"\n[3/3] {OUTPUT_F16} already exists")

    # Step 3: Quantize to Q8 (optional but recommended)
    print("\n" + "=" * 60)
    print(f"F16 GGUF created: {OUTPUT_F16}")
    print(f"Size: {os.path.getsize(OUTPUT_F16) / 1e9:.1f} GB")
    print()
    print("To quantize to Q8 (faster, ~99% quality):")
    print("  1. Build llama.cpp: cd llama.cpp && make")
    print(f"  2. Quantize: ./llama.cpp/llama-quantize {OUTPUT_F16} {OUTPUT_Q8} q8_0")
    print()
    print("Or just use the F16 GGUF as-is (already much faster than PyTorch)")
    print("=" * 60)


if __name__ == "__main__":
    main()
