"""
AARKA Infer Sampling & Generation Parameter Engine
Enforces deterministic seed control, repetition penalties, temperature, and top_p/top_k.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class SamplingParams:
    """Generation parameters for inference."""
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    repetition_penalty: float = 1.15
    seed: Optional[int] = None
    stop: List[str] = field(default_factory=lambda: ["<|im_end|>", "<|endoftext|>", "\nUser:"])
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    stream: bool = False

    def validate(self) -> None:
        """Sanitizes sampling bounds."""
        self.temperature = max(0.0, min(2.0, self.temperature))
        self.top_p = max(0.01, min(1.0, self.top_p))
        self.top_k = max(-1, self.top_k)
        self.repetition_penalty = max(1.0, min(2.0, self.repetition_penalty))
        self.max_tokens = max(1, min(32768, self.max_tokens))


class DeterministicSampler:
    """Applies reproducible sampling using local PRNG seeded per request."""

    def __init__(self, params: SamplingParams):
        self.params = params
        self.params.validate()
        # Seeded PRNG for deterministic reproducibility
        self.rng = random.Random(self.params.seed) if self.params.seed is not None else random.Random()
        self.generated_tokens: List[int] = []
        self.seen_tokens: Set[int] = set()

    def filter_logits(self, logits: List[float]) -> List[float]:
        """
        Applies temperature, repetition penalty, top_k, and top_p to a logit vector.
        """
        filtered = list(logits)

        # 1. Apply repetition penalty
        if self.params.repetition_penalty > 1.0 and self.seen_tokens:
            for tok_id in self.seen_tokens:
                if 0 <= tok_id < len(filtered):
                    val = filtered[tok_id]
                    filtered[tok_id] = val / self.params.repetition_penalty if val > 0 else val * self.params.repetition_penalty

        # 2. Greedy if temperature == 0
        if self.params.temperature == 0.0:
            max_idx = max(range(len(filtered)), key=lambda i: filtered[i])
            out = [0.0] * len(filtered)
            out[max_idx] = 1.0
            return out

        # 3. Apply temperature scaling
        inv_temp = 1.0 / self.params.temperature
        scaled = [x * inv_temp for x in filtered]

        # 4. Softmax to probabilities
        max_val = max(scaled)
        exp_vals = [math.exp(x - max_val) for x in scaled]
        sum_exp = sum(exp_vals)
        probs = [x / sum_exp for x in exp_vals]

        # 5. Top-K filtering
        if self.params.top_k > 0 and self.params.top_k < len(probs):
            sorted_indices = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)
            cutoff_indices = set(sorted_indices[self.params.top_k:])
            for idx in cutoff_indices:
                probs[idx] = 0.0
            s = sum(probs)
            if s > 0:
                probs = [p / s for p in probs]

        # 6. Top-P (Nucleus) filtering
        if self.params.top_p < 1.0:
            indexed_probs = sorted(enumerate(probs), key=lambda x: x[1], reverse=True)
            cumulative = 0.0
            keep_indices = set()
            for idx, p in indexed_probs:
                keep_indices.add(idx)
                cumulative += p
                if cumulative >= self.params.top_p:
                    break
            for idx in range(len(probs)):
                if idx not in keep_indices:
                    probs[idx] = 0.0
            s = sum(probs)
            if s > 0:
                probs = [p / s for p in probs]

        return probs

    def sample_token(self, probs: List[float]) -> int:
        """Samples the next token ID using the seeded PRNG."""
        r = self.rng.random()
        cumulative = 0.0
        for i, p in enumerate(probs):
            cumulative += p
            if r <= cumulative:
                self.record_token(i)
                return i
        chosen = len(probs) - 1
        self.record_token(chosen)
        return chosen

    def record_token(self, token_id: int) -> None:
        """Tracks generated tokens for repetition penalty and stops."""
        self.generated_tokens.append(token_id)
        self.seen_tokens.add(token_id)

    def check_stop_condition(self, generated_text: str) -> Optional[str]:
        """Checks if generated text has reached any designated stop sequence."""
        for stop_seq in self.params.stop:
            if stop_seq and stop_seq in generated_text:
                return stop_seq
        return None
