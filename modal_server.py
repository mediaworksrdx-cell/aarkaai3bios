"""
AARKAAI – Modal Serverless GPU Inference Engine
Hosts Aarkaa 7B, 3B, and Coder 3B GGUF models on dedicated NVIDIA GPUs.
Mounts modal.Volume("aarkaa-models") and exposes ultra-fast streaming HTTP endpoints.
"""
from __future__ import annotations

import json
import logging
from typing import Optional

import modal
from pydantic import BaseModel

# ─── Modal App Definition ───────────────────────────────────────────────────
app = modal.App("aarkaa-inference")

# Official NVIDIA CUDA 12.4 runtime image with Python 3.11 & prebuilt llama-cpp-python CUDA wheel
image = (
    modal.Image.from_registry("nvidia/cuda:12.4.1-runtime-ubuntu22.04", add_python="3.11")
    .pip_install(
        "llama-cpp-python",
        extra_index_url="https://abetlen.github.io/llama-cpp-python/whl/cu124"
    )
    .pip_install("fastapi", "uvicorn", "pydantic")
)

models_volume = modal.Volume.from_name("aarkaa-models")

# ─── Request Schemas ────────────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    prompt: str
    max_tokens: int = 3800
    temperature: float = 0.7
    top_p: float = 0.9
    repeat_penalty: float = 1.15
    stop: Optional[list[str]] = None
    model: str = "7b"  # "7b" | "3b" | "coder"
    stream: bool = False

# ─── Inference Class ────────────────────────────────────────────────────────
@app.cls(
    image=image,
    gpu="A10G",
    volumes={"/models": models_volume},
    timeout=600,
    scaledown_window=30,  # Scale down after 30 seconds of inactivity to minimize idle GPU credit usage
)
class AarkaaGPU:
    @modal.enter()
    def load_models(self):
        import os
        from llama_cpp import Llama
        
        self.models = {}
        print("Initializing Aarkaa GPU container with CUDA 12.4 on NVIDIA A10G (24GB VRAM)...")
        print("Mounted volume contents:", os.listdir("/models"))
        
        # Pre-load 7B model directly into VRAM (priority 1)
        candidates_7b = [
            "/models/aarkaa-7b-f16.gguf",
            "/models/aarkaa-7b-q16.gguf",
            "/models/aarkaa-7b-q8.gguf",
        ]
        path_7b = None
        for cand in candidates_7b:
            if os.path.exists(cand):
                path_7b = cand
                break

        if path_7b:
            print(f"Loading primary 7B model {path_7b} with n_gpu_layers=99, n_ctx=8192...")
            self.models["7b"] = Llama(
                model_path=path_7b,
                n_gpu_layers=99,
                n_ctx=8192,
                verbose=False
            )
            print(f"Aarkaa 7B ({os.path.basename(path_7b)}) successfully loaded to GPU VRAM.")

    def _get_model(self, model_name: str):
        import os
        import gc
        from llama_cpp import Llama
        
        m_lower = (model_name or "7b").lower()
        if "code" in m_lower:
            model_key = "coder"
        elif "3" in m_lower:
            model_key = "3b"
        elif "7" in m_lower:
            model_key = "7b"
        else:
            model_key = "7b"

        if model_key in self.models and self.models[model_key] is not None:
            return self.models[model_key]

        # If switching between secondary models (coder vs 3b), release the other to guarantee VRAM headroom
        other_key = "3b" if model_key == "coder" else ("coder" if model_key == "3b" else None)
        if other_key and other_key in self.models:
            print(f"Releasing {other_key} from VRAM to make room for {model_key}...")
            del self.models[other_key]
            gc.collect()

        path_candidates_map = {
            "3b": ["/models/aarkaa-3b-f16.gguf", "/models/aarkaa-3b-q16.gguf", "/models/aarkaa-3b-q8.gguf"],
            "coder": ["/models/aarkaa-coder-3b-f16.gguf", "/models/aarkaa-coder-3b-q16.gguf", "/models/aarkaa-coder-3b-q8.gguf"],
            "7b": ["/models/aarkaa-7b-f16.gguf", "/models/aarkaa-7b-q16.gguf", "/models/aarkaa-7b-q8.gguf"]
        }
        candidates = path_candidates_map.get(model_key, [])
        for target_path in candidates:
            if os.path.exists(target_path):
                print(f"Dynamically loading {target_path} into GPU VRAM...")
                try:
                    self.models[model_key] = Llama(
                        model_path=target_path,
                        n_gpu_layers=99,
                        n_ctx=8192,
                        verbose=False
                    )
                    return self.models[model_key]
                except Exception as load_err:
                    print(f"Notice: load with n_ctx=8192 returned {load_err}, retrying with n_ctx=4096...")
                    self.models[model_key] = Llama(
                        model_path=target_path,
                        n_gpu_layers=99,
                        n_ctx=4096,
                        verbose=False
                    )
                    return self.models[model_key]

        # Fallback to 7B if available
        return self.models.get("7b")

    @modal.method()
    def generate(self, prompt: str, max_tokens: int = 3800, temperature: float = 0.7,
                 top_p: float = 0.9, repeat_penalty: float = 1.15, stop: list = None,
                 model: str = "7b") -> str:
        llm = self._get_model(model)
        if llm is None:
            return "Aarkaa GPU engine unavailable."
        
        stop_tokens = [
            "<|im_end|>", "<|im_start|>", "<|endoftext|>",
            "\nBest regards", "\nBest Regards", "\nSincerely", "\n#Aarkaa",
            "Thank you for your question",
            "Please let me know if there is anything else",
            "Please let me know if you need",
            "Please let me know if you have",
            "Please let me know",
            "Let me know if you",
            "Feel free to ask",
            "Hope this helps",
            "**End of answer**", "**End of response**", "**End of Answer**", "**End of Response**",
            "**End of answer", "**End of response", "**End of Answer", "**End of Response",
            "End of answer.", "End of response.", "End of answer", "End of response",
            "(End of answer)", "(End of response)", "[End of answer]", "[End of response]",
            "--- END", "(End of text)", "### End of Answer", "### End of Response"
        ]
        if stop:
            stop_tokens.extend(stop)
            
        output = llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            repeat_penalty=repeat_penalty,
            stop=stop_tokens
        )
        return output["choices"][0]["text"].strip()

    @modal.method()
    def stream_generate(self, prompt: str, max_tokens: int = 3800, temperature: float = 0.7,
                        top_p: float = 0.9, repeat_penalty: float = 1.15, stop: list = None,
                        model: str = "7b"):
        llm = self._get_model(model)
        if llm is None:
            yield "Aarkaa GPU engine unavailable."
            return

        stop_tokens = [
            "<|im_end|>", "<|im_start|>", "<|endoftext|>",
            "\nBest regards", "\nBest Regards", "\nSincerely", "\n#Aarkaa",
            "Thank you for your question",
            "Please let me know if there is anything else",
            "Please let me know if you need",
            "Please let me know if you have",
            "Please let me know",
            "Let me know if you",
            "Feel free to ask",
            "Hope this helps",
            "**End of answer**", "**End of response**", "**End of Answer**", "**End of Response**",
            "**End of answer", "**End of response", "**End of Answer", "**End of Response",
            "End of answer.", "End of response.", "End of answer", "End of response",
            "(End of answer)", "(End of response)", "[End of answer]", "[End of response]",
            "--- END", "(End of text)", "### End of Answer", "### End of Response"
        ]
        if stop:
            stop_tokens.extend(stop)

        stream = llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            repeat_penalty=repeat_penalty,
            stop=stop_tokens,
            stream=True
        )
        for chunk in stream:
            token = chunk["choices"][0]["text"]
            if token:
                yield token

    @modal.fastapi_endpoint(method="POST")
    def endpoint(self, req: GenerateRequest):
        from fastapi.responses import StreamingResponse, JSONResponse
        
        if req.stream:
            def event_stream():
                for token in self.stream_generate.local(
                    req.prompt, req.max_tokens, req.temperature,
                    req.top_p, req.repeat_penalty, req.stop, req.model
                ):
                    data = json.dumps({"token": token})
                    yield f"data: {data}\n\n"
                yield "data: [DONE]\n\n"
            return StreamingResponse(event_stream(), media_type="text/event-stream")

        text = self.generate.local(
            req.prompt, req.max_tokens, req.temperature,
            req.top_p, req.repeat_penalty, req.stop, req.model
        )
        return JSONResponse({"text": text, "model": req.model})
