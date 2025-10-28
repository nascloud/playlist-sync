"""平台映射和搜索服务"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Tuple
import httpx
from thefuzz import fuzz

from services.download.download_constants import PLATFORM_MAPPING, PLATFORM_SEARCH_ORDER
from services.download.download_exceptions import APIError

logger = logging.getLogger(__name__)

class PlatformService:
    """处理平台相关的映射和搜索功能"""
    
    def map_platform_name(self, platform: str) -> str:
        """将面向用户的平台名称映射到 API 特定的名称。"""
        return PLATFORM_MAPPING.get(platform.lower(), platform)
    
    async def search_song_on_platform(self, search_term: str, platform: str, 
                                     page: int = 1, size: int = 10) -> Dict[str, Any]:
        """
        在指定平台上搜索歌曲
        注意：此方法需要与MusicDownloader集成以实际执行搜索
        """
        # 此方法将在重构后的DownloaderCore中实现具体逻辑
        pass
    
    def filter_and_score_candidates(self, item, songs_list: List[Dict[str, Any]], platform: str) -> List[Dict[str, Any]]:
        """过滤并评分候选歌曲"""
        candidates: List[Dict[str, Any]] = []
        for result in songs_list:
            # 新API返回的字段是'song'和'singer'
            title_match = fuzz.ratio(item.title, result.get('song', ''))
            artist_match = fuzz.ratio(item.artist, result.get('singer', ''))

            score = (title_match * 0.6) + (artist_match * 0.4)

            # song_id 可能是 'id' 或 'mid'
            song_id = result.get('id') or result.get('mid')

            if song_id:
                candidate = {
                    "song_id": str(song_id),  # 确保 song_id 是字符串
                    "platform": platform,
                    "score": score,
                    "name": result.get('song'),
                    "artist": result.get('singer')
                }
                candidates.append(candidate)

        # 按分数降序排序
        return sorted(candidates, key=lambda x: x['score'], reverse=True)
    
    def get_platforms_to_search(self, preferred_platform: Optional[str] = None, 
                               exclude_platforms: Optional[List[str]] = None) -> List[str]:
        """获取需要搜索的平台列表"""
        if exclude_platforms is None:
            exclude_platforms = []
            
        platforms_to_search = [p for p in PLATFORM_SEARCH_ORDER if p not in exclude_platforms]
        
        # 如果指定了平台，则优先搜索该平台
        if preferred_platform:
            if preferred_platform in platforms_to_search:
                platforms_to_search.insert(0, platforms_to_search.pop(platforms_to_search.index(preferred_platform)))
        
        return platforms_to_search