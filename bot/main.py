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
from utils.plugin_manager import PluginManager


# Configure logging
def setup_logging():
    """Setup logging for both Docker and local environments."""
    # Determine log file path based on environment
    if os.path.exists("/app/data"):
        # Docker environment
        log_file_path = "/app/data/bot.log"
        data_dir = Path("/app/data")
    else:
        # Local development environment
        project_root = Path(__file__).parent.parent
        data_dir = project_root / "data"
        data_dir.mkdir(exist_ok=True)
        log_file_path = str(data_dir / "bot.log")

    # Get log level from config
    log_level = getattr(logging, Config.LOG_LEVEL, logging.INFO)

    # Configure logging
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.FileHandler(log_file_path), logging.StreamHandler()],
    )

    return data_dir


# Setup logging and get data directory
data_dir = setup_logging()
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
        self.plugin_manager = PluginManager(self, data_dir)

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

        # Initialize plugin manager
        await self.plugin_manager.load_registry()

        # Load all plugins using plugin manager
        await self.load_plugins()

        logger.info("Bot setup completed!")

    async def load_plugins(self):
        """Load all plugins using the plugin manager."""
        logger.info("Loading plugins with plugin manager...")

        results = await self.plugin_manager.load_all_plugins()

        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)

        logger.info(
            f"Plugin loading completed: {success_count}/{total_count} plugins loaded successfully"
        )

        # Log any failed plugins
        for plugin_name, success in results.items():
            if not success:
                plugin_info = self.plugin_manager.get_plugin_info(plugin_name)
                error_msg = (
                    str(plugin_info.error)
                    if plugin_info and plugin_info.error
                    else "Unknown error"
                )
                logger.warning(f"Failed to load plugin {plugin_name}: {error_msg}")

    async def load_cogs(self):
        """Legacy method - redirects to load_plugins for compatibility."""
        await self.load_plugins()

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
