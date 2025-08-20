"""文件质量检测服务"""

import os
import logging
from pathlib import Path
from mutagen import File
from services.download.download_constants import MIN_FILE_SIZE_MB, MIN_DURATION_SECONDS

# Configure a dedicated logger for low-quality downloads
low_quality_logger = logging.getLogger('low_quality_downloads')
low_quality_logger.propagate = False  # Prevent propagation to root logger

class QualityChecker:
    """检查下载文件质量是否符合标准"""
    
    def is_file_acceptable(self, file_path: str, log: logging.Logger) -> bool:
        """
        Checks if a downloaded audio file meets quality standards.
        """
        try:
            # Check 1: File Size
            file_size_bytes = os.path.getsize(file_path)
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            if file_size_mb < MIN_FILE_SIZE_MB:
                log.warning(f"文件 '{Path(file_path).name}' 被标记为低质量: 文件大小 ({file_size_mb:.2f} MB) 小于阈值 ({MIN_FILE_SIZE_MB} MB)。")
                low_quality_logger.info(
                    "低质量文件: 文件过小",
                    extra={
                        "file_path": file_path,
                        "file_name": Path(file_path).name,
                        "check_type": "file_size",
                        "file_size_mb": file_size_mb,
                        "threshold_mb": MIN_FILE_SIZE_MB
                    }
                )
                return False
                
            # Check 2: Duration
            try:
                audio = File(file_path)
                if audio is not None and hasattr(audio, 'info') and audio.info is not None:
                    duration = audio.info.length
                    if duration < MIN_DURATION_SECONDS:
                        log.warning(f"文件 '{Path(file_path).name}' 被标记为低质量: 时长 ({duration:.2f} 秒) 小于阈值 ({MIN_DURATION_SECONDS} 秒)。")
                        low_quality_logger.info(
                            "低质量文件: 时长过短",
                            extra={
                                "file_path": file_path,
                                "file_name": Path(file_path).name,
                                "check_type": "duration",
                                "duration_seconds": duration,
                                "threshold_seconds": MIN_DURATION_SECONDS
                            }
                        )
                        return False
                else:
                    log.warning(f"无法读取文件 '{Path(file_path).name}' 的元数据以检查时长。")
                    low_quality_logger.info(
                        "低质量文件: 无法读取元数据",
                        extra={
                            "file_path": file_path,
                            "file_name": Path(file_path).name,
                            "check_type": "metadata_unreadable"
                        }
                    )
                    return False
            except Exception as e:
                log.warning(f"检查文件时长时出错: {e}")
                low_quality_logger.info(
                    "低质量文件: 时长检查异常",
                    extra={
                        "file_path": file_path,
                        "file_name": Path(file_path).name,
                        "check_type": "duration_check_error",
                        "error": str(e)
                    }
                )
                return False
                
            # If all checks pass
            log.info(f"文件 '{Path(file_path).name}' 通过了质量检查。")
            return True
            
        except OSError as e:
            log.error(f"检查文件 '{file_path}' 时发生系统错误: {e}")
            return False
        except Exception as e:
            log.error(f"检查文件 '{file_path}' 时发生未知错误: {e}", exc_info=True)
            return False