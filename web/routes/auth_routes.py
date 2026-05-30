from fastapi import APIRouter, Request, HTTPException, RedirectResponse
from starlette.responses import RedirectResponse
from config.settings import settings
from web.auth import get_discord_oauth_token, get_discord_user, get_user_guilds

router = APIRouter()

@router.get("/login")
async def login():
    """Redirect user to Discord OAuth2 consent screen."""
    redirect_uri = settings.DISCORD_REDIRECT_URI
    scope = "identify guilds"
    url = f"https://discord.com/api/oauth2/authorize?client_id={settings.DISCORD_CLIENT_ID}&redirect_uri={redirect_uri}&response_type=code&scope={scope}"
    return RedirectResponse(url)

@router.get("/callback")
async def auth_callback(request: Request, code: str = None):
    """Handle OAuth2 callback."""
    if not code:
        raise HTTPException(status_code=400, detail="Missing code")
        
    # Exchange code for token
    token_data = await get_discord_oauth_token(code, settings.DISCORD_REDIRECT_URI)
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token")
        
    # Get user info and guilds
    user = await get_discord_user(access_token)
    guilds = await get_user_guilds(access_token)
    
    # Store in session
    request.session["user"] = user
    request.session["guilds"] = guilds
    request.session["access_token"] = access_token
    
    return RedirectResponse(url="/")

@router.get("/logout")
async def logout(request: Request):
    """Clear session and logout."""
    request.session.clear()
    return RedirectResponse(url="/")