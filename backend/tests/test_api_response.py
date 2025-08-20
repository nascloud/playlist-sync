import asyncio
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from services.download.downloader_core import MusicDownloader

async def test_api_response():
    '''测试API响应格式'''
    print("=== 测试API响应格式 ===")
    
    # 使用一个示例API Key进行测试
    api_key = "test_key"  # 示例Key
    downloader = MusicDownloader(api_key=api_key)
    
    # 使用一个示例歌曲ID进行测试
    music_id = "003OUlho2HcRHe"  # 示例QQ音乐歌曲ID
    music_type = "qq"
    
    try:
        print(f"获取歌曲信息: ID={music_id}, 类型={music_type}")
        # 这里我们不会实际调用API，只是分析数据结构
        print("注意：实际API调用需要有效的API Key")
        
    except Exception as e:
        print(f"测试过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_api_response())