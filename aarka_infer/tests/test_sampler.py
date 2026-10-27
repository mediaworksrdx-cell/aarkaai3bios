"""
Test suite for AARKA Infer Deterministic Sampler.
"""
import pytest
from aarka_infer.runtime.sampler import DeterministicSampler, SamplingParams


def test_deterministic_seed_reproducibility():
    logits = [1.2, 3.4, 0.5, 2.8, 1.1]

    # Two samplers with identical seed MUST sample exact identical sequence
    sampler_a = DeterministicSampler(SamplingParams(temperature=0.8, seed=42))
    sampler_b = DeterministicSampler(SamplingParams(temperature=0.8, seed=42))

    probs_a = sampler_a.filter_logits(logits)
    probs_b = sampler_b.filter_logits(logits)
    assert probs_a == probs_b

    tokens_a = [sampler_a.sample_token(probs_a) for _ in range(10)]
    tokens_b = [sampler_b.sample_token(probs_b) for _ in range(10)]
    assert tokens_a == tokens_b


def test_greedy_sampling_temperature_zero():
    logits = [1.0, 5.0, 2.0]
    sampler = DeterministicSampler(SamplingParams(temperature=0.0))
    probs = sampler.filter_logits(logits)
    assert probs[1] == 1.0
    assert probs[0] < 0.0001
    assert sampler.sample_token(probs) == 1


def test_stop_sequence_detection():
    sampler = DeterministicSampler(SamplingParams(stop=["<|im_end|>", "STOP"]))
    assert sampler.check_stop_condition("Hello world<|im_end|>") == "<|im_end|>"
    assert sampler.check_stop_condition("Carry on") is None
