import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool, MetaData, Table, Column, Integer, String, DateTime, Boolean, Text, ForeignKey

from alembic import context

# 将项目根目录添加到 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 定义所有表的元数据
meta = MetaData()

Table(
    'settings', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String, nullable=False),
    Column('server_type', String, nullable=False),
    Column('url', String, nullable=False),
    Column('token', String, nullable=False)
)

Table(
    'tasks', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('name', String, nullable=False),
    Column('playlist_url', String, nullable=False),
    Column('platform', String, nullable=False),
    Column('status', String, default='pending'),
    Column('status_message', Text),
    Column('last_sync_time', DateTime),
    Column('cron_schedule', String, default='0 2 * * *'),
    Column('unmatched_songs', Text),
    Column('total_songs', Integer, default=0),
    Column('matched_songs', Integer, default=0),
    Column('created_at', DateTime, server_default='CURRENT_TIMESTAMP'),
    Column('updated_at', DateTime, server_default='CURRENT_TIMESTAMP'),
    Column('server_id', Integer, ForeignKey('settings.id', ondelete='CASCADE')),
    Column('auto_download', Boolean, default=False)
)

Table(
    'logs', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('task_id', Integer),
    Column('timestamp', String),
    Column('level', String),
    Column('message', Text)
)

Table(
    'download_settings', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('key', String, nullable=False, unique=True),
    Column('value', String, nullable=False)
)

Table(
    'download_sessions', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('task_id', Integer, nullable=False),
    Column('session_type', String, nullable=False),
    Column('total_songs', Integer, nullable=False),
    Column('success_count', Integer, default=0),
    Column('failed_count', Integer, default=0),
    Column('status', String, default='active'),
    Column('created_at', DateTime, server_default='CURRENT_TIMESTAMP'),
    Column('completed_at', DateTime)
)

Table(
    'download_queue', meta,
    Column('id', Integer, primary_key=True, autoincrement=True),
    Column('session_id', Integer, ForeignKey('download_sessions.id', ondelete='CASCADE')),
    Column('song_id', String),
    Column('title', String, nullable=False),
    Column('artist', String, nullable=False),
    Column('album', String),
    Column('status', String, default='pending'),
    Column('quality', String),
    Column('retry_count', Integer, default=0),
    Column('error_message', Text),
    Column('created_at', DateTime, server_default='CURRENT_TIMESTAMP'),
    Column('updated_at', DateTime, server_default='CURRENT_TIMESTAMP')
)

target_metadata = meta

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.
    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.
    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.
    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
