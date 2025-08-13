import os
import sys
from dotenv import load_dotenv

# 添加 backend 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# 加载 .env 文件
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(dotenv_path=env_path)

# 确保必要的环境变量已设置
required_env_vars = ['PLEX_URL', 'PLEX_TOKEN']
missing_env_vars = [var for var in required_env_vars if not os.getenv(var)]

if missing_env_vars:
    print(f"错误: 缺少必要的环境变量: {', '.join(missing_env_vars)}")
    print("请确保 .env 文件位于 backend 目录中，并包含 PLEX_URL 和 PLEX_TOKEN。")
    sys.exit(1)

# 运行测试
if __name__ == '__main__':
    import unittest
    from tests.test_enhanced_matching import TestEnhancedMatching
    
    # 设置标准输出编码为UTF-8
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    unittest.main()