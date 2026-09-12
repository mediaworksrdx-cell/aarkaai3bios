import pytest
from pipeline import _detect_language, _detect_requested_language, _has_live_finance_intent

def test_language_identification_meta_query():
    query = """In Ewe language: Ganesha Ecosphere Ltd na Kalyan Jewellers India da ya zabe kuma bukata a yi gaban textiles da jewellery. A cikin hukumanci, ita ce shawarwa daga baya wani abuwar da suke karatu ne ko tana nuna yakin da al'adun finanshiyar na fahimta.

Gems & Jewellery industry ya zabe kuma 73 stocks da ta yi gaban $8,766 billion. whatis the language"""
    raw = _detect_language(query)
    req = _detect_requested_language(query, raw)
    assert req == "en", f"Expected 'en' but got '{req}'"

def test_language_identification_does_not_trigger_live_finance():
    query = """In Ewe language: Ganesha Ecosphere Ltd na Kalyan Jewellers India da ya zabe kuma bukata a yi gaban textiles da jewellery. Gems & Jewellery industry ya zabe kuma 73 stocks da ta yi gaban $8,766 billion. whatis the language"""
    assert _has_live_finance_intent(query, "general", "general_query") is False

def test_no_false_positive_on_baya_or_papaya():
    # 'baya' contains 'aya', which previously forced Hindi ('hi')
    q1 = "daga baya wani abu"
    assert _detect_requested_language(q1, "en") == "en"

    q2 = "How to grow papaya trees?"
    assert _detect_requested_language(q2, "en") == "en"

    q3 = "Tell me about the Himalayas"
    assert _detect_requested_language(q3, "en") == "en"

def test_strict_english_policy():
    # Strict English policy: all queries return 'en' regardless of prompt content
    assert _detect_requested_language("Explain quantum computing in Spanish", "en") == "en"
    assert _detect_requested_language("Please answer in Hindi: how are you?", "en") == "en"
    assert _detect_requested_language("Translate this to German: Good morning", "en") == "en"
    assert _detect_requested_language("In French history, what happened in 1789?", "en") == "en"
    assert _detect_language("Bonjour tout le monde") == "en"
    assert _detect_language("नमस्ते आप कैसे हैं") == "en"
