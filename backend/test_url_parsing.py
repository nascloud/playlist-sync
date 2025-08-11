import re
from enum import Enum

class Platform(Enum):
    NETEASE = "netease"
    QQ = "qq"

def extract_playlist_id(url: str, platform: Platform) -> str:
    """
    从URL或ID中提取歌单ID
    :param url: 歌单URL或ID
    :param platform: 平台类型
    :return: 提取的歌单ID
    """
    if platform == Platform.NETEASE:
        # 匹配 id=数字 的模式
        match = re.search(r'id=(\d+)', url)
        if match:
            return match.group(1)
        
        # 如果输入是纯数字ID
        if url.isdigit():
            return url
            
    elif platform == Platform.QQ:
        # 匹配多种QQ音乐歌单URL格式
        # 例如: https://y.qq.com/n/ryqq/playlist/9295849532
        # 或包含 disstid=... 或 id=... 的URL
        patterns = [
            r'playlist/(\d+)',
            r'disstid=(\d+)',
            r'id=(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # 如果输入是纯数字ID
        if url.isdigit():
            return url
    
    return None

# 测试用例
test_urls = [
    ("https://y.qq.com/n/ryqq/playlist/9295849532", Platform.QQ),
    ("https://music.163.com/#/playlist?id=9295849532", Platform.NETEASE),
    ("9295849532", Platform.QQ),
    ("9295849532", Platform.NETEASE),
]

for url, platform in test_urls:
    result = extract_playlist_id(url, platform)
    print(f"URL: {url}, Platform: {platform.value}, Extracted ID: {result}")