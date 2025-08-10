import asyncio
from typing import Dict, AsyncGenerator

class ProgressManager:
    """
    一个用于管理多个任务实时进度消息流的单例类。
    """
    _instance = None
    _queues: Dict[int, asyncio.Queue] = {}
    _locks: Dict[int, asyncio.Lock] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ProgressManager, cls).__new__(cls)
        return cls._instance

    async def _get_queue(self, task_id: int) -> asyncio.Queue:
        """获取或创建一个新的任务队列"""
        if task_id not in self._locks:
            self._locks[task_id] = asyncio.Lock()
        
        async with self._locks[task_id]:
            if task_id not in self._queues:
                self._queues[task_id] = asyncio.Queue()
        return self._queues[task_id]

    async def send_message(self, task_id: int, message: str, event: str = "progress"):
        """向特定任务的流发送消息"""
        try:
            queue = await self._get_queue(task_id)
            await queue.put({"event": event, "data": message})
        except Exception as e:
            # 在这里可以添加日志记录
            print(f"Error sending message for task {task_id}: {e}")


    async def get_stream(self, task_id: int) -> AsyncGenerator[str, None]:
        """
        获取一个任务的异步生成器，用于 Server-Sent Events (SSE)。
        """
        queue = await self._get_queue(task_id)
        
        # 首先发送一个连接成功的消息
        yield "event: open\ndata: Connection established\n\n"
        
        try:
            while True:
                message_dict = await queue.get()
                event = message_dict.get("event", "message")
                data = message_dict.get("data", "")
                
                yield f"event: {event}\ndata: {data}\n\n"
                
                if event == "close":
                    break
        except asyncio.CancelledError:
            # 当客户端断开连接时，FastAPI会触发CancelledError
            pass
        finally:
            # 清理队列
            if task_id in self._queues:
                del self._queues[task_id]
            if task_id in self._locks:
                del self._locks[task_id]


# 创建一个全局单例
progress_manager = ProgressManager()
