import sys
import os
import logging
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add the project root directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.plex_service import PlexService, normalize_string, _remove_brackets, _remove_keywords, _remove_punctuation, _normalize_string

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestPlexServiceStringNormalization(unittest.TestCase):
    """测试字符串标准化功能"""
    
    def test_remove_brackets(self):
        """测试移除括号功能"""
        # 测试英文括号
        self.assertEqual(_remove_brackets("Song Title (feat. Artist)"), "Song Title ")
        self.assertEqual(_remove_brackets("Song Title [feat. Artist]"), "Song Title ")
        
        # 测试中文括号
        self.assertEqual(_remove_brackets("Song Title （feat. Artist）"), "Song Title ")
        self.assertEqual(_remove_brackets("Song Title ［feat. Artist］"), "Song Title ")
        
        # 测试混合括号
        self.assertEqual(_remove_brackets("Song Title (feat. Artist) [Remix]"), "Song Title  ")
        
        # 测试不包含特定内容的括号
        self.assertEqual(_remove_brackets("Song Title (Live)"), "Song Title ")
        self.assertEqual(_remove_brackets("Song Title [Acoustic]"), "Song Title ")
        
    def test_remove_keywords(self):
        """测试移除关键字功能"""
        self.assertEqual(_remove_keywords("Song Title feat Artist"), "Song Title  Artist")
        self.assertEqual(_remove_keywords("Song Title ft Artist"), "Song Title  Artist")
        self.assertEqual(_remove_keywords("Song Title remix"), "Song Title ")
        self.assertEqual(_remove_keywords("Song Title edit"), "Song Title ")
        self.assertEqual(_remove_keywords("Song Title version"), "Song Title ")
        self.assertEqual(_remove_keywords("Song Title explicit"), "Song Title ")
        self.assertEqual(_remove_keywords("Song Title deluxe"), "Song Title ")
        self.assertEqual(_remove_keywords("Song Title remastered"), "Song Title ")
        self.assertEqual(_remove_keywords("Song Title edition"), "Song Title ")
        
    def test_remove_punctuation(self):
        """测试移除标点符号功能"""
        self.assertEqual(_remove_punctuation("Song Title!"), "Song Title ")
        self.assertEqual(_remove_punctuation("Song Title?"), "Song Title ")
        self.assertEqual(_remove_punctuation("Song Title,"), "Song Title ")
        self.assertEqual(_remove_punctuation("Song Title;"), "Song Title ")
        self.assertEqual(_remove_punctuation("Song Title:"), "Song Title ")
        self.assertEqual(_remove_punctuation("Song Title-"), "Song Title ")
        
    def test_normalize_string(self):
        """测试完整的字符串标准化功能"""
        # 测试完整流程
        self.assertEqual(normalize_string("Song Title (feat. Artist) [Remix]"), "song title")
        self.assertEqual(normalize_string("Song Title ft Artist remix"), "song title artist")
        self.assertEqual(normalize_string("Song Title, Vol. 1!"), "song title vol 1")
        self.assertEqual(normalize_string("Song Title　（feat. Artist）"), "song title")  # 全角空格
        self.assertEqual(normalize_string(""), "")
        self.assertEqual(normalize_string(None), "")

class TestPlexService(unittest.TestCase):
    """测试 PlexService 类"""
    
    def setUp(self):
        """测试前的设置"""
        with patch('services.plex_service.PlexServer') as mock_plex_server:
            mock_server_instance = Mock()
            mock_plex_server.return_value = mock_server_instance
            self.plex_service = PlexService("http://test.com", "test_token")
            self.plex_service.server = mock_server_instance
            
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.plex_service)
        self.assertIsNotNone(self.plex_service.server)
        
    def test_find_newly_added_tracks_sync(self):
        """测试 _find_newly_added_tracks_sync 方法"""
        # 创建 MusicSection mock
        mock_library = Mock()
        
        # 创建 Track mocks
        mock_track1 = Mock()
        mock_track1.addedAt = datetime.now() - timedelta(hours=5)
        mock_track1.title = "Test Track 1"
        mock_track1.grandparentTitle = "Test Artist 1"
        
        mock_track2 = Mock()
        mock_track2.addedAt = datetime.now() - timedelta(days=2)
        mock_track2.title = "Test Track 2"
        mock_track2.grandparentTitle = "Test Artist 2"
        
        mock_track3 = Mock()
        mock_track3.addedAt = datetime.now() - timedelta(hours=1)
        mock_track3.title = "Test Track 3"
        mock_track3.grandparentTitle = "Test Artist 3"
        
        # 模拟 recentlyAddedTracks 方法返回
        mock_library.recentlyAddedTracks.return_value = [mock_track1, mock_track2, mock_track3]
        
        # 测试查找过去一天添加的音轨
        since_time = datetime.now() - timedelta(days=1)
        new_tracks = self.plex_service._find_newly_added_tracks_sync(mock_library, since_time)
        
        # 验证结果
        self.assertEqual(len(new_tracks), 2)  # 应该找到2个音轨 (track1 和 track3)
        self.assertIn(mock_track1, new_tracks)
        self.assertIn(mock_track3, new_tracks)
        self.assertNotIn(mock_track2, new_tracks)  # 这个音轨是2天前添加的，不应该包含在内
        
        # 验证 recentlyAddedTracks 方法被正确调用
        mock_library.recentlyAddedTracks.assert_called_once_with(maxresults=1000)
        
        # 重置 mock
        mock_library.recentlyAddedTracks.reset_mock()
        
        # 测试使用自定义 max_results 参数
        custom_max_results = 500
        new_tracks_custom = self.plex_service._find_newly_added_tracks_sync(mock_library, since_time, custom_max_results)
        
        # 验证 recentlyAddedTracks 方法被正确调用
        mock_library.recentlyAddedTracks.assert_called_once_with(maxresults=custom_max_results)
        
    def test_calculate_combined_score(self):
        """测试 _calculate_combined_score 方法"""
        # 测试权重计算
        score = self.plex_service._calculate_combined_score(100, 90, 80, (0.6, 0.25, 0.15))
        expected = 100 * 0.6 + 90 * 0.25 + 80 * 0.15
        self.assertEqual(score, expected)
        
        # 测试不同的权重
        score = self.plex_service._calculate_combined_score(100, 90, 80, (0.55, 0.3, 0.15))
        expected = 100 * 0.55 + 90 * 0.3 + 80 * 0.15
        self.assertEqual(score, expected)
        
    def test_create_or_update_playlist_sync_new_playlist(self):
        """测试 _create_or_update_playlist_sync 方法创建新播放列表"""
        # Mock playlist method to raise NotFound
        from plexapi.exceptions import NotFound
        self.plex_service.server.playlist.side_effect = NotFound("Playlist not found")
        
        # Mock createPlaylist method
        mock_playlist = Mock()
        mock_playlist.items.return_value = []
        self.plex_service.server.createPlaylist.return_value = mock_playlist
        
        # Create mock tracks
        mock_track1 = Mock()
        mock_track1.ratingKey = 1
        mock_track2 = Mock()
        mock_track2.ratingKey = 2
        tracks = [mock_track1, mock_track2]
        
        # Call the method
        result = self.plex_service._create_or_update_playlist_sync("Test Playlist", tracks)
        
        # Verify results
        self.assertTrue(result)
        self.plex_service.server.createPlaylist.assert_called_once_with("Test Playlist", items=tracks)
        
    def test_create_or_update_playlist_sync_update_playlist(self):
        """测试 _create_or_update_playlist_sync 方法更新现有播放列表"""
        # Create mock playlist
        mock_playlist = Mock()
        self.plex_service.server.playlist.return_value = mock_playlist
        
        # Create mock tracks for existing playlist
        mock_existing_track1 = Mock()
        mock_existing_track1.ratingKey = 1
        mock_existing_track2 = Mock()
        mock_existing_track2.ratingKey = 2
        mock_playlist.items.return_value = [mock_existing_track1, mock_existing_track2]
        
        # Create mock tracks for new playlist
        mock_new_track2 = Mock()
        mock_new_track2.ratingKey = 2
        mock_new_track3 = Mock()
        mock_new_track3.ratingKey = 3
        new_tracks = [mock_new_track2, mock_new_track3]
        
        # Call the method
        result = self.plex_service._create_or_update_playlist_sync("Test Playlist", new_tracks)
        
        # Verify results
        self.assertTrue(result)
        self.plex_service.server.playlist.assert_called_once_with("Test Playlist")
        
        # Verify removeItems was called with the correct tracks
        mock_playlist.removeItems.assert_called_once()
        removed_tracks = mock_playlist.removeItems.call_args[0][0]
        self.assertEqual(len(removed_tracks), 1)
        self.assertEqual(removed_tracks[0].ratingKey, 1)
        
        # Verify addItems was called with the correct tracks
        mock_playlist.addItems.assert_called_once()
        added_tracks = mock_playlist.addItems.call_args[0][0]
        self.assertEqual(len(added_tracks), 1)
        self.assertEqual(added_tracks[0].ratingKey, 3)
        
    def test_create_or_update_playlist_sync_empty_tracks(self):
        """测试 _create_or_update_playlist_sync 方法处理空曲目列表"""
        # Call the method with empty tracks
        result = self.plex_service._create_or_update_playlist_sync("Test Playlist", [])
        
        # Verify results
        self.assertTrue(result)

if __name__ == '__main__':
    unittest.main()