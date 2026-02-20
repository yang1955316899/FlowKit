"""图表卡片组件"""

from tkinter import Canvas


class ChartCard:
    """柱状图卡片"""

    def __init__(self, theme: dict):
        self.theme = theme

    def draw_bar_chart(self, canvas: Canvas, x: int, y: int, w: int, h: int,
                       data: list[dict], title: str = ""):
        """绘制柱状图"""
        c = self.theme

        # 背景
        self._rounded_rect(canvas, x, y, x + w, y + h, 8, c['card'], c['border'])

        if title:
            canvas.create_text(
                x + 12, y + 16,
                text=title, fill=c['text'],
                font=('Segoe UI', 10, 'bold'),
                anchor='w'
            )

        if not data:
            return

        # 图表区域
        chart_x = x + 35
        chart_y = y + 35
        chart_w = w - 50
        chart_h = h - 60

        # 计算最大值
        max_val = max((d.get('value', 0) for d in data), default=1) or 1

        # 绘制网格线
        for i in range(5):
            gy = chart_y + chart_h - (i * chart_h // 4)
            canvas.create_line(
                chart_x, gy, chart_x + chart_w, gy,
                fill=c['grid'], dash=(2, 2)
            )
            # Y轴标签
            label = self._format_num(max_val * i // 4)
            canvas.create_text(
                chart_x - 5, gy,
                text=label, fill=c['dim'],
                font=('Segoe UI', 7), anchor='e'
            )

        # 绘制柱子
        bar_count = len(data)
        if bar_count == 0:
            return

        bar_w = max(4, (chart_w - 10) // bar_count - 2)
        gap = (chart_w - bar_w * bar_count) // (bar_count + 1)

        for i, d in enumerate(data):
            val = d.get('value', 0)
            bar_h = int((val / max_val) * chart_h) if max_val > 0 else 0
            bx = chart_x + gap + i * (bar_w + gap)
            by = chart_y + chart_h - bar_h

            if bar_h > 0:
                canvas.create_rectangle(
                    bx, by, bx + bar_w, chart_y + chart_h,
                    fill=c['accent'], outline=''
                )

            # X轴标签
            label = d.get('label', '')
            if i % 3 == 0:  # 每3个显示一个标签
                canvas.create_text(
                    bx + bar_w // 2, chart_y + chart_h + 10,
                    text=label, fill=c['dim'],
                    font=('Segoe UI', 7)
                )

    def _format_num(self, n: int) -> str:
        if n >= 1_000_000:
            return f"{n // 1_000_000}M"
        if n >= 1_000:
            return f"{n // 1_000}K"
        return str(n)

    def _rounded_rect(self, canvas: Canvas, x1: int, y1: int, x2: int, y2: int,
                      r: int, fill: str, outline: str):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1, x2, y1 + r,
            x2, y2 - r, x2, y2, x2 - r, y2, x1 + r, y2,
            x1, y2, x1, y2 - r, x1, y1 + r, x1, y1, x1 + r, y1
        ]
        canvas.create_polygon(points, fill=fill, outline=outline, smooth=True)
