import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.playlist_service import PlaylistService

async def test_qq_playlist():
    '''测试QQ音乐歌单解析'''
    print("=== 测试QQ音乐歌单解析 ===")
    
    # 使用提供的QQ音乐歌单URL
    playlist_url = "https://y.qq.com/n/ryqq/playlist/9295849532"
    platform = "qq"
    
    try:
        print(f"解析歌单: {playlist_url}")
        playlist_data = await PlaylistService.parse_playlist(playlist_url, platform)
        
        print(f"歌单标题: {playlist_data['title']}")
        print(f"歌曲数量: {len(playlist_data['tracks'])}")
        
        # 检查前3首歌曲的专辑信息
        print("\n前3首歌曲信息:")
        for i, track in enumerate(playlist_data['tracks'][:3]):
            print(f"{i+1}. 标题: {track['title']}")
            print(f"   艺术家: {track['artist']}")
            print(f"   专辑: {track.get('album', 'N/A')}")
            print(f"   歌曲ID: {track.get('song_id', 'N/A')}")
            print(f"   平台: {track.get('platform', 'N/A')}")
            print()
            
        # 检查是否有缺失专辑信息的歌曲
        missing_album_count = 0
        for track in playlist_data['tracks'][:3]:
            if not track.get('album') or track.get('album') == '未知专辑':
                missing_album_count += 1
                
        print(f"前3首歌曲中缺失专辑信息的数量: {missing_album_count}/3")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_qq_playlist())