from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy import select, func, desc
from database import async_session, Guild, TikTokAccount, GuildTikTokSubscription, VideoHistory

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()

def is_authenticated(request: Request):
    """Check if user is logged in."""
    return request.session.get("user") is not None

async def is_admin_of_guild(request: Request, guild_id: int):
    """Check if user is administrator of the given Discord guild."""
    guilds = request.session.get("guilds", [])
    for g in guilds:
        if int(g["id"]) == guild_id:
            permissions = int(g.get("permissions", 0))
            return (permissions & 0x8) != 0  # Administrator permission
    return False

@router.get("/dashboard/home")
async def home(request: Request):
    if not is_authenticated(request):
        return templates.TemplateResponse("login.html", {"request": request})
        
    user = request.session["user"]
    guilds = request.session.get("guilds", [])
    
    # Filter guilds where user is admin
    admin_guilds = []
    for g in guilds:
        perms = int(g.get("permissions", 0))
        if perms & 0x8:
            admin_guilds.append(g)
            
    return templates.TemplateResponse("home.html", {
        "request": request,
        "user": user,
        "guilds": admin_guilds
    })

@router.get("/dashboard/guild/{guild_id}")
async def guild_settings(request: Request, guild_id: int):
    if not is_authenticated(request):
        return templates.TemplateResponse("login.html", {"request": request})
        
    if not await is_admin_of_guild(request, guild_id):
        raise HTTPException(status_code=403, detail="You need to be an administrator of this server.")
        
    async with async_session() as session:
        # Get guild DB record
        db_guild = await session.execute(
            select(Guild).where(Guild.guild_id == guild_id)
        )
        db_guild = db_guild.scalar_one_or_none()
        
        # Get subscriptions
        subscriptions = []
        if db_guild:
            sub_result = await session.execute(
                select(TikTokAccount.username, TikTokAccount.enabled)
                .join(GuildTikTokSubscription)
                .where(GuildTikTokSubscription.guild_id == db_guild.id)
            )
            subscriptions = [{"username": row[0], "enabled": row[1]} for row in sub_result.all()]
            
        # Get channel setting
        notification_channel = db_guild.notification_channel_id if db_guild else None
        
    return templates.TemplateResponse("guild_settings.html", {
        "request": request,
        "guild_id": guild_id,
        "subscriptions": subscriptions,
        "notification_channel": notification_channel,
        "user": request.session["user"]
    })

@router.get("/dashboard/activity/{guild_id}")
async def activity_logs(request: Request, guild_id: int):
    if not is_authenticated(request):
        return templates.TemplateResponse("login.html", {"request": request})
        
    if not await is_admin_of_guild(request, guild_id):
        raise HTTPException(status_code=403, detail="Admin required.")
        
    async with async_session() as session:
        # Get guild DB id
        db_guild = await session.execute(
            select(Guild).where(Guild.guild_id == guild_id)
        )
        db_guild = db_guild.scalar_one_or_none()
        
        logs = []
        if db_guild:
            # Get subscriptions to know which accounts to show videos for
            sub_accounts = await session.execute(
                select(TikTokAccount.username)
                .join(GuildTikTokSubscription)
                .where(GuildTikTokSubscription.guild_id == db_guild.id)
            )
            usernames = [row[0] for row in sub_accounts.all()]
            
            if usernames:
                video_logs = await session.execute(
                    select(VideoHistory)
                    .where(VideoHistory.username.in_(usernames))
                    .order_by(desc(VideoHistory.detected_at))
                    .limit(50)
                )
                logs = video_logs.scalars().all()
                
    return templates.TemplateResponse("logs.html", {
        "request": request,
        "logs": logs,
        "guild_id": guild_id,
        "user": request.session["user"]
    })

@router.get("/dashboard/status")
async def status_page(request: Request):
    if not is_authenticated(request):
        return templates.TemplateResponse("login.html", {"request": request})
        
    async with async_session() as session:
        total_accounts = await session.execute(select(func.count(TikTokAccount.id)))
        total_accounts = total_accounts.scalar()
        total_videos = await session.execute(select(func.count(VideoHistory.id)))
        total_videos = total_videos.scalar()
        total_guilds = await session.execute(select(func.count(Guild.id)))
        total_guilds = total_guilds.scalar()
        
    return templates.TemplateResponse("status.html", {
        "request": request,
        "total_accounts": total_accounts,
        "total_videos": total_videos,
        "total_guilds": total_guilds,
        "user": request.session["user"]
    })