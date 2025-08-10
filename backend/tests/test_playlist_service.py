import pytest
from unittest.mock import AsyncMock, Mock, patch
import sys
import os
import json


from services.playlist_service import PlaylistService, Platform

class TestPlaylistService:
    """播放列表服务测试类"""
    
    def test_extract_playlist_id_netease_with_id_param(self):
        """测试从网易云音乐URL中提取ID（id参数）"""
        url = "https://music.163.com/#/playlist?id=1234567890"
        result = PlaylistService.extract_playlist_id(url, Platform.NETEASE)
        assert result == "1234567890"
        
    def test_extract_playlist_id_netease_numeric(self):
        """测试直接提供网易云音乐ID"""
        url = "1234567890"
        result = PlaylistService.extract_playlist_id(url, Platform.NETEASE)
        assert result == "1234567890"
        
    def test_extract_playlist_id_qq_with_path(self):
        """测试从QQ音乐URL中提取ID（路径）"""
        url = "https://y.qq.com/n/ryqq/playlist/9876543210.html"
        result = PlaylistService.extract_playlist_id(url, Platform.QQ)
        assert result == "9876543210"
        
    def test_extract_playlist_id_qq_numeric(self):
        """测试直接提供QQ音乐ID"""
        url = "9876543210"
        result = PlaylistService.extract_playlist_id(url, Platform.QQ)
        assert result == "9876543210"
        
    def test_extract_playlist_id_invalid(self):
        """测试无效URL"""
        url = "https://example.com/playlist/123"
        result = PlaylistService.extract_playlist_id(url, Platform.NETEASE)
        assert result is None
        
    @pytest.mark.asyncio
    async def test_fetch_netease_playlist_success(self):
        """测试成功获取网易云音乐播放列表"""
        playlist_id = "1234567890"
        
        # 模拟HTTP响应
        mock_response = Mock()
        mock_response.json.return_value = {
            "playlist": {
                "name": "Test Playlist",
                "tracks": [
                    {
                        "name": "Song 1",
                        "ar": [{"name": "Artist 1"}]
                    },
                    {
                        "name": "Song 2",
                        "ar": [{"name": "Artist 2"}]
                    }
                ]
            }
        }
        
        with patch('services.playlist_service.httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get.return_value = mock_response
            
            result = await PlaylistService.fetch_netease_playlist(playlist_id)
            
            # 验证结果
            assert result['title'] == "Test Playlist"
            assert len(result['tracks']) == 2
            assert result['tracks'][0]['title'] == "Song 1"
            assert result['tracks'][0]['artist'] == "Artist 1"
            
    @pytest.mark.asyncio
    async def test_fetch_qq_playlist_success(self):
        """测试成功获取QQ音乐播放列表"""
        playlist_id = "9876543210"
        
        # 模拟HTTP响应
        mock_response = Mock()
        mock_response.text = '''{
            "cdlist": [{
                "dissname": "Test QQ Playlist",
                "songlist": [
                    {
                        "songname": "QQ Song 1",
                        "singer": [{"name": "QQ Artist 1"}]
                    }
                ]
            }]
        }'''
        
        with patch('services.playlist_service.httpx.AsyncClient') as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get.return_value = mock_response
            
            result = await PlaylistService.fetch_qq_playlist(playlist_id)
            
            # 验证结果
            assert result['title'] == "Test QQ Playlist"
            assert len(result['tracks']) == 1
            assert result['tracks'][0]['title'] == "QQ Song 1"
            assert result['tracks'][0]['artist'] == "QQ Artist 1"
            
    @pytest.mark.asyncio
    async def test_parse_playlist_success(self):
        """测试成功解析播放列表"""
        url = "https://music.163.com/#/playlist?id=1234567890"
        platform = "netease"
        
        # 模拟extract_playlist_id和fetch_netease_playlist
        with patch.object(PlaylistService, 'extract_playlist_id', return_value="1234567890") as mock_extract, \
             patch.object(PlaylistService, 'fetch_netease_playlist', return_value={"title": "Test", "tracks": []}) as mock_fetch:
            
            result = await PlaylistService.parse_playlist(url, platform)
            
            # 验证调用
            mock_extract.assert_called_once_with(url, Platform.NETEASE)
            mock_fetch.assert_called_once_with("1234567890")
            assert result['title'] == "Test"