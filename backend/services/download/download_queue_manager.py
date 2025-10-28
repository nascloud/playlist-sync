
import asyncio
import sqlite3
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from core.database import get_db_connection
from services.download.download_db_service import download_db_service
from schemas.download import DownloadQueueItem, DownloadQueueItemCreate
from core.logging_config import download_log_manager
from services.download.downloader_core import downloader as downloader_core
from services.settings_service import SettingsService
from services.auto_playlist_service import AutoPlaylistService
import logging

logger = logging.getLogger(__name__)

class DownloadQueueManager:
    """
    管理和处理下载队列。
    负责并发控制、任务调度和状态更新。
    """
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.download_semaphore = asyncio.Semaphore(self.max_concurrent)
        self.active_downloads: Dict[int, asyncio.Task] = {}
        self._is_processing = False
        self._downloader_initialized = False

    async def add_to_queue(self, task_id: int, session_type: str, items: List[DownloadQueueItemCreate], conn: Optional[sqlite3.Connection] = None) -> int:
        """
        将一批下载项添加到队列。如果存在与task_id关联的活跃会话，则将项目添加到该会话；否则，创建新会话。
        """
        count = len(items)
        if count == 0:
            return 0

        loop = asyncio.get_running_loop()

        def _add_logic():
            conn = get_db_connection()
            try:
                # 1. 查找与 task_id 关联的最新会话
                existing_session_id = download_db_service.find_latest_session_by_task_id(task_id, conn=conn)

                if existing_session_id:
                    # 2a. 加入现有会话
                    logger.info(f"找到任务 {task_id} 的现有会话 {existing_session_id}，将合并 {count} 个项目。")
                    # 重新激活（如果是 'completed' 状态）
                    download_db_service.reactivate_session(existing_session_id, conn=conn)
                    # 更新歌曲总数
                    download_db_service.update_session_song_count(existing_session_id, count, conn=conn)
                    # 添加新项目
                    download_db_service.add_items_to_queue(existing_session_id, items, conn=conn)
                    conn.commit()
                    return existing_session_id
                else:
                    # 2b. 创建新会话
                    logger.info(f"未找到任务 {task_id} 的会话，将创建新会话。")
                    session_id = download_db_service.create_download_session(
                        task_id, session_type, count, conn=conn
                    )
                    download_db_service.add_items_to_queue(session_id, items, conn=conn)
                    conn.commit()
                    return session_id
            except Exception as e:
                conn.rollback()
                logger.error(f"添加项目到队列时发生数据库错误: {e}", exc_info=True)
                raise
            finally:
                conn.close()

        session_id = await loop.run_in_executor(
            None, _add_logic
        )

        logger.info(f"会话 {session_id} 已更新/创建，并添加了 {count} 个项目到队列。")

        self.start_processing()
        return session_id

    async def _ensure_downloader_initialized(self):
        if self._downloader_initialized:
            return True
        
        print("下载器尚未初始化，正在加载设置...")
        loop = asyncio.get_running_loop()
        settings = await loop.run_in_executor(None, SettingsService.get_download_settings)
        
        if settings and settings.api_key:
            try:
                await loop.run_in_executor(
                    None,
                    downloader_core.initialize,
                    settings.download_path
                )
                self._downloader_initialized = True
                print("下载器初始化成功。")
                return True
            except Exception as e:
                logger.error(f"下载器初始化失败: {e}", exc_info=True)
                return False
        else:
            logger.error("无法初始化下载器：未找到下载设置或API Key。")
            return False

    def start_processing(self):
        if not self._is_processing:
            print("启动下载队列处理器...")
            self._is_processing = True
            asyncio.create_task(self.process_queue())

    async def process_queue(self):
        loop = asyncio.get_running_loop()
        if not await self._ensure_downloader_initialized():
            print("下载器初始化失败，队列处理已中止。")
            self._is_processing = False
            return

        while self._is_processing:
            # 我们需要确保不会获取到已暂停会话中的项目
            # 这是通过在 get_next_pending_item 中加入一个 JOIN 查询来实现的
            pending_item = await loop.run_in_executor(
                None, download_db_service.get_next_pending_item
            )

            if pending_item:
                queue_id = pending_item.id
                logger.debug(f"从队列中获取到新项目: ID {queue_id}, 标题: {pending_item.title}")
                await self.download_semaphore.acquire()
                logger.debug(f"项目 {queue_id} 获得信号量，即将开始下载。")
                download_task = asyncio.create_task(self._download_worker(pending_item))
                self.active_downloads[queue_id] = download_task
            else:
                logger.debug("队列中没有待处理的项目，等待5秒...")
                await asyncio.sleep(5)

    async def _download_worker(self, item: DownloadQueueItem):
        queue_id = item.id
        session_id = item.session_id
        title = item.title
        
        # 获取此会话的专用 logger
        session_logger = download_log_manager.get_logger(session_id)
        
        session_logger.info(f"Worker开始处理下载任务: {title} (ID: {queue_id})")
        
        loop = asyncio.get_running_loop()

        try:
            # 在下载前获取最新的下载设置
            settings = await loop.run_in_executor(None, SettingsService.get_download_settings)
            preferred_quality = settings.preferred_quality if settings else '无损'
            download_lyrics = settings.download_lyrics if settings else False
            
            session_logger.info(f"使用下载设置: 音质='{preferred_quality}', 下载歌词={download_lyrics}")

            # 调用真实的下载器逻辑,并增加300秒超时
            file_path = await asyncio.wait_for(
                downloader_core.download(item, preferred_quality, download_lyrics, session_logger), 
                timeout=300.0
            )

            await asyncio.get_running_loop().run_in_executor(
                None, download_db_service.update_queue_item_status, queue_id, "success"
            )
            session_logger.info(f"下载成功: {title} (ID: {queue_id})。文件保存在: {file_path}")
            
        except Exception as e:
            error_msg = str(e)
            session_logger.error(f"下载失败: {title} (ID: {queue_id}), 原因: {error_msg}", exc_info=True)
            await asyncio.get_running_loop().run_in_executor(
                None,
                download_db_service.update_queue_item_status,
                queue_id,
                "failed",
                error_msg,
            )
        except BaseException as e:
            # 捕获所有异常，包括系统退出等，确保状态被正确更新
            error_msg = f"下载过程中发生严重错误: {str(e)}"
            session_logger.error(f"下载严重错误: {title} (ID: {queue_id}), 原因: {error_msg}", exc_info=True)
            await asyncio.get_running_loop().run_in_executor(
                None,
                download_db_service.update_queue_item_status,
                queue_id,
                "failed",
                error_msg,
            )
            
        finally:
            # 检查会话是否已完成，如果已完成则触发自动播放列表处理
            def check_session_completed():
                conn = get_db_connection()
                try:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT ds.status, ds.total_songs, 
                               COALESCE(ds.success_count, 0) as success_count, 
                               COALESCE(ds.failed_count, 0) as failed_count,
                               ds.id as session_id
                        FROM download_sessions ds 
                        WHERE ds.id = ?
                    """, (session_id,))
                    session_info = cursor.fetchone()
                    if session_info and session_info['status'] == 'completed':
                        # 会话已完成，触发自动播放列表处理
                        return True, session_info['session_id']
                    return False, None
                finally:
                    conn.close()
            
            loop = asyncio.get_running_loop()
            is_completed, completed_session_id = await loop.run_in_executor(None, check_session_completed)
            
            if is_completed and completed_session_id:
                await self._trigger_auto_playlist_processing(completed_session_id, session_logger)
            
            session_logger.debug(f"项目 {queue_id} 释放信号量。")
            self.download_semaphore.release()
            del self.active_downloads[queue_id]

    async def pause_session(self, session_id: int):
        """暂停一个下载会话及其所有待处理的项目。"""
        logger.info(f"请求暂停会话 {session_id}...")
        
        # 1. 在数据库中将所有相关项目标记为 'paused'
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, download_db_service.pause_session_and_items, session_id
        )
        logger.info(f"数据库中的会话 {session_id} 及其项目已标记为暂停。")

        # 2. 取消所有属于该会话的、当前正在活跃的下载任务
        # 我们需要一种方法来从 item.id 映射到 session_id。
        # 暂时，我们将迭代活跃任务并检查它们的 session_id。
        # 这在有大量并发时效率不高，但对于小规模是可行的。
        # 一个更好的实现可能是在 self.active_downloads 中存储更丰富的信息。
        
        # 获取属于该会话的所有活跃任务ID
        active_ids_to_cancel = []
        for queue_id, task in self.active_downloads.items():
            # 这里需要一个方法从 queue_id 找到 session_id
            # 这是一个设计缺陷，我们暂时通过数据库查询来弥补
            item_details = await self.get_item_details_from_db(queue_id) # 需要实现这个辅助方法
            if item_details and item_details.session_id == session_id:
                active_ids_to_cancel.append(queue_id)

        logger.info(f"在会话 {session_id} 中找到 {len(active_ids_to_cancel)} 个需要取消的活跃下载。")

        for queue_id in active_ids_to_cancel:
            task = self.active_downloads.get(queue_id)
            if task:
                task.cancel()
                logger.info(f"已取消活跃的下载任务: {queue_id}")
        
        logger.info(f"会话 {session_id} 已成功暂停。")

    async def _trigger_auto_playlist_processing(self, session_id: int, session_logger: logging.Logger):
        """触发自动播放列表处理"""
        try:
            # 获取session_id对应的task_id
            task_id = download_db_service.get_task_id_by_session_id(session_id)
            if task_id:
                session_logger.info(f"触发自动播放列表处理 for task {task_id}")
                # 获取AutoPlaylistService实例
                try:
                    auto_playlist_service = AutoPlaylistService.get_instance()
                    # 获取Plex音乐库实例
                    # 注意：这需要plex_service已经初始化
                    if auto_playlist_service.plex_service:
                        music_library = await auto_playlist_service.plex_service.get_music_library()
                        if music_library:
                            # 首先触发Plex扫描新文件
                            session_logger.info("触发Plex扫描新文件")
                            scan_result = await auto_playlist_service.plex_service.scan_and_refresh(music_library)
                            if scan_result:
                                session_logger.info("Plex扫描请求已发送")
                            else:
                                session_logger.warning("Plex扫描请求失败")
                            
                            # 处理最近5分钟内添加的音轨（给Plex一些时间来索引文件）
                            since_time = datetime.now().replace(microsecond=0) - timedelta(minutes=5)
                            await auto_playlist_service.process_tracks_for_task(task_id, music_library, since_time)
                            session_logger.info(f"自动播放列表处理完成 for task {task_id}")
                        else:
                            session_logger.warning(f"未能获取Plex音乐库实例")
                    else:
                        session_logger.warning(f"PlexService未初始化")
                except RuntimeError as e:
                    session_logger.warning(f"AutoPlaylistService未初始化: {e}")
            else:
                session_logger.warning(f"未能找到session {session_id} 对应的task_id")
        except Exception as e:
            session_logger.error(f"自动播放列表处理失败: {e}", exc_info=True)

    async def get_item_details_from_db(self, queue_id: int) -> Optional[DownloadQueueItem]:
        """(辅助方法) 从数据库获取单个队列项目的详细信息。"""
        def _get_details(conn: sqlite3.Connection, item_id: int) -> Optional[DownloadQueueItem]:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM download_queue WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            if row:
                # 为了避免Pydantic验证错误，我们需要确保返回的字段与模型匹配
                # 这是一个简化的示例，并未处理所有字段的默认值/格式
                return DownloadQueueItem(
                    id=row['id'],
                    session_id=row['session_id'],
                    song_id=row['song_id'],
                    title=row['title'],
                    artist=row['artist'],
                    album=row['album'],
                    status=row['status'],
                    quality=row['quality'],
                    retry_count=row['retry_count'] or 0,
                    error_message=row['error_message'],
                    created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')) if row['created_at'] else datetime.now(),
                    updated_at=datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00')) if row['updated_at'] else datetime.now()
                )
            return None

        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, _get_details, get_db_connection(), queue_id)

    async def resume_session(self, session_id: int):
        """恢复一个已暂停的下载会话。"""
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, download_db_service.resume_session_and_items, session_id
        )
        print(f"会话 {session_id} 已被请求恢复。")
        self.start_processing() # 恢复后，确保队列处理器在运行

    async def delete_session(self, session_id: int):
        """删除一个下载会话及其所有关联的项目。"""
        # 与暂停类似，理想情况下先取消活跃任务
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, download_db_service.delete_session_and_items, session_id
        )
        print(f"会话 {session_id} 已被请求删除。")

    async def retry_item(self, item_id: int):
        """重试一个失败的下载项目。"""
        loop = asyncio.get_running_loop()
        success = await loop.run_in_executor(
            None, download_db_service.retry_queue_item, item_id
        )
        if success:
            print(f"项目 {item_id} 已被重新加入队列。")
            self.start_processing() # 确保队列正在运行
        else:
            # 如果数据库更新失败，尝试获取当前项目状态并记录日志
            item_details = await self.get_item_details_from_db(item_id)
            if item_details:
                logger.warning(f"无法重试项目 {item_id}，当前状态为: {item_details.status}")
            else:
                logger.warning(f"无法重试项目 {item_id}，项目不存在或数据库查询失败")
        return success

    async def clear_completed(self):
        """清除所有已完成的下载会话及其关联的项目。"""
        loop = asyncio.get_running_loop()
        count = await loop.run_in_executor(
            None, download_db_service.delete_completed_sessions
        )
        logger.info(f"清除了 {count} 个已完成的会话。")
        return count
        
    async def retry_failed_items_in_session(self, session_id: int):
        """重试一个会话中所有失败的项目。"""
        loop = asyncio.get_running_loop()
        count = await loop.run_in_executor(
            None, download_db_service.retry_failed_items_in_session, session_id
        )
        if count > 0:
            print(f"会话 {session_id} 中的 {count} 个失败项目已被重新加入队列。")
            self.start_processing() # 确保队列正在运行
            return count
        else:
            # 检查是否是因为计数器不一致导致的问题
            # 修复会话计数器并再次检查
            success_count, failed_count = await loop.run_in_executor(
                None, download_db_service.fix_session_counts, session_id
            )
            
            if failed_count > 0:
                # 计数器修复后有失败项目，再次尝试重试
                count = await loop.run_in_executor(
                    None, download_db_service.retry_failed_items_in_session, session_id
                )
                if count > 0:
                    print(f"会话 {session_id} 中的 {count} 个失败项目已被重新加入队列。")
                    self.start_processing() # 确保队列正在运行
                    return count
            
            return 0
        
# 实例化管理器，以便在应用的其他部分导入和使用
download_queue_manager = DownloadQueueManager()
