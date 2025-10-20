#!/usr/bin/env python3
"""
Discord Bot Main Entry Point
A modular Discord bot with role-based permissions and Docker support.
"""

import os
import asyncio
import logging
from pathlib import Path

import discord
from discord.ext import commands

from utils.config import Config
from utils.permissions import PermissionManager
from utils.database import Database

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("/app/data/bot.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class ModularBot(commands.Bot):
    """Main bot class with modular cog loading."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True

        super().__init__(
            command_prefix=self.get_prefix, intents=intents, help_command=None
        )

        self.config = Config()
        self.permission_manager = PermissionManager(self)
        self.database = Database()

    async def get_prefix(self, message):
        """Get the command prefix for a message."""
        # Default prefix for DMs
        if not message.guild:
            return Config.COMMAND_PREFIX

        try:
            # Get guild-specific prefix from database
            settings = await self.database.get_guild_settings(message.guild.id)
            return settings["command_prefix"]
        except Exception as e:
            logger.warning(f"Failed to get prefix for guild {message.guild.id}: {e}")
            return Config.COMMAND_PREFIX

    async def setup_hook(self):
        """Called when the bot is starting up."""
        logger.info("Setting up bot...")

        # Initialize database
        await self.database.initialize()

        # Load all cogs
        await self.load_cogs()

        logger.info("Bot setup completed!")

    async def load_cogs(self):
        """Load all cogs from the cogs directory."""
        cogs_dir = Path(__file__).parent / "cogs"

        for cog_file in cogs_dir.glob("*.py"):
            if cog_file.name.startswith("_"):
                continue

            cog_name = f"cogs.{cog_file.stem}"
            try:
                await self.load_extension(cog_name)
                logger.info(f"Loaded cog: {cog_name}")
            except Exception as e:
                logger.error(f"Failed to load cog {cog_name}: {e}")

    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f"Bot {self.user} is ready!")
        logger.info(f"Bot is in {len(self.guilds)} guilds")

        # Set bot status
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, name=f"{Config.COMMAND_PREFIX}help"
            )
        )

    async def on_command_error(self, ctx, error):
        """Global error handler."""
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ You don't have permission to use this command.")
            return

        if isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument: {error}")
            return

        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
            return

        logger.error(f"Unhandled error in command {ctx.command}: {error}")
        await ctx.send("❌ An unexpected error occurred. Please try again later.")


async def main():
    """Main function to run the bot."""
    bot = ModularBot()

    try:
        await bot.start(Config.BOT_TOKEN)
    except KeyboardInterrupt:
        logger.info("Bot shutdown requested...")
    except Exception as e:
        logger.error(f"Bot crashed: {e}")
    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
