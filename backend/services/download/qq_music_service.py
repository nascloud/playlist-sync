"""QQ音乐信息补全服务"""

import logging
from typing import Optional, Dict
import httpx

logger = logging.getLogger(__name__)

class QQMusicService:
    """处理QQ音乐相关信息的获取和缓存"""
    
    def __init__(self):
        # 缓存QQ音乐歌曲详情，避免重复请求
        self._qq_song_detail_cache: Dict[str, Dict] = {}
    
    async def fetch_song_detail(self, songmid: str, session_logger: logging.Logger) -> Optional[Dict]:
        """
        获取QQ音乐歌曲详情（用于补全缺失信息）
        :param songmid: 歌曲MID
        :param session_logger: 日志记录器
        :return: 包含歌曲详情的字典，如果获取失败则返回None
        """
        # 检查缓存
        if songmid in self._qq_song_detail_cache:
            session_logger.debug(f"从缓存中获取QQ音乐歌曲详情 (songmid: {songmid})")
            return self._qq_song_detail_cache[songmid]
        
        url = "https://c.y.qq.com/v8/fcg-bin/fcg_play_single_song.fcg"
        params = {
            'songmid': songmid,
            'platform': 'yqq',
            'format': 'json'
        }
        headers = {
            'Referer': 'https://y.qq.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                if data.get('code') == 0 and data.get('data'):
                    song_data = data['data'][0] if isinstance(data['data'], list) else data['data']
                    # 缓存结果
                    self._qq_song_detail_cache[songmid] = song_data
                    session_logger.debug(f"成功获取QQ音乐歌曲详情 (songmid: {songmid})")
                    return song_data
                else:
                    session_logger.warning(f"QQ音乐歌曲详情API返回错误 (songmid: {songmid}, code: {data.get('code')})")
        except Exception as e:
            session_logger.warning(f"获取QQ音乐歌曲详情失败 (songmid: {songmid}): {e}")
        
        return None
    
    def get_cached_detail(self, songmid: str) -> Optional[Dict]:
        """获取缓存的歌曲详情"""
        return self._qq_song_detail_cache.get(songmid)
    
    def clear_cache(self):
        """清空缓存"""
        self._qq_song_detail_cache.clear()