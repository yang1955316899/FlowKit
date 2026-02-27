"""输入捕获工具 - 坐标拾取器（从 dialogs/step_editor.py 提取）"""

import ctypes
import ctypes.wintypes
import threading
from .hotkey import HOOKPROC, MSLLHOOKSTRUCT, WH_MOUSE_LL, HC_ACTION


class CoordinatePicker:
    """鼠标坐标拾取器 - 使用 Windows hook 捕获鼠标点击"""

    def __init__(self):
        self.result = None
        self.hook_handle = None

    def pick(self, timeout: int = 30) -> tuple[int, int] | None:
        """
        拾取屏幕坐标

        Args:
            timeout: 超时时间（秒）

        Returns:
            (x, y) 坐标元组，超时或取消返回 None
        """
        result = [None]
        hook_handle = [None]

        def mouse_proc(nCode, wParam, lParam):
            if nCode == HC_ACTION and wParam == 0x0201:  # WM_LBUTTONDOWN
                info = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                result[0] = (info.pt.x, info.pt.y)
                # 卸载 hook
                if hook_handle[0]:
                    ctypes.windll.user32.UnhookWindowsHookEx(hook_handle[0])
                    hook_handle[0] = None
                ctypes.windll.user32.PostThreadMessageW(
                    ctypes.windll.kernel32.GetCurrentThreadId(), 0x0012, 0, 0)  # WM_QUIT
                return 1  # 吞掉这次点击
            return ctypes.windll.user32.CallNextHookEx(
                hook_handle[0], nCode, wParam, lParam)

        proc = HOOKPROC(mouse_proc)

        def run_hook():
            hook_handle[0] = ctypes.windll.user32.SetWindowsHookExW(
                WH_MOUSE_LL, proc, None, 0)
            msg = ctypes.wintypes.MSG()
            while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
            if hook_handle[0]:
                ctypes.windll.user32.UnhookWindowsHookEx(hook_handle[0])

        t = threading.Thread(target=run_hook, daemon=True)
        t.start()
        t.join(timeout=timeout)

        return result[0]
