"""流程编排器 — 右侧属性面板（重新设计）"""

from tkinter import Frame, Label, Canvas, Scrollbar
from ..widgets.draw import rrect
from .step_editor import StepEditor
from .flow_canvas import _get_step_color


class FlowProperties:
    """右侧属性面板 — 显示选中步骤的属性"""

    def __init__(self, parent: Frame, theme: dict, on_update=None):
        self.theme = theme
        self._f = theme['font']
        self._fm = theme['mono']
        self._on_update = on_update
        self._selected_step = None
        self._selected_index = None

        self.frame = Frame(parent, bg=theme['bg'], width=220)
        self.frame.pack(side='right', fill='y')
        self.frame.pack_propagate(False)

        # 标题
        title_frame = Frame(self.frame, bg=theme['bg'])
        title_frame.pack(fill='x', padx=12, pady=(12, 8))
        Label(title_frame, text="属性", fg=theme['text'], bg=theme['bg'],
              font=(self._f, 10, 'bold')).pack(anchor='w')

        # 滚动区域
        scroll_frame = Frame(self.frame, bg=theme['bg'])
        scroll_frame.pack(fill='both', expand=True, padx=8)

        self._canvas = Canvas(scroll_frame, bg=theme['bg'], highlightthickness=0)
        scrollbar = Scrollbar(scroll_frame, orient='vertical', command=self._canvas.yview)
        self._info_frame = Frame(self._canvas, bg=theme['bg'])

        self._info_frame.bind('<Configure>',
                              lambda e: self._canvas.configure(scrollregion=self._canvas.bbox('all')))
        self._canvas.create_window((0, 0), window=self._info_frame, anchor='nw')
        self._canvas.configure(yscrollcommand=scrollbar.set)

        self._canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # 鼠标滚轮
        self._canvas.bind('<Enter>',
                          lambda e: self._canvas.bind_all('<MouseWheel>', lambda ev: self._canvas.yview_scroll(-1 * (ev.delta // 120), 'units')))
        self._canvas.bind('<Leave>',
                          lambda e: self._canvas.unbind_all('<MouseWheel>'))

        # 初始提示
        self._hint = Label(self._info_frame, text="选择步骤\n查看属性",
                           fg=theme['dim'], bg=theme['bg'],
                           font=(self._f, 9), justify='center')
        self._hint.pack(expand=True, pady=40)

    def show_step(self, step: dict, index: int):
        """显示步骤属性"""
        self._selected_step = step
        self._selected_index = index
        self._refresh()

    def clear(self):
        self._selected_step = None
        self._selected_index = None
        self._refresh()

    def _refresh(self):
        for w in self._info_frame.winfo_children():
            w.destroy()

        if not self._selected_step:
            Label(self._info_frame, text="选择步骤\n查看属性",
                  fg=self.theme['dim'], bg=self.theme['bg'],
                  font=(self._f, 9), justify='center').pack(expand=True, pady=40)
            return

        step = self._selected_step
        c = self.theme

        # 类型卡片
        stype = step.get('type', '?')
        step_color, _ = _get_step_color(c, stype)

        type_card = Frame(self._info_frame, bg=c['card'],
                          highlightbackground=c['border_subtle'], highlightthickness=1)
        type_card.pack(fill='x', pady=(0, 8))

        Label(type_card, text="类型", fg=c['dim'], bg=c['card'],
              font=(self._f, 7)).pack(anchor='w', padx=10, pady=(8, 2))
        Label(type_card, text=stype, fg=step_color, bg=c['card'],
              font=(self._fm, 10, 'bold')).pack(anchor='w', padx=10, pady=(0, 8))

        # 属性列表
        skip_keys = {'type', 'then_steps', 'else_steps', 'body_steps', 'condition'}
        for key, val in step.items():
            if key in skip_keys:
                continue
            if isinstance(val, (str, int, float, bool)):
                self._draw_property(key, str(val))

        # 条件详情
        cond = step.get('condition')
        if cond:
            cond_card = Frame(self._info_frame, bg=c['card'],
                              highlightbackground=c['border_subtle'], highlightthickness=1)
            cond_card.pack(fill='x', pady=(0, 8))

            Label(cond_card, text="条件", fg=c['dim'], bg=c['card'],
                  font=(self._f, 7)).pack(anchor='w', padx=10, pady=(8, 4))
            for k, v in cond.items():
                if v:
                    Label(cond_card, text=f"{k}: {v}", fg=c['sub'], bg=c['card'],
                          font=(self._fm, 8)).pack(anchor='w', padx=10, pady=1)
            Label(cond_card, text="", bg=c['card']).pack(pady=4)  # padding

        # 编辑按钮 — 更大更醒目
        edit_btn = Label(self._info_frame, text="✎ 编辑步骤", fg='#fff',
                         bg=c['accent'], font=(self._f, 10, 'bold'), cursor='hand2',
                         padx=12, pady=8)
        edit_btn.pack(fill='x', pady=(8, 0))
        edit_btn.bind('<Button-1>', lambda e: self._edit_step())

    def _draw_property(self, key: str, value: str):
        """绘制单个属性"""
        c = self.theme
        prop_card = Frame(self._info_frame, bg=c['card'],
                          highlightbackground=c['border_subtle'], highlightthickness=1)
        prop_card.pack(fill='x', pady=(0, 4))

        Label(prop_card, text=key, fg=c['dim'], bg=c['card'],
              font=(self._f, 7)).pack(anchor='w', padx=10, pady=(6, 2))

        # 值可能很长，需要换行
        disp = value if len(value) <= 30 else value[:30] + '...'
        Label(prop_card, text=disp, fg=c['text'], bg=c['card'],
              font=(self._fm, 8), anchor='w', wraplength=180).pack(anchor='w', padx=10, pady=(0, 6))

    def _edit_step(self):
        if not self._selected_step:
            return
        parent = self.frame.winfo_toplevel()
        result = StepEditor(parent, self.theme, step=self._selected_step,
                            step_type=self._selected_step.get('type')).show()
        if result and self._on_update and self._selected_index is not None:
            # 保留嵌套步骤
            old = self._selected_step
            if old.get('type') == 'if_condition':
                result.setdefault('then_steps', old.get('then_steps', []))
                result.setdefault('else_steps', old.get('else_steps', []))
            elif old.get('type') == 'loop':
                result.setdefault('body_steps', old.get('body_steps', []))
            self._on_update(self._selected_index, result)
            self._selected_step = result
            self._refresh()
