"""Tests for src/utils/time_utils.py — settlement timing model.

Covers:
- Basic working-day addition (Mon→Wed, Fri→Tue, Thu→Mon)
- Weekend skipping
- Holiday skipping (Republic Day, Diwali, etc.)
- Cutoff-hour behaviour (after 6 PM → next working day)
- `is_settlement_late` edge cases
- `get_working_days_count` across month/year boundaries
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from src.utils.time_utils import (
    END_OF_DAY,
    INDIAN_HOLIDAYS,
    SETTLEMENT_CUTOFF_HOUR,
    _add_working_days,
    _next_working_day,
    calculate_settlement_expected_arrival,
    get_working_days_count,
    is_holiday,
    is_settlement_late,
    is_weekend,
    is_working_day,
)


# ── Fixtures ───────────────────────────────────────────────────────────────────


@pytest.fixture
def monday_10am() -> datetime:
    """Monday 10:00 AM."""
    return datetime(2025, 1, 6, 10, 0)  # Mon


@pytest.fixture
def friday_10am() -> datetime:
    """Friday 10:00 AM."""
    return datetime(2025, 1, 10, 10, 0)  # Fri


@pytest.fixture
def thursday_10am() -> datetime:
    """Thursday 10:00 AM."""
    return datetime(2025, 1, 9, 10, 0)  # Thu


@pytest.fixture
def friday_7pm() -> datetime:
    """Friday 7:00 PM — after cutoff."""
    return datetime(2025, 1, 10, 19, 0)  # Fri 19:00


@pytest.fixture
def christmas_day() -> datetime:
    """December 25 — Indian bank holiday."""
    return datetime(2025, 12, 25, 10, 0)


@pytest.fixture
def republic_day() -> datetime:
    """January 26 — Indian bank holiday."""
    return datetime(2025, 1, 26, 10, 0)


# ── is_weekend ─────────────────────────────────────────────────────────────────


class TestIsWeekend:
    @pytest.mark.parametrize(
        "d,expected",
        [
            (date(2025, 1, 6), False),   # Mon
            (date(2025, 1, 7), False),   # Tue
            (date(2025, 1, 8), False),   # Wed
            (date(2025, 1, 9), False),   # Thu
            (date(2025, 1, 10), False),  # Fri
            (date(2025, 1, 11), True),   # Sat
            (date(2025, 1, 12), True),   # Sun
        ],
    )
    def test_weekend_detection(self, d, expected):
        assert is_weekend(d) == expected


# ── is_holiday ─────────────────────────────────────────────────────────────────


class TestIsHoliday:
    def test_republic_day(self):
        assert is_holiday(date(2025, 1, 26)) is True

    def test_independence_day(self):
        assert is_holiday(date(2025, 8, 15)) is True

    def test_diwali_2025(self):
        assert is_holiday(date(2025, 10, 20)) is True

    def test_christmas(self):
        assert is_holiday(date(2025, 12, 25)) is True

    def test_normal_day(self):
        assert is_holiday(date(2025, 6, 18)) is False  # arbitrary Wednesday

    def test_2024_holidays_present(self):
        assert is_holiday(date(2024, 3, 25)) is True   # Holi 2024

    def test_2026_holidays_present(self):
        assert is_holiday(date(2026, 4, 14)) is True   # Ambedkar Jayanti


# ── is_working_day ─────────────────────────────────────────────────────────────


class TestIsWorkingDay:
    def test_monday_is_working(self):
        assert is_working_day(date(2025, 1, 6)) is True

    def test_saturday_not_working(self):
        assert is_working_day(date(2025, 1, 11)) is False

    def test_sunday_not_working(self):
        assert is_working_day(date(2025, 1, 12)) is False

    def test_republic_day_not_working(self):
        assert is_working_day(date(2025, 1, 26)) is False

    def test_26_jan_2024(self):
        # Republic Day 2024 falls on Friday — still a holiday
        d = date(2024, 1, 26)
        assert is_holiday(d) is True
        assert is_working_day(d) is False


# ── _next_working_day ──────────────────────────────────────────────────────────


class TestNextWorkingDay:
    def test_monday_returns_self(self):
        assert _next_working_day(date(2025, 1, 6)) == date(2025, 1, 6)

    def test_saturday_skips_to_monday(self):
        assert _next_working_day(date(2025, 1, 11)) == date(2025, 1, 13)

    def test_sunday_skips_to_monday(self):
        assert _next_working_day(date(2025, 1, 12)) == date(2025, 1, 13)

    def test_republic_day_friday_skips_to_monday(self):
        # 26 Jan 2025 is a Sunday → already not a working day
        # Let's test with a weekday that's a holiday:
        # 25 Dec 2025 is a Thursday (Christmas)
        assert _next_working_day(date(2025, 12, 25)) == date(2025, 12, 26)

    def test_friday_after_cutoff_skips_weekend(self):
        # Friday + cutoff → start from Monday
        d = date(2025, 1, 10)  # Fri
        result = _next_working_day(d + timedelta(days=1))
        assert result == date(2025, 1, 13)  # Mon


# ── _add_working_days ──────────────────────────────────────────────────────────


class TestAddWorkingDays:
    def test_monday_plus_2(self):
        result = _add_working_days(date(2025, 1, 6), 2)
        assert result == date(2025, 1, 8)  # Wed

    def test_friday_plus_2(self):
        result = _add_working_days(date(2025, 1, 10), 2)
        assert result == date(2025, 1, 14)  # Tue (skip weekend)

    def test_thursday_plus_2(self):
        result = _add_working_days(date(2025, 1, 9), 2)
        assert result == date(2025, 1, 13)  # Mon (skip weekend)

    def test_zero_days(self):
        result = _add_working_days(date(2025, 1, 6), 0)
        assert result == date(2025, 1, 6)  # Mon (same day)

    def test_one_week(self):
        result = _add_working_days(date(2025, 1, 6), 5)
        assert result == date(2025, 1, 13)  # Mon (next week)

    def test_across_holiday(self):
        # Mon 20 Jan → +4 working days → Tue 21, Wed 22, Thu 23, Fri 24
        result = _add_working_days(date(2025, 1, 20), 4)
        assert result == date(2025, 1, 24)  # Fri (all 4 days are in the same working week)

    def test_across_christmas(self):
        # Wed 24 Dec 2025 → +2 working days
        # Day 1: Thu 25 (Christmas, skip) → Fri 26
        # Day 2: Sat 27 (weekend, skip) → Mon 29
        result = _add_working_days(date(2025, 12, 24), 2)
        assert result == date(2025, 12, 29)  # Mon

    def test_new_year_2025(self):
        # Wed 1 Jan (New Year's Day is a holiday)
        # _next_working_day(1 Jan) → Thu 2 Jan
        # +2 → Mon 6 Jan
        result = _add_working_days(date(2025, 1, 1), 2)
        assert result == date(2025, 1, 6)  # Mon


# ── get_working_days_count ─────────────────────────────────────────────────────


class TestGetWorkingDaysCount:
    def test_same_week(self):
        # Mon to Fri: 4 working days (Mon exclusive, Fri inclusive)
        count = get_working_days_count(date(2025, 1, 6), date(2025, 1, 10))
        assert count == 4

    def test_across_weekend(self):
        # Fri to Wed: 2 working days (Mon, Tue, Wed) → actually:
        # start=Fri, end=Wed → Sat/skip, Sun/skip, Mon, Tue, Wed → 3
        count = get_working_days_count(date(2025, 1, 10), date(2025, 1, 15))
        assert count == 3

    def test_same_date(self):
        count = get_working_days_count(date(2025, 1, 6), date(2025, 1, 6))
        assert count == 0

    def test_reversed_dates(self):
        count = get_working_days_count(date(2025, 1, 10), date(2025, 1, 6))
        assert count == 0

    def test_two_weeks(self):
        # Mon to Mon (next week): 5 working days
        count = get_working_days_count(date(2025, 1, 6), date(2025, 1, 13))
        assert count == 5

    def test_month_boundary(self):
        # 30 Jan (Thu) to 3 Feb (Mon): Fri, Mon → 2 working days
        count = get_working_days_count(date(2025, 1, 30), date(2025, 2, 3))
        assert count == 2


# ── calculate_settlement_expected_arrival ──────────────────────────────────────


class TestCalculateSettlementExpectedArrival:
    def test_monday_10am(self, monday_10am):
        result = calculate_settlement_expected_arrival(monday_10am)
        assert result == datetime(2025, 1, 8, 23, 59, 59)  # Wed

    def test_friday_10am(self, friday_10am):
        result = calculate_settlement_expected_arrival(friday_10am)
        assert result == datetime(2025, 1, 14, 23, 59, 59)  # Tue (skip weekend)

    def test_thursday_10am(self, thursday_10am):
        result = calculate_settlement_expected_arrival(thursday_10am)
        assert result == datetime(2025, 1, 13, 23, 59, 59)  # Mon (skip weekend)

    def test_friday_after_cutoff(self, friday_7pm):
        """After 6 PM Friday → start from Monday → +2 → Wednesday."""
        result = calculate_settlement_expected_arrival(friday_7pm)
        # _next_working_day(Sat 11 Jan) → Mon 13 Jan
        # +2 working days → Wed 15 Jan
        assert result == datetime(2025, 1, 15, 23, 59, 59)

    def test_christmas_day(self, christmas_day):
        """25 Dec 2025 (Thu, Christmas) → next working day is Fri 26 Dec → +2 = Tue 30 Dec."""
        result = calculate_settlement_expected_arrival(christmas_day)
        assert result == datetime(2025, 12, 30, 23, 59, 59)

    def test_end_of_day_time(self, monday_10am):
        result = calculate_settlement_expected_arrival(monday_10am)
        assert result.time() == END_OF_DAY

    def test_before_cutoff_starts_same_day(self):
        """Settlement at 5:59 PM (before cutoff) should start counting from the same day."""
        dt = datetime(2025, 1, 10, 17, 59)  # Fri 17:59
        result = calculate_settlement_expected_arrival(dt)
        # Before cutoff → start = Fri 10 Jan (same day, working)
        # Day 1: Sat 11 → Mon 13 | Day 2: Tue 14
        assert result.date() == date(2025, 1, 14)  # Tue

    def test_at_cutoff_exactly(self):
        """Exactly 6 PM should be treated as after-cutoff (>=)."""
        dt = datetime(2025, 1, 10, 18, 0)  # Fri 18:00
        result = calculate_settlement_expected_arrival(dt)
        # After cutoff → start from Mon 13 → +2 → Wed 15
        assert result.date() == date(2025, 1, 15)


# ── is_settlement_late ─────────────────────────────────────────────────────────


class TestIsSettlementLate:
    def test_not_late_before_deadline(self, monday_10am):
        expected_arrival = calculate_settlement_expected_arrival(monday_10am)
        # Check 1 day before deadline
        current = expected_arrival - timedelta(days=1)
        is_late, delta = is_settlement_late(monday_10am, current, "pending")
        assert is_late is False
        assert delta.total_seconds() > 0

    def test_late_after_deadline(self, monday_10am):
        expected_arrival = calculate_settlement_expected_arrival(monday_10am)
        current = expected_arrival + timedelta(hours=1)
        is_late, delta = is_settlement_late(monday_10am, current, "pending")
        assert is_late is True
        assert delta.total_seconds() > 0

    def test_success_not_late(self, monday_10am):
        expected_arrival = calculate_settlement_expected_arrival(monday_10am)
        current = expected_arrival + timedelta(days=1)
        is_late, delta = is_settlement_late(monday_10am, current, "success")
        assert is_late is False
        assert delta == timedelta(0)

    def test_partial_status_can_be_late(self, monday_10am):
        expected_arrival = calculate_settlement_expected_arrival(monday_10am)
        current = expected_arrival + timedelta(days=2)
        is_late, delta = is_settlement_late(monday_10am, current, "partial")
        assert is_late is True

    def test_failed_can_be_late(self, monday_10am):
        expected_arrival = calculate_settlement_expected_arrival(monday_10am)
        current = expected_arrival + timedelta(days=5)
        is_late, delta = is_settlement_late(monday_10am, current, "failed")
        assert is_late is True
        assert delta.days >= 4

    def test_exact_deadline_not_late(self, monday_10am):
        """Exactly at the deadline → not late (uses >)."""
        expected_arrival = calculate_settlement_expected_arrival(monday_10am)
        is_late, _ = is_settlement_late(monday_10am, expected_arrival, "pending")
        assert is_late is False


# ── Holiday edge cases ─────────────────────────────────────────────────────────


class TestHolidayEdgeCases:
    def test_multi_day_holiday_streak(self):
        """Diwali 2025: 20 Oct (Mon) and 21 Oct (Tue) both holidays."""
        assert is_holiday(date(2025, 10, 20)) is True
        assert is_holiday(date(2025, 10, 21)) is True

        # Start from Fri 17 Oct → +2 working days
        result = _add_working_days(date(2025, 10, 17), 2)
        # Day 1: skip Sat/Sun, Mon(holiday), Tue(holiday) → Wed 22 Oct
        # Day 2: Thu 23 Oct
        assert result == date(2025, 10, 23)  # Thu

    def test_new_years_day(self):
        """1 Jan 2025 is a holiday (New Year's Day)."""
        assert is_holiday(date(2025, 1, 1)) is True

    def test_saturday_holiday_still_weekend(self):
        """If a Saturday is also a holiday, it's still not a working day."""
        # Even if we added a Saturday holiday, is_weekend catches it first
        assert is_working_day(date(2025, 1, 11)) is False  # Saturday
