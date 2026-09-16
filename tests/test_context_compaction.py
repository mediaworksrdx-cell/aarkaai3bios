"""
Tests for the enhanced context compaction module (Phase 1).
Validates token-budget awareness, structured checkpoints, rollback behavior,
and the compact_history function.
"""
import pytest
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# Mock model instance for tokenization
# ---------------------------------------------------------------------------

class MockModel:
    """Simulates llama-cpp model tokenizer behavior."""

    def tokenize(self, data: bytes, special: bool = True) -> list[int]:
        # Approximate: 1 token per 4 bytes (rough English average)
        text = data.decode("utf-8", errors="replace")
        return list(range(len(text) // 4))

    def detokenize(self, tokens: list[int]) -> bytes:
        # Each token ~4 chars
        return ("x" * (len(tokens) * 4)).encode("utf-8")

    def n_ctx(self) -> int:
        return 16384


# ---------------------------------------------------------------------------
# Layer unit tests
# ---------------------------------------------------------------------------

class TestLayer1AnsiCleanup:
    def test_strips_ansi_escapes(self):
        from modules.context_compaction import clean_ansi_escapes
        text = "\x1b[31mERROR\x1b[0m: something failed"
        result = clean_ansi_escapes(text)
        assert "\x1b" not in result
        assert "ERROR" in result

    def test_strips_progress_bars(self):
        from modules.context_compaction import clean_ansi_escapes
        text = "Installing... [========>] 75% done"
        result = clean_ansi_escapes(text)
        assert "75%" not in result


class TestLayer2Truncation:
    def test_no_truncation_under_limit(self):
        from modules.context_compaction import truncate_source_code_buffers
        text = "\n".join([f"line {i}" for i in range(50)])
        result = truncate_source_code_buffers(text, max_lines=100)
        assert result == text

    def test_truncation_over_limit(self):
        from modules.context_compaction import truncate_source_code_buffers
        text = "\n".join([f"line {i}" for i in range(200)])
        result = truncate_source_code_buffers(text, max_lines=100)
        assert "Truncated" in result
        assert "line 0" in result
        assert "line 199" in result


class TestLayer3Deduplication:
    def test_removes_consecutive_duplicates(self):
        from modules.context_compaction import semantic_deduplicate
        text = "line1\nline2\nline2\nline2\nline3"
        result = semantic_deduplicate(text)
        assert result.count("line2") == 1

    def test_preserves_non_consecutive_duplicates(self):
        from modules.context_compaction import semantic_deduplicate
        text = "line1\nline2\nline1"
        result = semantic_deduplicate(text)
        assert result.count("line1") == 2

    def test_preserves_blank_lines(self):
        from modules.context_compaction import semantic_deduplicate
        text = "line1\n\nline2\n\nline3"
        result = semantic_deduplicate(text)
        assert result == text


# ---------------------------------------------------------------------------
# Token budget tests
# ---------------------------------------------------------------------------

class TestTokenBudget:
    def test_usable_budget_with_default_reserve(self):
        from modules.context_compaction import _compute_usable_budget
        budget = _compute_usable_budget(context_window=16384, reserved_output=2048)
        assert budget == 14336

    def test_usable_budget_minimum_floor(self):
        from modules.context_compaction import _compute_usable_budget
        budget = _compute_usable_budget(context_window=1024, reserved_output=2048)
        assert budget == 1024  # floor of 1024

    def test_trigger_threshold(self):
        from modules.context_compaction import _compute_trigger_threshold
        threshold = _compute_trigger_threshold(usable_budget=14336, ratio=0.80)
        assert threshold == 11468

    def test_tokenize_len_with_model(self):
        from modules.context_compaction import _tokenize_len
        model = MockModel()
        length = _tokenize_len("Hello world test text", model)
        assert length == 5  # 20 chars / 4

    def test_tokenize_len_without_model(self):
        from modules.context_compaction import _tokenize_len
        # 21 chars / 3.5 = 6.0 -> int(6.0) = 6
        length = _tokenize_len("Hello world test text!", None)
        assert length == 6


# ---------------------------------------------------------------------------
# Compact history tests
# ---------------------------------------------------------------------------

class TestCompactHistory:
    def test_empty_history(self):
        from modules.context_compaction import compact_history
        result = compact_history([], token_budget=1000, model_instance=None)
        assert result == []

    def test_within_budget(self):
        from modules.context_compaction import compact_history
        history = [
            {"role": "user", "message": "Hi"},
            {"role": "assistant", "message": "Hello"},
        ]
        result = compact_history(history, token_budget=5000, model_instance=None)
        assert len(result) == 2

    def test_drops_oldest_first(self):
        from modules.context_compaction import compact_history
        history = [
            {"role": "user", "message": "a" * 1000},
            {"role": "user", "message": "b" * 1000},
            {"role": "user", "message": "c" * 100},
        ]
        # Budget fits only ~2 messages
        result = compact_history(history, token_budget=400, model_instance=None,
                                 preserve_turns=1)
        # Must preserve the last turn (c*100) always
        assert any("c" in (m.get("message", "") or m.get("content", "")) for m in result)

    def test_preserves_minimum_turns(self):
        from modules.context_compaction import compact_history
        history = [
            {"role": "user", "message": f"msg{i}"} for i in range(10)
        ]
        result = compact_history(history, token_budget=500, model_instance=None,
                                 preserve_turns=3)
        # At minimum, last 3 turns preserved
        assert len(result) >= 3


# ---------------------------------------------------------------------------
# Layer 5: Turn-aware truncation
# ---------------------------------------------------------------------------

class TestLayer5Truncation:
    def test_react_format_detection(self):
        from modules.context_compaction import _detect_turn_format
        text = "System\nThought: first\nAction: Tool\nThought: second"
        assert _detect_turn_format(text) == "react"

    def test_chatml_format_detection(self):
        from modules.context_compaction import _detect_turn_format
        text = "<|im_start|>user\nHi<|im_end|>\n<|im_start|>assistant\nHello"
        assert _detect_turn_format(text) == "chatml"

    def test_sliding_window_preserves_recent(self):
        from modules.context_compaction import _sliding_window_truncate
        text = "System prompt\nThought: old1\nThought: old2\nThought: recent1\nThought: recent2"
        result = _sliding_window_truncate(text, preserve_turns=2)
        assert "recent1" in result
        assert "recent2" in result
        assert "truncated" in result


# ---------------------------------------------------------------------------
# Full pipeline tests
# ---------------------------------------------------------------------------

class TestCompactPrompt:
    @patch("modules.context_compaction.COMPACTION_ENABLED", True)
    def test_short_prompt_unchanged(self):
        from modules.context_compaction import compact_prompt
        short = "System: Hello\nUser: Hi"
        result = compact_prompt(short, None, prompt_token_budget=14336)
        # Short prompt should pass through layers 1-3 unchanged
        assert "Hello" in result

    @patch("modules.context_compaction.COMPACTION_ENABLED", False)
    def test_rollback_uses_safe_fallback(self):
        from modules.context_compaction import compact_prompt
        # Even when disabled, layers 1-3 still run
        text = "\x1b[31mERROR\x1b[0m line\n" * 50
        result = compact_prompt(text, None, prompt_token_budget=14336)
        assert "\x1b" not in result  # ANSI still cleaned


# ---------------------------------------------------------------------------
# Checkpoint extraction tests
# ---------------------------------------------------------------------------

class TestCheckpointFields:
    def test_extracts_file_paths(self):
        from modules.context_compaction import _extract_checkpoint_fields
        text = 'Modified "src/config.py" and updated tests/test_main.py'
        fields = _extract_checkpoint_fields(text)
        assert "Modified Files" in fields
        assert "config.py" in fields["Modified Files"]

    def test_extracts_errors(self):
        from modules.context_compaction import _extract_checkpoint_fields
        text = "Error: ModuleNotFoundError\nTraceback (most recent call last)"
        fields = _extract_checkpoint_fields(text)
        assert "Errors Encountered" in fields

    def test_no_fabrication_on_empty(self):
        from modules.context_compaction import _extract_checkpoint_fields
        text = "Everything is working fine."
        fields = _extract_checkpoint_fields(text)
        assert "Modified Files" not in fields
        assert "Errors Encountered" not in fields
