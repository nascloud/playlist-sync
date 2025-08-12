import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from schemas.download import DownloadQueueItem

def test_song_info_parsing():
    '''测试歌曲信息解析'''
    print("=== 测试歌曲信息解析 ===")
    
    # 模拟下载队列项
    db_row_data = {
        'id': 1,
        'session_id': 1,
        'song_id': '231504820-0004jeEe4XTtjU',
        'title': '寂寞寂寞不好',
        'artist': '曹格',
        'album': 'Super Sun',  # 假设从队列中获取的专辑信息
        'status': 'pending',
        'quality': 'default',
        'retry_count': 0,
        'error_message': None,
        'platform': 'qq',
        'created_at': '2025-08-11T13:53:47Z',
        'updated_at': '2025-08-11T13:53:47Z'
    }
    
    item = DownloadQueueItem(**db_row_data)
    
    # 模拟几种可能的API返回数据结构
    
    # 情况1: API返回info字段包含name和artist，但不包含album
    music_info_1 = {
        'info': {
            'name': '寂寞寂寞不好',
            'artist': '曹格'
            # 没有album字段
        },
        'gm': '寂寞寂寞不好',
        'gs': '曹格'
    }
    
    song_info_details_1 = music_info_1.get('info', {})
    song_name_1 = music_info_1.get('gm') or song_info_details_1.get('name', item.title)
    singer_1 = music_info_1.get('gs') or song_info_details_1.get('artist', item.artist)
    
    print(f"情况1 - API返回info字段但不包含album:")
    print(f"  歌曲名称: {song_name_1}")
    print(f"  艺术家: {singer_1}")
    print(f"  info中的album: {song_info_details_1.get('album', 'N/A')}")
    print()
    
    # 情况2: API返回info字段包含完整的歌曲信息
    music_info_2 = {
        'info': {
            'name': '寂寞寂寞不好',
            'artist': '曹格',
            'album': 'Super Sun'
        },
        'gm': '寂寞寂寞不好',
        'gs': '曹格'
    }
    
    song_info_details_2 = music_info_2.get('info', {})
    song_name_2 = music_info_2.get('gm') or song_info_details_2.get('name', item.title)
    singer_2 = music_info_2.get('gs') or song_info_details_2.get('artist', item.artist)
    
    print(f"情况2 - API返回info字段包含完整信息:")
    print(f"  歌曲名称: {song_name_2}")
    print(f"  艺术家: {singer_2}")
    print(f"  专辑: {song_info_details_2.get('album', 'N/A')}")
    print()
    
    # 情况3: API返回info字段为空或None
    music_info_3 = {
        'info': None,
        'gm': '寂寞寂寞不好',
        'gs': '曹格'
    }
    
    song_info_details_3 = music_info_3.get('info', {})
    song_name_3 = music_info_3.get('gm') or song_info_details_3.get('name', item.title)
    singer_3 = music_info_3.get('gs') or song_info_details_3.get('artist', item.artist)
    
    print(f"情况3 - API返回info字段为None:")
    print(f"  歌曲名称: {song_name_3}")
    print(f"  艺术家: {singer_3}")
    print(f"  info类型: {type(song_info_details_3)}")
    print()
    
    print("=== 结论 ===")
    print("如果API返回的info字段中不包含album信息，那么在_embed_id3_tags方法中")
    print("song_api_info.get('album')就会返回None，然后会使用item.album作为回退。")

if __name__ == "__main__":
    test_song_info_parsing()