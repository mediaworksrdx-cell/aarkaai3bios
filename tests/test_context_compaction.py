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


# ---------------------------------------------------------------------------
# Long Multi-Turn & Multi-Step ReAct Integration Tests
# ---------------------------------------------------------------------------

class TestLongMultiTurnCompaction:
    def test_massive_history_constrained_to_budget(self):
        """A 40-turn conversation exceeding budget is pruned chronologically, keeping recent turns."""
        from modules.context_compaction import compact_history, _tokenize_len
        model = MockModel()
        # 40 turns, each turn ~200 characters = ~50 tokens
        history = [
            {"role": "user" if i % 2 == 0 else "assistant",
             "message": f"Turn {i}: " + ("detailed discussion point " * 8)}
            for i in range(40)
        ]
        # Target budget: 400 tokens (~8 turns)
        compacted = compact_history(history, token_budget=400, model_instance=model, preserve_turns=3)
        total_tokens = sum(_tokenize_len(m["message"], model) for m in compacted)
        assert total_tokens <= 400
        # The latest turns must be present
        assert "Turn 39" in compacted[-1]["message"]
        assert "Turn 38" in compacted[-2]["message"]
        assert "Turn 37" in compacted[-3]["message"]

    def test_chatml_multi_integration_within_budget(self):
        """_build_chatml_multi applies compact_history and stays bounded within token budget."""
        from modules.aarkaa_engine import _build_chatml_multi
        from modules.context_compaction import _tokenize_len
        history = [
            {"role": "user" if i % 2 == 0 else "assistant",
             "message": f"Historical message {i} with content " + ("X" * 150)}
            for i in range(30)
        ]
        result = _build_chatml_multi("You are AARKAA.", history, "What is the status?")
        assert "<|im_start|>system" in result
        assert "<|im_start|>user\nWhat is the status?" in result
        # Must retain recent history
        assert "Historical message 29" in result


class TestMultiStepReActCompaction:
    def test_long_react_trace_compacted_under_budget(self):
        """A 15-step ReAct agent execution trace exceeding 12,000 tokens is compacted cleanly."""
        from modules.context_compaction import compact_prompt, _compute_usable_budget, _tokenize_len
        model = MockModel()
        usable_budget = _compute_usable_budget(16384, 2048)  # 14336
        assert usable_budget == 14336

        # Build a 15-step ReAct prompt
        system_preamble = "You are AARKAA Agent Coordinator.\nAvailable tools: BashTool, FileReadTool\n"
        steps = []
        for step in range(1, 16):
            steps.append(
                f"Thought: Analyzing step {step}.\n"
                f"Action: FileReadTool\n"
                f"Action Input: {{\"path\": \"src/module_{step}.py\"}}\n"
                f"Observation: Source content for module_{step} with lots of lines.\n"
                + ("line code content for testing buffer truncation\n" * 40)
            )
        full_react_prompt = system_preamble + "\n".join(steps)

        compacted = compact_prompt(full_react_prompt, model, prompt_token_budget=usable_budget)
        token_count = _tokenize_len(compacted, model)
        assert token_count <= usable_budget
        assert "You are AARKAA Agent Coordinator." in compacted
        # Most recent steps must be preserved
        assert "step 15" in compacted or "module_15.py" in compacted


class TestCompactionRollbackFlag:
    def test_env_var_rollback_flag_takes_effect(self, monkeypatch):
        """Setting AARKAAI_COMPACTION_ENABLED=false switches to token-aware fallback immediately."""
        import os
        from modules.context_compaction import is_compaction_enabled, compact_prompt

        monkeypatch.setenv("AARKAAI_COMPACTION_ENABLED", "false")
        assert is_compaction_enabled() is False

        # Run prompt compaction under rollback
        prompt = "System preamble\n" + ("Thought: step\nAction: Tool\nObservation: " + ("Z" * 200) + "\n") * 30
        result = compact_prompt(prompt, None, prompt_token_budget=1000)
        assert is_compaction_enabled() is False
        # Token-aware sliding window still applies, keeping preamble and recent content
        assert "System preamble" in result

        monkeypatch.setenv("AARKAAI_COMPACTION_ENABLED", "true")
        assert is_compaction_enabled() is True

