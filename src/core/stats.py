"""动作使用统计"""

import json
import time
from pathlib import Path


class ActionStats:
    """记录动作执行次数和最后执行时间"""

    def __init__(self, data_path: str = None):
        self._path = data_path or str(
            Path(__file__).parent.parent.parent / '.action_stats.json')
        self._data: dict[str, dict] = {}
        self._load()

    def _load(self):
        try:
            with open(self._path, 'r', encoding='utf-8') as f:
                self._data = json.load(f)
        except Exception:
            self._data = {}

    def _save(self):
        try:
            with open(self._path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def record(self, action_id: str):
        """记录一次执行"""
        if not action_id:
            return
        entry = self._data.setdefault(action_id, {'count': 0, 'last': 0})
        entry['count'] = entry.get('count', 0) + 1
        entry['last'] = time.time()
        self._save()

    def get(self, action_id: str) -> dict:
        """获取单个动作的统计 {'count': int, 'last': float}"""
        return self._data.get(action_id, {'count': 0, 'last': 0})

    def get_all(self) -> dict[str, dict]:
        """获取所有统计数据"""
        return dict(self._data)

    def top(self, n: int = 10) -> list[tuple[str, int]]:
        """按执行次数排序，返回 top N [(action_id, count), ...]"""
        items = [(k, v.get('count', 0)) for k, v in self._data.items()]
        items.sort(key=lambda x: x[1], reverse=True)
        return items[:n]

    def total_count(self) -> int:
        """总执行次数"""
        return sum(v.get('count', 0) for v in self._data.values())
