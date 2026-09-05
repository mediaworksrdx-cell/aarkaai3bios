"""
AARKAAI Backend – User Settings Module

Per-user preferences persistence for model selection, response style,
language, theme, streaming, and reasoning depth.
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from database import SessionLocal

logger = logging.getLogger(__name__)

# Valid option sets for settings validation
VALID_MODELS = {
    "aarka-2.0", "aarkaa-7b", "aarkaa-3b",
    "gemini-3.7", "gemini-3.7-flash",
    "gemini-2.5", "gemini-2.5-flash", "gemini-2.5-pro",  # backward compat with stored user prefs
}
VALID_RESPONSE_STYLES = {"concise", "balanced", "detailed", "professional"}
VALID_THEMES = {"dark", "light", "auto"}
VALID_LANGUAGES = {"en", "hi", "ta", "te", "kn", "ml", "mr", "bn", "gu", "pa"}
VALID_REASONING_DEPTHS = {"fast", "balanced", "deep", "low", "medium", "high"}

# Default settings applied when a user has no stored preferences
DEFAULT_SETTINGS = {
    "default_model": "aarka-2.0",
    "response_style": "balanced",
    "theme": "dark",
    "language": "en",
    "streaming_enabled": True,
    "reasoning_depth": "balanced",
    "about_you": "",
    "system_directives": "",
    "extended_thinking": True,
    "thinking_budget": 4096,
    "web_search_enabled": True,
    "deep_research_enabled": True,
    "market_data_enabled": True,
}


def _validate_setting(key: str, value) -> tuple[bool, str]:
    """Validate a single setting key-value pair. Returns (is_valid, error_message)."""
    validators = {
        "default_model": (VALID_MODELS, "string"),
        "response_style": (VALID_RESPONSE_STYLES, "string"),
        "theme": (VALID_THEMES, "string"),
        "language": (VALID_LANGUAGES, "string"),
        "streaming_enabled": (None, "bool"),
        "reasoning_depth": (VALID_REASONING_DEPTHS, "string"),
        "about_you": (None, "string"),
        "system_directives": (None, "string"),
        "extended_thinking": (None, "bool"),
        "thinking_budget": (None, "int"),
        "web_search_enabled": (None, "bool"),
        "deep_research_enabled": (None, "bool"),
        "market_data_enabled": (None, "bool"),
    }

    if key not in validators:
        return False, f"Unknown setting: '{key}'"

    valid_set, expected_type = validators[key]

    if expected_type == "bool":
        if not isinstance(value, bool):
            return False, f"'{key}' must be a boolean"
        return True, ""

    if expected_type == "int":
        if not isinstance(value, int):
            return False, f"'{key}' must be an integer"
        return True, ""

    if not isinstance(value, str):
        return False, f"'{key}' must be a string"
    if valid_set and value not in valid_set:
        return False, f"'{key}' must be one of: {sorted(valid_set)}"
    return True, ""


def get_user_settings(user_id: str) -> dict:
    """
    Retrieve the current user's settings.
    Returns defaults for any fields not yet persisted.
    """
    import config
    if config.MONGODB_URI:
        from modules.mongo_repository import UserSettingsRepo
        doc = UserSettingsRepo.get_settings(user_id)
        if doc and isinstance(doc.get("updated_at"), datetime):
            doc["updated_at"] = doc["updated_at"].isoformat()
        if "_id" in doc:
            del doc["_id"]
        return doc

    session = SessionLocal()
    try:
        row = session.query(UserSettings).filter(UserSettings.user_id == user_id).first()
        if not row:
            return {**DEFAULT_SETTINGS, "user_id": user_id}

        def _bool(val, default: bool) -> bool:
            """Convert SQLite INTEGER (0/1/None) to bool."""
            if val is None:
                return default
            return bool(val)

        return {
            "user_id": user_id,
            "default_model": row.default_model or DEFAULT_SETTINGS["default_model"],
            "response_style": row.response_style or DEFAULT_SETTINGS["response_style"],
            "theme": row.theme or DEFAULT_SETTINGS["theme"],
            "language": row.language or DEFAULT_SETTINGS["language"],
            "streaming_enabled": _bool(row.streaming_enabled, DEFAULT_SETTINGS["streaming_enabled"]),
            "reasoning_depth": row.reasoning_depth or DEFAULT_SETTINGS["reasoning_depth"],
            # Extended fields — present in all paths after migration
            "about_you": row.about_you or DEFAULT_SETTINGS["about_you"],
            "system_directives": row.system_directives or DEFAULT_SETTINGS["system_directives"],
            "extended_thinking": _bool(row.extended_thinking, DEFAULT_SETTINGS["extended_thinking"]),
            "thinking_budget": row.thinking_budget if row.thinking_budget is not None else DEFAULT_SETTINGS["thinking_budget"],
            "web_search_enabled": _bool(row.web_search_enabled, DEFAULT_SETTINGS["web_search_enabled"]),
            "deep_research_enabled": _bool(row.deep_research_enabled, DEFAULT_SETTINGS["deep_research_enabled"]),
            "market_data_enabled": _bool(row.market_data_enabled, DEFAULT_SETTINGS["market_data_enabled"]),
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
    except Exception as exc:
        logger.error("get_user_settings failed for %s: %s", user_id, exc)
        return {**DEFAULT_SETTINGS, "user_id": user_id}
    finally:
        session.close()



def update_user_settings(user_id: str, **kwargs) -> dict:
    """
    Upsert user settings. Only provided fields are updated;
    unmentioned fields retain their current values.

    Returns the updated settings dict.
    Raises ValueError on invalid input.
    """
    # Validate all provided fields before touching the DB
    errors = []
    for key, value in kwargs.items():
        is_valid, msg = _validate_setting(key, value)
        if not is_valid:
            errors.append(msg)
    if errors:
        raise ValueError("; ".join(errors))

    import config
    if config.MONGODB_URI:
        from modules.mongo_repository import UserSettingsRepo
        doc = UserSettingsRepo.update_settings(user_id, kwargs)
        if doc and isinstance(doc.get("updated_at"), datetime):
            doc["updated_at"] = doc["updated_at"].isoformat()
        if "_id" in doc:
            del doc["_id"]
        return doc

    from database import UserSettings

    session = SessionLocal()
    try:
        row = session.query(UserSettings).filter(UserSettings.user_id == user_id).first()

        if not row:
            # Create with defaults, then overlay provided values
            row = UserSettings(
                user_id=user_id,
                default_model=kwargs.get("default_model", DEFAULT_SETTINGS["default_model"]),
                response_style=kwargs.get("response_style", DEFAULT_SETTINGS["response_style"]),
                theme=kwargs.get("theme", DEFAULT_SETTINGS["theme"]),
                language=kwargs.get("language", DEFAULT_SETTINGS["language"]),
                streaming_enabled=kwargs.get("streaming_enabled", DEFAULT_SETTINGS["streaming_enabled"]),
                reasoning_depth=kwargs.get("reasoning_depth", DEFAULT_SETTINGS["reasoning_depth"]),
                # Extended fields
                about_you=kwargs.get("about_you", DEFAULT_SETTINGS["about_you"]),
                system_directives=kwargs.get("system_directives", DEFAULT_SETTINGS["system_directives"]),
                extended_thinking=kwargs.get("extended_thinking", DEFAULT_SETTINGS["extended_thinking"]),
                thinking_budget=kwargs.get("thinking_budget", DEFAULT_SETTINGS["thinking_budget"]),
                web_search_enabled=kwargs.get("web_search_enabled", DEFAULT_SETTINGS["web_search_enabled"]),
                deep_research_enabled=kwargs.get("deep_research_enabled", DEFAULT_SETTINGS["deep_research_enabled"]),
                market_data_enabled=kwargs.get("market_data_enabled", DEFAULT_SETTINGS["market_data_enabled"]),
            )
            session.add(row)
        else:
            # Update only the fields that were provided
            for key, value in kwargs.items():
                setattr(row, key, value)
            row.updated_at = datetime.now(timezone.utc)

        session.commit()
        session.refresh(row)
        logger.info("Updated settings for user %s: %s", user_id, list(kwargs.keys()))

        def _bool(val, default: bool) -> bool:
            if val is None:
                return default
            return bool(val)

        return {
            "user_id": user_id,
            "default_model": row.default_model,
            "response_style": row.response_style,
            "theme": row.theme,
            "language": row.language,
            "streaming_enabled": _bool(row.streaming_enabled, DEFAULT_SETTINGS["streaming_enabled"]),
            "reasoning_depth": row.reasoning_depth,
            "about_you": row.about_you or DEFAULT_SETTINGS["about_you"],
            "system_directives": row.system_directives or DEFAULT_SETTINGS["system_directives"],
            "extended_thinking": _bool(row.extended_thinking, DEFAULT_SETTINGS["extended_thinking"]),
            "thinking_budget": row.thinking_budget if row.thinking_budget is not None else DEFAULT_SETTINGS["thinking_budget"],
            "web_search_enabled": _bool(row.web_search_enabled, DEFAULT_SETTINGS["web_search_enabled"]),
            "deep_research_enabled": _bool(row.deep_research_enabled, DEFAULT_SETTINGS["deep_research_enabled"]),
            "market_data_enabled": _bool(row.market_data_enabled, DEFAULT_SETTINGS["market_data_enabled"]),
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
    except ValueError:
        session.rollback()
        raise
    except Exception as exc:
        session.rollback()
        logger.error("update_user_settings failed for %s: %s", user_id, exc)
        raise
    finally:
        session.close()
