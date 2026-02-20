"""进度条卡片组件"""

from tkinter import Canvas


class ProgressCard:
    """进度条卡片"""

    def __init__(self, theme: dict):
        self.theme = theme

    def draw(self, canvas: Canvas, x: int, y: int, w: int, h: int,
             label: str, value: float, max_val: float = 100,
             show_percent: bool = True):
        """绘制进度条卡片"""
        c = self.theme
        percent = min(value / max_val, 1.0) if max_val > 0 else 0

        # 背景
        self._rounded_rect(canvas, x, y, x + w, y + h, 8, c['card'], c['border'])

        # 标签
        canvas.create_text(
            x + 12, y + h // 2,
            text=label, fill=c['text'],
            font=('Segoe UI', 9), anchor='w'
        )

        # 进度条背景
        bar_x = x + 100
        bar_w = w - 160
        bar_h = 8
        bar_y = y + (h - bar_h) // 2

        canvas.create_rectangle(
            bar_x, bar_y, bar_x + bar_w, bar_y + bar_h,
            fill=c['grid'], outline=''
        )

        # 进度条填充
        fill_w = int(bar_w * percent)
        color = self._get_color(percent)
        if fill_w > 0:
            canvas.create_rectangle(
                bar_x, bar_y, bar_x + fill_w, bar_y + bar_h,
                fill=color, outline=''
            )

        # 百分比文字
        if show_percent:
            canvas.create_text(
                x + w - 12, y + h // 2,
                text=f"{int(percent * 100)}%",
                fill=color, font=('Segoe UI', 9, 'bold'),
                anchor='e'
            )

    def _get_color(self, percent: float) -> str:
        """根据百分比返回颜色"""
        c = self.theme
        if percent >= 0.9:
            return c['red']
        if percent >= 0.7:
            return c['yellow']
        return c['green']

    def _rounded_rect(self, canvas: Canvas, x1: int, y1: int, x2: int, y2: int,
                      r: int, fill: str, outline: str):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1, x1 + r, y1
        ]
        canvas.create_polygon(points, fill=fill, outline=outline, smooth=True)
