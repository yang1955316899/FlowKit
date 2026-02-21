"""文本选中浮窗 UI"""

import webbrowser
from tkinter import Toplevel, Canvas
from ..widgets.draw import rrect


class SelectionPopup:
    """选中文本后弹出的快捷操作浮窗"""

    def __init__(self, root, theme, executor):
        self._root = root
        self._theme = theme
        self._executor = executor
        self._win = None
        self._text = ''

    def show(self, text: str, x: int, y: int):
        """在指定屏幕坐标弹出浮窗"""
        self.hide()
        if not text.strip():
            return

        self._text = text.strip()
        c = self._theme

        win = Toplevel(self._root)
        win.overrideredirect(True)
        win.attributes('-topmost', True)
        win.attributes('-alpha', 0.95)
        win.configure(bg=c['border'])
        self._win = win

        # 操作按钮定义
        buttons = self._get_buttons()
        btn_size = 28
        gap = 4
        pw = len(buttons) * (btn_size + gap) - gap + 12
        ph = btn_size + 12

        canvas = Canvas(win, width=pw, height=ph,
                        bg=c['bg'], highlightthickness=0)
        canvas.pack(padx=1, pady=1)

        bx = 6
        by = 6
        for icon, tip, cmd in buttons:
            tag = f'sel_{tip}'
            rrect(canvas, bx, by, bx + btn_size, by + btn_size, 6,
                  fill=c['card'], tags=tag)
            canvas.create_text(bx + btn_size // 2, by + btn_size // 2,
                               text=icon, font=('Segoe UI Emoji', 10),
                               fill=c['text'], tags=tag)
            canvas.create_rectangle(bx, by, bx + btn_size, by + btn_size,
                                    fill='', outline='', tags=tag)
            canvas.tag_bind(tag, '<Button-1>', lambda e, c=cmd: self._do(c))
            bx += btn_size + gap

        # 定位到鼠标附近
        win.geometry(f"+{x + 10}+{y - ph - 10}")

        # 失焦自动关闭
        win.bind('<FocusOut>', lambda e: win.after(300, self.hide))
        # 3秒后自动关闭
        win.after(3000, self.hide)

    def hide(self):
        if self._win:
            try:
                self._win.destroy()
            except Exception:
                pass
            self._win = None

    def _get_buttons(self):
        """返回 [(icon, name, command), ...]"""
        return [
            ('📋', 'copy', self._copy),
            ('🔍', 'search', self._search),
            ('🌐', 'translate', self._translate),
        ]

    def _do(self, cmd):
        self.hide()
        cmd()

    def _copy(self):
        """复制到剪贴板"""
        import ctypes
        CF_UNICODETEXT = 13
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        if not user32.OpenClipboard(0):
            return
        try:
            user32.EmptyClipboard()
            data = self._text.encode('utf-16-le') + b'\x00\x00'
            h = kernel32.GlobalAlloc(0x0042, len(data))
            if h:
                p = kernel32.GlobalLock(h)
                ctypes.memmove(p, data, len(data))
                kernel32.GlobalUnlock(h)
                user32.SetClipboardData(CF_UNICODETEXT, h)
        finally:
            user32.CloseClipboard()

    def _search(self):
        """用默认浏览器搜索"""
        import urllib.parse
        q = urllib.parse.quote(self._text)
        webbrowser.open(f'https://www.google.com/search?q={q}')

    def _translate(self):
        """用 Google 翻译"""
        import urllib.parse
        q = urllib.parse.quote(self._text)
        webbrowser.open(f'https://translate.google.com/?sl=auto&tl=zh-CN&text={q}')
