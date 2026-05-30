import aiohttp
import json
import re
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger("tiktok_monitor")

class TikTokMonitor:
    """Service to fetch latest videos from a TikTok user using public API."""
    
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }
    
    async def get_latest_videos(self, username: str, limit: int = 5) -> List[Dict]:
        """
        Fetch latest videos from a TikTok user.
        
        Returns list of dicts with keys: id, description, url, thumbnail, published_at
        """
        try:
            # Step 1: Get user info (secUid) from profile page
            user_info = await self._get_user_info(username)
            if not user_info:
                logger.error(f"Could not fetch user info for @{username}")
                return []
                
            sec_uid = user_info.get("secUid")
            user_id = user_info.get("uniqueId")
            
            # Step 2: Fetch video list using API
            videos = await self._fetch_videos_api(sec_uid, user_id, limit)
            return videos
            
        except Exception as e:
            logger.exception(f"Error fetching videos for @{username}: {e}")
            return []
            
    async def _get_user_info(self, username: str) -> Optional[Dict]:
        """Scrape user info from TikTok profile page to get secUid."""
        url = f"https://www.tiktok.com/@{username}"
        async with aiohttp.ClientSession(headers=self.HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logger.warning(f"Failed to fetch profile {username}, status: {resp.status}")
                    return None
                    
                html = await resp.text()
                
                # Extract __UNIVERSAL_DATA__ JSON
                pattern = r'<script id="__UNIVERSAL_DATA__" type="application/json">(.*?)</script>'
                match = re.search(pattern, html, re.DOTALL)
                if not match:
                    logger.error(f"Could not find universal data for @{username}")
                    return None
                    
                data = json.loads(match.group(1))
                
                # Navigate to user info
                try:
                    user_info = data["__DEFAULT_SCOPE__"]["webapp.user-detail"]["userInfo"]
                    return user_info.get("user", {})
                except KeyError:
                    logger.error(f"User info structure unexpected for @{username}")
                    return None
                    
    async def _fetch_videos_api(self, sec_uid: str, user_id: str, limit: int) -> List[Dict]:
        """Fetch video list from TikTok's internal API."""
        url = "https://www.tiktok.com/api/post/item_list/"
        params = {
            "aid": "1988",
            "count": str(min(limit, 30)),
            "cursor": "0",
            "secUid": sec_uid,
            "uniqueId": user_id,
            "source": "0"
        }
        headers = {
            **self.HEADERS,
            "Referer": f"https://www.tiktok.com/@{user_id}",
        }
        
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    logger.warning(f"API request failed with status {resp.status}")
                    return []
                    
                data = await resp.json()
                items = data.get("itemList", [])
                
                videos = []
                for item in items:
                    video = {
                        "id": item.get("id", ""),
                        "description": item.get("desc", ""),
                        "url": f"https://www.tiktok.com/@{user_id}/video/{item.get('id', '')}",
                        "thumbnail": item.get("video", {}).get("cover", ""),
                        "published_at": self._parse_timestamp(item.get("createTime"))
                    }
                    videos.append(video)
                    
                return videos[:limit]
                
    def _parse_timestamp(self, ts) -> Optional[datetime]:
        """Convert Unix timestamp to datetime."""
        if ts:
            try:
                return datetime.fromtimestamp(int(ts))
            except:
                pass
        return None