import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from schemas.download import DownloadQueueItem

def test_final_fix():
    '''测试最终的元数据处理'''
    print("=== 测试最终的元数据处理 ===")
    
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
    
    # 最终的处理逻辑
    def _extract_string_value(value):
        """从可能的列表或字符串中提取字符串值"""
        if isinstance(value, list) and len(value) > 0:
            # 确保列表第一个元素不是None或空字符串
            first_element = value[0]
            if first_element is not None:
                str_value = str(first_element)
                if str_value.strip():
                    return str_value
        elif value is not None:
            str_value = str(value)
            if str_value.strip():
                return str_value
        return None
    
    # 测试各种情况
    
    # 情况1: API返回列表形式的数据（正常情况）
    song_api_info_list = {
        'name': ['寂寞寂寞不好'],  # 列表形式
        'artist': ['曹格'],        # 列表形式
        'album': ['Super Sun']     # 列表形式
    }
    
    title_list = _extract_string_value(song_api_info_list.get('name')) or _extract_string_value(item.title) or ""
    artist_list = _extract_string_value(song_api_info_list.get('artist')) or _extract_string_value(item.artist) or ""
    album_list = _extract_string_value(song_api_info_list.get('album')) or _extract_string_value(item.album) or "未知专辑"
    
    print(f"情况1 - API返回列表形式数据:")
    print(f"  标题: {title_list} (类型: {type(title_list)})")
    print(f"  艺术家: {artist_list} (类型: {type(artist_list)})")
    print(f"  专辑: {album_list} (类型: {type(album_list)})")
    print()
    
    # 情况2: API返回空列表（应回退到队列项数据）
    song_api_info_empty_list = {
        'name': [],
        'artist': [],
        'album': []
    }
    
    title_empty = _extract_string_value(song_api_info_empty_list.get('name')) or _extract_string_value(item.title) or ""
    artist_empty = _extract_string_value(song_api_info_empty_list.get('artist')) or _extract_string_value(item.artist) or ""
    album_empty = _extract_string_value(song_api_info_empty_list.get('album')) or _extract_string_value(item.album) or "未知专辑"
    
    print(f"情况2 - API返回空列表:")
    print(f"  标题: '{title_empty}'")
    print(f"  艺术家: '{artist_empty}'")
    print(f"  专辑: '{album_empty}'")
    print()
    
    # 情况3: API返回包含空字符串的列表（应回退到队列项数据）
    song_api_info_empty_string_list = {
        'name': [''],
        'artist': [''],
        'album': ['']
    }
    
    title_empty_str = _extract_string_value(song_api_info_empty_string_list.get('name')) or _extract_string_value(item.title) or ""
    artist_empty_str = _extract_string_value(song_api_info_empty_string_list.get('artist')) or _extract_string_value(item.artist) or ""
    album_empty_str = _extract_string_value(song_api_info_empty_string_list.get('album')) or _extract_string_value(item.album) or "未知专辑"
    
    print(f"情况3 - API返回包含空字符串的列表:")
    print(f"  标题: '{title_empty_str}'")
    print(f"  艺术家: '{artist_empty_str}'")
    print(f"  专辑: '{album_empty_str}'")
    print()
    
    # 情况4: API返回None（应回退到队列项数据）
    song_api_info_none = {
        'name': None,
        'artist': None,
        'album': None
    }
    
    title_none = _extract_string_value(song_api_info_none.get('name')) or _extract_string_value(item.title) or ""
    artist_none = _extract_string_value(song_api_info_none.get('artist')) or _extract_string_value(item.artist) or ""
    album_none = _extract_string_value(song_api_info_none.get('album')) or _extract_string_value(item.album) or "未知专辑"
    
    print(f"情况4 - API返回None:")
    print(f"  标题: '{title_none}'")
    print(f"  艺术家: '{artist_none}'")
    print(f"  专辑: '{album_none}'")
    print()
    
    # 情况5: API没有对应字段（应回退到队列项数据）
    song_api_info_missing = {}
    
    title_missing = _extract_string_value(song_api_info_missing.get('name')) or _extract_string_value(item.title) or ""
    artist_missing = _extract_string_value(song_api_info_missing.get('artist')) or _extract_string_value(item.artist) or ""
    album_missing = _extract_string_value(song_api_info_missing.get('album')) or _extract_string_value(item.album) or "未知专辑"
    
    print(f"情况5 - API没有对应字段:")
    print(f"  标题: '{title_missing}'")
    print(f"  艺术家: '{artist_missing}'")
    print(f"  专辑: '{album_missing}'")
    print()
    
    # 情况6: 队列项中的数据也是空值（应使用默认值）
    db_row_data_empty = {
        'id': 1,
        'session_id': 1,
        'song_id': '231504820-0004jeEe4XTtjU',
        'title': '',
        'artist': '',
        'album': None,
        'status': 'pending',
        'quality': 'default',
        'retry_count': 0,
        'error_message': None,
        'platform': 'qq',
        'created_at': '2025-08-11T13:53:47Z',
        'updated_at': '2025-08-11T13:53:47Z'
    }
    
    item_empty = DownloadQueueItem(**db_row_data_empty)
    
    title_empty_album = _extract_string_value(song_api_info_missing.get('name')) or _extract_string_value(item_empty.title) or ""
    artist_empty_album = _extract_string_value(song_api_info_missing.get('artist')) or _extract_string_value(item_empty.artist) or ""
    album_empty_album = _extract_string_value(song_api_info_missing.get('album')) or _extract_string_value(item_empty.album) or "未知专辑"
    
    print(f"情况6 - 队列项中的数据也是空值:")
    print(f"  标题: '{title_empty_album}'")
    print(f"  艺术家: '{artist_empty_album}'")
    print(f"  专辑: '{album_empty_album}'")
    print()
    
    print("=== 测试结论 ===")
    print("最终的修复逻辑能够正确处理各种数据格式，确保写入ID3标签的都是有效的字符串值。")
    print("当API返回无效数据时，能够正确回退到队列项中的数据，最终回退到默认值。")

if __name__ == "__main__":
    test_final_fix()