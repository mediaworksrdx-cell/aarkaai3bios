import logging
from datetime import datetime, date, time, timedelta
from typing import Dict, Any, List
import pytz

logger = logging.getLogger(__name__)

def get_trading_holidays(year: int = 2026, exchange: str = "NSE") -> list:
    """Get list of trading holidays. Hardcoded for NSE 2026.
    Returns list of {date, name, day_of_week}."""
    holidays = []
    if exchange.upper() == "NSE" and year == 2026:
        holiday_dates = [
            (date(2026, 1, 26), "Republic Day"),
            (date(2026, 3, 3), "Holi"),
            (date(2026, 3, 20), "Eid-Ul-Fitr"),
            (date(2026, 4, 3), "Good Friday"),
            (date(2026, 4, 14), "Dr. Baba Saheb Ambedkar Jayanti"),
            (date(2026, 5, 1), "Maharashtra Day"),
            (date(2026, 5, 27), "Bakri Id"),
            (date(2026, 8, 15), "Independence Day"),
            (date(2026, 9, 14), "Ganesh Chaturthi"),
            (date(2026, 10, 2), "Mahatma Gandhi Jayanti"),
            (date(2026, 10, 18), "Dussehra"),
            (date(2026, 11, 8), "Diwali"),
            (date(2026, 11, 24), "Guru Nanak Jayanti"),
            (date(2026, 12, 25), "Christmas"),
        ]
        for d, name in holiday_dates:
            holidays.append({
                "date": str(d),
                "name": name,
                "day_of_week": d.strftime("%A")
            })
    return holidays

def market_session_info(exchange: str = "NSE") -> dict:
    """Full session breakdown: pre_market, market_open, market_close, post_market times."""
    exchange = exchange.upper()
    if exchange in ["NSE", "BSE"]:
        return {
            "pre_market": "09:00:00",
            "market_open": "09:15:00",
            "market_close": "15:30:00",
            "post_market": "16:00:00",
            "timezone": "Asia/Kolkata"
        }
    elif exchange in ["NYSE", "NASDAQ"]:
        return {
            "pre_market": "04:00:00",
            "market_open": "09:30:00",
            "market_close": "16:00:00",
            "post_market": "20:00:00",
            "timezone": "America/New_York"
        }
    return {}

def is_trading_day(check_date: date = None, exchange: str = "NSE") -> bool:
    """Check if a given date is a trading day (not weekend, not holiday)."""
    if check_date is None:
        check_date = date.today()
    
    if check_date.weekday() >= 5: # Saturday or Sunday
        return False
        
    if exchange.upper() == "NSE" and check_date.year == 2026:
        holiday_dates = [datetime.strptime(h["date"], "%Y-%m-%d").date() for h in get_trading_holidays(check_date.year, exchange)]
        if check_date in holiday_dates:
            return False
            
    return True

def is_market_open(exchange: str = "NSE") -> dict:
    """Check if market is currently open.
    Supports: NSE (9:15-15:30 IST), BSE (9:15-15:30 IST), NYSE (9:30-16:00 ET), NASDAQ (9:30-16:00 ET).
    Returns dict with is_open, exchange, current_time, session (pre_market/market/post_market/closed), next_open."""
    try:
        info = market_session_info(exchange)
        if not info:
            return {"is_open": False, "error": "Unknown exchange"}
            
        tz = pytz.timezone(info["timezone"])
        now = datetime.now(tz)
        
        pre_mkt = datetime.strptime(info["pre_market"], "%H:%M:%S").time()
        mkt_open = datetime.strptime(info["market_open"], "%H:%M:%S").time()
        mkt_close = datetime.strptime(info["market_close"], "%H:%M:%S").time()
        post_mkt = datetime.strptime(info["post_market"], "%H:%M:%S").time()
        
        current_time = now.time()
        is_td = is_trading_day(now.date(), exchange)
        
        session = "closed"
        is_open = False
        
        if is_td:
            if mkt_open <= current_time < mkt_close:
                session = "market"
                is_open = True
            elif pre_mkt <= current_time < mkt_open:
                session = "pre_market"
            elif mkt_close <= current_time < post_mkt:
                session = "post_market"

        # Find next open
        next_open = None
        if session == "market":
            next_open = str(now.date()) + " " + info["market_open"]
        else:
            check_date = now.date() if current_time < mkt_open else now.date() + timedelta(days=1)
            while not is_trading_day(check_date, exchange):
                check_date += timedelta(days=1)
            next_open = str(check_date) + " " + info["market_open"]
            
        return {
            "is_open": is_open,
            "exchange": exchange,
            "current_time": str(now),
            "session": session,
            "next_open": next_open
        }
    except Exception as e:
        logger.error(f"Error in is_market_open: {e}")
        return {"is_open": False, "error": str(e)}

def next_expiry(expiry_type: str = "monthly", exchange: str = "NSE") -> dict:
    """Next expiry date.
    expiry_type: 'weekly' (Thursday), 'monthly' (last Thursday)
    Returns dict with expiry_date, days_remaining, expiry_type."""
    try:
        info = market_session_info(exchange)
        if not info:
            return {}
        tz = pytz.timezone(info.get("timezone", "Asia/Kolkata"))
        now = datetime.now(tz).date()
        
        target_weekday = 3 # Thursday
        
        if expiry_type == "weekly":
            days_ahead = target_weekday - now.weekday()
            if days_ahead < 0:
                days_ahead += 7
            next_exp = now + timedelta(days=days_ahead)
            while not is_trading_day(next_exp, exchange):
                next_exp -= timedelta(days=1)
        elif expiry_type == "monthly":
            import calendar
            last_day = calendar.monthrange(now.year, now.month)[1]
            last_date = date(now.year, now.month, last_day)
            days_back = (last_date.weekday() - target_weekday) % 7
            last_thursday = last_date - timedelta(days=days_back)
            
            if now > last_thursday:
                next_month = now.month + 1 if now.month < 12 else 1
                next_year = now.year if now.month < 12 else now.year + 1
                last_day = calendar.monthrange(next_year, next_month)[1]
                last_date = date(next_year, next_month, last_day)
                days_back = (last_date.weekday() - target_weekday) % 7
                next_exp = last_date - timedelta(days=days_back)
            else:
                next_exp = last_thursday
                
            while not is_trading_day(next_exp, exchange):
                next_exp -= timedelta(days=1)
        else:
            return {}

        days_remaining = (next_exp - now).days
        
        return {
            "expiry_date": str(next_exp),
            "days_remaining": days_remaining,
            "expiry_type": expiry_type
        }
    except Exception as e:
        logger.error(f"Error in next_expiry: {e}")
        return {}

def trading_days_between(start_date: date, end_date: date, exchange: str = "NSE") -> int:
    """Count trading days between two dates."""
    try:
        if start_date > end_date:
            return 0
        count = 0
        current = start_date
        while current <= end_date:
            if is_trading_day(current, exchange):
                count += 1
            current += timedelta(days=1)
        return count
    except Exception as e:
        logger.error(f"Error in trading_days_between: {e}")
        return 0

def time_to_expiry(expiry_date_str: str) -> dict:
    """Calculate time remaining to expiry.
    Returns days, hours, minutes, trading_days_remaining, as_fraction_of_year."""
    try:
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        expiry_dt = datetime.combine(expiry_date, time(15, 30))
        
        now = datetime.now()
        diff = expiry_dt - now
        
        if diff.total_seconds() <= 0:
            return {"days": 0, "hours": 0, "minutes": 0, "trading_days_remaining": 0, "as_fraction_of_year": 0.0}
            
        days = diff.days
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        
        trading_days = trading_days_between(now.date(), expiry_date)
        as_fraction = trading_days / 252.0
        
        return {
            "days": days,
            "hours": hours,
            "minutes": minutes,
            "trading_days_remaining": trading_days,
            "as_fraction_of_year": round(as_fraction, 4)
        }
    except Exception as e:
        logger.error(f"Error in time_to_expiry: {e}")
        return {}
