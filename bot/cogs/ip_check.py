"""
IP Check Cog - Owner-level commands for checking bot's public IP.
"""

import aiohttp
import logging
from datetime import datetime

import discord
from discord.ext import commands

from utils.permissions import owner_only

logger = logging.getLogger(__name__)


class IPCheckCog(commands.Cog):
    """Cog for IP-related owner commands."""

    def __init__(self, bot):
        self.bot = bot
        self.ip_services = [
            "https://api.ipify.org",
            "https://icanhazip.com",
            "https://ipecho.net/plain",
            "https://checkip.amazonaws.com",
        ]

    async def _get_public_ip(self) -> str:
        """Get the bot's public IP address using multiple services."""
        async with aiohttp.ClientSession() as session:
            for service in self.ip_services:
                try:
                    async with session.get(service, timeout=5) as response:
                        if response.status == 200:
                            ip = (await response.text()).strip()
                            # Basic IP validation
                            if self._is_valid_ip(ip):
                                return ip
                except Exception as e:
                    logger.warning(f"Failed to get IP from {service}: {e}")
                    continue

        raise Exception("Unable to determine public IP from any service")

    def _is_valid_ip(self, ip: str) -> bool:
        """Basic IP address validation."""
        parts = ip.split(".")
        if len(parts) != 4:
            return False

        try:
            for part in parts:
                if not 0 <= int(part) <= 255:
                    return False
            return True
        except ValueError:
            return False

    @commands.command(name="ip", aliases=["myip", "public-ip"])
    @owner_only()
    async def check_ip(self, ctx):
        """
        Check the bot's public IP address.

        This command is restricted to the bot owner only for security reasons.
        """
        try:
            # Log the command usage
            await self.bot.database.log_command(
                ctx.author.id, ctx.guild.id if ctx.guild else None, "ip"
            )

            # Send initial message
            embed = discord.Embed(
                title="🌐 Checking Public IP...",
                description="Fetching IP address information...",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow(),
            )
            message = await ctx.send(embed=embed)

            # Get IP address
            ip_address = await self._get_public_ip()

            # Update embed with results
            embed = discord.Embed(
                title="🌐 Bot Public IP Address",
                color=discord.Color.green(),
                timestamp=datetime.utcnow(),
            )
            embed.add_field(name="IP Address", value=f"`{ip_address}`", inline=False)
            embed.add_field(
                name="Timestamp",
                value=f"<t:{int(datetime.utcnow().timestamp())}:F>",
                inline=False,
            )
            embed.set_footer(text=f"Requested by {ctx.author}")

            await message.edit(embed=embed)

        except Exception as e:
            # Log the error
            await self.bot.database.log_command(
                ctx.author.id,
                ctx.guild.id if ctx.guild else None,
                "ip",
                success=False,
                error_message=str(e),
            )

            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to retrieve IP address: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow(),
            )
            await ctx.send(embed=error_embed)
            logger.error(f"IP check failed: {e}")

    @commands.command(name="ip-info")
    @owner_only()
    async def ip_info(self, ctx):
        """
        Get detailed information about the bot's public IP.

        This command provides additional information about the IP address
        including geolocation data (if available).
        """
        try:
            # Log the command usage
            await self.bot.database.log_command(
                ctx.author.id, ctx.guild.id if ctx.guild else None, "ip-info"
            )

            # Send initial message
            embed = discord.Embed(
                title="🌐 Gathering IP Information...",
                description="Fetching detailed IP information...",
                color=discord.Color.blue(),
                timestamp=datetime.utcnow(),
            )
            message = await ctx.send(embed=embed)

            # Get IP address
            ip_address = await self._get_public_ip()

            # Get additional IP information
            ip_info = await self._get_ip_info(ip_address)

            # Create detailed embed
            embed = discord.Embed(
                title="🌐 Detailed IP Information",
                color=discord.Color.green(),
                timestamp=datetime.utcnow(),
            )

            embed.add_field(name="IP Address", value=f"`{ip_address}`", inline=True)

            if ip_info:
                for key, value in ip_info.items():
                    if value and key != "ip":
                        embed.add_field(name=key.title(), value=str(value), inline=True)

            embed.add_field(
                name="Timestamp",
                value=f"<t:{int(datetime.utcnow().timestamp())}:F>",
                inline=False,
            )
            embed.set_footer(text=f"Requested by {ctx.author}")

            await message.edit(embed=embed)

        except Exception as e:
            # Log the error
            await self.bot.database.log_command(
                ctx.author.id,
                ctx.guild.id if ctx.guild else None,
                "ip-info",
                success=False,
                error_message=str(e),
            )

            error_embed = discord.Embed(
                title="❌ Error",
                description=f"Failed to retrieve IP information: {str(e)}",
                color=discord.Color.red(),
                timestamp=datetime.utcnow(),
            )
            await ctx.send(embed=error_embed)
            logger.error(f"IP info check failed: {e}")

    async def _get_ip_info(self, ip: str) -> dict:
        """Get additional information about an IP address."""
        try:
            async with aiohttp.ClientSession() as session:
                # Using ipapi.co for IP geolocation (free service)
                async with session.get(
                    f"https://ipapi.co/{ip}/json/", timeout=10
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "city": data.get("city"),
                            "region": data.get("region"),
                            "country": data.get("country_name"),
                            "isp": data.get("org"),
                            "timezone": data.get("timezone"),
                        }
        except Exception as e:
            logger.warning(f"Failed to get IP info: {e}")

        return {}


async def setup(bot):
    """Setup function to add the cog to the bot."""
    await bot.add_cog(IPCheckCog(bot))
