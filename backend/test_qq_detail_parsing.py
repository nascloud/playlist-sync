import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import httpx
import json

async def test_qq_song_detail_parsing():
    '''测试解析QQ音乐歌曲详情API返回的数据'''
    print("=== 测试解析QQ音乐歌曲详情API返回的数据 ===")
    
    # 模拟从歌曲详情API获取的数据
    mock_response = {
        "code": 0,
        "data": [
            {
                "album": {
                    "id": 63224264,
                    "mid": "004eFADW2FLZ5N",
                    "name": "破碎的自己",
                    "pmid": "004eFADW2FLZ5N_1",
                    "subtitle": "",
                    "time_public": "2025-02-21",
                    "title": "破碎的自己"
                },
                "singer": [
                    {"id": 2868522, "mid": "003ViYoy2bJYmk", "name": "LBI利比（时柏尘）"},
                    {"id": 2094464, "mid": "0046bKHQ1EXZTU", "name": "前男友"}
                ],
                "songmid": "000itqkA4Dqusv",
                "songname": "破碎的自己"
            }
        ]
    }
    
    if mock_response.get('code') == 0 and mock_response.get('data'):
        song_data = mock_response['data'][0] if isinstance(mock_response['data'], list) else mock_response['data']
        
        # 提取歌曲信息
        title = song_data.get('songname', '未知歌名')
        singers = ', '.join([s.get('name', '未知歌手') for s in song_data.get('singer', [])])
        
        # 从歌曲详情中提取专辑信息
        album_info = song_data.get('album')
        if isinstance(album_info, dict):
            album = album_info.get('name', '未知专辑')
        else:
            album = '未知专辑'
            
        print(f"解析结果:")
        print(f"  标题: {title}")
        print(f"  艺术家: {singers}")
        print(f"  专辑: {album}")
        print(f"  歌曲MID: {song_data.get('songmid', 'N/A')}")
        
        # 检查是否能正确获取专辑信息
        if album != '未知专辑':
            print(f"\n[OK] 成功获取专辑信息: {album}")
        else:
            print(f"\n[FAIL] 未能获取专辑信息")
            
    else:
        print("API响应无效")

if __name__ == "__main__":
    asyncio.run(test_qq_song_detail_parsing())