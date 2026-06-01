from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import select, delete, desc
from database import async_session, Guild, TikTokAccount, GuildTikTokSubscription, VideoHistory

router = APIRouter()


# --- Dependencies ---

async def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


async def get_admin_guild(request: Request, guild_id: int):
    guilds = request.session.get("guilds", [])
    for g in guilds:
        if int(g["id"]) == guild_id and (int(g.get("permissions", 0)) & 0x8):
            return guild_id
    raise HTTPException(status_code=403, detail="Not admin of this guild")


# --- Models ---

class AddAccountRequest(BaseModel):
    username: str


# --- Endpoints ---

@router.get("/accounts")
async def get_accounts(request: Request, guild_id: int, user=Depends(get_current_user)):
    await get_admin_guild(request, guild_id)

    async with async_session() as session:
        db_guild = (await session.execute(
            select(Guild).where(Guild.guild_id == guild_id)
        )).scalar_one_or_none()

        if not db_guild:
            return {"accounts": []}

        result = await session.execute(
            select(TikTokAccount.username, TikTokAccount.enabled)
            .join(GuildTikTokSubscription)
            .where(GuildTikTokSubscription.guild_id == db_guild.id)
        )
        accounts = [{"username": row[0], "enabled": row[1]} for row in result.all()]

    return {"accounts": accounts}


@router.post("/accounts")
async def add_account(request: Request, guild_id: int, data: AddAccountRequest, user=Depends(get_current_user)):
    await get_admin_guild(request, guild_id)
    username = data.username.lower().strip()

    async with async_session() as session:
        db_guild = (await session.execute(
            select(Guild).where(Guild.guild_id == guild_id)
        )).scalar_one_or_none()

        if not db_guild:
            db_guild = Guild(guild_id=guild_id)
            session.add(db_guild)
            await session.flush()

        account = (await session.execute(
            select(TikTokAccount).where(TikTokAccount.username == username)
        )).scalar_one_or_none()

        if not account:
            account = TikTokAccount(username=username)
            session.add(account)
            await session.flush()

        sub_exists = (await session.execute(
            select(GuildTikTokSubscription).where(
                GuildTikTokSubscription.guild_id == db_guild.id,
                GuildTikTokSubscription.account_id == account.id,
            )
        )).scalar_one_or_none()

        if sub_exists:
            raise HTTPException(status_code=400, detail="Account already monitored")

        session.add(GuildTikTokSubscription(guild_id=db_guild.id, account_id=account.id))
        await session.commit()

    return {"status": "added", "username": username}


@router.delete("/accounts/{username}")
async def remove_account(request: Request, guild_id: int, username: str, user=Depends(get_current_user)):
    await get_admin_guild(request, guild_id)
    username = username.lower()

    async with async_session() as session:
        db_guild = (await session.execute(
            select(Guild).where(Guild.guild_id == guild_id)
        )).scalar_one_or_none()

        if not db_guild:
            raise HTTPException(status_code=404, detail="Guild not found")

        account = (await session.execute(
            select(TikTokAccount).where(TikTokAccount.username == username)
        )).scalar_one_or_none()

        if not account:
            raise HTTPException(status_code=404, detail="Account not found")

        await session.execute(
            delete(GuildTikTokSubscription).where(
                GuildTikTokSubscription.guild_id == db_guild.id,
                GuildTikTokSubscription.account_id == account.id,
            )
        )
        await session.commit()

    return {"status": "removed"}


@router.get("/logs")
async def get_logs(request: Request, guild_id: int, limit: int = 20, user=Depends(get_current_user)):
    await get_admin_guild(request, guild_id)

    async with async_session() as session:
        db_guild = (await session.execute(
            select(Guild).where(Guild.guild_id == guild_id)
        )).scalar_one_or_none()

        if not db_guild:
            return {"logs": []}

        subs = await session.execute(
            select(TikTokAccount.username)
            .join(GuildTikTokSubscription)
            .where(GuildTikTokSubscription.guild_id == db_guild.id)
        )
        usernames = [row[0] for row in subs.all()]

        if not usernames:
            return {"logs": []}

        logs = (await session.execute(
            select(VideoHistory)
            .where(VideoHistory.username.in_(usernames))
            .order_by(desc(VideoHistory.detected_at))
            .limit(limit)
        )).scalars().all()

        result = [
            {
                "id": log.id,
                "video_id": log.tiktok_video_id,
                "username": log.username,
                "video_url": log.video_url,
                "detected_at": log.detected_at.isoformat() if log.detected_at else None,
            }
            for log in logs
        ]

    return {"logs": result}


@router.get("/status")
async def get_system_status(user=Depends(get_current_user)):
    async with async_session() as session:
        total_accounts = len((await session.execute(
            select(TikTokAccount).where(TikTokAccount.enabled == True)
        )).scalars().all())

        total_videos = len((await session.execute(select(VideoHistory))).scalars().all())

    return {
        "monitored_accounts": total_accounts,
        "total_videos_detected": total_videos,
        "bot_online": True,
    }


@router.post("/force-check")
async def force_check(user=Depends(get_current_user)):
    return {"status": "Manual check triggered (bot will run in background)"}
