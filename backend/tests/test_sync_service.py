import pytest
from unittest.mock import AsyncMock, Mock, patch
import sys
import os
import sqlite3
from datetime import datetime


from services.sync_service import SyncService
from services.plex_service import PlexService
from services.playlist_service import PlaylistService

class TestSyncService:
    """同步服务测试类"""
    
    def setup_method(self):
        """在每个测试方法运行前执行"""
        self.sync_service = SyncService()
        
    def test_init(self):
        """测试初始化"""
        assert self.sync_service.plex_service is None
        assert isinstance(self.sync_service.playlist_service, PlaylistService)
        
    @pytest.mark.asyncio
    async def test_sync_playlist_success(self):
        """测试成功同步播放列表"""
        task_id = 1
        playlist_url = "https://music.163.com/#/playlist?id=1234567890"
        platform = "netease"
        playlist_name = "Test Playlist"
        
        # 创建模拟对象
        mock_plex_service = Mock(spec=PlexService)
        mock_music_library = Mock()
        mock_track = Mock()
        
        # 设置模拟返回值
        self.sync_service.plex_service = mock_plex_service
        mock_plex_service.get_music_library.return_value = mock_music_library
        self.sync_service.playlist_service = AsyncMock()
        self.sync_service.playlist_service.parse_playlist.return_value = {
            'title': 'Test Playlist',
            'tracks': [
                {'title': 'Song 1', 'artist': 'Artist 1'},
                {'title': 'Song 2', 'artist': 'Artist 2'}
            ]
        }
        mock_plex_service.find_track.return_value = mock_track  # 所有歌曲都匹配成功
        mock_plex_service.create_or_update_playlist.return_value = True
        
        # 模拟数据库操作
        with patch.object(self.sync_service, '_get_settings', return_value={'plex_url': 'http://test.com', 'plex_token': 'test_token'}), \
             patch.object(self.sync_service, '_update_task_status') as mock_update_status, \
             patch.object(self.sync_service, '_update_last_sync_time') as mock_update_time:
            
            log_callback = Mock()
            result = await self.sync_service.sync_playlist(task_id, playlist_url, platform, playlist_name, log_callback)
            
            # 验证结果
            assert result is True
            
            # 验证调用
            self.sync_service.playlist_service.parse_playlist.assert_called_once_with(playlist_url, platform)
            mock_plex_service.find_track.assert_called()
            mock_plex_service.create_or_update_playlist.assert_called_once()
            mock_update_status.assert_called_with(task_id, 'idle')
            mock_update_time.assert_called_with(task_id)
            log_callback.assert_called()
            
    @pytest.mark.asyncio
    async def test_sync_playlist_plex_settings_missing(self):
        """测试缺少Plex设置时的处理"""
        task_id = 1
        playlist_url = "https://music.163.com/#/playlist?id=1234567890"
        platform = "netease"
        playlist_name = "Test Playlist"
        
        # 模拟缺少设置
        with patch.object(self.sync_service, '_get_settings', return_value=None):
            log_callback = Mock()
            result = await self.sync_service.sync_playlist(task_id, playlist_url, platform, playlist_name, log_callback)
            
            # 验证结果
            assert result is False
            log_callback.assert_called_with('error', '任务失败: 未找到Plex设置')