"""统一日志配置"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logger(name: str = 'flowkit', level: int = logging.INFO,
                 log_file: str = None, console: bool = True) -> logging.Logger:
    """配置并返回日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径（可选，默认为 logs/flowkit.log）
        console: 是否输出到控制台

    Returns:
        配置好的 Logger 实例
    """
    logger = logging.getLogger(name)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 控制台格式化器（简洁）
    console_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%H:%M:%S'
    )

    # 文件格式化器（详细）
    file_formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

    # 文件处理器
    if log_file is None:
        # 默认日志文件路径
        log_dir = Path(__file__).parent.parent.parent / 'logs'
        log_dir.mkdir(exist_ok=True)
        log_file = str(log_dir / 'flowkit.log')

    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3,  # 保留 3 个备份
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        logger.info(f"Log file: {log_file}")

    return logger


def get_logger(name: str) -> logging.Logger:
    """获取子模块日志记录器

    Args:
        name: 模块名称（会自动添加 'flowkit.' 前缀）

    Returns:
        Logger 实例
    """
    full_name = f'flowkit.{name}' if not name.startswith('flowkit.') else name
    return logging.getLogger(full_name)

