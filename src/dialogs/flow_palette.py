"""流程编排器 — 左侧步骤面板，可拖入画布"""

from tkinter import Frame, Label, Canvas
from ..dialogs.step_editor import STEP_TYPES


# 步骤分类
PALETTE_CATEGORIES = [
    ('基础', [
        ('delay', '延迟', '⏱'),
        ('keys', '按键', '⌨'),
        ('app', '应用', '📂'),
        ('shell', '命令', '💻'),
        ('url', '网址', '🌐'),
        ('snippet', '文本', '📄'),
    ]),
    ('鼠标', [
        ('mouse_click', '点击', '🖱'),
        ('mouse_move', '移动', '↗'),
    ]),
    ('变量', [
        ('set_var', '赋值', '📝'),
        ('get_clipboard', '读剪贴板', '📋'),
        ('set_clipboard', '写剪贴板', '📌'),
    ]),
    ('流程', [
        ('if_condition', '条件', '🔀'),
        ('loop', '循环', '🔁'),
    ]),
    ('等待', [
        ('wait_window', '窗口', '🪟'),
        ('wait_pixel', '像素', '🎨'),
    ]),
]


class FlowPalette:
    """左侧步骤类型面板"""

    def __init__(self, parent: Frame, theme: dict, on_add=None):
        self.theme = theme
        self._f = theme['font']
        self._fm = theme['mono']
        self._on_add = on_add

        self.frame = Frame(parent, bg=theme['bg'], width=90)
        self.frame.pack(side='left', fill='y')
        self.frame.pack_propagate(False)

        Label(self.frame, text="步骤", fg=theme['sub'], bg=theme['bg'],
              font=(self._f, 8, 'bold')).pack(padx=6, pady=(8, 4), anchor='w')

        for cat_name, items in PALETTE_CATEGORIES:
            Label(self.frame, text=cat_name, fg=theme['dim'], bg=theme['bg'],
                  font=(self._fm, 6)).pack(padx=6, pady=(6, 2), anchor='w')

            for type_id, type_name, icon in items:
                btn = Label(self.frame, text=f"{icon}{type_name}",
                            fg=theme['text'], bg=theme['card2'],
                            font=(self._f, 7), cursor='hand2',
                            padx=4, pady=2, anchor='w')
                btn.pack(fill='x', padx=4, pady=1)
                btn.bind('<Button-1>',
                         lambda e, t=type_id: self._on_click(t))
                btn.bind('<Enter>',
                         lambda e, b=btn: b.configure(bg=theme['accent_glow']))
                btn.bind('<Leave>',
                         lambda e, b=btn: b.configure(bg=theme['card2']))

    def _on_click(self, step_type: str):
        if self._on_add:
            self._on_add(step_type)
