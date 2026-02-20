"""多显示器检测"""

import ctypes
from typing import Callable


def get_monitors() -> list[tuple[int, int, int, int]]:
    """获取所有显示器边界 (left, top, right, bottom)"""
    monitors = []

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

    def callback(hmon, hdc, lprect, lparam):
        rect = lprect.contents
        monitors.append((rect.left, rect.top, rect.right, rect.bottom))
        return True

    try:
        user32 = ctypes.windll.user32

        class RECT(ctypes.Structure):
            _fields_ = [
                ('left', ctypes.c_long),
                ('top', ctypes.c_long),
                ('right', ctypes.c_long),
                ('bottom', ctypes.c_long),
            ]

        MonitorEnumProc = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            ctypes.c_ulong,
            ctypes.c_ulong,
            ctypes.POINTER(RECT),
            ctypes.c_double,
        )

        user32.EnumDisplayMonitors(
            None, None, MonitorEnumProc(callback), 0
        )
    except Exception:
        pass

    return monitors if monitors else [(0, 0, 1920, 1080)]
