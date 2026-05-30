import discord
from discord import app_commands
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy import select, delete, func
from datetime import datetime
import logging

from database import async_session, Guild, TikTokAccount, GuildTikTokSubscription, VideoHistory
from bot.services.tiktok_monitor import TikTokMonitor
from bot.services.notification import send_new_video_notification
from config.settings import settings

logger = logging.getLogger("tiktok_commands")

class TikTokCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.monitor = TikTokMonitor()
        self._setup_scheduler()
        
    def _setup_scheduler(self):
        """Setup background monitoring job."""
        interval_minutes = settings.TIKTOK_POLL_INTERVAL_MINUTES
        self.scheduler.add_job(
            self._check_all_accounts,
            trigger=IntervalTrigger(minutes=interval_minutes),
            id="monitor_tiktok",
            replace_existing=True
        )
        self.scheduler.start()
        logger.info(f"Background monitoring scheduled every {interval_minutes} minutes")
        
    async def _check_all_accounts(self):
        """Check all enabled TikTok accounts for new videos."""
        logger.info("Running background check for all TikTok accounts...")
        async with async_session() as session:
            # Get all enabled accounts
            result = await session.execute(
                select(TikTokAccount).where(TikTokAccount.enabled == True)
            )
            accounts = result.scalars().all()
            
        for account in accounts:
            try:
                await self._check_account(account.username)
            except Exception as e:
                logger.error(f"Error checking account {account.username}: {e}")
                
    async def _check_account(self, username: str):
        """Check a single account for new videos and notify subscribers."""
        logger.debug(f"Checking account: {username}")
        
        # Fetch latest videos from TikTok
        videos = await self.monitor.get_latest_videos(username, limit=settings.TIKTOK_FETCH_LIMIT)
        if not videos:
            return
            
        async with async_session() as session:
            # Get existing video IDs to avoid duplicates
            video_ids = [v['id'] for v in videos]
            existing = await session.execute(
                select(VideoHistory.tiktok_video_id).where(
                    VideoHistory.tiktok_video_id.in_(video_ids)
                )
            )
            existing_ids = {row[0] for row in existing.all()}
            
            # Get all guilds subscribed to this account
            sub_result = await session.execute(
                select(GuildTikTokSubscription.guild_id)
                .join(TikTokAccount)
                .where(TikTokAccount.username == username)
            )
            subscribed_guild_ids = [row[0] for row in sub_result.all()]
            
            # For each guild, get notification channel
            guild_channels = {}
            for guild_id in subscribed_guild_ids:
                guild_result = await session.execute(
                    select(Guild).where(Guild.id == guild_id)
                )
                guild = guild_result.scalar_one_or_none()
                if guild and guild.notification_channel_id:
                    guild_channels[guild.guild_id] = guild.notification_channel_id
                    
            # Process new videos
            for video in videos:
                if video['id'] in existing_ids:
                    continue
                    
                # Save to history
                new_history = VideoHistory(
                    tiktok_video_id=video['id'],
                    username=username,
                    video_url=video['url'],
                    published_at=video.get('published_at')
                )
                session.add(new_history)
                
                # Send notifications to each guild
                for guild_discord_id, channel_id in guild_channels.items():
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await send_new_video_notification(
                            channel=channel,
                            username=username,
                            caption=video.get('description', 'No description'),
                            thumbnail_url=video.get('thumbnail'),
                            video_url=video['url'],
                            published_at=video.get('published_at'),
                            detected_at=datetime.utcnow()
                        )
                    else:
                        logger.warning(f"Channel {channel_id} not found for guild {guild_discord_id}")
                        
            await session.commit()
            
    # --- Slash Commands ---
    
    async def _is_admin(self, interaction: discord.Interaction) -> bool:
        """Check if user has administrator permission."""
        if not interaction.guild:
            await interaction.response.send_message("This command can only be used in a server.", ephemeral=True)
            return False
        perms = interaction.permissions
        if not perms.administrator:
            await interaction.response.send_message("You need Administrator permission to use this command.", ephemeral=True)
            return False
        return True
        
    @app_commands.command(name="addtiktok", description="Add a TikTok account to monitor (Admin only)")
    async def add_tiktok(self, interaction: discord.Interaction, username: str):
        if not await self._is_admin(interaction):
            return
            
        username = username.lower().strip()
        async with async_session() as session:
            # Get or create guild
            guild_result = await session.execute(
                select(Guild).where(Guild.guild_id == interaction.guild_id)
            )
            guild = guild_result.scalar_one_or_none()
            if not guild:
                guild = Guild(guild_id=interaction.guild_id)
                session.add(guild)
                await session.flush()
                
            # Get or create TikTok account
            acc_result = await session.execute(
                select(TikTokAccount).where(TikTokAccount.username == username)
            )
            account = acc_result.scalar_one_or_none()
            if not account:
                account = TikTokAccount(username=username)
                session.add(account)
                await session.flush()
                
            # Check if subscription already exists
            sub_result = await session.execute(
                select(GuildTikTokSubscription).where(
                    GuildTikTokSubscription.guild_id == guild.id,
                    GuildTikTokSubscription.account_id == account.id
                )
            )
            if sub_result.scalar_one_or_none():
                await interaction.response.send_message(f"@{username} is already being monitored in this server.", ephemeral=True)
                return
                
            # Create subscription
            sub = GuildTikTokSubscription(guild_id=guild.id, account_id=account.id)
            session.add(sub)
            await session.commit()
            
        await interaction.response.send_message(f"✅ Now monitoring TikTok account: **@{username}**")
        
    @app_commands.command(name="removetiktok", description="Remove a TikTok account from monitoring (Admin only)")
    async def remove_tiktok(self, interaction: discord.Interaction, username: str):
        if not await self._is_admin(interaction):
            return
            
        username = username.lower().strip()
        async with async_session() as session:
            # Get guild and account
            guild_result = await session.execute(
                select(Guild).where(Guild.guild_id == interaction.guild_id)
            )
            guild = guild_result.scalar_one_or_none()
            if not guild:
                await interaction.response.send_message("This server has no settings yet.", ephemeral=True)
                return
                
            acc_result = await session.execute(
                select(TikTokAccount).where(TikTokAccount.username == username)
            )
            account = acc_result.scalar_one_or_none()
            if not account:
                await interaction.response.send_message(f"Account @{username} not found.", ephemeral=True)
                return
                
            # Delete subscription
            await session.execute(
                delete(GuildTikTokSubscription).where(
                    GuildTikTokSubscription.guild_id == guild.id,
                    GuildTikTokSubscription.account_id == account.id
                )
            )
            await session.commit()
            
        await interaction.response.send_message(f"❌ Removed **@{username}** from monitoring.")
        
    @app_commands.command(name="listtiktok", description="List all monitored TikTok accounts in this server")
    async def list_tiktok(self, interaction: discord.Interaction):
        async with async_session() as session:
            guild_result = await session.execute(
                select(Guild).where(Guild.guild_id == interaction.guild_id)
            )
            guild = guild_result.scalar_one_or_none()
            if not guild:
                await interaction.response.send_message("No TikTok accounts are being monitored yet.", ephemeral=True)
                return
                
            result = await session.execute(
                select(TikTokAccount.username)
                .join(GuildTikTokSubscription)
                .where(GuildTikTokSubscription.guild_id == guild.id)
            )
            usernames = [row[0] for row in result.all()]
            
        if not usernames:
            await interaction.response.send_message("No TikTok accounts are being monitored in this server.")
        else:
            embed = discord.Embed(
                title="📱 Monitored TikTok Accounts",
                description="\n".join([f"• @{u}" for u in usernames]),
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
            
    @app_commands.command(name="setchannel", description="Set the channel for TikTok notifications (Admin only)")
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if not await self._is_admin(interaction):
            return
            
        async with async_session() as session:
            guild_result = await session.execute(
                select(Guild).where(Guild.guild_id == interaction.guild_id)
            )
            guild = guild_result.scalar_one_or_none()
            if not guild:
                guild = Guild(guild_id=interaction.guild_id)
                session.add(guild)
                
            guild.notification_channel_id = channel.id
            await session.commit()
            
        await interaction.response.send_message(f"✅ Notifications will be sent to {channel.mention}")
        
    @app_commands.command(name="forcecheck", description="Manually trigger a scan for new videos")
    async def force_check(self, interaction: discord.Interaction):
        await interaction.response.send_message("🔄 Force checking all monitored accounts...", ephemeral=True)
        await self._check_all_accounts()
        await interaction.edit_original_response(content="✅ Force check completed!")
        
    @app_commands.command(name="status", description="Show bot status and statistics")
    async def status(self, interaction: discord.Interaction):
        async with async_session() as session:
            # Total monitored accounts across all guilds
            total_accounts = await session.execute(select(func.count(TikTokAccount.id)))
            total_accounts = total_accounts.scalar()
            
            # Total videos detected
            total_videos = await session.execute(select(func.count(VideoHistory.id)))
            total_videos = total_videos.scalar()
            
            # Number of guilds with subscriptions
            guilds_with_subs = await session.execute(
                select(func.count(Guild.id.distinct()))
                .join(GuildTikTokSubscription)
            )
            guilds_with_subs = guilds_with_subs.scalar()
            
        embed = discord.Embed(title="📊 Bot Status", color=discord.Color.green())
        embed.add_field(name="Monitored TikTok Accounts", value=str(total_accounts), inline=True)
        embed.add_field(name="Videos Detected (All Time)", value=str(total_videos), inline=True)
        embed.add_field(name="Servers with Subscriptions", value=str(guilds_with_subs), inline=True)
        embed.add_field(name="Check Interval", value=f"{settings.TIKTOK_POLL_INTERVAL_MINUTES} minutes", inline=True)
        embed.set_footer(text=f"Online since {self.bot.user.created_at.strftime('%Y-%m-%d')}")
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name="help", description="Show help information")
    async def help_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🤖 TikTok Monitor Bot Help",
            description="Monitor TikTok accounts and get notified when new videos are posted.",
            color=discord.Color.purple()
        )
        embed.add_field(
            name="📌 Admin Commands",
            value=(
                "`/addtiktok <username>` – Add a TikTok account\n"
                "`/removetiktok <username>` – Remove an account\n"
                "`/setchannel #channel` – Set notification channel\n"
                "`/forcecheck` – Manually trigger a scan"
            ),
            inline=False
        )
        embed.add_field(
            name="📌 User Commands",
            value=(
                "`/listtiktok` – List monitored accounts\n"
                "`/status` – Show bot status\n"
                "`/help` – Show this message"
            ),
            inline=False
        )
        embed.add_field(
            name="🔗 Web Dashboard",
            value="Manage everything from the web dashboard at `http://localhost:8000`",
            inline=False
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(TikTokCommands(bot))