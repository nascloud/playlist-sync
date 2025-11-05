import sqlite3
import os
import logging
from core.config import settings

logger = logging.getLogger(__name__)

def get_db_connection():
    """获取数据库连接并启用WAL模式"""
    db_path = "./data/database.sqlite"
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    conn.execute('PRAGMA journal_mode=WAL')  # 启用WAL模式，提高并发性能
    return conn

def init_db():
    """
    确保数据库连接启用了必要的 PRAGMA 设置。
    表结构的创建和修改现在由 Alembic 管理。
    """
    conn = get_db_connection()
    # 启用外键约束，这对于保持数据完整性很重要
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.close()
    logger.info("数据库连接 PRAGMA 设置已应用。")

