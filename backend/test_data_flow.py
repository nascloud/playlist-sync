import asyncio
import sys
import os
import json

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from schemas.download import DownloadQueueItemCreate, DownloadQueueItem

def test_data_flow():
    '''测试数据流中专辑信息的传递'''
    print("=== 测试数据流中专辑信息的传递 ===")
    
    # 模拟从播放列表解析得到的歌曲信息
    playlist_track = {
        'title': '测试歌曲',
        'artist': '测试艺术家',
        'album': '测试专辑',
        'song_id': '12345',
        'platform': 'netease'
    }
    
    print(f"1. 播放列表解析得到的歌曲信息:")
    print(f"   标题: {playlist_track['title']}")
    print(f"   艺术家: {playlist_track['artist']}")
    print(f"   专辑: {playlist_track['album']}")
    print(f"   歌曲ID: {playlist_track['song_id']}")
    print()
    
    # 模拟创建下载队列项
    download_item_create = DownloadQueueItemCreate(
        title=playlist_track['title'],
        artist=playlist_track['artist'],
        album=playlist_track['album'],
        song_id=playlist_track['song_id'],
        platform=playlist_track['platform']
    )
    
    print(f"2. 创建的 DownloadQueueItemCreate 对象:")
    print(f"   标题: {download_item_create.title}")
    print(f"   艺术家: {download_item_create.artist}")
    print(f"   专辑: {download_item_create.album}")
    print(f"   歌曲ID: {download_item_create.song_id}")
    print()
    
    # 模拟存储到数据库后的数据（JSON格式）
    db_json_data = {
        'title': download_item_create.title,
        'artist': download_item_create.artist,
        'album': download_item_create.album,
        'song_id': download_item_create.song_id,
        'platform': download_item_create.platform
    }
    
    json_str = json.dumps(db_json_data, ensure_ascii=False)
    print(f"3. 存储到数据库的JSON数据:")
    print(f"   {json_str}")
    print()
    
    # 模拟从数据库读取数据
    parsed_data = json.loads(json_str)
    print(f"4. 从数据库读取并解析的数据:")
    print(f"   标题: {parsed_data['title']}")
    print(f"   艺术家: {parsed_data['artist']}")
    print(f"   专辑: {parsed_data['album']}")
    print(f"   歌曲ID: {parsed_data['song_id']}")
    print()
    
    # 模拟创建下载队列项对象
    # 注意：这里我们模拟数据库行数据
    db_row_data = {
        'id': 1,
        'session_id': 1,
        'song_id': parsed_data['song_id'],
        'title': parsed_data['title'],
        'artist': parsed_data['artist'],
        'album': parsed_data['album'],
        'status': 'pending',
        'quality': 'default',
        'retry_count': 0,
        'error_message': None,
        'platform': parsed_data['platform'],
        'created_at': '2025-08-11T13:53:47Z',
        'updated_at': '2025-08-11T13:53:47Z'
    }
    
    download_item = DownloadQueueItem(**db_row_data)
    
    print(f"5. 创建的 DownloadQueueItem 对象:")
    print(f"   ID: {download_item.id}")
    print(f"   标题: {download_item.title}")
    print(f"   艺术家: {download_item.artist}")
    print(f"   专辑: {download_item.album}")
    print(f"   歌曲ID: {download_item.song_id}")
    print()
    
    # 模拟 API 返回的歌曲信息
    song_api_info = {
        'name': 'API返回的歌曲名',
        'artist': 'API返回的艺术家',
        'album': 'API返回的专辑',
        'pic': 'http://example.com/cover.jpg'
    }
    
    print(f"6. API返回的歌曲信息:")
    print(f"   标题: {song_api_info['name']}")
    print(f"   艺术家: {song_api_info['artist']}")
    print(f"   专辑: {song_api_info['album']}")
    print(f"   封面: {song_api_info['pic']}")
    print()
    
    # 模拟 _embed_id3_tags 方法中的专辑信息获取逻辑
    title = song_api_info.get('name', download_item.title)
    artist = song_api_info.get('artist', download_item.artist)
    album = song_api_info.get('album', download_item.album) or "未知专辑"
    
    print(f"7. _embed_id3_tags 方法中的信息获取逻辑:")
    print(f"   标题: {title} (来自API: {song_api_info.get('name') is not None})")
    print(f"   艺术家: {artist} (来自API: {song_api_info.get('artist') is not None})")
    print(f"   专辑: {album} (来自API: {song_api_info.get('album') is not None})")
    print()
    
    # 模拟当API没有返回专辑信息时的情况
    song_api_info_no_album = {
        'name': 'API返回的歌曲名',
        'artist': 'API返回的艺术家',
        # 注意：这里没有 album 字段
        'pic': 'http://example.com/cover.jpg'
    }
    
    title_no_album = song_api_info_no_album.get('name', download_item.title)
    artist_no_album = song_api_info_no_album.get('artist', download_item.artist)
    album_no_album = song_api_info_no_album.get('album', download_item.album) or "未知专辑"
    
    print(f"8. 当API没有返回专辑信息时的处理:")
    print(f"   标题: {title_no_album} (来自API: {song_api_info_no_album.get('name') is not None})")
    print(f"   艺术家: {artist_no_album} (来自API: {song_api_info_no_album.get('artist') is not None})")
    print(f"   专辑: {album_no_album} (来自API: {song_api_info_no_album.get('album') is not None}, 来自队列项: {download_item.album is not None})")
    print()
    
    print("=== 测试结论 ===")
    print("从数据流分析来看，专辑信息在整个流程中应该是正确传递的。")
    print("如果实际下载中出现专辑信息丢失，可能的原因:")
    print("1. API返回的歌曲信息中确实没有专辑字段")
    print("2. 数据库中的专辑信息在存储时就已经是空值")
    print("3. 某些特殊字符导致JSON序列化/反序列化出现问题")

if __name__ == "__main__":
    test_data_flow()