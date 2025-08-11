
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

# 定义日志目录
LOGS_DIR = Path(__file__).resolve().parent.parent / 'logs'
LOGS_DIR.mkdir(exist_ok=True)

def setup_logging():
    """
    配置全局日志记录。
    - 输出到控制台
    - 输出到 app.log 文件，并按大小轮换
    """
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 1. 控制台 Handler
    # 移除旧的 handlers，避免重复添加
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 显式地为 stdout 设置 UTF-8 编码
    sys.stdout.reconfigure(encoding='utf-8')
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)
    
    # 2. 主应用文件 Handler (app.log)
    app_log_file = LOGS_DIR / "app.log"
    # 轮换文件处理器，每个文件最大 5MB，保留 5 个备份
    file_handler = RotatingFileHandler(
        app_log_file, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)
    
    logging.info("全局日志记录已初始化。")

class DownloadLogManager:
    """
    为每个下载会话动态创建和管理专用的日志记录器。
    """
    _loggers = {}
    
    @classmethod
    def get_logger(cls, session_id: int) -> logging.Logger:
        """
        获取或创建一个与特定下载会话关联的logger。
        """
        if session_id in cls._loggers:
            return cls._loggers[session_id]

        # 创建一个新的 logger，以避免与根 logger 的 handlers 冲突
        logger_name = f"download_session_{session_id}"
        logger = logging.getLogger(logger_name)
        
        # 防止日志向上传播到根 logger，避免在 app.log 和控制台中重复记录
        logger.propagate = False
        logger.setLevel(logging.INFO)

        # 为这个 logger 配置自己的 handler
        downloads_log_dir = LOGS_DIR / "downloads"
        downloads_log_dir.mkdir(exist_ok=True)
        log_file = downloads_log_dir / f"session_{session_id}.log"
        
        # 创建文件 handler
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        
        cls._loggers[session_id] = logger
        logger.info(f"为会话 {session_id} 初始化专用日志记录器。")
        return logger

# 实例化
download_log_manager = DownloadLogManager()
