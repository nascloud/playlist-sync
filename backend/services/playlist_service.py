import httpx
import re
import json
from typing import Dict, List, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class Platform(Enum):
    NETEASE = "netease"
    QQ = "qq"

class PlaylistService:
    @staticmethod
    def extract_playlist_id(url: str, platform: Platform) -> str:
        """
        从URL或ID中提取歌单ID
        :param url: 歌单URL或ID
        :param platform: 平台类型
        :return: 提取的歌单ID
        """
        if platform == Platform.NETEASE:
            # 匹配 id=数字 的模式
            match = re.search(r'id=(\d+)', url)
            if match:
                return match.group(1)
            
            # 如果输入是纯数字ID
            if url.isdigit():
                return url
                
        elif platform == Platform.QQ:
            # 匹配 /playlist/(数字) 的模式
            match = re.search(r'/playlist/(\d+)', url)
            if match:
                return match.group(1)
            
            # 如果输入是纯数字ID
            if url.isdigit():
                return url
        
        return None
    
    @staticmethod
    async def fetch_netease_playlist(playlist_id: str) -> Dict:
        """
        获取网易云音乐歌单（增强版，包含歌曲ID）
        :param playlist_id: 歌单ID
        :return: 包含歌单标题和曲目的字典，曲目包含歌曲ID
        """
        # 使用更可靠的v6 API端点，以获取完整的歌单信息
        playlist_url = f"https://music.163.com/api/v6/playlist/detail?id={playlist_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://music.163.com/',
            'Cookie': 'appver=2.0.2; os=pc;'
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(playlist_url, headers=headers, timeout=10.0)
                response.raise_for_status()
                data = response.json()
                
                if not data.get('playlist'):
                    raise Exception('无法获取网易云歌单，请检查ID或歌单是否公开。')
                
                playlist_data = data['playlist']
                playlist_title = playlist_data.get('name', '未知歌单')
                tracks = []
                
                # 优先使用 trackIds 字段，因为它通常包含完整的歌曲ID列表
                if playlist_data.get('trackIds'):
                    track_ids = [str(item['id']) for item in playlist_data['trackIds']]
                    if track_ids:
                        song_details_url = "https://music.163.com/api/v3/song/detail"
                        headers_songs = headers.copy()
                        # 分批获取歌曲详情
                        for i in range(0, len(track_ids), 500):
                            batch_ids = track_ids[i:i+500]
                            c_param = json.dumps([{'id': tid} for tid in batch_ids])
                            payload = {'c': c_param}
                            try:
                                details_response = await client.post(song_details_url, headers=headers_songs, data=payload, timeout=15.0)
                                details_response.raise_for_status()
                                details_data = details_response.json()
                                if details_data.get('songs'):
                                    for track_detail in details_data['songs']:
                                        artists = ", ".join([artist.get('name', '未知歌手') for artist in track_detail.get('ar', [])])
                                        album = track_detail.get('al', {}).get('name', '未知专辑')
                                        # 提取歌曲ID - 网易云音乐直接使用id字段
                                        song_id = str(track_detail.get('id', ''))
                                        tracks.append({
                                            'title': track_detail.get('name', '未知歌名'), 
                                            'artist': artists, 
                                            'album': album,
                                            'song_id': song_id,  # 新增：包含歌曲ID
                                            'platform': 'netease'  # 新增：标识平台
                                        })
                            except Exception as e:
                                logger.warning(f"获取歌曲详情失败 (batch starting at {i}): {e}")
                                continue
                
                # 如果 trackIds 不可用或为空，则回退到使用 tracks 字段（作为备用）
                if not tracks and playlist_data.get('tracks'):
                    for track in playlist_data['tracks']:
                        artists = ', '.join([a.get('name', '未知歌手') for a in track.get('ar', [])])
                        album = track.get('al', {}).get('name', '未知专辑')
                        # 提取歌曲ID - 网易云音乐直接使用id字段
                        song_id = str(track.get('id', ''))
                        tracks.append({
                            'title': track.get('name', '未知歌名'), 
                            'artist': artists, 
                            'album': album,
                            'song_id': song_id,  # 新增：包含歌曲ID
                            'platform': 'netease'  # 新增：标识平台
                        })

                # 如果仍然没有获取到歌曲，记录警告
                if not tracks:
                    logger.warning(f"网易云歌单 {playlist_id} 未能获取到任何歌曲。")

                return {'title': playlist_title, 'tracks': tracks}
            except httpx.RequestError as e:
                logger.error(f"请求网易云歌单失败: {e}")
                raise Exception(f'请求网易云歌单失败: {e}')
            except Exception as e:
                logger.error(f"处理网易云歌单时出错: {str(e)}")
                raise Exception(f'处理网易云歌单时出错: {str(e)}')
    
    @staticmethod
    async def fetch_qq_playlist(playlist_id: str) -> Dict:
        """
        获取QQ音乐歌单（增强版，包含歌曲ID）
        :param playlist_id: 歌单ID
        :return: 包含歌单标题和曲目的字典，曲目包含歌曲ID
        """
        url = "https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg"
        params = {
            'type': '1', 'json': '1', 'utf8': '1', 'onlysong': '0', 
            'disstid': playlist_id, 'format': 'json', 'platform': 'yqq.json'
        }
        headers = {
            'Referer': 'https://y.qq.com/',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, headers=headers, params=params, timeout=10.0)
                response.raise_for_status()
                # 响应可能包含非标准的JSON开头，需要清理
                cleaned_text = response.text.strip()
                if cleaned_text.startswith('callback('):
                    cleaned_text = cleaned_text[len('callback('):-1]
                elif cleaned_text.startswith('jsonpCallback('):
                    cleaned_text = cleaned_text[len('jsonpCallback('):-1]
                
                data = json.loads(cleaned_text)

                if not data or not data.get('cdlist') or len(data['cdlist']) == 0:
                    raise Exception('无法获取QQ音乐歌单，请检查ID或歌单是否公开，或响应格式是否正确。')
                
                playlist = data['cdlist'][0]
                playlist_title = playlist.get('dissname', '未知歌单')
                tracks = []
                
                if playlist.get('songlist'):
                    for song in playlist['songlist']:
                        singers = ', '.join([s.get('name', '未知歌手') for s in song.get('singer', [])])
                        album = song.get('album', {}).get('name', '未知专辑')
                        
                        # 提取歌曲ID - QQ音乐需要组合songid和songmid
                        songid = song.get('songid', '')
                        songmid = song.get('songmid', '')
                        
                        # 组合为下载器需要的格式: "songid-songmid"
                        if songid and songmid:
                            song_id = f"{songid}-{songmid}"
                        else:
                            song_id = ''
                        
                        tracks.append({
                            'title': song.get('songname', '未知歌名'), 
                            'artist': singers, 
                            'album': album,
                            'song_id': song_id,  # 新增：包含歌曲ID（组合格式）
                            'platform': 'qq'  # 新增：标识平台
                        })
                
                return {'title': playlist_title, 'tracks': tracks}
            except httpx.RequestError as e:
                logger.error(f"请求QQ音乐歌单失败: {e}")
                raise Exception(f"请求QQ音乐歌单失败: {e}")
            except json.JSONDecodeError:
                logger.error("解析QQ音乐歌单响应失败，可能不是有效的JSON。")
                raise Exception("解析QQ音乐歌单响应失败。")
            except Exception as e:
                logger.error(f"处理QQ音乐歌单时出错: {str(e)}")
                raise Exception(f'处理QQ音乐歌单时出错: {str(e)}')
    
    @classmethod
    async def parse_playlist(cls, url: str, platform: str) -> Dict:
        """
        解析歌单（增强版，包含歌曲ID）
        :param url: 歌单URL
        :param platform: 平台类型 ('netease' 或 'qq')
        :return: 包含歌单标题和曲目的字典，曲目包含歌曲ID
        """
        if not url or not platform:
            raise Exception('URL 和平台类型为必填项。')
        
        try:
            platform_enum = Platform(platform)
        except ValueError:
            raise Exception('不支持的平台类型。')
        
        playlist_id = cls.extract_playlist_id(url, platform_enum)
        if not playlist_id:
            raise Exception('无法从URL中提取有效的歌单ID。')
        
        if platform_enum == Platform.NETEASE:
            return await cls.fetch_netease_playlist(playlist_id)
        elif platform_enum == Platform.QQ:
            return await cls.fetch_qq_playlist(playlist_id)

    @staticmethod
    def get_song_id_for_downloader(track: Dict) -> Optional[str]:
        """
        从曲目信息中提取适合下载器使用的歌曲ID
        :param track: 曲目信息字典
        :return: 歌曲ID字符串，如果没有则返回None
        """
        song_id = track.get('song_id')
        platform = track.get('platform')
        
        if not song_id:
            return None
            
        # 根据平台格式化歌曲ID
        if platform == 'netease':
            # 网易云音乐歌曲ID可以直接使用
            return song_id
        elif platform == 'qq':
            # QQ音乐歌曲ID已经是组合格式 (songid-songmid)
            return song_id
        
        return song_id

    @staticmethod
    def can_use_direct_download(track: Dict) -> bool:
        """
        判断是否可以直接使用歌曲ID进行下载
        :param track: 曲目信息字典
        :return: 是否可以直接下载
        """
        song_id = track.get('song_id')
        platform = track.get('platform')
        
        # 检查是否有有效的歌曲ID和平台信息
        return bool(song_id and platform in ['netease', 'qq'])
