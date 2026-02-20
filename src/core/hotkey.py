"""全局热键 + 鼠标中键钩子 (ctypes)"""

import ctypes
import ctypes.wintypes
import threading

WM_HOTKEY = 0x0312
WH_MOUSE_LL = 14
WM_MBUTTONDOWN = 0x0207
HC_ACTION = 0

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# 设置 CallNextHookEx 的参数类型，防止 64 位指针溢出
user32.CallNextHookEx.argtypes = [
    ctypes.wintypes.HHOOK,
    ctypes.c_int,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
]
user32.CallNextHookEx.restype = ctypes.wintypes.LPARAM

user32.SetWindowsHookExW.argtypes = [
    ctypes.c_int,
    ctypes.c_void_p,
    ctypes.wintypes.HINSTANCE,
    ctypes.wintypes.DWORD,
]
user32.SetWindowsHookExW.restype = ctypes.wintypes.HHOOK

# 修饰键映射
MOD_MAP = {
    'alt': 0x0001,
    'ctrl': 0x0002, 'control': 0x0002,
    'shift': 0x0004,
    'win': 0x0008,
}

# 虚拟键码映射
VK_MAP = {
    'space': 0x20, 'tab': 0x09, 'enter': 0x0D, 'return': 0x0D,
    'esc': 0x1B, 'escape': 0x1B,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73,
    'f5': 0x74, 'f6': 0x75, 'f7': 0x76, 'f8': 0x77,
    'f9': 0x78, 'f10': 0x79, 'f11': 0x7A, 'f12': 0x7B,
}

# HOOKPROC: 使用 LPARAM (c_ssize_t) 确保 64 位兼容
HOOKPROC = ctypes.CFUNCTYPE(
    ctypes.wintypes.LPARAM,   # return type
    ctypes.c_int,             # nCode
    ctypes.wintypes.WPARAM,   # wParam
    ctypes.wintypes.LPARAM,   # lParam
)


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ('pt', ctypes.wintypes.POINT),
        ('mouseData', ctypes.wintypes.DWORD),
        ('flags', ctypes.wintypes.DWORD),
        ('time', ctypes.wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)),
    ]


class InputHookManager:
    """全局热键 + 鼠标钩子管理器"""

    def __init__(self):
        self._hotkey_id = 1
        self._hotkeys: dict[int, tuple] = {}  # id -> (mods, vk, callback)
        self._middle_click_cb = None
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._running = False
        self._mouse_hook = None
        self._hook_proc = None  # prevent GC

    def register_hotkey(self, hotkey_str: str, callback):
        """注册全局热键，如 'ctrl+space'"""
        mods, vk = self._parse_hotkey(hotkey_str)
        if vk:
            hid = self._hotkey_id
            self._hotkeys[hid] = (mods, vk, callback)
            self._hotkey_id += 1

    def register_middle_click(self, callback):
        """注册鼠标中键回调"""
        self._middle_click_cb = callback

    def start(self):
        """启动后台线程"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """停止"""
        self._running = False
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, 0x0012, 0, 0)  # WM_QUIT

    def _run(self):
        """后台线程：注册热键 + 鼠标钩子 + 消息循环"""
        self._thread_id = kernel32.GetCurrentThreadId()

        # 注册热键
        for hid, (mods, vk, _) in self._hotkeys.items():
            user32.RegisterHotKey(None, hid, mods, vk)

        # 安装鼠标钩子
        if self._middle_click_cb:
            self._hook_proc = HOOKPROC(self._mouse_proc)
            self._mouse_hook = user32.SetWindowsHookExW(
                WH_MOUSE_LL, self._hook_proc, None, 0
            )

        # 消息循环
        msg = ctypes.wintypes.MSG()
        while self._running:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret <= 0:
                break
            if msg.message == WM_HOTKEY:
                hid = msg.wParam
                entry = self._hotkeys.get(hid)
                if entry:
                    entry[2]()  # callback
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        # 清理
        for hid in self._hotkeys:
            user32.UnregisterHotKey(None, hid)
        if self._mouse_hook:
            user32.UnhookWindowsHookEx(self._mouse_hook)
            self._mouse_hook = None

    def _mouse_proc(self, nCode, wParam, lParam):
        """鼠标钩子回调"""
        if nCode == HC_ACTION and wParam == WM_MBUTTONDOWN:
            if self._middle_click_cb:
                self._middle_click_cb()
        return user32.CallNextHookEx(self._mouse_hook, nCode, wParam, lParam)

    @staticmethod
    def _parse_hotkey(hotkey_str: str) -> tuple[int, int]:
        """解析热键字符串，返回 (modifiers, vk)"""
        parts = [p.strip().lower() for p in hotkey_str.split('+')]
        mods = 0
        vk = 0
        for part in parts:
            if part in MOD_MAP:
                mods |= MOD_MAP[part]
            elif part in VK_MAP:
                vk = VK_MAP[part]
            elif len(part) == 1 and part.isalnum():
                vk = ord(part.upper())
        return mods, vk
