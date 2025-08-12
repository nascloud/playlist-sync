import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from schemas.download import DownloadQueueItem

def test_api_data_structure():
    '''测试API数据结构对元数据处理的影响'''
    print("=== 测试API数据结构对元数据处理的影响 ===")
    
    # 模拟下载队列项
    db_row_data = {
        'id': 1,
        'session_id': 1,
        'song_id': '231504820-0004jeEe4XTtjU',
        'title': '寂寞寂寞不好',
        'artist': '曹格',
        'album': 'Super Sun',
        'status': 'pending',
        'quality': 'default',
        'retry_count': 0,
        'error_message': None,
        'platform': 'qq',
        'created_at': '2025-08-11T13:53:47Z',
        'updated_at': '2025-08-11T13:53:47Z'
    }
    
    item = DownloadQueueItem(**db_row_data)
    
    print(f"下载队列项信息:")
    print(f"  标题: {item.title} (类型: {type(item.title)})")
    print(f"  艺术家: {item.artist} (类型: {type(item.artist)})")
    print(f"  专辑: {item.album} (类型: {type(item.album)})")
    print()
    
    # 模拟几种可能的API返回数据结构
    
    # 情况1: API正常返回字符串
    song_api_info_1 = {
        'name': '寂寞寂寞不好',
        'artist': '曹格',
        'album': 'Super Sun'
    }
    
    title_1 = song_api_info_1.get('name', item.title)
    artist_1 = song_api_info_1.get('artist', item.artist)
    album_1 = song_api_info_1.get('album', item.album) or "未知专辑"
    
    print(f"情况1 - API正常返回字符串:")
    print(f"  标题: {title_1} (类型: {type(title_1)})")
    print(f"  艺术家: {artist_1} (类型: {type(artist_1)})")
    print(f"  专辑: {album_1} (类型: {type(album_1)})")
    print()
    
    # 情况2: API返回列表形式的数据
    song_api_info_2 = {
        'name': ['寂寞寂寞不好'],  # 列表形式
        'artist': ['曹格'],        # 列表形式
        'album': ['Super Sun']     # 列表形式
    }
    
    title_2 = song_api_info_2.get('name', item.title)
    artist_2 = song_api_info_2.get('artist', item.artist)
    album_2 = song_api_info_2.get('album', item.album) or "未知专辑"
    
    print(f"情况2 - API返回列表形式数据:")
    print(f"  标题: {title_2} (类型: {type(title_2)})")
    print(f"  艺术家: {artist_2} (类型: {type(artist_2)})")
    print(f"  专辑: {album_2} (类型: {type(album_2)})")
    print()
    
    # 情况3: API没有返回专辑信息
    song_api_info_3 = {
        'name': '寂寞寂寞不好',
        'artist': '曹格'
        # 没有 album 字段
    }
    
    title_3 = song_api_info_3.get('name', item.title)
    artist_3 = song_api_info_3.get('artist', item.artist)
    album_3 = song_api_info_3.get('album', item.album) or "未知专辑"
    
    print(f"情况3 - API没有返回专辑信息:")
    print(f"  标题: {title_3} (类型: {type(title_3)})")
    print(f"  艺术家: {artist_3} (类型: {type(artist_3)})")
    print(f"  专辑: {album_3} (类型: {type(album_3)})")
    print()
    
    # 情况4: 队列项中的专辑信息本身就是 None
    db_row_data_no_album = db_row_data.copy()
    db_row_data_no_album['album'] = None
    item_no_album = DownloadQueueItem(**db_row_data_no_album)
    
    title_4 = song_api_info_3.get('name', item_no_album.title)
    artist_4 = song_api_info_3.get('artist', item_no_album.artist)
    album_4 = song_api_info_3.get('album', item_no_album.album) or "未知专辑"
    
    print(f"情况4 - 队列项中专辑信息为 None:")
    print(f"  标题: {title_4} (类型: {type(title_4)})")
    print(f"  艺术家: {artist_4} (类型: {type(artist_4)})")
    print(f"  专辑: {album_4} (类型: {type(album_4)})")
    print()
    
    print("=== 分析结果 ===")
    print("从模拟结果看，如果API返回的是列表形式数据，会导致最终写入ID3标签的值也是列表形式。")
    print("这与日志中看到的现象一致：Title='['寂寞寂寞不好']', Artist='['曹格']', Album='['未知专辑']'")

if __name__ == "__main__":
    test_api_data_structure()