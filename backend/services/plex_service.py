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
from thefuzz import fuzz
import asyncio

logger = logging.getLogger(__name__)

def normalize_string(text: str) -> str:
    """标准化字符串，用于模糊比较。"""
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

class PlexService:
    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_fixed(2),
        retry=retry_if_exception_type((ConnectionError, PlexApiException))
    )
    def __init__(self, base_url: str, token: str):
        """
        初始化Plex服务 - 注意：这是一个同步方法，将在一个独立的线程中被调用。
        :param base_url: Plex服务器URL
        :param token: Plex认证令牌
        """
        try:
            self.server = PlexServer(base_url, token)
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
    def test_connection(base_url: str, token: str) -> Tuple[bool, str]:
        """测试与Plex服务器的连接"""
        try:
            PlexServer(base_url, token)
            return True, "连接成功。"
        except Exception as e:
            return False, f"连接失败: {str(e)}"
			
    @classmethod
    async def create_instance(cls, base_url: str, token: str):
        """异步创建PlexService实例"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, cls, base_url, token)

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

    @retry(
        stop=stop_after_attempt(3), 
        wait=wait_fixed(2),
        retry=retry_if_exception_type((ConnectionError, PlexApiException))
    )
    def _search_by_artist(self, norm_title, norm_artist, norm_album, library):
        """策略1: 按艺术家搜索歌曲"""
        best_match, highest_score = None, 0
        if not norm_artist:
            return best_match, highest_score

        try:
            artists = library.search(norm_artist, libtype='artist')
            for art in artists:
                artist_match_score = fuzz.ratio(norm_artist, normalize_string(art.title))
                if artist_match_score < 70:
                    continue
                
                for track in art.tracks():
                    norm_plex_title = normalize_string(track.title)
                    norm_plex_album = normalize_string(track.parentTitle or "")
                    title_score = fuzz.ratio(norm_title, norm_plex_title)
                    album_score = fuzz.ratio(norm_album, norm_plex_album) if norm_album else 70
                    combined_score = (title_score * 0.6) + (artist_match_score * 0.25) + (album_score * 0.15)

                    if combined_score > highest_score:
                        highest_score = combined_score
                        best_match = track
        except Exception as e:
            logger.warning(f"按艺术家搜索时出错: {e}")
        
        return best_match, highest_score

    def _search_globally(self, norm_title, norm_artist, norm_album, library):
        """策略2: 全局搜索歌曲"""
        best_match, highest_score = None, 0
        try:
            results = library.search(norm_title, libtype='track')
            for track in results:
                norm_plex_title = normalize_string(track.title)
                norm_plex_artist = normalize_string(track.grandparentTitle or "")
                norm_plex_album = normalize_string(track.parentTitle or "")
                title_score = fuzz.ratio(norm_title, norm_plex_title)
                artist_score = fuzz.ratio(norm_artist, norm_plex_artist) if norm_artist else 70
                album_score = fuzz.ratio(norm_album, norm_plex_album) if norm_album else 70
                combined_score = (title_score * 0.55) + (artist_score * 0.3) + (album_score * 0.15)
                
                if combined_score > highest_score:
                    highest_score = combined_score
                    best_match = track
        except Exception as e:
            logger.error(f"在Plex中搜索音轨时出错 '{norm_title} - {norm_artist}': {e}", exc_info=True)
            
        return best_match, highest_score

    def _find_track_with_score_sync(self, title: str, artist: str, album: str, library: MusicSection) -> Tuple[Optional[Track], int]:
        norm_title = normalize_string(title)
        norm_artist = normalize_string(artist)
        norm_album = normalize_string(album)

        # 策略1: 按艺术家搜索
        best_match, highest_score = self._search_by_artist(norm_title, norm_artist, norm_album, library)

        # 策略2: 全局搜索
        global_match, global_score = self._search_globally(norm_title, norm_artist, norm_album, library)

        if global_score > highest_score:
            highest_score = global_score
            best_match = global_match
            
        if highest_score > 80:
            logger.info(f"模糊匹配成功: '{title} | {artist}' -> '{best_match.title} | {best_match.grandparentTitle}' (综合分: {highest_score:.0f})")
            return best_match, int(highest_score)
      
        return None, 0

    async def create_or_update_playlist(self, name: str, tracks: List[Track], log_callback=None) -> bool:
        """异步创建或更新播放列表"""
        return await asyncio.to_thread(self._create_or_update_playlist_sync, name, tracks, log_callback)

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
                if log_callback: log_callback('info', f'找到现有播放列表 "{name}"，将清空并重新添加。')
                target_playlist.removeItems(target_playlist.items())
            except NotFound:
                if log_callback: log_callback('info', f'播放列表 "{name}" 不存在，将创建它。')
                self.server.createPlaylist(name, items=tracks)
                if log_callback: log_callback('success', f'成功创建并导入 {len(tracks)} 首歌曲到 Plex 播放列表 "{name}"。')
                return True
            
            if tracks:
                target_playlist.addItems(tracks)

            final_size = len(target_playlist.items())
            if log_callback: log_callback('success', f'成功更新并导入 {final_size} 首歌曲到 Plex 播放列表 "{name}"。')
            
            return True
            
        except Exception as e:
            logger.error(f'导入到 Plex 时出错: {str(e)}', exc_info=True)
            if log_callback: log_callback('error', f'导入到 Plex 时出错: {str(e)}')
            return False
