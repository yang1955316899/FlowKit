"""HTTP 客户端缓存管理"""

from typing import Callable, Any, Dict


class HttpClientCache:
    """HTTP 客户端实例缓存管理器"""

    def __init__(self):
        self._cache: Dict[str, Any] = {}

    def get(self, key: str, factory: Callable[[], Any]) -> Any:
        """获取或创建缓存实例

        Args:
            key: 缓存键
            factory: 工厂函数，用于创建新实例

        Returns:
            缓存的或新创建的实例
        """
        if key not in self._cache:
            self._cache[key] = factory()
        return self._cache[key]

    def invalidate(self, key: str = None):
        """清除缓存

        Args:
            key: 要清除的缓存键，None 表示清除所有
        """
        if key is None:
            self._cache.clear()
        else:
            self._cache.pop(key, None)

    def has(self, key: str) -> bool:
        """检查缓存是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        return key in self._cache

    def size(self) -> int:
        """获取缓存大小

        Returns:
            缓存项数量
        """
        return len(self._cache)
