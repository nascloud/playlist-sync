"""下载服务相关常量配置"""

# 平台映射配置
PLATFORM_MAPPING = {
    "netease": "wy",
    "qqmusic": "qq",
}

# 平台搜索顺序
PLATFORM_SEARCH_ORDER = ['qq', 'wy', 'kg', 'kw', 'mg']

# 音质优先级排序
QUALITY_ORDER = ['无损', '高品', '标准']

# 文件大小和时长阈值（单位：MB和秒）
MIN_FILE_SIZE_MB = 2.0
MIN_DURATION_SECONDS = 90.0