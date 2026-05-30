import discord
from datetime import datetime

async def send_new_video_notification(
    channel: discord.TextChannel,
    username: str,
    caption: str,
    thumbnail_url: str,
    video_url: str,
    published_at: datetime = None,
    detected_at: datetime = None
):
    """Send a Discord embed notification for a new TikTok video."""
    
    embed = discord.Embed(
        title=f"🎬 New TikTok Video from @{username}",
        description=caption[:200] + ("..." if len(caption) > 200 else ""),
        color=discord.Color.red(),
        url=video_url
    )
    
    if thumbnail_url:
        embed.set_image(url=thumbnail_url)
        
    embed.add_field(name="Watch on TikTok", value=f"[Click here]({video_url})", inline=False)
    
    if published_at:
        embed.add_field(name="Uploaded", value=f"<t:{int(published_at.timestamp())}:R>", inline=True)
    if detected_at:
        embed.add_field(name="Detected", value=f"<t:{int(detected_at.timestamp())}:R>", inline=True)
        
    embed.set_footer(text="TikTok Monitor Bot", icon_url="https://cdn-icons-png.flaticon.com/512/3046/3046126.png")
    
    # Create view with button
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Watch on TikTok", url=video_url))
    
    await channel.send(embed=embed, view=view)