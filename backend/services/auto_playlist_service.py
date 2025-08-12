import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from services.plex_service import PlexService
from services.task_service import TaskService
from plexapi.library import MusicSection
from plexapi.audio import Track as PlexTrack
from thefuzz import fuzz

logger = logging.getLogger(__name__)

class AutoPlaylistService:
    """
    自动播放列表服务，负责智能地将新音乐添加到对应的Plex播放列表中。
    """
    
    _instance: Optional["AutoPlaylistService"] = None
    _initialized: bool = False
    
    def __new__(cls, plex_service: Optional[PlexService] = None, task_service: Optional[TaskService] = None):
        if cls._instance is None:
            cls._instance = super(AutoPlaylistService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, plex_service: Optional[PlexService] = None, task_service: Optional[TaskService] = None):
        # 防止重复初始化
        if AutoPlaylistService._initialized:
            return
            
        if plex_service is None or task_service is None:
            raise ValueError("AutoPlaylistService requires plex_service and task_service for initialization")
            
        self.plex_service = plex_service
        self.task_service = task_service
        AutoPlaylistService._initialized = True
        
    @classmethod
    def get_instance(cls) -> "AutoPlaylistService":
        """获取AutoPlaylistService的单例实例"""
        if cls._instance is None:
            raise RuntimeError("AutoPlaylistService has not been initialized yet")
        return cls._instance
        
    @classmethod
    def set_instance(cls, instance: "AutoPlaylistService"):
        """设置AutoPlaylistService的单例实例"""
        cls._instance = instance
        cls._initialized = True
        
    def _normalize_string(self, text: str) -> str:
        """标准化字符串，用于模糊比较。复用PlexService的逻辑。"""
        # 直接使用plex_service的normalize_string方法
        # 需要导入 PlexService 类来访问静态方法
        # 但为了避免循环依赖，我们在这里复制实现
        
        # 导入放在方法内部，避免循环依赖
        import re
        if not text:
            return ""
        # 统一转为小写
        text = text.lower()
        # 全角转半角
        text = text.translate(str.maketrans('１２３４５６７８９０ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ', 
                                            '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'))
        # 移除括号内的特定内容，而不是整个括号
        text = re.sub(r"\((feat|ft|remix|edit)[^)]*\)", "", text)
        text = re.sub(r"\[(feat|ft|remix|edit)[^]]*\]", "", text)
        # 移除标点
        text = re.sub(r'[^\w\s]', ' ', text)
        # 移除关键字
        text = re.sub(r"\b(deluxe|explicit|remastered|edition|feat|ft|remix|edit|version)\b", "", text)
        # 移除多余的空格
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
        
    def _match_track_to_missing_song(self, plex_track: PlexTrack, missing_song: Dict) -> Tuple[bool, int]:
        """
        将一个Plex音轨与缺失列表中的一首歌进行匹配。
        :param plex_track: Plex音轨对象
        :param missing_song: 缺失列表中的歌曲信息字典
        :return: (是否匹配, 匹配分数)
        """
        try:
            # 从Plex音轨获取信息
            plex_title = self._normalize_string(plex_track.title)
            plex_artist = self._normalize_string(plex_track.grandparentTitle or "")
            plex_album = self._normalize_string(plex_track.parentTitle or "")
            
            # 从缺失歌曲获取信息
            missing_title = self._normalize_string(missing_song.get('title', ''))
            missing_artist = self._normalize_string(missing_song.get('artist', ''))
            missing_album = self._normalize_string(missing_song.get('album', ''))
            
            # 计算匹配分数
            title_score = fuzz.ratio(plex_title, missing_title)
            artist_score = fuzz.ratio(plex_artist, missing_artist)
            album_score = fuzz.ratio(plex_album, missing_album)
            
            # 综合分数 (标题权重最高，艺术家次之，专辑最低)
            combined_score = (title_score * 0.6) + (artist_score * 0.3) + (album_score * 0.1)
            
            # 设定一个阈值，例如80分以上认为是匹配
            is_match = combined_score > 80
            
            logger.debug(f"Matching {plex_title} by {plex_artist} to {missing_title} by {missing_artist} - Score: {combined_score:.2f}")
            
            return is_match, int(combined_score)
        except Exception as e:
            logger.error(f"Error matching track {plex_track.title} to missing song: {e}")
            return False, 0

    async def process_tracks_for_task(self, task_id: int, music_library: MusicSection, since: datetime):
        """
        处理特定任务下载后的新音轨。
        :param task_id: 同步任务ID
        :param music_library: Plex音乐库对象
        :param since: 查找此时间之后添加的音轨
        """
        logger.info(f"[Task {task_id}] Starting post-download processing for tracks added since {since}")
        
        try:
            # 1. 获取新内容
            new_tracks = await self.plex_service.find_newly_added_tracks(music_library, since)
            logger.info(f"[Task {task_id}] Found {len(new_tracks)} newly added tracks")
            
            if not new_tracks:
                logger.info(f"[Task {task_id}] No new tracks to process.")
                return
                
            # 2. 获取任务的缺失列表
            unmatched_songs = self.task_service.get_unmatched_songs_for_task(task_id)
            logger.info(f"[Task {task_id}] Retrieved {len(unmatched_songs)} unmatched songs from task")
            
            if not unmatched_songs:
                logger.info(f"[Task {task_id}] No unmatched songs in task, nothing to match.")
                return
                
            # 3. 匹配新音轨与缺失歌曲
            matched_songs_info = []  # 存储匹配成功的歌曲信息，用于后续更新任务状态
            tracks_to_add = {}  # key: playlist_name, value: list of PlexTrack objects
            
            for track in new_tracks:
                for song in unmatched_songs:
                    is_match, score = self._match_track_to_missing_song(track, song)
                    if is_match:
                        logger.info(f"[Task {task_id}] Matched Plex track '{track.title}' to missing song '{song.get('title')}' (Score: {score})")
                        
                        # 记录匹配信息
                        matched_songs_info.append({
                            'plex_track': track,
                            'missing_song': song,
                            'score': score
                        })
                        
                        # 获取任务对应的播放列表名称
                        task = self.task_service.get_task_by_id(task_id)
                        if task and task.name:
                            playlist_name = task.name
                            if playlist_name not in tracks_to_add:
                                tracks_to_add[playlist_name] = []
                            tracks_to_add[playlist_name].append(track)
                        else:
                            logger.warning(f"[Task {task_id}] Could not find task or task name, skipping playlist update")
                        break  # 一个Plex音轨只匹配一个缺失歌曲
                        
            # 4. 更新歌单
            for playlist_name, tracks in tracks_to_add.items():
                if tracks:
                    logger.info(f"[Task {task_id}] Adding {len(tracks)} tracks to playlist '{playlist_name}'")
                    success = await self.plex_service.create_or_update_playlist(
                        playlist_name, 
                        tracks, 
                        lambda level, msg: logger.log(getattr(logging, level.upper()), f"[Task {task_id}] {msg}")
                    )
                    if success:
                        logger.info(f"[Task {task_id}] Successfully added tracks to playlist '{playlist_name}'")
                    else:
                        logger.error(f"[Task {task_id}] Failed to add tracks to playlist '{playlist_name}'")
                        
            # 5. 更新任务状态
            if matched_songs_info:
                # 提取匹配的缺失歌曲信息用于更新任务
                matched_missing_songs = [info['missing_song'] for info in matched_songs_info]
                logger.info(f"[Task {task_id}] Updating task status, removing {len(matched_missing_songs)} matched songs")
                
                # 调用TaskService的方法来更新任务状态
                success = self.task_service.remove_matched_songs_from_task(task_id, matched_missing_songs)
                if success:
                    logger.info(f"[Task {task_id}] Successfully updated task status")
                else:
                    logger.error(f"[Task {task_id}] Failed to update task status")
            else:
                logger.info(f"[Task {task_id}] No matches found, task status unchanged")
                
        except Exception as e:
            logger.error(f"[Task {task_id}] Error in post-download processing: {e}", exc_info=True)

    async def process_newly_added_tracks(self, music_library: MusicSection, since: datetime):
        """
        处理定期扫描发现的新音轨。
        :param music_library: Plex音乐库对象
        :param since: 查找此时间之后添加的音轨
        """
        logger.info(f"Starting periodic processing for tracks added since {since}")
        
        try:
            # 1. 获取新内容
            new_tracks = await self.plex_service.find_newly_added_tracks(music_library, since)
            logger.info(f"Found {len(new_tracks)} newly added tracks")
            
            if not new_tracks:
                logger.info("No new tracks to process.")
                return
                
            # 2. 获取所有任务及其缺失列表
            all_tasks = self.task_service.get_all_tasks()  # 假设TaskService有这个方法
            task_unmatched_songs = {
                task.id: self.task_service.get_unmatched_songs_for_task(task.id) 
                for task in all_tasks
            }
            
            # 3. 匹配新音轨与所有任务的缺失歌曲
            task_updates = {}  # key: task_id, value: list of matched missing songs
            tracks_to_add = {}  # key: (task_id, playlist_name), value: list of PlexTrack objects
            
            for track in new_tracks:
                for task in all_tasks:
                    unmatched_songs = task_unmatched_songs.get(task.id, [])
                    for song in unmatched_songs:
                        is_match, score = self._match_track_to_missing_song(track, song)
                        if is_match:
                            logger.info(f"Matched Plex track '{track.title}' to missing song '{song.get('title')}' in task {task.id} (Score: {score})")
                            
                            # 记录需要更新的任务
                            if task.id not in task_updates:
                                task_updates[task.id] = []
                            task_updates[task.id].append(song)
                            
                            # 记录需要添加到播放列表的音轨
                            playlist_key = (task.id, task.name)
                            if playlist_key not in tracks_to_add:
                                tracks_to_add[playlist_key] = []
                            tracks_to_add[playlist_key].append(track)
                            break  # 一个Plex音轨只匹配一个任务的一个缺失歌曲
                            
            # 4. 更新歌单
            for (task_id, playlist_name), tracks in tracks_to_add.items():
                if tracks:
                    logger.info(f"[Task {task_id}] Adding {len(tracks)} tracks to playlist '{playlist_name}'")
                    success = await self.plex_service.create_or_update_playlist(
                        playlist_name, 
                        tracks, 
                        lambda level, msg: logger.log(getattr(logging, level.upper()), f"[Task {task_id}] {msg}")
                    )
                    if success:
                        logger.info(f"[Task {task_id}] Successfully added tracks to playlist '{playlist_name}'")
                    else:
                        logger.error(f"[Task {task_id}] Failed to add tracks to playlist '{playlist_name}'")
                        
            # 5. 更新所有相关任务的状态
            for task_id, matched_songs in task_updates.items():
                if matched_songs:
                    logger.info(f"[Task {task_id}] Updating task status, removing {len(matched_songs)} matched songs")
                    # 调用TaskService的方法来更新任务状态
                    success = self.task_service.remove_matched_songs_from_task(task_id, matched_songs)
                    if success:
                        logger.info(f"[Task {task_id}] Successfully updated task status")
                    else:
                        logger.error(f"[Task {task_id}] Failed to update task status")
                    
        except Exception as e:
            logger.error(f"Error in periodic processing: {e}", exc_info=True)