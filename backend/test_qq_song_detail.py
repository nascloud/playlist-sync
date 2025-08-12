import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import httpx
import json

async def test_qq_song_detail():
    '''测试通过歌曲ID获取详细信息'''
    print("=== 测试通过歌曲ID获取详细信息 ===")
    
    # 使用第一首歌曲的ID进行测试
    song_id = "563268487"
    song_mid = "000itqkA4Dqusv"
    
    # 构造获取歌曲详情的URL
    # 尝试几种可能的API端点
    urls_to_try = [
        f"https://u.y.qq.com/cgi-bin/musicu.fcg?data=%7B%22comm%22%3A%7B%22ct%22%3A24%2C%22cv%22%3A0%7D%2C%22songinfo%22%3A%7B%22method%22%3A%22get_song_detail_yqq%22%2C%22param%22%3A%7B%22song_type%22%3A0%2C%22song_mid%22%3A%22{song_mid}%22%7D%2C%22module%22%3A%22music.pf_song_detail_svr%22%7D%7D",
        f"https://c.y.qq.com/v8/fcg-bin/fcg_play_single_song.fcg?songmid={song_mid}&platform=yqq&format=json",
        f"https://c.y.qq.com/soso/fcgi-bin/client_search_cp?w={song_mid}&format=json"
    ]
    
    headers = {
        'Referer': 'https://y.qq.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    async with httpx.AsyncClient() as client:
        for i, url in enumerate(urls_to_try):
            try:
                print(f"\n尝试API端点 {i+1}: {url}")
                response = await client.get(url, headers=headers, timeout=10.0)
                response.raise_for_status()
                
                data = response.json()
                print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)[:500]}...")
                
                # 检查是否包含专辑信息
                if 'data' in data:
                    # 检查各种可能的数据结构
                    album_info = None
                    if isinstance(data['data'], dict):
                        if 'songinfo' in data['data']:
                            song_info = data['data']['songinfo']
                            if isinstance(song_info, dict) and 'data' in song_info:
                                track_info = song_info['data']
                                if isinstance(track_info, dict) and 'track_info' in track_info:
                                    track = track_info['track_info']
                                    if isinstance(track, dict) and 'album' in track:
                                        album_info = track['album']
                        elif 'album' in data['data']:
                            album_info = data['data']['album']
                    
                    if album_info:
                        print(f"找到专辑信息: {album_info}")
                        if isinstance(album_info, dict) and 'name' in album_info:
                            print(f"专辑名称: {album_info['name']}")
                        break
                    else:
                        print("未找到专辑信息")
                        
            except Exception as e:
                print(f"API端点 {i+1} 失败: {e}")
                continue
        else:
            print("所有API端点都失败了")

if __name__ == "__main__":
    asyncio.run(test_qq_song_detail())