"""
Test suite for AARKA Infer Model Loader and Architectural Verifier.
"""
import pytest
from pathlib import Path
from aarka_infer.config import settings
from aarka_infer.runtime.model_loader import AarkaModelLoader, ArchitectureSpecs, ModelVerifier


def test_architecture_specs_defaults():
    specs = ArchitectureSpecs()
    assert specs.architecture == "Qwen2ForCausalLM"
    assert specs.num_hidden_layers == 36
    assert specs.num_attention_heads == 16
    assert specs.num_key_value_heads == 2
    assert specs.hidden_size == 2048
    assert specs.vocab_size == 151936


def test_verify_real_config_json():
    verifier = ModelVerifier()
    is_valid, warnings, errors = verifier.verify_config_json(settings.config_json_path)

    # config.json in "aarkaai 3b/config.json" must match authoritative Qwen2 3B specs
    assert is_valid is True, f"Validation errors: {errors}"
    assert len(errors) == 0


def test_model_loader_resolution():
    loader = AarkaModelLoader()
    report = loader.resolve_model(force_backend="mock")

    assert report.is_valid is True
    assert report.architecture_matched is True
    assert report.backend_type == "mock"
    assert report.details["model_id"] == settings.model_id
