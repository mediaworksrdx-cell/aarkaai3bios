"""
AARKA Infer Tokenizer & Chat Template Engine
Supports tokenization, detokenization, and Jinja2 chat template rendering.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jinja2

from aarka_infer.config import settings

logger = logging.getLogger("aarka_infer.tokenizer")


class AarkaTokenizer:
    """Manages token encoding, decoding, and Jinja2 chat template rendering for AARKAA-3B."""

    def __init__(
        self,
        tokenizer_json_path: Optional[Path] = None,
        chat_template_path: Optional[Path] = None,
    ):
        self.tokenizer_path = tokenizer_json_path or settings.tokenizer_json_path
        self.template_path = chat_template_path or settings.chat_template_path
        self._hf_tokenizer = None
        self._jinja_env = None
        self._compiled_template = None
        self._init_tokenizer()
        self._init_chat_template()

    def _init_tokenizer(self) -> None:
        """Loads HuggingFace tokenizers from tokenizer.json if available."""
        if self.tokenizer_path.exists():
            try:
                from tokenizers import Tokenizer
                self._hf_tokenizer = Tokenizer.from_file(str(self.tokenizer_path))
                logger.info("Loaded fast tokenizer from %s", self.tokenizer_path)
            except Exception as e:
                logger.warning("Failed to load tokenizers library (%s); using fallback tokenizer", e)
        else:
            logger.warning("tokenizer.json not found at %s", self.tokenizer_path)

    def _init_chat_template(self) -> None:
        """Compiles chat_template.jinja using Jinja2."""
        template_str = ""
        if self.template_path.exists():
            try:
                template_str = self.template_path.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning("Failed to read chat_template.jinja: %s", e)

        if not template_str:
            # Canonical fallback template matching Qwen2 / ChatML convention
            template_str = (
                "{%- for message in messages %}"
                "{{- '<|im_start|>' + message.role + '\\n' + message.content + '<|im_end|>\\n' }}"
                "{%- endfor %}"
                "{%- if add_generation_prompt %}"
                "{{- '<|im_start|>assistant\\n' }}"
                "{%- endif %}"
            )

        try:
            self._jinja_env = jinja2.Environment(
                loader=jinja2.BaseLoader(),
                trim_blocks=True,
                lstrip_blocks=True,
            )
            # Add json filter for tools rendering
            self._jinja_env.filters["tojson"] = json.dumps
            self._compiled_template = self._jinja_env.from_string(template_str)
            logger.info("Compiled chat template successfully")
        except Exception as e:
            logger.error("Failed to compile Jinja2 chat template: %s", e)

    def apply_chat_template(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        add_generation_prompt: bool = True,
    ) -> str:
        """Renders conversational messages into model prompt format."""
        if self._compiled_template is not None:
            try:
                rendered = self._compiled_template.render(
                    messages=messages,
                    tools=tools or [],
                    add_generation_prompt=add_generation_prompt,
                )
                if add_generation_prompt and not rendered.endswith("<|im_start|>assistant\n"):
                    rendered += "<|im_start|>assistant\n"
                return rendered
            except Exception as e:
                logger.warning("Error rendering chat template: %s. Using basic ChatML fallback.", e)

        # Fallback basic ChatML serialization
        res = []
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            res.append(f"<|im_start|>{role}\n{content}<|im_end|>\n")
        if add_generation_prompt:
            res.append("<|im_start|>assistant\n")
        return "".join(res)

    def encode(self, text: str) -> List[int]:
        """Encodes text to a list of token IDs."""
        if self._hf_tokenizer is not None:
            try:
                encoded = self._hf_tokenizer.encode(text)
                return encoded.ids
            except Exception:
                pass
        # Fallback estimation: ~4 chars per token for Latin, ~1-2 for non-Latin
        return [hash(w) % 151936 for w in text.split()]

    def decode(self, token_ids: List[int]) -> str:
        """Decodes token IDs back to a string."""
        if self._hf_tokenizer is not None:
            try:
                return self._hf_tokenizer.decode(token_ids, skip_special_tokens=True)
            except Exception:
                pass
        return " ".join(str(tid) for tid in token_ids)

    def count_tokens(self, text_or_messages: Union[str, List[Dict[str, Any]]]) -> int:
        """Counts total tokens for a string or list of messages."""
        if isinstance(text_or_messages, list):
            text = self.apply_chat_template(text_or_messages, add_generation_prompt=True)
        else:
            text = text_or_messages
        return len(self.encode(text))
