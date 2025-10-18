"""
General Cog - Basic bot commands and help system.
"""

import logging
from datetime import datetime

import discord
from discord.ext import commands

from utils.permissions import user_level, admin_only, owner_only, PermissionLevel

logger = logging.getLogger(__name__)


class GeneralCog(commands.Cog):
    """General bot commands and utilities."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    @user_level()
    async def help_command(self, ctx, *, command: str = None):
        """
        Show help information for bot commands.

        Usage: !help [command]
        """
        if command:
            # Show help for specific command
            cmd = self.bot.get_command(command)
            if cmd:
                embed = discord.Embed(
                    title=f"Help: {cmd.name}",
                    description=cmd.help or "No description available.",
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow(),
                )

                if cmd.aliases:
                    embed.add_field(
                        name="Aliases",
                        value=", ".join(f"`{alias}`" for alias in cmd.aliases),
                        inline=False,
                    )

                embed.add_field(
                    name="Usage",
                    value=f"`{ctx.prefix}{cmd.name} {cmd.signature}`",
                    inline=False,
                )
            else:
                embed = discord.Embed(
                    title="❌ Command Not Found",
                    description=f"No command named `{command}` found.",
                    color=discord.Color.red(),
                    timestamp=datetime.utcnow(),
                )
        else:
            # Show general help
            embed = await self._create_help_embed(ctx)

        await ctx.send(embed=embed)

    async def _create_help_embed(self, ctx) -> discord.Embed:
        """Create the main help embed."""
        embed = discord.Embed(
            title="🤖 Bot Help",
            description="A modular Discord bot with role-based permissions.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )

        # Get user permission level
        permission_level = self.bot.permission_manager.get_user_permission_level(
            ctx.author, ctx.guild
        )

        # General commands (available to all users)
        general_commands = [
            f"`{ctx.prefix}help` - Show this help message",
            f"`{ctx.prefix}ping` - Check bot latency",
            f"`{ctx.prefix}info` - Show bot information",
        ]

        embed.add_field(
            name="📋 General Commands", value="\n".join(general_commands), inline=False
        )

        # Reminder commands (user level)
        reminder_commands = [
            f"`{ctx.prefix}remind <time> <message>` - Set a reminder",
            f"`{ctx.prefix}remind list` - List your reminders",
            f"`{ctx.prefix}remind cancel <id>` - Cancel a reminder",
            f"`{ctx.prefix}remind help` - Detailed reminder help",
        ]

        embed.add_field(
            name="⏰ Reminder Commands",
            value="\n".join(reminder_commands),
            inline=False,
        )

        # Time commands (user level)
        time_commands = [
            f"`{ctx.prefix}time` - Show UTC time",
            f"`{ctx.prefix}time <timezone>` - Show time in timezone",
            f"`{ctx.prefix}time list` - List popular timezones",
            f"`{ctx.prefix}time help` - Detailed timezone help",
        ]

        embed.add_field(
            name="🕐 Time Commands",
            value="\n".join(time_commands),
            inline=False,
        )

        # Admin commands (admin level and above)
        if permission_level.value >= PermissionLevel.ADMIN.value:
            admin_commands = [
                f"`{ctx.prefix}reload <cog>` - Reload a bot module",
                f"`{ctx.prefix}status` - Show bot status",
            ]

            embed.add_field(
                name="🛠️ Admin Commands", value="\n".join(admin_commands), inline=False
            )

        # Owner commands (owner only)
        if permission_level.value >= PermissionLevel.OWNER.value:
            owner_commands = [
                f"`{ctx.prefix}ip` - Check bot's public IP",
                f"`{ctx.prefix}ip-info` - Detailed IP information",
                f"`{ctx.prefix}shutdown` - Shutdown the bot",
            ]

            embed.add_field(
                name="👑 Owner Commands", value="\n".join(owner_commands), inline=False
            )

        embed.add_field(
            name="🔑 Your Permission Level",
            value=f"`{permission_level.name.title()}`",
            inline=True,
        )

        embed.add_field(
            name="📊 Bot Stats",
            value=f"Servers: {len(self.bot.guilds)}\nUsers: {len(self.bot.users)}",
            inline=True,
        )

        embed.set_footer(
            text=f"Use {ctx.prefix}help <command> for detailed help on a specific command"
        )

        return embed

    @commands.command(name="ping")
    @user_level()
    async def ping(self, ctx):
        """Check the bot's latency."""
        latency = round(self.bot.latency * 1000)

        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"Bot latency: **{latency}ms**",
            color=(
                discord.Color.green()
                if latency < 100
                else discord.Color.yellow() if latency < 200 else discord.Color.red()
            ),
            timestamp=datetime.utcnow(),
        )

        await ctx.send(embed=embed)

    @commands.command(name="info", aliases=["about"])
    @user_level()
    async def info(self, ctx):
        """Show information about the bot."""
        embed = discord.Embed(
            title="🤖 Bot Information",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )

        embed.add_field(name="Bot Name", value=self.bot.user.name, inline=True)
        embed.add_field(name="Bot ID", value=self.bot.user.id, inline=True)
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Users", value=len(self.bot.users), inline=True)
        embed.add_field(name="Commands", value=len(self.bot.commands), inline=True)
        embed.add_field(
            name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True
        )

        embed.add_field(
            name="Features",
            value="• Role-based permissions\n• Reminder system\n• IP checking\n• Docker support",
            inline=False,
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Running on Docker")

        await ctx.send(embed=embed)

    @commands.command(name="reload")
    @admin_only()
    async def reload_cog(self, ctx, *, cog_name: str):
        """
        Reload a bot cog/module.

        Usage: !reload <cog_name>
        """
        try:
            cog_name = (
                f"cogs.{cog_name}" if not cog_name.startswith("cogs.") else cog_name
            )

            await self.bot.reload_extension(cog_name)

            embed = discord.Embed(
                title="✅ Cog Reloaded",
                description=f"Successfully reloaded `{cog_name}`",
                color=discord.Color.green(),
                timestamp=datetime.utcnow(),
            )

        except Exception as e:
            embed = discord.Embed(
                title="❌ Reload Failed",
                description=f"Failed to reload `{cog_name}`: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow(),
            )

        await ctx.send(embed=embed)

    @commands.command(name="status")
    @admin_only()
    async def status_command(self, ctx):
        """Show detailed bot status information."""
        embed = discord.Embed(
            title="📊 Bot Status",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )

        # Get database stats
        try:
            pending_reminders = await self.bot.database.get_pending_reminders()
            reminder_count = len(pending_reminders)
        except:
            reminder_count = "Error"

        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Users", value=len(self.bot.users), inline=True)
        embed.add_field(
            name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True
        )
        embed.add_field(name="Loaded Cogs", value=len(self.bot.cogs), inline=True)
        embed.add_field(name="Commands", value=len(self.bot.commands), inline=True)
        embed.add_field(name="Pending Reminders", value=reminder_count, inline=True)

        await ctx.send(embed=embed)

    @commands.command(name="shutdown")
    @owner_only()
    async def shutdown(self, ctx):
        """Shutdown the bot (owner only)."""
        embed = discord.Embed(
            title="👋 Shutting Down",
            description="Bot is shutting down...",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow(),
        )

        await ctx.send(embed=embed)
        logger.info(f"Bot shutdown initiated by {ctx.author}")

        await self.bot.close()


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(GeneralCog(bot))
