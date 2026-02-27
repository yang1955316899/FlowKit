"""流程编排器 — Canvas 渲染引擎（视觉重设计）：彩色卡片、glow 选中、箭头连接线、点阵背景"""

from tkinter import Canvas, Frame
from ..widgets.draw import rrect
from ..dialogs.step_editor import STEP_TYPES
from ..dialogs.enhanced_combo_editor import _step_summary, _step_type_name, _step_icon


# 卡片尺寸
CARD_W = 200
CARD_H = 60
CARD_GAP = 24
CARD_R = 12
NEST_INDENT = 32
NEST_CARD_W = 180
COLOR_BAR_W = 4

# ── 步骤类型颜色映射 ──

STEP_CATEGORY_COLORS = {
    'delay': 'teal',
    'keys': 'lavender', 'type_text': 'lavender',
    'app': 'peach',
    'shell': 'mauve',
    'url': 'accent2', 'http_request': 'accent2', 'screenshot': 'accent2',
    'snippet': 'pink', 'toast': 'pink',
    'mouse_click': 'peach', 'mouse_move': 'peach',
    'mouse_double_click': 'peach', 'mouse_scroll': 'peach',
    'set_var': 'green', 'get_clipboard': 'green', 'set_clipboard': 'green',
    'file_read': 'green', 'file_write': 'green',
    'if_condition': 'mauve', 'loop': 'mauve',
    'wait_window': 'yellow', 'wait_pixel': 'yellow',
    'window_activate': 'yellow',
}

# glow 色映射（主题色 → glow 键名）
_GLOW_MAP = {
    'teal': 'teal_glow', 'peach': 'peach_glow', 'mauve': 'mauve_glow',
    'lavender': 'lavender_glow', 'pink': 'pink_glow', 'accent2': 'cyan_glow',
    'green': 'green_glow', 'yellow': 'yellow_glow',
}


def _get_step_color(theme: dict, stype: str) -> tuple[str, str]:
    """返回 (主题色, glow色) 元组"""
    color_key = STEP_CATEGORY_COLORS.get(stype, 'accent')
    main_color = theme.get(color_key, theme['accent'])
    glow_key = _GLOW_MAP.get(color_key, 'accent_glow')
    glow_color = theme.get(glow_key, theme['accent_glow'])
    return main_color, glow_color


class FlowCanvas:
    """Canvas 流程图渲染引擎 — 现代化视觉设计"""

    def __init__(self, parent: Frame, theme: dict, on_select=None):
        self.theme = theme
        self._f = theme['font']
        self._fm = theme['mono']
        self._on_select = on_select
        self._steps: list[dict] = []
        self._selected_idx: int | None = None
        self._card_positions: list[tuple] = []
        self._drag_idx: int | None = None
        self._drag_start = None
        self._drag_active = False
        self._scroll_y = 0

        self.canvas = Canvas(parent, bg=theme['bg'], highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)

        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_drag_end)
        self.canvas.bind('<MouseWheel>', self._on_scroll)

    def set_steps(self, steps: list[dict]):
        self._steps = steps
        self._selected_idx = None
        self.render()

    def render(self):
        self.canvas.delete('all')
        self._card_positions.clear()
        c = self.theme

        cw = self.canvas.winfo_width() or 500
        ch = self.canvas.winfo_height() or 600

        # ── 点阵网格背景 ──
        dot_color = c['border_subtle']
        for gx in range(0, max(cw, 1200), 24):
            for gy in range(0, max(ch, 1200), 24):
                dy = gy - (self._scroll_y % 24)
                self.canvas.create_oval(gx, dy, gx + 2, dy + 2,
                                        fill=dot_color, outline='')

        start_x = (cw - CARD_W) // 2
        y = 30 - self._scroll_y

        # ── 开始节点 — 加大 + 图标 + 彩色边框 ──
        sx1, sy1 = start_x + 40, y
        sx2, sy2 = start_x + CARD_W - 40, y + 40
        rrect(self.canvas, sx1, sy1, sx2, sy2, 20,
              fill=c.get('green_glow', c['accent_glow']),
              outline=c.get('green', c['accent']), width=2)
        self.canvas.create_text(start_x + CARD_W // 2, y + 20,
                                text="\u25b6  \u5f00\u59cb",
                                fill=c.get('green', c['accent']),
                                font=(self._f, 10, 'bold'))
        y += 40

        # ── 空状态引导 ──
        if not self._steps:
            ey = y + 80
            self.canvas.create_text(cw // 2, ey,
                                    text="\U0001f4cb",
                                    font=('Segoe UI Emoji', 28), fill=c['dim'])
            self.canvas.create_text(cw // 2, ey + 44,
                                    text="\u4ece\u5de6\u4fa7\u9762\u677f\u6dfb\u52a0\u6b65\u9aa4",
                                    font=(self._f, 10), fill=c['dim'])

        y = self._render_steps(self._steps, start_x, y, CARD_W, 0)

        # ── 结束节点 ──
        y += CARD_GAP
        ex1, ey1 = start_x + 40, y
        ex2, ey2 = start_x + CARD_W - 40, y + 40
        rrect(self.canvas, ex1, ey1, ex2, ey2, 20,
              fill=c.get('red_glow', c['accent_glow']),
              outline=c.get('red', '#f38ba8'), width=2)
        self.canvas.create_text(start_x + CARD_W // 2, y + 20,
                                text="\u25a0  \u7ed3\u675f",
                                fill=c.get('red', '#f38ba8'),
                                font=(self._f, 10, 'bold'))

        total_h = y + 80 + self._scroll_y
        self.canvas.configure(scrollregion=(0, 0, cw, total_h))

    def _render_steps(self, steps: list, x: int, y: int, card_w: int,
                       flat_offset: int) -> int:
        """递归渲染步骤列表，返回最终 y 坐标"""
        c = self.theme
        flat_idx = flat_offset

        for i, step in enumerate(steps):
            if not step:
                flat_idx += 1
                continue

            stype = step.get('type', '?')
            step_color, step_glow = _get_step_color(c, stype)

            # ── 连接线 + 箭头 ──
            y += CARD_GAP // 2
            cx = x + card_w // 2
            line_end = y + CARD_GAP // 2
            self.canvas.create_line(cx, y, cx, line_end,
                                     fill=c['border'], width=3, capstyle='round')
            # 小三角箭头
            aw = 5
            self.canvas.create_polygon(
                cx - aw, line_end - 2,
                cx + aw, line_end - 2,
                cx, line_end + 4,
                fill=c['border'], outline='')
            y = line_end

            # ── 卡片 ──
            is_selected = (flat_idx == self._selected_idx)

            if is_selected:
                # 外层 glow — 两层
                rrect(self.canvas, x - 4, y - 4, x + card_w + 4, y + CARD_H + 4,
                      CARD_R + 2, fill=step_glow, outline='')
                rrect(self.canvas, x - 2, y - 2, x + card_w + 2, y + CARD_H + 2,
                      CARD_R + 1, fill=step_glow, outline='')
                # 卡片本体
                rrect(self.canvas, x, y, x + card_w, y + CARD_H, CARD_R,
                      fill=c['card2'], outline=step_color, width=2)
            else:
                rrect(self.canvas, x, y, x + card_w, y + CARD_H, CARD_R,
                      fill=c['card'], outline=c['border_subtle'], width=1)

            # ── 左侧彩色竖条 ──
            bar_x = x + 1
            bar_y1 = y + CARD_R
            bar_y2 = y + CARD_H - CARD_R
            self.canvas.create_rectangle(bar_x, bar_y1, bar_x + COLOR_BAR_W, bar_y2,
                                          fill=step_color, outline='')

            # ── 图标 ──
            icon = _step_icon(stype)
            self.canvas.create_text(x + 18, y + CARD_H // 2, text=icon,
                                     font=('Segoe UI Emoji', 14), anchor='w',
                                     fill=c['text'])

            # ── 类型名（步骤专属颜色）──
            self.canvas.create_text(x + 44, y + 16, text=_step_type_name(stype),
                                     font=(self._f, 9, 'bold'), anchor='w',
                                     fill=step_color)

            # ── 摘要 ──
            summary = _step_summary(step)
            if summary:
                disp = summary[:24] + ('...' if len(summary) > 24 else '')
                self.canvas.create_text(x + 44, y + 38, text=disp,
                                         font=(self._f, 8), anchor='w',
                                         fill=c['sub'])

            self._card_positions.append((x, y, card_w, CARD_H, step, flat_idx))
            y += CARD_H
            flat_idx += 1

            # ── 嵌套块 ──
            if stype == 'if_condition':
                then_steps = step.get('then_steps', [])
                else_steps = step.get('else_steps', [])

                y += 8
                self.canvas.create_text(x + NEST_INDENT, y + 10, text="then",
                                         font=(self._f, 8, 'bold'), anchor='w',
                                         fill=c.get('green', c['accent']))
                y += 20

                if then_steps:
                    y = self._render_steps(then_steps, x + NEST_INDENT, y,
                                            NEST_CARD_W, flat_idx)
                    flat_idx += self._count_steps(then_steps)

                y += 8
                self.canvas.create_text(x + NEST_INDENT, y + 10, text="else",
                                         font=(self._f, 8, 'bold'), anchor='w',
                                         fill=c.get('yellow', '#f9e2af'))
                y += 20

                if else_steps:
                    y = self._render_steps(else_steps, x + NEST_INDENT, y,
                                            NEST_CARD_W, flat_idx)
                    flat_idx += self._count_steps(else_steps)

            elif stype == 'loop':
                body_steps = step.get('body_steps', [])

                y += 8
                self.canvas.create_text(x + NEST_INDENT, y + 10, text="body",
                                         font=(self._f, 8, 'bold'), anchor='w',
                                         fill=c['accent'])
                y += 20

                if body_steps:
                    y = self._render_steps(body_steps, x + NEST_INDENT, y,
                                            NEST_CARD_W, flat_idx)
                    flat_idx += self._count_steps(body_steps)

                loop_x = x + card_w + 12
                self.canvas.create_line(loop_x, y, loop_x, y - 30,
                                         fill=c['accent'], width=2, dash=(4, 4))

        return y

    def _count_steps(self, steps: list) -> int:
        """递归计算步骤总数"""
        count = 0
        for step in steps:
            if not step:
                count += 1
                continue
            count += 1
            stype = step.get('type', '')
            if stype == 'if_condition':
                count += self._count_steps(step.get('then_steps', []))
                count += self._count_steps(step.get('else_steps', []))
            elif stype == 'loop':
                count += self._count_steps(step.get('body_steps', []))
        return count

    def _on_click(self, event):
        clicked = self._hit_test(event.x, event.y + self._scroll_y)
        if clicked is not None:
            self._selected_idx = clicked[5]
            self._drag_idx = clicked[5]
            self._drag_start = (event.x, event.y)
            self._drag_active = False
            self.render()
            if self._on_select:
                self._on_select(clicked[4], clicked[5])
        else:
            self._selected_idx = None
            self._drag_idx = None
            self.render()
            if self._on_select:
                self._on_select(None, None)

    def _on_drag(self, event):
        if self._drag_idx is None or self._drag_start is None:
            return
        dx = abs(event.x - self._drag_start[0])
        dy = abs(event.y - self._drag_start[1])
        if not self._drag_active and (dx > 8 or dy > 8):
            self._drag_active = True

    def _on_drag_end(self, event):
        if self._drag_active and self._drag_idx is not None:
            target = self._hit_test(event.x, event.y + self._scroll_y)
            if target and target[5] != self._drag_idx:
                self._swap_flat(self._drag_idx, target[5])
        self._drag_idx = None
        self._drag_start = None
        self._drag_active = False

    def _swap_flat(self, src_flat: int, dst_flat: int):
        """在顶层步骤列表中交换（仅支持顶层）"""
        if src_flat < len(self._steps) and dst_flat < len(self._steps):
            self._steps[src_flat], self._steps[dst_flat] = \
                self._steps[dst_flat], self._steps[src_flat]
            self.render()

    def _on_scroll(self, event):
        delta = -event.delta // 120 * 40
        self._scroll_y = max(0, self._scroll_y + delta)
        self.render()

    def _hit_test(self, x: int, y: int):
        """检测点击了哪个卡片"""
        for pos in self._card_positions:
            px, py, pw, ph = pos[0], pos[1], pos[2], pos[3]
            if px <= x <= px + pw and py <= y <= py + ph:
                return pos
        return None
