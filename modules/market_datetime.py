"""
AARKAAI – Market date/time utilities.

* Exchange rules (sessions, expiry weekday, trading-days-per-year) are loaded
  from ``modules/market_rules.json`` (override with AARKA_MARKET_RULES_PATH).
* Holidays are fetched from the exchange source and cached per year under
  ``data/market_holidays/``. Operators may also drop a verified JSON file in
  that directory. Nothing is hardcoded; if no calendar is available the
  functions report ``holiday_calendar_verified = False`` instead of guessing.
"""
from __future__ import annotations

import calendar
import json
import logging
import os
from datetime import date, datetime, time, timedelta, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytz

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parent.parent
_RULES_PATH = Path(os.environ.get("AARKA_MARKET_RULES_PATH", Path(__file__).with_name("market_rules.json")))
_HOLIDAY_DIR = Path(os.environ.get("AARKA_HOLIDAY_DIR", _ROOT / "data" / "market_holidays"))
_WEEKDAYS = {name: i for i, name in enumerate(calendar.day_name)}


@lru_cache(maxsize=1)
def _rules() -> Dict[str, Any]:
    with open(_RULES_PATH, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {k.upper(): v for k, v in data.items() if not k.startswith("_")}


def exchange_rules(exchange: str) -> Dict[str, Any]:
    ex = (exchange or "").upper()
    rules = _rules()
    if ex not in rules:
        raise ValueError(f"Unknown exchange '{exchange}'. Configured: {sorted(rules)}")
    return rules[ex]


def _tz(exchange: str):
    return pytz.timezone(exchange_rules(exchange)["timezone"])


def now(exchange: str) -> datetime:
    return datetime.now(_tz(exchange))


def _parse_hhmm(s: str) -> time:
    return datetime.strptime(s, "%H:%M").time()


# ─────────────────────────────── holidays ─────────────────────────────────────

def _cache_file(exchange: str, year: int) -> Path:
    return _HOLIDAY_DIR / f"{exchange.upper()}_{year}.json"


def _fetch_nse_holidays(src: Dict[str, Any], year: int) -> Optional[List[Dict[str, str]]]:
    try:
        import requests
    except ImportError:
        return None
    headers = {"User-Agent": "Mozilla/5.0 (AARKAAI market calendar)", "Accept": "application/json",
               "Referer": src.get("warmup_url", "")}
    try:
        with requests.Session() as s:
            if src.get("warmup_url"):
                s.get(src["warmup_url"], headers=headers, timeout=8)
            r = s.get(src["url"], headers=headers, timeout=8)
            r.raise_for_status()
            payload = r.json()
    except Exception as exc:  # network/API failures are reported, not hidden
        logger.warning("Holiday fetch failed (%s): %s", src.get("url"), exc)
        return None
    rows = payload.get(src.get("segment", "CM"), []) if isinstance(payload, dict) else []
    out = []
    for row in rows:
        try:
            d = datetime.strptime(row["tradingDate"], "%d-%b-%Y").date()
        except (KeyError, ValueError):
            continue
        if d.year == year:
            out.append({"date": d.isoformat(), "name": row.get("description", ""), "day_of_week": d.strftime("%A")})
    return out or None


@lru_cache(maxsize=32)
def _load_holidays(exchange: str, year: int) -> Optional[tuple]:
    path = _cache_file(exchange, year)
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return tuple(tuple(sorted(h.items())) for h in data["holidays"])
        except Exception as exc:
            logger.warning("Invalid holiday cache %s: %s", path, exc)
    if os.environ.get("AARKA_OFFLINE") == "1":
        return None
    src = exchange_rules(exchange).get("holiday_source", {})
    fetched = _fetch_nse_holidays(src, year) if src.get("provider") == "nse_api" else None
    if not fetched:
        return None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"exchange": exchange.upper(), "year": year, "source": src.get("url"),
                                    "fetched_at": datetime.now(timezone.utc).isoformat(), "holidays": fetched},
                                   indent=2), encoding="utf-8")
    except OSError as exc:
        logger.warning("Could not write holiday cache: %s", exc)
    return tuple(tuple(sorted(h.items())) for h in fetched)


def holiday_calendar_status(year: int, exchange: str = "NSE") -> Dict[str, Any]:
    loaded = _load_holidays(exchange.upper(), int(year))
    src = exchange_rules(exchange).get("holiday_source", {})
    return {"exchange": exchange.upper(), "year": int(year), "verified": loaded is not None,
            "source": str(_cache_file(exchange, year)) if loaded is not None else src.get("url", "none configured")}


def get_trading_holidays(year: Optional[int] = None, exchange: str = "NSE") -> list:
    """Holidays for ``year`` (default: current exchange-local year). Empty list if unavailable."""
    yr = int(year) if year is not None else now(exchange).year
    loaded = _load_holidays(exchange.upper(), yr)
    return [dict(h) for h in loaded] if loaded else []


# ─────────────────────────────── sessions ─────────────────────────────────────

def market_session_info(exchange: str = "NSE") -> dict:
    r = exchange_rules(exchange)
    s = r["sessions"]
    return {"pre_market": s["pre_open_start"], "pre_open_order_end": s.get("pre_open_order_end"),
            "market_open": s["market_open"], "market_close": s["market_close"],
            "post_market": s["post_close_end"], "timezone": r["timezone"]}


def is_trading_day(check_date: Any = None, exchange: str = "NSE") -> bool:
    """Weekday and (when a verified calendar is available) holiday check."""
    exchange = exchange or "NSE"
    if check_date is None:
        check_date = now(exchange).date()
    elif isinstance(check_date, str):
        check_date = datetime.strptime(check_date, "%Y-%m-%d").date()
    if check_date.weekday() >= 5:
        return False
    holidays = {h["date"] for h in get_trading_holidays(check_date.year, exchange)}
    return check_date.isoformat() not in holidays


def is_market_open(exchange: str = "NSE") -> dict:
    try:
        info = market_session_info(exchange)
        n = now(exchange)
        cur = n.time()
        pre, op, cl, post = (_parse_hhmm(info[k]) for k in ("pre_market", "market_open", "market_close", "post_market"))
        td = is_trading_day(n.date(), exchange)
        session, is_open = "closed", False
        if td:
            if op <= cur < cl:
                session, is_open = "market", True
            elif pre <= cur < op:
                session = "pre_market"
            elif cl <= cur < post:
                session = "post_market"
        d = n.date() if (cur < op and td) else n.date() + timedelta(days=1)
        for _ in range(30):
            if is_trading_day(d, exchange):
                break
            d += timedelta(days=1)
        status = holiday_calendar_status(n.year, exchange)
        return {"is_open": is_open, "exchange": exchange.upper(), "current_time": n.isoformat(),
                "session": session, "next_open": f"{d.isoformat()} {info['market_open']}",
                "timezone": info["timezone"], "holiday_calendar_verified": status["verified"],
                "holiday_calendar_source": status["source"]}
    except Exception as e:
        logger.error("Error in is_market_open: %s", e)
        return {"is_open": None, "error": str(e)}


def _adjust_to_trading_day(d: date, exchange: str) -> date:
    for _ in range(10):
        if is_trading_day(d, exchange):
            return d
        d -= timedelta(days=1)
    return d


def next_expiry(expiry_type: str = "monthly", exchange: str = "NSE") -> dict:
    try:
        rules = exchange_rules(exchange).get("derivatives_expiry")
        if not rules:
            return {"error": f"No derivatives expiry rule configured for {exchange}"}
        wd = _WEEKDAYS[rules["weekday"]]
        today = now(exchange).date()

        def weekly_from(d: date) -> date:
            return d + timedelta(days=(wd - d.weekday()) % 7)

        def monthly_for(y: int, m: int) -> date:
            last = date(y, m, calendar.monthrange(y, m)[1])
            return last - timedelta(days=(last.weekday() - wd) % 7)

        if expiry_type == "weekly":
            exp = _adjust_to_trading_day(weekly_from(today), exchange)
            if exp < today:
                exp = _adjust_to_trading_day(weekly_from(today + timedelta(days=1)), exchange)
        elif expiry_type == "monthly":
            exp = _adjust_to_trading_day(monthly_for(today.year, today.month), exchange)
            if exp < today:
                y, m = (today.year + (today.month // 12), today.month % 12 + 1)
                exp = _adjust_to_trading_day(monthly_for(y, m), exchange)
        else:
            return {"error": "expiry_type must be 'weekly' or 'monthly'"}
        status = holiday_calendar_status(exp.year, exchange)
        return {"expiry_date": exp.isoformat(), "days_remaining": (exp - today).days, "expiry_type": expiry_type,
                "expiry_weekday_rule": rules["weekday"], "rule_source": rules.get("source"),
                "holiday_calendar_verified": status["verified"]}
    except Exception as e:
        logger.error("Error in next_expiry: %s", e)
        return {"error": str(e)}


def trading_days_between(start_date: date, end_date: date, exchange: str = "NSE") -> int:
    if start_date > end_date:
        return 0
    count, cur = 0, start_date
    while cur <= end_date:
        if is_trading_day(cur, exchange):
            count += 1
        cur += timedelta(days=1)
    return count


def time_to_expiry(expiry_date_str: str, exchange: str = "NSE") -> dict:
    try:
        rules = exchange_rules(exchange)
        tz = _tz(exchange)
        exp_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        exp_dt = tz.localize(datetime.combine(exp_date, _parse_hhmm(rules["sessions"]["market_close"])))
        n = now(exchange)
        diff = exp_dt - n
        if diff.total_seconds() <= 0:
            return {"days": 0, "hours": 0, "minutes": 0, "trading_days_remaining": 0,
                    "as_fraction_of_year": 0.0, "calendar_fraction_of_year": 0.0}
        tdays = trading_days_between(n.date(), exp_date, exchange)
        tdpy = float(rules["trading_days_per_year"])
        return {"days": diff.days, "hours": diff.seconds // 3600, "minutes": (diff.seconds % 3600) // 60,
                "trading_days_remaining": tdays, "as_fraction_of_year": tdays / tdpy,
                "calendar_fraction_of_year": diff.total_seconds() / (365.0 * 86400.0),
                "trading_days_per_year": tdpy}
    except Exception as e:
        logger.error("Error in time_to_expiry: %s", e)
        return {"error": str(e)}


def session_context_block(exchange: str = "NSE") -> str:
    """Human-readable exchange-local time context for agent prompts."""
    st = is_market_open(exchange)
    if "error" in st:
        return f"[Market Clock] unavailable: {st['error']}"
    return (f"[Market Clock — {st['exchange']}]\n- Exchange-local time: {st['current_time']} ({st['timezone']})\n"
            f"- Session: {st['session']} | Next open: {st['next_open']}\n"
            f"- Holiday calendar verified: {st['holiday_calendar_verified']} (source: {st['holiday_calendar_source']})")
