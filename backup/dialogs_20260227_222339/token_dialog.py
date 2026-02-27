"""Token 新增/编辑对话框"""

from tkinter import Toplevel, Label, Entry, Frame, Canvas
from ..widgets.draw import rr_points


class TokenDialog:

    def __init__(self, parent, theme: dict, token: dict = None):
        self.result = None
        self.theme = theme
        self._f = theme['font']
        self._fm = theme['mono']
        self._drag = {'x': 0, 'y': 0}

        self.win = Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.configure(bg=theme['border'])

        inner = Frame(self.win, bg=theme['bg'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)

        # title bar
        tb = Frame(inner, bg=theme['card'], height=30)
        tb.pack(fill='x')
        tb.pack_propagate(False)

        # accent dot + title
        dot = Canvas(tb, width=8, height=8, bg=theme['card'], highlightthickness=0)
        dot.pack(side='left', padx=(12, 0), pady=0)
        dot.create_oval(0, 0, 8, 8, fill=theme['accent'], outline='')

        title = "编辑 Token" if token else "添加 Token"
        Label(tb, text=title, fg=theme['sub'], bg=theme['card'],
              font=(self._f, 8, 'bold')).pack(side='left', padx=(6, 0))

        cl = Label(tb, text="\u00D7", fg=theme['dim'], bg=theme['card'],
                  font=(self._f, 11), cursor='hand2')
        cl.pack(side='right', padx=10)
        cl.bind('<Button-1>', lambda e: self.win.destroy())
        tb.bind('<Button-1>', self._ds)
        tb.bind('<B1-Motion>', self._dm)

        # separator
        Frame(inner, bg=theme['border_subtle'], height=1).pack(fill='x')

        # form
        fm = Frame(inner, bg=theme['bg'])
        fm.pack(fill='both', expand=True, padx=16, pady=(12, 14))

        # Name
        Label(fm, text="名称", fg=theme['dim'], bg=theme['bg'],
              font=(self._fm, 7)).pack(anchor='w', pady=(0, 4))
        self.name_e = Entry(fm, bg=theme['card'], fg=theme['text'],
                           insertbackground=theme['accent'], relief='flat',
                           font=(self._f, 9), bd=0, highlightthickness=1,
                           highlightbackground=theme['border_subtle'],
                           highlightcolor=theme['accent'])
        self.name_e.pack(fill='x', ipady=5)

        # Credential
        Label(fm, text="凭证", fg=theme['dim'], bg=theme['bg'],
              font=(self._fm, 7)).pack(anchor='w', pady=(12, 4))
        self.cred_e = Entry(fm, bg=theme['card'], fg=theme['text'],
                           insertbackground=theme['accent'], relief='flat',
                           font=(self._fm, 8), bd=0, highlightthickness=1,
                           highlightbackground=theme['border_subtle'],
                           highlightcolor=theme['accent'])
        self.cred_e.pack(fill='x', ipady=5)

        # Daily Limit
        Label(fm, text="每日限额 ($)", fg=theme['dim'], bg=theme['bg'],
              font=(self._fm, 7)).pack(anchor='w', pady=(12, 4))
        self.limit_e = Entry(fm, bg=theme['card'], fg=theme['text'],
                            insertbackground=theme['accent'], relief='flat',
                            font=(self._fm, 9), bd=0, highlightthickness=1,
                            highlightbackground=theme['border_subtle'],
                            highlightcolor=theme['accent'])
        self.limit_e.pack(fill='x', ipady=5)

        if token:
            self.name_e.insert(0, token.get('name', ''))
            self.cred_e.insert(0, token.get('credential', ''))
            lim = token.get('daily_limit', '')
            if lim: self.limit_e.insert(0, str(lim))

        # buttons
        bf = Frame(fm, bg=theme['bg'])
        bf.pack(fill='x', pady=(14, 0))

        # Save button — pill shaped via canvas polygon
        sc = Canvas(bf, width=60, height=28, bg=theme['bg'], highlightthickness=0, cursor='hand2')
        sc.pack(side='right')
        pts = rr_points(0, 0, 60, 28, 14)
        sc.create_polygon(pts, fill=theme['accent'], outline='')
        sc.create_text(30, 14, text="保存", fill='#1e1e2e', font=(self._f, 8, 'bold'))
        sc.bind('<Button-1>', lambda e: self._save())

        # Cancel button
        cc = Canvas(bf, width=60, height=28, bg=theme['bg'], highlightthickness=0, cursor='hand2')
        cc.pack(side='right', padx=(0, 8))
        pts2 = rr_points(0, 0, 60, 28, 14)
        cc.create_polygon(pts2, fill='', outline=theme['border'])
        cc.create_text(30, 14, text="取消", fill=theme['dim'], font=(self._f, 8))
        cc.bind('<Button-1>', lambda e: self.win.destroy())

        self.win.bind('<Return>', lambda e: self._save())
        self.win.bind('<Escape>', lambda e: self.win.destroy())
        self.name_e.focus_set()

        dw, dh = 300, 290
        self.win.geometry(f"{dw}x{dh}")
        self.win.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - dw) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - dh) // 2
        self.win.geometry(f"+{px}+{py}")
        self.win.grab_set()

    def _ds(self, e):
        self._drag['x'] = e.x_root - self.win.winfo_x()
        self._drag['y'] = e.y_root - self.win.winfo_y()

    def _dm(self, e):
        self.win.geometry(f"+{e.x_root-self._drag['x']}+{e.y_root-self._drag['y']}")

    def _save(self):
        name = self.name_e.get().strip()
        cred = self.cred_e.get().strip()
        if not name or not cred: return
        r = {'name': name, 'credential': cred}
        ls = self.limit_e.get().strip()
        if ls:
            try: r['daily_limit'] = float(ls)
            except: pass
        self.result = r
        self.win.destroy()

    def show(self):
        self.win.wait_window()
        return self.result
