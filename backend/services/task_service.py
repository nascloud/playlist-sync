import json
import sqlite3
from core.database import get_db_connection
from schemas.tasks import TaskCreate, Task
from typing import List, Optional, Callable, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class TaskService:
    """
    封装所有与任务相关的数据库操作，确保线程安全。
    """

    @staticmethod
    def _execute(func: Callable[..., Any], *args, **kwargs) -> Any:
        """
        在与 get_db_connection 相同的线程中安全地执行数据库操作。
        """
        conn = None
        try:
            conn = get_db_connection()
            return func(conn, *args, **kwargs)
        except Exception as e:
            logger.error(f"任务数据库操作失败: {e}", exc_info=True)
            raise

        finally:
            if conn:
                conn.close()

    @staticmethod
    def _row_to_task(row) -> Task:
        if not row:
            return None
        
        row_dict = dict(row)
            
        created_at_str = str(row_dict['created_at']).upper()
        updated_at_str = str(row_dict['updated_at']).upper()
        
        created_at = datetime.utcnow() if 'CURRENT_TIMESTAMP' in created_at_str else row_dict['created_at']
        updated_at = datetime.utcnow() if 'CURRENT_TIMESTAMP' in updated_at_str else row_dict['updated_at']

        return Task(
            id=row_dict['id'],
            name=row_dict['name'],
            playlist_url=row_dict['playlist_url'],
            platform=row_dict['platform'],
            cron_schedule=row_dict['cron_schedule'] or '0 2 * * *',
            last_sync_time=row_dict['last_sync_time'],
            status=row_dict['status'],
            unmatched_songs=row_dict['unmatched_songs'],
            total_songs=row_dict['total_songs'] or 0,
            matched_songs=row_dict['matched_songs'] or 0,
            created_at=created_at,
            updated_at=updated_at,
            server_id=row_dict['server_id'],
            auto_download=row_dict.get('auto_download', False)
        )

    # --- Public-facing methods ---

    @staticmethod
    def get_all_tasks() -> List[Task]:
        def _get_all(conn: sqlite3.Connection) -> List[Task]:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks ORDER BY id DESC')
            rows = cursor.fetchall()
            return [TaskService._row_to_task(row) for row in rows]
        return TaskService._execute(_get_all)
    
    @staticmethod
    def get_task_by_id(task_id: int) -> Optional[Task]:
        def _get_by_id(conn: sqlite3.Connection, task_id: int) -> Optional[Task]:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            return TaskService._row_to_task(row)
        return TaskService._execute(_get_by_id, task_id)
    
    @staticmethod
    def create_task(task: TaskCreate) -> int:
        def _create(conn: sqlite3.Connection, task: TaskCreate) -> int:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO tasks (name, playlist_url, platform, cron_schedule, server_id, status)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                task.name, str(task.playlist_url), task.platform, 
                task.cron_schedule, task.server_id, 'pending'
            ))
            conn.commit()
            return cursor.lastrowid
        return TaskService._execute(_create, task)
    
    @staticmethod
    def update_task_schedule(task_id: int, cron_schedule: str) -> bool:
        def _update_schedule(conn: sqlite3.Connection, task_id: int, cron_schedule: str) -> bool:
            cursor = conn.cursor()
            cursor.execute('UPDATE tasks SET cron_schedule = ? WHERE id = ?', (cron_schedule, task_id))
            conn.commit()
            return cursor.rowcount > 0
        return TaskService._execute(_update_schedule, task_id, cron_schedule)

    @staticmethod
    def update_task_name(task_id: int, new_name: str) -> bool:
        def _update_name(conn: sqlite3.Connection, task_id: int, new_name: str) -> bool:
            cursor = conn.cursor()
            cursor.execute('UPDATE tasks SET name = ? WHERE id = ?', (new_name, task_id))
            conn.commit()
            return cursor.rowcount > 0
        return TaskService._execute(_update_name, task_id, new_name)

    @staticmethod
    def update_task_status(task_id: int, status: str, status_message: Optional[str] = None) -> bool:
        def _update_status(conn: sqlite3.Connection, task_id: int, status: str, status_message: Optional[str]) -> bool:
            cursor = conn.cursor()
            
            # 保留原始逻辑，如果 message 为 None，则只更新 status
            if status_message is not None:
                cursor.execute(
                    'UPDATE tasks SET status = ?, status_message = ? WHERE id = ?',
                    (status, status_message, task_id)
                )
            else:
                cursor.execute('UPDATE tasks SET status = ? WHERE id = ?', (status, task_id))

            conn.commit()
            return cursor.rowcount > 0
        return TaskService._execute(_update_status, task_id, status, status_message)

    @staticmethod
    def update_sync_counts(task_id: int, total: int, matched: int) -> bool:
        def _update_counts(conn: sqlite3.Connection, task_id: int, total: int, matched: int) -> bool:
            cursor = conn.cursor()
            cursor.execute('UPDATE tasks SET total_songs = ?, matched_songs = ? WHERE id = ?', (total, matched, task_id))
            conn.commit()
            return cursor.rowcount > 0
        return TaskService._execute(_update_counts, task_id, total, matched)
        
    @staticmethod
    def update_unmatched_songs(task_id: int, unmatched_songs: list) -> bool:
        def _update_unmatched(conn: sqlite3.Connection, task_id: int, unmatched_songs: list) -> bool:
            cursor = conn.cursor()
            cursor.execute('UPDATE tasks SET unmatched_songs = ? WHERE id = ?', (json.dumps(unmatched_songs), task_id))
            conn.commit()
            return cursor.rowcount > 0
        return TaskService._execute(_update_unmatched, task_id, unmatched_songs)

    @staticmethod
    def update_last_sync_time(task_id: int) -> bool:
        def _update_time(conn: sqlite3.Connection, task_id: int) -> bool:
            now_utc = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3] + 'Z'
            cursor = conn.cursor()
            cursor.execute('UPDATE tasks SET last_sync_time = ? WHERE id = ?', (now_utc, task_id))
            conn.commit()
            return cursor.rowcount > 0
        return TaskService._execute(_update_time, task_id)

    @staticmethod
    def delete_task(task_id: int) -> bool:
        def _delete(conn: sqlite3.Connection, task_id: int) -> bool:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
            conn.commit()
            return cursor.rowcount > 0
        return TaskService._execute(_delete, task_id)

    @staticmethod
    def get_unmatched_songs_for_task(task_id: int, db: Optional[sqlite3.Connection] = None) -> List[dict]:
        def _get_unmatched(conn: sqlite3.Connection, task_id: int) -> List[dict]:
            cursor = conn.cursor()
            cursor.execute('SELECT unmatched_songs FROM tasks WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            if not row or not row['unmatched_songs']:
                return []
            try:
                return json.loads(row['unmatched_songs'])
            except json.JSONDecodeError:
                return []
        
        if db:
            return _get_unmatched(db, task_id)
        else:
            return TaskService._execute(_get_unmatched, task_id)
            
    @staticmethod
    def remove_matched_songs_from_task(task_id: int, matched_songs: List[dict], db: Optional[sqlite3.Connection] = None) -> bool:
        """
        从任务的未匹配歌曲列表中移除已匹配的歌曲，并更新同步计数。
        :param task_id: 任务ID
        :param matched_songs: 已匹配的歌曲列表
        :param db: 数据库连接（可选）
        :return: 操作是否成功
        """
        def _remove_matched(conn: sqlite3.Connection, task_id: int, matched_songs: List[dict]) -> bool:
            try:
                cursor = conn.cursor()
                
                # 1. 获取当前的未匹配歌曲列表
                cursor.execute('SELECT unmatched_songs, matched_songs FROM tasks WHERE id = ?', (task_id,))
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"Task {task_id} not found")
                    return False
                    
                current_unmatched = []
                if row['unmatched_songs']:
                    try:
                        current_unmatched = json.loads(row['unmatched_songs'])
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse unmatched_songs for task {task_id}")
                        current_unmatched = []
                
                current_matched_count = row['matched_songs'] or 0
                
                # 2. 从当前未匹配列表中移除已匹配的歌曲
                # 通过比较歌曲的关键信息（标题、艺术家）来识别匹配项
                matched_song_keys = {
                    (song.get('title', ''), song.get('artist', '')) 
                    for song in matched_songs 
                    if song.get('title') and song.get('artist')
                }
                
                new_unmatched = [
                    song for song in current_unmatched
                    if (song.get('title', ''), song.get('artist', '')) not in matched_song_keys
                ]
                
                removed_count = len(current_unmatched) - len(new_unmatched)
                new_matched_count = current_matched_count + removed_count
                
                # 3. 更新数据库
                cursor.execute(
                    'UPDATE tasks SET unmatched_songs = ?, matched_songs = ? WHERE id = ?', 
                    (json.dumps(new_unmatched), new_matched_count, task_id)
                )
                conn.commit()
                
                logger.info(f"Task {task_id}: Removed {removed_count} matched songs, new matched count: {new_matched_count}")
                return True
            except Exception as e:
                logger.error(f"Error removing matched songs from task {task_id}: {e}", exc_info=True)
                return False
        
        if db:
            return _remove_matched(db, task_id, matched_songs)
        else:
            return TaskService._execute(_remove_matched, task_id, matched_songs)
