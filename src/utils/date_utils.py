"""
Date and time utilities for the Daily arXiv Paper Collection System.
Handles Beijing timezone conversions and date calculations.
"""
from datetime import datetime, timedelta
from typing import Tuple
import pytz


def get_beijing_timezone():
    """Get Beijing timezone object."""
    return pytz.timezone('Asia/Shanghai')


def get_current_beijing_time() -> datetime:
    """Get current time in Beijing timezone."""
    beijing_tz = get_beijing_timezone()
    return datetime.now(beijing_tz)


def get_previous_day_beijing(target_date: datetime | None = None) -> str:
    """
    Get the previous day's date in Beijing timezone.

    Args:
        target_date: Target date (defaults to current time)

    Returns:
        Date string in YYYY-MM-DD format
    """
    if target_date is None:
        target_date = get_current_beijing_time()

    previous_day = target_date - timedelta(days=1)
    return previous_day.strftime("%Y-%m-%d")


def is_last_day_of_month(target_date: datetime | None = None) -> bool:
    """
    Check if the given date is the last day of the month in Beijing timezone.

    Args:
        target_date: Target date (defaults to current time)

    Returns:
        True if the date is the last day of the month
    """
    if target_date is None:
        target_date = get_current_beijing_time()

    # Get next day
    next_day = target_date + timedelta(days=1)

    # If next day is in a different month, today is the last day
    return target_date.month != next_day.month


def get_week_start_end(target_date: datetime | None = None) -> Tuple[str, str]:
    """
    Get the start and end dates of the week containing the target date.
    Week starts on Monday and ends on Sunday.

    Args:
        target_date: Target date (defaults to current time)

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    if target_date is None:
        target_date = get_current_beijing_time()

    # Get weekday (Monday=0, Sunday=6)
    weekday = target_date.weekday()

    # Calculate start of week (Monday)
    week_start = target_date - timedelta(days=weekday)

    # Calculate end of week (Sunday)
    week_end = week_start + timedelta(days=6)

    return (
        week_start.strftime("%Y-%m-%d"),
        week_end.strftime("%Y-%m-%d")
    )


def get_month_start_end(target_date: datetime | None = None) -> Tuple[str, str]:
    """
    Get the start and end dates of the month containing the target date.

    Args:
        target_date: Target date (defaults to current time)

    Returns:
        Tuple of (start_date, end_date) in YYYY-MM-DD format
    """
    if target_date is None:
        target_date = get_current_beijing_time()

    # First day of month
    month_start = target_date.replace(day=1)

    # Last day of month
    # Get first day of next month, then subtract one day
    if target_date.month == 12:
        next_month = target_date.replace(year=target_date.year + 1, month=1, day=1)
    else:
        next_month = target_date.replace(month=target_date.month + 1, day=1)

    month_end = next_month - timedelta(days=1)

    return (
        month_start.strftime("%Y-%m-%d"),
        month_end.strftime("%Y-%m-%d")
    )


def parse_date_string(date_str: str) -> datetime:
    """
    Parse a date string in YYYY-MM-DD format to Beijing timezone datetime.

    Args:
        date_str: Date string in YYYY-MM-DD format

    Returns:
        datetime object in Beijing timezone
    """
    beijing_tz = get_beijing_timezone()
    naive_date = datetime.strptime(date_str, "%Y-%m-%d")
    return beijing_tz.localize(naive_date)
