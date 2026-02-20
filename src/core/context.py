"""上下文感知 — 检测前台窗口进程，自动切换到匹配的动作页"""

import ctypes
import ctypes.wintypes
import os


def get_foreground_process() -> str:
    """获取当前前台窗口的进程名（如 Code.exe）"""
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return ''

    pid = ctypes.wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if not pid.value:
        return ''

    # 打开进程获取可执行文件名
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value)
    if not handle:
        return ''

    try:
        buf = ctypes.create_unicode_buffer(260)
        size = ctypes.wintypes.DWORD(260)
        # QueryFullProcessImageNameW
        kernel32.QueryFullProcessImageNameW(handle, 0, buf, ctypes.byref(size))
        full_path = buf.value
        return os.path.basename(full_path) if full_path else ''
    finally:
        kernel32.CloseHandle(handle)


def find_context_page(pages: list, process_name: str) -> int | None:
    """在页面列表中查找匹配当前进程的页面索引

    Args:
        pages: config 中的 pages 列表
        process_name: 当前前台进程名

    Returns:
        匹配的页面索引，无匹配返回 None
    """
    if not process_name:
        return None

    pname = process_name.lower()
    for i, page in enumerate(pages):
        ctx = page.get('context', '')
        if not ctx:
            continue
        # 支持逗号分隔多个进程名
        targets = [t.strip().lower() for t in ctx.split(',')]
        if pname in targets:
            return i
    return None
