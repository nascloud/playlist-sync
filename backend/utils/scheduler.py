from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
import logging
from services.task_service import TaskService
from services.sync_service import SyncService
from services.log_service import LogService
from services.settings_service import SettingsService
from core.logging_config import download_log_manager
from croniter import croniter
import os
from pathlib import Path

logger = logging.getLogger(__name__)

async def cleanup_old_download_logs():
    """
    一个后台任务，用于定期清理过期的下载日志文件。
    """
    logger.info("[日志清理] 开始执行过期下载日志清理任务...")
    try:
        settings = SettingsService.get_download_settings()
        if not settings or not settings.log_retention_days:
            logger.info("[日志清理] 未配置日志保留天数，任务跳过。")
            return

        retention_days = settings.log_retention_days
        log_dir = download_log_manager.LOGS_DIR / "downloads"
        
        if not log_dir.exists():
            logger.info(f"[日志清理] 日志目录 {log_dir} 不存在，无需清理。")
            return

        cutoff_time = datetime.now() - timedelta(days=retention_days)
        deleted_count = 0
        
        for log_file in log_dir.glob("session_*.log"):
            try:
                file_mod_time = datetime.fromtimestamp(os.path.getmtime(log_file))
                if file_mod_time < cutoff_time:
                    os.remove(log_file)
                    deleted_count += 1
                    logger.info(f"[日志清理] 已删除过期日志文件: {log_file.name}")
            except Exception as e:
                logger.error(f"[日志清理] 删除日志文件 {log_file.name} 时出错: {e}")

        logger.info(f"[日志清理] 清理任务完成。共删除了 {deleted_count} 个过期的日志文件。")

    except Exception as e:
        logger.error(f"[日志清理] 执行日志清理任务时发生意外错误: {e}", exc_info=True)


class TaskScheduler:
    def __init__(self, sync_service: SyncService):
        self.scheduler = AsyncIOScheduler()
        self.sync_service = sync_service
    
    def should_run_task(self, task) -> bool:
        """
        判断任务是否应该运行（用于手动检查）
        :param task: 任务对象
        :return: 是否应该运行任务
        """
        sync_schedule = task.cron_schedule
        last_sync_time = task.last_sync_time
        
        if not sync_schedule or sync_schedule.lower() in ['关闭', 'off']:
            return False
            
        # 使用UTC时区
        from datetime import timezone
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        
        if not last_sync_time:
            return True
            
        try:
            last_sync = datetime.fromisoformat(last_sync_time.replace('Z', '+00:00')).replace(tzinfo=None)
        except ValueError:
            # 如果无法解析时间，假设从未同步过
            return True
            
        # 检查是否为预定义的调度计划
        if sync_schedule.lower() in ['每小时', 'hourly']:
            diff_hours = (now - last_sync).total_seconds() / 3600
            return diff_hours >= 1
        elif sync_schedule.lower() in ['每日', 'daily']:
            diff_hours = (now - last_sync).total_seconds() / 3600
            return diff_hours >= 24
        elif sync_schedule.lower() in ['每周', 'weekly']:
            diff_hours = (now - last_sync).total_seconds() / 3600
            return diff_hours >= 24 * 7
        elif sync_schedule.lower() in ['每月', 'monthly']:
            diff_hours = (now - last_sync).total_seconds() / 3600
            return diff_hours >= 24 * 30
        else:
            # 对于cron表达式，使用croniter来判断
            try:
                # 创建cron迭代器
                cron = croniter(sync_schedule, last_sync)
                # 获取下一次运行时间
                next_run = cron.get_next(datetime)
                # 检查是否应该运行
                return now >= next_run
            except Exception as e:
                logger.error(f"[调度器] 任务 #{task.id} 的调度表达式 \"{sync_schedule}\" 无效: {str(e)}")
                # 如果cron表达式无效，则使用简化的方法
                diff_hours = (now - last_sync).total_seconds() / 3600
                return diff_hours >= 1
    
    async def run_sync_task(self, task_id: int):
        """
        运行同步任务
        :param task_id: 任务ID
        """
        logger.info(f"[调度器] 任务 #{task_id} 符合运行条件，即将开始同步。")
        
        # 获取任务详情
        task = TaskService.get_task_by_id(task_id)
        if not task:
            logger.error(f"[调度器] 无法找到任务 #{task_id}")
            return
        
        # 将任务状态更新为“排队中”
        TaskService.update_task_status(task_id, 'queued', '任务已加入队列，等待同步...')
        logger.info(f"[调度器] 任务 #{task_id} 状态更新为 'queued'。")

        # 定义日志回调函数
        def log_callback(level: str, message: str):
            LogService.log_activity(task_id, level, message)
        
        # 执行同步
        try:
            # 伪代码/未来规划:
            # - 在一个更复杂的系统中, SyncService 实例可能需要根据
            #   task.server_id 动态创建或获取, 例如:
            #   sync_service = ServiceFactory.get_service(task.server_type)
            # - 但在当前架构下, SyncService 内部处理了多服务器逻辑, 所以保持不变。
            
            await self.sync_service.sync_playlist(
                task_id=task.id,
                server_id=task.server_id,
                playlist_url=task.playlist_url,
                platform=task.platform,
                playlist_name=task.name,
                log_callback=log_callback
            )
        except Exception as e:
            logger.error(f"[调度器] 任务 #{task_id} 同步失败: {str(e)}")
            LogService.log_activity(task_id, 'error', f'调度器同步失败: {str(e)}')
    
    def add_scheduled_jobs(self):
        """添加所有已调度的任务"""
        try:
            tasks = TaskService.get_all_tasks()
            for task in tasks:
                if task.status not in ['syncing', 'queued']:
                    sync_schedule = task.cron_schedule
                    if not sync_schedule or sync_schedule.lower() in ['关闭', 'off']:
                        continue
                    
                    # 检查是否为预定义的调度计划
                    if sync_schedule.lower() in ['每小时', 'hourly']:
                        # 每小时执行
                        self.scheduler.add_job(
                            self.run_sync_task,
                            'cron',
                            hour='*',
                            id=f'task_sync_{task.id}',
                            args=[task.id],
                            replace_existing=True
                        )
                    elif sync_schedule.lower() in ['每日', 'daily']:
                        # 每天凌晨2点执行
                        self.scheduler.add_job(
                            self.run_sync_task,
                            'cron',
                            hour=2,
                            minute=0,
                            id=f'task_sync_{task.id}',
                            args=[task.id],
                            replace_existing=True
                        )
                    elif sync_schedule.lower() in ['每周', 'weekly']:
                        # 每周日凌晨2点执行
                        self.scheduler.add_job(
                            self.run_sync_task,
                            'cron',
                            day_of_week=0,
                            hour=2,
                            minute=0,
                            id=f'task_sync_{task.id}',
                            args=[task.id],
                            replace_existing=True
                        )
                    elif sync_schedule.lower() in ['每月', 'monthly']:
                        # 每月1号凌晨2点执行
                        self.scheduler.add_job(
                            self.run_sync_task,
                            'cron',
                            day=1,
                            hour=2,
                            minute=0,
                            id=f'task_sync_{task.id}',
                            args=[task.id],
                            replace_existing=True
                        )
                    else:
                        # 尝试解析为cron表达式
                        try:
                            # 验证cron表达式是否有效
                            CronTrigger.from_crontab(sync_schedule)
                            # 添加cron作业
                            self.scheduler.add_job(
                                self.run_sync_task,
                                CronTrigger.from_crontab(sync_schedule),
                                id=f'task_sync_{task.id}',
                                args=[task.id],
                                replace_existing=True
                            )
                        except Exception as e:
                            logger.error(f"[调度器] 任务 #{task.id} 的调度表达式 \"{sync_schedule}\" 无效: {str(e)}")
                            # 如果cron表达式无效，则使用每小时检查的方式
                            self.scheduler.add_job(
                                self.check_and_run_task,
                                'interval',
                                minutes=1,
                                id=f'task_check_{task.id}',
                                args=[task.id],
                                replace_existing=True
                            )
        except Exception as e:
            logger.error(f"[调度器] 添加调度任务时出错: {str(e)}")
    
    async def check_and_run_task(self, task_id: int):
        """
        检查并运行任务（如果符合条件）
        :param task_id: 任务ID
        """
        task = TaskService.get_task_by_id(task_id)
        if task and self.should_run_task(task):
            await self.run_sync_task(task_id)
    
    def remove_task_from_schedule(self, task_id: int):
        """从调度器中移除任务"""
        job_id_sync = f'task_sync_{task_id}'
        job_id_check = f'task_check_{task_id}'
        
        if self.scheduler.get_job(job_id_sync):
            self.scheduler.remove_job(job_id_sync)
            logger.info(f"[调度器] 已移除同步作业: {job_id_sync}")
        
        if self.scheduler.get_job(job_id_check):
            self.scheduler.remove_job(job_id_check)
            logger.info(f"[调度器] 已移除检查作业: {job_id_check}")

    def reload_task_schedule(self, task_id: int):
        """
        重新加载任务调度
        :param task_id: 任务ID
        """
        try:
            # 移除旧的作业
            self.remove_task_from_schedule(task_id)
            
            # 添加新的作业
            task = TaskService.get_task_by_id(task_id)
            if task and task.status not in ['syncing', 'queued']:
                sync_schedule = task.cron_schedule
                if not sync_schedule or sync_schedule.lower() in ['关闭', 'off']:
                    return
                
                job_id_sync = f'task_sync_{task.id}'
                job_id_check = f'task_check_{task.id}'

                # 检查是否为预定义的调度计划
                if sync_schedule.lower() in ['每小时', 'hourly']:
                    # 每小时执行
                    self.scheduler.add_job(
                        self.run_sync_task,
                        'cron',
                        hour='*',
                        id=job_id_sync,
                        args=[task.id],
                        replace_existing=True
                    )
                elif sync_schedule.lower() in ['每日', 'daily']:
                    # 每天凌晨2点执行
                    self.scheduler.add_job(
                        self.run_sync_task,
                        'cron',
                        hour=2,
                        minute=0,
                        id=job_id_sync,
                        args=[task.id],
                        replace_existing=True
                    )
                elif sync_schedule.lower() in ['每周', 'weekly']:
                    # 每周日凌晨2点执行
                    self.scheduler.add_job(
                        self.run_sync_task,
                        'cron',
                        day_of_week=0,
                        hour=2,
                        minute=0,
                        id=job_id_sync,
                        args=[task.id],
                        replace_existing=True
                    )
                elif sync_schedule.lower() in ['每月', 'monthly']:
                    # 每月1号凌晨2点执行
                    self.scheduler.add_job(
                        self.run_sync_task,
                        'cron',
                        day=1,
                        hour=2,
                        minute=0,
                        id=job_id_sync,
                        args=[task.id],
                        replace_existing=True
                    )
                else:
                    # 尝试解析为cron表达式
                    try:
                        # 验证cron表达式是否有效
                        CronTrigger.from_crontab(sync_schedule)
                        # 添加cron作业
                        self.scheduler.add_job(
                            self.run_sync_task,
                            CronTrigger.from_crontab(sync_schedule),
                            id=job_id_sync,
                            args=[task.id],
                            replace_existing=True
                        )
                    except Exception as e:
                        logger.error(f"[调度器] 任务 #{task.id} 的调度表达式 \"{sync_schedule}\" 无效: {str(e)}")
                        # 如果cron表达式无效，则使用每小时检查的方式
                        self.scheduler.add_job(
                            self.check_and_run_task,
                            'interval',
                            minutes=1,
                            id=job_id_check,
                            args=[task.id],
                            replace_existing=True
                        )
        except Exception as e:
            logger.error(f"[调度器] 重新加载任务 #{task_id} 的调度时出错: {str(e)}")
    
    def start(self):
        """启动调度器"""
        logger.info("[调度器] 启动任务调度器...")
        self.add_scheduled_jobs()
        
        # 添加每日的日志清理任务
        self.scheduler.add_job(
            cleanup_old_download_logs,
            'cron',
            hour=4,  # 每天凌晨4点执行
            minute=0,
            id='cleanup_download_logs',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info("[调度器] 任务调度器已启动，并已安排日志清理任务。")
    
    def shutdown(self):
        """关闭调度器"""
        logger.info("[调度器] 关闭任务调度器...")
        self.scheduler.shutdown()
        logger.info("[调度器] 任务调度器已关闭。")

# 全局变量，用于存储 TaskScheduler 的单例
_scheduler_instance: "TaskScheduler" = None

def get_scheduler() -> "TaskScheduler":
    """依赖注入函数，用于获取 TaskScheduler 的单例。"""
    global _scheduler_instance
    if _scheduler_instance is None:
        # 这个分支理论上不应该在正常应用流程中被执行
        raise RuntimeError("TaskScheduler 尚未在应用启动时初始化。")
    return _scheduler_instance

def set_scheduler(instance: "TaskScheduler"):
    """在应用启动时设置调度器实例。"""
    global _scheduler_instance
    _scheduler_instance = instance