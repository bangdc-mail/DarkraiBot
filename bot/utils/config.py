"""
Configuration management for the Discord bot.
"""

import os
from typing import List


class Config:
    """Configuration class that loads settings from environment variables."""

    # Bot configuration
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
    OWNER_ID = int(os.getenv("OWNER_ID", 0))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///data/bot.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

    # Admin role configuration
    ADMIN_ROLE_NAMES = [
        name.strip()
        for name in os.getenv("ADMIN_ROLE_NAMES", "admin,moderator,mod").split(",")
    ]

    # Feature toggles
    ENABLE_REMINDERS = os.getenv("ENABLE_REMINDERS", "true").lower() == "true"
    ENABLE_IP_CHECK = os.getenv("ENABLE_IP_CHECK", "true").lower() == "true"

    @classmethod
    def validate(cls) -> List[str]:
        """Validate configuration and return list of errors."""
        errors = []

        if not cls.BOT_TOKEN:
            errors.append("BOT_TOKEN environment variable is required")

        if not cls.OWNER_ID:
            errors.append("OWNER_ID environment variable is required")

        return errors

    @classmethod
    def is_valid(cls) -> bool:
        """Check if configuration is valid."""
        return len(cls.validate()) == 0
