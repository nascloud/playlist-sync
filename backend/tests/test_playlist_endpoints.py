import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import sys
import os


from main import app  # 假设FastAPI应用实例在main.py中

# 使用TestClient包装FastAPI应用
client = TestClient(app)

class TestPlaylistEndpoints:
    """播放列表端点测试类"""
    
    @patch('services.playlist_service.PlaylistService.parse_playlist', new_callable=AsyncMock)
    def test_parse_playlist_success(self, mock_parse_playlist):
        """测试成功解析播放列表"""
        # 模拟服务返回值
        mock_parse_playlist.return_value = {
            "title": "Test Playlist",
            "tracks": [{"title": "Song 1", "artist": "Artist 1"}]
        }
        
        # 发送请求
        response = client.post(
            "/api/playlists/parse",
            json={"url": "http://music.163.com/playlist?id=123456789", "platform": "netease"}
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["title"] == "Test Playlist"
        assert len(data["tracks"]) == 1
        
    @patch('services.playlist_service.PlaylistService.parse_playlist', new_callable=AsyncMock)
    def test_parse_playlist_failure(self, mock_parse_playlist):
        """测试解析播放列表失败"""
        # 模拟服务抛出异常
        mock_parse_playlist.side_effect = Exception("解析失败")
        
        # 发送请求
        response = client.post(
            "/api/playlists/parse",
            json={"url": "http://music.163.com/playlist?id=123456789", "platform": "netease"}
        )
        
        # 验证响应
        assert response.status_code == 500
        assert "解析歌单失败" in response.json()["detail"]
        
    def test_parse_playlist_bad_request(self):
        """测试解析播放列表时的无效请求"""
        # 发送缺少参数的请求
        response = client.post("/api/playlists/parse", json={"url": "http://music.163.com/playlist?id=123456789"})
        
        # 验证响应
        assert response.status_code == 422
        
    @patch('services.task_service.TaskService.create_task')
    def test_import_playlist_success(self, mock_create_task):
        """测试成功导入播放列表任务"""
        # 模拟服务返回值
        mock_create_task.return_value = 1  # 返回任务ID
        
        # 发送请求
        response = client.post(
            "/api/playlists/import",
            json={
                "playlistTitle": "My Playlist",
                "sourceUrl": "http://music.163.com/playlist?id=123456789",
                "sourcePlatform": "netease",
                "syncSchedule": "daily"
            }
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "任务已成功创建。"
        assert data["taskId"] == 1
        
    def test_import_playlist_bad_request(self):
        """测试导入播放列表时的无效请求"""
        # 发送缺少参数的请求
        response = client.post(
            "/api/playlists/import",
            json={"playlistTitle": "My Playlist"}
        )
        
        # 验证响应
        assert response.status_code == 422