import asyncio
import logging
from datetime import datetime, timedelta
from services.sync_service import SyncService

logger = logging.getLogger(__name__)

async def periodic_new_track_processing(sync_service: SyncService):
    """
    定期处理新添加的音轨
    :param sync_service: SyncService实例
    """
    logger.info("[定期扫描] 开始执行新音轨处理任务...")
    try:
        # 获取AutoPlaylistService实例
        auto_playlist_service = sync_service.auto_playlist_service
        if not auto_playlist_service:
            logger.warning("[定期扫描] AutoPlaylistService未初始化")
            return
            
        # 获取PlexService实例
        plex_service = auto_playlist_service.plex_service
        if not plex_service:
            logger.warning("[定期扫描] PlexService未初始化")
            return
            
        # 获取音乐库
        music_library = await plex_service.get_music_library()
        if not music_library:
            logger.warning("[定期扫描] 未能获取Plex音乐库")
            return
            
        # 处理最近1小时内添加的音轨
        since_time = datetime.now().replace(microsecond=0) - timedelta(hours=1)
        await auto_playlist_service.process_newly_added_tracks(music_library, since_time)
        
        logger.info("[定期扫描] 新音轨处理任务完成")
        
    except Exception as e:
        logger.error(f"[定期扫描] 处理新音轨时出错: {e}", exc_info=True)