
import asyncio
import logging
from typing import List, Dict, Any, Optional

from core.database import get_db_connection
from services.settings_service import SettingsService
from services.download_queue_manager import download_queue_manager
from schemas.download import DownloadQueueItemCreate
from schemas.download_schemas import DownloadSingleRequest
from services.task_service import TaskService
from .downloader_core import DownloaderCore, downloader

logger = logging.getLogger(__name__)

class DownloadService:
    """
    核心服务，用于管理下载任务的创建、执行和监控。
    """
    def __init__(self, settings_service: SettingsService):
        self.downloader: Optional[DownloaderCore] = None
        self.queue_manager = download_queue_manager
        self.settings_service = settings_service
        self.task_service = TaskService()

    async def initialize_downloader(self):
        """
        根据系统设置初始化或重新初始化下载器。
        """
        self.downloader = downloader
        
        loop = asyncio.get_running_loop()
        settings = await loop.run_in_executor(None, self.settings_service.get_download_settings)
        
        if not settings or not settings.api_key:
            logger.warning("下载服务的 API Key 未配置，下载功能将不可用。")
            return

        self.downloader.initialize(api_key=settings.api_key, download_path=settings.download_path)
        logger.info("下载器初始化成功。")

    async def download_all_missing(self, task_id: int, db=None) -> int:
        """
        下载指定同步任务中所有缺失的歌曲。
        """
        # 验证 task_id 是否存在
        task = self.task_service.get_task_by_id(task_id)
        if not task:
            raise ValueError(f"任务ID {task_id} 不存在。")

        logger.info(f"任务 {task_id}: 请求批量下载所有缺失歌曲。")
        loop = asyncio.get_running_loop()
        unmatched_songs = await loop.run_in_executor(
            None, 
            self.task_service.get_unmatched_songs_for_task, 
            task_id
        )
        
        if not unmatched_songs:
            logger.info(f"任务 {task_id}: 没有找到未匹配的歌曲可供下载。")
            return 0
        
        download_items = [
            DownloadQueueItemCreate(
                title=song['title'], 
                artist=song['artist'],
                album=song.get('album'),
                song_id=song.get('song_id'),
                platform=task.platform
            ) for song in unmatched_songs
        ]

        session_id = await self.queue_manager.add_to_queue(
            task_id=task_id,
            session_type='batch',
            items=download_items,
            conn=db
        )
        return session_id

    async def download_single_song(self, task_id: int, song_info: DownloadSingleRequest, db=None) -> int:
        """
        下载单个指定的歌曲。
        """
        # 验证 task_id 是否存在
        task = self.task_service.get_task_by_id(task_id)
        if not task:
            raise ValueError(f"任务ID {task_id} 不存在。")
            
        logger.info(f"任务 {task_id}: 请求下载单曲 '{song_info.title}'。")
        
        item = DownloadQueueItemCreate(
            song_id=song_info.song_id,
            title=song_info.title,
            artist=song_info.artist,
            album=song_info.album,
            platform=task.platform
        )

        session_id = await self.queue_manager.add_to_queue(
            task_id=task_id,
            session_type='individual',
            items=[item],
            conn=db
        )
        return session_id

    async def _get_auto_download_settings(self, task_id: int) -> dict:
        """从数据库获取全局下载设置和特定任务的设置"""
        
        def db_calls():
            conn = get_db_connection()
            try:
                cursor = conn.cursor()
                # 获取全局设置
                cursor.execute("SELECT value FROM download_settings WHERE key = 'auto_download'")
                global_setting_row = cursor.fetchone()
                # 获取任务设置
                cursor.execute("SELECT auto_download FROM tasks WHERE id = ?", (task_id,))
                task_setting_row = cursor.fetchone()
                return {
                    "global_auto_download": bool(int(global_setting_row['value'])) if global_setting_row else False,
                    "task_auto_download": task_setting_row['auto_download'] if task_setting_row else False,
                }
            finally:
                conn.close()

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, db_calls)

    async def auto_download_missing(self, task_id: int) -> int:
        """
        在一个同步任务完成后，自动下载所有缺失的歌曲。
        只有在该任务和全局都启用了自动下载时才会触发。
        :param task_id: 同步任务的 ID
        :return: 创建的下载会话 ID，如果没有创建则返回 0
        """
        logger.info(f"任务 {task_id}: 检查是否需要自动下载。")
        
        settings = await self._get_auto_download_settings(task_id)
        
        if settings['global_auto_download'] and settings['task_auto_download']:
            logger.info(f"任务 {task_id}: 全局和任务均已启用自动下载，开始批量下载...")
            # 在新线程中，我们需要确保数据库操作使用正确的会话
            db = get_db_connection()
            try:
                return await self.download_all_missing(task_id, db=db)
            finally:
                db.close()
        else:
            logger.info(f"任务 {task_id}: 未满足自动下载条件 (全局: {settings['global_auto_download']}, 任务: {settings['task_auto_download']})。")
            return 0

# 实例化服务，以便在应用的其他部分导入和使用
download_service = DownloadService(settings_service=SettingsService())
