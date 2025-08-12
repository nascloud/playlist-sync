import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import httpx
import re
import json

async def test_qq_api_response():
    '''测试QQ音乐API响应数据结构'''
    print("=== 测试QQ音乐API响应数据结构 ===")
    
    # 使用提供的QQ音乐歌单ID
    playlist_id = "9295849532"
    
    url = "https://c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg"
    params = {
        'type': '1', 'json': '1', 'utf8': '1', 'onlysong': '0', 
        'disstid': playlist_id, 'format': 'json', 'platform': 'yqq.json'
    }
    headers = {
        'Referer': 'https://y.qq.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    async with httpx.AsyncClient() as client:
        try:
            print(f"请求QQ音乐歌单数据: {url}")
            response = await client.get(url, headers=headers, params=params, timeout=10.0)
            response.raise_for_status()
            
            # 处理响应文本
            cleaned_text = response.text.strip()
            if cleaned_text.startswith('callback('):
                cleaned_text = cleaned_text[len('callback('):-1]
            elif cleaned_text.startswith('jsonpCallback('):
                cleaned_text = cleaned_text[len('jsonpCallback('):-1]
            
            data = json.loads(cleaned_text)
            
            if not data or not data.get('cdlist') or len(data['cdlist']) == 0:
                print("无法获取QQ音乐歌单数据")
                return
                
            playlist = data['cdlist'][0]
            playlist_title = playlist.get('dissname', '未知歌单')
            print(f"歌单标题: {playlist_title}")
            
            if playlist.get('songlist'):
                print(f"\n前3首歌曲的原始数据结构:")
                for i, song in enumerate(playlist['songlist'][:3]):
                    print(f"\n歌曲 {i+1}:")
                    print(f"  songname: {song.get('songname', 'N/A')}")
                    print(f"  singer: {song.get('singer', 'N/A')}")
                    print(f"  album: {song.get('album', 'N/A')}")
                    print(f"  album类型: {type(song.get('album'))}")
                    if isinstance(song.get('album'), dict):
                        print(f"  album[name]: {song['album'].get('name', 'N/A')}")
                    print(f"  songid: {song.get('songid', 'N/A')}")
                    print(f"  songmid: {song.get('songmid', 'N/A')}")
            
        except Exception as e:
            print(f"测试过程中出错: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_qq_api_response())