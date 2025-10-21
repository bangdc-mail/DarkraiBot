# Plugin: Core
# Version: 2.0.0
# Author: DarkraiBot
# Description: Core bot functionality - Essential commands and administrative utilities
# Dependencies:
# Permissions: user

"""
Core Cog - The essential foundation of DarkraiBot.

This is the primary cog that provides all essential bot functionality including:
- Help system with role-based command filtering
- Bot information, status, and diagnostics
- Owner administrative utilities (DM, server management, restart/shutdown)
- Admin utilities (reload, system status)
- User services (contact system, basic commands)

This cog is critical to bot operation and should always be loaded.
"""

import os
import sys
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import discord
from discord.ext import commands

from utils.permissions import user_level, admin_only, owner_only, PermissionLevel

logger = logging.getLogger(__name__)


class CoreCog(commands.Cog):
    """Core bot functionality - Essential commands and administrative utilities."""

    def __init__(self, bot):
        self.bot = bot
        self.start_time = datetime.utcnow()
        self.contact_cooldowns: Dict[int, datetime] = {}  # user_id -> last_contact_time
        logger.info("Core cog initialized - Essential bot functionality loaded")

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
            title="🤖 DarkraiBot Help",
            description="A modular Discord bot with role-based permissions and dynamic plugin system.",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )

        # Get user permission level
        permission_level = self.bot.permission_manager.get_user_permission_level(
            ctx.author, ctx.guild
        )

        # Core commands (available to all users)
        embed.add_field(
            name="🔷 Core Commands",
            value=(
                f"`{ctx.prefix}help` - Show this help message\n"
                f"`{ctx.prefix}ping` - Check bot latency\n"
                f"`{ctx.prefix}info` - Bot information and statistics\n"
                f"`{ctx.prefix}uptime` - Show bot uptime\n"
                f"`{ctx.prefix}contact <message>` - Contact bot owner"
            ),
            inline=False,
        )

        # Feature-specific commands based on loaded cogs
        cog_commands = []

        if "ReminderCog" in self.bot.cogs:
            cog_commands.append(
                "⏰ **Reminders**: `remind`, `remind list`, `remind cancel`"
            )

        if "TimezoneCog" in self.bot.cogs:
            cog_commands.append("🌍 **Timezone**: `time`, `time list`, `time compare`")

        if (
            "SettingsCog" in self.bot.cogs
            and permission_level.value >= PermissionLevel.ADMIN.value
        ):
            cog_commands.append(
                "⚙️ **Settings**: `set prefix`, `set admin-roles`, `set mod-roles`"
            )

        if (
            "PluginManagementCog" in self.bot.cogs
            and permission_level.value >= PermissionLevel.ADMIN.value
        ):
            cog_commands.append(
                "🔌 **Plugins**: `plugin list`, `plugin load/unload`, `plugin reload`"
            )

        if cog_commands:
            embed.add_field(
                name="🔧 Available Features",
                value="\n".join(cog_commands),
                inline=False,
            )

        # Admin commands
        if permission_level.value >= PermissionLevel.ADMIN.value:
            admin_commands = [
                f"`{ctx.prefix}reload <cog>` - Reload a cog or plugin",
                f"`{ctx.prefix}status` - Detailed bot status information",
            ]

            embed.add_field(
                name="👑 Admin Commands",
                value="\n".join(admin_commands),
                inline=False,
            )

        # Owner commands
        if permission_level == PermissionLevel.OWNER:
            owner_commands = [
                f"`{ctx.prefix}dm <user_id> <message>` - Send DM to user",
                f"`{ctx.prefix}servers` - List all bot servers",
                f"`{ctx.prefix}leave <server_id>` - Leave server(s)",
                f"`{ctx.prefix}restart` - Restart the bot",
                f"`{ctx.prefix}shutdown` - Shutdown the bot",
            ]

            if "IPCheckCog" in self.bot.cogs:
                owner_commands.append(f"`{ctx.prefix}ip` - Check bot IP address")

            embed.add_field(
                name="🔒 Owner Commands",
                value="\n".join(owner_commands),
                inline=False,
            )

        embed.add_field(
            name="🏷️ Your Permission Level",
            value=f"`{permission_level.name.title()}`",
            inline=True,
        )

        embed.set_footer(
            text=f"Use {ctx.prefix}help <command> for detailed information • Core v2.0.0"
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
        """Show comprehensive information about the bot."""
        embed = discord.Embed(
            title="🤖 DarkraiBot Information",
            description="Modular Discord bot with dynamic plugin system and role-based permissions",
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

        # Calculate uptime
        uptime = datetime.utcnow() - self.start_time
        uptime_str = self._format_uptime(uptime)
        embed.add_field(name="Uptime", value=uptime_str, inline=True)

        # Plugin stats if available
        if hasattr(self.bot, "plugin_manager"):
            stats = self.bot.plugin_manager.get_plugin_stats()
            embed.add_field(
                name="Plugins",
                value=f"{stats['loaded_plugins']}/{stats['total_plugins']} loaded",
                inline=True,
            )
        else:
            embed.add_field(name="Loaded Cogs", value=len(self.bot.cogs), inline=True)

        embed.add_field(name="Core Version", value="v2.0.0", inline=True)

        embed.add_field(
            name="Key Features",
            value="• Role-based permissions (4 levels)\n• Dynamic plugin system with hot-reload\n• Guild-specific settings\n• Docker deployment ready\n• Comprehensive logging system",
            inline=False,
        )

        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="DarkraiBot Core • Essential Bot Functionality")

        await ctx.send(embed=embed)

    @commands.command(name="uptime")
    @user_level()
    async def uptime(self, ctx):
        """Show bot uptime information."""
        uptime = datetime.utcnow() - self.start_time
        uptime_str = self._format_uptime(uptime)

        embed = discord.Embed(
            title="⏱️ Bot Uptime",
            description=f"**{uptime_str}**",
            color=discord.Color.green(),
            timestamp=datetime.utcnow(),
        )

        embed.add_field(
            name="Started",
            value=f"<t:{int(self.start_time.timestamp())}:F>",
            inline=True,
        )

        embed.add_field(
            name="Total Seconds", value=f"{int(uptime.total_seconds())}", inline=True
        )

        await ctx.send(embed=embed)

    @commands.command(name="contact")
    @user_level()
    async def contact_owner(self, ctx, *, message: str):
        """
        Send a message to the bot owner.

        Limited to one message per user every 60 seconds to prevent spam.

        Usage: !contact <message>
        """
        user_id = ctx.author.id
        current_time = datetime.utcnow()

        # Check cooldown
        if user_id in self.contact_cooldowns:
            last_contact = self.contact_cooldowns[user_id]
            time_diff = (current_time - last_contact).total_seconds()

            if time_diff < 60:
                remaining = 60 - int(time_diff)
                embed = discord.Embed(
                    title="⏰ Cooldown Active",
                    description=f"You can contact the owner again in {remaining} seconds.",
                    color=discord.Color.orange(),
                )
                await ctx.send(embed=embed)
                return

        # Update cooldown
        self.contact_cooldowns[user_id] = current_time

        try:
            # Get bot owner
            owner = self.bot.get_user(self.bot.config.OWNER_ID)
            if not owner:
                owner = await self.bot.fetch_user(self.bot.config.OWNER_ID)

            if not owner:
                await ctx.send("❌ Could not reach the bot owner.")
                return

            # Create message embed
            embed = discord.Embed(
                title="📬 New Contact Message",
                description=message,
                color=discord.Color.blue(),
                timestamp=current_time,
            )

            embed.add_field(
                name="From User", value=f"{ctx.author} (`{ctx.author.id}`)", inline=True
            )

            if ctx.guild:
                embed.add_field(
                    name="From Server",
                    value=f"{ctx.guild.name} (`{ctx.guild.id}`)",
                    inline=True,
                )
                embed.add_field(
                    name="Channel", value=f"{ctx.channel.mention}", inline=True
                )
            else:
                embed.add_field(name="Source", value="Direct Message", inline=True)

            embed.set_author(
                name=str(ctx.author), icon_url=ctx.author.display_avatar.url
            )

            # Send to owner
            await owner.send(embed=embed)

            # Confirm to user
            confirm_embed = discord.Embed(
                title="✅ Message Sent",
                description="Your message has been sent to the bot owner.",
                color=discord.Color.green(),
            )
            await ctx.send(embed=confirm_embed)

            # Log the contact
            logger.info(
                f"Contact message from {ctx.author} ({ctx.author.id}): {message[:100]}"
            )

        except discord.Forbidden:
            await ctx.send("❌ Could not send message to the bot owner (DMs disabled).")
        except Exception as e:
            await ctx.send(f"❌ Error sending message: {str(e)}")
            logger.error(f"Error in contact command: {e}")

    @commands.command(name="dm")
    @owner_only()
    async def dm_user(self, ctx, user_id: int, *, message: str):
        """
        Send a direct message to a user.

        Usage: !dm <user_id> <message>
        """
        try:
            # Get the user
            user = self.bot.get_user(user_id)
            if not user:
                user = await self.bot.fetch_user(user_id)

            if not user:
                await ctx.send(f"❌ User with ID `{user_id}` not found.")
                return

            # Create DM embed
            embed = discord.Embed(
                title="📨 Message from Bot Owner",
                description=message,
                color=discord.Color.blue(),
                timestamp=datetime.utcnow(),
            )

            embed.set_footer(
                text="This message was sent by the bot owner",
                icon_url=self.bot.user.display_avatar.url,
            )

            # Send the DM
            await user.send(embed=embed)

            # Confirm to owner
            confirm_embed = discord.Embed(
                title="✅ DM Sent",
                description=f"Message sent to {user} (`{user.id}`)",
                color=discord.Color.green(),
            )
            await ctx.send(embed=confirm_embed)

            logger.info(f"Owner DM sent to {user} ({user.id}): {message[:100]}")

        except discord.Forbidden:
            await ctx.send(f"❌ Cannot send DM to {user} (DMs disabled or blocked).")
        except discord.NotFound:
            await ctx.send(f"❌ User with ID `{user_id}` not found.")
        except Exception as e:
            await ctx.send(f"❌ Error sending DM: {str(e)}")
            logger.error(f"Error in dm command: {e}")

    @commands.command(name="servers")
    @owner_only()
    async def list_servers(self, ctx):
        """List all servers the bot is currently in."""
        guilds = self.bot.guilds

        if not guilds:
            await ctx.send("❌ Bot is not in any servers.")
            return

        # Sort by member count (descending)
        guilds.sort(key=lambda g: g.member_count, reverse=True)

        embed = discord.Embed(
            title="📋 Bot Server List",
            description=f"Bot is currently in {len(guilds)} server(s)",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )

        # Show servers in chunks
        guild_list = []
        for guild in guilds[:20]:  # Limit to first 20
            member_count = guild.member_count or "Unknown"
            guild_info = (
                f"**{guild.name}**\n`ID:` {guild.id}\n`Members:` {member_count}"
            )

            if guild.owner:
                guild_info += f"\n`Owner:` {guild.owner}"

            guild_list.append(guild_info)

        # Split into multiple embeds if needed
        if len(guild_list) <= 5:
            for i, guild_info in enumerate(guild_list):
                embed.add_field(name=f"Server {i+1}", value=guild_info, inline=True)
        else:
            # Create a text list for many servers
            server_text = []
            for i, guild in enumerate(guilds[:50]):  # Limit to 50
                member_count = guild.member_count or "?"
                server_text.append(
                    f"{i+1}. **{guild.name}** (`{guild.id}`) - {member_count} members"
                )

            embed.add_field(
                name="Server List",
                value="\n".join(server_text[:20]),  # Discord embed field limit
                inline=False,
            )

            if len(guilds) > 20:
                embed.add_field(
                    name="Note",
                    value=f"Showing 20 of {len(guilds)} servers. Use `!leave <server_id>` to leave specific servers.",
                    inline=False,
                )

        await ctx.send(embed=embed)

    @commands.command(name="leave")
    @owner_only()
    async def leave_servers(self, ctx, *server_ids):
        """
        Leave one or more servers by ID.

        Usage: !leave <server_id1> [server_id2] [server_id3]...
        """
        if not server_ids:
            await ctx.send("❌ Please provide at least one server ID.")
            return

        results = []

        for server_id_str in server_ids:
            try:
                server_id = int(server_id_str)
                guild = self.bot.get_guild(server_id)

                if not guild:
                    results.append(f"❌ Server `{server_id}` not found")
                    continue

                guild_name = guild.name
                await guild.leave()
                results.append(f"✅ Left **{guild_name}** (`{server_id}`)")
                logger.info(
                    f"Bot left guild {guild_name} ({server_id}) by owner command"
                )

            except ValueError:
                results.append(f"❌ Invalid server ID: `{server_id_str}`")
            except Exception as e:
                results.append(f"❌ Error leaving `{server_id_str}`: {str(e)}")

        embed = discord.Embed(
            title="🚪 Leave Servers Results",
            description="\n".join(results),
            color=discord.Color.orange(),
            timestamp=datetime.utcnow(),
        )

        await ctx.send(embed=embed)

    @commands.command(name="restart")
    @owner_only()
    async def restart_bot(self, ctx):
        """Restart the bot (owner only)."""
        embed = discord.Embed(
            title="🔄 Restarting Bot",
            description="Bot is restarting... Please wait a moment.",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow(),
        )

        await ctx.send(embed=embed)
        logger.info(f"Bot restart initiated by {ctx.author}")

        # Save any pending data
        if hasattr(self.bot, "plugin_manager"):
            await self.bot.plugin_manager.save_registry()

        # Close the bot and exit
        await self.bot.close()

        # Exit with code 1 to trigger restart in Docker/systemd
        os._exit(1)

    @commands.command(name="reload")
    @admin_only()
    async def reload_cog(self, ctx, *, cog_name: str):
        """
        Reload a bot cog or plugin module.

        Usage: !reload <cog_name>
        """
        try:
            # Handle plugin manager reload
            if (
                hasattr(self.bot, "plugin_manager")
                and cog_name in self.bot.plugin_manager.plugins
            ):
                success = await self.bot.plugin_manager.reload_plugin(cog_name)

                if success:
                    embed = discord.Embed(
                        title="✅ Plugin Reloaded",
                        description=f"Successfully reloaded plugin `{cog_name}`",
                        color=discord.Color.green(),
                        timestamp=datetime.utcnow(),
                    )
                else:
                    plugin_info = self.bot.plugin_manager.get_plugin_info(cog_name)
                    error_msg = (
                        str(plugin_info.error)
                        if plugin_info and plugin_info.error
                        else "Unknown error"
                    )
                    embed = discord.Embed(
                        title="❌ Plugin Reload Failed",
                        description=f"Failed to reload plugin `{cog_name}`: {error_msg}",
                        color=discord.Color.red(),
                        timestamp=datetime.utcnow(),
                    )
            else:
                # Traditional cog reload
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
        """Show detailed bot status and diagnostic information."""
        embed = discord.Embed(
            title="📊 Bot Status",
            description="Comprehensive system status and diagnostics",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )

        # Basic stats
        embed.add_field(name="Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Users", value=len(self.bot.users), inline=True)
        embed.add_field(
            name="Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True
        )

        # Uptime
        uptime = datetime.utcnow() - self.start_time
        embed.add_field(name="Uptime", value=self._format_uptime(uptime), inline=True)

        # Plugin/Cog stats
        if hasattr(self.bot, "plugin_manager"):
            stats = self.bot.plugin_manager.get_plugin_stats()
            embed.add_field(
                name="Plugins",
                value=f"{stats['loaded_plugins']}/{stats['total_plugins']} ({stats['success_rate']})",
                inline=True,
            )
        else:
            embed.add_field(name="Loaded Cogs", value=len(self.bot.cogs), inline=True)

        embed.add_field(name="Commands", value=len(self.bot.commands), inline=True)
        embed.add_field(name="Core Version", value="v2.0.0", inline=True)

        # Get database stats if available
        try:
            if hasattr(self.bot, "database"):
                pending_reminders = await self.bot.database.get_pending_reminders()
                reminder_count = len(pending_reminders)
                embed.add_field(
                    name="Pending Reminders", value=reminder_count, inline=True
                )
        except Exception:
            pass

        # Memory usage (if psutil is available)
        try:
            import psutil

            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            embed.add_field(
                name="Memory Usage", value=f"{memory_mb:.1f} MB", inline=True
            )
        except ImportError:
            pass

        await ctx.send(embed=embed)

    @commands.command(name="shutdown")
    @owner_only()
    async def shutdown(self, ctx):
        """Gracefully shutdown the bot (owner only)."""
        embed = discord.Embed(
            title="👋 Shutting Down",
            description="Bot is shutting down gracefully...",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow(),
        )

        await ctx.send(embed=embed)
        logger.info(f"Bot shutdown initiated by {ctx.author}")

        # Save any pending data
        if hasattr(self.bot, "plugin_manager"):
            await self.bot.plugin_manager.save_registry()

        await self.bot.close()

    def _format_uptime(self, uptime: timedelta) -> str:
        """Format uptime timedelta as a readable string."""
        total_seconds = int(uptime.total_seconds())
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")

        return " ".join(parts)


async def setup(bot):
    """Setup function to add the CoreCog to the bot."""
    await bot.add_cog(CoreCog(bot))
    logger.info("Core cog loaded successfully - Essential bot functionality available")
