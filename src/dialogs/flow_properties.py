"""流程编排器 — 右侧属性面板"""

from tkinter import Frame, Label
from .step_editor import StepEditor


class FlowProperties:
    """右侧属性面板 — 显示选中步骤的属性"""

    def __init__(self, parent: Frame, theme: dict, on_update=None):
        self.theme = theme
        self._f = theme['font']
        self._fm = theme['mono']
        self._on_update = on_update
        self._selected_step = None
        self._selected_index = None

        self.frame = Frame(parent, bg=theme['bg'], width=160)
        self.frame.pack(side='right', fill='y')
        self.frame.pack_propagate(False)

        Label(self.frame, text="属性", fg=theme['sub'], bg=theme['bg'],
              font=(self._f, 8, 'bold')).pack(padx=8, pady=(8, 4), anchor='w')

        self._info_frame = Frame(self.frame, bg=theme['bg'])
        self._info_frame.pack(fill='both', expand=True, padx=8)

        self._hint = Label(self._info_frame, text="选择步骤\n查看属性",
                            fg=theme['dim'], bg=theme['bg'],
                            font=(self._f, 8), justify='center')
        self._hint.pack(expand=True)

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
                  font=(self._f, 8), justify='center').pack(expand=True)
            return

        step = self._selected_step
        c = self.theme

        # 类型
        Label(self._info_frame, text=f"类型: {step.get('type', '?')}",
              fg=c['accent'], bg=c['bg'],
              font=(self._fm, 7, 'bold')).pack(anchor='w', pady=(0, 4))

        # 显示所有属性
        skip_keys = {'type', 'then_steps', 'else_steps', 'body_steps', 'condition'}
        for key, val in step.items():
            if key in skip_keys:
                continue
            if isinstance(val, (str, int, float)):
                text = f"{key}: {val}"
                if len(text) > 24:
                    text = text[:24] + '...'
                Label(self._info_frame, text=text, fg=c['sub'], bg=c['bg'],
                      font=(self._fm, 6), anchor='w').pack(anchor='w', pady=1)

        # 条件详情
        cond = step.get('condition')
        if cond:
            Label(self._info_frame, text="条件:", fg=c['dim'], bg=c['bg'],
                  font=(self._fm, 6, 'bold')).pack(anchor='w', pady=(4, 0))
            for k, v in cond.items():
                if v:
                    Label(self._info_frame, text=f"  {k}: {v}",
                          fg=c['sub'], bg=c['bg'],
                          font=(self._fm, 6)).pack(anchor='w')

        # 编辑按钮
        edit_btn = Label(self._info_frame, text="✎ 编辑", fg=c['accent'],
                         bg=c['card2'], font=(self._f, 8), cursor='hand2',
                         padx=8, pady=3)
        edit_btn.pack(fill='x', pady=(8, 0))
        edit_btn.bind('<Button-1>', lambda e: self._edit_step())

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
