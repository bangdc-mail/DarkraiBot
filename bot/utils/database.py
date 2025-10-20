"""
Database management for the Discord bot.
"""

import aiosqlite
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


class Database:
    """Database manager for the bot."""

    def __init__(self, db_path: str = "/app/data/bot.db"):
        self.db_path = db_path
        self._connection = None

    async def initialize(self):
        """Initialize the database and create tables."""
        # Ensure data directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._connection = await aiosqlite.connect(self.db_path)
        await self._create_tables()
        logger.info("Database initialized successfully")

    async def _create_tables(self):
        """Create necessary tables."""
        # Reminders table
        await self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER,
                channel_id INTEGER NOT NULL,
                message TEXT NOT NULL,
                remind_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                completed BOOLEAN DEFAULT FALSE
            )
        """
        )

        # User settings table
        await self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS user_settings (
                user_id INTEGER PRIMARY KEY,
                timezone TEXT DEFAULT 'UTC',
                reminder_enabled BOOLEAN DEFAULT TRUE,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Bot activity log
        await self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                guild_id INTEGER,
                command TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                success BOOLEAN DEFAULT TRUE,
                error_message TEXT
            )
        """
        )

        # Guild settings table
        await self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                command_prefix TEXT DEFAULT '!',
                admin_roles TEXT DEFAULT 'admin,administrator',
                mod_roles TEXT DEFAULT 'moderator,mod',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        await self._connection.commit()

    async def close(self):
        """Close the database connection."""
        if self._connection:
            await self._connection.close()

    # Reminder methods
    async def add_reminder(
        self,
        user_id: int,
        guild_id: Optional[int],
        channel_id: int,
        message: str,
        remind_at: datetime,
    ) -> int:
        """Add a new reminder."""
        cursor = await self._connection.execute(
            """
            INSERT INTO reminders (user_id, guild_id, channel_id, message, remind_at)
            VALUES (?, ?, ?, ?, ?)
        """,
            (user_id, guild_id, channel_id, message, remind_at),
        )
        await self._connection.commit()
        return cursor.lastrowid

    async def get_pending_reminders(self) -> List[Dict[str, Any]]:
        """Get all pending reminders that should be sent."""
        cursor = await self._connection.execute(
            """
            SELECT id, user_id, guild_id, channel_id, message, remind_at
            FROM reminders
            WHERE completed = FALSE AND remind_at <= ?
        """,
            (datetime.utcnow(),),
        )

        rows = await cursor.fetchall()
        return [
            {
                "id": row[0],
                "user_id": row[1],
                "guild_id": row[2],
                "channel_id": row[3],
                "message": row[4],
                "remind_at": row[5],
            }
            for row in rows
        ]

    async def mark_reminder_completed(self, reminder_id: int):
        """Mark a reminder as completed."""
        await self._connection.execute(
            """
            UPDATE reminders SET completed = TRUE WHERE id = ?
        """,
            (reminder_id,),
        )
        await self._connection.commit()

    async def get_user_reminders(
        self, user_id: int, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get reminders for a specific user."""
        cursor = await self._connection.execute(
            """
            SELECT id, message, remind_at, completed
            FROM reminders
            WHERE user_id = ?
            ORDER BY remind_at DESC
            LIMIT ?
        """,
            (user_id, limit),
        )

        rows = await cursor.fetchall()
        return [
            {
                "id": row[0],
                "message": row[1],
                "remind_at": row[2],
                "completed": bool(row[3]),
            }
            for row in rows
        ]

    async def delete_reminder(self, reminder_id: int, user_id: int) -> bool:
        """Delete a reminder if it belongs to the user."""
        cursor = await self._connection.execute(
            """
            DELETE FROM reminders
            WHERE id = ? AND user_id = ?
        """,
            (reminder_id, user_id),
        )
        await self._connection.commit()
        return cursor.rowcount > 0

    # Activity logging
    async def log_command(
        self,
        user_id: int,
        guild_id: Optional[int],
        command: str,
        success: bool = True,
        error_message: Optional[str] = None,
    ):
        """Log command usage."""
        await self._connection.execute(
            """
            INSERT INTO activity_log (user_id, guild_id, command, success, error_message)
            VALUES (?, ?, ?, ?, ?)
        """,
            (user_id, guild_id, command, success, error_message),
        )
        await self._connection.commit()

    # User settings
    async def get_user_settings(self, user_id: int) -> Dict[str, Any]:
        """Get user settings."""
        cursor = await self._connection.execute(
            """
            SELECT timezone, reminder_enabled
            FROM user_settings
            WHERE user_id = ?
        """,
            (user_id,),
        )

        row = await cursor.fetchone()
        if row:
            return {"timezone": row[0], "reminder_enabled": bool(row[1])}
        else:
            # Return defaults
            return {"timezone": "UTC", "reminder_enabled": True}

    async def update_user_settings(self, user_id: int, **settings):
        """Update user settings."""
        # Insert or update user settings
        await self._connection.execute(
            """
            INSERT INTO user_settings (user_id, timezone, reminder_enabled, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                timezone = COALESCE(excluded.timezone, timezone),
                reminder_enabled = COALESCE(excluded.reminder_enabled, reminder_enabled),
                updated_at = excluded.updated_at
        """,
            (
                user_id,
                settings.get("timezone"),
                settings.get("reminder_enabled"),
                datetime.utcnow(),
            ),
        )
        await self._connection.commit()

    # Guild settings methods
    async def get_guild_settings(self, guild_id: int) -> Dict[str, Any]:
        """Get guild settings."""
        cursor = await self._connection.execute(
            """
            SELECT command_prefix, admin_roles, mod_roles
            FROM guild_settings
            WHERE guild_id = ?
        """,
            (guild_id,),
        )

        row = await cursor.fetchone()
        if row:
            return {
                "command_prefix": row[0],
                "admin_roles": row[1].split(",") if row[1] else [],
                "mod_roles": row[2].split(",") if row[2] else [],
            }
        else:
            # Return defaults from config
            from .config import Config

            return {
                "command_prefix": Config.COMMAND_PREFIX,
                "admin_roles": Config.ADMIN_ROLE_NAMES,
                "mod_roles": Config.MOD_ROLE_NAMES,
            }

    async def update_guild_settings(self, guild_id: int, **settings):
        """Update guild settings."""
        # Convert lists to comma-separated strings
        admin_roles = settings.get("admin_roles")
        if isinstance(admin_roles, list):
            admin_roles = ",".join(admin_roles)

        mod_roles = settings.get("mod_roles")
        if isinstance(mod_roles, list):
            mod_roles = ",".join(mod_roles)

        # Insert or update guild settings
        await self._connection.execute(
            """
            INSERT INTO guild_settings (guild_id, command_prefix, admin_roles, mod_roles, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(guild_id) DO UPDATE SET
                command_prefix = COALESCE(excluded.command_prefix, command_prefix),
                admin_roles = COALESCE(excluded.admin_roles, admin_roles),
                mod_roles = COALESCE(excluded.mod_roles, mod_roles),
                updated_at = excluded.updated_at
        """,
            (
                guild_id,
                settings.get("command_prefix"),
                admin_roles,
                mod_roles,
                datetime.utcnow(),
            ),
        )
        await self._connection.commit()
