from core.database import get_db_connection
from typing import List, Optional

class LogService:
    @staticmethod
    def log_activity(task_id: int, level: str, message: str):
        """
        记录活动日志
        :param task_id: 任务ID
        :param level: 日志级别
        :param message: 日志消息
        """
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat() + 'Z'
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO logs (task_id, timestamp, level, message)
            VALUES (?, ?, ?, ?)
        ''', (task_id, timestamp, level, message))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_logs(
        task_id: Optional[int] = None, 
        level: Optional[str] = None, 
        limit: int = 100
    ) -> List[dict]:
        """
        获取日志
        :param task_id: 任务ID（可选）
        :param level: 日志级别（可选）
        :param limit: 限制返回的日志数量
        :return: 日志列表
        """
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 构建查询语句和参数
        query = "SELECT * FROM logs WHERE 1=1"
        params = []
        
        if task_id is not None:
            query += " AND task_id = ?"
            params.append(task_id)
            
        if level is not None:
            query += " AND level = ?"
            params.append(level)
            
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()
        
        logs = []
        for row in rows:
            logs.append({
                'id': row['id'],
                'task_id': row['task_id'],
                'timestamp': row['timestamp'],
                'level': row['level'],
                'message': row['message']
            })
        
        return logs