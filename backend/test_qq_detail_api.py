import asyncio
import sys
import os
import logging

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.downloader_core import downloader

# 创建一个简单的logger
logging.basicConfig(level=logging.INFO)
test_logger = logging.getLogger("test_qq_detail")

async def test_qq_song_detail():
    '''测试QQ音乐歌曲详情获取功能'''
    print("=== 测试QQ音乐歌曲详情获取功能 ===")
    
    # 初始化下载器（使用假的API key，因为我们只测试信息补全功能）
    try:
        downloader.initialize("test_api_key", "./test_downloads")
    except:
        pass  # 忽略API key验证错误
    
    # 测试获取歌曲详情
    try:
        songmid = "000itqkA4Dqusv"  # 破碎的自己的songmid
        detail = await downloader._fetch_qq_song_detail(songmid, test_logger)
        
        if detail and isinstance(detail, dict):
            print(f"成功获取歌曲详情:")
            print(f"  歌曲名称: {detail.get('songname', 'N/A')}")
            
            album_info = detail.get('album')
            if isinstance(album_info, dict):
                print(f"  专辑名称: {album_info.get('name', 'N/A')}")
                print(f"  专辑MID: {album_info.get('mid', 'N/A')}")
            else:
                print(f"  专辑信息: {album_info}")
            
            singers = detail.get('singer', [])
            if singers:
                singer_names = [s.get('name', '未知歌手') for s in singers]
                print(f"  演唱者: {', '.join(singer_names)}")
            
            print(f"\n[成功] 成功获取并解析QQ音乐歌曲详情")
        else:
            print(f"[失败] 未能获取QQ音乐歌曲详情")
            
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_qq_song_detail())