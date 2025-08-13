from plexapi.server import PlexServer
from plexapi.library import MusicSection
from plexapi.audio import Track
from plexapi.playlist import Playlist as PlexPlaylist
from plexapi.exceptions import NotFound, PlexApiException
from requests.exceptions import ConnectionError
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from typing import List, Optional, Callable, Tuple
import logging
import re
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import datetime

# 忽略不安全请求的警告 (当 verify=False 时)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
from thefuzz import fuzz
import asyncio

logger = logging.getLogger(__name__)

# 版本关键词列表，用于提取核心标题
VERSION_KEYWORDS = [
    "live", "demo", "acoustic", "instrumental", "mix", "version", "remix", "edit",
    "feat", "ft", "radio", "album", "single", "explicit", "clean", "session", "take"
]

def _remove_brackets(text: str) -> str:
    """移除括号内的内容"""
    if not text:
        return ""
    # 移除括号内的特定内容（支持中英文括号）
    # 英文括号
    text = re.sub(r"\(\s*(feat|ft|remix|edit)\s*[^)]*\)", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\[\s*(feat|ft|remix|edit)\s*[^\]]*\]", "", text, flags=re.IGNORECASE)
    # 中文括号
    text = re.sub(r"（\s*(feat|ft|remix|edit)\s*[^）]*）", "", text, flags=re.IGNORECASE)
    text = re.sub(r"［\s*(feat|ft|remix|edit)\s*[^］]*］", "", text, flags=re.IGNORECASE)
    # 移除所有剩余的括号内容（不管是否包含关键词）
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"（[^）]*）", "", text)
    text = re.sub(r"［[^］]*］", "", text)
    return text

def _remove_keywords(text: str) -> str:
    """移除关键字"""
    return re.sub(r"\b(deluxe|explicit|remastered|edition|feat|ft|remix|edit|version|demo|live)\b", "", text)

def _remove_punctuation(text: str) -> str:
    """移除标点符号"""
    return re.sub(r'[^\w\s]', ' ', text)

def _normalize_string(text: str) -> str:
    """标准化字符串，用于模糊比较。"""
    if not text:
        return ""
    # 统一转为小写
    text = text.lower()
    # 全角转半角
    text = text.translate(str.maketrans('１２３４５６７８９０ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ', 
                                        '1234567890abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'))
    # 移除括号内的特定内容和所有剩余的括号内容
    text = _remove_brackets(text)
    # 移除标点
    text = _remove_punctuation(text)
    # 移除关键字
    text = _remove_keywords(text)
    # 移除多余的空格
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def normalize_string(text: str) -> str:
    """标准化字符串，用于模糊比较。"""
    return _normalize_string(text)

def _extract_core_title(norm_title: str) -> str:
    """从标准化标题中提取核心标题，移除版本信息。"""
    if not norm_title:
        return ""
    core_title = norm_title
    # 移除括号内容（更智能的版本，但这里简化处理，直接移除所有括号）
    core_title = _remove_brackets(core_title)
    # 移除版本关键词 (使用词边界确保准确)
    for keyword in VERSION_KEYWORDS:
        # 使用 re.IGNORECASE 确保大小写不敏感匹配
        core_title = re.sub(rf"\b{re.escape(keyword)}\b", "", core_title, flags=re.IGNORECASE)
    # 移除多余的空格
    core_title = re.sub(r'\s+', ' ', core_title)
    return core_title.strip()

def _calculate_artist_score(norm_artist: str, plex_artist: str) -> int:
    """计算艺术家匹配分数。"""
    if not norm_artist:
        return 70 # 如果输入没有艺术家信息，给一个基础分

    # 更严格的标准化：去除空格并转为小写
    norm_artist_clean = norm_artist.replace(" ", "").lower()
    plex_artist_clean = plex_artist.replace(" ", "").lower()

    # 如果完全匹配，给高分
    if norm_artist_clean == plex_artist_clean:
        return 90

    # 将艺术家字符串分割成集合进行比较 (原始逻辑)
    norm_artist_set = set(norm_artist.split())
    plex_artist_set = set(plex_artist.split())

    if not norm_artist_set or not plex_artist_set:
        # 如果任一集合为空，回退到 fuzz.ratio
        return fuzz.ratio(norm_artist, plex_artist)

    # 计算交集
    intersection = norm_artist_set & plex_artist_set
    # 计算并集
    union = norm_artist_set | plex_artist_set
    
    # 使用 Jaccard 相似度作为基础
    if len(union) > 0:
        jaccard_similarity = len(intersection) / len(union)
    else:
        jaccard_similarity = 0

    # 使用 fuzz.ratio 作为辅助
    fuzz_score = fuzz.ratio(norm_artist, plex_artist) / 100.0

    # 综合评分：Jaccard 占 70%，fuzz.ratio 占 30%
    # 增加 Jaccard 的权重，因为它更能体现多艺术家场景下的匹配度
    combined_score = (jaccard_similarity * 0.7 + fuzz_score * 0.3) * 100

    return int(combined_score)

def _calculate_enhanced_score(track: Track, norm_title: str, norm_artist: str, norm_album: str, core_title: str) -> float:
    """计算增强版综合匹配分数。"""
    try:
        plex_norm_title = normalize_string(track.title)
        plex_core_title = _extract_core_title(plex_norm_title)
        plex_artist = normalize_string(track.grandparentTitle or "")
        plex_album = normalize_string(track.parentTitle or "")

        # --- 标题评分 ---
        title_score = fuzz.ratio(norm_title, plex_norm_title)
        core_title_score = fuzz.ratio(core_title, plex_core_title)
        # 结合原始标题和核心标题分数
        combined_title_score = (title_score * 0.7) + (core_title_score * 0.3)
        # 版本惩罚：如果输入的核心标题与Plex的核心标题匹配，但完整标题不匹配，则轻微惩罚
        # 降低惩罚力度，从 0.95 调整为 0.98
        version_penalty_applied = False
        if core_title == plex_core_title and norm_title != plex_norm_title:
            combined_title_score *= 0.98
            version_penalty_applied = True

        # --- 艺术家评分 ---
        artist_score = _calculate_artist_score(norm_artist, plex_artist)

        # --- 专辑评分 ---
        album_score = fuzz.ratio(norm_album, plex_album) if norm_album else 70

        # --- 动态权重 ---
        # 调整权重，略微增加艺术家和专辑的权重，略微降低标题权重
        # 因为观察到艺术家信息对于区分不同版本的歌曲很重要
        W_TITLE = 0.35
        W_ARTIST = 0.45
        W_ALBUM = 0.2

        # --- 综合分数 ---
        final_score = (combined_title_score * W_TITLE) + (artist_score * W_ARTIST) + (album_score * W_ALBUM)
        
        # --- 详细调试日志 ---
        logger.debug(
            f"评分详情 - Plex Track: '{track.title}' (Artist: {track.grandparentTitle}) | "
            f"查询: '{norm_title}' (Artist: {norm_artist}) | "
            f"Title Score: {title_score:.2f}, Core Title Score: {core_title_score:.2f}, "
            f"Combined Title Score: {combined_title_score:.2f} (Penalty: {version_penalty_applied}), "
            f"Artist Score: {artist_score:.2f}, Album Score: {album_score:.2f}, "
            f"Final Score: {final_score:.2f}"
        )
        
        return final_score
    except Exception as e:
        logger.warning(f"计算分数时出错 for track {track.title}: {e}")
        return 0.0

class PlexService:
    # 定义常量
    SEARCH_SCORE_THRESHOLD_HIGH = 65  # 进一步降低阈值以测试匹配效果
    SEARCH_SCORE_THRESHOLD_LOW = 45   # 进一步降低阈值以测试匹配效果
    RETRY_STOP_AFTER_ATTEMPT = 3      # 重试次数
    RETRY_WAIT_FIXED = 2              # 重试等待时间（秒）
    
    @retry(
        stop=stop_after_attempt(RETRY_STOP_AFTER_ATTEMPT), 
        wait=wait_fixed(RETRY_WAIT_FIXED),
        retry=retry_if_exception_type((ConnectionError, PlexApiException))
    )
    def __init__(self, base_url: str, token: str, verify_ssl: bool = True):
        """
        初始化Plex服务 - 注意：这是一个同步方法，将在一个独立的线程中被调用。
        :param base_url: Plex服务器URL
        :param token: Plex认证令牌
        :param verify_ssl: 是否验证SSL证书
        """
        try:
            session = requests.Session()
            session.verify = verify_ssl
            self.server = PlexServer(base_url, token, session=session)
            logger.info(f"Plex连接成功: {self.server.friendlyName}")
        except Exception as e:
            logger.error(f"Plex连接失败: {str(e)}")
            raise Exception(f"无法连接到 Plex 服务器或 Token 无效。详细错误: {str(e)}")
            
    @staticmethod
    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_fixed(2),
        retry=retry_if_exception_type((ConnectionError, PlexApiException))
    )
    def test_connection(base_url: str, token: str, verify_ssl: bool = True) -> Tuple[bool, str]:
        """测试与Plex服务器的连接"""
        try:
            session = requests.Session()
            session.verify = verify_ssl
            PlexServer(base_url, token, session=session)
            return True, "连接成功。"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
			
    @classmethod
    async def create_instance(cls, base_url: str, token: str, verify_ssl: bool = True):
        """异步创建PlexService实例"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, cls, base_url, token, verify_ssl)

    async def get_music_library(self) -> Optional[MusicSection]:
        """异步获取音乐资料库"""
        return await asyncio.to_thread(self._get_music_library_sync)

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_fixed(2),
        retry=retry_if_exception_type((ConnectionError, PlexApiException))
    )
    def _get_music_library_sync(self) -> Optional[MusicSection]:
        try:
            libraries = self.server.library.sections()
            for library in libraries:
                if library.type == 'artist':
                    logger.info(f"[信息] 找到音乐资料库: \"{library.title}\" (ID: {library.key})")
                    return library
            logger.error("[错误] 未在Plex中找到类型为 \"artist\" 的音乐资料库。")
            return None
        except Exception as e:
            logger.error(f"[错误] 获取Plex资料库时发生错误: {str(e)}")
            return None
            
    async def find_track_with_score(self, title: str, artist: str, album: str, library: MusicSection, progress_callback: Optional[Callable] = None) -> Tuple[Optional[Track], int]:
        """异步在Plex中查找音轨，并在完成后调用回调。"""
        result = await asyncio.to_thread(self._find_track_with_score_sync, title, artist, album, library)
        if progress_callback:
            await progress_callback()
        return result

    def _find_track_with_score_sync(self, title: str, artist: str, album: str, library: MusicSection) -> Tuple[Optional[Track], int]:
        """使用增强版匹配策略查找音轨。"""
        norm_title = normalize_string(title)
        core_title = _extract_core_title(norm_title)
        norm_artist = normalize_string(artist)
        norm_album = normalize_string(album)

        best_match, highest_score = None, 0
        candidates = []

        try:
            # 核心标题搜索：最大化召回率
            results = library.search(core_title, libtype='track')
            logger.debug(f"核心标题 '{core_title}' 搜索到 {len(results)} 个候选结果。")

            # 对每个候选结果进行精细化评分
            for track in results:
                score = _calculate_enhanced_score(track, norm_title, norm_artist, norm_album, core_title)
                candidates.append((track, score))

            # 按分数排序
            candidates.sort(key=lambda x: x[1], reverse=True)

            # 选择最高分的候选
            if candidates:
                best_match, highest_score = candidates[0]
                logger.debug(f"最高分候选: '{best_match.title}' (分数: {highest_score:.2f})")

        except Exception as e:
            logger.error(f"在Plex中搜索音轨时出错 '{title} - {artist}': {e}", exc_info=True)

        # 根据阈值返回结果
        if highest_score >= self.SEARCH_SCORE_THRESHOLD_HIGH:
            logger.info(f"高置信度匹配成功: '{title} | {artist}' -> '{best_match.title} | {best_match.grandparentTitle}' (分数: {highest_score:.0f})")
            return best_match, int(highest_score)
        elif highest_score >= self.SEARCH_SCORE_THRESHOLD_LOW:
            logger.info(f"低置信度匹配: '{title} | {artist}' -> '{best_match.title} | {best_match.grandparentTitle}' (分数: {highest_score:.0f})")
            # 可以选择返回低置信度匹配或返回 None, 0
            # 这里我们返回它，但主调用者需要知道这是低置信度
            return best_match, int(highest_score) 
        else:
            logger.info(f"匹配失败: '{title} | {artist}'")
            return None, 0

    async def create_or_update_playlist(self, name: str, tracks: List[Track], log_callback=None) -> bool:
        """异步创建或更新播放列表"""
        return await asyncio.to_thread(self._create_or_update_playlist_sync, name, tracks, log_callback)

    def _find_newly_added_tracks_sync(self, library: MusicSection, since: datetime, max_results: int = 1000) -> List[Track]:
        """
        (同步) 查找自 'since' 时间以来新添加到库的音轨。
        :param library: Plex音乐库对象
        :param since: datetime 对象，表示查找此时间之后添加的音轨
        :param max_results: 最大返回结果数，默认为1000
        :return: 新添加的 Track 对象列表
        """
        try:
            # 使用 Plex API 的 recentlyAddedTracks 方法获取最近添加的音轨
            recently_added = library.recentlyAddedTracks(maxresults=max_results)
            
            # 检查是否达到了最大结果数，如果是则记录警告
            if len(recently_added) == max_results:
                logger.warning(f"Recently added tracks count reached the maximum limit of {max_results}. "
                               "There might be more newly added tracks that were not processed.")
            
            # 过滤出在指定时间之后添加的音轨
            # 注意：Plex 的 addedAt 是 datetime 类型
            new_tracks = [track for track in recently_added if track.addedAt and track.addedAt > since]
            
            logger.info(f"Found {len(new_tracks)} tracks added since {since}")
            return new_tracks
        except Exception as e:
            logger.error(f"Error finding newly added tracks: {e}", exc_info=True)
            return [] # Return empty list on error to prevent breaking the caller

    async def find_newly_added_tracks(self, library: MusicSection, since: datetime, max_results: int = 1000) -> List[Track]:
        """
        (异步) 查找自 'since' 时间以来新添加到库的音轨。
        :param library: Plex音乐库对象
        :param since: datetime 对象，表示查找此时间之后添加的音轨
        :param max_results: 最大返回结果数，默认为1000
        :return: 新添加的 Track 对象列表
        """
        return await asyncio.to_thread(self._find_newly_added_tracks_sync, library, since, max_results)

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_fixed(2),
        retry=retry_if_exception_type((ConnectionError, PlexApiException))
    )
    def _create_or_update_playlist_sync(self, name: str, tracks: List[Track], log_callback=None) -> bool:
        if not tracks:
            if log_callback: log_callback('info', '没有匹配到任何歌曲，跳过 Plex 播放列表的创建/更新。')
            return True
        
        try:
            try:
                target_playlist = self.server.playlist(name)
                if log_callback: log_callback('info', f'找到现有播放列表 "{name}"，将进行增量更新。')
                
                # 获取现有播放列表的所有项目
                current_tracks = target_playlist.items()
                
                # 将 current_tracks 和 tracks 转换为基于 ratingKey 的集合
                current_tracks_set = {track.ratingKey for track in current_tracks}
                new_tracks_set = {track.ratingKey for track in tracks}
                
                # 计算需要移除和添加的项目
                tracks_to_remove_keys = current_tracks_set - new_tracks_set
                tracks_to_add_keys = new_tracks_set - current_tracks_set
                
                # 获取实际需要移除和添加的 Track 对象
                tracks_to_remove = [track for track in current_tracks if track.ratingKey in tracks_to_remove_keys]
                tracks_to_add = [track for track in tracks if track.ratingKey in tracks_to_add_keys]
                
                # 执行移除操作
                if tracks_to_remove:
                    try:
                        target_playlist.removeItems(tracks_to_remove)
                        logger.info(f"从播放列表 '{name}' 移除了 {len(tracks_to_remove)} 首歌曲")
                    except Exception as e:
                        logger.error(f"从播放列表 '{name}' 移除歌曲时出错: {e}")
                        if log_callback: log_callback('error', f"从播放列表 '{name}' 移除歌曲时出错: {e}")
                
                # 执行添加操作
                if tracks_to_add:
                    try:
                        target_playlist.addItems(tracks_to_add)
                        logger.info(f"向播放列表 '{name}' 添加了 {len(tracks_to_add)} 首歌曲")
                    except Exception as e:
                        logger.error(f"向播放列表 '{name}' 添加歌曲时出错: {e}")
                        if log_callback: log_callback('error', f"向播放列表 '{name}' 添加歌曲时出错: {e}")
                        
                final_size = len(target_playlist.items())
                if log_callback: log_callback('success', f'成功更新并导入 {final_size} 首歌曲到 Plex 播放列表 "{name}"。')
                
            except NotFound:
                if log_callback: log_callback('info', f'播放列表 "{name}" 不存在，将创建它。')
                self.server.createPlaylist(name, items=tracks)
                if log_callback: log_callback('success', f'成功创建并导入 {len(tracks)} 首歌曲到 Plex 播放列表 "{name}"。')
                
            return True
            
        except Exception as e:
            logger.error(f'导入到 Plex 时出错: {str(e)}', exc_info=True)
            if log_callback: log_callback('error', f'导入到 Plex 时出错: {str(e)}')
            return False
            
    def _scan_and_refresh_sync(self, library: MusicSection, file_path: Optional[str] = None) -> bool:
        """
        (同步) 通知Plex扫描指定路径或整个音乐库以导入新文件。
        :param library: Plex音乐库对象
        :param file_path: (可选) 需要扫描的文件或文件夹在Plex服务器上的绝对路径。
                          如果为None，则刷新整个音乐库。
        :return: 是否成功发起扫描请求
        """
        try:
            if file_path:
                logger.info(f"Requesting Plex to scan and refresh specific path: {file_path}")
                # Use the update method which is more targeted
                library.update(path=file_path)
                logger.info(f"Successfully requested scan for path: {file_path}")
            else:
                logger.info("Requesting Plex to refresh the entire music library")
                # Refresh the entire library section
                library.refresh()
                logger.info("Successfully requested refresh for the entire music图书馆")
            return True
        except Exception as e:
            logger.error(f"Failed to request scan/refresh: {e}", exc_info=True)
            return False

    async def scan_and_refresh(self, library: MusicSection, file_path: Optional[str] = None) -> bool:
        """
        (异步) 通知Plex扫描指定路径或整个音乐库以导入新文件。
        :param library: Plex音乐库对象
        :param file_path: (可选) 需要扫描的文件或文件夹在Plex服务器上的绝对路径。
                          如果为None，则刷新整个音乐库。
        :return: 是否成功发起扫描请求
        """
        return await asyncio.to_thread(self._scan_and_refresh_sync, library, file_path)