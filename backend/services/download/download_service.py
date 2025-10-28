
import asyncio
import logging
from typing import List, Dict, Any, Optional

from core.database import get_db_connection
from services.settings_service import SettingsService
from services.download.download_queue_manager import download_queue_manager
from schemas.download import DownloadQueueItemCreate
from schemas.download_schemas import DownloadSingleRequest, SearchResultItem, SearchResponse
from services.task_service import TaskService
from services.download.downloader_core import DownloaderCore, downloader

logger = logging.getLogger(__name__)

class DownloadService:
    """
    核心服务，用于管理下载任务的创建、执行和监控。
    """
    # 表示"搜索下载"的虚拟任务对象
    SEARCH_DOWNLOAD_TASK = {
        'id': 0,
        'name': '搜索下载'
    }
    
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

        if not settings or not settings.download_path:
            logger.warning("下载服务的下载路径未配置，下载功能将不可用。")
            return

        # 新的 initialize 方法不再需要 api_key
        self.downloader.initialize(download_path=settings.download_path)
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
        # 处理 task_id 为 0 或 None 的情况，将其视为"搜索下载"任务
        if task_id == 0 or task_id is None:
            # 对于搜索下载，使用默认平台
            platform = 'qq'  # 默认使用 qq 平台
            logger.info(f"搜索下载任务: 下载单曲 '{song_info.title}'。")
            # 使用搜索下载任务的ID
            effective_task_id = self.SEARCH_DOWNLOAD_TASK['id']
        else:
            # 验证 task_id 是否存在
            task = self.task_service.get_task_by_id(task_id)
            if not task:
                raise ValueError(f"任务ID {task_id} 不存在。")
            platform = task.platform
            logger.info(f"任务 {task_id}: 请求下载单曲 '{song_info.title}'。")
            effective_task_id = task_id
        
        item = DownloadQueueItemCreate(
            song_id=song_info.song_id,
            title=song_info.title,
            artist=song_info.artist,
            album=song_info.album,
            platform=platform
        )

        session_id = await self.queue_manager.add_to_queue(
            task_id=effective_task_id,
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

    async def search_songs(self, keyword: str, platform: Optional[str] = None,
                          page: int = 1, size: int = 10) -> SearchResponse:
        """
        搜索歌曲
        :param keyword: 搜索关键词
        :param platform: 可选，指定音乐平台
        :param page: 页码，默认为1
        :param size: 每页大小，默认为10
        :return: 搜索结果
        """
        try:
            # 确保下载器已初始化
            if not self.downloader:
                await self.initialize_downloader()
            
            if not self.downloader:
                return SearchResponse(
                    success=False,
                    message="下载器未初始化，请检查API Key配置",
                    results=[],
                    total=0,
                    page=page,
                    size=size
                )
            
            # 获取要搜索的平台列表
            platforms_to_search = []
            if platform:
                # 如果指定了平台，只搜索该平台
                mapped_platform = self.downloader.platform_service.map_platform_name(platform)
                platforms_to_search = [mapped_platform]
            else:
                # 否则搜索所有平台
                platforms_to_search = self.downloader.platform_service.get_platforms_to_search()
            
            all_results = []
            
            # 遍历所有平台进行搜索
            for plat in platforms_to_search:
                try:
                    logger.info(f"在平台 '{plat}' 上搜索关键词: '{keyword}'")
                    # 调用更新后的 search_platform 方法
                    search_results = await self.downloader.downloader.search_platform(plat, keyword, page, size)

                    # 新API直接在 'data' 键下返回列表
                    songs_list = search_results.get('data', [])
                    if not isinstance(songs_list, list):
                        logger.warning(f"平台 '{plat}' 的API响应格式不符合预期（'data' 不是列表）。")
                        songs_list = []

                    # 转换为SearchResultItem格式
                    for song in songs_list:
                        result_item = SearchResultItem(
                            song_id=str(song.get('id') or song.get('mid', '')),
                            title=song.get('song', ''),
                            artist=song.get('singer', ''),
                            album=song.get('album'),
                            platform=plat,
                            duration=song.get('interval'), # 'time' in docs, but 'interval' in example
                            quality=song.get('quality'),
                            score=None
                        )
                        all_results.append(result_item)

                    logger.info(f"在平台 '{plat}' 上找到 {len(songs_list)} 首歌曲")

                except Exception as e:
                    logger.error(f"在平台 '{plat}' 上搜索时出错: {e}")
                    logger.error(f"搜索参数 - 关键词: '{keyword}', 平台: '{plat}', 页码: {page}, 大小: {size}")
                    logger.error(f"错误类型: {type(e).__name__}")
                    logger.error(f"错误详情: {str(e)}")
                    # 如果是RetryError，记录更多详细信息
                    if "RetryError" in str(type(e)):
                        logger.error(f"重试错误详情: {e}")
                        if hasattr(e, 'last_attempt') and e.last_attempt:
                            logger.error(f"最后一次尝试的异常: {e.last_attempt.exception()}")
                    continue
            
            # 如果没有结果，返回空结果
            if not all_results:
                return SearchResponse(
                    success=True,
                    message=f"未找到与 '{keyword}' 相关的歌曲",
                    results=[],
                    total=0,
                    page=page,
                    size=size
                )
            
            # 计算分页
            total = len(all_results)
            start_idx = (page - 1) * size
            end_idx = start_idx + size
            paginated_results = all_results[start_idx:end_idx]
            
            return SearchResponse(
                success=True,
                message=f"成功找到 {total} 首与 '{keyword}' 相关的歌曲",
                results=paginated_results,
                total=total,
                page=page,
                size=size
            )
            
        except Exception as e:
            logger.exception(f"搜索歌曲时发生错误:")
            return SearchResponse(
                success=False,
                message=f"搜索失败: {str(e)}",
                results=[],
                total=0,
                page=page,
                size=size
            )

# 全局变量，用于存储 DownloadService 的单例
_download_service_instance: Optional[DownloadService] = None

def get_download_service() -> "DownloadService":
    """
    依赖注入函数，用于获取 DownloadService 的单例。
    确保返回的是已初始化的实例。
    """
    global _download_service_instance
    if _download_service_instance is None:
        # 在正常应用生命周期外（如测试或脚本），创建一个临时实例
        # 注意：在 FastAPI 应用中，这个分支不应该被执行
        _download_service_instance = DownloadService(settings_service=SettingsService())
        logger.warning("DownloadService 在应用生命周期外被临时实例化。")
    return _download_service_instance

def set_download_service(instance: "DownloadService"):
    """在应用启动时设置服务实例"""
    global _download_service_instance
    _download_service_instance = instance

