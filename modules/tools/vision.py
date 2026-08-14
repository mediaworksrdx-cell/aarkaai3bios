import logging
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from PIL import Image
from modules.tools.base import Tool
from config import SAFE_WORK_DIR
from pathlib import Path

logger = logging.getLogger(__name__)

_vision_model = None
_vision_tokenizer = None

class AarkaVisionAnalyzeTool(Tool):
    name = "AarkaVisionAnalyze"
    description = (
        "Analyze, describe, or answer questions about an uploaded photo/image in the workspace. "
        "Provide the 'image_path' (the filename, e.g., 'receipt.jpg') and a 'question' (e.g. 'What is the total amount?' or 'Describe the scene') in the Action Input."
    )

    def execute(self, params: dict) -> str:
        global _vision_model, _vision_tokenizer
        image_path_param = params.get("image_path")
        question = params.get("question", "Describe this image in detail.")

        if not image_path_param:
            return "Error: 'image_path' parameter is required in Action Input."

        try:
            # Prevent path traversal
            safe_dir = Path(SAFE_WORK_DIR).resolve()
            full_path = (safe_dir / Path(image_path_param).name).resolve()

            if not full_path.is_file():
                return f"Error: Image file '{image_path_param}' not found in workspace."

            # Lazy load the local vision model
            if _vision_model is None:
                logger.info("Loading local Aarka Vision VLM on GPU...")
                model_id = "vikhyat/moondream2"
                
                # Load tokenizer and model in float16
                _vision_tokenizer = AutoTokenizer.from_pretrained(model_id)
                _vision_model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    trust_remote_code=True,
                    torch_dtype=torch.float16
                ).to("cuda")
                logger.info("Aarka Vision VLM loaded successfully on GPU.")

            # Open image
            image = Image.open(full_path).convert("RGB")
            
            # Encode image and get answer
            enc_image = _vision_model.encode_image(image)
            answer = _vision_model.answer_question(enc_image, question, _vision_tokenizer)

            return f"Aarka Vision Analysis of '{image_path_param}':\n\n{answer}"
        except Exception as e:
            return f"Error executing Aarka Vision Analysis: {str(e)}"
