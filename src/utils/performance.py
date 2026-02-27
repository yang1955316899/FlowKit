"""性能监控工具"""

import time
from functools import wraps
from .logger import get_logger

logger = get_logger('performance')


def monitor_performance(threshold_ms: float = 100):
    """性能监控装饰器

    Args:
        threshold_ms: 超过此阈值（毫秒）时记录警告

    Usage:
        @monitor_performance(threshold_ms=100)
        def slow_function():
            time.sleep(0.2)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = (time.perf_counter() - start) * 1000
                if elapsed > threshold_ms:
                    logger.warning(
                        f"{func.__module__}.{func.__name__} took {elapsed:.1f}ms "
                        f"(threshold: {threshold_ms}ms)"
                    )
                else:
                    logger.debug(f"{func.__module__}.{func.__name__} took {elapsed:.1f}ms")
        return wrapper
    return decorator


class PerformanceTimer:
    """性能计时器上下文管理器

    Usage:
        with PerformanceTimer("database query"):
            # ... slow operation
            pass
    """

    def __init__(self, name: str, threshold_ms: float = 100):
        self.name = name
        self.threshold_ms = threshold_ms
        self.start_time = None
        self.elapsed_ms = 0

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_ms = (time.perf_counter() - self.start_time) * 1000
        if self.elapsed_ms > self.threshold_ms:
            logger.warning(
                f"{self.name} took {self.elapsed_ms:.1f}ms "
                f"(threshold: {self.threshold_ms}ms)"
            )
        else:
            logger.debug(f"{self.name} took {self.elapsed_ms:.1f}ms")
        return False
