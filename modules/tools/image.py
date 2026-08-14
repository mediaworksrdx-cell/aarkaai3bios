import torch
import uuid
import os
import logging
from pathlib import Path
from modules.tools.base import Tool
from config import SAFE_WORK_DIR

logger = logging.getLogger(__name__)

_sd_pipeline = None

class ImageGenTool(Tool):
    name = "ImageGen"
    description = (
        "Generate a high-quality image from a text prompt using the standalone AARKAA-VISION model. "
        "Provide a descriptive 'prompt' in the Action Input JSON. "
        "The tool will automatically save the image and return a markdown image link to display it."
    )
    risk_level = "LOW"
    latency_weight = 4.0
    cost_weight = 2.0
    base_confidence = 0.95

    def execute(self, params: dict) -> str:
        global _sd_pipeline
        prompt = params.get("prompt")
        if not prompt:
            return "Error: 'prompt' parameter is required in Action Input."
        
        try:
            # Lazy load our custom standalone AARKAA-VISION model
            if _sd_pipeline is None:
                from diffusers import StableDiffusionPipeline
                # The standalone fused model directory on the server
                standalone_model_path = "/workspace/aarkaai3b/aarkaa-vision-standalone"
                
                # Fallback to online loading if the standalone model is not yet merged/present on the server
                if os.path.exists(standalone_model_path):
                    logger.info("Loading standalone AARKAA-VISION model from %s...", standalone_model_path)
                    pipe = StableDiffusionPipeline.from_pretrained(
                        standalone_model_path,
                        torch_dtype=torch.float16,
                        use_safetensors=True
                    )
                else:
                    logger.info("Standalone model not found. Falling back to dynamic base + LoRA loading...")
                    token = os.getenv("HF_TOKEN", "")
                    base_model = "CompVis/stable-diffusion-v1-4"
                    lora_model = "rthshr/aarkaa-ai-vision"
                    
                    pipe = StableDiffusionPipeline.from_pretrained(
                        base_model,
                        torch_dtype=torch.float16,
                        use_safetensors=True
                    )
                    if token:
                        pipe.load_lora_weights(lora_model, token=token)
                    else:
                        pipe.load_lora_weights(lora_model)

                pipe.to("cuda")
                _sd_pipeline = pipe
                logger.info("AARKAA-VISION standalone pipeline initialized successfully on GPU.")

            # Generate the image
            image = _sd_pipeline(prompt, num_inference_steps=30).images[0]
            
            # Save inside SAFE_WORK_DIR so the Nginx /download route can serve it
            filename = f"image_{uuid.uuid4().hex[:8]}.png"
            output_dir = Path(SAFE_WORK_DIR)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / filename
            
            image.save(output_path)
            
            # Return markdown link to render the image in the chat interface
            return (
                f"Image generated successfully.\n\n"
                f"![Generated Image](/download/{filename})"
            )
        except Exception as e:
            return f"Error executing ImageGen: {e}"
