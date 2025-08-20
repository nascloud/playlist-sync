"""音频文件元数据处理服务"""

import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
from mutagen import File
from mutagen.flac import Picture, FLAC
from mutagen.mp3 import MP3

from schemas.download import DownloadQueueItem

logger = logging.getLogger(__name__)

class MetadataHandler:
    """处理音频文件的元数据嵌入"""
    
    def embed_metadata(self, file_path: str, item: DownloadQueueItem, 
                      song_api_info: dict, log: logging.Logger):
        """
        将元数据和封面图片嵌入到音频文件中。
        """
        log.info(f"开始为文件 '{Path(file_path).name}' 嵌入元数据...")
        try:
            self._embed_basic_metadata(file_path, item, song_api_info, log)
            self._embed_cover_art(file_path, song_api_info, log)
            log.info("元数据处理流程完成。")
        except Exception as e:
            log.error(f"嵌入元数据时发生未知错误: {e}", exc_info=True)
            raise

    def _extract_string_value(self, value) -> Optional[str]:
        """从可能的列表或字符串中提取字符串值"""
        if isinstance(value, list):
            if len(value) > 0:
                first_element = value[0]
                if first_element is not None:
                    str_value = str(first_element)
                    if str_value.strip():
                        return str_value
            return None
        elif value is not None:
            str_value = str(value)
            if str_value.strip():
                return str_value
        return None

    def _embed_basic_metadata(self, file_path: str, item: DownloadQueueItem,
                             song_api_info: dict, log: logging.Logger):
        """嵌入基础元数据（标题、艺术家、专辑）"""
        audio = File(file_path, easy=True)
        if audio is None:
            log.error("Mutagen无法加载音频文件，可能是不支持的格式或文件已损坏。")
            raise ValueError("无法加载音频文件，可能是不支持的格式。")

        # 处理元数据值
        title = self._extract_string_value(song_api_info.get('name')) or \
                self._extract_string_value(item.title) or ""
        artist = self._extract_string_value(song_api_info.get('artist')) or \
                 self._extract_string_value(item.artist) or ""
        album = self._extract_string_value(song_api_info.get('album')) or \
                self._extract_string_value(item.album) or "未知专辑"

        audio['title'] = title
        audio['artist'] = artist
        audio['album'] = album
        
        log.info(f"基础元数据待写入: Title='{audio['title']}', Artist='{audio['artist']}', Album='{audio['album']}'")
        audio.save()
        log.info("基础元数据写入成功。")

    def _embed_cover_art(self, file_path: str, song_api_info: dict, log: logging.Logger):
        """嵌入封面图片"""
        audio = File(file_path)
        pic_url = song_api_info.get('pic') if song_api_info else None
        log.info(f"API返回的封面URL: {pic_url}")

        if not pic_url:
            log.info("未找到有效的封面图片URL，跳过封面嵌入。")
            return

        log.info(f"正在从 {pic_url} 下载封面图片...")
        try:
            cover_response = requests.get(pic_url, timeout=15)
            cover_response.raise_for_status()
            cover_data = cover_response.content
            log.info(f"封面图片下载成功，大小: {len(cover_data)} bytes。")

            if isinstance(audio, FLAC):
                log.info("检测到FLAC文件，使用 add_picture 方法。")
                self._embed_flac_cover(audio, cover_data, log)
            elif isinstance(audio, MP3):
                log.info("检测到MP3文件，使用 APIC 帧。")
                self._embed_mp3_cover(audio, cover_data, log)
            else:
                log.warning(f"文件类型 {type(audio)} 可能不支持封面嵌入，将尝试使用APIC。")
                self._embed_generic_cover(audio, cover_data, log)

            log.info("封面数据帧创建成功，准备保存。")
            audio.save()
            log.info("封面图片嵌入并保存成功。")

        except requests.exceptions.RequestException as e:
            log.warning(f"下载封面图片失败: {e}")
        except Exception as e_mutagen_apic:
            log.error(f"使用Mutagen嵌入封面时出错: {e_mutagen_apic}", exc_info=True)

    def _embed_flac_cover(self, audio: FLAC, cover_data: bytes, log: logging.Logger):
        """为FLAC文件嵌入封面"""
        pic = Picture()
        pic.type = 3  # Cover (front)
        pic.mime = "image/jpeg"
        pic.desc = "Cover"
        pic.data = cover_data
        audio.add_picture(pic)

    def _embed_mp3_cover(self, audio: MP3, cover_data: bytes, log: logging.Logger):
        """为MP3文件嵌入封面"""
        audio['APIC'] = APIC(
            encoding=3,
            mime='image/jpeg',
            type=3,
            desc='Cover',
            data=cover_data
        )

    def _embed_generic_cover(self, audio, cover_data: bytes, log: logging.Logger):
        """为其他格式文件嵌入封面"""
        audio['APIC'] = APIC(
            encoding=3,
            mime='image/jpeg',
            type=3,
            desc='Cover',
            data=cover_data
        )
