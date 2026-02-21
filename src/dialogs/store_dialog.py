"""动作商店浏览对话框"""

import time
from tkinter import (Toplevel, Frame, Label, Entry, Canvas, StringVar,
                     Scrollbar, Listbox)
from ..widgets.draw import rrect, rr_points


class StoreDialog:
    """动作商店浏览/安装界面"""

    def __init__(self, parent, theme: dict, store, on_install=None):
        """
        Args:
            parent: 父窗口
            theme: 主题字典
            store: ActionStore 实例
            on_install: callback(data) 安装成功后回调
        """
        self.theme = theme
        self._store = store
        self._on_install = on_install
        self._f = theme['font']
        self._fm = theme['mono']
        self._items = []
        self._category = None

        self.win = Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.configure(bg=theme['border'])

        inner = Frame(self.win, bg=theme['bg'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)

        # title bar
        title_bar = Frame(inner, bg=theme['card'])
        title_bar.pack(fill='x')
        Label(title_bar, text="📦 动作商店", fg=theme['text'], bg=theme['card'],
              font=(self._f, 10, 'bold')).pack(side='left', padx=12, pady=8)

        close_btn = Label(title_bar, text="×", fg=theme['dim'], bg=theme['card'],
                          font=(self._f, 12), cursor='hand2')
        close_btn.pack(side='right', padx=12)
        close_btn.bind('<Button-1>', lambda e: self.win.destroy())

        # drag support
        title_bar.bind('<Button-1>', self._drag_start)
        title_bar.bind('<B1-Motion>', self._drag_move)

        # search bar
        search_frame = Frame(inner, bg=theme['bg'])
        search_frame.pack(fill='x', padx=12, pady=(8, 4))

        self._search_var = StringVar()
        search_entry = Entry(search_frame, textvariable=self._search_var,
                             bg=theme['card'], fg=theme['text'],
                             insertbackground=theme['accent'], relief='flat',
                             font=(self._f, 9), bd=0, highlightthickness=1,
                             highlightbackground=theme['border_subtle'],
                             highlightcolor=theme['accent'])
        search_entry.pack(fill='x', ipady=4)
        search_entry.insert(0, '')
        self._search_var.trace_add('write', lambda *_: self._refresh_list())

        # category tabs
        cat_frame = Frame(inner, bg=theme['bg'])
        cat_frame.pack(fill='x', padx=12, pady=(4, 4))

        self._cat_labels = []
        all_btn = Label(cat_frame, text="全部", fg=theme['accent'], bg=theme['card'],
                        font=(self._f, 7), cursor='hand2', padx=8, pady=2)
        all_btn.pack(side='left', padx=(0, 4))
        all_btn.bind('<Button-1>', lambda e: self._set_category(None))
        self._cat_labels.append(('__all__', all_btn))

        for cat in store.get_categories():
            btn = Label(cat_frame, text=cat, fg=theme['dim'], bg=theme['card'],
                        font=(self._f, 7), cursor='hand2', padx=8, pady=2)
            btn.pack(side='left', padx=(0, 4))
            btn.bind('<Button-1>', lambda e, c=cat: self._set_category(c))
            self._cat_labels.append((cat, btn))

        # item list (canvas-based)
        list_frame = Frame(inner, bg=theme['bg'])
        list_frame.pack(fill='both', expand=True, padx=12, pady=(4, 8))

        self._canvas = Canvas(list_frame, bg=theme['bg'], highlightthickness=0)
        scrollbar = Scrollbar(list_frame, orient='vertical',
                              command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self._canvas.pack(side='left', fill='both', expand=True)

        self._list_frame = Frame(self._canvas, bg=theme['bg'])
        self._canvas.create_window((0, 0), window=self._list_frame, anchor='nw')
        self._list_frame.bind('<Configure>',
                              lambda e: self._canvas.configure(
                                  scrollregion=self._canvas.bbox('all')))

        # initial load
        self._refresh_list()

        # position
        dw, dh = 400, 500
        self.win.geometry(f"{dw}x{dh}")
        self.win.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - dw) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - dh) // 2
        self.win.geometry(f"+{px}+{py}")
        self.win.grab_set()
        search_entry.focus_set()

    def _drag_start(self, event):
        self._drag_x = event.x
        self._drag_y = event.y

    def _drag_move(self, event):
        x = self.win.winfo_x() + event.x - self._drag_x
        y = self.win.winfo_y() + event.y - self._drag_y
        self.win.geometry(f"+{x}+{y}")

    def _set_category(self, cat):
        self._category = cat
        c = self.theme
        for name, lbl in self._cat_labels:
            if (cat is None and name == '__all__') or name == cat:
                lbl.configure(fg=c['accent'])
            else:
                lbl.configure(fg=c['dim'])
        self._refresh_list()

    def _refresh_list(self):
        """刷新商店列表"""
        keyword = self._search_var.get().strip() or None
        self._items = self._store.list_items(
            category=self._category, keyword=keyword)

        # 清空列表
        for w in self._list_frame.winfo_children():
            w.destroy()

        c = self.theme

        if not self._items:
            Label(self._list_frame, text="暂无动作", fg=c['dim'], bg=c['bg'],
                  font=(self._f, 9)).pack(pady=20)
            return

        for item in self._items:
            self._draw_item(item)

    def _draw_item(self, item: dict):
        """绘制单个商店条目"""
        c = self.theme
        frame = Frame(self._list_frame, bg=c['card'], cursor='hand2')
        frame.pack(fill='x', pady=2)

        # 左侧图标
        icon = item.get('icon', '📦')
        Label(frame, text=icon, font=('Segoe UI Emoji', 16),
              fg=c['text'], bg=c['card']).pack(side='left', padx=(10, 6), pady=8)

        # 中间信息
        info = Frame(frame, bg=c['card'])
        info.pack(side='left', fill='x', expand=True, pady=6)

        name = item.get('name', '未命名')
        Label(info, text=name, fg=c['text'], bg=c['card'],
              font=(self._f, 9, 'bold'), anchor='w').pack(fill='x')

        desc = item.get('description', '')
        if desc:
            Label(info, text=desc[:40], fg=c['dim'], bg=c['card'],
                  font=(self._f, 7), anchor='w').pack(fill='x')

        meta_parts = []
        author = item.get('author', '')
        if author:
            meta_parts.append(author)
        downloads = item.get('downloads', 0)
        meta_parts.append(f"↓{downloads}")
        cat = item.get('category', '')
        if cat:
            meta_parts.append(cat)

        Label(info, text=" · ".join(meta_parts), fg=c['sub'], bg=c['card'],
              font=(self._f, 6), anchor='w').pack(fill='x')

        # 右侧安装按钮
        install_btn = Label(frame, text="安装", fg='#fff', bg=c['accent'],
                            font=(self._f, 7, 'bold'), cursor='hand2',
                            padx=10, pady=3)
        install_btn.pack(side='right', padx=10, pady=8)
        install_btn.bind('<Button-1>',
                         lambda e, i=item: self._install_item(i))

    def _install_item(self, item: dict):
        """安装商店条目"""
        item_id = item.get('id')
        data = self._store.install(item_id)
        if data and self._on_install:
            self._on_install(data)
            # 更新按钮状态
            self._refresh_list()

    def show(self):
        self.win.wait_window()
