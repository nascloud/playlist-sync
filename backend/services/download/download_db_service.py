import sqlite3
from typing import List, Optional, Callable, Any
from core.database import get_db_connection
from schemas.download import DownloadQueueItem, DownloadQueueItemCreate
import logging

logger = logging.getLogger(__name__)

class DownloadDBService:
    """封装所有与下载相关的数据库操作，确保线程安全。"""

    def _execute_in_thread(self, func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        在与 get_db_connection 相同的线程中安全地执行数据库操作。
        """
        conn = None
        try:
            conn = get_db_connection()
            return func(conn, *args, **kwargs)
        except Exception as e:
            logger.error(f"数据库操作失败: {e}", exc_info=True)
            # 根据需要，可以决定是重新抛出异常还是返回一个默认值
            raise  
        finally:
            if conn:
                conn.close()

    def create_download_session(self, task_id: int, session_type: str, total_songs: int, conn: Optional[sqlite3.Connection] = None) -> int:
        """创建一个新的下载会话并返回其ID。"""
        def _create_session(conn: sqlite3.Connection, task_id: int, session_type: str, total_songs: int) -> int:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO download_sessions (task_id, session_type, total_songs, status, success_count, failed_count)
                VALUES (?, ?, ?, 'active', 0, 0)
                """,
                (task_id, session_type, total_songs)
            )
            conn.commit()
            return cursor.lastrowid

        if conn:
            return _create_session(conn, task_id, session_type, total_songs)
        return self._execute_in_thread(_create_session, task_id, session_type, total_songs)

    def add_items_to_queue(self, session_id: int, items: List[DownloadQueueItemCreate], conn: Optional[sqlite3.Connection] = None):
        """将多个项目批量添加到下载队列。"""
        def _add_items(conn: sqlite3.Connection, session_id: int, items: List[DownloadQueueItemCreate]):
            cursor = conn.cursor()
            
            from datetime import datetime, timezone
            now_utc = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')

            items_to_insert = [
                (
                    session_id,
                    item.song_id,
                    item.title,
                    item.artist,
                    item.album,
                    item.quality or 'default',
                    'pending',
                    item.platform,
                    now_utc,
                    now_utc
                ) for item in items
            ]
            cursor.executemany(
                """
                INSERT INTO download_queue (
                    session_id, song_id, title, artist, album, quality, 
                    status, platform, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                items_to_insert
            )
            conn.commit()
        
        if conn:
            _add_items(conn, session_id, items)
        else:
            self._execute_in_thread(_add_items, session_id, items)

    def find_latest_session_by_task_id(self, task_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[int]:
        """根据 task_id 查找最新的一个会话，无论状态如何。"""
        def _find_session(conn: sqlite3.Connection, task_id: int) -> Optional[int]:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id FROM download_sessions WHERE task_id = ? ORDER BY created_at DESC LIMIT 1",
                (task_id,)
            )
            row = cursor.fetchone()
            return row['id'] if row else None

        if conn:
            return _find_session(conn, task_id)
        return self._execute_in_thread(_find_session, task_id)

    def reactivate_session(self, session_id: int, conn: Optional[sqlite3.Connection] = None):
        """如果一个会话已完成，则将其重新激活。"""
        def _reactivate(conn: sqlite3.Connection, session_id: int):
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE download_sessions SET status = 'active', completed_at = NULL WHERE id = ? AND status = 'completed'",
                (session_id,)
            )
            conn.commit()

        if conn:
            _reactivate(conn, session_id)
        else:
            self._execute_in_thread(_reactivate, session_id)

    def update_session_song_count(self, session_id: int, count_to_add: int, conn: Optional[sqlite3.Connection] = None):
        """更新会话的歌曲总数。"""
        def _update_count(conn: sqlite3.Connection, session_id: int, count_to_add: int):
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE download_sessions SET total_songs = total_songs + ? WHERE id = ?",
                (count_to_add, session_id)
            )
            conn.commit()

        if conn:
            _update_count(conn, session_id, count_to_add)
        else:
            self._execute_in_thread(_update_count, session_id, count_to_add)

    def get_next_pending_item(self) -> Optional[DownloadQueueItem]:
        """从队列中获取下一个待处理的项目并将其标记为"下载中"（原子操作）。"""
        def _get_next(conn: sqlite3.Connection) -> Optional[DownloadQueueItem]:
            try:
                conn.isolation_level = 'EXCLUSIVE'
                cursor = conn.cursor()
                cursor.execute('BEGIN EXCLUSIVE')
                
                # 关联查询会话状态，确保不会获取到已暂停会话中的项目
                query = """
                    SELECT 
                        q.id, q.session_id, q.song_id, q.title, q.artist, q.album, 
                        q.status, q.quality, q.error_message, q.platform,
                        COALESCE(q.retry_count, 0) as retry_count,
                        strftime('%Y-%m-%dT%H:%M:%SZ', COALESCE(q.created_at, '1970-01-01T00:00:00Z')) as created_at,
                        strftime('%Y-%m-%dT%H:%M:%SZ', COALESCE(q.updated_at, '1970-01-01T00:00:00Z')) as updated_at
                    FROM download_queue q
                    JOIN download_sessions s ON q.session_id = s.id
                    WHERE q.status = 'pending' AND s.status = 'active'
                    ORDER BY q.created_at ASC 
                    LIMIT 1
                """
                cursor.execute(query)
                item_row = cursor.fetchone()

                if item_row:
                    item_id = item_row['id']
                    cursor.execute(
                        "UPDATE download_queue SET status = 'downloading', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (item_id,)
                    )
                    conn.commit()
                    return DownloadQueueItem(**dict(item_row))
                else:
                    conn.commit()
                    return None
            except Exception:
                conn.rollback()
                raise
        return self._execute_in_thread(_get_next)

    def update_queue_item_status(self, item_id: int, status: str, error_message: Optional[str] = None):
        """更新队列项目的状态，并级联更新会话状态。"""
        def _update_status(conn: sqlite3.Connection, item_id: int, status: str, error_message: Optional[str]):
            try:
                conn.isolation_level = 'EXCLUSIVE'
                cursor = conn.cursor()
                cursor.execute('BEGIN EXCLUSIVE')

                # 1. 更新队列项目状态
                cursor.execute(
                    "UPDATE download_queue SET status = ?, error_message = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (status, error_message, item_id)
                )

                # 获取 session_id
                cursor.execute("SELECT session_id FROM download_queue WHERE id = ?", (item_id,))
                session_id_row = cursor.fetchone()
                session_id = session_id_row['session_id'] if session_id_row else None

                # 更新计数和检查会话状态（无论成功还是失败）
                if status == 'success':
                    # 2. 增加 session 的 success_count
                    if session_id:
                        cursor.execute(
                            "UPDATE download_sessions SET success_count = success_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (session_id,)
                        )
                elif status == 'failed':
                    # 如果失败，也更新计数器
                    if session_id:
                        cursor.execute(
                            "UPDATE download_sessions SET failed_count = failed_count + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (session_id,)
                        )
                
                # 检查会话是否完成（无论成功还是失败）
                if session_id:
                    cursor.execute("SELECT total_songs, COALESCE(success_count, 0) as success_count, COALESCE(failed_count, 0) as failed_count FROM download_sessions WHERE id = ?", (session_id,))
                    session_info = cursor.fetchone()
                    if session_info and (session_info['success_count'] + session_info['failed_count'] >= session_info['total_songs']):
                        cursor.execute(
                            "UPDATE download_sessions SET status = 'completed', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
                            (session_id,)
                        )
                
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        
        self._execute_in_thread(_update_status, item_id, status, error_message)

    def cancel_queue_item(self, item_id: int):
        """将单个队列项目标记为"已取消"。"""
        def _cancel_item(conn: sqlite3.Connection, item_id: int):
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE download_queue SET status = 'cancelled' WHERE id = ? AND status IN ('pending', 'downloading')",
                (item_id,)
            )
            conn.commit()
            return cursor.rowcount > 0
        
        return self._execute_in_thread(_cancel_item, item_id)

    def retry_queue_item(self, item_id: int):
        """重置失败的项目为待处理状态。"""
        def _retry_item(conn: sqlite3.Connection, item_id: int):
            try:
                conn.isolation_level = 'EXCLUSIVE'
                cursor = conn.cursor()
                cursor.execute('BEGIN EXCLUSIVE')
                
                # 获取项目当前状态和session_id
                cursor.execute(
                    "SELECT status, session_id FROM download_queue WHERE id = ?",
                    (item_id,)
                )
                item_info = cursor.fetchone()
                
                if not item_info or item_info['status'] != 'failed':
                    conn.commit()
                    return False
                
                session_id = item_info['session_id']
                
                # 1. 更新项目状态
                cursor.execute(
                    "UPDATE download_queue SET status = 'pending', error_message = NULL, retry_count = 0 WHERE id = ? AND status = 'failed'",
                    (item_id,)
                )
                updated = cursor.rowcount > 0
                
                # 2. 如果项目被更新，相应更新会话的failed_count
                if updated:
                    # 更新会话的failed_count
                    cursor.execute(
                        "UPDATE download_sessions SET failed_count = failed_count - 1 WHERE id = ?",
                        (session_id,)
                    )
                    # 将会话状态从completed改回active，以便重新处理
                    cursor.execute(
                        "UPDATE download_sessions SET status = 'active', completed_at = NULL WHERE id = ? AND status = 'completed'",
                        (session_id,)
                    )
                
                conn.commit()
                return updated
            except Exception:
                conn.rollback()
                raise

        return self._execute_in_thread(_retry_item, item_id)

    def delete_completed_sessions(self):
        """在一个事务中删除所有已完成的会话及其所有关联的项目。"""
        def _delete_completed(conn: sqlite3.Connection):
            try:
                conn.isolation_level = 'EXCLUSIVE'
                cursor = conn.cursor()
                cursor.execute('BEGIN EXCLUSIVE')

                # 1. 查找所有已完成的会话ID
                cursor.execute("SELECT id FROM download_sessions WHERE status = 'completed'")
                session_ids_to_delete = [row['id'] for row in cursor.fetchall()]

                if not session_ids_to_delete:
                    return 0 # 没有需要删除的会话

                placeholders = ','.join('?' for _ in session_ids_to_delete)

                # 2. 删除这些会话下的所有队列项目
                cursor.execute(f"DELETE FROM download_queue WHERE session_id IN ({placeholders})", tuple(session_ids_to_delete))
                
                # 3. 删除会话本身
                cursor.execute(f"DELETE FROM download_sessions WHERE id IN ({placeholders})", tuple(session_ids_to_delete))
                
                conn.commit()
                return len(session_ids_to_delete)
            except Exception:
                conn.rollback()
                raise
        
        return self._execute_in_thread(_delete_completed)

    def retry_failed_items_in_session(self, session_id: int):
        """重试一个会话中所有失败的项目。"""
        def _retry_failed(conn: sqlite3.Connection, session_id: int):
            try:
                conn.isolation_level = 'EXCLUSIVE'
                cursor = conn.cursor()
                cursor.execute('BEGIN EXCLUSIVE')
                
                # 1. 更新失败项目的状态为pending
                cursor.execute(
                    "UPDATE download_queue SET status = 'pending', error_message = NULL, retry_count = 0 WHERE session_id = ? AND status = 'failed'",
                    (session_id,)
                )
                count = cursor.rowcount
                
                # 2. 如果有项目被重置，相应更新会话的failed_count和状态
                if count > 0:
                    # 更新会话的failed_count
                    cursor.execute(
                        "UPDATE download_sessions SET failed_count = failed_count - ? WHERE id = ?",
                        (count, session_id)
                    )
                    # 将会话状态从completed改回active，以便重新处理
                    cursor.execute(
                        "UPDATE download_sessions SET status = 'active', completed_at = NULL WHERE id = ? AND status = 'completed'",
                        (session_id,)
                    )
                
                conn.commit()
                return count
            except Exception:
                conn.rollback()
                raise

        return self._execute_in_thread(_retry_failed, session_id)

    def pause_session_and_items(self, session_id: int):
        """在一个事务中暂停会话及其所有待处理的项目。"""
        def _pause(conn: sqlite3.Connection, session_id: int):
            try:
                conn.isolation_level = 'EXCLUSIVE'
                cursor = conn.cursor()
                cursor.execute('BEGIN EXCLUSIVE')

                # 1. 更新会话状态
                cursor.execute(
                    "UPDATE download_sessions SET status = 'paused' WHERE id = ? AND status = 'active'",
                    (session_id,)
                )

                # 2. 更新该会话中所有待处理和正在下载的项目的状态
                cursor.execute(
                    "UPDATE download_queue SET status = 'paused' WHERE session_id = ? AND status IN ('pending', 'downloading')",
                    (session_id,)
                )
                
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        
        return self._execute_in_thread(_pause, session_id)

    def resume_session_and_items(self, session_id: int):
        """在一个事务中恢复会话及其所有暂停的项目。"""
        def _resume(conn: sqlite3.Connection, session_id: int):
            logger.info(f"数据库: 正在恢复会话 {session_id}")
            try:
                conn.isolation_level = 'EXCLUSIVE'
                cursor = conn.cursor()
                cursor.execute('BEGIN EXCLUSIVE')

                # 1. 更新会话状态
                cursor.execute(
                    "UPDATE download_sessions SET status = 'active' WHERE id = ? AND status = 'paused'",
                    (session_id,)
                )
                logger.info(f"数据库: 会话 {session_id} 状态已更新为 'active' (影响行数: {cursor.rowcount})")

                # 2. 更新该会话中所有暂停项目的状态为待处理
                cursor.execute(
                    "UPDATE download_queue SET status = 'pending' WHERE session_id = ? AND status = 'paused'",
                    (session_id,)
                )
                logger.info(f"数据库: 会话 {session_id} 的暂停项目状态已更新为 'pending' (影响行数: {cursor.rowcount})")
                
                conn.commit()
                logger.info(f"数据库: 会话 {session_id} 恢复事务已提交。")
            except Exception as e:
                logger.error(f"数据库: 恢复会话 {session_id} 时发生错误", exc_info=True)
                conn.rollback()
                raise
        
        return self._execute_in_thread(_resume, session_id)

    def delete_session_and_items(self, session_id: int):
        """在一个事务中删除会话及其所有关联的项目。"""
        def _delete(conn: sqlite3.Connection, session_id: int):
            try:
                conn.isolation_level = 'EXCLUSIVE'
                cursor = conn.cursor()
                cursor.execute('BEGIN EXCLUSIVE')

                # 1. 删除队列中的项目
                cursor.execute("DELETE FROM download_queue WHERE session_id = ?", (session_id,))
                
                # 2. 删除会话本身
                cursor.execute("DELETE FROM download_sessions WHERE id = ?", (session_id,))
                
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        
        return self._execute_in_thread(_delete, session_id)

    def get_item_details(self, item_id: int):
        """获取单个队列项目的详细信息。"""
        def _get_details(conn: sqlite3.Connection, item_id: int):
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM download_queue WHERE id = ?", (item_id,))
            row = cursor.fetchone()
            return row

        return self._execute_in_thread(_get_details, item_id)

    def fix_session_counts(self, session_id: int):
        """修复会话的计数器，使其与实际项目状态一致。"""
        def _fix_counts(conn: sqlite3.Connection, session_id: int):
            try:
                conn.isolation_level = 'EXCLUSIVE'
                cursor = conn.cursor()
                cursor.execute('BEGIN EXCLUSIVE')
                
                # 1. 计算实际的成功和失败项目数量
                cursor.execute(
                    "SELECT COUNT(*) as success_count FROM download_queue WHERE session_id = ? AND status = 'success'",
                    (session_id,)
                )
                success_count = cursor.fetchone()['success_count']
                
                cursor.execute(
                    "SELECT COUNT(*) as failed_count FROM download_queue WHERE session_id = ? AND status = 'failed'",
                    (session_id,)
                )
                failed_count = cursor.fetchone()['failed_count']
                
                # 2. 更新会话的计数器
                cursor.execute(
                    "UPDATE download_sessions SET success_count = ?, failed_count = ? WHERE id = ?",
                    (success_count, failed_count, session_id)
                )
                
                conn.commit()
                return success_count, failed_count
            except Exception:
                conn.rollback()
                raise
        
        return self._execute_in_thread(_fix_counts, session_id)

    def get_full_queue_status(self) -> dict:
        """获取所有会话（包含其下所有项目）的层级结构列表。"""
        def _get_status(conn: sqlite3.Connection) -> dict:
            cursor = conn.cursor()
            
            # 1. 获取所有会话，并关联任务名称。使用 CASE WHEN 处理搜索下载任务的特殊情况。
            query = """
                SELECT
                    s.id, s.task_id,
                    CASE
                        WHEN s.task_id = 0 THEN '搜索下载'
                        ELSE COALESCE(t.name, '未知任务')
                    END as task_name,
                    s.session_type, s.total_songs,
                    COALESCE(s.success_count, 0) as success_count,
                    COALESCE(s.failed_count, 0) as failed_count,
                    s.status,
                    strftime('%Y-%m-%dT%H:%M:%SZ', COALESCE(s.created_at, '1970-01-01T00:00:00Z')) as created_at,
                    strftime('%Y-%m-%dT%H:%M:%SZ', s.completed_at) as completed_at
                FROM download_sessions s
                LEFT JOIN tasks t ON s.task_id = t.id
                ORDER BY s.created_at DESC
            """
            cursor.execute(query)
            sessions_raw = cursor.fetchall()
            
            sessions_map = {row['id']: dict(row) for row in sessions_raw}
            for session_id in sessions_map:
                sessions_map[session_id]['items'] = []

            if not sessions_map:
                return {"sessions": []}

            session_ids = tuple(sessions_map.keys())
            placeholders = ','.join('?' for _ in session_ids)
            
            # 2. 获取所有队列项目，同样使用 COALESCE
            queue_query = f"""
                SELECT 
                    id, session_id, song_id, title, artist, album, 
                    COALESCE(quality, 'unknown') as quality, 
                    COALESCE(status, 'pending') as status, 
                    error_message,
                    strftime('%Y-%m-%dT%H:%M:%SZ', COALESCE(created_at, '1970-01-01T00:00:00Z')) as created_at,
                    strftime('%Y-%m-%dT%H:%M:%SZ', updated_at) as updated_at
                FROM download_queue
                WHERE session_id IN ({placeholders})
                ORDER BY created_at ASC
            """
            cursor.execute(queue_query, session_ids)
            queue_items = [dict(row) for row in cursor.fetchall()]

            for item in queue_items:
                session_id = item['session_id']
                if session_id in sessions_map:
                    sessions_map[session_id]['items'].append(item)

            return {"sessions": list(sessions_map.values())}

        return self._execute_in_thread(_get_status)
        
    def get_task_id_by_session_id(self, session_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[int]:
        """
        根据session_id获取对应的task_id。
        :param session_id: 下载会话ID
        :param conn: 数据库连接（可选）
        :return: 任务ID或None（如果未找到）
        """
        def _get_task_id(conn: sqlite3.Connection, session_id: int) -> Optional[int]:
            cursor = conn.cursor()
            cursor.execute('SELECT task_id FROM download_sessions WHERE id = ?', (session_id,))
            row = cursor.fetchone()
            return row['task_id'] if row else None
        
        if conn:
            return _get_task_id(conn, session_id)
        else:
            return self._execute_in_thread(_get_task_id, session_id)

    def update_session_download_lyrics(self, session_id: int, download_lyrics: bool, conn: Optional[sqlite3.Connection] = None):
        """更新会话的歌词下载设置。"""
        def _update_download_lyrics(conn: sqlite3.Connection, session_id: int, download_lyrics: bool):
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE download_sessions SET download_lyrics = ? WHERE id = ?",
                (1 if download_lyrics else 0, session_id)
            )
            conn.commit()
        
        if conn:
            _update_download_lyrics(conn, session_id, download_lyrics)
        else:
            self._execute_in_thread(_update_download_lyrics, session_id, download_lyrics)

    def get_session_download_lyrics(self, session_id: int, conn: Optional[sqlite3.Connection] = None) -> Optional[bool]:
        """获取会话的歌词下载设置。"""
        def _get_download_lyrics(conn: sqlite3.Connection, session_id: int) -> Optional[bool]:
            cursor = conn.cursor()
            cursor.execute("SELECT download_lyrics FROM download_sessions WHERE id = ?", (session_id,))
            row = cursor.fetchone()
            if row and row['download_lyrics'] is not None:
                return bool(row['download_lyrics'])
            return None
        
        if conn:
            return _get_download_lyrics(conn, session_id)
        else:
            return self._execute_in_thread(_get_download_lyrics, session_id)

# 实例化服务
download_db_service = DownloadDBService()