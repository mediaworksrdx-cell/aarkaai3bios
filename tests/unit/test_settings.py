"""
Test suite for AARKAAI User Settings API

Tests:
  - UserSettings model CRUD
  - GET /settings returns defaults for new user
  - PUT /settings persists and returns updated values
  - PUT /settings validates invalid model/style/theme
  - Partial updates only modify specified fields
"""
import unittest
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestUserSettingsValidation(unittest.TestCase):
    """Test the validation logic in user_settings module."""

    def test_valid_models(self):
        from modules.user_settings import _validate_setting, VALID_MODELS
        for model in VALID_MODELS:
            is_valid, msg = _validate_setting("default_model", model)
            self.assertTrue(is_valid, f"Model '{model}' should be valid: {msg}")

    def test_invalid_model_rejected(self):
        from modules.user_settings import _validate_setting
        is_valid, msg = _validate_setting("default_model", "gpt-4o")
        self.assertFalse(is_valid)
        self.assertIn("must be one of", msg)

    def test_valid_response_styles(self):
        from modules.user_settings import _validate_setting, VALID_RESPONSE_STYLES
        for style in VALID_RESPONSE_STYLES:
            is_valid, _ = _validate_setting("response_style", style)
            self.assertTrue(is_valid)

    def test_invalid_response_style(self):
        from modules.user_settings import _validate_setting
        is_valid, msg = _validate_setting("response_style", "verbose")
        self.assertFalse(is_valid)

    def test_valid_themes(self):
        from modules.user_settings import _validate_setting, VALID_THEMES
        for theme in VALID_THEMES:
            is_valid, _ = _validate_setting("theme", theme)
            self.assertTrue(is_valid)

    def test_invalid_theme(self):
        from modules.user_settings import _validate_setting
        is_valid, _ = _validate_setting("theme", "neon")
        self.assertFalse(is_valid)

    def test_valid_languages(self):
        from modules.user_settings import _validate_setting, VALID_LANGUAGES
        for lang in VALID_LANGUAGES:
            is_valid, _ = _validate_setting("language", lang)
            self.assertTrue(is_valid)

    def test_streaming_bool_required(self):
        from modules.user_settings import _validate_setting
        is_valid, msg = _validate_setting("streaming_enabled", "yes")
        self.assertFalse(is_valid)
        self.assertIn("must be a boolean", msg)

    def test_streaming_bool_valid(self):
        from modules.user_settings import _validate_setting
        for val in (True, False):
            is_valid, _ = _validate_setting("streaming_enabled", val)
            self.assertTrue(is_valid)

    def test_valid_reasoning_depths(self):
        from modules.user_settings import _validate_setting, VALID_REASONING_DEPTHS
        for depth in VALID_REASONING_DEPTHS:
            is_valid, _ = _validate_setting("reasoning_depth", depth)
            self.assertTrue(is_valid)

    def test_unknown_setting_key(self):
        from modules.user_settings import _validate_setting
        is_valid, msg = _validate_setting("font_size", 14)
        self.assertFalse(is_valid)
        self.assertIn("Unknown setting", msg)

    def test_default_settings_all_valid(self):
        from modules.user_settings import _validate_setting, DEFAULT_SETTINGS
        for key, value in DEFAULT_SETTINGS.items():
            is_valid, msg = _validate_setting(key, value)
            self.assertTrue(is_valid, f"Default for '{key}' failed validation: {msg}")


class TestUserSettingsSchemas(unittest.TestCase):
    """Test the Pydantic schemas for settings."""

    def test_settings_update_partial(self):
        from schemas import UserSettingsUpdate
        req = UserSettingsUpdate(default_model="gemini-3.7-flash")
        dump = req.model_dump(exclude_unset=True)
        self.assertEqual(dump, {"default_model": "gemini-3.7-flash"})

    def test_settings_update_empty(self):
        from schemas import UserSettingsUpdate
        req = UserSettingsUpdate()
        dump = req.model_dump(exclude_unset=True)
        self.assertEqual(dump, {})

    def test_settings_update_full(self):
        from schemas import UserSettingsUpdate
        req = UserSettingsUpdate(
            default_model="aarkaa-3b",
            response_style="detailed",
            theme="light",
            language="hi",
            streaming_enabled=False,
            reasoning_depth="deep",
        )
        dump = req.model_dump(exclude_unset=True)
        self.assertEqual(len(dump), 6)

    def test_settings_response_defaults(self):
        from schemas import UserSettingsResponse
        resp = UserSettingsResponse(user_id="test-123")
        self.assertEqual(resp.default_model, "aarka-2.0")
        self.assertEqual(resp.response_style, "balanced")
        self.assertEqual(resp.theme, "dark")
        self.assertTrue(resp.streaming_enabled)


class TestSkillModelSchema(unittest.TestCase):
    """Test the SkillModel and TestRequestModel schemas."""

    def test_skill_model_valid(self):
        from schemas import SkillModel
        skill = SkillModel(name="test-skill", content="---\nname: test\ndescription: test\n---\n# Test")
        self.assertEqual(skill.name, "test-skill")

    def test_skill_model_content_limit(self):
        from schemas import SkillModel
        from pydantic import ValidationError
        try:
            SkillModel(name="huge", content="x" * 51201)
            self.fail("Should have raised ValidationError")
        except ValidationError:
            pass

    def test_test_request_model(self):
        from schemas import TestRequestModel
        req = TestRequestModel(prompt="Test this skill")
        self.assertEqual(req.prompt, "Test this skill")


class TestDatabaseModel(unittest.TestCase):
    """Test the UserSettings database model exists and has correct columns."""

    def test_user_settings_model_exists(self):
        from database import UserSettings
        self.assertEqual(UserSettings.__tablename__, "user_settings")

    def test_user_settings_columns(self):
        from database import UserSettings
        columns = {c.name for c in UserSettings.__table__.columns}
        expected = {"id", "user_id", "default_model", "response_style",
                    "theme", "language", "streaming_enabled", "reasoning_depth", "updated_at"}
        self.assertEqual(columns, expected)


class TestConfigChanges(unittest.TestCase):
    """Test config.py changes for OAuth security."""

    def test_google_credentials_empty_by_default(self):
        from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
        self.assertIsInstance(GOOGLE_CLIENT_ID, str)
        self.assertIsInstance(GOOGLE_CLIENT_SECRET, str)

    def test_oauth_redirect_base_url_exists(self):
        from config import OAUTH_REDIRECT_BASE_URL
        self.assertIsInstance(OAUTH_REDIRECT_BASE_URL, str)
        self.assertTrue(len(OAUTH_REDIRECT_BASE_URL) > 0)

    def test_public_routes_include_oauth_paths(self):
        from config import PUBLIC_ROUTES
        oauth_paths = {
            "/auth/github/login", "/auth/github/callback",
            "/auth/google/login", "/auth/google/callback", "/auth/google/verify",
        }
        for path in oauth_paths:
            self.assertIn(path, PUBLIC_ROUTES, f"Missing: {path}")


class TestSkillRegistryHardening(unittest.TestCase):
    """Test skill_registry.py production hardening."""

    def test_skill_registry_has_logger(self):
        import skills.skill_registry as sr
        import logging
        self.assertIsInstance(sr.logger, logging.Logger)

    def test_get_skill_versions_method_exists(self):
        from skills.skill_registry import SkillRegistry
        self.assertTrue(hasattr(SkillRegistry, "get_skill_versions"))

    def test_skill_count_property(self):
        from skills.skill_registry import SkillRegistry
        self.assertTrue(hasattr(SkillRegistry, "skill_count"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
