"""
Permission management system for role-based command access.
"""

import functools
from typing import Union, List
from enum import Enum

import discord
from discord.ext import commands

from .config import Config


class PermissionLevel(Enum):
    """Permission levels for commands."""

    USER = 1
    ADMIN = 2
    OWNER = 3


class PermissionManager:
    """Manages user permissions and role-based access control."""

    def __init__(self, bot):
        self.bot = bot

    def get_user_permission_level(
        self, user: Union[discord.Member, discord.User], guild: discord.Guild = None
    ) -> PermissionLevel:
        """Get the permission level for a user."""
        # Owner check
        if user.id == Config.OWNER_ID:
            return PermissionLevel.OWNER

        # If not in a guild, can only be owner or user
        if not guild or not isinstance(user, discord.Member):
            return PermissionLevel.USER

        # Admin check - check for admin permissions or specific roles
        if user.guild_permissions.administrator:
            return PermissionLevel.ADMIN

        # Check for admin role names
        user_role_names = [role.name.lower() for role in user.roles]
        admin_role_names = [name.lower() for name in Config.ADMIN_ROLE_NAMES]

        if any(role_name in admin_role_names for role_name in user_role_names):
            return PermissionLevel.ADMIN

        return PermissionLevel.USER

    def has_permission(
        self,
        user: Union[discord.Member, discord.User],
        required_level: PermissionLevel,
        guild: discord.Guild = None,
    ) -> bool:
        """Check if user has required permission level."""
        user_level = self.get_user_permission_level(user, guild)
        return user_level.value >= required_level.value


def require_permission(level: PermissionLevel):
    """Decorator to require specific permission level for commands."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(self, ctx, *args, **kwargs):
            bot = self.bot if hasattr(self, "bot") else ctx.bot
            permission_manager = bot.permission_manager

            if not permission_manager.has_permission(ctx.author, level, ctx.guild):
                level_names = {
                    PermissionLevel.USER: "user",
                    PermissionLevel.ADMIN: "admin/moderator",
                    PermissionLevel.OWNER: "owner",
                }
                await ctx.send(
                    f"❌ This command requires {level_names[level]} permissions."
                )
                return

            return await func(self, ctx, *args, **kwargs)

        return wrapper

    return decorator


def owner_only():
    """Decorator for owner-only commands."""
    return require_permission(PermissionLevel.OWNER)


def admin_only():
    """Decorator for admin-only commands."""
    return require_permission(PermissionLevel.ADMIN)


def user_level():
    """Decorator for user-level commands (all users can use)."""
    return require_permission(PermissionLevel.USER)
