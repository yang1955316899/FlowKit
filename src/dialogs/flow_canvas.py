"""流程编排器 — Canvas 渲染引擎：步骤卡片、连接线、拖拽"""

from tkinter import Canvas, Frame
from ..widgets.draw import rrect
from ..dialogs.step_editor import STEP_TYPES
from ..dialogs.enhanced_combo_editor import _step_summary, _step_type_name, _step_icon


# 卡片尺寸
CARD_W = 140
CARD_H = 40
CARD_GAP = 16
CARD_R = 8
NEST_INDENT = 24
NEST_CARD_W = 120


class FlowCanvas:
    """Canvas 流程图渲染引擎"""

    def __init__(self, parent: Frame, theme: dict, on_select=None):
        self.theme = theme
        self._f = theme['font']
        self._fm = theme['mono']
        self._on_select = on_select
        self._steps: list[dict] = []
        self._selected_idx: int | None = None
        self._card_positions: list[tuple] = []  # (x, y, w, h, step_ref, flat_idx)
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

        cw = self.canvas.winfo_width() or 400
        start_x = (cw - CARD_W) // 2
        y = 20 - self._scroll_y

        # 开始节点
        rrect(self.canvas, start_x + 30, y, start_x + CARD_W - 30, y + 24, 12,
              fill=c['green_glow'])
        self.canvas.create_text(start_x + CARD_W // 2, y + 12, text="开始",
                                 fill=c['green'], font=(self._f, 7, 'bold'))
        y += 24

        y = self._render_steps(self._steps, start_x, y, CARD_W, 0)

        # 结束节点
        y += CARD_GAP
        rrect(self.canvas, start_x + 30, y, start_x + CARD_W - 30, y + 24, 12,
              fill=c['red_glow'] if 'red_glow' in c else c.get('accent_glow', '#1e1e3e'))
        self.canvas.create_text(start_x + CARD_W // 2, y + 12, text="结束",
                                 fill=c.get('red', '#f38ba8'),
                                 font=(self._f, 7, 'bold'))

        # 更新滚动区域
        total_h = y + 40 + self._scroll_y
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

            # 连接线
            y += CARD_GAP // 2
            cx = x + card_w // 2
            self.canvas.create_line(cx, y, cx, y + CARD_GAP // 2,
                                     fill=c['border_subtle'], width=2)
            y += CARD_GAP // 2

            # 卡片
            is_selected = (flat_idx == self._selected_idx)
            outline = c['accent'] if is_selected else c['border_subtle']
            fill = c['accent_glow'] if is_selected else c['card']

            rrect(self.canvas, x, y, x + card_w, y + CARD_H, CARD_R,
                  fill=fill, outline=outline, width=1)

            # 图标 + 类型名
            icon = _step_icon(stype)
            self.canvas.create_text(x + 8, y + CARD_H // 2, text=icon,
                                     font=('Segoe UI Emoji', 8), anchor='w',
                                     fill=c['text'])
            self.canvas.create_text(x + 24, y + 10, text=_step_type_name(stype),
                                     font=(self._fm, 6, 'bold'), anchor='w',
                                     fill=c['accent'])

            # 摘要
            summary = _step_summary(step)
            if summary:
                disp = summary[:16] + ('...' if len(summary) > 16 else '')
                self.canvas.create_text(x + 24, y + 26, text=disp,
                                         font=(self._f, 6), anchor='w',
                                         fill=c['sub'])

            # 记录位置
            self._card_positions.append((x, y, card_w, CARD_H, step, flat_idx))
            y += CARD_H
            flat_idx += 1

            # 嵌套块
            if stype == 'if_condition':
                then_steps = step.get('then_steps', [])
                else_steps = step.get('else_steps', [])

                # then 分支标签
                y += 4
                self.canvas.create_text(x + NEST_INDENT, y + 8, text="then",
                                         font=(self._fm, 6, 'bold'), anchor='w',
                                         fill=c['green'])
                y += 14

                if then_steps:
                    y = self._render_steps(then_steps, x + NEST_INDENT, y,
                                            NEST_CARD_W, flat_idx)
                    flat_idx += self._count_steps(then_steps)

                # else 分支标签
                y += 4
                self.canvas.create_text(x + NEST_INDENT, y + 8, text="else",
                                         font=(self._fm, 6, 'bold'), anchor='w',
                                         fill=c.get('yellow', '#f9e2af'))
                y += 14

                if else_steps:
                    y = self._render_steps(else_steps, x + NEST_INDENT, y,
                                            NEST_CARD_W, flat_idx)
                    flat_idx += self._count_steps(else_steps)

            elif stype == 'loop':
                body_steps = step.get('body_steps', [])

                y += 4
                self.canvas.create_text(x + NEST_INDENT, y + 8, text="body",
                                         font=(self._fm, 6, 'bold'), anchor='w',
                                         fill=c['accent'])
                y += 14

                if body_steps:
                    y = self._render_steps(body_steps, x + NEST_INDENT, y,
                                            NEST_CARD_W, flat_idx)
                    flat_idx += self._count_steps(body_steps)

                # 循环回线
                loop_x = x + card_w + 8
                self.canvas.create_line(loop_x, y, loop_x, y - 20,
                                         fill=c['accent'], width=1, dash=(3, 3))

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
            self._selected_idx = clicked[5]  # flat_idx
            self._drag_idx = clicked[5]
            self._drag_start = (event.x, event.y)
            self._drag_active = False
            self.render()
            if self._on_select:
                self._on_select(clicked[4], clicked[5])  # step, flat_idx
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
        delta = -event.delta // 120 * 30
        self._scroll_y = max(0, self._scroll_y + delta)
        self.render()

    def _hit_test(self, x: int, y: int):
        """检测点击了哪个卡片"""
        for pos in self._card_positions:
            px, py, pw, ph = pos[0], pos[1], pos[2], pos[3]
            if px <= x <= px + pw and py <= y <= py + ph:
                return pos
        return None
