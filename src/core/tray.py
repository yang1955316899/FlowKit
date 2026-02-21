"""系统托盘图标 — 使用 ctypes Shell_NotifyIconW"""

import ctypes
import ctypes.wintypes
import threading


# Shell_NotifyIconW 常量
NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
NIF_INFO = 0x00000010

WM_USER = 0x0400
WM_TRAYICON = WM_USER + 20
WM_COMMAND = 0x0111
WM_DESTROY = 0x0002

WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
WM_LBUTTONDBLCLK = 0x0203

# Menu
MF_STRING = 0x0000
MF_SEPARATOR = 0x0800
TPM_LEFTALIGN = 0x0000
TPM_RETURNCMD = 0x0100

IDI_APPLICATION = 32512

user32 = ctypes.windll.user32
shell32 = ctypes.windll.shell32
kernel32 = ctypes.windll.kernel32

# 设置 DefWindowProcW 的参数类型，避免 64 位 LPARAM 溢出
user32.DefWindowProcW.argtypes = [
    ctypes.wintypes.HWND, ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM, ctypes.wintypes.LPARAM,
]
user32.DefWindowProcW.restype = ctypes.c_longlong


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.wintypes.DWORD),
        ('hWnd', ctypes.wintypes.HWND),
        ('uID', ctypes.wintypes.UINT),
        ('uFlags', ctypes.wintypes.UINT),
        ('uCallbackMessage', ctypes.wintypes.UINT),
        ('hIcon', ctypes.wintypes.HICON),
        ('szTip', ctypes.c_wchar * 128),
        ('dwState', ctypes.wintypes.DWORD),
        ('dwStateMask', ctypes.wintypes.DWORD),
        ('szInfo', ctypes.c_wchar * 256),
        ('uVersion', ctypes.wintypes.UINT),
        ('szInfoTitle', ctypes.c_wchar * 64),
        ('dwInfoFlags', ctypes.wintypes.DWORD),
    ]


# 窗口过程 — 64 位 Windows 需要 LRESULT (c_longlong)
LRESULT = ctypes.c_longlong
WNDPROC = ctypes.WINFUNCTYPE(
    LRESULT,
    ctypes.wintypes.HWND,
    ctypes.wintypes.UINT,
    ctypes.wintypes.WPARAM,
    ctypes.wintypes.LPARAM,
)


class WNDCLASSEXW(ctypes.Structure):
    _fields_ = [
        ('cbSize', ctypes.wintypes.UINT),
        ('style', ctypes.wintypes.UINT),
        ('lpfnWndProc', WNDPROC),
        ('cbClsExtra', ctypes.c_int),
        ('cbWndExtra', ctypes.c_int),
        ('hInstance', ctypes.wintypes.HINSTANCE),
        ('hIcon', ctypes.wintypes.HICON),
        ('hCursor', ctypes.wintypes.HANDLE),
        ('hbrBackground', ctypes.wintypes.HBRUSH),
        ('lpszMenuName', ctypes.wintypes.LPCWSTR),
        ('lpszClassName', ctypes.wintypes.LPCWSTR),
        ('hIconSm', ctypes.wintypes.HICON),
    ]


# 菜单命令 ID
CMD_SHOW = 1001
CMD_SETTINGS = 1002
CMD_EXIT = 1003


class SystemTray:
    """系统托盘图标"""

    def __init__(self, on_show=None, on_settings=None, on_exit=None):
        self._on_show = on_show
        self._on_settings = on_settings
        self._on_exit = on_exit
        self._hwnd = None
        self._nid = None
        self._running = False
        self._wndproc = None  # prevent GC
        self._thread = None

    def start(self):
        """在后台线程中创建托盘图标"""
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """移除托盘图标"""
        self._running = False
        if self._hwnd:
            user32.PostMessageW(self._hwnd, WM_DESTROY, 0, 0)

    def _run(self):
        hinstance = kernel32.GetModuleHandleW(None)
        class_name = 'MonitorTrayClass'

        self._wndproc = WNDPROC(self._wnd_proc)

        wc = WNDCLASSEXW()
        wc.cbSize = ctypes.sizeof(WNDCLASSEXW)
        wc.lpfnWndProc = self._wndproc
        wc.hInstance = hinstance
        wc.lpszClassName = class_name

        user32.RegisterClassExW(ctypes.byref(wc))

        self._hwnd = user32.CreateWindowExW(
            0, class_name, 'MonitorTray', 0,
            0, 0, 0, 0, None, None, hinstance, None
        )

        # 创建托盘图标
        nid = NOTIFYICONDATAW()
        nid.cbSize = ctypes.sizeof(NOTIFYICONDATAW)
        nid.hWnd = self._hwnd
        nid.uID = 1
        nid.uFlags = NIF_MESSAGE | NIF_ICON | NIF_TIP
        nid.uCallbackMessage = WM_TRAYICON
        nid.hIcon = user32.LoadIconW(None, IDI_APPLICATION)
        nid.szTip = '监控台'
        shell32.Shell_NotifyIconW(NIM_ADD, ctypes.byref(nid))
        self._nid = nid

        # 消息循环
        msg = ctypes.wintypes.MSG()
        while self._running:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret <= 0:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        # 清理
        shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(nid))

    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        if msg == WM_TRAYICON:
            if lparam == WM_RBUTTONUP:
                self._show_menu()
                return 0
            elif lparam == WM_LBUTTONDBLCLK:
                if self._on_show:
                    self._on_show()
                return 0
        elif msg == WM_COMMAND:
            cmd = wparam & 0xFFFF
            if cmd == CMD_SHOW and self._on_show:
                self._on_show()
            elif cmd == CMD_SETTINGS and self._on_settings:
                self._on_settings()
            elif cmd == CMD_EXIT and self._on_exit:
                self._on_exit()
            return 0
        elif msg == WM_DESTROY:
            user32.PostQuitMessage(0)
            return 0
        return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

    def _show_menu(self):
        menu = user32.CreatePopupMenu()
        user32.AppendMenuW(menu, MF_STRING, CMD_SHOW, '显示面板')
        user32.AppendMenuW(menu, MF_STRING, CMD_SETTINGS, '设置')
        user32.AppendMenuW(menu, MF_SEPARATOR, 0, None)
        user32.AppendMenuW(menu, MF_STRING, CMD_EXIT, '退出')

        pt = ctypes.wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))

        # 必须先 SetForegroundWindow 否则菜单不会消失
        user32.SetForegroundWindow(self._hwnd)
        cmd = user32.TrackPopupMenu(
            menu, TPM_LEFTALIGN | TPM_RETURNCMD,
            pt.x, pt.y, 0, self._hwnd, None
        )
        user32.DestroyMenu(menu)

        if cmd:
            user32.PostMessageW(self._hwnd, WM_COMMAND, cmd, 0)
