import logging
import yfinance as yf
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import Base, SessionLocal, _utcnow, MarketAlert

def init() -> None:
    """Create alerts table."""
    try:
        session = SessionLocal()
        engine = session.get_bind()
        Base.metadata.create_all(bind=engine)
        session.close()
        logger.info("Notifications tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating notifications tables: {e}")

def get_current_price(symbol: str) -> float:
    """Helper to fetch live price."""
    try:
        ticker = yf.Ticker(symbol)
        return ticker.fast_info.last_price
    except Exception as e:
        logger.warning(f"Error fetching live price for {symbol}: {e}")
        return 0.0

def create_alert(user_id: str, symbol: str, condition: str, threshold: float, notes: str = None) -> dict:
    """Create a new price alert. Validate condition type."""
    valid_conditions = ['above', 'below', 'crosses_above', 'crosses_below', 'pct_change']
    if condition not in valid_conditions:
        return {"status": "error", "message": f"Invalid condition. Must be one of {valid_conditions}"}

    session: Session = SessionLocal()
    try:
        alert = MarketAlert(
            user_id=user_id,
            symbol=symbol.upper(),
            condition=condition,
            threshold=threshold,
            notes=notes
        )
        session.add(alert)
        session.commit()
        session.refresh(alert)
        return {"status": "success", "alert_id": alert.id, "message": "Alert created"}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error in create_alert: {e}")
        return {"status": "error", "message": "Database error"}
    finally:
        session.close()

def check_alerts(user_id: str) -> list[dict]:
    """Check all active alerts against live prices. Return list of triggered alerts."""
    session: Session = SessionLocal()
    triggered = []
    try:
        alerts = session.query(MarketAlert).filter_by(user_id=user_id, is_active=True).all()
        prices_cache = {}
        
        for alert in alerts:
            symbol = alert.symbol
            if symbol not in prices_cache:
                prices_cache[symbol] = get_current_price(symbol)
            
            price = prices_cache[symbol]
            if price == 0.0:
                continue
                
            is_triggered = False
            
            if alert.condition == 'above' and price > alert.threshold:
                is_triggered = True
            elif alert.condition == 'below' and price < alert.threshold:
                is_triggered = True
            # crosses logic needs previous price history, treating as above/below for now
            elif alert.condition == 'crosses_above' and price >= alert.threshold:
                is_triggered = True
            elif alert.condition == 'crosses_below' and price <= alert.threshold:
                is_triggered = True
                
            if is_triggered:
                alert.is_active = False
                alert.triggered_at = _utcnow()
                triggered.append({
                    "alert_id": alert.id,
                    "symbol": alert.symbol,
                    "condition": alert.condition,
                    "threshold": alert.threshold,
                    "triggered_price": price,
                    "notes": alert.notes
                })
        
        if triggered:
            session.commit()
            
        return triggered
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error in check_alerts: {e}")
        return []
    finally:
        session.close()

def get_active_alerts(user_id: str) -> list[dict]:
    """List all active alerts for user."""
    session: Session = SessionLocal()
    try:
        alerts = session.query(MarketAlert).filter_by(user_id=user_id, is_active=True).all()
        return [{
            "id": a.id,
            "symbol": a.symbol,
            "condition": a.condition,
            "threshold": a.threshold,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "notes": a.notes
        } for a in alerts]
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_active_alerts: {e}")
        return []
    finally:
        session.close()

def cancel_alert(user_id: str, alert_id: int) -> dict:
    """Cancel (deactivate) a specific alert."""
    session: Session = SessionLocal()
    try:
        alert = session.query(MarketAlert).filter_by(id=alert_id, user_id=user_id).first()
        if alert:
            alert.is_active = False
            session.commit()
            return {"status": "success", "message": f"Alert {alert_id} cancelled"}
        return {"status": "error", "message": "Alert not found"}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error in cancel_alert: {e}")
        return {"status": "error", "message": "Database error"}
    finally:
        session.close()

def get_alert_history(user_id: str, limit: int = 20) -> list[dict]:
    """Get alert history including triggered alerts."""
    session: Session = SessionLocal()
    try:
        alerts = session.query(MarketAlert).filter_by(user_id=user_id).order_by(MarketAlert.created_at.desc()).limit(limit).all()
        return [{
            "id": a.id,
            "symbol": a.symbol,
            "condition": a.condition,
            "threshold": a.threshold,
            "is_active": a.is_active,
            "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "notes": a.notes
        } for a in alerts]
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_alert_history: {e}")
        return []
    finally:
        session.close()

def get_upcoming_market_events() -> list[dict]:
    """Static list of upcoming market events for next 30 days:
    F&O expiries, RBI policy dates, major earnings season dates, IPO dates.
    Hardcoded for Aug-Sep 2026."""
    return [
        {"date": "2026-08-27", "event_type": "F&O Expiry", "description": "August Monthly Expiry"},
        {"date": "2026-09-24", "event_type": "F&O Expiry", "description": "September Monthly Expiry"},
        {"date": "2026-08-15", "event_type": "Market Holiday", "description": "Independence Day"},
        {"date": "2026-09-07", "event_type": "Market Holiday", "description": "Ganesh Chaturthi"},
        {"date": "2026-08-30", "event_type": "Economic Data", "description": "Q1 GDP Data Release"},
    ]
