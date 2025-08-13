import sys
import os
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.plex_service import PlexService

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_recently_added_tracks():
    """测试 recentlyAdded 方法的修复"""
    
    # 创建 PlexService 实例的 mock
    with patch('services.plex_service.PlexServer') as mock_plex_server:
        mock_server_instance = Mock()
        mock_plex_server.return_value = mock_server_instance
        plex_service = PlexService("http://test.com", "test_token")
        plex_service.server = mock_server_instance
        
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
        new_tracks = plex_service._find_newly_added_tracks_sync(mock_library, since_time)
        
        # 验证结果
        assert len(new_tracks) == 2  # 应该找到2个音轨 (track1 和 track3)
        assert mock_track1 in new_tracks
        assert mock_track3 in new_tracks
        assert mock_track2 not in new_tracks  # 这个音轨是2天前添加的，不应该包含在内
        
        # 验证 recentlyAddedTracks 方法被正确调用
        mock_library.recentlyAddedTracks.assert_called_once_with(maxresults=1000)
        
        # 重置 mock
        mock_library.recentlyAddedTracks.reset_mock()
        
        # 测试使用自定义 max_results 参数
        custom_max_results = 500
        new_tracks_custom = plex_service._find_newly_added_tracks_sync(mock_library, since_time, custom_max_results)
        
        # 验证 recentlyAddedTracks 方法被正确调用
        mock_library.recentlyAddedTracks.assert_called_once_with(maxresults=custom_max_results)
        
        logger.info("Recently added tracks test passed!")
        print("Recently added tracks test passed!")

if __name__ == "__main__":
    test_recently_added_tracks()