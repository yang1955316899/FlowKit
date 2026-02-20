"""定时任务调度器"""

import threading
import time
from typing import Callable


class Scheduler:
    """后台任务调度器"""

    def __init__(self):
        self._tasks: list[tuple[Callable, int, bool]] = []
        self._running = False
        self._thread: threading.Thread | None = None

    def add(self, func: Callable, interval: int, immediate: bool = True):
        """添加定时任务"""
        self._tasks.append((func, interval, immediate))

    def start(self):
        """启动调度器"""
        self._running = True
        for func, interval, immediate in self._tasks:
            t = threading.Thread(
                target=self._loop,
                args=(func, interval, immediate),
                daemon=True
            )
            t.start()

    def _loop(self, func: Callable, interval: int, immediate: bool):
        """任务循环"""
        if immediate:
            try:
                func()
            except Exception:
                pass
        while self._running:
            time.sleep(interval)
            try:
                func()
            except Exception:
                pass

    def stop(self):
        """停止调度器"""
        self._running = False
