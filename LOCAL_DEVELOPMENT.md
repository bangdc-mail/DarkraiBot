# Local Development Setup

This guide covers setting up DarkraiBot for local development without Docker.

## Prerequisites

- Python 3.9 or higher
- Git
- Redis server (optional, for full functionality)

## Quick Setup

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd DarkraiBot

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 2. Automated Setup

Use the development utility script for easy setup:

```bash
# Run the setup command
python dev.py setup
```

This will:

- Create `.env` file from template
- Install all required dependencies
- Check for Redis availability
- Validate the setup

### 3. Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env file with your values
nano .env  # or your preferred editor
```

### 4. Configure Environment Variables

Edit the `.env` file and set the following required values:

```env
# Required
BOT_TOKEN=your_discord_bot_token_here
OWNER_ID=your_discord_user_id

# Optional (with defaults)
COMMAND_PREFIX=!
LOG_LEVEL=INFO
ADMIN_ROLE_NAMES=admin,administrator,mod
MOD_ROLE_NAMES=moderator,mod
```

### 5. Redis Setup (Optional)

Redis is optional but recommended for full functionality.

#### Option A: Local Redis Installation

**macOS (using Homebrew):**

```bash
brew install redis
brew services start redis
```

**Ubuntu/Debian:**

```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**Windows:**

- Download Redis from: https://github.com/microsoftarchive/redis/releases
- Or use WSL with Linux instructions

#### Option B: Docker Redis Only

If you only want Redis in Docker:

```bash
docker run -d -p 6379:6379 --name redis redis:alpine
```

#### Option C: Without Redis

The bot will work without Redis, but some features may be limited. Set in `.env`:

```env
REDIS_URL=none
```

## Running the Bot

### Development Mode

```bash
# Validate configuration first
python dev.py validate

# Run the bot
python dev.py run

# Or run directly
cd bot
python main.py
```

### Development Utilities

The `dev.py` script provides several utilities:

```bash
# Setup development environment
python dev.py setup

# Run the bot
python dev.py run

# Validate environment configuration
python dev.py validate

# Check dependencies
python dev.py check

# Create a new plugin template
python dev.py plugin my_new_plugin

# Run code linting (requires flake8)
python dev.py lint
```

## Project Structure for Development

```
DarkraiBot/
├── bot/                    # Bot source code
│   ├── main.py            # Main entry point
│   ├── cogs/              # Built-in cogs
│   │   ├── general.py
│   │   ├── settings.py
│   │   ├── reminders.py
│   │   ├── timezone.py
│   │   ├── ip_check.py
│   │   └── plugin_management.py
│   ├── plugins/           # Custom plugins directory
│   └── utils/             # Utility modules
│       ├── config.py
│       ├── permissions.py
│       ├── database.py
│       ├── time_parser.py
│       └── plugin_manager.py
├── data/                  # Local data storage
│   ├── bot.db            # SQLite database
│   ├── bot.log           # Log files
│   └── plugin_registry.json
├── dev.py                 # Development utilities
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
└── .env.example          # Environment template
```

## Plugin Development

### Creating a New Plugin

1. **Use the template generator:**

   ```bash
   python dev.py plugin my_plugin
   ```

2. **Edit the generated plugin** in `bot/plugins/my_plugin.py`

3. **Load the plugin** using bot commands:
   ```
   !plugin rescan
   !plugin load my_plugin
   ```

### Plugin Template Structure

```python
# Plugin: My Plugin
# Version: 1.0.0
# Author: Your Name
# Description: What your plugin does
# Dependencies: other_plugin,another_plugin
# Permissions: user

import discord
from discord.ext import commands
from utils.permissions import user_level, admin_only

class MyPluginCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @user_level()
    async def my_command(self, ctx):
        await ctx.send("Hello from my plugin!")

async def setup(bot):
    await bot.add_cog(MyPluginCog(bot))
```

### Plugin Metadata

Add metadata at the top of your plugin files:

- `Plugin:` - Display name
- `Version:` - Plugin version
- `Author:` - Your name
- `Description:` - What the plugin does
- `Dependencies:` - Required other plugins (comma-separated)
- `Permissions:` - Required permission level

## Development Workflow

### 1. Making Changes

1. Edit code in your preferred editor
2. The bot supports hot-reloading via plugin commands:
   ```
   !plugin reload my_plugin
   !plugin reload  # Reload all plugins
   ```

### 2. Testing

```bash
# Validate your code
python dev.py validate

# Check for linting issues
python dev.py lint

# Test with the bot running
python dev.py run
```

### 3. Database Management

The bot automatically creates and manages the SQLite database. For development:

- Database location: `data/bot.db`
- View with any SQLite browser
- Schema is auto-created on first run

## Common Development Tasks

### Adding a New Command

1. Create or edit a plugin/cog file
2. Add your command with proper decorators:
   ```python
   @commands.command()
   @user_level()  # or @admin_only(), @owner_only()
   async def my_command(self, ctx, arg: str = None):
       """Command description."""
       await ctx.send(f"You said: {arg}")
   ```
3. Reload the plugin: `!plugin reload plugin_name`

### Adding Database Tables

1. Edit `bot/utils/database.py`
2. Add your table schema to `initialize()` method
3. Add methods to interact with your table
4. Restart the bot to apply schema changes

### Environment-Specific Configuration

Use `utils.config.Config` to access environment variables:

```python
from utils.config import Config

# Access configuration
prefix = Config.COMMAND_PREFIX
token = Config.BOT_TOKEN
```

## Troubleshooting

### Common Issues

1. **Import Errors:**

   - Make sure you're in the project root
   - Virtual environment is activated
   - All dependencies are installed

2. **Permission Errors:**

   - Check file permissions
   - Make sure data directory is writable

3. **Redis Connection:**

   - Check if Redis is running: `redis-cli ping`
   - Verify Redis URL in .env

4. **Bot Token Issues:**
   - Verify token in .env file
   - Check bot permissions in Discord Developer Portal

### Logs and Debugging

- Log file location: `data/bot.log`
- Set `LOG_LEVEL=DEBUG` in .env for detailed logging
- Use `logger.info()`, `logger.error()` in your code

### Getting Help

1. Check the logs in `data/bot.log`
2. Use `python dev.py validate` to check configuration
3. Test individual components with the development utilities

## Production Deployment

When ready for production, you can:

1. **Use Docker** (recommended):

   ```bash
   docker compose up -d
   ```

2. **Deploy to a server** with systemd, pm2, or similar process manager

3. **Use a cloud service** like Heroku, Railway, or DigitalOcean

The bot is designed to work the same way in both development and production environments.
