import logging
import yfinance as yf
from typing import List, Dict, Any
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from database import Base, SessionLocal, _utcnow, PortfolioHolding, WatchlistItem


def init() -> None:
    """Create tables if they don't exist."""
    try:
        session = SessionLocal()
        engine = session.get_bind()
        Base.metadata.create_all(bind=engine)
        session.close()
        logger.info("Portfolio tables created successfully.")
    except Exception as e:
        logger.error(f"Error creating portfolio tables: {e}")


def get_current_price(symbol: str) -> float:
    """Helper to fetch live price."""
    try:
        ticker = yf.Ticker(symbol)
        data = ticker.fast_info
        return data.last_price
    except Exception as e:
        logger.warning(f"Error fetching live price for {symbol}: {e}")
        return 0.0


def add_holding(user_id: str, symbol: str, quantity: float, avg_price: float) -> dict:
    """Add or update a portfolio holding. If symbol exists, recalculate avg price."""
    session: Session = SessionLocal()
    try:
        symbol = symbol.upper()
        holding = session.query(PortfolioHolding).filter_by(user_id=user_id, symbol=symbol).first()
        
        if holding:
            # Recalculate average price
            total_cost = (holding.quantity * holding.avg_price) + (quantity * avg_price)
            total_qty = holding.quantity + quantity
            
            if total_qty == 0:
                session.delete(holding)
                session.commit()
                return {"status": "success", "message": f"Holding {symbol} removed due to 0 quantity"}
                
            holding.avg_price = total_cost / total_qty
            holding.quantity = total_qty
        else:
            holding = PortfolioHolding(
                user_id=user_id,
                symbol=symbol,
                quantity=quantity,
                avg_price=avg_price
            )
            session.add(holding)
            
        session.commit()
        session.refresh(holding)
        return {
            "status": "success",
            "holding": {
                "symbol": holding.symbol,
                "quantity": holding.quantity,
                "avg_price": holding.avg_price
            }
        }
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error in add_holding: {e}")
        return {"status": "error", "message": "Database error occurred"}
    finally:
        session.close()


def remove_holding(user_id: str, symbol: str) -> dict:
    """Remove a holding from portfolio."""
    session: Session = SessionLocal()
    try:
        symbol = symbol.upper()
        holding = session.query(PortfolioHolding).filter_by(user_id=user_id, symbol=symbol).first()
        if holding:
            session.delete(holding)
            session.commit()
            return {"status": "success", "message": f"Removed {symbol} from portfolio"}
        return {"status": "error", "message": f"Holding {symbol} not found"}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error in remove_holding: {e}")
        return {"status": "error", "message": "Database error occurred"}
    finally:
        session.close()


def get_holdings(user_id: str) -> list[dict]:
    """Get all holdings with live market prices and P&L."""
    session: Session = SessionLocal()
    try:
        holdings = session.query(PortfolioHolding).filter_by(user_id=user_id).all()
        result = []
        for h in holdings:
            current_price = get_current_price(h.symbol)
            current_value = h.quantity * current_price
            invested_value = h.quantity * h.avg_price
            pnl = current_value - invested_value
            pnl_pct = (pnl / invested_value * 100) if invested_value > 0 else 0.0
            
            result.append({
                "symbol": h.symbol,
                "quantity": h.quantity,
                "avg_price": h.avg_price,
                "current_price": current_price,
                "current_value": current_value,
                "pnl": pnl,
                "pnl_pct": pnl_pct
            })
        return result
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_holdings: {e}")
        return []
    finally:
        session.close()


def get_portfolio_summary(user_id: str) -> dict:
    """Portfolio summary."""
    holdings = get_holdings(user_id)
    if not holdings:
        return {
            "total_invested": 0.0,
            "current_value": 0.0,
            "total_pnl": 0.0,
            "total_pnl_pct": 0.0,
            "holdings_count": 0,
            "top_gainer": None,
            "top_loser": None,
            "sector_allocation": {}
        }
        
    total_invested = sum(h["quantity"] * h["avg_price"] for h in holdings)
    current_value = sum(h["current_value"] for h in holdings)
    total_pnl = current_value - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0.0
    
    sorted_by_pct = sorted(holdings, key=lambda x: x["pnl_pct"])
    top_loser = sorted_by_pct[0]["symbol"] if sorted_by_pct else None
    top_gainer = sorted_by_pct[-1]["symbol"] if sorted_by_pct else None
    
    # Sector allocation proxy based on equal weighting if sector data unavailable
    sector_allocation = {"General": 100.0}
    
    return {
        "total_invested": total_invested,
        "current_value": current_value,
        "total_pnl": total_pnl,
        "total_pnl_pct": total_pnl_pct,
        "holdings_count": len(holdings),
        "top_gainer": top_gainer,
        "top_loser": top_loser,
        "sector_allocation": sector_allocation
    }


def get_portfolio_risk(user_id: str) -> dict:
    """Portfolio risk metrics."""
    holdings = get_holdings(user_id)
    if not holdings:
        return {
            "portfolio_beta": 1.0,
            "concentration_risk": 0.0,
            "largest_position_pct": 0.0,
            "sector_diversification_score": 0.0
        }
        
    current_value = sum(h["current_value"] for h in holdings)
    
    if current_value == 0:
        return {
            "portfolio_beta": 1.0,
            "concentration_risk": 0.0,
            "largest_position_pct": 0.0,
            "sector_diversification_score": 0.0
        }
        
    weights = [h["current_value"] / current_value for h in holdings]
    hhi = sum((w * 100) ** 2 for w in weights)
    largest_position = max(weights) * 100 if weights else 0.0
    
    # Simple proxy for beta (1.0 default)
    portfolio_beta = 1.0
    # Simple proxy for diversification score (100 is perfectly diversified across arbitrary sectors)
    sector_diversification_score = min(100.0, len(holdings) * 10.0)
    
    return {
        "portfolio_beta": portfolio_beta,
        "concentration_risk": hhi,
        "largest_position_pct": largest_position,
        "sector_diversification_score": sector_diversification_score
    }


def add_to_watchlist(user_id: str, symbol: str) -> dict:
    """Add symbol to watchlist."""
    session: Session = SessionLocal()
    try:
        symbol = symbol.upper()
        item = session.query(WatchlistItem).filter_by(user_id=user_id, symbol=symbol).first()
        if not item:
            item = WatchlistItem(user_id=user_id, symbol=symbol)
            session.add(item)
            session.commit()
            return {"status": "success", "message": f"Added {symbol} to watchlist"}
        return {"status": "success", "message": f"{symbol} already in watchlist"}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error in add_to_watchlist: {e}")
        return {"status": "error", "message": "Database error occurred"}
    finally:
        session.close()


def remove_from_watchlist(user_id: str, symbol: str) -> dict:
    """Remove from watchlist."""
    session: Session = SessionLocal()
    try:
        symbol = symbol.upper()
        item = session.query(WatchlistItem).filter_by(user_id=user_id, symbol=symbol).first()
        if item:
            session.delete(item)
            session.commit()
            return {"status": "success", "message": f"Removed {symbol} from watchlist"}
        return {"status": "error", "message": f"{symbol} not found in watchlist"}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"Database error in remove_from_watchlist: {e}")
        return {"status": "error", "message": "Database error occurred"}
    finally:
        session.close()


def get_watchlist(user_id: str) -> list[dict]:
    """Get watchlist with live prices."""
    session: Session = SessionLocal()
    try:
        items = session.query(WatchlistItem).filter_by(user_id=user_id).all()
        result = []
        for item in items:
            symbol = item.symbol
            price = get_current_price(symbol)
            
            # Fetch previous close for change metrics
            try:
                ticker = yf.Ticker(symbol)
                prev_close = ticker.fast_info.previous_close
                change = price - prev_close
                change_pct = (change / prev_close * 100) if prev_close else 0.0
            except Exception:
                change = 0.0
                change_pct = 0.0
                
            result.append({
                "symbol": symbol,
                "current_price": price,
                "change": change,
                "change_pct": change_pct
            })
        return result
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_watchlist: {e}")
        return []
    finally:
        session.close()
