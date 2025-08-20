"""歌曲信息验证服务"""

import logging
from typing import Dict, Optional
from thefuzz import fuzz
from mutagen import File
from mutagen.id3 import ID3
from mutagen.flac import FLAC

logger = logging.getLogger(__name__)

class SongValidator:
    """验证下载的歌曲信息是否与原始信息匹配"""
    
    def validate_song_info(self, file_path: str, original_item: Dict, log: logging.Logger) -> bool:
        """
        验证下载的歌曲文件信息是否与原始信息匹配
        :param file_path: 下载的歌曲文件路径
        :param original_item: 原始歌曲信息字典
        :param log: 日志记录器
        :return: 是否匹配
        """
        try:
            # 读取文件的元数据
            metadata = self._extract_metadata(file_path, log)
            if not metadata:
                log.warning(f"无法读取文件 '{file_path}' 的元数据")
                return False
            
            # 获取原始信息
            original_title = original_item.get('title', '')
            original_artist = original_item.get('artist', '')
            original_album = original_item.get('album', '')
            
            # 获取文件元数据
            file_title = metadata.get('title', '')
            file_artist = metadata.get('artist', '')
            file_album = metadata.get('album', '')
            
            log.debug(f"原始信息: 标题='{original_title}', 艺术家='{original_artist}', 专辑='{original_album}'")
            log.debug(f"文件信息: 标题='{file_title}', 艺术家='{file_artist}', 专辑='{file_album}'")
            
            # 计算匹配分数
            title_score = fuzz.ratio(original_title.lower(), file_title.lower())
            artist_score = fuzz.ratio(original_artist.lower(), file_artist.lower())
            album_score = fuzz.ratio(original_album.lower(), file_album.lower()) if original_album and file_album else 100
            
            # 综合评分 (标题权重最高，艺术家次之，专辑最低)
            combined_score = (title_score * 0.5) + (artist_score * 0.4) + (album_score * 0.1)
            
            log.debug(f"匹配分数: 标题={title_score}, 艺术家={artist_score}, 专辑={album_score}, 综合={combined_score}")
            
            # 设定阈值，例如80分以上认为是匹配
            is_match = combined_score >= 80
            
            if not is_match:
                log.warning(f"歌曲信息不匹配: '{original_title}' vs '{file_title}' (综合分数: {combined_score})")
            
            return is_match
            
        except Exception as e:
            log.error(f"验证歌曲信息时出错: {e}", exc_info=True)
            return False
    
    def _extract_metadata(self, file_path: str, log: logging.Logger) -> Optional[Dict[str, str]]:
        """
        从音频文件中提取元数据
        :param file_path: 音频文件路径
        :param log: 日志记录器
        :return: 包含元数据的字典
        """
        try:
            # 使用mutagen读取文件
            audio_file = File(file_path, easy=True)
            if audio_file is None:
                log.warning(f"无法使用mutagen读取文件: {file_path}")
                return None
            
            # 提取基本信息
            metadata = {}
            
            # 提取标题
            if 'title' in audio_file:
                title = audio_file['title']
                if isinstance(title, list):
                    metadata['title'] = title[0] if title else ''
                else:
                    metadata['title'] = str(title)
            
            # 提取艺术家
            if 'artist' in audio_file:
                artist = audio_file['artist']
                if isinstance(artist, list):
                    metadata['artist'] = artist[0] if artist else ''
                else:
                    metadata['artist'] = str(artist)
            
            # 提取专辑
            if 'album' in audio_file:
                album = audio_file['album']
                if isinstance(album, list):
                    metadata['album'] = album[0] if album else ''
                else:
                    metadata['album'] = str(album)
            
            return metadata
            
        except Exception as e:
            log.error(f"提取元数据时出错: {e}", exc_info=True)
            return None