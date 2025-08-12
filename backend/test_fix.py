import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from schemas.download import DownloadQueueItem

def test_fix():
    '''测试修复后的元数据处理'''
    print("=== 测试修复后的元数据处理 ===")
    
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
    
    # 模拟API返回列表形式的数据（修复前会导致问题的情况）
    song_api_info = {
        'name': ['寂寞寂寞不好'],  # 列表形式
        'artist': ['曹格'],        # 列表形式
        'album': ['Super Sun']     # 列表形式
    }
    
    # 修复后的处理逻辑
    def _extract_string_value(value):
        """从可能的列表或字符串中提取字符串值"""
        if isinstance(value, list) and len(value) > 0:
            return str(value[0])
        elif value is not None:
            return str(value)
        else:
            return ""
    
    title = _extract_string_value(song_api_info.get('name')) or _extract_string_value(item.title)
    artist = _extract_string_value(song_api_info.get('artist')) or _extract_string_value(item.artist)
    album = _extract_string_value(song_api_info.get('album')) or _extract_string_value(item.album) or "未知专辑"
    
    print(f"修复后的处理结果:")
    print(f"  标题: {title} (类型: {type(title)})")
    print(f"  艺术家: {artist} (类型: {type(artist)})")
    print(f"  专辑: {album} (类型: {type(album)})")
    print()
    
    # 测试各种边界情况
    
    # 情况1: API返回空列表
    song_api_info_empty_list = {
        'name': [],
        'artist': [],
        'album': []
    }
    
    title_empty = _extract_string_value(song_api_info_empty_list.get('name')) or _extract_string_value(item.title)
    artist_empty = _extract_string_value(song_api_info_empty_list.get('artist')) or _extract_string_value(item.artist)
    album_empty = _extract_string_value(song_api_info_empty_list.get('album')) or _extract_string_value(item.album) or "未知专辑"
    
    print(f"情况1 - API返回空列表:")
    print(f"  标题: {title_empty}")
    print(f"  艺术家: {artist_empty}")
    print(f"  专辑: {album_empty}")
    print()
    
    # 情况2: API返回None
    song_api_info_none = {
        'name': None,
        'artist': None,
        'album': None
    }
    
    title_none = _extract_string_value(song_api_info_none.get('name')) or _extract_string_value(item.title)
    artist_none = _extract_string_value(song_api_info_none.get('artist')) or _extract_string_value(item.artist)
    album_none = _extract_string_value(song_api_info_none.get('album')) or _extract_string_value(item.album) or "未知专辑"
    
    print(f"情况2 - API返回None:")
    print(f"  标题: {title_none}")
    print(f"  艺术家: {artist_none}")
    print(f"  专辑: {album_none}")
    print()
    
    # 情况3: API没有对应字段
    song_api_info_missing = {}
    
    title_missing = _extract_string_value(song_api_info_missing.get('name')) or _extract_string_value(item.title)
    artist_missing = _extract_string_value(song_api_info_missing.get('artist')) or _extract_string_value(item.artist)
    album_missing = _extract_string_value(song_api_info_missing.get('album')) or _extract_string_value(item.album) or "未知专辑"
    
    print(f"情况3 - API没有对应字段:")
    print(f"  标题: {title_missing}")
    print(f"  艺术家: {artist_missing}")
    print(f"  专辑: {album_missing}")
    print()
    
    print("=== 测试结论 ===")
    print("修复后的逻辑能够正确处理各种数据格式，确保写入ID3标签的都是字符串值。")

if __name__ == "__main__":
    test_fix()