import sqlite3
from core.database import get_db_connection
from core.security import encrypt_token, decrypt_token
from core.config import settings as env_settings
from typing import Optional, List, Callable, Any
from schemas.settings import ServerCreate, ServerUpdate, Server
from schemas.download_schemas import DownloadSettings, DownloadSettingsCreate
import logging

logger = logging.getLogger(__name__)

class SettingsService:
    """
    封装所有与设置相关的数据库操作，确保线程安全。
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
            logger.error(f"设置数据库操作失败: {e}", exc_info=True)
            raise
        finally:
            if conn:
                conn.close()

    # --- Server Settings ---

    @staticmethod
    def get_all_servers() -> List[Server]:
        def _get_all(conn: sqlite3.Connection) -> List[Server]:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, server_type, url FROM settings')
            servers = cursor.fetchall()
            
            # 如果数据库中没有服务器，并且环境变量中有Plex配置
            if not servers and env_settings.plex.URL and env_settings.plex.TOKEN:
                logger.info("数据库中无服务器配置，尝试从环境变量创建 Plex 服务器。")
                
                # 检查是否已存在名为 'Plex (from env)' 的服务器
                cursor.execute("SELECT id FROM settings WHERE name = ?", ('Plex (from env)',))
                if not cursor.fetchone():
                    try:
                        encrypted_token = encrypt_token(env_settings.plex.TOKEN)
                        cursor.execute(
                            'INSERT INTO settings (name, server_type, url, token) VALUES (?, ?, ?, ?)',
                            ('Plex (from env)', 'plex', env_settings.plex.URL, encrypted_token)
                        )
                        conn.commit()
                        logger.info("已成功从环境变量中创建并存储 Plex 服务器配置。")
                        
                        # 重新查询以包含新创建的服务器
                        cursor.execute('SELECT id, name, server_type, url FROM settings')
                        servers = cursor.fetchall()
                    except Exception as e:
                        logger.error(f"从环境变量创建服务器时出错: {e}", exc_info=True)
                        conn.rollback() # 出错时回滚

            return [Server(**dict(server)) for server in servers]
        return SettingsService._execute(_get_all)

    @staticmethod
    def get_server_by_id(server_id: int) -> Optional[Server]:
        def _get_by_id(conn: sqlite3.Connection, server_id: int) -> Optional[Server]:
            cursor = conn.cursor()
            cursor.execute('SELECT id, name, server_type, url, token FROM settings WHERE id = ?', (server_id,))
            server_data = cursor.fetchone()
            if server_data:
                decrypted_token = decrypt_token(server_data['token'])
                server = Server(**dict(server_data))
                server.decrypted_token = decrypted_token
                return server
            return None
        return SettingsService._execute(_get_by_id, server_id)

    @staticmethod
    def add_server(server: ServerCreate) -> Server:
        def _add(conn: sqlite3.Connection, server: ServerCreate) -> Server:
            encrypted_token = encrypt_token(server.token)
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO settings (name, server_type, url, token) VALUES (?, ?, ?, ?)',
                (server.name, server.server_type.value, str(server.url), encrypted_token)
            )
            server_id = cursor.lastrowid
            conn.commit()
            # 在同一连接/事务中获取新创建的服务器
            cursor.execute('SELECT id, name, server_type, url FROM settings WHERE id = ?', (server_id,))
            new_server_data = cursor.fetchone()
            return Server(**dict(new_server_data))
        return SettingsService._execute(_add, server)

    @staticmethod
    def update_server(server_id: int, server_update: ServerUpdate) -> Optional[Server]:
        def _update(conn: sqlite3.Connection, server_id: int, server_update: ServerUpdate) -> Optional[Server]:
            fields_to_update = server_update.model_dump(exclude_unset=True)
            if not fields_to_update:
                return SettingsService.get_server_by_id(server_id)
            
            if 'token' in fields_to_update:
                fields_to_update['token'] = encrypt_token(fields_to_update['token'])

            set_clause = ", ".join([f"{key} = ?" for key in fields_to_update.keys()])
            values = list(fields_to_update.values())
            values.append(server_id)

            cursor = conn.cursor()
            cursor.execute(f'UPDATE settings SET {set_clause} WHERE id = ?', tuple(values))
            conn.commit()
            
            cursor.execute('SELECT id, name, server_type, url, token FROM settings WHERE id = ?', (server_id,))
            updated_server_data = cursor.fetchone()
            if updated_server_data:
                decrypted_token = decrypt_token(updated_server_data['token'])
                server = Server(**dict(updated_server_data))
                server.decrypted_token = decrypted_token
                return server
            return None
        return SettingsService._execute(_update, server_id, server_update)

    @staticmethod
    def delete_server(server_id: int) -> bool:
        def _delete(conn: sqlite3.Connection, server_id: int) -> bool:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM settings WHERE id = ?', (server_id,))
            conn.commit()
            return cursor.rowcount > 0
        return SettingsService._execute(_delete, server_id)

    # --- Download Settings ---

    @staticmethod
    def get_download_settings() -> Optional[DownloadSettings]:
        def _get_settings(conn: sqlite3.Connection) -> Optional[DownloadSettings]:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM download_settings")
            db_settings = {row['key']: row['value'] for row in cursor.fetchall()}

            if 'api_key' in db_settings:
                try:
                    db_settings['api_key'] = decrypt_token(db_settings['api_key'])
                except Exception:
                    db_settings['api_key'] = ""

            final_api_key = env_settings.downloader.API_KEY or db_settings.get('api_key', '')
            final_download_path = env_settings.downloader.PATH or db_settings.get('download_path', '/downloads')

            return DownloadSettings(
                id=1,
                api_key=final_api_key,
                download_path=final_download_path,
                preferred_quality=db_settings.get('preferred_quality', 'high'),
                download_lyrics=bool(int(db_settings.get('download_lyrics', 0))),
                auto_download=bool(int(db_settings.get('auto_download', 0))),
                max_concurrent_downloads=int(db_settings.get('max_concurrent_downloads', 3))
            )
        return SettingsService._execute(_get_settings)

    @staticmethod
    def save_download_settings(settings: DownloadSettingsCreate) -> DownloadSettings:
        def _save_settings(conn: sqlite3.Connection, settings: DownloadSettingsCreate) -> DownloadSettings:
            settings_to_save = settings.model_dump()
            settings_to_save.pop('api_key', None)
            settings_to_save.pop('download_path', None)

            cursor = conn.cursor()
            for key, value in settings_to_save.items():
                if isinstance(value, bool): value = int(value)
                cursor.execute(
                    "INSERT INTO download_settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, str(value))
                )
            conn.commit()
            
            # Re-fetch to return the complete, merged settings
            cursor.execute("SELECT key, value FROM download_settings")
            db_settings = {row['key']: row['value'] for row in cursor.fetchall()}
            final_api_key = env_settings.downloader.API_KEY or ""
            final_download_path = env_settings.downloader.PATH or "/downloads"

            return DownloadSettings(
                id=1,
                api_key=final_api_key,
                download_path=final_download_path,
                preferred_quality=db_settings.get('preferred_quality', 'high'),
                download_lyrics=bool(int(db_settings.get('download_lyrics', 0))),
                auto_download=bool(int(db_settings.get('auto_download', 0))),
                max_concurrent_downloads=int(db_settings.get('max_concurrent_downloads', 3))
            )
        return SettingsService._execute(_save_settings, settings)
