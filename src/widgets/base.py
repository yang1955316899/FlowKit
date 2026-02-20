"""卡片基类"""

from abc import ABC, abstractmethod
from tkinter import Canvas
from typing import Any


class BaseCard(ABC):
    """卡片基类"""

    def __init__(self, title: str, config: dict, theme: dict):
        self.title = title
        self.config = config
        self.theme = theme
        self.refresh_interval = config.get('refresh', 30)
        self.height = 0  # 由子类设置
        self._data: dict = {}

    @abstractmethod
    def fetch_data(self) -> dict[str, Any] | None:
        """获取数据，子类实现"""
        pass

    @abstractmethod
    def render(self, canvas: Canvas, x: int, y: int, w: int) -> int:
        """渲染卡片，返回卡片高度"""
        pass

    def update(self, data: dict):
        """更新数据"""
        self._data = data
