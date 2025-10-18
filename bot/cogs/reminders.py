"""
Reminder Cog - User-level commands for setting up reminders.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import discord
from discord.ext import commands, tasks

from utils.permissions import user_level
from utils.time_parser import TimeParser

logger = logging.getLogger(__name__)


class ReminderCog(commands.Cog):
    """Cog for reminder functionality."""

    def __init__(self, bot):
        self.bot = bot
        self.time_parser = TimeParser()
        self.reminder_check_loop.start()

    def cog_unload(self):
        """Clean up when cog is unloaded."""
        self.reminder_check_loop.cancel()

    @tasks.loop(seconds=30)
    async def reminder_check_loop(self):
        """Check for pending reminders every 30 seconds."""
        try:
            pending_reminders = await self.bot.database.get_pending_reminders()

            for reminder in pending_reminders:
                await self._send_reminder(reminder)
                await self.bot.database.mark_reminder_completed(reminder["id"])

        except Exception as e:
            logger.error(f"Error in reminder check loop: {e}")

    @reminder_check_loop.before_loop
    async def before_reminder_check(self):
        """Wait for bot to be ready before starting reminder loop."""
        await self.bot.wait_until_ready()

    async def _send_reminder(self, reminder: dict):
        """Send a reminder to the user."""
        try:
            channel = self.bot.get_channel(reminder["channel_id"])
            if not channel:
                logger.warning(
                    f"Channel {reminder['channel_id']} not found for reminder {reminder['id']}"
                )
                return

            user = self.bot.get_user(reminder["user_id"])
            if not user:
                logger.warning(
                    f"User {reminder['user_id']} not found for reminder {reminder['id']}"
                )
                return

            embed = discord.Embed(
                title="⏰ Reminder",
                description=reminder["message"],
                color=discord.Color.orange(),
                timestamp=datetime.utcnow(),
            )
            embed.set_footer(text="Reminder Service")

            await channel.send(f"{user.mention}", embed=embed)
            logger.info(f"Sent reminder {reminder['id']} to user {user.id}")

        except Exception as e:
            logger.error(f"Failed to send reminder {reminder['id']}: {e}")

    @commands.group(name="remind", aliases=["reminder"], invoke_without_command=True)
    @user_level()
    async def remind_group(self, ctx, time: str, *, message: str):
        """
        Set a reminder for yourself.

        Usage:
        !remind 1h Take a break
        !remind 30m Check the oven
        !remind 2h30m Call mom
        !remind tomorrow Go to the store

        Time formats supported:
        - 1h, 2h30m, 45m, 30s
        - tomorrow, next week
        - in 5 minutes, in 2 hours
        """
        try:
            # Parse the time
            remind_at = self.time_parser.parse_time(time)

            if remind_at <= datetime.utcnow():
                await ctx.send("❌ Reminder time must be in the future!")
                return

            # Check if too far in the future (1 year limit)
            max_time = datetime.utcnow() + timedelta(days=365)
            if remind_at > max_time:
                await ctx.send(
                    "❌ Reminder time cannot be more than 1 year in the future!"
                )
                return

            # Add reminder to database
            reminder_id = await self.bot.database.add_reminder(
                user_id=ctx.author.id,
                guild_id=ctx.guild.id if ctx.guild else None,
                channel_id=ctx.channel.id,
                message=message,
                remind_at=remind_at,
            )

            # Log the command
            await self.bot.database.log_command(
                ctx.author.id, ctx.guild.id if ctx.guild else None, "remind"
            )

            # Send confirmation
            time_diff = remind_at - datetime.utcnow()
            embed = discord.Embed(
                title="✅ Reminder Set",
                color=discord.Color.green(),
                timestamp=datetime.utcnow(),
            )
            embed.add_field(name="Message", value=message, inline=False)
            embed.add_field(
                name="Remind At",
                value=f"<t:{int(remind_at.timestamp())}:F>",
                inline=True,
            )
            embed.add_field(
                name="In", value=self._format_time_delta(time_diff), inline=True
            )
            embed.add_field(name="Reminder ID", value=f"`{reminder_id}`", inline=True)
            embed.set_footer(text=f"Set by {ctx.author}")

            await ctx.send(embed=embed)

        except ValueError as e:
            await ctx.send(f"❌ Invalid time format: {e}")
        except Exception as e:
            await ctx.send(f"❌ Failed to set reminder: {e}")
            logger.error(f"Failed to set reminder: {e}")

    @remind_group.command(name="list", aliases=["ls"])
    @user_level()
    async def list_reminders(self, ctx, limit: int = 5):
        """
        List your active and recent reminders.

        Usage: !remind list [limit]
        """
        try:
            if limit > 20:
                limit = 20

            reminders = await self.bot.database.get_user_reminders(ctx.author.id, limit)

            if not reminders:
                await ctx.send("📝 You have no reminders set.")
                return

            embed = discord.Embed(
                title="📝 Your Reminders",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow(),
            )

            for reminder in reminders:
                status = "✅ Completed" if reminder["completed"] else "⏳ Pending"
                remind_time = datetime.fromisoformat(reminder["remind_at"])

                embed.add_field(
                    name=f"ID: {reminder['id']} - {status}",
                    value=(
                        f"**Message:** {reminder['message'][:100]}{'...' if len(reminder['message']) > 100 else ''}\n"
                        f"**Time:** <t:{int(remind_time.timestamp())}:F>"
                    ),
                    inline=False,
                )

            embed.set_footer(text=f"Showing {len(reminders)} reminders")
            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to list reminders: {e}")
            logger.error(f"Failed to list reminders: {e}")

    @remind_group.command(name="cancel", aliases=["delete", "remove"])
    @user_level()
    async def cancel_reminder(self, ctx, reminder_id: int):
        """
        Cancel a pending reminder.

        Usage: !remind cancel <reminder_id>
        """
        try:
            success = await self.bot.database.delete_reminder(
                reminder_id, ctx.author.id
            )

            if success:
                embed = discord.Embed(
                    title="✅ Reminder Cancelled",
                    description=f"Reminder with ID `{reminder_id}` has been cancelled.",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow(),
                )
            else:
                embed = discord.Embed(
                    title="❌ Reminder Not Found",
                    description=f"No reminder with ID `{reminder_id}` found, or you don't have permission to cancel it.",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow(),
                )

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to cancel reminder: {e}")
            logger.error(f"Failed to cancel reminder: {e}")

    @remind_group.command(name="help")
    @user_level()
    async def reminder_help(self, ctx):
        """Show detailed help for reminder commands."""
        embed = discord.Embed(
            title="⏰ Reminder System Help",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )

        embed.add_field(
            name="📝 Set a Reminder",
            value=(
                f"`{ctx.prefix}remind <time> <message>`\n"
                "Set a reminder with a custom message"
            ),
            inline=False,
        )

        embed.add_field(
            name="📋 List Reminders",
            value=(
                f"`{ctx.prefix}remind list [limit]`\n"
                "Show your active and recent reminders"
            ),
            inline=False,
        )

        embed.add_field(
            name="❌ Cancel Reminder",
            value=(
                f"`{ctx.prefix}remind cancel <id>`\n" "Cancel a pending reminder by ID"
            ),
            inline=False,
        )

        embed.add_field(
            name="⏰ Time Formats",
            value=(
                "• `1h`, `30m`, `45s` - Hours, minutes, seconds\n"
                "• `2h30m` - Combined format\n"
                "• `tomorrow`, `next week` - Natural language\n"
                "• `in 5 minutes`, `in 2 hours` - Relative time"
            ),
            inline=False,
        )

        embed.add_field(
            name="📌 Examples",
            value=(
                f"`{ctx.prefix}remind 1h Take a break`\n"
                f"`{ctx.prefix}remind 30m Check the oven`\n"
                f"`{ctx.prefix}remind tomorrow Call mom`"
            ),
            inline=False,
        )

        await ctx.send(embed=embed)

    def _format_time_delta(self, delta: timedelta) -> str:
        """Format a timedelta into a human-readable string."""
        total_seconds = int(delta.total_seconds())

        if total_seconds < 60:
            return f"{total_seconds} second{'s' if total_seconds != 1 else ''}"

        minutes = total_seconds // 60
        if minutes < 60:
            return f"{minutes} minute{'s' if minutes != 1 else ''}"

        hours = minutes // 60
        remaining_minutes = minutes % 60

        if hours < 24:
            if remaining_minutes == 0:
                return f"{hours} hour{'s' if hours != 1 else ''}"
            return f"{hours} hour{'s' if hours != 1 else ''} and {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"

        days = hours // 24
        remaining_hours = hours % 24

        if remaining_hours == 0:
            return f"{days} day{'s' if days != 1 else ''}"
        return f"{days} day{'s' if days != 1 else ''} and {remaining_hours} hour{'s' if remaining_hours != 1 else ''}"


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(ReminderCog(bot))
