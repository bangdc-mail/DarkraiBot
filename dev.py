#!/usr/bin/env python3
"""
Development utility script for DarkraiBot.
Provides various development commands and utilities.
"""

import os
import sys
import asyncio
import argparse
import subprocess
from pathlib import Path

# Add the bot directory to Python path
bot_dir = Path(__file__).parent / "bot"
sys.path.insert(0, str(bot_dir))


def check_requirements():
    """Check if all required packages are installed."""
    requirements_file = Path(__file__).parent / "requirements.txt"

    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "check"], capture_output=True, text=True
        )

        if result.returncode != 0:
            print("❌ Some packages have dependency conflicts:")
            print(result.stdout)
            print(result.stderr)
            return False

        print("✅ All packages are properly installed")
        return True

    except Exception as e:
        print(f"❌ Error checking requirements: {e}")
        return False


def install_requirements():
    """Install requirements from requirements.txt."""
    requirements_file = Path(__file__).parent / "requirements.txt"

    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        return False

    try:
        print("📦 Installing requirements...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
            check=True,
        )

        print("✅ Requirements installed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install requirements: {e}")
        return False


def create_env_file():
    """Create .env file from template."""
    env_example = Path(__file__).parent / ".env.example"
    env_file = Path(__file__).parent / ".env"

    if env_file.exists():
        print("⚠️ .env file already exists")
        return True

    if not env_example.exists():
        print("❌ .env.example template not found")
        return False

    try:
        env_file.write_text(env_example.read_text())
        print("✅ Created .env file from template")
        print("📝 Please edit .env file and fill in your bot token and other values")
        return True

    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def check_redis():
    """Check if Redis is running locally."""
    try:
        import redis

        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis is running locally")
        return True
    except Exception as e:
        print(f"❌ Redis not available locally: {e}")
        print("💡 Install Redis or use Docker compose for Redis")
        return False


def setup_dev_environment():
    """Set up the complete development environment."""
    print("🚀 Setting up development environment...\n")

    steps = [
        ("Creating .env file", create_env_file),
        ("Installing requirements", install_requirements),
        ("Checking requirements", check_requirements),
        ("Checking Redis", check_redis),
    ]

    success_count = 0
    for step_name, step_func in steps:
        print(f"📋 {step_name}...")
        if step_func():
            success_count += 1
        print()

    print(f"✅ Setup completed: {success_count}/{len(steps)} steps successful")

    if success_count == len(steps):
        print("🎉 Development environment is ready!")
        print("💡 Run `python dev.py run` to start the bot")
    else:
        print("⚠️ Some setup steps failed. Please check the errors above.")


async def run_bot():
    """Run the bot in development mode."""
    try:
        from main import main

        await main()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error running bot: {e}")


def validate_env():
    """Validate .env configuration."""
    env_file = Path(__file__).parent / ".env"

    if not env_file.exists():
        print("❌ .env file not found. Run `python dev.py setup` first.")
        return False

    # Load environment variables
    try:
        from dotenv import load_dotenv

        load_dotenv(env_file)
    except ImportError:
        print("❌ python-dotenv not installed. Run `pip install python-dotenv`")
        return False

    required_vars = ["BOT_TOKEN", "OWNER_ID"]
    missing_vars = []

    for var in required_vars:
        value = os.getenv(var)
        if not value or value.startswith("your_"):
            missing_vars.append(var)

    if missing_vars:
        print("❌ Missing or invalid environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n📝 Please edit .env file and set proper values")
        return False

    print("✅ Environment configuration is valid")
    return True


def lint_code():
    """Run code linting."""
    bot_dir = Path(__file__).parent / "bot"

    try:
        # Try to run flake8 if available
        result = subprocess.run(
            [sys.executable, "-m", "flake8", str(bot_dir), "--max-line-length=100"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            print("✅ Code passes linting checks")
        else:
            print("⚠️ Linting issues found:")
            print(result.stdout)

    except FileNotFoundError:
        print("💡 flake8 not installed. Run `pip install flake8` for code linting")


def create_plugin_template(plugin_name: str):
    """Create a new plugin template."""
    plugins_dir = Path(__file__).parent / "bot" / "plugins"
    plugins_dir.mkdir(exist_ok=True)

    plugin_file = plugins_dir / f"{plugin_name}.py"

    if plugin_file.exists():
        print(f"❌ Plugin {plugin_name} already exists")
        return False

    template = f'''# Plugin: {plugin_name.title()}
# Version: 1.0.0
# Author: Your Name
# Description: Description of your plugin
# Dependencies:
# Permissions: user

"""
{plugin_name.title()} Plugin - Description of your plugin.
"""

import logging

import discord
from discord.ext import commands

from utils.permissions import user_level, admin_only, owner_only

logger = logging.getLogger(__name__)


class {plugin_name.title()}Cog(commands.Cog):
    """Your plugin description."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="{plugin_name}")
    @user_level()
    async def {plugin_name}_command(self, ctx):
        """Your command description."""
        await ctx.send(f"Hello from {{plugin_name}} plugin!")

    @commands.group(name="{plugin_name[:4]}", invoke_without_command=True)
    @user_level()
    async def {plugin_name[:4]}_group(self, ctx):
        """Group command example."""
        await ctx.send("Use subcommands with this group!")

    @{plugin_name[:4]}_group.command(name="info")
    @user_level()
    async def {plugin_name[:4]}_info(self, ctx):
        """Show plugin information."""
        embed = discord.Embed(
            title=f"🔌 {{plugin_name.title()}} Plugin",
            description="Plugin information",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Version",
            value="1.0.0",
            inline=True
        )

        await ctx.send(embed=embed)


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog({plugin_name.title()}Cog(bot))
'''

    try:
        plugin_file.write_text(template)
        print(f"✅ Created plugin template: {plugin_file}")
        print(f"💡 Use `!plugin load {plugin_name}` to load your plugin")
        return True
    except Exception as e:
        print(f"❌ Failed to create plugin: {e}")
        return False


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="DarkraiBot Development Utilities")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Setup command
    setup_parser = subparsers.add_parser("setup", help="Set up development environment")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run the bot")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate environment")

    # Lint command
    lint_parser = subparsers.add_parser("lint", help="Run code linting")

    # Check command
    check_parser = subparsers.add_parser(
        "check", help="Check requirements and dependencies"
    )

    # Plugin command
    plugin_parser = subparsers.add_parser("plugin", help="Create a new plugin template")
    plugin_parser.add_argument("name", help="Plugin name")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == "setup":
        setup_dev_environment()
    elif args.command == "run":
        if not validate_env():
            return
        asyncio.run(run_bot())
    elif args.command == "validate":
        validate_env()
    elif args.command == "lint":
        lint_code()
    elif args.command == "check":
        check_requirements()
    elif args.command == "plugin":
        create_plugin_template(args.name)


if __name__ == "__main__":
    main()
