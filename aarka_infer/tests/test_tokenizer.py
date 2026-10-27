"""
Test suite for AARKA Infer Tokenizer and Chat Template Engine.
"""
import pytest
from aarka_infer.runtime.tokenizer import AarkaTokenizer


def test_tokenizer_encoding_and_decoding():
    tok = AarkaTokenizer()
    text = "Hello, AARKAA-3B!"
    token_ids = tok.encode(text)
    assert isinstance(token_ids, list)
    assert len(token_ids) > 0

    count = tok.count_tokens(text)
    assert count == len(token_ids)


def test_chat_template_rendering():
    tok = AarkaTokenizer()
    messages = [
        {"role": "system", "content": "You are a quantitative finance assistant."},
        {"role": "user", "content": "Calculate the PE ratio for stock X."},
    ]
    rendered = tok.apply_chat_template(messages, add_generation_prompt=True)

    assert "<|im_start|>system" in rendered
    assert "You are a quantitative finance assistant." in rendered
    assert "<|im_start|>user" in rendered
    assert "Calculate the PE ratio for stock X." in rendered
    assert rendered.endswith("<|im_start|>assistant\n")
