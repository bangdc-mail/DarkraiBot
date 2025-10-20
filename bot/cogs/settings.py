"""
Settings Cog - Admin commands for configuring bot settings per guild.
"""

import logging
from typing import List

import discord
from discord.ext import commands

from utils.permissions import admin_only, PermissionLevel

logger = logging.getLogger(__name__)


class SettingsCog(commands.Cog):
    """Cog for bot settings management."""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="set", invoke_without_command=True)
    @admin_only()
    async def set_group(self, ctx):
        """
        Bot settings management commands.

        Available subcommands:
        - set prefix <new_prefix>
        - set admin-roles <role1> [role2] [role3]...
        - set mod-roles <role1> [role2] [role3]...

        Use !set help for detailed information.
        """
        embed = discord.Embed(
            title="⚙️ Bot Settings",
            description="Use subcommands to configure bot settings.",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="Available Commands",
            value=(
                f"`{ctx.prefix}set prefix <new_prefix>` - Change command prefix\n"
                f"`{ctx.prefix}set admin-roles <roles...>` - Set admin role names\n"
                f"`{ctx.prefix}set mod-roles <roles...>` - Set moderator role names\n"
                f"`{ctx.prefix}set show` - Show current settings"
            ),
            inline=False,
        )

        await ctx.send(embed=embed)

    @set_group.command(name="prefix")
    @admin_only()
    async def set_prefix(self, ctx, new_prefix: str):
        """
        Change the bot's command prefix for this server.

        Usage: !set prefix <new_prefix>
        Example: !set prefix ?
        """
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        # Validate prefix
        if len(new_prefix) > 5:
            await ctx.send("❌ Prefix cannot be longer than 5 characters.")
            return

        if " " in new_prefix:
            await ctx.send("❌ Prefix cannot contain spaces.")
            return

        try:
            # Update guild settings
            await self.bot.database.update_guild_settings(
                ctx.guild.id, command_prefix=new_prefix
            )

            # Log the command
            await self.bot.database.log_command(
                ctx.author.id, ctx.guild.id, "set prefix"
            )

            embed = discord.Embed(
                title="✅ Prefix Updated",
                description=f"Command prefix changed to `{new_prefix}`",
                color=discord.Color.green(),
            )
            embed.add_field(
                name="Note",
                value=f"You can now use `{new_prefix}help` to see commands.",
                inline=False,
            )
            embed.set_footer(text=f"Changed by {ctx.author}")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to update prefix: {str(e)}")
            logger.error(f"Failed to update prefix: {e}")

    @set_group.command(name="admin-roles", aliases=["admin", "adminroles"])
    @admin_only()
    async def set_admin_roles(self, ctx, *role_names):
        """
        Set the role names that grant admin permissions.

        Usage: !set admin-roles <role1> [role2] [role3]...
        Example: !set admin-roles admin administrator staff
        """
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        if not role_names:
            await ctx.send("❌ You must specify at least one role name.")
            return

        # Validate role names
        if len(role_names) > 10:
            await ctx.send("❌ You can specify a maximum of 10 role names.")
            return

        # Clean up role names
        clean_roles = [role.strip() for role in role_names if role.strip()]
        if not clean_roles:
            await ctx.send("❌ Please provide valid role names.")
            return

        try:
            # Update guild settings
            await self.bot.database.update_guild_settings(
                ctx.guild.id, admin_roles=clean_roles
            )

            # Log the command
            await self.bot.database.log_command(
                ctx.author.id, ctx.guild.id, "set admin-roles"
            )

            embed = discord.Embed(
                title="✅ Admin Roles Updated",
                description="Admin role names have been updated.",
                color=discord.Color.green(),
            )
            embed.add_field(
                name="Admin Roles",
                value=", ".join(f"`{role}`" for role in clean_roles),
                inline=False,
            )
            embed.add_field(
                name="Note",
                value="Users with these roles (or server admin permissions) can use admin commands.",
                inline=False,
            )
            embed.set_footer(text=f"Changed by {ctx.author}")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to update admin roles: {str(e)}")
            logger.error(f"Failed to update admin roles: {e}")

    @set_group.command(name="mod-roles", aliases=["mod", "modroles", "moderator-roles"])
    @admin_only()
    async def set_mod_roles(self, ctx, *role_names):
        """
        Set the role names that grant moderator permissions.

        Usage: !set mod-roles <role1> [role2] [role3]...
        Example: !set mod-roles moderator mod helper
        """
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        if not role_names:
            await ctx.send("❌ You must specify at least one role name.")
            return

        # Validate role names
        if len(role_names) > 10:
            await ctx.send("❌ You can specify a maximum of 10 role names.")
            return

        # Clean up role names
        clean_roles = [role.strip() for role in role_names if role.strip()]
        if not clean_roles:
            await ctx.send("❌ Please provide valid role names.")
            return

        try:
            # Update guild settings
            await self.bot.database.update_guild_settings(
                ctx.guild.id, mod_roles=clean_roles
            )

            # Log the command
            await self.bot.database.log_command(
                ctx.author.id, ctx.guild.id, "set mod-roles"
            )

            embed = discord.Embed(
                title="✅ Moderator Roles Updated",
                description="Moderator role names have been updated.",
                color=discord.Color.green(),
            )
            embed.add_field(
                name="Moderator Roles",
                value=", ".join(f"`{role}`" for role in clean_roles),
                inline=False,
            )
            embed.add_field(
                name="Note",
                value="Users with these roles can use moderator+ commands.",
                inline=False,
            )
            embed.set_footer(text=f"Changed by {ctx.author}")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to update moderator roles: {str(e)}")
            logger.error(f"Failed to update moderator roles: {e}")

    @set_group.command(name="show", aliases=["display", "current"])
    @admin_only()
    async def show_settings(self, ctx):
        """Show current bot settings for this server."""
        if not ctx.guild:
            await ctx.send("❌ This command can only be used in a server.")
            return

        try:
            # Get current settings
            settings = await self.bot.database.get_guild_settings(ctx.guild.id)

            embed = discord.Embed(
                title="⚙️ Current Bot Settings",
                description=f"Settings for **{ctx.guild.name}**",
                color=discord.Color.blue(),
            )

            embed.add_field(
                name="Command Prefix",
                value=f"`{settings['command_prefix']}`",
                inline=True,
            )

            embed.add_field(
                name="Admin Roles",
                value=(
                    ", ".join(f"`{role}`" for role in settings["admin_roles"])
                    if settings["admin_roles"]
                    else "None set"
                ),
                inline=False,
            )

            embed.add_field(
                name="Moderator Roles",
                value=(
                    ", ".join(f"`{role}`" for role in settings["mod_roles"])
                    if settings["mod_roles"]
                    else "None set"
                ),
                inline=False,
            )

            # Get user's permission level
            user_level = self.bot.permission_manager.get_user_permission_level(
                ctx.author, ctx.guild
            )
            embed.add_field(
                name="Your Permission Level",
                value=f"`{user_level.name.title()}`",
                inline=True,
            )

            embed.set_footer(text=f"Requested by {ctx.author}")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"❌ Failed to get settings: {str(e)}")
            logger.error(f"Failed to get settings: {e}")

    @set_group.command(name="help")
    @admin_only()
    async def settings_help(self, ctx):
        """Show detailed help for settings commands."""
        embed = discord.Embed(
            title="⚙️ Settings Commands Help",
            description="Detailed help for bot settings management.",
            color=discord.Color.blue(),
        )

        embed.add_field(
            name="🔧 Set Prefix",
            value=(
                f"`{ctx.prefix}set prefix <new_prefix>`\n"
                "Change the command prefix for this server.\n"
                "Example: `!set prefix ?`"
            ),
            inline=False,
        )

        embed.add_field(
            name="👑 Set Admin Roles",
            value=(
                f"`{ctx.prefix}set admin-roles <role1> [role2]...`\n"
                "Set role names that grant admin permissions.\n"
                "Example: `!set admin-roles admin administrator`"
            ),
            inline=False,
        )

        embed.add_field(
            name="🛡️ Set Moderator Roles",
            value=(
                f"`{ctx.prefix}set mod-roles <role1> [role2]...`\n"
                "Set role names that grant moderator permissions.\n"
                "Example: `!set mod-roles moderator mod helper`"
            ),
            inline=False,
        )

        embed.add_field(
            name="📋 Show Settings",
            value=(
                f"`{ctx.prefix}set show`\n"
                "Display current bot settings for this server."
            ),
            inline=False,
        )

        embed.add_field(
            name="📝 Permission Levels",
            value=(
                "**Owner**: Bot owner (full control)\n"
                "**Admin**: Server admins + configured admin roles\n"
                "**Mod**: Configured moderator roles\n"
                "**User**: All server members"
            ),
            inline=False,
        )

        await ctx.send(embed=embed)


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(SettingsCog(bot))
