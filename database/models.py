from sqlalchemy import Column, Integer, String, Boolean, DateTime, BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Guild(Base):
    __tablename__ = "guilds"
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, unique=True, nullable=False)
    notification_channel_id = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("GuildTikTokSubscription", back_populates="guild", cascade="all, delete-orphan")

class TikTokAccount(Base):
    __tablename__ = "tiktok_accounts"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    subscriptions = relationship("GuildTikTokSubscription", back_populates="account", cascade="all, delete-orphan")

class GuildTikTokSubscription(Base):
    __tablename__ = "guild_tiktok_subscriptions"
    
    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey("guilds.id", ondelete="CASCADE"), nullable=False)
    account_id = Column(Integer, ForeignKey("tiktok_accounts.id", ondelete="CASCADE"), nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    guild = relationship("Guild", back_populates="subscriptions")
    account = relationship("TikTokAccount", back_populates="subscriptions")
    
    __table_args__ = (
        UniqueConstraint('guild_id', 'account_id', name='unique_guild_account'),
    )

class VideoHistory(Base):
    __tablename__ = "video_history"
    
    id = Column(Integer, primary_key=True)
    tiktok_video_id = Column(String(100), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=False, index=True)
    video_url = Column(String(500), nullable=False)
    published_at = Column(DateTime, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)