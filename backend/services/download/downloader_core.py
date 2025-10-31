"""音乐下载器核心模块"""

import asyncio
import os
import re
import json
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import httpx
import tenacity
from tenacity import retry, stop_after_attempt, wait_exponential

from schemas.download import DownloadQueueItem
import logging

# Import services
from services.download.metadata_handler import MetadataHandler
from services.download.platform_service import PlatformService
from services.download.quality_checker import QualityChecker
from services.download.qq_music_service import QQMusicService
from services.download.download_constants import QUALITY_ORDER, API_VALIDATION_TITLE_THRESHOLD, API_VALIDATION_ARTIST_THRESHOLD
from services.download.download_exceptions import APIError

# 添加模糊匹配库
from thefuzz import fuzz

logger = logging.getLogger(__name__)

class MusicDownloader:
    """
    一个用于与 api.vkeys.cn 交互的音乐下载器核心。
    """
    def __init__(self):
        self.base_url = "https://api.vkeys.cn"
        # 使用 httpx.AsyncClient 替代 requests，配置允许重定向
        self.http_client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,  # 明确启用重定向跟随
            max_redirects=5  # 设置最大重定向次数
        )

    async def close(self):
        """关闭HTTP客户端"""
        await self.http_client.aclose()

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

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=6),
           retry=tenacity.retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError, ValueError)))
    async def _request(self, method: str, endpoint: str, params: dict = None, data: dict = None) -> dict:
        """
        一个私有的方法，用于发送 HTTP 请求。
        """
        url = f"{self.base_url}{endpoint}"
        all_params = {}
        if params:
            all_params.update(params)

        try:
            if method.upper() == 'GET':
                response = await self.http_client.get(url, params=all_params)
            elif method.upper() == 'POST':
                response = await self.http_client.post(url, params=all_params, data=data)
            else:
                raise ValueError(f"不支持的 HTTP 方法: {method}")

            response.raise_for_status()
            
            json_response = response.json()
            
            # 添加诊断日志：记录完整的API响应
            logger.debug(f"API响应详情 - URL: {url}, 参数: {all_params}")
            logger.debug(f"API响应内容: {json_response}")
            
            # Check if the API returned an error in the response body
            # 添加更灵活的响应格式检查
            response_code = json_response.get('code')
            if response_code != 200:
                error_msg = json_response.get('message', 'API 返回未知错误')
                
                # 记录完整的响应文本作为DEBUG级别日志
                try:
                    logger.debug(f"完整响应文本 - URL: {url}, 状态码: {response_code}, 响应内容: {response.text}")
                except Exception:
                    # 如果无法获取响应文本，记录JSON响应
                    logger.debug(f"完整响应JSON - URL: {url}, 状态码: {response_code}, 响应内容: {json_response}")
                
                # 特别处理404错误 - 这可能是API端点问题，但我们可以继续处理空结果
                if response_code == 404:
                    logger.warning(f"API返回404错误，可能是端点或参数问题 - URL: {url}, 参数: {all_params}")
                    logger.warning(f"404错误消息: {error_msg}")
                    # 返回空结果而不是抛出异常，允许系统继续运行
                    return {"code": 404, "message": error_msg, "data": []}
                
                # 特别处理"未知异常"错误，记录更多调试信息
                if response_code == 400 and "未知异常" in error_msg:
                    logger.warning(f"API返回400未知异常错误，URL: {url}, 参数: {all_params}")
                    logger.warning(f"完整响应内容: {json_response}")
                
                # 检查是否是新的响应格式，可能数据在其他字段中
                if 'data' in json_response and isinstance(json_response['data'], list):
                    logger.warning(f"API返回非200代码但包含有效数据，尝试继续处理 - 代码: {response_code}")
                    logger.warning(f"响应数据: {json_response['data']}")
                    # 不抛出异常，继续处理数据
                    return json_response
                
                logger.error(f"API错误详情 - 代码: {response_code}, 消息: {error_msg}")
                logger.error(f"完整响应内容: {json_response}")
                raise APIError(f"API 错误 [{response_code}]: {error_msg}", status_code=response_code)

            return json_response

        except httpx.HTTPStatusError as http_err:
            # Try to parse the response body even for HTTP errors
            try:
                error_response = http_err.response.json()
                logger.error(f"HTTP状态错误详情 - URL: {url}, 参数: {all_params}")
                logger.error(f"HTTP状态码: {http_err.response.status_code}")
                logger.error(f"错误响应内容: {error_response}")
                # 记录完整的响应文本作为DEBUG级别日志
                logger.debug(f"完整响应文本 - URL: {url}, 状态码: {http_err.response.status_code}, 响应内容: {http_err.response.text}")
                if 'code' in error_response and 'message' in error_response:
                    error_msg = error_response.get('message', 'API 返回未知错误')
                    # 特别处理"未知异常"错误，记录更多调试信息
                    if error_response.get('code') == 400 and "未知异常" in error_msg:
                        logger.warning(f"API返回400未知异常错误，URL: {url}, 参数: {all_params}")
                    raise APIError(f"API 错误 [{error_response.get('code')}]: {error_msg}", status_code=error_response.get('code'))
            except json.JSONDecodeError:
                logger.error(f"无法解析JSON响应 - URL: {url}, 状态码: {http_err.response.status_code}")
                logger.error(f"原始响应内容: {http_err.response.text}")
                # 记录完整的响应文本作为DEBUG级别日志
                logger.debug(f"完整响应文本 - URL: {url}, 状态码: {http_err.response.status_code}, 响应内容: {http_err.response.text}")
                pass  # If we can't parse JSON, fall back to the original error
            
            raise APIError(f"HTTP 错误: {http_err}", status_code=http_err.response.status_code)
        except httpx.RequestError as req_err:
            logger.error(f"请求错误详情 - URL: {url}, 参数: {all_params}")
            logger.error(f"请求错误: {req_err}")
            raise APIError(f"请求错误: {req_err}")
        except ValueError as json_err:
            logger.error(f"JSON解析错误详情 - URL: {url}, 参数: {all_params}")
            logger.error(f"JSON解析错误: {json_err}")
            raise APIError(f"JSON 解析错误: {json_err}")

    async def search_platform(self, platform: str, text: str, page: int = 1, size: int = 10) -> dict:
        """在指定平台搜索歌曲。"""
        endpoint = f"/v2/music/{platform}"
        params = {"word": text, "page": page, "num": size}
        logger.debug(f"开始搜索 - 平台: {platform}, 关键词: '{text}', 页码: {page}, 大小: {size}")
        logger.debug(f"请求端点: {endpoint}, 参数: {params}")
        try:
            result = await self._request("GET", endpoint, params=params)
            logger.debug(f"搜索成功 - 平台: {platform}, 结果: {result}")
            return result
        except APIError as e:
            logger.error(f"API错误 - 平台: {platform}, 关键词: '{text}', 错误: {e}")
            # 如果是API错误，检查是否可以降级处理
            if e.status_code and e.status_code != 200:
                logger.warning(f"平台 '{platform}' API返回错误代码 {e.status_code}，可能存在服务问题")
                # 返回空结果而不是抛出异常，允许继续尝试其他平台
                return {"code": e.status_code, "message": str(e), "data": []}
            raise
        except Exception as e:
            logger.error(f"搜索失败 - 平台: {platform}, 关键词: '{text}', 错误: {e}")
            # 对于所有其他异常，也返回空结果而不是抛出异常，确保程序不会崩溃
            return {"code": 500, "message": f"搜索失败: {str(e)}", "data": []}

    async def get_music_url(self, platform: str, music_id: str, info: bool = False, quality: str = '无损') -> dict:
        """获取歌曲 URL。"""
        endpoint = f"/v2/music/{platform}"
        params = {"id": music_id}
        
        # 根据平台添加音质参数
        if platform == 'tencent':
            # QQ音乐音质映射：无损=10, 高品=8, 标准=4
            quality_mapping = {'无损': 10, '高品': 8, '标准': 4}
            params['quality'] = quality_mapping.get(quality, 10)  # 默认最高音质
        elif platform == 'netease':
            # 网易云音乐音质映射：无损=5, 高品=3, 标准=1
            quality_mapping = {'无损': 5, '高品': 3, '标准': 1}
            params['quality'] = quality_mapping.get(quality, 5)  # 默认最高音质
        
        # 新API的点歌模式似乎总会返回详细信息，因此 info 参数可能不再需要
        # 但我们仍然可以保留它，以备将来使用
        try:
            return await self._request("GET", endpoint, params=params)
        except APIError as e:
            logger.error(f"获取歌曲URL失败 - 平台: {platform}, 音乐ID: {music_id}, 错误: {e}")
            # 如果是API错误，返回空结果而不是抛出异常
            return {"code": e.status_code or 500, "message": str(e), "data": {}}
        except Exception as e:
            logger.error(f"获取歌曲URL时发生未知错误 - 平台: {platform}, 音乐ID: {music_id}, 错误: {e}")
            # 对于所有其他异常，也返回空结果而不是抛出异常，确保程序不会崩溃
            return {"code": 500, "message": f"获取歌曲URL失败: {str(e)}", "data": {}}

    async def get_lyrics(self, platform: str, song_id: str, session_logger: logging.Logger) -> Optional[str]:
        """
        获取歌曲歌词
        :param platform: 平台，如 'tencent' 或 'netease' (注意：这里使用的是映射后的平台名)
        :param song_id: 歌曲ID
        :param session_logger: 日志记录器
        :return: 歌词内容，如果失败则返回 None
        """
        try:
            # 根据平台构造相应的歌词 API 请求 URL
            # 根据API文档，不同的平台有不同的歌词API端点
            if platform == 'tencent':
                endpoint = "/v2/music/tencent/lyric"
                # QQ音乐的song_id可能是"songid-songmid"格式，需要提取songmid部分
                # 或者直接使用song_id，因为API支持两种参数格式
                if '-' in song_id:
                    # 如果是"songid-songmid"格式，提取mid
                    parts = song_id.split('-', 1)
                    params = {"mid": parts[1]}  # 使用mid参数
                else:
                    params = {"id": song_id}  # 使用id参数
            elif platform == 'netease':
                endpoint = "/v2/music/netease/lyric"
                params = {"id": song_id}
            else:
                session_logger.warning(f"不支持的平台: {platform}，无法获取歌词")
                return None
            
            session_logger.info(f"正在获取 {platform} 平台歌曲 ID {song_id} 的歌词...")
            
            # 调用现有的 _request() 方法发送 GET 请求
            response = await self._request("GET", endpoint, params=params)
            
            # 处理 API 的响应
            if response.get('code') == 200 and 'data' in response:
                data = response.get('data', {})
                # API响应可能在不同的字段中包含歌词数据
                # 检查多个可能的歌词字段
                lrc_content = data.get('lrc') or data.get('lyric') or data.get('lyrics') or data.get('content')
                
                if lrc_content:
                    session_logger.info("歌词获取成功")
                    return lrc_content
                else:
                    session_logger.warning(f"API 响应中未找到歌词内容。返回的数据: {data}")
                    return None
            else:
                session_logger.warning(f"获取歌词失败，API 返回错误: {response.get('message', '未知错误')}")
                return None
                
        except APIError as e:
            session_logger.warning(f"获取歌词时发生 API 错误: {e}")
            # 记录更多调试信息
            session_logger.debug(f"API错误详情 - 平台: {platform}, 歌曲ID: {song_id}, 错误代码: {e.status_code}, 错误消息: {str(e)}")
            return None
        except Exception as e:
            session_logger.warning(f"获取歌词时发生未知错误: {e}")
            # 记录更多调试信息
            session_logger.debug(f"未知错误详情 - 平台: {platform}, 歌曲ID: {song_id}, 错误: {str(e)}")
            return None

    async def download_song(self, item: DownloadQueueItem, music_id: str, music_type: str,
                           download_dir: str, preferred_quality: str = '无损',
                           download_lyrics: bool = True, session_logger: Optional[logging.Logger] = None,
                           music_info: Optional[Dict[str, Any]] = None) -> str:
        """
        下载歌曲，并可选择下载歌词和音质。返回下载的文件路径。
        """
        log = session_logger or logging.getLogger(__name__)

        if not music_info:
            log.info(f"获取歌曲 '{music_id}' (平台: {music_type}) 的信息...")
            music_info = await self.get_music_url(music_type, music_id, info=True, quality=preferred_quality)

        data = music_info.get('data')
        if not data or not isinstance(data, dict):
            raise APIError("API未返回有效的歌曲数据。")

        # 从新API响应中提取信息
        song_url = data.get('url')
        if not song_url:
            raise APIError("未找到可用的下载链接。")

        # 提取专辑封面URL
        cover_url = data.get('cover')
        
        # 尝试从API响应中获取文件格式，如果没有，则根据URL推断
        file_format_match = re.search(r'\.(\w+)$', song_url.split('?')[0])
        file_format = file_format_match.group(1) if file_format_match else 'mp3'

        actual_quality = data.get('quality', '未知')

        song_name = data.get('song', item.title)
        singer = data.get('singer', item.artist)

        clean_singer = re.sub(r'[\\/*?:"<>|]', "", singer)
        clean_name = re.sub(r'[\\/*?:"<>|]', "", song_name)
        file_basename = f"{clean_singer} - {clean_name}"

        download_path = Path(download_dir)
        download_path.mkdir(parents=True, exist_ok=True)

        song_filepath = download_path / f"{file_basename}.{file_format}"
        log.info(f"选择音质: {actual_quality}。正在下载到: {song_filepath}")

        try:
            # 使用GET请求下载文件，httpx会自动处理重定向
            async with self.http_client.stream("GET", song_url, timeout=180.0) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    log.info(f"收到重定向响应 {response.status_code}，httpx将自动跟随重定向...")

                response.raise_for_status()
                with open(song_filepath, 'wb') as f:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        f.write(chunk)
            log.info("歌曲下载完成。")
        except httpx.RequestError as e:
            raise APIError(f"下载歌曲时出错: {e}")
        except IOError as e:
            raise APIError(f"保存歌曲文件时出错: {e}")

        # 下载完成后，先进行低质量文件检测
        quality_checker = QualityChecker()
        if not quality_checker.is_file_acceptable(str(song_filepath), log):
            try:
                os.remove(str(song_filepath))
                log.info(f"已删除低质量文件: {song_filepath}")
            except OSError as e:
                log.warning(f"删除低质量文件 '{song_filepath}' 时出错: {e}")
            raise APIError(f"下载的文件 '{song_filepath}' 被标记为低质量或广告。")

        # 文件质量合格，继续嵌入 ID3 标签
        # 注意：我们需要确保 song_info_details 仍然可用或调整它
        song_info_details = data  # 使用整个 data 字典作为 song_info_details
        metadata_handler = MetadataHandler()
        # 传递封面URL到metadata_handler
        metadata_handler.embed_metadata(str(song_filepath), item, song_info_details, log, cover_url=cover_url)

        if download_lyrics:
            log.info("正在下载歌词...")
            
            # 调用 get_lyrics 方法获取歌词数据
            lrc_content = await self.get_lyrics(music_type, music_id, log)
            
            # 检查是否获取到歌词
            if lrc_content and lrc_content.strip():
                # 创建与歌曲文件同名但扩展名为 .lrc 的文件路径
                lyrics_filepath = song_filepath.with_suffix('.lrc')
                
                try:
                    # 将获取到的歌词内容以 UTF-8 编码写入文件
                    with open(lyrics_filepath, 'w', encoding='utf-8') as f:
                        f.write(lrc_content)
                    log.info(f"歌词下载成功并保存至 {lyrics_filepath}")
                except IOError as e:
                    log.warning(f"保存歌词文件时出错: {e}")
            else:
                log.info("未找到可用歌词")

        return str(song_filepath)

class DownloaderCore:
    """
    对 MusicDownloader 的包装，以适应我们的服务架构。
    """
    def __init__(self):
        self.downloader: Optional[MusicDownloader] = None
        self.download_path: str = "/downloads"
        # 服务实例
        self.platform_service = PlatformService()
        self.qq_music_service = QQMusicService()
        self.quality_checker = QualityChecker()

    def initialize(self, download_path: str):
        """初始化下载器，配置下载路径。"""
        logger.info("开始初始化下载器核心 (DownloaderCore)...")
        self.downloader = MusicDownloader()
        self.download_path = download_path
        Path(self.download_path).mkdir(parents=True, exist_ok=True)
        logger.info(f"下载器核心 (DownloaderCore) 初始化成功。下载路径: {self.download_path}")

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
                    detail = await self.qq_music_service.fetch_song_detail(songmid, session_logger)
                    if detail and isinstance(detail, dict):
                        # 补全专辑信息
                        album_info = detail.get('album')
                        if isinstance(album_info, dict) and album_info.get('name'):
                            # 创建一个新的对象，复制原有属性并更新专辑信息
                            # 检查item是否有__class__属性并且可以被正确复制
                            if hasattr(item, '__class__') and item.__class__.__name__ == 'DownloadQueueItem':
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
                            else:
                                # 对于测试中的Mock对象或其他不支持的类型，直接修改album属性
                                item.album = album_info['name']
                                enriched_item = item
                            session_logger.info(f"成功补全歌曲 '{item.title}' 的专辑信息: {album_info['name']}")
                            return enriched_item
                        else:
                            session_logger.debug(f"歌曲 '{item.title}' 的详情中未找到专辑信息")
        
        # 如果不需要补全或补全失败，返回原始项
        return item

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _find_song_id(self, item: DownloadQueueItem, session_logger: logging.Logger, 
                           exclude_platforms: Optional[List[str]] = None) -> Tuple[Optional[str], Optional[str], List[Dict[str, Any]]]:
        """使用歌曲信息搜索并返回最佳匹配的歌曲ID、平台和候选列表。"""
        session_logger.info(f"开始为 '{item.title}' 查找歌曲 ID...")
        if not self.downloader:
            raise ValueError("下载器未初始化")
        
        # 修改搜索策略：只使用歌曲标题进行搜索，搜索结果后再进行匹配
        search_term = item.title
        # 处理需要排除的平台
        if exclude_platforms is None:
            exclude_platforms = []

        platforms_to_search = self.platform_service.get_platforms_to_search(
            preferred_platform=self.platform_service.map_platform_name(item.platform) if item.platform else None,
            exclude_platforms=[self.platform_service.map_platform_name(p) if p else p for p in exclude_platforms]
        )
        
        # 遍历平台，逐一搜索
        for platform in platforms_to_search:
            try:
                session_logger.info(f"正在平台 '{platform}' 上搜索 '{search_term}'...")
                search_results = await self.downloader.search_platform(platform, search_term, 1, 10)

                # 新API直接在 'data' 键下返回列表
                songs_list = search_results.get('data', [])
                if not isinstance(songs_list, list):
                    session_logger.warning(f"平台 '{platform}' 的API响应格式不符合预期（'data' 不是列表）。")
                    songs_list = []

                if songs_list:
                    # 这里的 filter_and_score_candidates 可能需要根据新API的字段进行调整
                    # 我们假设它能处理 'song', 'singer', 'album' 等通用字段
                    # 并且能从候选对象中提取 'id' 或 'mid' 作为 song_id
                    candidates = self.platform_service.filter_and_score_candidates(item, songs_list, platform)

                    # Filter candidates with score > 70 for this platform
                    high_score_candidates = [c for c in candidates if c['score'] > 70]

                    # 如果当前平台找到了高匹配度的候选结果，则返回这些结果
                    if high_score_candidates:
                        session_logger.info(f"在平台 '{platform}' 上找到 {len(high_score_candidates)} 个高匹配度候选结果。")
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

    def _validate_api_response(self, music_info: dict, item: DownloadQueueItem) -> Tuple[bool, str]:
        """验证API响应与请求信息的一致性
        :param music_info: API返回的歌曲信息
        :param item: 下载队列项
        :return: (是否通过验证, 验证信息)
        """
        try:
            # 新API的点歌模式响应，信息在 'data' 字段中
            api_data = music_info.get('data', {})
            if not api_data:
                return False, "API未返回有效的歌曲数据"

            # 从API响应中提取歌曲信息
            api_title = api_data.get('song', '')
            api_artist = api_data.get('singer', '')

            # 如果API没有返回有效信息，认为验证失败
            if not api_title or not api_artist:
                return False, "API未返回有效的歌曲标题或艺术家信息"

            # 使用模糊匹配计算相似度
            requested_title = item.title or ''
            requested_artist = item.artist or ''

            title_score = fuzz.ratio(requested_title.lower(), api_title.lower())
            artist_score = fuzz.ratio(requested_artist.lower(), api_artist.lower())

            # 记录详细信息用于调试
            validation_details = f"请求:'{requested_title} by {requested_artist}', 实际:'{api_title} by {api_artist}', 标题匹配度:{title_score}, 艺术家匹配度:{artist_score}"

            # 设定阈值，如果匹配度低于阈值则认为不一致
            if title_score < API_VALIDATION_TITLE_THRESHOLD or artist_score < API_VALIDATION_ARTIST_THRESHOLD:
                return False, f"信息匹配度不足 - {validation_details}"

            return True, f"信息匹配度良好 - {validation_details}"
        except Exception as e:
            return False, f"验证过程中发生错误: {str(e)}"

    async def download(self, item: DownloadQueueItem, preferred_quality: str = '无损', 
                      download_lyrics: bool = False, session_logger: Optional[logging.Logger] = None) -> str:
        """执行单个下载任务。"""
        
        # 如果没有提供专用的 logger，则使用全局 logger
        if not session_logger:
            session_logger = logging.getLogger(__name__)

        session_logger.info(f"开始处理下载任务 for: {item.title} - {item.artist}")
        if not self.downloader:
            raise ValueError("下载器未初始化。")

        # 补全缺失的歌曲信息
        enriched_item = await self._enrich_track_info(item, session_logger)
        
        song_id = enriched_item.song_id
        platform = self.platform_service.map_platform_name(enriched_item.platform) if enriched_item.platform else None

        # 步骤 1: 如果有现成的 song_id 和 platform，先验证再尝试下载
        if song_id and platform:
            session_logger.info(f"步骤 1: 验证提供的歌曲 ID '{song_id}' 和平台 '{platform}' 的信息匹配度")
            try:
                # 获取API返回的歌曲详细信息
                # 注意：get_music_url 现在需要平台作为第一个参数，并传递音质参数
                music_info = await self.downloader.get_music_url(platform, song_id, info=True, quality=preferred_quality)
                # 验证API返回信息与请求信息的一致性
                is_valid, validation_msg = self._validate_api_response(music_info, enriched_item)
                
                if is_valid:
                    session_logger.info(f"API响应验证通过: {validation_msg}")
                    # 信息匹配，使用直接下载
                    file_path = await self.downloader.download_song(
                        enriched_item,
                        song_id,
                        platform,
                        self.download_path,
                        preferred_quality,
                        download_lyrics,
                        session_logger,
                        music_info=music_info  # 传递已获取的 music_info
                    )
                    session_logger.info(f"步骤 1 完成. 直接下载成功。文件路径: {file_path}")
                    return file_path
                else:
                    session_logger.warning(f"API响应验证失败: {validation_msg}。将回退到搜索模式。")
                    # 信息不匹配，清空 song_id 和 platform，进入搜索流程
                    song_id = None
                    platform = None  # 同时清空 platform
            except tenacity.RetryError as retry_err:
                # 捕获 RetryError，获取原始的 APIError
                original_err = retry_err.last_attempt.exception()
                session_logger.warning(f"获取歌曲信息失败 (重试次数已用尽): {original_err}。将回退到搜索模式。")
                # 直接下载失败，清空 song_id 和 platform，进入搜索流程
                song_id = None
                platform = None  # 同时清空 platform
            except APIError as e:
                session_logger.warning(f"获取歌曲信息失败: {e}。将回退到搜索模式。")
                # 直接下载失败，清空 song_id 和 platform，进入搜索流程
                song_id = None
                platform = None  # 同时清空 platform
        
        # 步骤 2: 如果没有 song_id 或直接下载失败，则进行逐一平台搜索和下载
        failed_platforms = []  # Track platforms that have failed or produced low-quality results
        if not song_id:
            session_logger.info(f"步骤 2: 开始逐一平台搜索并尝试下载 '{enriched_item.title}'...")
            
            while True:  # 循环搜索，直到成功或所有平台都失败
                try:
                    # 调用修改后的 _find_song_id，它会在找到高匹配度结果的平台后立即返回
                    song_id, platform, candidates_list = await self._find_song_id(enriched_item, session_logger, failed_platforms)
                    if not song_id or not platform:
                        # 理论上 _find_song_id 会抛出异常，但如果返回了无效ID/平台，也应处理
                        raise APIError(f"搜索返回了无效的歌曲 ID 或平台。")
                    
                    session_logger.info(f"在平台 '{platform}' 上找到候选结果，开始尝试下载...")
                    
                    # 尝试下载找到的候选结果
                    try:
                        file_path = await self.downloader.download_song(
                            enriched_item,  # 传递补全信息后的 item
                            song_id,
                            platform,
                            self.download_path,
                            preferred_quality,
                            download_lyrics,
                            session_logger
                        )
                        # Check if this file is acceptable (质量合格)
                        if self.quality_checker.is_file_acceptable(file_path, session_logger):
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
                        # 特别处理"未知异常"错误
                        if "未知异常" in str(e):
                            session_logger.warning(f"使用平台 '{platform}' 下载失败，遇到'未知异常'错误: {e}。将跳过此平台并记录详细信息。")
                            # 记录更多调试信息
                            session_logger.warning(f"详细信息 - 歌曲ID: {song_id}, 平台: {platform}")
                        else:
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
                    file_path = await self.downloader.download_song(
                        enriched_item,
                        song_id,
                        platform,
                        self.download_path,
                        preferred_quality,
                        download_lyrics,
                        session_logger
                    )
                    # Check if this file is acceptable
                    if self.quality_checker.is_file_acceptable(file_path, session_logger):
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