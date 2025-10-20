"""
Plugin Manager - Dynamic cog loading and management system.
"""

import os
import sys
import json
import logging
import importlib
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

import discord
from discord.ext import commands

logger = logging.getLogger(__name__)


class PluginInfo:
    """Information about a plugin/cog."""

    def __init__(self, name: str, path: str, metadata: Dict[str, Any] = None):
        self.name = name
        self.path = path
        self.metadata = metadata or {}
        self.loaded = False
        self.load_time = None
        self.error = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert plugin info to dictionary."""
        return {
            "name": self.name,
            "path": self.path,
            "metadata": self.metadata,
            "loaded": self.loaded,
            "load_time": self.load_time.isoformat() if self.load_time else None,
            "error": str(self.error) if self.error else None,
        }


class PluginManager:
    """Manages dynamic loading and unloading of bot plugins/cogs."""

    def __init__(self, bot: commands.Bot, data_dir: Path = None):
        self.bot = bot
        self.plugins: Dict[str, PluginInfo] = {}

        # Determine data directory
        if data_dir:
            self.data_dir = data_dir
        elif os.path.exists("/app/data"):
            self.data_dir = Path("/app/data")
        else:
            self.data_dir = Path(__file__).parent.parent.parent / "data"

        self.plugin_dirs = [
            Path(__file__).parent.parent / "cogs",
            Path(__file__).parent.parent / "plugins",  # Additional plugins directory
        ]
        self.registry_file = self.data_dir / "plugin_registry.json"

    def discover_plugins(self) -> List[PluginInfo]:
        """Discover all available plugins in plugin directories."""
        discovered = []

        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue

            logger.info(f"Scanning for plugins in: {plugin_dir}")

            for plugin_file in plugin_dir.glob("*.py"):
                if plugin_file.name.startswith("_"):
                    continue

                plugin_name = plugin_file.stem
                relative_path = str(plugin_file.relative_to(plugin_dir.parent))
                module_name = relative_path.replace(os.sep, ".").replace(".py", "")

                # Load metadata from plugin file if available
                metadata = self._load_plugin_metadata(plugin_file)

                plugin_info = PluginInfo(
                    name=plugin_name, path=module_name, metadata=metadata
                )

                discovered.append(plugin_info)
                self.plugins[plugin_name] = plugin_info

        logger.info(f"Discovered {len(discovered)} plugins")
        return discovered

    def _load_plugin_metadata(self, plugin_file: Path) -> Dict[str, Any]:
        """Load metadata from plugin file docstring or comments."""
        metadata = {}

        try:
            with open(plugin_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Look for metadata in docstring or special comments
            lines = content.split("\n")
            for i, line in enumerate(lines[:50]):  # Check first 50 lines
                line = line.strip()

                # Check for metadata comments
                if line.startswith("# Plugin:"):
                    metadata["name"] = line.split(":", 1)[1].strip()
                elif line.startswith("# Version:"):
                    metadata["version"] = line.split(":", 1)[1].strip()
                elif line.startswith("# Author:"):
                    metadata["author"] = line.split(":", 1)[1].strip()
                elif line.startswith("# Description:"):
                    metadata["description"] = line.split(":", 1)[1].strip()
                elif line.startswith("# Dependencies:"):
                    deps = line.split(":", 1)[1].strip()
                    metadata["dependencies"] = [
                        dep.strip() for dep in deps.split(",") if dep.strip()
                    ]
                elif line.startswith("# Permissions:"):
                    metadata["required_permissions"] = line.split(":", 1)[1].strip()

        except Exception as e:
            logger.warning(f"Failed to load metadata for {plugin_file}: {e}")

        return metadata

    async def load_plugin(self, plugin_name: str, reload: bool = False) -> bool:
        """Load a specific plugin."""
        if plugin_name not in self.plugins:
            logger.error(f"Plugin {plugin_name} not found in registry")
            return False

        plugin_info = self.plugins[plugin_name]

        try:
            if reload and plugin_info.loaded:
                await self.unload_plugin(plugin_name)

            # Load the extension
            await self.bot.load_extension(plugin_info.path)

            plugin_info.loaded = True
            plugin_info.load_time = datetime.utcnow()
            plugin_info.error = None

            logger.info(f"Successfully loaded plugin: {plugin_name}")
            await self.save_registry()
            return True

        except Exception as e:
            plugin_info.error = e
            plugin_info.loaded = False
            logger.error(f"Failed to load plugin {plugin_name}: {e}")
            return False

    async def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a specific plugin."""
        if plugin_name not in self.plugins:
            logger.error(f"Plugin {plugin_name} not found in registry")
            return False

        plugin_info = self.plugins[plugin_name]

        try:
            await self.bot.unload_extension(plugin_info.path)

            plugin_info.loaded = False
            plugin_info.error = None

            logger.info(f"Successfully unloaded plugin: {plugin_name}")
            await self.save_registry()
            return True

        except Exception as e:
            plugin_info.error = e
            logger.error(f"Failed to unload plugin {plugin_name}: {e}")
            return False

    async def reload_plugin(self, plugin_name: str) -> bool:
        """Reload a specific plugin."""
        if plugin_name not in self.plugins:
            logger.error(f"Plugin {plugin_name} not found in registry")
            return False

        plugin_info = self.plugins[plugin_name]

        try:
            # Reload the extension
            await self.bot.reload_extension(plugin_info.path)

            plugin_info.loaded = True
            plugin_info.load_time = datetime.utcnow()
            plugin_info.error = None

            logger.info(f"Successfully reloaded plugin: {plugin_name}")
            await self.save_registry()
            return True

        except Exception as e:
            plugin_info.error = e
            logger.error(f"Failed to reload plugin {plugin_name}: {e}")
            return False

    async def load_all_plugins(self) -> Dict[str, bool]:
        """Load all discovered plugins."""
        self.discover_plugins()
        results = {}

        for plugin_name in self.plugins:
            results[plugin_name] = await self.load_plugin(plugin_name)

        return results

    async def reload_all_plugins(self) -> Dict[str, bool]:
        """Reload all currently loaded plugins."""
        results = {}

        for plugin_name, plugin_info in self.plugins.items():
            if plugin_info.loaded:
                results[plugin_name] = await self.reload_plugin(plugin_name)

        return results

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """Get information about a specific plugin."""
        return self.plugins.get(plugin_name)

    def get_loaded_plugins(self) -> List[PluginInfo]:
        """Get list of all loaded plugins."""
        return [plugin for plugin in self.plugins.values() if plugin.loaded]

    def get_available_plugins(self) -> List[PluginInfo]:
        """Get list of all available plugins."""
        return list(self.plugins.values())

    async def save_registry(self):
        """Save plugin registry to file."""
        try:
            # Ensure data directory exists
            self.registry_file.parent.mkdir(parents=True, exist_ok=True)

            registry_data = {
                "last_updated": datetime.utcnow().isoformat(),
                "plugins": {
                    name: plugin.to_dict() for name, plugin in self.plugins.items()
                },
            }

            with open(self.registry_file, "w", encoding="utf-8") as f:
                json.dump(registry_data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"Failed to save plugin registry: {e}")

    async def load_registry(self):
        """Load plugin registry from file."""
        try:
            if not self.registry_file.exists():
                logger.info("No existing plugin registry found")
                return

            with open(self.registry_file, "r", encoding="utf-8") as f:
                registry_data = json.load(f)

            # Restore plugin information
            for name, plugin_data in registry_data.get("plugins", {}).items():
                plugin_info = PluginInfo(
                    name=plugin_data["name"],
                    path=plugin_data["path"],
                    metadata=plugin_data.get("metadata", {}),
                )
                plugin_info.loaded = False  # Will be determined during discovery
                if plugin_data.get("load_time"):
                    plugin_info.load_time = datetime.fromisoformat(
                        plugin_data["load_time"]
                    )

                self.plugins[name] = plugin_info

            logger.info(f"Loaded plugin registry with {len(self.plugins)} plugins")

        except Exception as e:
            logger.error(f"Failed to load plugin registry: {e}")

    def check_dependencies(self, plugin_name: str) -> List[str]:
        """Check if plugin dependencies are satisfied."""
        plugin_info = self.plugins.get(plugin_name)
        if not plugin_info or not plugin_info.metadata.get("dependencies"):
            return []

        missing_deps = []
        dependencies = plugin_info.metadata["dependencies"]

        for dep in dependencies:
            if dep not in self.plugins or not self.plugins[dep].loaded:
                missing_deps.append(dep)

        return missing_deps

    def get_plugin_stats(self) -> Dict[str, Any]:
        """Get statistics about plugins."""
        total = len(self.plugins)
        loaded = len([p for p in self.plugins.values() if p.loaded])
        errors = len([p for p in self.plugins.values() if p.error])

        return {
            "total_plugins": total,
            "loaded_plugins": loaded,
            "failed_plugins": errors,
            "success_rate": f"{(loaded/total*100):.1f}%" if total > 0 else "0%",
        }
