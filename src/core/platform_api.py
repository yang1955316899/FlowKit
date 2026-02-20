"""平台 API 服务端 — TCP JSON-RPC，供脚本子进程调用主进程能力"""

import json
import socket
import threading
import ctypes
import ctypes.wintypes
import os
import webbrowser
import subprocess
import requests as _requests
from pathlib import Path


class PlatformAPIServer:
    """在主进程中运行的 TCP JSON-RPC 服务，处理子进程的 API 调用"""

    def __init__(self, root=None, theme=None, feedback_cb=None):
        self._root = root
        self._theme = theme
        self._feedback_cb = feedback_cb
        self._server: socket.socket | None = None
        self._port = 0
        self._running = False
        self._store: dict = {}  # 脚本间持久化存储
        self._store_path = Path(__file__).parent.parent.parent / '.script_store.json'
        self._load_store()

        # API 方法注册表
        self._handlers: dict[str, callable] = {
            # 剪贴板
            'clipboard.get_text': self._clipboard_get_text,
            'clipboard.set_text': self._clipboard_set_text,
            'clipboard.get_files': self._clipboard_get_files,
            # 窗口
            'window.get_foreground': self._window_get_foreground,
            'window.find': self._window_find,
            'window.activate': self._window_activate,
            'window.move': self._window_move,
            'window.minimize': self._window_minimize,
            'window.maximize': self._window_maximize,
            'window.close': self._window_close,
            'window.set_topmost': self._window_set_topmost,
            # HTTP
            'http.get': self._http_get,
            'http.post': self._http_post,
            'http.download': self._http_download,
            # 通知/对话框
            'ui.toast': self._ui_toast,
            'ui.notify': self._ui_notify,
            'ui.input': self._ui_input,
            'ui.confirm': self._ui_confirm,
            'ui.select': self._ui_select,
            # 按键/鼠标
            'keys.send': self._keys_send,
            'keys.type_text': self._keys_type_text,
            'mouse.click': self._mouse_click,
            'mouse.move': self._mouse_move,
            # 系统
            'system.env': self._system_env,
            'system.run': self._system_run,
            'system.open': self._system_open,
            # 存储
            'store.get': self._store_get,
            'store.set': self._store_set,
        }

    @property
    def port(self) -> int:
        return self._port

    def start(self):
        """启动 TCP 服务"""
        self._server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server.bind(('127.0.0.1', 0))
        self._port = self._server.getsockname()[1]
        self._server.listen(8)
        self._server.settimeout(1.0)
        self._running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()

    def stop(self):
        """停止 TCP 服务"""
        self._running = False
        if self._server:
            try:
                self._server.close()
            except Exception:
                pass
        self._save_store()

    def _accept_loop(self):
        while self._running:
            try:
                conn, _ = self._server.accept()
                threading.Thread(target=self._handle_conn, args=(conn,), daemon=True).start()
            except socket.timeout:
                continue
            except Exception:
                if self._running:
                    continue
                break

    def _handle_conn(self, conn: socket.socket):
        """处理单个连接 — 支持多次请求（长连接）"""
        conn.settimeout(60)
        buf = b''
        try:
            while self._running:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                buf += chunk
                # 按换行分割消息
                while b'\n' in buf:
                    line, buf = buf.split(b'\n', 1)
                    if not line.strip():
                        continue
                    try:
                        req = json.loads(line.decode('utf-8'))
                        resp = self._dispatch(req)
                    except json.JSONDecodeError:
                        resp = {'error': 'invalid json'}
                    except Exception as e:
                        resp = {'error': str(e)}
                    data = json.dumps(resp, ensure_ascii=False).encode('utf-8') + b'\n'
                    conn.sendall(data)
        except Exception:
            pass
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def _dispatch(self, req: dict) -> dict:
        method = req.get('method', '')
        params = req.get('params', {})
        req_id = req.get('id', 0)
        handler = self._handlers.get(method)
        if not handler:
            return {'id': req_id, 'error': f'unknown method: {method}'}
        try:
            result = handler(**params) if isinstance(params, dict) else handler(*params)
            return {'id': req_id, 'result': result}
        except Exception as e:
            return {'id': req_id, 'error': str(e)}

    # ── 持久化存储 ──

    def _load_store(self):
        try:
            if self._store_path.exists():
                self._store = json.loads(self._store_path.read_text('utf-8'))
        except Exception:
            self._store = {}

    def _save_store(self):
        try:
            self._store_path.write_text(json.dumps(self._store, ensure_ascii=False, indent=2), 'utf-8')
        except Exception:
            pass

    # ── 剪贴板 API ──

    def _clipboard_get_text(self) -> str:
        CF_UNICODETEXT = 13
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        if not user32.OpenClipboard(0):
            return ''
        try:
            h = user32.GetClipboardData(CF_UNICODETEXT)
            if not h:
                return ''
            p = kernel32.GlobalLock(h)
            if not p:
                return ''
            try:
                return ctypes.wstring_at(p)
            finally:
                kernel32.GlobalUnlock(h)
        finally:
            user32.CloseClipboard()

    def _clipboard_set_text(self, text: str = '') -> bool:
        CF_UNICODETEXT = 13
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        if not user32.OpenClipboard(0):
            return False
        try:
            user32.EmptyClipboard()
            data = text.encode('utf-16-le') + b'\x00\x00'
            h = kernel32.GlobalAlloc(0x0042, len(data))
            if h:
                p = kernel32.GlobalLock(h)
                ctypes.memmove(p, data, len(data))
                kernel32.GlobalUnlock(h)
                user32.SetClipboardData(CF_UNICODETEXT, h)
            return True
        finally:
            user32.CloseClipboard()

    def _clipboard_get_files(self) -> list:
        CF_HDROP = 15
        user32 = ctypes.windll.user32
        shell32 = ctypes.windll.shell32
        if not user32.OpenClipboard(0):
            return []
        try:
            h = user32.GetClipboardData(CF_HDROP)
            if not h:
                return []
            count = shell32.DragQueryFileW(h, 0xFFFFFFFF, None, 0)
            files = []
            buf = ctypes.create_unicode_buffer(260)
            for i in range(count):
                shell32.DragQueryFileW(h, i, buf, 260)
                files.append(buf.value)
            return files
        finally:
            user32.CloseClipboard()

    # ── 窗口 API ──

    def _get_window_info(self, hwnd: int) -> dict:
        user32 = ctypes.windll.user32
        buf = ctypes.create_unicode_buffer(256)
        user32.GetWindowTextW(hwnd, buf, 256)
        title = buf.value
        user32.GetClassNameW(hwnd, buf, 256)
        class_name = buf.value
        pid = ctypes.wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))
        return {
            'hwnd': hwnd,
            'title': title,
            'class_name': class_name,
            'pid': pid.value,
            'rect': [rect.left, rect.top, rect.right, rect.bottom],
        }

    def _window_get_foreground(self) -> dict:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        return self._get_window_info(hwnd)

    def _window_find(self, title: str = None, class_name: str = None) -> list:
        results = []
        user32 = ctypes.windll.user32

        @ctypes.WINFUNCTYPE(ctypes.wintypes.BOOL, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
        def enum_cb(hwnd, _):
            if not user32.IsWindowVisible(hwnd):
                return True
            info = self._get_window_info(hwnd)
            match = True
            if title and title.lower() not in info['title'].lower():
                match = False
            if class_name and class_name.lower() not in info['class_name'].lower():
                match = False
            if match and info['title']:
                results.append(info)
            return True

        user32.EnumWindows(enum_cb, 0)
        return results

    def _window_activate(self, hwnd: int = 0) -> bool:
        user32 = ctypes.windll.user32
        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        user32.SetForegroundWindow(hwnd)
        return True

    def _window_move(self, hwnd: int = 0, x: int = 0, y: int = 0, w: int = 0, h: int = 0) -> bool:
        ctypes.windll.user32.MoveWindow(hwnd, x, y, w, h, True)
        return True

    def _window_minimize(self, hwnd: int = 0) -> bool:
        ctypes.windll.user32.ShowWindow(hwnd, 6)  # SW_MINIMIZE
        return True

    def _window_maximize(self, hwnd: int = 0) -> bool:
        ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
        return True

    def _window_close(self, hwnd: int = 0) -> bool:
        WM_CLOSE = 0x0010
        ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        return True

    def _window_set_topmost(self, hwnd: int = 0, topmost: bool = True) -> bool:
        HWND_TOPMOST = -1
        HWND_NOTOPMOST = -2
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        flag = HWND_TOPMOST if topmost else HWND_NOTOPMOST
        ctypes.windll.user32.SetWindowPos(hwnd, flag, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)
        return True

    # ── HTTP API ──

    def _http_get(self, url: str = '', headers: dict = None, timeout: int = 10) -> dict:
        r = _requests.get(url, headers=headers, timeout=timeout)
        return {'status': r.status_code, 'text': r.text, 'headers': dict(r.headers)}

    def _http_post(self, url: str = '', data=None, json_body=None, headers: dict = None,
                   timeout: int = 10) -> dict:
        r = _requests.post(url, data=data, json=json_body, headers=headers, timeout=timeout)
        return {'status': r.status_code, 'text': r.text, 'headers': dict(r.headers)}

    def _http_download(self, url: str = '', save_path: str = '') -> str:
        r = _requests.get(url, stream=True, timeout=30)
        with open(save_path, 'wb') as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return save_path

    # ── UI API ──

    def _ui_toast(self, msg: str = '', duration: int = 1500) -> bool:
        if self._feedback_cb and self._root:
            self._root.after(0, self._feedback_cb, msg)
        return True

    def _ui_notify(self, title: str = '', msg: str = '') -> bool:
        # 使用 Windows 10+ toast 通知
        try:
            from tkinter import Toplevel, Label
            def show():
                n = Toplevel(self._root)
                n.overrideredirect(True)
                n.attributes('-topmost', True)
                n.configure(bg='#1e1e2e')
                f = Label(n, text=f"{title}\n{msg}", fg='#cdd6f4', bg='#1e1e2e',
                          font=('Microsoft YaHei UI', 9), padx=16, pady=10, justify='left')
                f.pack()
                sw = n.winfo_screenwidth()
                n.update_idletasks()
                nw = n.winfo_reqwidth()
                n.geometry(f"+{sw - nw - 20}+40")
                n.after(3000, n.destroy)
            if self._root:
                self._root.after(0, show)
        except Exception:
            pass
        return True

    def _ui_input(self, title: str = '', default: str = '') -> str | None:
        result = [None]
        event = threading.Event()

        def show():
            from tkinter import Toplevel, Label, Entry, Frame, Canvas
            from ..widgets.draw import rr_points
            c = self._theme or {}
            bg = c.get('bg', '#0f0f17')
            card = c.get('card', '#181825')
            text = c.get('text', '#cdd6f4')
            dim = c.get('dim', '#6c7086')
            accent = c.get('accent', '#89b4fa')
            border = c.get('border_subtle', '#252538')
            font = c.get('font', 'Microsoft YaHei UI')

            dlg = Toplevel(self._root)
            dlg.overrideredirect(True)
            dlg.attributes('-topmost', True)
            dlg.configure(bg=c.get('border', '#313147'))

            inner = Frame(dlg, bg=bg)
            inner.pack(fill='both', expand=True, padx=1, pady=1)

            Label(inner, text=title, fg=text, bg=bg, font=(font, 9, 'bold')).pack(
                padx=16, pady=(12, 8))

            entry = Entry(inner, bg=card, fg=text, insertbackground=accent, relief='flat',
                          font=(font, 9), bd=0, highlightthickness=1,
                          highlightbackground=border, highlightcolor=accent)
            entry.pack(fill='x', padx=16, ipady=5)
            entry.insert(0, default)
            entry.select_range(0, 'end')

            bf = Frame(inner, bg=bg)
            bf.pack(fill='x', padx=16, pady=(10, 12))

            def ok():
                result[0] = entry.get()
                event.set()
                dlg.destroy()

            def cancel():
                event.set()
                dlg.destroy()

            ok_btn = Canvas(bf, width=60, height=28, bg=bg, highlightthickness=0, cursor='hand2')
            ok_btn.pack(side='right')
            pts = rr_points(0, 0, 60, 28, 14)
            ok_btn.create_polygon(pts, fill=accent, outline='')
            ok_btn.create_text(30, 14, text="确定", fill='#1e1e2e', font=(font, 8, 'bold'))
            ok_btn.bind('<Button-1>', lambda e: ok())

            cc = Canvas(bf, width=60, height=28, bg=bg, highlightthickness=0, cursor='hand2')
            cc.pack(side='right', padx=(0, 8))
            pts2 = rr_points(0, 0, 60, 28, 14)
            cc.create_polygon(pts2, fill='', outline=c.get('border', '#313147'))
            cc.create_text(30, 14, text="取消", fill=dim, font=(font, 8))
            cc.bind('<Button-1>', lambda e: cancel())

            dlg.bind('<Return>', lambda e: ok())
            dlg.bind('<Escape>', lambda e: cancel())

            dlg.geometry('300x120')
            dlg.update_idletasks()
            px = self._root.winfo_rootx() + (self._root.winfo_width() - 300) // 2
            py = self._root.winfo_rooty() + (self._root.winfo_height() - 120) // 2
            dlg.geometry(f"+{px}+{py}")
            entry.focus_set()

        if self._root:
            self._root.after(0, show)
            event.wait(timeout=120)
        return result[0]

    def _ui_confirm(self, title: str = '', msg: str = '') -> bool:
        result = [False]
        event = threading.Event()

        def show():
            from tkinter import Toplevel, Label, Frame, Canvas
            from ..widgets.draw import rr_points
            c = self._theme or {}
            bg = c.get('bg', '#0f0f17')
            text = c.get('text', '#cdd6f4')
            dim = c.get('dim', '#6c7086')
            accent = c.get('accent', '#89b4fa')
            font = c.get('font', 'Microsoft YaHei UI')

            dlg = Toplevel(self._root)
            dlg.overrideredirect(True)
            dlg.attributes('-topmost', True)
            dlg.configure(bg=c.get('border', '#313147'))

            inner = Frame(dlg, bg=bg)
            inner.pack(fill='both', expand=True, padx=1, pady=1)

            Label(inner, text=title, fg=text, bg=bg, font=(font, 9, 'bold')).pack(
                padx=16, pady=(12, 4))
            Label(inner, text=msg, fg=dim, bg=bg, font=(font, 8), wraplength=260).pack(
                padx=16, pady=(0, 8))

            bf = Frame(inner, bg=bg)
            bf.pack(fill='x', padx=16, pady=(4, 12))

            def yes():
                result[0] = True
                event.set()
                dlg.destroy()

            def no():
                event.set()
                dlg.destroy()

            ok_btn = Canvas(bf, width=60, height=28, bg=bg, highlightthickness=0, cursor='hand2')
            ok_btn.pack(side='right')
            pts = rr_points(0, 0, 60, 28, 14)
            ok_btn.create_polygon(pts, fill=accent, outline='')
            ok_btn.create_text(30, 14, text="确定", fill='#1e1e2e', font=(font, 8, 'bold'))
            ok_btn.bind('<Button-1>', lambda e: yes())

            cc = Canvas(bf, width=60, height=28, bg=bg, highlightthickness=0, cursor='hand2')
            cc.pack(side='right', padx=(0, 8))
            pts2 = rr_points(0, 0, 60, 28, 14)
            cc.create_polygon(pts2, fill='', outline=c.get('border', '#313147'))
            cc.create_text(30, 14, text="取消", fill=dim, font=(font, 8))
            cc.bind('<Button-1>', lambda e: no())

            dlg.bind('<Return>', lambda e: yes())
            dlg.bind('<Escape>', lambda e: no())

            dlg.geometry('300x110')
            dlg.update_idletasks()
            px = self._root.winfo_rootx() + (self._root.winfo_width() - 300) // 2
            py = self._root.winfo_rooty() + (self._root.winfo_height() - 110) // 2
            dlg.geometry(f"+{px}+{py}")

        if self._root:
            self._root.after(0, show)
            event.wait(timeout=120)
        return result[0]

    def _ui_select(self, title: str = '', options: list = None) -> str | None:
        if not options:
            return None
        result = [None]
        event = threading.Event()

        def show():
            from tkinter import Toplevel, Label, Frame, Canvas
            from ..widgets.draw import rr_points
            c = self._theme or {}
            bg = c.get('bg', '#0f0f17')
            card = c.get('card', '#181825')
            text = c.get('text', '#cdd6f4')
            dim = c.get('dim', '#6c7086')
            accent = c.get('accent', '#89b4fa')
            font = c.get('font', 'Microsoft YaHei UI')

            dlg = Toplevel(self._root)
            dlg.overrideredirect(True)
            dlg.attributes('-topmost', True)
            dlg.configure(bg=c.get('border', '#313147'))

            inner = Frame(dlg, bg=bg)
            inner.pack(fill='both', expand=True, padx=1, pady=1)

            Label(inner, text=title, fg=text, bg=bg, font=(font, 9, 'bold')).pack(
                padx=16, pady=(12, 8))

            for opt in options:
                lbl = Label(inner, text=opt, fg=text, bg=card, font=(font, 8),
                            cursor='hand2', padx=12, pady=6, anchor='w')
                lbl.pack(fill='x', padx=16, pady=1)
                lbl.bind('<Enter>', lambda e, l=lbl: l.configure(bg=accent, fg='#1e1e2e'))
                lbl.bind('<Leave>', lambda e, l=lbl: l.configure(bg=card, fg=text))
                lbl.bind('<Button-1>', lambda e, o=opt: (
                    result.__setitem__(0, o), event.set(), dlg.destroy()))

            Frame(inner, bg=bg, height=8).pack()

            h = 50 + len(options) * 32
            dlg.geometry(f'280x{h}')
            dlg.update_idletasks()
            px = self._root.winfo_rootx() + (self._root.winfo_width() - 280) // 2
            py = self._root.winfo_rooty() + (self._root.winfo_height() - h) // 2
            dlg.geometry(f"+{px}+{py}")
            dlg.bind('<Escape>', lambda e: (event.set(), dlg.destroy()))

        if self._root:
            self._root.after(0, show)
            event.wait(timeout=120)
        return result[0]

    # ── 按键/鼠标 API ──

    def _keys_send(self, combo: str = '') -> bool:
        from .actions import _parse_keys, _send_keys
        keys = _parse_keys(combo)
        _send_keys(keys)
        return True

    def _keys_type_text(self, text: str = '') -> bool:
        if not text:
            return True
        from .actions import INPUT, INPUT_KEYBOARD, KEYEVENTF_KEYUP
        KEYEVENTF_UNICODE = 0x0004
        inputs = []
        for ch in text:
            inp = INPUT(type=INPUT_KEYBOARD)
            inp._input.ki.wVk = 0
            inp._input.ki.wScan = ord(ch)
            inp._input.ki.dwFlags = KEYEVENTF_UNICODE
            inputs.append(inp)
            inp2 = INPUT(type=INPUT_KEYBOARD)
            inp2._input.ki.wVk = 0
            inp2._input.ki.wScan = ord(ch)
            inp2._input.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
            inputs.append(inp2)
        if inputs:
            n = len(inputs)
            arr = (INPUT * n)(*inputs)
            ctypes.windll.user32.SendInput(n, arr, ctypes.sizeof(INPUT))
        return True

    def _mouse_click(self, x: int = 0, y: int = 0) -> bool:
        ctypes.windll.user32.SetCursorPos(x, y)
        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        return True

    def _mouse_move(self, x: int = 0, y: int = 0) -> bool:
        ctypes.windll.user32.SetCursorPos(x, y)
        return True

    # ── 系统 API ──

    def _system_env(self, name: str = '') -> str:
        return os.environ.get(name, '')

    def _system_run(self, cmd: str = '', shell_type: str = 'cmd') -> str:
        if shell_type == 'powershell':
            args = ['powershell', '-Command', cmd]
        else:
            args = cmd
        r = subprocess.run(args, shell=(shell_type == 'cmd'), capture_output=True,
                           text=True, encoding='utf-8', errors='replace',
                           creationflags=subprocess.CREATE_NO_WINDOW, timeout=30)
        return r.stdout

    def _system_open(self, path: str = '') -> bool:
        os.startfile(path)
        return True

    # ── 存储 API ──

    def _store_get(self, key: str = '', default=None):
        return self._store.get(key, default)

    def _store_set(self, key: str = '', value=None) -> bool:
        self._store[key] = value
        self._save_store()
        return True
