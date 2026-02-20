"""统计数字卡片组件"""

from tkinter import Canvas


class StatCard:
    """统计数字卡片"""

    def __init__(self, theme: dict):
        self.theme = theme

    def draw(self, canvas: Canvas, x: int, y: int, w: int, h: int,
             label: str, value: str, color: str = None):
        """绘制统计卡片"""
        c = self.theme
        color = color or c['accent']

        # 背景
        self._rounded_rect(canvas, x, y, x + w, y + h, 8, c['card'], c['border'])

        # 标签
        canvas.create_text(
            x + w // 2, y + 16,
            text=label, fill=c['dim'],
            font=('Segoe UI', 9)
        )

        # 数值
        canvas.create_text(
            x + w // 2, y + h - 16,
            text=value, fill=color,
            font=('Segoe UI', 13, 'bold')
        )

    def _rounded_rect(self, canvas: Canvas, x1: int, y1: int, x2: int, y2: int,
                      r: int, fill: str, outline: str):
        """绘制圆角矩形"""
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1, x1 + r, y1
        ]
        canvas.create_polygon(points, fill=fill, outline=outline, smooth=True)
