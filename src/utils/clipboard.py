"""剪贴板操作工具"""

import ctypes
import ctypes.wintypes
from .logger import get_logger

logger = get_logger('clipboard')

CF_UNICODETEXT = 13


def get_text() -> str:
    """从剪贴板获取文本

    Returns:
        剪贴板中的文本内容，失败返回空字符串
    """
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    if not user32.OpenClipboard(0):
        logger.warning("Failed to open clipboard")
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
        except Exception as e:
            logger.error(f"Failed to read clipboard data: {e}")
            return ''
        finally:
            kernel32.GlobalUnlock(h)
    except Exception as e:
        logger.error(f"Clipboard operation error: {e}")
        return ''
    finally:
        user32.CloseClipboard()


def set_text(text: str) -> bool:
    """设置剪贴板文本

    Args:
        text: 要设置的文本内容

    Returns:
        成功返回 True，失败返回 False
    """
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32

    if not user32.OpenClipboard(0):
        logger.warning("Failed to open clipboard")
        return False

    try:
        user32.EmptyClipboard()
        data = text.encode('utf-16-le') + b'\x00\x00'
        h = kernel32.GlobalAlloc(0x0042, len(data))

        if not h:
            logger.error("Failed to allocate global memory")
            return False

        p = kernel32.GlobalLock(h)
        if not p:
            logger.error("Failed to lock global memory")
            return False

        try:
            ctypes.memmove(p, data, len(data))
        finally:
            kernel32.GlobalUnlock(h)

        if not user32.SetClipboardData(CF_UNICODETEXT, h):
            logger.error("Failed to set clipboard data")
            return False

        return True
    except Exception as e:
        logger.error(f"Failed to set clipboard: {e}")
        return False
    finally:
        user32.CloseClipboard()
