import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from config.settings import settings

router = APIRouter()


async def get_discord_oauth_token(code: str, redirect_uri: str) -> dict:
    """Exchange OAuth2 code for access token."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": settings.DISCORD_CLIENT_ID,
                "client_secret": settings.DISCORD_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        return response.json()


async def get_discord_user(access_token: str) -> dict:
    """Fetch authenticated user info from Discord."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()


async def get_user_guilds(access_token: str) -> list:
    """Fetch guilds the authenticated user is in."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://discord.com/api/users/@me/guilds",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        return response.json()


@router.get("/login")
async def login():
    """Redirect user to Discord OAuth2 consent screen."""
    redirect_uri = settings.DISCORD_REDIRECT_URI
    scope = "identify guilds"
    url = (
        f"https://discord.com/api/oauth2/authorize"
        f"?client_id={settings.DISCORD_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scope}"
    )
    return RedirectResponse(url)


@router.get("/callback")
async def auth_callback(request: Request, code: str = None):
    """Handle OAuth2 callback."""
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")

    token_data = await get_discord_oauth_token(code, settings.DISCORD_REDIRECT_URI)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token")

    user = await get_discord_user(access_token)
    guilds = await get_user_guilds(access_token)

    request.session["user"] = user
    request.session["guilds"] = guilds
    request.session["access_token"] = access_token

    return RedirectResponse(url="/dashboard/home")


@router.get("/logout")
async def logout(request: Request):
    """Clear session and logout."""
    request.session.clear()
    return RedirectResponse(url="/")
