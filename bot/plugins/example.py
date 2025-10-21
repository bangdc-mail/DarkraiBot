# Plugin: Example
# Version: 1.0.0
# Author: DarkraiBot Team
# Description: Example plugin showing basic functionality and structure
# Dependencies:
# Permissions: user

"""
Example Plugin - Demonstrates plugin structure and basic functionality.
This serves as a template for creating new plugins.
"""

import logging
from datetime import datetime

import discord
from discord.ext import commands

from utils.permissions import user_level, admin_only, owner_only

logger = logging.getLogger(__name__)


class ExampleCog(commands.Cog):
    """Example plugin demonstrating basic bot functionality."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="example")
    @user_level()
    async def example_command(self, ctx):
        """
        Example command demonstrating basic functionality.

        Usage: !example
        """
        embed = discord.Embed(
            title="🔌 Example Plugin",
            description="This is an example plugin command!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow(),
        )

        embed.add_field(
            name="Purpose",
            value="This plugin demonstrates the basic structure and features available in DarkraiBot plugins.",
            inline=False,
        )

        embed.add_field(
            name="Features Demonstrated",
            value="• Basic command structure\n• Permission decorators\n• Embed responses\n• Plugin metadata",
            inline=False,
        )

        embed.set_footer(text="Example Plugin v1.0.0")

        await ctx.send(embed=embed)

    @commands.group(name="demo", invoke_without_command=True)
    @user_level()
    async def demo_group(self, ctx):
        """
        Example command group.

        Usage: !demo [subcommand]
        """
        embed = discord.Embed(
            title="📋 Demo Command Group",
            description="This is an example of a command group.",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="Available Subcommands",
            value=f"`{ctx.prefix}demo info` - Show plugin information\n`{ctx.prefix}demo admin` - Admin-only example",
            inline=False,
        )

        await ctx.send(embed=embed)

    @demo_group.command(name="info")
    @user_level()
    async def demo_info(self, ctx):
        """Show example plugin information."""
        embed = discord.Embed(
            title="ℹ️ Plugin Information",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )

        embed.add_field(name="Plugin Name", value="Example", inline=True)
        embed.add_field(name="Version", value="1.0.0", inline=True)
        embed.add_field(name="Author", value="DarkraiBot Team", inline=True)

        embed.add_field(
            name="Description",
            value="Example plugin showing basic functionality and structure",
            inline=False,
        )

        embed.add_field(
            name="Commands",
            value=f"`{ctx.prefix}example` - Basic example command\n`{ctx.prefix}demo` - Example command group",
            inline=False,
        )

        # Show user's permission level
        user_level_obj = self.bot.permission_manager.get_user_permission_level(
            ctx.author, ctx.guild
        )
        embed.add_field(
            name="Your Permission Level",
            value=f"`{user_level_obj.name.title()}`",
            inline=True,
        )

        await ctx.send(embed=embed)

    @demo_group.command(name="admin")
    @admin_only()
    async def demo_admin(self, ctx):
        """Example admin-only command."""
        embed = discord.Embed(
            title="👑 Admin Example",
            description="This command is only available to administrators!",
            color=discord.Color.gold(),
            timestamp=datetime.utcnow(),
        )

        embed.add_field(
            name="Permission Level",
            value="This command requires admin permissions or higher.",
            inline=False,
        )

        embed.add_field(
            name="Usage in Plugins",
            value="Use the `@admin_only()` decorator to restrict commands to admins and above.",
            inline=False,
        )

        await ctx.send(embed=embed)

    @commands.command(name="greet")
    @user_level()
    async def greet_user(self, ctx, user: discord.Member = None):
        """
        Greet a user or yourself.

        Usage: !greet [user]
        """
        target = user or ctx.author

        embed = discord.Embed(
            title="👋 Greeting",
            description=f"Hello, {target.mention}!",
            color=discord.Color.green(),
            timestamp=datetime.utcnow(),
        )

        embed.add_field(name="Greeted by", value=ctx.author.mention, inline=True)

        if user and user != ctx.author:
            embed.add_field(name="Target", value=user.mention, inline=True)

        embed.set_thumbnail(url=target.display_avatar.url)

        await ctx.send(embed=embed)

    @commands.command(name="serverinfo")
    @user_level()
    async def server_info(self, ctx):
        """Show information about the current server."""
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        guild = ctx.guild

        embed = discord.Embed(
            title=f"📊 {guild.name}",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow(),
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="Server ID", value=guild.id, inline=True)
        embed.add_field(
            name="Owner",
            value=guild.owner.mention if guild.owner else "Unknown",
            inline=True,
        )
        embed.add_field(name="Members", value=guild.member_count, inline=True)
        embed.add_field(
            name="Text Channels", value=len(guild.text_channels), inline=True
        )
        embed.add_field(
            name="Voice Channels", value=len(guild.voice_channels), inline=True
        )
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)

        embed.add_field(
            name="Created",
            value=f"<t:{int(guild.created_at.timestamp())}:F>",
            inline=False,
        )

        if guild.description:
            embed.add_field(name="Description", value=guild.description, inline=False)

        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_ready(self):
        """Example event listener."""
        logger.info("Example plugin loaded and ready!")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Example message listener.
        Responds to messages containing 'hello bot' (case-insensitive).
        """
        # Ignore bot messages
        if message.author.bot:
            return

        # Check for greeting
        if "hello bot" in message.content.lower():
            await message.add_reaction("👋")


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(ExampleCog(bot))
