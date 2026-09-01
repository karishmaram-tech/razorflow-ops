"""Settlement timing model — working-day calculations for Indian markets.

All public functions are timezone-naive and operate in IST (UTC+5:30).
Import ``IST`` if you need the timezone object.

Usage::

    from src.utils.time_utils import (
        calculate_settlement_expected_arrival,
        is_settlement_late,
        get_working_days_count,
        is_working_day,
        IST,
    )
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Tuple

logger = logging.getLogger(__name__)

# ── Timezone ───────────────────────────────────────────────────────────────────

IST = timezone(timedelta(hours=5, minutes=30))

# ── Constants ──────────────────────────────────────────────────────────────────

SETTLEMENT_WORKING_DAYS = 2  # T+2 for settlements
SETTLEMENT_CUTOFF_HOUR = 18  # 6 PM IST — settlements created after this count as next business day
from datetime import time as _time

END_OF_DAY = _time(23, 59, 59)


# ── Indian Bank Holidays (2024-2026) ──────────────────────────────────────────
# Source: RBI holiday calendar + commonly observed bank holidays.
# Format: set of ``(month, day)`` tuples so we can check across years.

INDIAN_HOLIDAYS: set[tuple[int, int]] = {
    # ── Fixed-date holidays (every year) ────────────────────────────
    (1, 1),    # New Year's Day
    (1, 26),   # Republic Day
    (8, 15),   # Independence Day
    (10, 2),   # Gandhi Jayanti
    (12, 25),  # Christmas

    # ── 2024 lunar / variable holidays ──────────────────────────────
    (1, 17),   # Guru Gobind Singh Jayanti
    (3, 8),    # Maha Shivaratri
    (3, 25),   # Holi
    (4, 11),   # Eid al-Fitr (Ramadan)
    (4, 14),   # Dr. Ambedkar Jayanti
    (4, 17),   # Ram Navami
    (5, 23),   # Buddha Purnima
    (6, 17),   # Eid al-Adha (Bakrid)
    (7, 17),   # Muharram
    (8, 19),   # Janmashtami
    (10, 12),  # Dussehra
    (10, 31),  # Diwali
    (11, 1),   # Diwali (Day 2 / Govardhan Puja)
    (11, 15),  # Guru Nanak Jayanti

    # ── 2025 lunar / variable holidays ──────────────────────────────
    (2, 26),   # Maha Shivaratri
    (3, 14),   # Holi
    (3, 31),   # Eid al-Fitr
    (4, 6),    # Ram Navami
    (4, 14),   # Dr. Ambedkar Jayanti
    (5, 12),   # Buddha Purnima
    (6, 7),    # Eid al-Adha
    (7, 6),    # Muharram
    (8, 16),   # Janmashtami
    (10, 2),   # Gandhi Jayanti
    (10, 21),  # Dussehra
    (10, 20),  # Diwali
    (10, 21),  # Diwali (Day 2)
    (11, 5),   # Guru Nanak Jayanti

    # ── 2026 approximate / declared dates (may shift) ───────────────
    (2, 15),   # Maha Shivaratri (approx)
    (3, 4),    # Holi (approx)
    (3, 20),   # Eid al-Fitr (approx)
    (3, 26),   # Ram Navami (approx)
    (4, 14),   # Dr. Ambedkar Jayanti
    (5, 1),    # Buddha Purnima (approx)
    (5, 27),   # Eid al-Adha (approx)
    (6, 26),   # Muharram (approx)
    (8, 5),    # Janmashtami (approx)
    (10, 2),   # Gandhi Jayanti
    (10, 11),  # Dussehra (approx)
    (11, 8),   # Diwali (approx)
    (11, 9),   # Diwali (Day 2)
    (11, 24),  # Guru Nanak Jayanti (approx)
}


# ── Core helpers ───────────────────────────────────────────────────────────────


def is_weekend(d: date) -> bool:
    """Return True if *d* is Saturday (5) or Sunday (6)."""
    return d.weekday() >= 5


def is_holiday(d: date) -> bool:
    """Return True if *d* is an Indian bank holiday."""
    return (d.month, d.day) in INDIAN_HOLIDAYS


def is_working_day(d: date) -> bool:
    """Return True if *d* is Mon-Fri **and** not an Indian bank holiday."""
    return not is_weekend(d) and not is_holiday(d)


def _next_working_day(d: date) -> date:
    """Return the next working day on or after *d*."""
    while not is_working_day(d):
        d += timedelta(days=1)
    return d


def _add_working_days(start: date, n: int) -> date:
    """Return *start* + *n* working days (skipping weekends and holidays)."""
    current = _next_working_day(start)
    for _ in range(n):
        current = _next_working_day(current + timedelta(days=1))
    return current


def get_working_days_count(start_date: date, end_date: date) -> int:
    """Count working days between *start_date* (exclusive) and *end_date* (inclusive).

    Example: Monday to Thursday (same week) → 3 working days.
    """
    if start_date >= end_date:
        return 0
    count = 0
    current = start_date + timedelta(days=1)
    while current <= end_date:
        if is_working_day(current):
            count += 1
        current += timedelta(days=1)
    return count


# ── Settlement timing ──────────────────────────────────────────────────────────


def _normalise_settlement_start(created_at: datetime) -> date:
    """If a settlement is created after the cutoff hour, start counting from
    the next working day (similar to how banks treat T+2).

    Cutoff: 6 PM IST.
    """
    if created_at.hour >= SETTLEMENT_CUTOFF_HOUR:
        return _next_working_day(created_at.date() + timedelta(days=1))
    return _next_working_day(created_at.date())


def calculate_settlement_expected_arrival(created_at: datetime) -> datetime:
    """Compute the expected settlement arrival datetime (T+2 working days).

    Rules:
    - Weekends and Indian bank holidays are excluded.
    - Settlements created after 6 PM IST start counting from the next
      working day.
    - The result is set to 23:59:59 on the expected arrival date.

    Parameters
    ----------
    created_at : datetime
        When the settlement was created (naive IST or UTC).

    Returns
    -------
    datetime
        Expected arrival datetime with time set to 23:59:59.
    """
    logger.debug("Calculating settlement T+2 for created_at=%s", created_at)
    start_date = _normalise_settlement_start(created_at)
    arrival_date = _add_working_days(start_date, SETTLEMENT_WORKING_DAYS)
    result = datetime.combine(arrival_date, END_OF_DAY)
    logger.debug(
        "Settlement expected arrival: %s (start=%s, +%d working days)",
        result, start_date, SETTLEMENT_WORKING_DAYS,
    )
    return result


def is_settlement_late(
    created_at: datetime,
    current_time: datetime,
    settlement_status: str,
) -> Tuple[bool, timedelta]:
    """Determine whether a settlement is past its expected arrival.

    Parameters
    ----------
    created_at : datetime
        Settlement creation timestamp.
    current_time : datetime
        Current or evaluation timestamp.
    settlement_status : str
        Current settlement status (e.g. ``"success"``).

    Returns
    -------
    tuple[bool, timedelta]
        ``(is_late, delta)`` where:
        - If **late**: ``delta`` is the positive time overdue.
        - If **not late**: ``delta`` is the positive time remaining.
        - If **on time but already succeeded**: ``delta`` is zero.
    """
    expected = calculate_settlement_expected_arrival(created_at)

    if settlement_status == "success":
        logger.debug("Settlement already succeeded — not late.")
        return False, timedelta(0)

    if current_time > expected:
        delta = current_time - expected
        logger.info(
            "Settlement LATE by %s (expected %s, now %s)",
            delta, expected, current_time,
        )
        return True, delta

    delta = expected - current_time
    logger.debug("Settlement not yet due — %s remaining.", delta)
    return False, delta


# ── Formatting helpers ────────────────────────────────────────────────────────


def format_time_for_merchant(seconds: int) -> str:
    """Convert a time delta in seconds to a merchant-friendly string.

    Examples::

        >>> format_time_for_merchant(3600)
        '1 hour'
        >>> format_time_for_merchant(90000)
        '1 day 1 hour'
        >>> format_time_for_merchant(259200)
        '3 days'
        >>> format_time_for_merchant(0)
        '0 minutes'

    Parameters
    ----------
    seconds : int
        Time duration in seconds.

    Returns
    -------
    str
        Human-readable duration string.
    """
    if seconds < 0:
        seconds = abs(seconds)
    if seconds == 0:
        return "0 minutes"

    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60

    parts: list[str] = []
    if days > 0:
        parts.append(f"{days} day{'s' if days != 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
    if minutes > 0 and days == 0:  # only show minutes if < 1 day
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")

    return " ".join(parts) if parts else "0 minutes"
