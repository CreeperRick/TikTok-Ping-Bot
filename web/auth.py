import aiohttp
from config.settings import settings

DISCORD_API_BASE = "https://discord.com/api/v10"

async def get_discord_oauth_token(code: str, redirect_uri: str):
    """Exchange code for access token."""
    data = {
        "client_id": settings.DISCORD_CLIENT_ID,
        "client_secret": settings.DISCORD_CLIENT_SECRET,
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{DISCORD_API_BASE}/oauth2/token", data=data, headers=headers) as resp:
            return await resp.json()
            
async def get_discord_user(access_token: str):
    """Fetch user info from Discord."""
    headers = {"Authorization": f"Bearer {access_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{DISCORD_API_BASE}/users/@me", headers=headers) as resp:
            return await resp.json()
            
async def get_user_guilds(access_token: str):
    """Fetch user's guilds."""
    headers = {"Authorization": f"Bearer {access_token}"}
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{DISCORD_API_BASE}/users/@me/guilds", headers=headers) as resp:
            return await resp.json()