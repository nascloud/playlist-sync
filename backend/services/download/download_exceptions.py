"""下载服务相关的自定义异常"""

class APIError(Exception):
    """自定义 API 异常"""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code