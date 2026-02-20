"""操作执行引擎"""

import os
import time
import ctypes
import ctypes.wintypes
import subprocess
import webbrowser
import threading


class ActionExecutor:
    """执行各类快捷操作"""

    def __init__(self, root=None, theme=None):
        self._root = root
        self._theme = theme
        self._on_feedback = None  # callback(msg) for toast

    def set_feedback_callback(self, cb):
        self._on_feedback = cb

    def execute(self, action: dict):
        """按 type 分发执行"""
        if not action:
            return
        t = action.get('type', '')
        handler = {
            'app': self._exec_app,
            'file': self._exec_file,
            'folder': self._exec_folder,
            'url': self._exec_url,
            'shell': self._exec_shell,
            'snippet': self._exec_snippet,
            'keys': self._exec_keys,
            'combo': self._exec_combo,
        }.get(t)
        if handler:
            threading.Thread(target=handler, args=(action,), daemon=True).start()

    def _feedback(self, msg: str):
        if self._on_feedback and self._root:
            self._root.after(0, self._on_feedback, msg)

    def _exec_app(self, action: dict):
        """启动应用程序"""
        target = action.get('target', '')
        if not target:
            return
        args = action.get('args', '')
        try:
            if action.get('admin'):
                ctypes.windll.shell32.ShellExecuteW(
                    None, 'runas', target, args, None, 1
                )
            else:
                if args:
                    ctypes.windll.shell32.ShellExecuteW(
                        None, 'open', target, args, None, 1
                    )
                else:
                    os.startfile(target)
        except Exception:
            self._feedback("Failed!")

    def _exec_file(self, action: dict):
        """打开文件"""
        target = action.get('target', '')
        if target:
            try:
                os.startfile(target)
            except Exception:
                self._feedback("Failed!")

    def _exec_folder(self, action: dict):
        """打开文件夹"""
        target = action.get('target', '')
        if target:
            try:
                os.startfile(target)
            except Exception:
                self._feedback("Failed!")

    def _exec_url(self, action: dict):
        """打开 URL"""
        target = action.get('target', '')
        if target:
            webbrowser.open(target)

    def _exec_shell(self, action: dict):
        """执行 shell 命令"""
        target = action.get('target', '')
        if not target:
            return
        shell_type = action.get('shell_type', 'cmd')

        if action.get('show_output') and self._root and self._theme:
            self._root.after(0, self._show_shell_output,
                             action.get('label', 'Shell'), target, shell_type)
            return

        if shell_type == 'powershell':
            subprocess.Popen(
                ['powershell', '-Command', target],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        elif shell_type == 'python':
            subprocess.Popen(
                ['python', '-c', target],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            subprocess.Popen(
                target, shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

    def _show_shell_output(self, title, command, shell_type):
        from ..dialogs.shell_output import ShellOutputDialog
        ShellOutputDialog(self._root, self._theme, title=title,
                          command=command, shell_type=shell_type)

    def _exec_snippet(self, action: dict):
        """复制文本到剪贴板"""
        target = action.get('target', '')
        if not target:
            return
        CF_UNICODETEXT = 13
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        if not user32.OpenClipboard(0):
            return
        try:
            user32.EmptyClipboard()
            data = target.encode('utf-16-le') + b'\x00\x00'
            h = kernel32.GlobalAlloc(0x0042, len(data))
            if h:
                p = kernel32.GlobalLock(h)
                ctypes.memmove(p, data, len(data))
                kernel32.GlobalUnlock(h)
                user32.SetClipboardData(CF_UNICODETEXT, h)
        finally:
            user32.CloseClipboard()
        self._feedback("Copied!")

    def _exec_keys(self, action: dict):
        """模拟按键"""
        target = action.get('target', '')
        if not target:
            return
        keys = _parse_keys(target)
        _send_keys(keys)
        self._feedback("Sent!")

    def _exec_combo(self, action: dict):
        """顺序执行组合动作"""
        steps = action.get('steps', [])
        delay = action.get('delay', 500) / 1000.0
        for i, step in enumerate(steps):
            if i > 0:
                time.sleep(delay)
            # combo 内部同步执行，不再开新线程
            t = step.get('type', '')
            handler = {
                'app': self._exec_app,
                'file': self._exec_file,
                'folder': self._exec_folder,
                'url': self._exec_url,
                'shell': self._exec_shell,
                'snippet': self._exec_snippet,
                'keys': self._exec_keys,
            }.get(t)
            if handler:
                handler(step)


# ── 按键模拟工具 ──

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001

VK_MAP = {
    'ctrl': 0x11, 'control': 0x11,
    'alt': 0x12, 'menu': 0x12,
    'shift': 0x10,
    'win': 0x5B, 'lwin': 0x5B,
    'tab': 0x09, 'enter': 0x0D, 'return': 0x0D,
    'esc': 0x1B, 'escape': 0x1B,
    'space': 0x20, 'backspace': 0x08, 'delete': 0x2E,
    'up': 0x26, 'down': 0x28, 'left': 0x25, 'right': 0x27,
    'home': 0x24, 'end': 0x23, 'pageup': 0x21, 'pagedown': 0x22,
    'insert': 0x2D, 'printscreen': 0x2C,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
    'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
    'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
}


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk', ctypes.wintypes.WORD),
        ('wScan', ctypes.wintypes.WORD),
        ('dwFlags', ctypes.wintypes.DWORD),
        ('time', ctypes.wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [('ki', KEYBDINPUT)]
    _fields_ = [
        ('type', ctypes.wintypes.DWORD),
        ('_input', _INPUT),
    ]


def _parse_keys(combo_str: str) -> list[int]:
    keys = []
    for part in combo_str.lower().split('+'):
        part = part.strip()
        if part in VK_MAP:
            keys.append(VK_MAP[part])
        elif len(part) == 1 and part.isalnum():
            keys.append(ord(part.upper()))
        elif part.startswith('0x'):
            try:
                keys.append(int(part, 16))
            except ValueError:
                pass
    return keys


def _send_keys(vk_codes: list[int]):
    if not vk_codes:
        return
    inputs = []
    for vk in vk_codes:
        inp = INPUT(type=INPUT_KEYBOARD)
        inp._input.ki.wVk = vk
        inp._input.ki.dwFlags = 0
        inputs.append(inp)
    for vk in reversed(vk_codes):
        inp = INPUT(type=INPUT_KEYBOARD)
        inp._input.ki.wVk = vk
        inp._input.ki.dwFlags = KEYEVENTF_KEYUP
        inputs.append(inp)
    n = len(inputs)
    arr = (INPUT * n)(*inputs)
    ctypes.windll.user32.SendInput(n, arr, ctypes.sizeof(INPUT))
