import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.playlist_service import PlaylistService
from services.task_service import TaskService
from schemas.tasks import TaskCreate
import json

async def test_task_creation():
    '''测试任务创建和专辑信息传递'''
    print("=== 测试任务创建和专辑信息传递 ===")
    
    # 测试一个网易云歌单URL
    playlist_url = "https://music.163.com/#/playlist?id=123456789"  # 示例URL
    platform = "netease"
    
    try:
        print(f"解析歌单: {playlist_url}")
        playlist_data = await PlaylistService.parse_playlist(playlist_url, platform)
        
        print(f"歌单标题: {playlist_data['title']}")
        print(f"歌曲数量: {len(playlist_data['tracks'])}")
        
        # 检查前几首歌曲的专辑信息
        print("\n前3首歌曲信息:")
        for i, track in enumerate(playlist_data['tracks'][:3]):
            print(f"{i+1}. 标题: {track['title']}")
            print(f"   艺术家: {track['artist']}")
            print(f"   专辑: {track.get('album', 'N/A')}")
            print(f"   歌曲ID: {track.get('song_id', 'N/A')}")
            print()
            
        # 创建任务
        task_create = TaskCreate(
            name=f"测试任务 - {playlist_data['title']}",
            playlist_url=playlist_url,
            platform=platform,
            cron_schedule="0 2 * * *",
            server_id=1
        )
        
        # 注意：这里我们不会实际创建任务，只是模拟流程
        print("模拟任务创建过程...")
        
        # 模拟同步任务中的 unmatched_songs 存储
        unmatched_songs = []
        for track in playlist_data['tracks'][:5]:  # 只取前5首用于测试
            unmatched_songs.append({
                'title': track['title'],
                'artist': track['artist'],
                'album': track.get('album'),
                'song_id': track.get('song_id'),
                'platform': track.get('platform')
            })
            
        print(f"模拟存储到任务中的未匹配歌曲数量: {len(unmatched_songs)}")
        
        # 检查专辑信息是否完整保存
        missing_album_in_task = 0
        for song in unmatched_songs:
            if not song.get('album'):
                missing_album_in_task += 1
                
        print(f"在任务中缺失专辑信息的歌曲数量: {missing_album_in_task}/{len(unmatched_songs)}")
        
        # 模拟下载队列创建过程
        print("\n模拟下载队列创建过程...")
        from schemas.download import DownloadQueueItemCreate
        
        download_items = [
            DownloadQueueItemCreate(
                title=song['title'], 
                artist=song['artist'],
                album=song.get('album'),
                song_id=song.get('song_id'),
                platform=song.get('platform')
            ) for song in unmatched_songs
        ]
        
        print(f"创建的下载项数量: {len(download_items)}")
        
        # 检查下载项中的专辑信息
        missing_album_in_queue = 0
        for item in download_items:
            if not item.album:
                missing_album_in_queue += 1
                
        print(f"在下载队列中缺失专辑信息的项数量: {missing_album_in_queue}/{len(download_items)}")
        
        print("\n=== 分析结果 ===")
        if missing_album_in_task == 0 and missing_album_in_queue == 0:
            print("✓ 专辑信息在整个流程中都得到了正确传递")
        else:
            print("✗ 专辑信息在某个环节丢失了")
            print(f"  - 任务创建阶段丢失: {missing_album_in_task}")
            print(f"  - 下载队列阶段丢失: {missing_album_in_queue}")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_task_creation())