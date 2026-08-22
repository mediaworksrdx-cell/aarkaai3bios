import torch
from diffusers import StableDiffusionPipeline
import os
import shutil

def main():
    print("============================================================")
    # AARKAA-VISION Standalone Model Merger
    print("AARKAA-VISION Standalone Model Merger")
    print("============================================================")

    token = os.environ.get("HF_TOKEN", "")
    base_model = "CompVis/stable-diffusion-v1-4"
    lora_model = "rthshr/aarkaa-ai-vision"
    
    # Save directory for the standalone model
    output_dir = os.path.join(os.path.dirname(__file__), "aarkaa-vision-standalone")

    try:
        print("\n1. Loading base model and LoRA weights...")
        pipe = StableDiffusionPipeline.from_pretrained(
            base_model,
            torch_dtype=torch.float16,
            use_safetensors=True
        )
        
        print("\n2. Loading LoRA weights...")
        pipe.load_lora_weights(lora_model, token=token)
        
        print("\n3. Fusing LoRA weights directly into the base model parameters...")
        # fuse_lora merges the adapter weights into the UNet/Text Encoder linear layers permanently
        pipe.fuse_lora()
        
        print(f"\n5. Saving standalone fused model to: {output_dir}")
        if os.path.exists(output_dir):
            print("Target directory exists, clearing it first...")
            shutil.rmtree(output_dir)
            
        pipe.save_pretrained(output_dir, safe_serialization=True)
        print("\n============================================================")
        print("SUCCESS: Standalone AARKAA-VISION model created.")
        print(f"Location: {os.path.abspath(output_dir)}")
        print("============================================================")
        
    except Exception as e:
        print(f"\nError merging models: {e}")

if __name__ == "__main__":
    main()
