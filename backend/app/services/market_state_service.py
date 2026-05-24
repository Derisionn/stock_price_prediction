"""
Market State Service
Checks if US stock market is currently open.
"""
from __future__ import annotations

from datetime import datetime, time, date
import pytz

# US Eastern timezone
ET = pytz.timezone("America/New_York")

# NYSE market hours (Eastern Time)
MARKET_OPEN = time(9, 30, 0)
MARKET_CLOSE = time(16, 0, 0)

# Known US market holidays for 2024-2026 (NYSE)
MARKET_HOLIDAYS = {
    # 2024
    date(2024, 1, 1),   # New Year's Day
    date(2024, 1, 15),  # MLK Day
    date(2024, 2, 19),  # Presidents' Day
    date(2024, 3, 29),  # Good Friday
    date(2024, 5, 27),  # Memorial Day
    date(2024, 6, 19),  # Juneteenth
    date(2024, 7, 4),   # Independence Day
    date(2024, 9, 2),   # Labor Day
    date(2024, 11, 28), # Thanksgiving
    date(2024, 12, 25), # Christmas
    # 2025
    date(2025, 1, 1),
    date(2025, 1, 20),
    date(2025, 2, 17),
    date(2025, 4, 18),
    date(2025, 5, 26),
    date(2025, 6, 19),
    date(2025, 7, 4),
    date(2025, 9, 1),
    date(2025, 11, 27),
    date(2025, 12, 25),
    # 2026
    date(2026, 1, 1),
    date(2026, 1, 19),
    date(2026, 2, 16),
    date(2026, 4, 3),
    date(2026, 5, 25),
    date(2026, 6, 19),
    date(2026, 7, 3),
    date(2026, 9, 7),
    date(2026, 11, 26),
    date(2026, 12, 25),
}


def get_market_state() -> dict:
    """
    Returns whether the US stock market is currently open.
    Returns:
        {
            "is_open": bool,
            "current_time_et": str,
            "message": str
        }
    """
    now_et = datetime.now(ET)
    today = now_et.date()
    current_time = now_et.time()
    weekday = now_et.weekday()  # 0=Monday, 6=Sunday

    is_weekend = weekday >= 5
    is_holiday = today in MARKET_HOLIDAYS
    is_trading_hours = MARKET_OPEN <= current_time < MARKET_CLOSE

    is_open = not is_weekend and not is_holiday and is_trading_hours

    if is_open:
        message = "Market Open"
    elif is_weekend:
        message = "Market Closed (Weekend)"
    elif is_holiday:
        message = "Market Closed (Holiday)"
    elif current_time < MARKET_OPEN:
        message = f"Market Opens at {MARKET_OPEN.strftime('%I:%M %p')} ET"
    else:
        message = "Market Closed (After Hours)"

    return {
        "is_open": is_open,
        "current_time_et": now_et.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "message": message,
    }
