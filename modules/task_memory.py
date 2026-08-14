"""
AARKAAI – Task Memory manager
Handles reading, writing, and state serialization of TaskGoals.
"""
from __future__ import annotations

import json
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from database import SessionLocal, TaskGoal

logger = logging.getLogger(__name__)

def save_goal(user_id: str, session_id: str, goal_text: str, plan: Dict[str, Any]) -> int:
    """Create a persistent task goal record."""
    session: Session = SessionLocal()
    try:
        goal = TaskGoal(
            user_id=user_id,
            session_id=session_id,
            goal_text=goal_text,
            task_dag=json.dumps(plan),
            scratchpad=json.dumps({
                "facts": [],
                "assumptions": [],
                "unknowns": [],
                "evidence": []
            }),
            status="pending"
        )
        session.add(goal)
        session.commit()
        logger.info("Saved new task goal with ID: %d for user %s", goal.id, user_id)
        return goal.id
    except Exception as exc:
        session.rollback()
        logger.error("save_goal failed: %s", exc)
        raise exc
    finally:
        session.close()

def get_goal(goal_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve goal state info from DB."""
    session: Session = SessionLocal()
    try:
        row = session.query(TaskGoal).filter(TaskGoal.id == goal_id).first()
        if not row:
            return None
        return {
            "id": row.id,
            "user_id": row.user_id,
            "session_id": row.session_id,
            "goal_text": row.goal_text,
            "task_dag": json.loads(row.task_dag),
            "scratchpad": json.loads(row.scratchpad),
            "status": row.status
        }
    finally:
        session.close()

def update_goal_state(goal_id: int, plan: Dict[str, Any], scratchpad: Dict[str, Any], status: str) -> None:
    """Update database values representing execution progress."""
    session: Session = SessionLocal()
    try:
        row = session.query(TaskGoal).filter(TaskGoal.id == goal_id).first()
        if row:
            row.task_dag = json.dumps(plan)
            row.scratchpad = json.dumps(scratchpad)
            row.status = status
            session.commit()
            logger.debug("Updated goal %d to state status=%s", goal_id, status)
    except Exception as exc:
        session.rollback()
        logger.error("update_goal_state failed: %s", exc)
    finally:
        session.close()
