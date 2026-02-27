"""流程编排器 — 左侧步骤面板（重新设计）"""

from tkinter import Frame, Label, Canvas, Scrollbar
from ..widgets.draw import rrect
from ..dialogs.flow_canvas import STEP_CATEGORY_COLORS


# 步骤分类
PALETTE_CATEGORIES = [
    ('基础', [
        ('delay', '延迟', '⏱', '暂停指定毫秒'),
        ('keys', '按键', '⌨', '模拟键盘输入'),
        ('type_text', '打字', '✍', '逐字符输入文本'),
        ('app', '应用', '📂', '启动程序'),
        ('shell', '命令', '💻', '执行脚本'),
        ('url', '网址', '🌐', '打开链接'),
        ('snippet', '文本', '📄', '输入文本'),
        ('toast', '提示', '💬', '显示提示消息'),
    ]),
    ('鼠标', [
        ('mouse_click', '点击', '🖱', '鼠标点击'),
        ('mouse_double_click', '双击', '🖱', '鼠标双击'),
        ('mouse_move', '移动', '↗', '移动鼠标'),
        ('mouse_scroll', '滚轮', '🔄', '鼠标滚轮'),
    ]),
    ('变量', [
        ('set_var', '赋值', '📝', '设置变量'),
        ('get_clipboard', '读剪贴板', '📋', '获取剪贴板'),
        ('set_clipboard', '写剪贴板', '📌', '设置剪贴板'),
    ]),
    ('数据', [
        ('file_read', '读文件', '📖', '读取文件内容'),
        ('file_write', '写文件', '✏️', '写入文件内容'),
    ]),
    ('系统', [
        ('screenshot', '截图', '📸', '截取屏幕区域'),
    ]),
    ('网络', [
        ('http_request', 'HTTP请求', '🔗', 'GET/POST请求'),
    ]),
    ('流程', [
        ('if_condition', '条件', '🔀', '条件分支'),
        ('loop', '循环', '🔁', '循环执行'),
    ]),
    ('等待', [
        ('wait_window', '窗口', '🪟', '等待窗口'),
        ('wait_pixel', '像素', '🎨', '等待像素'),
        ('window_activate', '激活窗口', '🪟', '激活指定窗口'),
    ]),
]


def _get_palette_color(theme: dict, type_id: str) -> str:
    """获取步骤类型的主题色"""
    color_key = STEP_CATEGORY_COLORS.get(type_id, 'accent')
    return theme.get(color_key, theme['accent'])


class FlowPalette:
    """左侧步骤类型面板 — 卡片式设计"""

    def __init__(self, parent: Frame, theme: dict, on_add=None):
        self.theme = theme
        self._f = theme['font']
        self._fm = theme['mono']
        self._on_add = on_add

        self.frame = Frame(parent, bg=theme['bg'], width=180)
        self.frame.pack(side='left', fill='y')
        self.frame.pack_propagate(False)

        # 标题
        title_frame = Frame(self.frame, bg=theme['bg'])
        title_frame.pack(fill='x', padx=12, pady=(12, 8))
        Label(title_frame, text="步骤库", fg=theme['text'], bg=theme['bg'],
              font=(self._f, 10, 'bold')).pack(anchor='w')
        Label(title_frame, text="拖入画布或点击添加", fg=theme['dim'], bg=theme['bg'],
              font=(self._f, 7)).pack(anchor='w', pady=(2, 0))

        # 滚动区域
        scroll_frame = Frame(self.frame, bg=theme['bg'])
        scroll_frame.pack(fill='both', expand=True, padx=8)

        canvas = Canvas(scroll_frame, bg=theme['bg'], highlightthickness=0)
        scrollbar = Scrollbar(scroll_frame, orient='vertical', command=canvas.yview)
        content = Frame(canvas, bg=theme['bg'])

        content.bind('<Configure>',
                     lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.create_window((0, 0), window=content, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # 渲染分类卡片
        for cat_name, items in PALETTE_CATEGORIES:
            Label(content, text=cat_name, fg=theme['sub'], bg=theme['bg'],
                  font=(self._f, 8, 'bold')).pack(anchor='w', padx=4, pady=(8, 4))

            for type_id, type_name, icon, desc in items:
                self._create_step_card(content, type_id, type_name, icon, desc)

        # 鼠标滚轮
        canvas.bind('<Enter>',
                    lambda e: canvas.bind_all('<MouseWheel>', lambda ev: canvas.yview_scroll(-1 * (ev.delta // 120), 'units')))
        canvas.bind('<Leave>',
                    lambda e: canvas.unbind_all('<MouseWheel>'))

    def _create_step_card(self, parent, type_id, type_name, icon, desc):
        """创建步骤卡片"""
        c = self.theme
        step_color = _get_palette_color(c, type_id)

        card = Frame(parent, bg=c['card'], cursor='hand2',
                     highlightbackground=c['border_subtle'], highlightthickness=1)
        card.pack(fill='x', padx=4, pady=2)

        # 左侧彩色竖条
        color_bar = Frame(card, bg=step_color, width=3)
        color_bar.pack(side='left', fill='y')

        # 图标（步骤专属颜色）
        Label(card, text=icon, font=('Segoe UI Emoji', 16),
              bg=c['card'], fg=step_color).pack(side='left', padx=(6, 6), pady=6)

        # 文字
        text_frame = Frame(card, bg=c['card'])
        text_frame.pack(side='left', fill='both', expand=True, pady=6)

        Label(text_frame, text=type_name, fg=c['text'], bg=c['card'],
              font=(self._f, 9, 'bold'), anchor='w').pack(fill='x')
        Label(text_frame, text=desc, fg=c['dim'], bg=c['card'],
              font=(self._f, 7), anchor='w').pack(fill='x')

        # 交互
        card.bind('<Button-1>', lambda e: self._on_click(type_id))
        card.bind('<Enter>', lambda e: card.configure(bg=c['accent_glow'],
                                                       highlightbackground=c['accent']))
        card.bind('<Leave>', lambda e: card.configure(bg=c['card'],
                                                       highlightbackground=c['border_subtle']))

        # 子控件也要绑定
        for child in card.winfo_children():
            child.bind('<Button-1>', lambda e: self._on_click(type_id))
            child.bind('<Enter>', lambda e: card.event_generate('<Enter>'))
            child.bind('<Leave>', lambda e: card.event_generate('<Leave>'))
            if isinstance(child, Frame):
                for subchild in child.winfo_children():
                    subchild.bind('<Button-1>', lambda e: self._on_click(type_id))
                    subchild.bind('<Enter>', lambda e: card.event_generate('<Enter>'))
                    subchild.bind('<Leave>', lambda e: card.event_generate('<Leave>'))

    def _on_click(self, step_type: str):
        if self._on_add:
            self._on_add(step_type)
