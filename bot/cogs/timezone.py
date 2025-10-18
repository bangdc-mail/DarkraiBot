"""
Timezone Cog - User-level commands for checking time in different timezones.
"""

import logging
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands
import pytz

from utils.permissions import user_level

logger = logging.getLogger(__name__)


class TimezoneCog(commands.Cog):
    """Cog for timezone and time-related commands."""

    def __init__(self, bot):
        self.bot = bot

        # Common timezone mappings for user convenience
        self.timezone_aliases = {
            # US Timezones
            "est": "US/Eastern",
            "eastern": "US/Eastern",
            "cst": "US/Central",
            "central": "US/Central",
            "mst": "US/Mountain",
            "mountain": "US/Mountain",
            "pst": "US/Pacific",
            "pacific": "US/Pacific",
            "hst": "US/Hawaii",
            "hawaii": "US/Hawaii",
            # Europe
            "gmt": "GMT",
            "bst": "Europe/London",
            "cet": "Europe/Berlin",
            "eet": "Europe/Helsinki",
            # Asia
            "jst": "Asia/Tokyo",
            "japan": "Asia/Tokyo",
            "kst": "Asia/Seoul",
            "korea": "Asia/Seoul",
            "ist": "Asia/Kolkata",
            "india": "Asia/Kolkata",
            "cst_china": "Asia/Shanghai",
            "china": "Asia/Shanghai",
            # Australia
            "aest": "Australia/Sydney",
            "awst": "Australia/Perth",
            # Other common ones
            "utc": "UTC",
            "gmt": "GMT",
        }

        # Popular timezones for the list command
        self.popular_timezones = [
            ("UTC", "UTC"),
            ("EST", "US/Eastern"),
            ("CST", "US/Central"),
            ("PST", "US/Pacific"),
            ("GMT", "GMT"),
            ("CET", "Europe/Berlin"),
            ("JST", "Asia/Tokyo"),
            ("IST", "Asia/Kolkata"),
            ("AEST", "Australia/Sydney"),
        ]

    def _resolve_timezone(self, timezone_input: str) -> Optional[pytz.BaseTzInfo]:
        """
        Resolve a timezone string to a pytz timezone object.

        Args:
            timezone_input: User input for timezone

        Returns:
            pytz timezone object or None if not found
        """
        if not timezone_input:
            return pytz.UTC

        timezone_input = timezone_input.lower().strip()

        # Check aliases first
        if timezone_input in self.timezone_aliases:
            timezone_name = self.timezone_aliases[timezone_input]
        else:
            timezone_name = timezone_input

        try:
            # Try to get the timezone directly
            return pytz.timezone(timezone_name)
        except pytz.UnknownTimeZoneError:
            # Try some common variations
            variations = [
                timezone_name.upper(),
                timezone_name.title(),
                f"US/{timezone_name.title()}",
                f"Europe/{timezone_name.title()}",
                f"Asia/{timezone_name.title()}",
                f"Australia/{timezone_name.title()}",
            ]

            for variation in variations:
                try:
                    return pytz.timezone(variation)
                except pytz.UnknownTimeZoneError:
                    continue

        return None

    def _format_time(self, dt: datetime, timezone_name: str) -> str:
        """Format datetime for display."""
        return f"{dt.strftime('%Y-%m-%d %H:%M:%S')} {timezone_name}"

    @commands.group(
        name="time", aliases=["tz", "timezone"], invoke_without_command=True
    )
    @user_level()
    async def time_group(self, ctx, *, timezone: str = None):
        """
        Show current time in UTC or specified timezone.

        Usage:
        !time              - Show UTC time
        !time EST          - Show Eastern time
        !time Europe/London - Show London time
        !time PST          - Show Pacific time

        Use !time list to see popular timezones
        """
        try:
            # Log the command usage
            await self.bot.database.log_command(
                ctx.author.id, ctx.guild.id if ctx.guild else None, "time"
            )

            if timezone is None:
                # Default to UTC
                target_tz = pytz.UTC
                display_name = "UTC"
            else:
                target_tz = self._resolve_timezone(timezone)
                if target_tz is None:
                    await ctx.send(
                        f"❌ Unknown timezone: `{timezone}`\nUse `{ctx.prefix}time list` to see available timezones."
                    )
                    return
                display_name = str(target_tz)

            # Get current time in the timezone
            utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
            local_time = utc_now.astimezone(target_tz)

            # Create embed
            embed = discord.Embed(
                title="🕐 Current Time",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow(),
            )

            embed.add_field(
                name=f"Time in {display_name}",
                value=f"**{self._format_time(local_time, display_name)}**",
                inline=False,
            )

            # Add UTC time if not already showing UTC
            if target_tz != pytz.UTC:
                embed.add_field(
                    name="UTC Time",
                    value=f"{self._format_time(utc_now, 'UTC')}",
                    inline=False,
                )

            # Add Unix timestamp
            embed.add_field(
                name="Unix Timestamp",
                value=f"`{int(utc_now.timestamp())}`",
                inline=True,
            )

            # Add Discord timestamp
            embed.add_field(
                name="Discord Timestamp",
                value=f"<t:{int(utc_now.timestamp())}:F>",
                inline=True,
            )

            embed.set_footer(text=f"Requested by {ctx.author}")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error getting time: {str(e)}")
            logger.error(f"Time command error: {e}")

    @time_group.command(name="list", aliases=["zones"])
    @user_level()
    async def list_timezones(self, ctx):
        """Show popular timezones and their current times."""
        try:
            embed = discord.Embed(
                title="🌍 Popular Timezones",
                description="Current times in popular timezones",
                color=discord.Color.green(),
                timestamp=datetime.utcnow(),
            )

            utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)

            timezone_times = []
            for display_name, timezone_name in self.popular_timezones:
                try:
                    tz = pytz.timezone(timezone_name)
                    local_time = utc_now.astimezone(tz)
                    time_str = local_time.strftime("%H:%M")
                    timezone_times.append(f"**{display_name}**: {time_str}")
                except:
                    continue

            # Split into two columns for better display
            mid = len(timezone_times) // 2
            left_column = timezone_times[:mid]
            right_column = timezone_times[mid:]

            if left_column:
                embed.add_field(
                    name="🌎 Americas & Europe",
                    value="\n".join(left_column),
                    inline=True,
                )

            if right_column:
                embed.add_field(
                    name="🌏 Asia & Oceania", value="\n".join(right_column), inline=True
                )

            embed.add_field(
                name="💡 Usage Examples",
                value=(
                    f"`{ctx.prefix}time EST` - Eastern time\n"
                    f"`{ctx.prefix}time Asia/Tokyo` - Tokyo time\n"
                    f"`{ctx.prefix}time UTC` - UTC time"
                ),
                inline=False,
            )

            embed.set_footer(text="Use !time <timezone> to get specific time")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error listing timezones: {str(e)}")
            logger.error(f"Timezone list error: {e}")

    @time_group.command(name="compare", aliases=["diff"])
    @user_level()
    async def compare_timezones(self, ctx, tz1: str, tz2: str):
        """
        Compare time between two timezones.

        Usage: !time compare EST PST
        """
        try:
            # Resolve both timezones
            timezone1 = self._resolve_timezone(tz1)
            timezone2 = self._resolve_timezone(tz2)

            if timezone1 is None:
                await ctx.send(f"❌ Unknown timezone: `{tz1}`")
                return

            if timezone2 is None:
                await ctx.send(f"❌ Unknown timezone: `{tz2}`")
                return

            utc_now = datetime.utcnow().replace(tzinfo=pytz.UTC)
            time1 = utc_now.astimezone(timezone1)
            time2 = utc_now.astimezone(timezone2)

            # Calculate time difference
            diff = time1.utcoffset() - time2.utcoffset()
            diff_hours = diff.total_seconds() / 3600

            embed = discord.Embed(
                title="🕐 Timezone Comparison",
                color=discord.Color.purple(),
                timestamp=datetime.utcnow(),
            )

            embed.add_field(
                name=f"{str(timezone1)}",
                value=f"**{self._format_time(time1, str(timezone1))}**",
                inline=False,
            )

            embed.add_field(
                name=f"{str(timezone2)}",
                value=f"**{self._format_time(time2, str(timezone2))}**",
                inline=False,
            )

            if diff_hours > 0:
                diff_text = f"{str(timezone1)} is {abs(diff_hours):.1f} hours ahead of {str(timezone2)}"
            elif diff_hours < 0:
                diff_text = f"{str(timezone2)} is {abs(diff_hours):.1f} hours ahead of {str(timezone1)}"
            else:
                diff_text = "Both timezones are the same"

            embed.add_field(name="⏰ Time Difference", value=diff_text, inline=False)

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Error comparing timezones: {str(e)}")
            logger.error(f"Timezone compare error: {e}")

    @time_group.command(name="help")
    @user_level()
    async def time_help(self, ctx):
        """Show detailed help for time commands."""
        embed = discord.Embed(
            title="🕐 Time Commands Help",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )

        embed.add_field(
            name="📅 Basic Time",
            value=(
                f"`{ctx.prefix}time` - Show UTC time\n"
                f"`{ctx.prefix}time <timezone>` - Show time in timezone"
            ),
            inline=False,
        )

        embed.add_field(
            name="📋 List Timezones",
            value=(f"`{ctx.prefix}time list` - Show popular timezones"),
            inline=False,
        )

        embed.add_field(
            name="⚖️ Compare Timezones",
            value=(f"`{ctx.prefix}time compare <tz1> <tz2>` - Compare two timezones"),
            inline=False,
        )

        embed.add_field(
            name="🌍 Timezone Formats",
            value=(
                "• **Aliases**: EST, PST, GMT, UTC, JST\n"
                "• **Full names**: US/Eastern, Europe/London\n"
                "• **Cities**: Asia/Tokyo, America/New_York"
            ),
            inline=False,
        )

        embed.add_field(
            name="📌 Examples",
            value=(
                f"`{ctx.prefix}time EST` - Eastern time\n"
                f"`{ctx.prefix}time Asia/Tokyo` - Tokyo time\n"
                f"`{ctx.prefix}time compare EST PST` - Compare EST and PST"
            ),
            inline=False,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(TimezoneCog(bot))
