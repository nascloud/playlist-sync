import asyncio
import os
import re
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

import requests
from tenacity import retry, stop_after_attempt, wait_exponential
from schemas.download import DownloadQueueItem
import logging
from thefuzz import fuzz

# Mutagen imports for ID3 tags
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
from mutagen import File

logger = logging.getLogger(__name__)

class APIError(Exception):
    """自定义 API 异常"""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code

class MusicDownloader:
    """
    一个用于与 AIAPI.VIP 交互的音乐下载器核心。
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("API key 不能为空")
        self.api_key = api_key
        self.base_url = "https://aiapi.vip/v1"

    def _format_lrc_time(self, time_val) -> str:
        """
        将 API 返回的时间 (可能是浮点数或字符串) 格式化为 LRC 标准时间标签 [mm:ss.ff]。
        """
        try:
            total_seconds = float(time_val)
            if total_seconds < 0:
                total_seconds = 0
            
            total_seconds_rounded = round(total_seconds, 2)
            
            minutes = int(total_seconds_rounded // 60)
            seconds = int(total_seconds_rounded % 60)
            hundredths = int((total_seconds_rounded * 100) % 100)

            return f"[{minutes:02d}:{seconds:02d}.{hundredths:02d}]"
        except (ValueError, TypeError):
            return f"[{time_val}]"

    def _embed_id3_tags(self, file_path: str, item: DownloadQueueItem, song_api_info: dict, log: logging.Logger):
        """
        将元数据和封面图片嵌入到音频文件中。
        """
        log.info(f"开始为文件 '{Path(file_path).name}' 嵌入 ID3 元数据...")
        try:
            audio = File(file_path, easy=True)
            if audio is None:
                log.error("Mutagen无法加载音频文件，可能是不支持的格式或文件已损坏。")
                raise ValueError("无法加载音频文件，可能是不支持的格式。")

            # 确保元数据是字符串
            title = song_api_info.get('name', item.title)
            artist = song_api_info.get('artist', item.artist)
            album = item.album

            audio['title'] = str(title) if title else ""
            audio['artist'] = str(artist) if artist else ""
            audio['album'] = str(album) if album else ""
            
            log.info(f"基础元数据待写入: Title='{audio['title']}', Artist='{audio['artist']}', Album='{audio['album']}'")
            audio.save()
            log.info("基础元数据写入成功。")

            # 重新加载以处理封面
            audio = File(file_path)
            pic_url = song_api_info.get('pic') if song_api_info else None
            log.info(f"API返回的封面URL: {pic_url}")

            if pic_url:
                log.info(f"正在从 {pic_url} 下载封面图片...")
                try:
                    cover_response = requests.get(pic_url, timeout=15)
                    cover_response.raise_for_status()
                    cover_data = cover_response.content
                    log.info(f"封面图片下载成功，大小: {len(cover_data)} bytes。")

                    from mutagen.flac import Picture, FLAC
                    from mutagen.mp3 import MP3

                    if isinstance(audio, FLAC):
                        log.info("检测到FLAC文件，使用 add_picture 方法。")
                        pic = Picture()
                        pic.type = 3  # Cover (front)
                        pic.mime = u"image/jpeg"
                        pic.desc = u"Cover"
                        pic.data = cover_data
                        audio.add_picture(pic)
                    elif isinstance(audio, MP3):
                         log.info("检测到MP3文件，使用 APIC 帧。")
                         audio['APIC'] = APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3,
                            desc='Cover',
                            data=cover_data
                        )
                    else:
                        log.warning(f"文件类型 {type(audio)} 可能不支持封面嵌入，将尝试使用APIC。")
                        audio['APIC'] = APIC(
                            encoding=3,
                            mime='image/jpeg',
                            type=3,
                            desc='Cover',
                            data=cover_data
                        )

                    log.info("封面数据帧创建成功，准备保存。")
                    audio.save()
                    log.info("封面图片嵌入并保存成功。")

                except requests.exceptions.RequestException as e:
                    log.warning(f"下载封面图片失败: {e}")
                except Exception as e_mutagen_apic:
                    log.error(f"使用Mutagen嵌入封面时出错: {e_mutagen_apic}", exc_info=True)
            else:
                log.info("未找到有效的封面图片URL，跳过封面嵌入。")

            log.info("ID3 元数据处理流程完成。")

        except Exception as e:
            log.error(f"嵌入 ID3 标签时发生未知错误: {e}", exc_info=True)


    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=6))
    def _request(self, method: str, endpoint: str, params: dict = None, data: dict = None) -> dict:
        """
        一个私有的方法，用于发送 HTTP 请求。
        """
        url = f"{self.base_url}{endpoint}"
        all_params = {"key": self.api_key}
        if params:
            all_params.update(params)

        try:
            if method.upper() == 'GET':
                response = requests.get(url, params=all_params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, params=all_params, data=data, timeout=30)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")

            response.raise_for_status()
            
            json_response = response.json()
            
            if json_response.get('code') != 200:
                raise APIError(json_response.get('msg', 'API 返回未知错误'), status_code=json_response.get('code'))

            return json_response

        except requests.exceptions.HTTPError as http_err:
            raise APIError(f"HTTP 错误: {http_err}", status_code=http_err.response.status_code)
        except requests.exceptions.RequestException as req_err:
            raise APIError(f"请求错误: {req_err}")
        except ValueError as json_err:
             raise APIError(f"JSON 解析错误: {json_err}")

    def search(self, text: str, music_type: str, page: int = 1, size: int = 10) -> dict:
        """搜索歌曲。"""
        params = {"text": text, "type": music_type, "page": page, "size": size}
        return self._request("GET", "/search", params=params)

    def get_music_url(self, music_id: str, music_type: str, info: bool = False) -> dict:
        """获取歌曲 URL。"""
        params = {"id": music_id, "type": music_type, "info": info}
        return self._request("GET", "/musicUrl", params=params)

    def download_song(self, item: DownloadQueueItem, music_id: str, music_type: str, download_dir: str, preferred_quality: str = '无损', download_lyrics: bool = False, session_logger: Optional[logging.Logger] = None) -> str:
        """
        下载歌曲，并可选择下载歌词和音质。返回下载的文件路径。
        """
        log = session_logger or logging.getLogger(__name__)

        log.info(f"获取歌曲 '{music_id}' (平台: {music_type}) 的信息...")
        music_info = self.get_music_url(music_id, music_type, info=True)
        
        data = music_info.get('data')
        if not data or not isinstance(data, list):
            raise APIError("API未返回有效的歌曲数据。")

        quality_order = ['无损', '高品', '标准']
        sorted_tracks = sorted(data, key=lambda x: x.get('br', 0), reverse=True)

        selected_track = None
        try:
            start_index = quality_order.index(preferred_quality)
        except ValueError:
            start_index = 0

        for i in range(start_index, len(quality_order)):
            quality = quality_order[i]
            for track in sorted_tracks:
                if track.get('ts') == quality and track.get('url'):
                    selected_track = track
                    break
            if selected_track:
                break

        if not selected_track:
            if sorted_tracks and sorted_tracks[0].get('url'):
                selected_track = sorted_tracks[0]
            else:
                raise APIError("未找到可用的下载链接。")

        song_url = selected_track.get('url')
        file_format = selected_track.get('format', 'mp3')
        actual_quality = selected_track.get('ts', '未知')

        song_info_details = music_info.get('info', {})
        song_name = music_info.get('gm') or song_info_details.get('name', item.title)
        singer = music_info.get('gs') or song_info_details.get('artist', item.artist)
        clean_singer = re.sub(r'[\\\\/*?:\"<>|]', "", singer)
        clean_name = re.sub(r'[\\\\/*?:\"<>|]', "", song_name)
        file_basename = f"{clean_singer} - {clean_name}"

        download_path = Path(download_dir)
        download_path.mkdir(parents=True, exist_ok=True)

        song_filepath = download_path / f"{file_basename}.{file_format}"
        log.info(f"选择音质: {actual_quality}。正在下载到: {song_filepath}")
        
        try:
            with requests.get(song_url, stream=True, timeout=180) as r:
                r.raise_for_status()
                with open(song_filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            log.info("歌曲下载完成。")
        except requests.exceptions.RequestException as e:
            raise APIError(f"下载歌曲时出错: {e}")
        except IOError as e:
            raise APIError(f"保存歌曲文件时出错: {e}")

        # 下载完成后，嵌入 ID3 标签
        self._embed_id3_tags(str(song_filepath), item, song_info_details, log)

        if download_lyrics:
            lyrics_data = song_info_details.get('lyric')
            if lyrics_data and isinstance(lyrics_data, list):
                lyric_filepath = download_path / f"{file_basename}.lrc"
                log.info(f"正在下载歌词到: {lyric_filepath}")
                try:
                    with open(lyric_filepath, 'w', encoding='utf-8') as f:
                        for line in lyrics_data:
                            if isinstance(line, dict) and 'time' in line and 'words' in line:
                                cleaned_words = line['words'].replace('\\n', ' ').replace('\\r', '')
                                f.write(f"{self._format_lrc_time(line['time'])} {cleaned_words}\n")
                    log.info("歌词下载完成。")
                except (IOError, KeyError) as e:
                    log.warning(f"警告: 保存歌词文件时出错: {e}")
            else:
                log.info("信息: API未提供该歌曲的歌词。")
        
        return str(song_filepath)

class DownloaderCore:
    """
    对 MusicDownloader 的包装，以适应我们的服务架构。
    """
    def __init__(self):
        self.downloader: Optional[MusicDownloader] = None
        self.download_path: str = "/downloads"

    def initialize(self, api_key: str, download_path: str):
        """初始化下载器，配置API Key和下载路径。"""
        logger.info("开始初始化下载器核心 (DownloaderCore)...")
        if not api_key:
            raise ValueError("API Key 不能为空")
        self.downloader = MusicDownloader(api_key=api_key)
        self.download_path = download_path
        Path(self.download_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"下载器核心 (DownloaderCore) 初始化成功。下载路径: {self.download_path}")

    def _map_platform_name(self, platform: str) -> str:
        """将面向用户的平台名称映射到 API 特定的名称。"""
        mapping = {
            "netease": "wy",
            "qqmusic": "qq",
        }
        return mapping.get(platform.lower(), platform)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _find_song_id(self, item: DownloadQueueItem, session_logger: logging.Logger) -> Tuple[Optional[str], Optional[str]]:
        """使用歌曲信息搜索并返回最佳匹配的歌曲ID和平台。"""
        session_logger.info(f"开始为 '{item.title}' 查找歌曲 ID...")
        if not self.downloader:
            raise ValueError("下载器未初始化")
        
        search_term = f"{item.artist} {item.title}"
        loop = asyncio.get_running_loop()
        best_match: Dict[str, Any] = {}
        highest_score = 0

        platforms_to_search = ['qq', 'wy', 'kg', 'kw', 'mg']
        if item.platform:
            mapped_platform = self._map_platform_name(item.platform)
            if mapped_platform in platforms_to_search:
                platforms_to_search.insert(0, platforms_to_search.pop(platforms_to_search.index(mapped_platform)))

        for platform in platforms_to_search:
            try:
                session_logger.info(f"正在平台 '{platform}' 上搜索 '{search_term}'...")
                search_results = await loop.run_in_executor(
                    None, self.downloader.search, search_term, platform, 1, 10
                )
                songs_data = search_results.get('data', {})
                songs_list: List[Dict[str, Any]] = []
                if isinstance(songs_data, dict):
                    songs_list = songs_data.get('data', [])

                if not songs_list and isinstance(songs_data, dict):
                    # 兼容可能存在的 'list' 字段
                    songs_list = songs_data.get('list', [])

                if songs_list and isinstance(songs_list, list):
                    for result in songs_list:
                        # API返回的字段是name和artist
                        title_match = fuzz.ratio(item.title, result.get('name', ''))
                        artist_match = fuzz.ratio(item.artist, result.get('artist', ''))
                        
                        score = (title_match * 0.6) + (artist_match * 0.4)

                        if score > highest_score:
                            highest_score = score
                            # API返回的歌曲ID是id
                            best_match = {"song_id": result.get('id'), "platform": platform, "score": score}
            except APIError as e:
                session_logger.warning(f"在平台 '{platform}' 上搜索时出错: {e}")
                continue

        if best_match and highest_score > 70:
            session_logger.info(f"为 '{item.title}' 找到最佳匹配: {best_match}，分数为 {highest_score}")
            return best_match.get('song_id'), best_match.get('platform')
        
        session_logger.warning(f"未能为 '{item.title}' 找到足够匹配的结果 (最高分: {highest_score})。")
        raise APIError(f"在所有平台上都未能找到 '{search_term}' 的可下载版本。")

    async def download(self, item: DownloadQueueItem, preferred_quality: str = '无损', download_lyrics: bool = False, session_logger: Optional[logging.Logger] = None) -> str:
        """执行单个下载任务。"""
        
        # 如果没有提供专用的 logger，则使用全局 logger
        if not session_logger:
            session_logger = logging.getLogger(__name__)

        session_logger.info(f"开始处理下载任务 for: {item.title} - {item.artist}")
        if not self.downloader:
            raise ValueError("下载器未初始化或 API Key 无效。")

        loop = asyncio.get_running_loop()
        song_id = item.song_id
        platform = self._map_platform_name(item.platform) if item.platform else None

        # 步骤 1: 如果有现成的 song_id 和 platform，直接尝试下载
        if song_id and platform:
            session_logger.info(f"步骤 1: 使用提供的歌曲 ID '{song_id}' 和平台 '{platform}' 直接下载 '{item.title}'")
            try:
                file_path = await loop.run_in_executor(
                    None,
                    self.downloader.download_song,
                    item, # 传递完整的 item
                    song_id,
                    platform,
                    self.download_path,
                    preferred_quality,
                    download_lyrics,
                    session_logger
                )
                session_logger.info(f"步骤 1 完成. 直接下载成功。文件路径: {file_path}")
                return file_path
            except APIError as e:
                session_logger.warning(f"使用提供的 ID '{song_id}' 直接下载失败: {e}。将回退到搜索模式。")
                # 直接下载失败，清空 song_id，进入搜索流程
                song_id = None
        
        # 步骤 2: 如果没有 song_id 或直接下载失败，则进行搜索
        if not song_id:
            session_logger.info(f"步骤 2: 查找歌曲 ID for '{item.title}'")
            try:
                song_id, platform = await self._find_song_id(item, session_logger)
                if not song_id or not platform:
                    raise APIError(f"未能找到 '{item.title}' 的有效歌曲 ID。")
                session_logger.info(f"步骤 2 完成. 找到歌曲 ID: {song_id}, 平台: {platform}")
            except APIError as e:
                session_logger.error(f"下载 '{item.title}' 失败，因为无法找到匹配项: {e}")
                raise e

        # 步骤 3: 使用找到的ID进行下载
        try:
            session_logger.info(f"步骤 3: 提交下载任务 for '{item.title}'")
            file_path = await loop.run_in_executor(
                None,
                self.downloader.download_song,
                item, # 传递完整的 item
                song_id,
                platform,
                self.download_path,
                preferred_quality,
                download_lyrics,
                session_logger
            )
            session_logger.info(f"步骤 3 完成. '{item.title}' 的下载任务已成功提交。文件路径: {file_path}")
            return file_path
        
        except APIError as e:
            session_logger.error(f"下载 '{item.title}' 失败: {e}")
            raise e
        except Exception as e:
            session_logger.error(f"下载 '{item.title}' 时发生未知错误: {e}", exc_info=True)
            raise APIError(f"未知错误: {e}") from e

# 实例化下载器核心
downloader = DownloaderCore()
