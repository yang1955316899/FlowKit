"""动作使用统计"""

import json
import time
import threading
from pathlib import Path
from typing import Dict, List, Tuple


class ActionStats:
    """记录动作执行次数和最后执行时间"""

    def __init__(self, data_path: str = None):
        self._path: str = data_path or str(
            Path(__file__).parent.parent.parent / '.action_stats.json')
        self._data: Dict[str, Dict[str, int | float]] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        try:
            with open(self._path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        except Exception:
            self._data = {}

    def _save(self) -> None:
        try:
            with open(self._path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def record(self, action_id: str) -> None:
        """记录一次执行"""
        if not action_id:
            return
        with self._lock:
            entry = self._data.setdefault(action_id, {'count': 0, 'last': 0})
            entry['count'] = entry.get('count', 0) + 1
            entry['last'] = time.time()
            self._save()

    def get(self, action_id: str) -> Dict[str, int | float]:
        """获取单个动作的统计 {'count': int, 'last': float}"""
        with self._lock:
            return self._data.get(action_id, {'count': 0, 'last': 0}).copy()

    def get_all(self) -> Dict[str, Dict[str, int | float]]:
        """获取所有统计数据"""
        with self._lock:
            return {k: v.copy() for k, v in self._data.items()}

    def top(self, n: int = 10) -> List[Tuple[str, int]]:
        """按执行次数排序，返回 top N [(action_id, count), ...]"""
        with self._lock:
            items = [(k, v.get('count', 0)) for k, v in self._data.items()]
        items.sort(key=lambda x: x[1], reverse=True)
        return items[:n]

    def total_count(self) -> int:
        """总执行次数"""
        with self._lock:
            return sum(v.get('count', 0) for v in self._data.values())

    def cleanup_old_entries(self, days: int = 90) -> int:
        """清理 N 天前的统计数据

        Args:
            days: 保留最近 N 天的数据

        Returns:
            清理的条目数
        """
        cutoff = time.time() - (days * 86400)
        with self._lock:
            old_count = len(self._data)
            self._data = {
                k: v for k, v in self._data.items()
                if v.get('last', 0) > cutoff
            }
            removed = old_count - len(self._data)
            if removed > 0:
                self._save()
        return removed
