from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, func
from config.settings import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Keep old name for backwards compatibility
AsyncSessionLocal = async_session

Base = declarative_base()


class Guild(Base):
    __tablename__ = "guilds"
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(Integer, unique=True, nullable=False)
    notification_channel_id = Column(String, nullable=True)
    subscriptions = relationship("GuildTikTokSubscription", back_populates="guild")


class TikTokAccount(Base):
    __tablename__ = "tiktok_accounts"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    enabled = Column(Boolean, default=True)
    subscriptions = relationship("GuildTikTokSubscription", back_populates="account")


class GuildTikTokSubscription(Base):
    __tablename__ = "guild_tiktok_subscriptions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    guild_id = Column(Integer, ForeignKey("guilds.id"), nullable=False)
    account_id = Column(Integer, ForeignKey("tiktok_accounts.id"), nullable=False)
    guild = relationship("Guild", back_populates="subscriptions")
    account = relationship("TikTokAccount", back_populates="subscriptions")


class VideoHistory(Base):
    __tablename__ = "video_history"
    id = Column(Integer, primary_key=True, autoincrement=True)
    tiktok_video_id = Column(String, unique=True, nullable=False)
    username = Column(String, nullable=False)
    video_url = Column(String, nullable=True)
    detected_at = Column(DateTime, server_default=func.now())


async def init_db():
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Dependency for database sessions."""
    async with async_session() as session:
        yield session
