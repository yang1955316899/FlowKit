"""文本选中浮窗 — 检测选中文本并弹出快捷操作"""

import ctypes
import ctypes.wintypes
import threading
import time


class SelectionWatcher:
    """监控文本选中事件，触发浮窗"""

    def __init__(self, root, theme, on_selection):
        """
        Args:
            root: tkinter root
            theme: 主题字典
            on_selection: callback(text, x, y) 选中文本后回调
        """
        self._root = root
        self._theme = theme
        self._on_selection = on_selection
        self._running = False
        self._thread = None
        self._last_text = ''

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False

    def _watch_loop(self):
        """轮询检测剪贴板变化（通过模拟 Ctrl+C 后检测）"""
        # 使用 WinEvent hook 检测鼠标抬起事件
        user32 = ctypes.windll.user32

        WH_MOUSE_LL = 14
        WM_LBUTTONUP = 0x0202

        @ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_int,
                            ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM)
        def mouse_proc(nCode, wParam, lParam):
            if nCode >= 0 and wParam == WM_LBUTTONUP:
                # 鼠标抬起后延迟检测选中文本
                threading.Thread(target=self._check_selection,
                                 daemon=True).start()
            return user32.CallNextHookEx(None, nCode, wParam, lParam)

        self._hook_proc = mouse_proc  # prevent GC
        hook = user32.SetWindowsHookExW(WH_MOUSE_LL, mouse_proc, None, 0)
        if not hook:
            return

        msg = ctypes.wintypes.MSG()
        while self._running:
            ret = user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1)
            if ret:
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            else:
                time.sleep(0.05)

        user32.UnhookWindowsHookEx(hook)

    def _check_selection(self):
        """检测当前选中的文本"""
        time.sleep(0.15)  # 等待选中完成

        # 获取选中文本：模拟 Ctrl+C 并读取剪贴板
        text = self._get_selected_text()
        if text and text != self._last_text and len(text.strip()) > 0:
            self._last_text = text
            # 获取鼠标位置
            pt = ctypes.wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            self._root.after(0, self._on_selection, text.strip(),
                             pt.x, pt.y)

    def _get_selected_text(self) -> str:
        """通过剪贴板获取选中文本（先备份再恢复）"""
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        CF_UNICODETEXT = 13

        # 备份当前剪贴板
        old_text = ''
        if user32.OpenClipboard(0):
            h = user32.GetClipboardData(CF_UNICODETEXT)
            if h:
                p = kernel32.GlobalLock(h)
                if p:
                    old_text = ctypes.wstring_at(p)
                    kernel32.GlobalUnlock(h)
            user32.CloseClipboard()

        # 模拟 Ctrl+C
        from .actions import INPUT, INPUT_KEYBOARD, KEYEVENTF_KEYUP
        inputs = []
        # Ctrl down
        inp = INPUT(type=INPUT_KEYBOARD)
        inp._input.ki.wVk = 0x11
        inputs.append(inp)
        # C down
        inp = INPUT(type=INPUT_KEYBOARD)
        inp._input.ki.wVk = 0x43
        inputs.append(inp)
        # C up
        inp = INPUT(type=INPUT_KEYBOARD)
        inp._input.ki.wVk = 0x43
        inp._input.ki.dwFlags = KEYEVENTF_KEYUP
        inputs.append(inp)
        # Ctrl up
        inp = INPUT(type=INPUT_KEYBOARD)
        inp._input.ki.wVk = 0x11
        inp._input.ki.dwFlags = KEYEVENTF_KEYUP
        inputs.append(inp)

        n = len(inputs)
        arr = (INPUT * n)(*inputs)
        user32.SendInput(n, arr, ctypes.sizeof(INPUT))

        time.sleep(0.1)

        # 读取新剪贴板内容
        new_text = ''
        if user32.OpenClipboard(0):
            h = user32.GetClipboardData(CF_UNICODETEXT)
            if h:
                p = kernel32.GlobalLock(h)
                if p:
                    new_text = ctypes.wstring_at(p)
                    kernel32.GlobalUnlock(h)
            # 恢复旧剪贴板
            if old_text:
                user32.EmptyClipboard()
                data = old_text.encode('utf-16-le') + b'\x00\x00'
                hm = kernel32.GlobalAlloc(0x0042, len(data))
                if hm:
                    pm = kernel32.GlobalLock(hm)
                    ctypes.memmove(pm, data, len(data))
                    kernel32.GlobalUnlock(hm)
                    user32.SetClipboardData(CF_UNICODETEXT, hm)
            user32.CloseClipboard()

        if new_text and new_text != old_text:
            return new_text
        return ''
