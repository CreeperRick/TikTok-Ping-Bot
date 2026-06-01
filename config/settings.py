import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Discord
    DISCORD_TOKEN: str = os.getenv("DISCORD_TOKEN", "")
    DISCORD_CLIENT_ID: str = os.getenv("DISCORD_CLIENT_ID", "")
    DISCORD_CLIENT_SECRET: str = os.getenv("DISCORD_CLIENT_SECRET", "")
    DISCORD_REDIRECT_URI: str = os.getenv("DISCORD_REDIRECT_URI", "http://192.168.1.177:8000/auth/callback")

    # Web
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change_this_in_production")

    # TikTok Monitoring
    TIKTOK_POLL_INTERVAL_MINUTES: int = int(os.getenv("TIKTOK_POLL_INTERVAL_MINUTES", "5"))
    TIKTOK_FETCH_LIMIT: int = int(os.getenv("TIKTOK_FETCH_LIMIT", "5"))

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./tiktok_bot.db")

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
