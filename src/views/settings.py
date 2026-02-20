"""设置视图"""

from tkinter import Canvas, Entry, Frame, Label, Toplevel, StringVar
from .base import BaseView
from ..widgets.draw import rrect, pill


class SettingsView(BaseView):

    def __init__(self, app):
        super().__init__(app)
        self._editing = None  # which field is being edited

    def render(self, canvas: Canvas, w: int, y: int) -> int:
        c = self.theme
        mx = 10
        cw = w - 20
        cfg = self.app.config
        launcher_cfg = cfg.get('launcher', {})
        window_cfg = cfg.get('window', {})

        # section: Window
        canvas.create_text(mx + 4, y + 4, text="窗口", fill=c['dim'],
                           font=(self._f, 7), anchor='w')
        y += 20

        y = self._draw_row(canvas, mx, y, cw, "透明度",
                           f"{window_cfg.get('opacity', 0.92)}", 'set_opacity')
        y = self._draw_row(canvas, mx, y, cw, "宽度",
                           f"{window_cfg.get('width', 360)}px", 'set_width')

        y += 8

        # section: Launcher
        canvas.create_text(mx + 4, y + 4, text="启动器", fill=c['dim'],
                           font=(self._f, 7), anchor='w')
        y += 20

        grid = launcher_cfg.get('grid', [4, 7])
        y = self._draw_row(canvas, mx, y, cw, "网格",
                           f"{grid[0]} x {grid[1]}", 'set_grid')
        y = self._draw_row(canvas, mx, y, cw, "热键",
                           launcher_cfg.get('hotkey', 'ctrl+space'), 'set_hotkey')

        # middle click toggle
        mc = launcher_cfg.get('middle_click', True)
        y = self._draw_toggle(canvas, mx, y, cw, "鼠标中键", mc, 'tog_middle')

        y += 8

        # section: Default View
        canvas.create_text(mx + 4, y + 4, text="默认视图", fill=c['dim'],
                           font=(self._f, 7), anchor='w')
        y += 20

        default = launcher_cfg.get('default_view', 'launcher')
        view_labels = {'launcher': '启动器', 'detail': '详情', 'overview': '总览'}
        for vname in ['launcher', 'detail', 'overview']:
            active = default == vname
            y = self._draw_radio(canvas, mx, y, cw, view_labels[vname], active,
                                 f'dv_{vname}')

        y += 10
        return y

    def _draw_row(self, canvas, x, y, w, label, value, tag):
        c = self.theme
        h = 32
        rrect(canvas, x, y, x + w, y + h, 8, fill=c['card'], tags=tag)
        canvas.create_text(x + 14, y + h // 2, text=label, fill=c['text'],
                           font=(self._f, 8), anchor='w', tags=tag)
        canvas.create_text(x + w - 14, y + h // 2, text=value, fill=c['accent'],
                           font=(self._fm, 8), anchor='e', tags=tag)
        canvas.create_rectangle(x, y, x + w, y + h, fill='', outline='', tags=tag)
        return y + h + 4

    def _draw_toggle(self, canvas, x, y, w, label, active, tag):
        c = self.theme
        h = 32
        rrect(canvas, x, y, x + w, y + h, 8, fill=c['card'], tags=tag)
        canvas.create_text(x + 14, y + h // 2, text=label, fill=c['text'],
                           font=(self._f, 8), anchor='w', tags=tag)

        # toggle indicator
        tx = x + w - 40
        ty = y + h // 2 - 7
        tw, th = 26, 14
        if active:
            pill(canvas, tx, ty, tx + tw, ty + th, fill=c['accent'], tags=tag)
            canvas.create_oval(tx + tw - th + 2, ty + 2, tx + tw - 2, ty + th - 2,
                               fill='#fff', outline='', tags=tag)
        else:
            pill(canvas, tx, ty, tx + tw, ty + th, fill=c['dim'], tags=tag)
            canvas.create_oval(tx + 2, ty + 2, tx + th - 2, ty + th - 2,
                               fill=c['card'], outline='', tags=tag)

        canvas.create_rectangle(x, y, x + w, y + h, fill='', outline='', tags=tag)
        return y + h + 4

    def _draw_radio(self, canvas, x, y, w, label, active, tag):
        c = self.theme
        h = 28
        rrect(canvas, x, y, x + w, y + h, 8,
              fill=c['accent_glow'] if active else c['card'], tags=tag)
        dot_x = x + 14
        dot_y = y + h // 2
        if active:
            canvas.create_oval(dot_x - 4, dot_y - 4, dot_x + 4, dot_y + 4,
                               fill=c['accent'], outline='', tags=tag)
        else:
            canvas.create_oval(dot_x - 4, dot_y - 4, dot_x + 4, dot_y + 4,
                               fill='', outline=c['dim'], tags=tag)
        canvas.create_text(x + 28, dot_y, text=label,
                           fill=c['accent'] if active else c['text'],
                           font=(self._f, 8), anchor='w', tags=tag)
        canvas.create_rectangle(x, y, x + w, y + h, fill='', outline='', tags=tag)
        return y + h + 4

    def on_click(self, canvas: Canvas, event, tags: list[str]) -> bool:
        for tag in tags:
            if tag == 'tog_middle':
                self._toggle_middle_click()
                return True
            if tag.startswith('dv_'):
                self._set_default_view(tag[3:])
                return True
            if tag == 'set_opacity':
                self._edit_value("透明度 (0.5-1.0)", 'opacity',
                                 self.app.config.get('window', {}).get('opacity', 0.92),
                                 self._apply_opacity)
                return True
            if tag == 'set_width':
                self._edit_value("宽度 (300-600)", 'width',
                                 self.app.config.get('window', {}).get('width', 360),
                                 self._apply_width)
                return True
            if tag == 'set_grid':
                self._edit_grid()
                return True
            if tag == 'set_hotkey':
                self._edit_value("热键 (如 ctrl+space)", 'hotkey',
                                 self.app.config.get('launcher', {}).get('hotkey', 'ctrl+space'),
                                 self._apply_hotkey)
                return True
        return False

    def _toggle_middle_click(self):
        launcher = self.app.config.setdefault('launcher', {})
        launcher['middle_click'] = not launcher.get('middle_click', True)
        self.app._save_config()
        self.app._render()

    def _set_default_view(self, view_name):
        launcher = self.app.config.setdefault('launcher', {})
        launcher['default_view'] = view_name
        self.app._save_config()
        self.app._render()

    def _edit_value(self, title, key, current, apply_fn):
        """弹出小输入框编辑单个值"""
        c = self.theme
        dlg = Toplevel(self.app.root)
        dlg.overrideredirect(True)
        dlg.attributes('-topmost', True)
        dlg.configure(bg=c['border'])

        inner = Frame(dlg, bg=c['bg'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)

        Label(inner, text=title, fg=c['sub'], bg=c['bg'],
              font=(self._f, 8)).pack(padx=12, pady=(10, 6))

        entry = Entry(inner, bg=c['card'], fg=c['text'],
                      insertbackground=c['accent'], relief='flat',
                      font=(self._fm, 9), bd=0, highlightthickness=1,
                      highlightbackground=c['border_subtle'],
                      highlightcolor=c['accent'])
        entry.pack(fill='x', padx=12, ipady=5)
        entry.insert(0, str(current))
        entry.select_range(0, 'end')

        def save(e=None):
            val = entry.get().strip()
            dlg.destroy()
            if val:
                apply_fn(val)

        entry.bind('<Return>', save)
        dlg.bind('<Escape>', lambda e: dlg.destroy())
        entry.focus_set()

        dw, dh = 240, 80
        dlg.geometry(f"{dw}x{dh}")
        px = self.app.root.winfo_rootx() + (self.app.root.winfo_width() - dw) // 2
        py = self.app.root.winfo_rooty() + 60
        dlg.geometry(f"+{px}+{py}")
        dlg.grab_set()

    def _edit_grid(self):
        """编辑网格尺寸"""
        c = self.theme
        grid = self.app.config.get('launcher', {}).get('grid', [4, 7])

        dlg = Toplevel(self.app.root)
        dlg.overrideredirect(True)
        dlg.attributes('-topmost', True)
        dlg.configure(bg=c['border'])

        inner = Frame(dlg, bg=c['bg'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)

        Label(inner, text="网格 (列 x 行)", fg=c['sub'], bg=c['bg'],
              font=(self._f, 8)).pack(padx=12, pady=(10, 6))

        row = Frame(inner, bg=c['bg'])
        row.pack(fill='x', padx=12)

        col_e = Entry(row, bg=c['card'], fg=c['text'], width=5,
                      insertbackground=c['accent'], relief='flat',
                      font=(self._fm, 9), bd=0, highlightthickness=1,
                      highlightbackground=c['border_subtle'],
                      highlightcolor=c['accent'])
        col_e.pack(side='left', ipady=5)
        col_e.insert(0, str(grid[0]))

        Label(row, text=" x ", fg=c['dim'], bg=c['bg'],
              font=(self._fm, 9)).pack(side='left')

        row_e = Entry(row, bg=c['card'], fg=c['text'], width=5,
                      insertbackground=c['accent'], relief='flat',
                      font=(self._fm, 9), bd=0, highlightthickness=1,
                      highlightbackground=c['border_subtle'],
                      highlightcolor=c['accent'])
        row_e.pack(side='left', ipady=5)
        row_e.insert(0, str(grid[1]))

        def save(e=None):
            try:
                cols = max(2, min(8, int(col_e.get())))
                rows = max(2, min(12, int(row_e.get())))
            except ValueError:
                dlg.destroy()
                return
            dlg.destroy()
            launcher = self.app.config.setdefault('launcher', {})
            launcher['grid'] = [cols, rows]
            # update launcher view
            lv = self.app._views.get('launcher')
            if lv:
                lv._cols = cols
                lv._rows = rows
            self.app._save_config()
            self.app._render()

        col_e.bind('<Return>', save)
        row_e.bind('<Return>', save)
        dlg.bind('<Escape>', lambda e: dlg.destroy())
        col_e.focus_set()

        dw, dh = 240, 80
        dlg.geometry(f"{dw}x{dh}")
        px = self.app.root.winfo_rootx() + (self.app.root.winfo_width() - dw) // 2
        py = self.app.root.winfo_rooty() + 60
        dlg.geometry(f"+{px}+{py}")
        dlg.grab_set()

    def _apply_opacity(self, val):
        try:
            opacity = max(0.5, min(1.0, float(val)))
        except ValueError:
            return
        self.app.config.setdefault('window', {})['opacity'] = opacity
        self.app.root.attributes('-alpha', opacity)
        self.app._save_config()
        self.app._render()

    def _apply_width(self, val):
        try:
            width = max(300, min(600, int(val)))
        except ValueError:
            return
        self.app.config.setdefault('window', {})['width'] = width
        self.app.canvas.configure(width=width)
        self.app._save_config()
        self.app._render()

    def _apply_hotkey(self, val):
        launcher = self.app.config.setdefault('launcher', {})
        launcher['hotkey'] = val
        self.app._save_config()
        # 热键需要重启才能生效
        self.app._show_toast("重启后生效")
        self.app._render()
