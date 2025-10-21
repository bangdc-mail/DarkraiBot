# Discord Bot - Modular & Dockerized

A simple yet feature-rich self-hosted Discord bot built with Python, featuring role-based permissions, reminder system, and Docker deployment support. You can refer to setup.sh for fast installation script (Please do double check .sh script as it currently may not run without sudo permission enabled).

## Features

### 🔐 Role-Based Permission System

- **Owner Level**: Full bot control (IP checking, shutdown, etc.)
- **Admin Level**: Server management and bot configuration
- **Moderator Level**: Server moderation commands
- **User Level**: Basic commands available to all users

### ⚙️ Settings Management

- Configurable command prefix per server
- Customizable admin and moderator role names
- Guild-specific permission settings
- Easy-to-use settings commands

### ⏰ Reminder System

- Set reminders with flexible time formats
- Persistent storage with SQLite database
- User-friendly time parsing (1h, 30m, tomorrow, etc.)
- List and cancel pending reminders

### 🌐 IP Monitoring

- Owner-only commands to check bot's public IP
- Multiple IP service fallbacks for reliability
- Detailed IP information with geolocation data

### � Dynamic Plugin System

- Hot-reload plugins without restarting the bot
- Plugin discovery and dependency management
- Plugin registry with metadata support
- Easy plugin development with templates
- Runtime plugin loading/unloading

### �🐳 Docker Support

- Fully containerized with Docker Compose
- Redis integration for caching
- Persistent data storage
- Health checks and auto-restart

### 🛠️ Development Features

- Local development support without Docker
- Development utilities and scripts
- Plugin template generator
- Comprehensive logging system

## Quick Start

Choose your preferred setup method:

- **🐳 [Docker Setup](#docker-setup)** - Recommended for production
- **💻 [Local Development](#local-development)** - For development and testing

### Prerequisites

- Docker and Docker Compose (for Docker setup)
- Python 3.9+ (for local development)
- A Discord application/bot token
- Your Discord user ID

## Docker Setup

### Installation

1. **Clone/Download the project**

   ```bash
   cd /path/to/your/project
   ```

2. **Set up environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and fill in your values:

   ```env
   BOT_TOKEN=your_bot_token_here
   OWNER_ID=your_discord_user_id
   COMMAND_PREFIX=!
   ```

3. **(Optional) Change docker compose file accordingly to your needs**

   ```bash
   sudo nano docker-compose.yml
   ```

   Edit file path instead of "./" for build and volumns. Change port to "[your_port]:6379" if default redis port is taken

4. **Start the bot**

   ```bash
   docker compose up -d
   ```

5. **Check logs**
   ```bash
   docker compose logs -f discord-bot
   ```

### Getting Your Bot Token

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application
3. Go to the "Bot" section
4. Create a bot and copy the token
5. Enable "Message Content Intent" under "Privileged Gateway Intents"

### Getting Your User ID

1. Enable Developer Mode in Discord (User Settings > Advanced > Developer Mode)
2. Right-click your username and select "Copy ID"

## Local Development

For local development without Docker, see the detailed [Local Development Guide](LOCAL_DEVELOPMENT.md).

### Quick Local Setup

```bash
# Clone and setup
git clone <repo-url>
cd DarkraiBot

# Automated setup
python dev.py setup

# Run the bot
python dev.py run
```

## Commands

### Core Commands (All Users)

- `!help` - Comprehensive help system with role-based filtering
- `!ping` - Check bot latency
- `!info` - Detailed bot information and statistics
- `!uptime` - Show bot uptime
- `!contact <message>` - Send message to bot owner (60s cooldown)

### Reminder Commands (All Users)

- `!remind <time> <message>` - Set a reminder
- `!remind list` - List your reminders
- `!remind cancel <id>` - Cancel a reminder
- `!remind help` - Detailed reminder help

**Time Format Examples:**

- `!remind 1h Take a break`
- `!remind 30m Check the oven`
- `!remind 2h30m Call mom`
- `!remind tomorrow Go to the store`
- `!remind in 5 minutes Meeting starts`

### Time & Timezone Commands (All Users)

- `!time` - Show current UTC time
- `!time <timezone>` - Show time in specific timezone
- `!time list` - List popular timezones
- `!time compare <tz1> <tz2>` - Compare two timezones
- `!time help` - Detailed timezone help

**Timezone Examples:**

- `!time EST` - Eastern Standard Time
- `!time Asia/Tokyo` - Tokyo time
- `!time Europe/London` - London time
- `!time compare EST PST` - Compare EST and PST

### Admin Commands (Admin Level)

- `!reload <cog>` - Reload a bot module
- `!status` - Show detailed bot status

### Settings Commands (Admin Level)

- `!set prefix <new_prefix>` - Change command prefix for this server
- `!set admin-roles <role1> [role2]...` - Set admin role names
- `!set mod-roles <role1> [role2]...` - Set moderator role names
- `!set show` - Display current bot settings
- `!set help` - Detailed settings help

**Settings Examples:**

- `!set prefix ?` - Change prefix to "?"
- `!set admin-roles admin administrator` - Set admin roles
- `!set mod-roles moderator mod helper` - Set moderator roles

### Plugin Management Commands (Admin Level)

- `!plugin list` - List all available plugins
- `!plugin load <name>` - Load a specific plugin
- `!plugin unload <name>` - Unload a plugin
- `!plugin reload <name>` - Reload a plugin (or all if no name)
- `!plugin info <name>` - Show plugin information
- `!plugin status` - Plugin system statistics
- `!plugin rescan` - Rediscover plugins

**Plugin Examples:**

- `!plugin load my_plugin` - Load a plugin
- `!plugin reload` - Reload all plugins
- `!plugin info general` - Show info about general plugin

### Owner Commands (Owner Only)

- `!dm <user_id> <message>` - Send direct message to any user
- `!servers` - List all servers the bot is in
- `!leave <server_id> [server_id2]...` - Leave one or more servers
- `!restart` - Restart the bot
- `!shutdown` - Shutdown the bot
- `!ip` - Check bot's public IP address (if IP check cog loaded)
- `!ip-info` - Detailed IP information with geolocation (if IP check cog loaded)

## Configuration

### Environment Variables

| Variable           | Required | Default                 | Description                                    |
| ------------------ | -------- | ----------------------- | ---------------------------------------------- |
| `BOT_TOKEN`        | Yes      | -                       | Discord bot token                              |
| `OWNER_ID`         | Yes      | -                       | Discord user ID of the owner                   |
| `COMMAND_PREFIX`   | No       | `!`                     | Command prefix                                 |
| `LOG_LEVEL`        | No       | `INFO`                  | Logging level                                  |
| `ADMIN_ROLE_NAMES` | No       | `admin,moderator,mod`   | Default admin role names (comma-separated)     |
| `MOD_ROLE_NAMES`   | No       | `moderator,mod`         | Default moderator role names (comma-separated) |
| `DATABASE_URL`     | No       | `sqlite:///data/bot.db` | Database connection string                     |
| `REDIS_URL`        | No       | `redis://redis:6379/0`  | Redis connection string                        |

### Permission Levels

The bot has a four-tier permission system:

1. **Owner**: Bot owner (configured via OWNER_ID)
2. **Admin**: Users with server admin permissions OR configured admin roles
3. **Moderator**: Users with configured moderator roles
4. **User**: All server members

Default role names:

- Admin roles: `admin`, `administrator`, `mod`
- Moderator roles: `moderator`, `mod`

Role names can be customized per server using the settings commands.

## Architecture

### Project Structure

```
discordbot/
├── bot/                    # Bot source code
│   ├── main.py            # Main bot entry point
│   ├── cogs/              # Built-in command modules
│   │   ├── core.py        # Essential bot commands and admin utilities
│   │   ├── reminders.py   # Reminder system
│   │   ├── timezone.py    # Timezone commands
│   │   ├── settings.py    # Bot settings management
│   │   ├── plugin_management.py # Plugin system commands
│   │   ├── ip_check.py    # IP checking commands
│   │   └── general.py     # Legacy general commands (deprecated)
│   ├── plugins/           # Custom plugins directory
│   │   ├── example.py     # Example plugin template
│   │   └── README.md      # Plugin development guide
│   └── utils/             # Utility modules
│       ├── config.py      # Configuration management
│       ├── permissions.py # Permission system
│       ├── database.py    # Database operations
│       ├── time_parser.py # Time parsing utilities
│       └── plugin_manager.py # Dynamic plugin loading
├── data/                  # Persistent data storage
├── config/                # Configuration files
├── docker-compose.yml     # Docker Compose configuration
├── Dockerfile             # Docker image definition
├── requirements.txt       # Python dependencies
└── .env.example          # Environment variables template
```

### Database Schema

The bot uses SQLite with the following tables:

- `reminders` - User reminders with timestamps
- `user_settings` - User preferences and settings
- `activity_log` - Command usage tracking

### Permission System

Three permission levels with decorator-based access control:

- `@user_level()` - Available to all users
- `@admin_only()` - Requires admin permissions
- `@owner_only()` - Requires owner privileges

## Development

### Adding New Commands

1. Create a new cog file in `bot/cogs/`
2. Import and use permission decorators
3. Implement the `setup()` function
4. The bot will automatically load the cog

Example:

```python
from discord.ext import commands
from utils.permissions import user_level

class MyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @user_level()
    async def mycommand(self, ctx):
        await ctx.send("Hello!")

async def setup(bot):
    await bot.add_cog(MyCog(bot))
```

### Running in Development

For development without Docker:

1. Install Python 3.11+
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables
4. Run: `python bot/main.py`

## Docker Management

### Common Commands

(assuming you have sudo permission)

```bash
# Start the bot
docker compose up -d

# View logs
docker compose logs -f discord-bot

# Restart the bot
docker compose restart discord-bot

# Stop the bot
docker compose down

# Update and rebuild
docker compose build --no-cache
docker compose up -d

# Access bot container
docker compose exec discord-bot bash
```

### Data Persistence

- Bot database: `./data/bot.db`
- Bot logs: `./data/bot.log`
- Redis data: Docker volume `redis-data`

## Monitoring & Troubleshooting

### Health Checks

The bot includes health checks that monitor:

- Container responsiveness
- Database connectivity
- Redis connectivity

### Common Issues

1. **Bot not responding**: Check logs for token/permission issues
2. **Commands not working**: Verify user permissions and role names
3. **Reminders not firing**: Check database connectivity and time parsing
4. **IP commands failing**: Network connectivity or service availability

### Logs

Check bot logs for detailed error information:

```bash
docker compose logs -f discord-bot
```

## Security Notes

- Never share your bot token
- Use environment variables for sensitive data
- The bot runs as a non-root user in Docker
- IP commands are restricted to owner only
- Database is stored in a Docker volume

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is available under the GNU General Public License v3.0. See LICENSE file for details.

## Support

For issues and questions:

1. Check the logs for error messages
2. Verify your configuration
3. Review the troubleshooting section
4. Check Discord.py documentation for API issues
