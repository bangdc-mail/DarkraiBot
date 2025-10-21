# DarkraiBot Plugins Directory

This directory contains custom plugins for DarkraiBot. Plugins are dynamically loadable extensions that add new functionality to the bot.

## Plugin Structure

### Basic Plugin Template

```python
# Plugin: Your Plugin Name
# Version: 1.0.0
# Author: Your Name
# Description: What your plugin does
# Dependencies: other_plugin,another_plugin
# Permissions: user

"""
Plugin docstring describing functionality.
"""

import logging
import discord
from discord.ext import commands
from utils.permissions import user_level, admin_only, owner_only

logger = logging.getLogger(__name__)

class YourPluginCog(commands.Cog):
    """Plugin description."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="yourcommand")
    @user_level()  # Permission decorator
    async def your_command(self, ctx):
        """Command description."""
        await ctx.send("Hello from your plugin!")

async def setup(bot):
    """Required setup function."""
    await bot.add_cog(YourPluginCog(bot))
```

## Plugin Metadata

Add metadata at the top of your plugin file using comments:

- `Plugin:` - Display name for the plugin
- `Version:` - Plugin version (e.g., 1.0.0)
- `Author:` - Your name or organization
- `Description:` - Brief description of functionality
- `Dependencies:` - Required plugins (comma-separated)
- `Permissions:` - Minimum permission level (user, mod, admin, owner)

## Permission Decorators

Use these decorators to control command access:

- `@user_level()` - All server members can use
- `@mod_only()` - Moderators and above
- `@admin_only()` - Administrators and above
- `@owner_only()` - Bot owner only

## Plugin Management

### Loading Plugins

```
!plugin load my_plugin     # Load a specific plugin
!plugin reload my_plugin   # Reload a plugin
!plugin unload my_plugin   # Unload a plugin
```

### Plugin Discovery

```
!plugin rescan    # Rediscover plugins
!plugin list      # Show all plugins
!plugin info name # Show plugin details
```

## Development Workflow

### 1. Create Your Plugin

Use the development utility to create a template:

```bash
python dev.py plugin my_new_plugin
```

Or create manually in this directory.

### 2. Test Your Plugin

1. Save your plugin file in this directory
2. Use `!plugin rescan` to discover it
3. Use `!plugin load your_plugin` to load it
4. Test your commands
5. Use `!plugin reload your_plugin` to reload after changes

### 3. Plugin Features

#### Commands

```python
@commands.command(name="mycommand")
@user_level()
async def my_command(self, ctx, arg: str = None):
    """Command with optional argument."""
    await ctx.send(f"You said: {arg}")

# Command groups
@commands.group(name="mygroup", invoke_without_command=True)
@user_level()
async def my_group(self, ctx):
    """Group command."""
    await ctx.send("Use subcommands!")

@my_group.command(name="subcommand")
@user_level()
async def my_subcommand(self, ctx):
    """Subcommand."""
    await ctx.send("Subcommand executed!")
```

#### Event Listeners

```python
@commands.Cog.listener()
async def on_message(self, message):
    """Listen for messages."""
    if message.author.bot:
        return
    # Your logic here

@commands.Cog.listener()
async def on_member_join(self, member):
    """Welcome new members."""
    # Your logic here
```

#### Database Access

```python
# Access bot's database
async def my_function(self):
    # Use the bot's database instance
    await self.bot.database.some_method()
```

#### Configuration Access

```python
# Access bot configuration
def my_function(self):
    prefix = self.bot.config.COMMAND_PREFIX
    owner_id = self.bot.config.OWNER_ID
```

## Best Practices

### Error Handling

```python
@commands.command()
@user_level()
async def my_command(self, ctx):
    try:
        # Your command logic
        pass
    except Exception as e:
        await ctx.send(f"❌ Error: {str(e)}")
        logger.error(f"Error in my_command: {e}")
```

### Embeds

```python
embed = discord.Embed(
    title="Command Title",
    description="Description text",
    color=discord.Color.blue(),
    timestamp=datetime.utcnow()
)

embed.add_field(
    name="Field Name",
    value="Field Value",
    inline=True
)

await ctx.send(embed=embed)
```

### Logging

```python
import logging
logger = logging.getLogger(__name__)

# Log important events
logger.info("Plugin loaded successfully")
logger.error(f"Error occurred: {error}")
logger.warning("Warning message")
```

### User Input Validation

```python
@commands.command()
@user_level()
async def my_command(self, ctx, number: int):
    """Command that expects an integer."""
    if number < 0:
        await ctx.send("❌ Number must be positive!")
        return

    await ctx.send(f"You entered: {number}")
```

## Plugin Examples

Check out the `example.py` plugin in this directory for a comprehensive example showing:

- Basic commands
- Command groups
- Permission decorators
- Event listeners
- Embed responses
- User input handling

## Troubleshooting

### Common Issues

1. **Plugin won't load:**

   - Check syntax errors in your code
   - Ensure the `setup(bot)` function exists
   - Check the plugin metadata format

2. **Commands not working:**

   - Verify permission decorators are correct
   - Check command names don't conflict
   - Ensure proper indentation

3. **Import errors:**
   - Make sure all required imports are present
   - Check the `utils` module imports

### Debug Commands

```
!plugin info my_plugin    # Check plugin status and errors
!plugin status            # Plugin system statistics
```

## Guidelines

1. **Naming:** Use descriptive, lowercase names for plugin files
2. **Commands:** Use clear, intuitive command names
3. **Help:** Always include docstrings for commands
4. **Permissions:** Use appropriate permission levels
5. **Error Handling:** Handle errors gracefully
6. **Logging:** Log important events and errors

## Advanced Features

### Task Loops

```python
from discord.ext import tasks

class MyPlugin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.my_task.start()

    def cog_unload(self):
        self.my_task.cancel()

    @tasks.loop(minutes=5)
    async def my_task(self):
        """Task that runs every 5 minutes."""
        # Your periodic task logic

    @my_task.before_loop
    async def before_my_task(self):
        await self.bot.wait_until_ready()
```

### Database Operations

```python
# If you need custom database operations
async def store_data(self, user_id: int, data: str):
    # Use bot's database connection
    query = "INSERT INTO my_table (user_id, data) VALUES (?, ?)"
    # Implementation depends on your database setup
```

Happy plugin development! 🔌
