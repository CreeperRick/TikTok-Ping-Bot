import discord
from discord.ext import commands
import logging
from config.settings import settings

logger = logging.getLogger("discord_bot")


class DiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )

    async def setup_hook(self):
        """Load cogs and sync commands."""
        await self.load_extension("bot.cogs.tiktok_commands")
        logger.info("Loaded tiktok_commands cog")

        await self.tree.sync()
        logger.info("Synced slash commands")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        await self.change_presence(activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="TikTok | /help"
        ))

    async def start(self):
        """Start the bot with token."""
        await super().start(settings.DISCORD_TOKEN)
