# Plugin: Plugin Management
# Version: 1.0.0
# Author: DarkraiBot
# Description: Commands for managing bot plugins/cogs dynamically
# Dependencies:
# Permissions: admin

"""
Plugin Management Cog - Admin commands for managing bot plugins/cogs.
"""

import logging
from typing import List, Optional

import discord
from discord.ext import commands

from utils.permissions import admin_only, owner_only

logger = logging.getLogger(__name__)


class PluginManagementCog(commands.Cog):
    """Cog for managing bot plugins and extensions."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        name="plugin", aliases=["plugins", "cog", "cogs"], invoke_without_command=True
    )
    @admin_only()
    async def plugin_group(self, ctx):
        """
        Plugin management commands.

        Available subcommands:
        - plugin list - List all available plugins
        - plugin load <name> - Load a plugin
        - plugin unload <name> - Unload a plugin
        - plugin reload <name> - Reload a plugin
        - plugin info <name> - Get plugin information
        - plugin status - Show plugin statistics
        """
        embed = discord.Embed(
            title="🔌 Plugin Management",
            description="Manage bot plugins and extensions dynamically.",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="Available Commands",
            value=(
                f"`{ctx.prefix}plugin list` - List all plugins\n"
                f"`{ctx.prefix}plugin load <name>` - Load a plugin\n"
                f"`{ctx.prefix}plugin unload <name>` - Unload a plugin\n"
                f"`{ctx.prefix}plugin reload <name>` - Reload a plugin\n"
                f"`{ctx.prefix}plugin info <name>` - Plugin information\n"
                f"`{ctx.prefix}plugin status` - System statistics\n"
                f"`{ctx.prefix}plugin rescan` - Rediscover plugins"
            ),
            inline=False,
        )

        # Show quick stats
        stats = self.bot.plugin_manager.get_plugin_stats()
        embed.add_field(
            name="Quick Stats",
            value=(
                f"**Total**: {stats['total_plugins']}\n"
                f"**Loaded**: {stats['loaded_plugins']}\n"
                f"**Success Rate**: {stats['success_rate']}"
            ),
            inline=True,
        )

        await ctx.send(embed=embed)

    @plugin_group.command(name="list")
    @admin_only()
    async def list_plugins(self, ctx):
        """List all available plugins with their status."""
        plugins = self.bot.plugin_manager.get_available_plugins()

        if not plugins:
            await ctx.send(
                "❌ No plugins found. Use `!plugin rescan` to discover plugins."
            )
            return

        # Group plugins by status
        loaded_plugins = [p for p in plugins if p.loaded]
        unloaded_plugins = [p for p in plugins if not p.loaded and not p.error]
        failed_plugins = [p for p in plugins if p.error]

        embed = discord.Embed(title="📋 Available Plugins", color=discord.Color.blue())

        if loaded_plugins:
            loaded_list = []
            for plugin in loaded_plugins:
                name = plugin.name
                if plugin.metadata.get("version"):
                    name += f" v{plugin.metadata['version']}"
                loaded_list.append(f"✅ {name}")

            embed.add_field(
                name=f"Loaded ({len(loaded_plugins)})",
                value="\n".join(loaded_list[:10])
                + ("\n..." if len(loaded_list) > 10 else ""),
                inline=False,
            )

        if unloaded_plugins:
            unloaded_list = []
            for plugin in unloaded_plugins:
                name = plugin.name
                if plugin.metadata.get("version"):
                    name += f" v{plugin.metadata['version']}"
                unloaded_list.append(f"⏸️ {name}")

            embed.add_field(
                name=f"Available ({len(unloaded_plugins)})",
                value="\n".join(unloaded_list[:10])
                + ("\n..." if len(unloaded_list) > 10 else ""),
                inline=False,
            )

        if failed_plugins:
            failed_list = []
            for plugin in failed_plugins:
                name = plugin.name
                if plugin.metadata.get("version"):
                    name += f" v{plugin.metadata['version']}"
                failed_list.append(f"❌ {name}")

            embed.add_field(
                name=f"Failed ({len(failed_plugins)})",
                value="\n".join(failed_list[:10])
                + ("\n..." if len(failed_list) > 10 else ""),
                inline=False,
            )

        embed.set_footer(text=f"Total: {len(plugins)} plugins")
        await ctx.send(embed=embed)

    @plugin_group.command(name="load")
    @admin_only()
    async def load_plugin(self, ctx, plugin_name: str):
        """Load a specific plugin."""
        # Check if plugin exists
        if plugin_name not in self.bot.plugin_manager.plugins:
            await ctx.send(
                f"❌ Plugin `{plugin_name}` not found. Use `!plugin list` to see available plugins."
            )
            return

        plugin_info = self.bot.plugin_manager.get_plugin_info(plugin_name)

        # Check if already loaded
        if plugin_info.loaded:
            await ctx.send(
                f"⚠️ Plugin `{plugin_name}` is already loaded. Use `!plugin reload` to reload it."
            )
            return

        # Check dependencies
        missing_deps = self.bot.plugin_manager.check_dependencies(plugin_name)
        if missing_deps:
            await ctx.send(
                f"❌ Cannot load `{plugin_name}`: Missing dependencies: {', '.join(missing_deps)}"
            )
            return

        # Attempt to load
        success = await self.bot.plugin_manager.load_plugin(plugin_name)

        if success:
            embed = discord.Embed(
                title="✅ Plugin Loaded",
                description=f"Successfully loaded plugin `{plugin_name}`",
                color=discord.Color.green(),
            )

            if plugin_info.metadata:
                if plugin_info.metadata.get("description"):
                    embed.add_field(
                        name="Description",
                        value=plugin_info.metadata["description"],
                        inline=False,
                    )

                if plugin_info.metadata.get("version"):
                    embed.add_field(
                        name="Version",
                        value=plugin_info.metadata["version"],
                        inline=True,
                    )

            await ctx.send(embed=embed)
        else:
            error_msg = str(plugin_info.error) if plugin_info.error else "Unknown error"
            await ctx.send(f"❌ Failed to load plugin `{plugin_name}`: {error_msg}")

    @plugin_group.command(name="unload")
    @admin_only()
    async def unload_plugin(self, ctx, plugin_name: str):
        """Unload a specific plugin."""
        # Check if plugin exists
        if plugin_name not in self.bot.plugin_manager.plugins:
            await ctx.send(f"❌ Plugin `{plugin_name}` not found.")
            return

        plugin_info = self.bot.plugin_manager.get_plugin_info(plugin_name)

        # Check if loaded
        if not plugin_info.loaded:
            await ctx.send(f"⚠️ Plugin `{plugin_name}` is not currently loaded.")
            return

        # Prevent unloading critical plugins
        critical_plugins = ["general", "settings", "plugin_management"]
        if plugin_name in critical_plugins:
            await ctx.send(f"❌ Cannot unload critical plugin `{plugin_name}`.")
            return

        # Attempt to unload
        success = await self.bot.plugin_manager.unload_plugin(plugin_name)

        if success:
            embed = discord.Embed(
                title="✅ Plugin Unloaded",
                description=f"Successfully unloaded plugin `{plugin_name}`",
                color=discord.Color.orange(),
            )
            await ctx.send(embed=embed)
        else:
            error_msg = str(plugin_info.error) if plugin_info.error else "Unknown error"
            await ctx.send(f"❌ Failed to unload plugin `{plugin_name}`: {error_msg}")

    @plugin_group.command(name="reload")
    @admin_only()
    async def reload_plugin(self, ctx, plugin_name: str = None):
        """Reload a specific plugin or all plugins."""
        if plugin_name:
            # Reload specific plugin
            if plugin_name not in self.bot.plugin_manager.plugins:
                await ctx.send(f"❌ Plugin `{plugin_name}` not found.")
                return

            success = await self.bot.plugin_manager.reload_plugin(plugin_name)

            if success:
                embed = discord.Embed(
                    title="✅ Plugin Reloaded",
                    description=f"Successfully reloaded plugin `{plugin_name}`",
                    color=discord.Color.green(),
                )
                await ctx.send(embed=embed)
            else:
                plugin_info = self.bot.plugin_manager.get_plugin_info(plugin_name)
                error_msg = (
                    str(plugin_info.error) if plugin_info.error else "Unknown error"
                )
                await ctx.send(
                    f"❌ Failed to reload plugin `{plugin_name}`: {error_msg}"
                )
        else:
            # Reload all plugins
            async with ctx.typing():
                results = await self.bot.plugin_manager.reload_all_plugins()

            success_count = sum(1 for success in results.values() if success)
            total_count = len(results)

            embed = discord.Embed(
                title="🔄 Mass Plugin Reload",
                description=f"Reloaded {success_count}/{total_count} plugins successfully",
                color=discord.Color.blue(),
            )

            if success_count < total_count:
                failed = [name for name, success in results.items() if not success]
                embed.add_field(
                    name="Failed Plugins",
                    value=", ".join(failed[:10]) + ("..." if len(failed) > 10 else ""),
                    inline=False,
                )

            await ctx.send(embed=embed)

    @plugin_group.command(name="info")
    @admin_only()
    async def plugin_info(self, ctx, plugin_name: str):
        """Get detailed information about a plugin."""
        plugin_info = self.bot.plugin_manager.get_plugin_info(plugin_name)

        if not plugin_info:
            await ctx.send(f"❌ Plugin `{plugin_name}` not found.")
            return

        embed = discord.Embed(
            title=f"🔌 Plugin: {plugin_info.name}",
            color=discord.Color.green() if plugin_info.loaded else discord.Color.red(),
        )

        embed.add_field(
            name="Status",
            value=(
                "✅ Loaded"
                if plugin_info.loaded
                else ("❌ Error" if plugin_info.error else "⏸️ Not Loaded")
            ),
            inline=True,
        )

        embed.add_field(name="Module Path", value=f"`{plugin_info.path}`", inline=True)

        if plugin_info.load_time:
            embed.add_field(
                name="Last Loaded",
                value=f"<t:{int(plugin_info.load_time.timestamp())}:R>",
                inline=True,
            )

        # Metadata fields
        metadata = plugin_info.metadata
        if metadata:
            if metadata.get("description"):
                embed.add_field(
                    name="Description", value=metadata["description"], inline=False
                )

            if metadata.get("version"):
                embed.add_field(name="Version", value=metadata["version"], inline=True)

            if metadata.get("author"):
                embed.add_field(name="Author", value=metadata["author"], inline=True)

            if metadata.get("dependencies"):
                deps = metadata["dependencies"]
                embed.add_field(
                    name="Dependencies",
                    value=", ".join(f"`{dep}`" for dep in deps) if deps else "None",
                    inline=False,
                )

            if metadata.get("required_permissions"):
                embed.add_field(
                    name="Required Permissions",
                    value=metadata["required_permissions"],
                    inline=True,
                )

        if plugin_info.error:
            embed.add_field(
                name="Error",
                value=f"```\n{str(plugin_info.error)[:1000]}\n```",
                inline=False,
            )

        await ctx.send(embed=embed)

    @plugin_group.command(name="status")
    @admin_only()
    async def plugin_status(self, ctx):
        """Show plugin system status and statistics."""
        stats = self.bot.plugin_manager.get_plugin_stats()
        plugins = self.bot.plugin_manager.get_available_plugins()

        embed = discord.Embed(
            title="📊 Plugin System Status", color=discord.Color.blue()
        )

        embed.add_field(
            name="Statistics",
            value=(
                f"**Total Plugins**: {stats['total_plugins']}\n"
                f"**Loaded**: {stats['loaded_plugins']}\n"
                f"**Failed**: {stats['failed_plugins']}\n"
                f"**Success Rate**: {stats['success_rate']}"
            ),
            inline=True,
        )

        # Plugin directories
        plugin_dirs = [
            str(d) for d in self.bot.plugin_manager.plugin_dirs if d.exists()
        ]
        embed.add_field(
            name="Plugin Directories",
            value="\n".join(f"`{d}`" for d in plugin_dirs) if plugin_dirs else "None",
            inline=False,
        )

        # Recent errors
        failed_plugins = [p for p in plugins if p.error]
        if failed_plugins:
            error_list = []
            for plugin in failed_plugins[:5]:
                error_str = str(plugin.error)[:100]
                error_list.append(f"**{plugin.name}**: {error_str}")

            embed.add_field(
                name="Recent Errors", value="\n".join(error_list), inline=False
            )

        await ctx.send(embed=embed)

    @plugin_group.command(name="rescan")
    @admin_only()
    async def rescan_plugins(self, ctx):
        """Rediscover plugins in plugin directories."""
        async with ctx.typing():
            discovered = self.bot.plugin_manager.discover_plugins()
            await self.bot.plugin_manager.save_registry()

        embed = discord.Embed(
            title="🔍 Plugin Discovery",
            description=f"Discovered {len(discovered)} plugins",
            color=discord.Color.green(),
        )

        if discovered:
            new_plugins = [p.name for p in discovered if not p.loaded]
            if new_plugins:
                embed.add_field(
                    name="New Plugins Found",
                    value=", ".join(new_plugins[:10])
                    + ("..." if len(new_plugins) > 10 else ""),
                    inline=False,
                )

        await ctx.send(embed=embed)


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(PluginManagementCog(bot))
