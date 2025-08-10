import pytest
from unittest.mock import AsyncMock, Mock, patch
import sys
import os


from services.plex_service import PlexService, normalize_string
from services.playlist_service import PlaylistService
from plexapi.library import MusicSection
from plexapi.audio import Track

class TestPlexService:
    """Plex服务测试类"""
    
    def setup_method(self):
        """在每个测试方法运行前执行"""
        with patch('services.plex_service.PlexServer') as mock_plex_server:
            mock_server_instance = Mock()
            mock_plex_server.return_value = mock_server_instance
            self.plex_service = PlexService("http://test.com", "test_token")
            self.plex_service.server = mock_server_instance
            
    def test_init_success(self):
        """测试初始化成功"""
        assert self.plex_service.server is not None
        
    def test_get_music_library_success(self):
        """测试成功获取音乐资料库"""
        # 模拟返回的资料库列表
        mock_library = Mock(spec=MusicSection)
        mock_library.type = 'artist'
        mock_library.title = 'Music'
        mock_library.key = 1
        
        self.plex_service.server.library.sections.return_value = [mock_library]
        
        library = self.plex_service.get_music_library()
        assert library == mock_library
        
    def test_get_music_library_not_found(self):
        """测试未找到音乐资料库"""
        # 模拟返回的资料库列表（没有artist类型）
        mock_library = Mock()
        mock_library.type = 'photo'
        
        self.plex_service.server.library.sections.return_value = [mock_library]
        
        library = self.plex_service.get_music_library()
        assert library is None
        
    def test_find_track_exact_match_with_artist(self):
        """测试使用艺术家精确匹配音轨"""
        mock_library = Mock(spec=MusicSection)
        mock_track = Mock(spec=Track)
        mock_track.title = 'Test Song'
        
        # 模拟搜索结果
        mock_library.searchTracks.return_value = [mock_track]
        
        with patch('services.plex_service.fuzz', None):  # 禁用模糊匹配
            result = self.plex_service.find_track('Test Song', 'Test Artist', mock_library)
            
        assert result == mock_track
        mock_library.searchTracks.assert_called_once_with(title='Test Song', artist='Test Artist')
        
    def test_create_or_update_playlist_create_new(self):
        """测试创建新的播放列表"""
        mock_server = self.plex_service.server
        mock_playlist = Mock()
        mock_tracks = [Mock(), Mock()]
        
        # 模拟找不到现有播放列表
        from plexapi.exceptions import NotFound
        mock_server.playlist.side_effect = NotFound("Not found")
        mock_server.createPlaylist.return_value = mock_playlist
        
        log_callback = Mock()
        result = self.plex_service.create_or_update_playlist('New Playlist', mock_tracks, log_callback)
        
        assert result is True
        mock_server.createPlaylist.assert_called_once_with('New Playlist', items=mock_tracks)
        log_callback.assert_called_with('success', '成功创建并导入 2 首歌曲到 Plex 播放列表 "New Playlist"。')
        
    def test_create_or_update_playlist_update_existing(self):
        """测试更新现有的播放列表"""
        mock_server = self.plex_service.server
        mock_playlist = Mock()
        mock_tracks = [Mock(), Mock()]
        
        # 模拟找到现有播放列表
        mock_server.playlist.return_value = mock_playlist
        mock_playlist.items.return_value = []
        
        log_callback = Mock()
        result = self.plex_service.create_or_update_playlist('Existing Playlist', mock_tracks, log_callback)
        
        assert result is True
        mock_server.playlist.assert_called_once_with('Existing Playlist')
        mock_playlist.addItems.assert_called_once_with(mock_tracks)
        log_callback.assert_called_with('success', '成功更新并导入 0 首歌曲到 Plex 播放列表 "Existing Playlist"。')

class TestNormalizeString:
    """测试字符串标准化函数"""
    
    def test_normalize_string_basic(self):
        """测试基本字符串标准化"""
        assert normalize_string("Hello World") == "hello world"
        assert normalize_string("HELLO WORLD") == "hello world"
        
    def test_normalize_string_with_parentheses(self):
        """测试移除括号内容"""
        assert normalize_string("Song Title (feat. Artist)") == "song title"
        assert normalize_string("Track [Remastered]") == "track"
        
    def test_normalize_string_with_keywords(self):
        """测试移除特定关键词"""
        assert normalize_string("Song - Deluxe Edition") == "song"
        assert normalize_string("Track explicit") == "track"
        assert normalize_string("Music remastered") == "music"
        assert normalize_string("Song feat. Artist") == "song artist"
        assert normalize_string("Track ft. Singer") == "track singer"
        
    def test_normalize_string_with_punctuation(self):
        """测试移除标点符号"""
        assert normalize_string("Song, Track: Title!") == "song track title"
        
    def test_normalize_string_empty(self):
        """测试空字符串"""
        assert normalize_string("") == ""
        assert normalize_string(None) == ""