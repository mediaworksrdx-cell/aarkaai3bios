import torch
from diffusers import StableDiffusionPipeline
import os

token = os.environ.get("HF_TOKEN", "")
base_model = "CompVis/stable-diffusion-v1-4"
lora_model = "rthshr/aarkaa-ai-vision"

print("Loading base model...")
try:
    pipe = StableDiffusionPipeline.from_pretrained(
        base_model,
        torch_dtype=torch.float16,
        use_safetensors=True
    )
    pipe.to("cuda")
    print("Base model loaded successfully.")

    print("Loading LoRA weights...")
    pipe.load_lora_weights(lora_model, token=token)
    print("LoRA weights loaded successfully.")

    print("Generating a test image...")
    prompt = "a futuristic AI vision interface, high tech, digital art"
    # Run with a low step count for quick testing
    image = pipe(prompt, num_inference_steps=10).images[0]
    
    output_path = "test_vision.png"
    image.save(output_path)
    print(f"Test image generated and saved to: {os.path.abspath(output_path)}")
except Exception as e:
    print("Error during test:", e)
