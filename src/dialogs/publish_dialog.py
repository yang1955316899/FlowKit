"""动作发布对话框"""

from tkinter import Toplevel, Frame, Label, Entry, Canvas, StringVar
from ..widgets.draw import rr_points


class PublishDialog:
    """发布动作到商店"""

    def __init__(self, parent, theme: dict, action: dict = None, page: dict = None):
        self.result = None
        self.theme = theme
        self._f = theme['font']
        self._fm = theme['mono']
        self._action = action
        self._page = page

        self.win = Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.configure(bg=theme['border'])

        inner = Frame(self.win, bg=theme['bg'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)

        # title
        Label(inner, text="发布到商店", fg=theme['text'], bg=theme['bg'],
              font=(self._f, 10, 'bold')).pack(padx=16, pady=(12, 8))

        # 名称
        Label(inner, text="名称", fg=theme['dim'], bg=theme['bg'],
              font=(self._f, 7)).pack(anchor='w', padx=16)
        self._name_entry = self._make_entry(inner)
        self._name_entry.pack(fill='x', padx=16, ipady=4, pady=(0, 6))

        # 预填名称
        default_name = ''
        if action:
            default_name = action.get('label', '')
        elif page:
            default_name = page.get('name', '')
        self._name_entry.insert(0, default_name)

        # 描述
        Label(inner, text="描述", fg=theme['dim'], bg=theme['bg'],
              font=(self._f, 7)).pack(anchor='w', padx=16)
        self._desc_entry = self._make_entry(inner)
        self._desc_entry.pack(fill='x', padx=16, ipady=4, pady=(0, 6))

        # 作者
        Label(inner, text="作者", fg=theme['dim'], bg=theme['bg'],
              font=(self._f, 7)).pack(anchor='w', padx=16)
        self._author_entry = self._make_entry(inner)
        self._author_entry.pack(fill='x', padx=16, ipady=4, pady=(0, 6))

        # 分类
        Label(inner, text="分类", fg=theme['dim'], bg=theme['bg'],
              font=(self._f, 7)).pack(anchor='w', padx=16)
        self._cat_entry = self._make_entry(inner)
        self._cat_entry.pack(fill='x', padx=16, ipady=4, pady=(0, 6))
        self._cat_entry.insert(0, '通用')

        # buttons
        bf = Frame(inner, bg=theme['bg'])
        bf.pack(fill='x', padx=16, pady=(8, 12))

        sc = Canvas(bf, width=60, height=28, bg=theme['bg'],
                    highlightthickness=0, cursor='hand2')
        sc.pack(side='right')
        pts = rr_points(0, 0, 60, 28, 14)
        sc.create_polygon(pts, fill=theme['accent'], outline='')
        sc.create_text(30, 14, text="发布", fill='#1e1e2e',
                       font=(self._f, 8, 'bold'))
        sc.bind('<Button-1>', lambda e: self._save())

        cc = Canvas(bf, width=60, height=28, bg=theme['bg'],
                    highlightthickness=0, cursor='hand2')
        cc.pack(side='right', padx=(0, 8))
        pts2 = rr_points(0, 0, 60, 28, 14)
        cc.create_polygon(pts2, fill='', outline=theme['border'])
        cc.create_text(30, 14, text="取消", fill=theme['dim'],
                       font=(self._f, 8))
        cc.bind('<Button-1>', lambda e: self.win.destroy())

        self.win.bind('<Return>', lambda e: self._save())
        self.win.bind('<Escape>', lambda e: self.win.destroy())

        dw, dh = 320, 340
        self.win.geometry(f"{dw}x{dh}")
        self.win.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - dw) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - dh) // 2
        self.win.geometry(f"+{px}+{py}")
        self.win.grab_set()
        self._name_entry.focus_set()

    def _make_entry(self, parent):
        c = self.theme
        return Entry(parent, bg=c['card'], fg=c['text'],
                     insertbackground=c['accent'], relief='flat',
                     font=(self._f, 9), bd=0, highlightthickness=1,
                     highlightbackground=c['border_subtle'],
                     highlightcolor=c['accent'])

    def _save(self):
        name = self._name_entry.get().strip()
        if not name:
            return
        self.result = {
            'name': name,
            'description': self._desc_entry.get().strip(),
            'author': self._author_entry.get().strip() or '匿名',
            'category': self._cat_entry.get().strip() or '通用',
            'action': self._action,
            'page': self._page,
        }
        self.win.destroy()

    def show(self):
        self.win.wait_window()
        return self.result
