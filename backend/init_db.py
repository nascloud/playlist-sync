#!/usr/bin/env python3
"""
数据库初始化脚本
确保数据目录存在并初始化数据库（如果需要）
"""
import os
import sqlite3
from core.config import settings
from core.database import init_db

def ensure_data_directory():
    """确保数据目录存在"""
    data_dir = os.path.dirname(settings.DATABASE_URL.replace("sqlite:///", ""))
    os.makedirs(data_dir, exist_ok=True)
    print(f"确保数据目录存在: {data_dir}")

def init_database():
    """初始化数据库"""
    print("初始化数据库...")
    init_db()
    print("数据库初始化完成")

if __name__ == "__main__":
    ensure_data_directory()
    init_database()
    print("数据库初始化脚本执行完成")