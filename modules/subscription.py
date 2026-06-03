"""
AARKAAI – Subscription & Freemium Gate Module

Manages user subscription tiers and enforces daily usage limits
for premium features (strategy queries, full technical analysis).

Tiers:
  free    → 5 premium queries/day (basic tech summary + limited strategy)
  premium → unlimited (full strategy + multi-stock + alerts)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Session

from config import FREE_TIER_STRATEGY_LIMIT, FREE_TIER_RESET_HOURS
from database import Base, SessionLocal, _utcnow

logger = logging.getLogger(__name__)


# ─── Database Model ──────────────────────────────────────────────────────────


class UserSubscription(Base):
    """Tracks user subscription tier and daily premium usage."""

    __tablename__ = "user_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), nullable=False, unique=True, index=True)
    tier = Column(String(32), default="free")  # "free" | "premium"
    premium_queries_today = Column(Integer, default=0)
    last_query_date = Column(String(32), default="")  # ISO timestamp of window start
    subscription_start = Column(DateTime, nullable=True)
    subscription_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


# ─── Ensure table exists on import ──────────────────────────────────────────

def init():
    """Create the subscription table if it doesn't exist."""
    from database import engine
    UserSubscription.__table__.create(bind=engine, checkfirst=True)
    logger.info("Subscription table ready")


# ─── Core Functions ──────────────────────────────────────────────────────────


def _get_or_create_sub(session: Session, user_id: str) -> UserSubscription:
    """Get the subscription record, creating a free-tier default if missing."""
    sub = session.query(UserSubscription).filter(
        UserSubscription.user_id == user_id
    ).first()
    if sub is None:
        sub = UserSubscription(user_id=user_id, tier="free")
        session.add(sub)
        session.commit()
    return sub


def check_access(user_id: str, feature: str = "strategy") -> dict:
    """
    Check whether a user can access a premium feature.

    Returns
    -------
    dict with keys:
        allowed   : bool   — can the user proceed?
        remaining : int    — how many free queries left today
        tier      : str    — "free" or "premium"
        message   : str    — human-readable status message
    """
    session = SessionLocal()
    try:
        sub = _get_or_create_sub(session, user_id)

        # Premium users have unlimited access
        if sub.tier == "premium":
            # Check if subscription has expired
            if sub.subscription_end and sub.subscription_end < datetime.now(timezone.utc):
                # Expired — downgrade to free
                sub.tier = "free"
                session.commit()
                logger.info("Subscription expired for user %s, downgraded to free", user_id)
            else:
                return {
                    "allowed": True,
                    "remaining": -1,  # unlimited
                    "tier": "premium",
                    "message": "Premium access — unlimited strategy queries.",
                }

        # Free tier — check hourly window limit
        now = datetime.now(timezone.utc)
        
        # Check if window has expired
        reset_needed = True
        if sub.last_query_date:
            try:
                window_start = datetime.fromisoformat(sub.last_query_date)
                from datetime import timedelta
                if now - window_start < timedelta(hours=FREE_TIER_RESET_HOURS):
                    reset_needed = False
            except ValueError:
                pass # Fallback to reset if parsing fails

        # Reset counter if needed
        if reset_needed:
            sub.premium_queries_today = 0
            sub.last_query_date = now.isoformat()
            session.commit()

        remaining = FREE_TIER_STRATEGY_LIMIT - sub.premium_queries_today

        if remaining > 0:
            return {
                "allowed": True,
                "remaining": remaining,
                "tier": "free",
                "message": f"Free tier — {remaining} strategy queries remaining in this {FREE_TIER_RESET_HOURS}-hour window.",
            }
        else:
            return {
                "allowed": False,
                "remaining": 0,
                "tier": "free",
                "message": (
                    f"🔒 You've used all your free strategy queries for this {FREE_TIER_RESET_HOURS}-hour window. "
                    "Upgrade to Aarka AI Premium for unlimited technical analysis "
                    "and options strategies. Visit your account settings to subscribe."
                ),
            }

    except Exception as exc:
        logger.error("Subscription check failed for %s: %s", user_id, exc)
        # Fail open — allow access on errors to avoid blocking users
        return {
            "allowed": True,
            "remaining": 1,
            "tier": "free",
            "message": "Access granted (fallback).",
        }
    finally:
        session.close()


def record_premium_usage(user_id: str) -> None:
    """Increment the daily premium query counter after a strategy query."""
    session = SessionLocal()
    try:
        sub = _get_or_create_sub(session, user_id)

        # Skip counting for premium users
        if sub.tier == "premium":
            return

        now = datetime.now(timezone.utc)
        reset_needed = True
        if sub.last_query_date:
            try:
                window_start = datetime.fromisoformat(sub.last_query_date)
                from datetime import timedelta
                if now - window_start < timedelta(hours=FREE_TIER_RESET_HOURS):
                    reset_needed = False
            except ValueError:
                pass

        if reset_needed:
            sub.premium_queries_today = 1
            sub.last_query_date = now.isoformat()
        else:
            sub.premium_queries_today += 1

        session.commit()
        logger.debug(
            "User %s used %d/%d free strategy queries in current window",
            user_id, sub.premium_queries_today, FREE_TIER_STRATEGY_LIMIT,
        )
    except Exception as exc:
        logger.error("Failed to record premium usage for %s: %s", user_id, exc)
        session.rollback()
    finally:
        session.close()


def upgrade_user(user_id: str, months: int = 1) -> dict:
    """
    Upgrade a user to premium tier.

    Parameters
    ----------
    user_id : str
    months : int — number of months of premium access

    Returns
    -------
    dict with subscription details
    """
    from datetime import timedelta

    session = SessionLocal()
    try:
        sub = _get_or_create_sub(session, user_id)

        now = datetime.now(timezone.utc)
        # If already premium, extend from current end date
        if sub.tier == "premium" and sub.subscription_end and sub.subscription_end > now:
            start = sub.subscription_end
        else:
            start = now

        sub.tier = "premium"
        sub.subscription_start = now
        sub.subscription_end = start + timedelta(days=30 * months)
        session.commit()

        logger.info(
            "User %s upgraded to premium (until %s)",
            user_id, sub.subscription_end.strftime("%Y-%m-%d"),
        )

        return {
            "user_id": user_id,
            "tier": "premium",
            "start": sub.subscription_start.isoformat(),
            "end": sub.subscription_end.isoformat(),
            "months": months,
        }
    except Exception as exc:
        logger.error("Failed to upgrade user %s: %s", user_id, exc)
        session.rollback()
        raise
    finally:
        session.close()


def get_subscription_info(user_id: str) -> dict:
    """Return the current subscription status for a user."""
    session = SessionLocal()
    try:
        sub = _get_or_create_sub(session, user_id)
        now = datetime.now(timezone.utc)
        used = 0
        if sub.last_query_date:
            try:
                window_start = datetime.fromisoformat(sub.last_query_date)
                from datetime import timedelta
                if now - window_start < timedelta(hours=FREE_TIER_RESET_HOURS):
                    used = sub.premium_queries_today
            except ValueError:
                pass

        return {
            "user_id": user_id,
            "tier": sub.tier,
            "queries_used_in_window": used,
            "window_limit": FREE_TIER_STRATEGY_LIMIT if sub.tier == "free" else -1,
            "subscription_end": sub.subscription_end.isoformat() if sub.subscription_end else None,
        }
    except Exception as exc:
        logger.error("Failed to get subscription info for %s: %s", user_id, exc)
        return {"user_id": user_id, "tier": "free", "queries_used_in_window": 0, "window_limit": FREE_TIER_STRATEGY_LIMIT}
    finally:
        session.close()
