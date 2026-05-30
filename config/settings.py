import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Discord
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID")
    DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")
    DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI", "http://localhost:8000/auth/callback")
    
    # Web
    SECRET_KEY = os.getenv("SECRET_KEY", "change_this_in_production")
    
    # TikTok Monitoring
    TIKTOK_POLL_INTERVAL_MINUTES = int(os.getenv("TIKTOK_POLL_INTERVAL_MINUTES", "5"))
    TIKTOK_FETCH_LIMIT = int(os.getenv("TIKTOK_FETCH_LIMIT", "5"))
    
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./tiktok_bot.db")
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

settings = Settings()