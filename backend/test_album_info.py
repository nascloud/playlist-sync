import asyncio
import logging
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.playlist_service import PlaylistService
from services.download_service import DownloadService
from services.settings_service import SettingsService
from core.database import init_db

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

async def test_album_info():
    """测试专辑信息传递"""
    print("=== 测试专辑信息传递 ===")
    
    # 初始化数据库
    init_db()
    
    # 创建服务实例
    settings_service = SettingsService()
    download_service = DownloadService(settings_service)
    
    # 测试一个网易云歌单URL（示例）
    # 请替换为实际的歌单URL进行测试
    playlist_url = "https://music.163.com/#/playlist?id=123456789"  # 示例URL
    platform = "netease"
    
    try:
        print(f"解析歌单: {playlist_url}")
        playlist_data = await PlaylistService.parse_playlist(playlist_url, platform)
        
        print(f"歌单标题: {playlist_data['title']}")
        print(f"歌曲数量: {len(playlist_data['tracks'])}")
        
        # 检查前几首歌曲的专辑信息
        print("\n前5首歌曲信息:")
        for i, track in enumerate(playlist_data['tracks'][:5]):
            print(f"{i+1}. 标题: {track['title']}")
            print(f"   艺术家: {track['artist']}")
            print(f"   专辑: {track.get('album', 'N/A')}")
            print(f"   歌曲ID: {track.get('song_id', 'N/A')}")
            print(f"   平台: {track.get('platform', 'N/A')}")
            print()
            
        # 检查是否有缺失专辑信息的歌曲
        missing_album_count = 0
        for track in playlist_data['tracks']:
            if not track.get('album'):
                missing_album_count += 1
                
        print(f"缺失专辑信息的歌曲数量: {missing_album_count}/{len(playlist_data['tracks'])}")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_album_info())