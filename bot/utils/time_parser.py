"""
Time parsing utilities for reminder system.
"""

import re
from datetime import datetime, timedelta
from typing import Union


class TimeParser:
    """Parse various time formats into datetime objects."""

    def __init__(self):
        # Regex patterns for different time formats
        self.time_patterns = {
            "simple": re.compile(r"^(\d+)([smhd])$", re.IGNORECASE),
            "combined": re.compile(
                r"^(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?$", re.IGNORECASE
            ),
            "relative": re.compile(r"^in\s+(.+)$", re.IGNORECASE),
        }

        self.unit_multipliers = {
            "s": 1,  # seconds
            "m": 60,  # minutes
            "h": 3600,  # hours
            "d": 86400,  # days
        }

        self.word_to_seconds = {
            "second": 1,
            "seconds": 1,
            "sec": 1,
            "secs": 1,
            "minute": 60,
            "minutes": 60,
            "min": 60,
            "mins": 60,
            "hour": 3600,
            "hours": 3600,
            "hr": 3600,
            "hrs": 3600,
            "day": 86400,
            "days": 86400,
            "week": 604800,
            "weeks": 604800,
            "month": 2592000,
            "months": 2592000,  # 30 days
            "year": 31536000,
            "years": 31536000,  # 365 days
        }

        self.special_times = {
            "tomorrow": lambda: datetime.now().replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            + timedelta(days=1),
            "next week": lambda: datetime.now().replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            + timedelta(weeks=1),
            "next month": lambda: datetime.now().replace(
                hour=9, minute=0, second=0, microsecond=0
            )
            + timedelta(days=30),
        }

    def parse_time(self, time_str: str) -> datetime:
        """
        Parse a time string and return a datetime object.

        Args:
            time_str: String representing time (e.g., "1h", "30m", "tomorrow")

        Returns:
            datetime object representing when the reminder should trigger

        Raises:
            ValueError: If the time string cannot be parsed
        """
        time_str = time_str.strip().lower()

        # Handle special times
        if time_str in self.special_times:
            return self.special_times[time_str]()

        # Handle "in X" format
        relative_match = self.time_patterns["relative"].match(time_str)
        if relative_match:
            inner_time = relative_match.group(1)
            try:
                seconds = self._parse_time_to_seconds(inner_time)
                return datetime.utcnow() + timedelta(seconds=seconds)
            except ValueError:
                pass

        # Try to parse as duration
        try:
            seconds = self._parse_time_to_seconds(time_str)
            return datetime.utcnow() + timedelta(seconds=seconds)
        except ValueError:
            pass

        raise ValueError(f"Could not parse time string: '{time_str}'")

    def _parse_time_to_seconds(self, time_str: str) -> int:
        """Parse a time string to total seconds."""
        # Try simple format (e.g., "1h", "30m")
        simple_match = self.time_patterns["simple"].match(time_str)
        if simple_match:
            value, unit = simple_match.groups()
            return int(value) * self.unit_multipliers[unit.lower()]

        # Try combined format (e.g., "1h30m", "2h30m15s")
        combined_match = self.time_patterns["combined"].match(time_str)
        if combined_match:
            hours, minutes, seconds = combined_match.groups()
            total_seconds = 0
            if hours:
                total_seconds += int(hours) * 3600
            if minutes:
                total_seconds += int(minutes) * 60
            if seconds:
                total_seconds += int(seconds)

            if total_seconds > 0:
                return total_seconds

        # Try word format (e.g., "5 minutes", "2 hours")
        return self._parse_word_format(time_str)

    def _parse_word_format(self, time_str: str) -> int:
        """Parse word-based time format."""
        # Pattern for "X unit" or "X units"
        word_pattern = re.compile(r"^(\d+)\s+(\w+)$")
        match = word_pattern.match(time_str)

        if match:
            value, unit = match.groups()
            unit = unit.lower()

            if unit in self.word_to_seconds:
                return int(value) * self.word_to_seconds[unit]

        # Try without number (e.g., "hour", "day")
        if time_str in self.word_to_seconds:
            return self.word_to_seconds[time_str]

        raise ValueError(f"Could not parse time format: '{time_str}'")
