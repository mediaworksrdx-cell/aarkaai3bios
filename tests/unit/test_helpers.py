"""
Unit tests for pipeline helper functions.
All tests operate on pure functions with no I/O or model dependencies.
"""
import pytest


# ─── _sanitize_query ─────────────────────────────────────────────────────────

class TestSanitizeQuery:
    def _fn(self, q):
        from pipeline.helpers import _sanitize_query
        return _sanitize_query(q)

    def test_strips_control_characters(self):
        assert "\x00" not in self._fn("hello\x00world")
        assert "\x1f" not in self._fn("test\x1fstring")

    def test_strips_chatML_tokens(self):
        result = self._fn("<|im_start|>user<|im_end|>")
        assert "<|im_start|>" not in result
        assert "<|im_end|>" not in result

    def test_strips_endoftext_token(self):
        result = self._fn("query<|endoftext|>")
        assert "<|endoftext|>" not in result

    def test_truncates_to_max_length(self):
        from config import MAX_QUERY_LENGTH
        long_q = "a" * (MAX_QUERY_LENGTH + 100)
        result = self._fn(long_q)
        assert len(result) == MAX_QUERY_LENGTH

    def test_strips_whitespace(self):
        assert self._fn("  hello  ") == "hello"

    def test_normal_query_unchanged(self):
        q = "What is the RSI of RELIANCE.NS?"
        assert self._fn(q) == q


# ─── _is_reasoning_query ─────────────────────────────────────────────────────

class TestIsReasoningQuery:
    def _fn(self, q):
        from pipeline.helpers import _is_reasoning_query
        return _is_reasoning_query(q)

    def test_river_crossing_puzzle(self):
        assert self._fn("A farmer wants to cross a river with a fox, a chicken, and a bag of grain")

    def test_light_switch_puzzle(self):
        assert self._fn("Three light switches control three bulbs in another room")

    def test_normal_query_false(self):
        assert not self._fn("What is the stock price of TCS?")

    def test_general_question_false(self):
        assert not self._fn("Explain the concept of RSI in technical analysis")


# ─── _is_pdf_generation_query ────────────────────────────────────────────────

class TestIsPdfQuery:
    def _fn(self, q):
        from pipeline.helpers import _is_pdf_generation_query
        return _is_pdf_generation_query(q)

    def test_generate_pdf(self):
        assert self._fn("generate a PDF report on AI trends")

    def test_create_report(self):
        assert self._fn("create a report on the Indian economy")

    def test_normal_query_false(self):
        assert not self._fn("What is machine learning?")

    def test_download_pdf_false(self):
        # Asking to download is not asking to generate
        assert not self._fn("download the quarterly report PDF")


# ─── _is_image_generation_query ─────────────────────────────────────────────

class TestIsImageQuery:
    def _fn(self, q):
        from pipeline.helpers import _is_image_generation_query
        return _is_image_generation_query(q)

    def test_draw_a(self):
        assert self._fn("draw a sunset over the mountains")

    def test_generate_image(self):
        assert self._fn("generate an image of a cat coding")

    def test_create_picture(self):
        assert self._fn("create a picture of a futuristic city")

    def test_normal_query_false(self):
        assert not self._fn("What is machine learning?")


# ─── _fuse_context_budget ────────────────────────────────────────────────────

class TestFuseContextBudget:
    def _fn(self, parts, budget):
        from pipeline.helpers import _fuse_context_budget
        return _fuse_context_budget(parts, budget)

    def test_empty_parts(self):
        assert self._fn([], 8000) == ""

    def test_within_budget_joins_with_separator(self):
        result = self._fn(["part A", "part B"], 8000)
        assert "part A" in result
        assert "part B" in result
        assert "---" in result

    def test_exceeds_budget_truncates(self):
        parts = ["x" * 5000, "y" * 5000]
        result = self._fn(parts, 8000)
        assert len(result) <= 8000

    def test_first_part_preserved_on_overflow(self):
        parts = ["important" * 500, "overflow" * 1000]
        result = self._fn(parts, 8000)
        assert "important" in result

    def test_single_part_returned_as_is(self):
        assert self._fn(["hello world"], 8000) == "hello world"


# ─── _has_keyword_match ──────────────────────────────────────────────────────

class TestHasKeywordMatch:
    def _fn(self, q, kws):
        from pipeline.helpers import _has_keyword_match
        return _has_keyword_match(q, kws)

    def test_exact_word_match(self):
        assert self._fn("what is the latest news?", ["news"])

    def test_phrase_match(self):
        assert self._fn("tell me about breaking news today", ["breaking news"])

    def test_no_match(self):
        assert not self._fn("what is machine learning?", ["bitcoin", "crypto"])

    def test_case_insensitive(self):
        assert self._fn("Bitcoin price today", ["bitcoin"])

    def test_partial_word_no_match(self):
        # "news" inside "newsfeed" — should not match as exact word boundary
        assert not self._fn("check newsfeed", ["news"])
