"""视图基类"""

from abc import ABC, abstractmethod
from tkinter import Canvas


class BaseView(ABC):
    """所有视图的抽象基类"""

    def __init__(self, app):
        self.app = app
        self.theme = app.theme
        self._f = app.theme['font']
        self._fm = app.theme['mono']

    @abstractmethod
    def render(self, canvas: Canvas, w: int, y: int) -> int:
        """渲染视图内容，返回最终 y 坐标"""
        pass

    @abstractmethod
    def on_click(self, canvas: Canvas, event, tags: list[str]) -> bool:
        """处理点击事件，返回 True 表示已处理"""
        pass

    def on_scroll(self, event):
        """处理鼠标滚轮事件，子类可选覆盖"""
        pass
