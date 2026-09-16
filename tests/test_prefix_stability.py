"""
Tests for KV-Cache Prefix Stabilization (Phase 2).
Validates that compile_prompt_layered produces identical static prefixes
across requests with different dynamic contexts.
"""
import pytest
from unittest.mock import patch, MagicMock


class MockToolRegistry:
    """Minimal mock tool registry for testing."""

    def __init__(self):
        self._tools = {
            "BashTool": MagicMock(name="BashTool", description="Execute shell commands"),
            "FileReadTool": MagicMock(name="FileReadTool", description="Read file contents"),
            "FileEditTool": MagicMock(name="FileEditTool", description="Edit file contents"),
        }

    def get_tool(self, name):
        return self._tools.get(name)


@pytest.fixture
def mock_registry():
    reg = MockToolRegistry()
    with patch("modules.tools.registry", reg):
        yield reg


@pytest.fixture
def agent():
    from modules.agents.base import BaseAgent
    return BaseAgent(
        name="TestCoding",
        description="Test coding agent",
        persona="You are a senior software engineer.",
        rules=["Write clean code", "Follow best practices", "Test thoroughly"],
        default_temp=0.2,
        allowed_tools=["BashTool", "FileReadTool", "FileEditTool"],
        use_rag=False,
    )


class TestPrefixStability:
    """Verify that the static prefix is identical across requests
    with different sessions, timestamps, and queries."""

    @patch("modules.agents.base.memory")
    def test_static_prefix_identical_across_requests(self, mock_memory, agent, mock_registry):
        """Two requests with different sessions should produce identical static prefixes."""
        mock_memory.get_user_facts_prompt.return_value = ""
        mock_memory.get_user_profile.return_value = {"interests": [], "expertise_areas": [], "interaction_count": 5}
        mock_memory.get_user_memories.return_value = []

        with patch("config.KV_PREFIX_CACHE_ENABLED", True):
            static1, dynamic1 = agent.compile_prompt_layered(
                user_id="user1", session_id="session-aaa", device="iOS", query="fix my bug"
            )
            static2, dynamic2 = agent.compile_prompt_layered(
                user_id="user1", session_id="session-bbb", device="Android", query="write a test"
            )

        # Static prefixes MUST be byte-identical
        assert static1 == static2, (
            f"Static prefixes differ!\n--- prefix1 ---\n{static1[:200]}\n--- prefix2 ---\n{static2[:200]}"
        )
        # Dynamic suffixes SHOULD differ (different session IDs, devices)
        assert dynamic1 != dynamic2

    @patch("modules.agents.base.memory")
    def test_static_prefix_contains_persona(self, mock_memory, agent, mock_registry):
        mock_memory.get_user_facts_prompt.return_value = ""
        mock_memory.get_user_profile.return_value = {"interests": [], "expertise_areas": [], "interaction_count": 0}
        mock_memory.get_user_memories.return_value = []

        with patch("config.KV_PREFIX_CACHE_ENABLED", True):
            static, _ = agent.compile_prompt_layered(
                user_id="u1", session_id="s1", device="Web", query="test"
            )

        assert "senior software engineer" in static

    @patch("modules.agents.base.memory")
    def test_static_prefix_contains_rules(self, mock_memory, agent, mock_registry):
        mock_memory.get_user_facts_prompt.return_value = ""
        mock_memory.get_user_profile.return_value = {"interests": [], "expertise_areas": [], "interaction_count": 0}
        mock_memory.get_user_memories.return_value = []

        with patch("config.KV_PREFIX_CACHE_ENABLED", True):
            static, _ = agent.compile_prompt_layered(
                user_id="u1", session_id="s1", device="Web", query="test"
            )

        assert "Write clean code" in static
        assert "Follow best practices" in static

    @patch("modules.agents.base.memory")
    def test_static_prefix_contains_sorted_tools(self, mock_memory, agent, mock_registry):
        mock_memory.get_user_facts_prompt.return_value = ""
        mock_memory.get_user_profile.return_value = {"interests": [], "expertise_areas": [], "interaction_count": 0}
        mock_memory.get_user_memories.return_value = []

        with patch("config.KV_PREFIX_CACHE_ENABLED", True):
            static, _ = agent.compile_prompt_layered(
                user_id="u1", session_id="s1", device="Web", query="test"
            )

        # Tools must be sorted alphabetically
        bash_pos = static.index("BashTool")
        edit_pos = static.index("FileEditTool")
        read_pos = static.index("FileReadTool")
        assert bash_pos < edit_pos < read_pos

    @patch("modules.agents.base.memory")
    def test_dynamic_suffix_contains_session_context(self, mock_memory, agent, mock_registry):
        mock_memory.get_user_facts_prompt.return_value = ""
        mock_memory.get_user_profile.return_value = {"interests": [], "expertise_areas": [], "interaction_count": 0}
        mock_memory.get_user_memories.return_value = []

        with patch("config.KV_PREFIX_CACHE_ENABLED", True):
            _, dynamic = agent.compile_prompt_layered(
                user_id="u1", session_id="sess-xyz", device="Web/Browser", query="test"
            )

        assert "sess-xyz" in dynamic
        assert "Web/Browser" in dynamic


class TestCompilePromptFlagBehavior:
    """Verify feature flag controls prompt assembly strategy."""

    @patch("modules.agents.base.memory")
    def test_layered_when_enabled(self, mock_memory, agent, mock_registry):
        mock_memory.get_user_facts_prompt.return_value = ""
        mock_memory.get_user_profile.return_value = {"interests": [], "expertise_areas": [], "interaction_count": 0}
        mock_memory.get_user_memories.return_value = []

        with patch("config.KV_PREFIX_CACHE_ENABLED", True):
            prompt = agent.compile_prompt("u1", "s1", "Web", "test")

        # Layered prompt uses "[Session State]" delimiter
        assert "[Session State]" in prompt

    @patch("modules.agents.base.memory")
    def test_original_when_disabled(self, mock_memory, agent, mock_registry):
        mock_memory.get_user_facts_prompt.return_value = ""
        mock_memory.get_user_profile.return_value = {"interests": [], "expertise_areas": [], "interaction_count": 0}
        mock_memory.get_user_memories.return_value = []

        with patch("config.KV_PREFIX_CACHE_ENABLED", False):
            prompt = agent.compile_prompt("u1", "s1", "Web", "test")

        # Original ordering does NOT use "[Session State]" delimiter
        assert "[Session State]" not in prompt
        assert "---" in prompt  # Original trailing delimiter
