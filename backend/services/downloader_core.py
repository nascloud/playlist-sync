import asyncio
import os
import re
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

import requests
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from schemas.download import DownloadQueueItem
import logging
from thefuzz import fuzz

# Mutagen imports for ID3 tags
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
from mutagen import File

# Import low-quality detection
from services.low_quality_detector import is_file_acceptable, low_quality_logger

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

            # 确保元数据是字符串，优先从API信息中获取
            # 处理可能的列表形式数据
            def _extract_string_value(value):
                """从可能的列表或字符串中提取字符串值"""
                if isinstance(value, list):
                    if len(value) > 0:
                        # 确保列表第一个元素不是None或空字符串
                        first_element = value[0]
                        if first_element is not None:
                            str_value = str(first_element)
                            if str_value.strip():
                                return str_value
                    # 如果列表为空或第一个元素无效，返回None以便回退
                    return None
                elif value is not None:
                    str_value = str(value)
                    if str_value.strip():
                        return str_value
                return None
            
            title = _extract_string_value(song_api_info.get('name')) or _extract_string_value(item.title) or ""
            artist = _extract_string_value(song_api_info.get('artist')) or _extract_string_value(item.artist) or ""
            album = _extract_string_value(song_api_info.get('album')) or _extract_string_value(item.album) or "未知专辑"

            audio['title'] = title
            audio['artist'] = artist
            audio['album'] = album
            
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
            
            # Check if the API returned an error in the response body
            if json_response.get('code') != 200:
                error_msg = json_response.get('message', 'API 返回未知错误')
                raise APIError(f"API 错误 [{json_response.get('code')}]: {error_msg}", status_code=json_response.get('code'))

            return json_response

        except requests.exceptions.HTTPError as http_err:
            # Try to parse the response body even for HTTP errors
            try:
                error_response = http_err.response.json()
                if 'code' in error_response and 'message' in error_response:
                    error_msg = error_response.get('message', 'API 返回未知错误')
                    raise APIError(f"API 错误 [{error_response.get('code')}]: {error_msg}", status_code=error_response.get('code'))
            except json.JSONDecodeError:
                pass  # If we can't parse JSON, fall back to the original error
            
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

        # 下载完成后，先进行低质量文件检测
        if not is_file_acceptable(str(song_filepath), log):
            # 如果文件质量不合格，删除文件并抛出异常
            try:
                os.remove(str(song_filepath))
                log.info(f"已删除低质量文件: {song_filepath}")
            except OSError as e:
                log.warning(f"删除低质量文件 '{song_filepath}' 时出错: {e}")
            raise APIError(f"下载的文件 '{song_filepath}' 被标记为低质量或广告。")

        # 文件质量合格，继续嵌入 ID3 标签
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
                                cleaned_words = line['words'].replace('\n', ' ').replace('\r', '')
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
        # 缓存QQ音乐歌曲详情，避免重复请求
        self._qq_song_detail_cache: Dict[str, Dict] = {}

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

    async def _fetch_qq_song_detail(self, songmid: str, session_logger: logging.Logger) -> Optional[Dict]:
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

    async def _enrich_track_info(self, item: DownloadQueueItem, session_logger: logging.Logger) -> DownloadQueueItem:
        """
        补全歌曲信息（如果缺失）
        :param item: 下载队列项
        :param session_logger: 日志记录器
        :return: 补全后的下载队列项
        """
        # 只有当信息缺失时才尝试补全
        if (not item.album or item.album == '未知专辑') and item.platform == 'qq' and item.song_id:
            # QQ音乐的song_id格式是 "songid-songmid"
            parts = item.song_id.split('-', 1)
            if len(parts) == 2:
                songmid = parts[1]
                if songmid:
                    session_logger.info(f"检测到歌曲 '{item.title}' 缺少专辑信息，尝试从QQ音乐补全...")
                    detail = await self._fetch_qq_song_detail(songmid, session_logger)
                    if detail and isinstance(detail, dict):
                        # 补全专辑信息
                        album_info = detail.get('album')
                        if isinstance(album_info, dict) and album_info.get('name'):
                            # 创建一个新的对象，复制原有属性并更新专辑信息
                            enriched_item = type(item)(
                                id=item.id,
                                session_id=item.session_id,
                                title=item.title,
                                artist=item.artist,
                                album=album_info['name'],  # 补全专辑信息
                                platform=item.platform,
                                song_id=item.song_id,
                                status=item.status,
                                quality=item.quality,
                                retry_count=item.retry_count,
                                error_message=item.error_message,
                                created_at=item.created_at,
                                updated_at=item.updated_at
                            )
                            session_logger.info(f"成功补全歌曲 '{item.title}' 的专辑信息: {album_info['name']}")
                            return enriched_item
                        else:
                            session_logger.debug(f"歌曲 '{item.title}' 的详情中未找到专辑信息")
        
        # 如果不需要补全或补全失败，返回原始项
        return item

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _find_song_id(self, item: DownloadQueueItem, session_logger: logging.Logger, exclude_platforms: Optional[List[str]] = None) -> Tuple[Optional[str], Optional[str], List[Dict[str, Any]]]:
        """使用歌曲信息搜索并返回最佳匹配的歌曲ID、平台和候选列表。"""
        session_logger.info(f"开始为 '{item.title}' 查找歌曲 ID...")
        if not self.downloader:
            raise ValueError("下载器未初始化")
        
        search_term = f"{item.artist} {item.title}"
        loop = asyncio.get_running_loop()
        # 处理需要排除的平台
        if exclude_platforms is None:
            exclude_platforms = []
        exclude_platforms = [self._map_platform_name(p) if p else p for p in exclude_platforms]

        platforms_to_search = ['qq', 'wy', 'kg', 'kw', 'mg']
        # 移除需要排除的平台
        platforms_to_search = [p for p in platforms_to_search if p not in exclude_platforms]
        
        # 如果指定了平台，则优先搜索该平台
        if item.platform:
            mapped_platform = self._map_platform_name(item.platform)
            if mapped_platform in platforms_to_search:
                platforms_to_search.insert(0, platforms_to_search.pop(platforms_to_search.index(mapped_platform)))

        # 遍历平台，逐一搜索
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
                    candidates: List[Dict[str, Any]] = []
                    for result in songs_list:
                        # API返回的字段是name和artist
                        title_match = fuzz.ratio(item.title, result.get('name', ''))
                        artist_match = fuzz.ratio(item.artist, result.get('artist', ''))
                        
                        score = (title_match * 0.6) + (artist_match * 0.4)
                        
                        candidate = {
                            "song_id": result.get('id'),
                            "platform": platform,
                            "score": score,
                            "name": result.get('name'),
                            "artist": result.get('artist')
                        }
                        candidates.append(candidate)

                    # Filter candidates with score > 70 for this platform
                    high_score_candidates = [c for c in candidates if c['score'] > 70]
                    
                    # 如果当前平台找到了高匹配度的候选结果，则返回这些结果
                    # 这样调用者可以立即尝试下载这些候选结果
                    if high_score_candidates:
                        session_logger.info(f"在平台 '{platform}' 上找到 {len(high_score_candidates)} 个高匹配度候选结果。")
                        # 可以选择返回分数最高的一个，或者返回所有高分候选
                        # 这里为了简化，返回第一个高分候选的ID和平台，以及所有高分候选列表
                        best_candidate = high_score_candidates[0]
                        session_logger.debug(f"返回平台 '{platform}' 的最佳候选: {best_candidate}")
                        return best_candidate.get('song_id'), best_candidate.get('platform'), high_score_candidates

            except APIError as e:
                session_logger.warning(f"在平台 '{platform}' 上搜索时出错: {e}")
                continue
            except Exception as e:
                session_logger.warning(f"在平台 '{platform}' 上搜索时发生未知错误: {e}")
                continue
        
        session_logger.warning(f"在所有可用平台上都未能为 '{item.title}' 找到高匹配度的结果。")
        # 如果所有平台都搜索完毕仍未找到，则抛出异常
        raise APIError(f"在所有平台上都未能找到 '{search_term}' 的高匹配度可下载版本。")

    async def download(self, item: DownloadQueueItem, preferred_quality: str = '无损', download_lyrics: bool = False, session_logger: Optional[logging.Logger] = None) -> str:
        """执行单个下载任务。"""
        
        # 如果没有提供专用的 logger，则使用全局 logger
        if not session_logger:
            session_logger = logging.getLogger(__name__)

        session_logger.info(f"开始处理下载任务 for: {item.title} - {item.artist}")
        if not self.downloader:
            raise ValueError("下载器未初始化或 API Key 无效。")

        # 补全缺失的歌曲信息
        enriched_item = await self._enrich_track_info(item, session_logger)
        
        loop = asyncio.get_running_loop()
        song_id = enriched_item.song_id
        platform = self._map_platform_name(enriched_item.platform) if enriched_item.platform else None

        # 步骤 1: 如果有现成的 song_id 和 platform，直接尝试下载
        if song_id and platform:
            session_logger.info(f"步骤 1: 使用提供的歌曲 ID '{song_id}' 和平台 '{platform}' 直接下载 '{enriched_item.title}'")
            try:
                file_path = await loop.run_in_executor(
                    None,
                    self.downloader.download_song,
                    enriched_item, # 传递补全信息后的 item
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
                # 直接下载失败，清空 song_id 和 platform，进入搜索流程
                song_id = None
                platform = None # 同时清空 platform
        
        # 步骤 2: 如果没有 song_id 或直接下载失败，则进行逐一平台搜索和下载
        failed_platforms = []  # Track platforms that have failed or produced low-quality results
        if not song_id:
            session_logger.info(f"步骤 2: 开始逐一平台搜索并尝试下载 '{enriched_item.title}'...")
            
            while True: # 循环搜索，直到成功或所有平台都失败
                try:
                    # 调用修改后的 _find_song_id，它会在找到高匹配度结果的平台后立即返回
                    song_id, platform, candidates_list = await self._find_song_id(enriched_item, session_logger, failed_platforms)
                    if not song_id or not platform:
                        # 理论上 _find_song_id 会抛出异常，但如果返回了无效ID/平台，也应处理
                        raise APIError(f"搜索返回了无效的歌曲 ID 或平台。")
                    
                    session_logger.info(f"在平台 '{platform}' 上找到候选结果，开始尝试下载...")
                    
                    # 尝试下载找到的候选结果
                    try:
                        file_path = await loop.run_in_executor(
                            None,
                            self.downloader.download_song,
                            enriched_item, # 传递补全信息后的 item
                            song_id,
                            platform,
                            self.download_path,
                            preferred_quality,
                            download_lyrics,
                            session_logger
                        )
                        # Check if this file is acceptable (质量合格)
                        if is_file_acceptable(file_path, session_logger):
                            session_logger.info(f"下载成功且文件合格: {file_path}")
                            return file_path
                        else:
                            # If not acceptable, delete the file
                            try:
                                os.remove(file_path)
                                session_logger.info(f"已删除低质量文件: {file_path}")
                            except OSError as remove_err:
                                session_logger.warning(f"删除低质量文件 '{file_path}' 时出错: {remove_err}")
                            
                            # 将产生低质量文件的平台加入排除列表，以便下次搜索时跳过
                            if platform not in failed_platforms:
                                failed_platforms.append(platform)
                            session_logger.info(f"来自平台 '{platform}' 的结果因质量不合格被排除，将继续搜索其他平台。")
                            
                    except APIError as e:
                        session_logger.warning(f"使用平台 '{platform}' 下载失败: {e}")
                        # 将下载失败的平台加入排除列表
                        if platform not in failed_platforms:
                            failed_platforms.append(platform)
                        # 继续循环，尝试下一个平台
                    
                except APIError as e:
                    # 如果 _find_song_id 抛出异常，说明在所有剩余平台上都未能找到高匹配度结果
                    session_logger.error(f"下载 '{enriched_item.title}' 失败: {e}")
                    # 所有平台都已尝试且失败，抛出最终异常
                    raise e
                except Exception as e:
                    session_logger.error(f"下载 '{enriched_item.title}' 时发生未知错误: {e}", exc_info=True)
                    # 所有平台都已尝试且失败，抛出最终异常
                    raise APIError(f"下载 '{enriched_item.title}' 时发生未知错误: {e}") from e

        else:
            # 步骤 3 (仅当有初始 song_id 且直接下载失败时): 使用找到的ID进行下载 (回退逻辑)
            # 注意：如果初始 song_id 下载失败，我们已经在上面的逻辑中清空了 song_id 和 platform
            # 这部分代码实际上不会被执行，因为如果初始下载失败，song_id 会被设为 None，
            # 从而进入上面的 while True 循环。
            # 但为了逻辑完整性，我们保留一个简化的直接下载逻辑。
            session_logger.info(f"步骤 3: 使用初始找到的ID进行下载 (如果有的话) for '{enriched_item.title}'")
            if song_id and platform:
                try:
                    file_path = await loop.run_in_executor(
                        None,
                        self.downloader.download_song,
                        enriched_item,
                        song_id,
                        platform,
                        self.download_path,
                        preferred_quality,
                        download_lyrics,
                        session_logger
                    )
                    # Check if this file is acceptable
                    if is_file_acceptable(file_path, session_logger):
                        session_logger.info(f"直接下载成功且文件合格: {file_path}")
                        return file_path
                    else:
                        # If not acceptable, delete the file
                        try:
                            os.remove(file_path)
                            session_logger.info(f"已删除低质量的直接下载文件: {file_path}")
                        except OSError as remove_err:
                            session_logger.warning(f"删除低质量直接下载文件 '{file_path}' 时出错: {remove_err}")
                        # 如果初始ID下载得到的文件质量不合格，也应该失败
                        raise APIError(f"使用初始ID下载的文件质量不合格。")
                
                except APIError as e:
                    session_logger.error(f"使用初始ID下载 '{enriched_item.title}' 失败: {e}")
                    raise e
                except Exception as e:
                    session_logger.error(f"使用初始ID下载 '{enriched_item.title}' 时发生未知错误: {e}", exc_info=True)
                    raise APIError(f"使用初始ID下载 '{enriched_item.title}' 时发生未知错误: {e}") from e
            else:
                # 这种情况理论上不应该发生，因为我们是在 else 分支里
                session_logger.error(f"逻辑错误：在步骤3中，song_id 或 platform 为空。")
                raise APIError("下载逻辑错误：song_id 或 platform 未正确设置。")

# 实例化下载器核心
downloader = DownloaderCore()
