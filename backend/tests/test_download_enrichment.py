import asyncio
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.download.downloader_core import downloader

# 创建一个简单的logger
logging.basicConfig(level=logging.INFO)
test_logger = logging.getLogger("test_enrichment")

# 创建一个模拟的DownloadQueueItem类

class MockDownloadQueueItem:
    def __init__(self, title, artist, album, platform, song_id):
        self.id = 1  # 添加id属性
        self.session_id = 1  # 添加session_id属性
        self.title = title
        self.artist = artist
        self.album = album
        self.platform = platform
        self.song_id = song_id
        self.status = "pending"
        self.quality = "无损"
        self.retry_count = 0
        self.error_message = None
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

async def test_qq_info_enrichment():
    '''测试在下载阶段补全QQ音乐歌曲信息'''
    print("=== 测试在下载阶段补全QQ音乐歌曲信息 ===")
    
    # 模拟一个缺少专辑信息的QQ音乐歌曲
    item = MockDownloadQueueItem(
        title="破碎的自己",
        artist="LBI利比（时柏尘）, 前男友",
        album="未知专辑",  # 缺少专辑信息
        platform="qq",
        song_id="563268487-000itqkA4Dqusv"  # 包含songmid
    )
    
    print(f"原始歌曲信息:")
    print(f"  标题: {item.title}")
    print(f"  艺术家: {item.artist}")
    print(f"  专辑: {item.album}")
    print(f"  平台: {item.platform}")
    print(f"  歌曲ID: {item.song_id}")
    
    # 初始化下载器（使用假的API key，因为我们只测试信息补全功能）
    try:
        downloader.initialize("test_api_key", "./test_downloads")
    except:
        pass  # 忽略API key验证错误
    
    # 测试信息补全功能
    try:
        enriched_item = await downloader._enrich_track_info(item, test_logger)
        print(f"\n补全后的歌曲信息:")
        print(f"  标题: {enriched_item.title}")
        print(f"  艺术家: {enriched_item.artist}")
        print(f"  专辑: {getattr(enriched_item, 'album', 'N/A')}")
        print(f"  平台: {getattr(enriched_item, 'platform', 'N/A')}")
        print(f"  歌曲ID: {getattr(enriched_item, 'song_id', 'N/A')}")
        
        # 检查是否补全了专辑信息
        original_album = item.album
        enriched_album = getattr(enriched_item, 'album', 'N/A')
        
        if enriched_album != original_album and enriched_album != 'N/A':
            print(f"\n[成功] 专辑信息已从 '{original_album}' 补全为 '{enriched_album}'")
        else:
            print(f"\n[信息] 专辑信息未发生变化")
            
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_qq_info_enrichment())