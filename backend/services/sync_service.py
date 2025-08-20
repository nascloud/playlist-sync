import json
import asyncio
from services.plex_service import PlexService
from services.playlist_service import PlaylistService
from services.task_service import TaskService
from core.database import get_db_connection
from core.security import decrypt_token
import logging
from typing import Callable
from utils.progress_manager import progress_manager
from asyncio import Lock
from services.download.download_service import DownloadService
from services.auto_playlist_service import AutoPlaylistService

logger = logging.getLogger(__name__)

class SyncService:
    def __init__(self, download_service: DownloadService):
        self.plex_service = None
        self.playlist_service = PlaylistService()
        self.download_service = download_service
        # 初始化AutoPlaylistService
        self.auto_playlist_service = None
    
    async def initialize_auto_playlist_service(self):
        """初始化AutoPlaylistService"""
        try:
            # 如果还没有PlexService实例，尝试初始化一个默认的
            if self.plex_service is None:
                # 获取默认服务器设置（ID为1的服务器）
                settings = await asyncio.to_thread(self._get_settings_sync, 1)
                if settings and settings['type'] == 'plex':
                    url = settings['url']
                    encrypted_token = settings['token']
                    verify_ssl = settings.get('verify_ssl', True)
                    token = await asyncio.to_thread(decrypt_token, encrypted_token)
                    self.plex_service = await PlexService.create_instance(url, token, verify_ssl)
            
            # 初始化AutoPlaylistService
            if self.auto_playlist_service is None and self.plex_service is not None:
                self.auto_playlist_service = AutoPlaylistService(plex_service=self.plex_service, task_service=TaskService())
                AutoPlaylistService.set_instance(self.auto_playlist_service)
                logger.info("AutoPlaylistService initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize AutoPlaylistService: {e}")
            # 不抛出异常，因为AutoPlaylistService是可选功能
    
    async def _initialize_plex_service(self, server_id: int):
        """(异步) 根据 server_id 获取设置并初始化对应的媒体服务客户端"""
        
        # 伪代码/未来规划:
        # 每次同步都可能针对不同服务器，因此简单地检查 self.plex_service 已不够。
        # 应该为每个 server_id 缓存一个客户端实例，或在每次调用时重新创建。
        # 这里为了简单起见，我们每次都重新创建。

        settings = await asyncio.to_thread(self._get_settings_sync, server_id)
        if not settings:
            raise Exception(f"未找到 ID 为 {server_id} 的服务器设置")
        
        server_type = settings['type']
        url = settings['url']
        encrypted_token = settings['token']
        verify_ssl = settings.get('verify_ssl', True)  # 默认为 True
        
        # 伪代码/未来规划:
        # if server_type == 'plex':
        #     token = await asyncio.to_thread(decrypt_token, encrypted_token)
        #     self.plex_service = await PlexService.create_instance(url, token, verify_ssl)
        # elif server_type == 'emby':
        #     # self.media_service = await EmbyService.create_instance(...)
        #     raise NotImplementedError("Emby 服务尚未支持。")
        # else:
        #     raise Exception(f"不支持的服务器类型: {server_type}")
        
        # 当前实现只支持 Plex
        if server_type != 'plex':
            raise Exception(f"当前同步任务仅支持Plex服务器，但任务配置的服务器类型为 '{server_type}'。")

        token = await asyncio.to_thread(decrypt_token, encrypted_token)
        self.plex_service = await PlexService.create_instance(url, token, verify_ssl)
        
        # 初始化AutoPlaylistService
        if self.auto_playlist_service is None:
            self.auto_playlist_service = AutoPlaylistService(plex_service=self.plex_service, task_service=TaskService())
            AutoPlaylistService.set_instance(self.auto_playlist_service)

    async def preview_playlist(self, playlist_url: str, platform: str):
        """
        预览歌单，返回标题和歌曲数量。
        """
        try:
            external_playlist = await self.playlist_service.parse_playlist(playlist_url, platform)
            return {
                "title": external_playlist.get('title', '未知标题'),
                "track_count": len(external_playlist.get('tracks', []))
            }
        except Exception as e:
            logger.error(f"预览歌单失败: {playlist_url}, 错误: {e}")
            raise e
    
    async def _match_tracks(self, task_id, external_playlist, music_library):
        total_tracks = len(external_playlist['tracks'])
        TaskService.update_task_status(task_id, 'matching', '正在匹配歌曲...')
        await progress_manager.send_message(
            task_id,
            json.dumps({"status": "matching", "message": f"开始匹配 {total_tracks} 首歌曲...", "progress": 0, "total": total_tracks}),
            event="progress"
        )

        matched_plex_tracks = []
        unmatched_tracks_info = []
        
        processed_count = 0
        counter_lock = Lock()

        async def progress_callback():
            nonlocal processed_count
            async with counter_lock:
                processed_count += 1
                await progress_manager.send_message(
                    task_id,
                    json.dumps({
                        "status": "matching",
                        "message": f"正在匹配歌曲... ({processed_count}/{total_tracks})",
                        "progress": processed_count,
                        "total": total_tracks
                    }),
                    event="progress"
                )

        match_tasks = [
            self.plex_service.find_track_with_score(
                t['title'], t['artist'], t.get('album'), music_library, progress_callback
            ) for t in external_playlist['tracks']
        ]
        results = await asyncio.gather(*match_tasks)

        for i, (plex_track, score) in enumerate(results):
            if plex_track:
                matched_plex_tracks.append(plex_track)
            else:
                unmatched_tracks_info.append(external_playlist['tracks'][i])
        
        return matched_plex_tracks, unmatched_tracks_info

    async def sync_playlist(self, task_id: int, server_id: int, playlist_url: str, platform: str, 
                          playlist_name: str, log_callback: Callable = None) -> bool:
        """
        (异步) 同步播放列表到Plex，并发送实时进度。
        """
        
        # 创建一个安全的 log_callback 副本，以防在子函数中被意外修改。
        # 确保我们总是使用原始的、可调用的回调函数。
        safe_log_callback = log_callback if callable(log_callback) else None

        if safe_log_callback: safe_log_callback('info', f'开始同步任务: {playlist_name}')
        
        await progress_manager.send_message(task_id, json.dumps({"status": "starting", "message": "同步任务已开始..."}), event="progress")
        
        try:
            TaskService.update_task_status(task_id, 'syncing', '正在同步...')
            await progress_manager.send_message(task_id, json.dumps({"status": "syncing", "message": "正在初始化..."}), event="progress")

            await self._initialize_plex_service(server_id)
            if safe_log_callback: safe_log_callback('info', '媒体服务器客户端初始化成功。')
            
            music_library = await self.plex_service.get_music_library()
            if not music_library:
                raise Exception('无法找到音乐资料库。')
            
            external_playlist = await self.playlist_service.parse_playlist(playlist_url, platform)
            total_tracks = len(external_playlist['tracks'])
            if safe_log_callback: safe_log_callback('info', f"成功获取到 \"{external_playlist['title']}\"，共 {total_tracks} 首歌曲。")
            
            matched_plex_tracks, unmatched_tracks_info = await self._match_tracks(task_id, external_playlist, music_library)

            TaskService.update_unmatched_songs(task_id, unmatched_tracks_info)
            TaskService.update_sync_counts(
                task_id,
                total=len(external_playlist['tracks']),
                matched=len(matched_plex_tracks)
            )
            if safe_log_callback: safe_log_callback('info', f"匹配完成。成功: {len(matched_plex_tracks)}, 失败: {len(unmatched_tracks_info)}")
            
            TaskService.update_task_status(task_id, 'importing', '正在导入...')
            await progress_manager.send_message(task_id, json.dumps({"status": "importing", "message": "正在导入..."}), event="progress")
            
            success = await self.plex_service.create_or_update_playlist(playlist_name, tracks=matched_plex_tracks, log_callback=safe_log_callback)
            
            if success:
                TaskService.update_task_status(task_id, 'success', '同步成功')
                TaskService.update_last_sync_time(task_id)
                await progress_manager.send_message(task_id, json.dumps({"status": "success", "message": "同步成功！正在检查自动下载..."}), event="progress")

                # 触发自动下载检查
                try:
                    await progress_manager.send_message(task_id, json.dumps({"status": "downloading", "message": "检查自动下载设置..."}), event="progress")
                    session_id = await self.download_service.auto_download_missing(task_id)
                    if session_id:
                        await progress_manager.send_message(task_id, json.dumps({"status": "downloading", "message": f"自动下载会话 {session_id} 已启动。"}), event="progress")
                    else:
                        await progress_manager.send_message(task_id, json.dumps({"status": "downloading", "message": "未启动自动下载。"}), event="progress")
                except Exception as e:
                    logger.error(f"[任务 {task_id}] 自动下载触发失败: {e}")
                    await progress_manager.send_message(task_id, json.dumps({"status": "downloading", "message": f"自动下载检查失败: {e}"}), event="progress")

                return True
            else:
                raise Exception("导入失败")
                
        except Exception as e:
            logger.error(f"[任务 {task_id}] 同步失败: {e}", exc_info=True)
            error_message = f"任务失败: {str(e)}"
            if safe_log_callback: safe_log_callback('error', error_message)
            TaskService.update_task_status(task_id, 'failed', error_message)
            await progress_manager.send_message(task_id, json.dumps({"status": "failed", "message": error_message}), event="error")
            return False
        finally:
            await progress_manager.send_message(task_id, "close", event="close")
    
    def _get_settings_sync(self, server_id: int):
        """ (同步) 根据 server_id 获取服务器设置 """
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT url, token, server_type, verify_ssl FROM settings WHERE id = ?", (server_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'url': row['url'], 
                'token': row['token'], 
                'type': row['server_type'],
                'verify_ssl': bool(row['verify_ssl'])
            }
        return None
