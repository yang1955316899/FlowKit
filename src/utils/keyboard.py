"""按键模拟工具"""

import ctypes
import ctypes.wintypes
from .logger import get_logger

logger = get_logger('keyboard')

# 常量
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_UNICODE = 0x0004

# 虚拟键码映射
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

# 反向映射（用于录制）
VK_NAMES = {
    0x08: 'backspace', 0x09: 'tab', 0x0D: 'enter', 0x1B: 'esc',
    0x20: 'space', 0x21: 'pageup', 0x22: 'pagedown',
    0x23: 'end', 0x24: 'home',
    0x25: 'left', 0x26: 'up', 0x27: 'right', 0x28: 'down',
    0x2C: 'printscreen', 0x2D: 'insert', 0x2E: 'delete',
    0x5B: 'win',
    0x70: 'f1', 0x71: 'f2', 0x72: 'f3', 0x73: 'f4',
    0x74: 'f5', 0x75: 'f6', 0x76: 'f7', 0x77: 'f8',
    0x78: 'f9', 0x79: 'f10', 0x7A: 'f11', 0x7B: 'f12',
    0x10: 'shift', 0x11: 'ctrl', 0x12: 'alt',
    0xA0: 'shift', 0xA1: 'shift',  # L/R shift
    0xA2: 'ctrl', 0xA3: 'ctrl',    # L/R ctrl
    0xA4: 'alt', 0xA5: 'alt',      # L/R alt
}


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ('wVk', ctypes.wintypes.WORD),
        ('wScan', ctypes.wintypes.WORD),
        ('dwFlags', ctypes.wintypes.DWORD),
        ('time', ctypes.wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)),
    ]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ('dx', ctypes.wintypes.LONG),
        ('dy', ctypes.wintypes.LONG),
        ('mouseData', ctypes.wintypes.DWORD),
        ('dwFlags', ctypes.wintypes.DWORD),
        ('time', ctypes.wintypes.DWORD),
        ('dwExtraInfo', ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [('ki', KEYBDINPUT), ('mi', MOUSEINPUT)]
    _fields_ = [
        ('type', ctypes.wintypes.DWORD),
        ('_input', _INPUT),
    ]


def parse_keys(combo_str: str) -> list[int]:
    """解析按键组合字符串

    Args:
        combo_str: 按键组合，如 'ctrl+c', 'alt+f4'

    Returns:
        虚拟键码列表
    """
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
                logger.warning(f"Invalid hex key code: {part}")
    return keys


def send_keys(vk_codes: list[int]) -> bool:
    """发送按键序列

    Args:
        vk_codes: 虚拟键码列表

    Returns:
        成功返回 True
    """
    if not vk_codes:
        logger.warning("Empty key codes")
        return False

    try:
        inputs = []

        # 按下所有键
        for vk in vk_codes:
            inp = INPUT(type=INPUT_KEYBOARD)
            inp._input.ki.wVk = vk
            inp._input.ki.dwFlags = 0
            inputs.append(inp)

        # 释放所有键（逆序）
        for vk in reversed(vk_codes):
            inp = INPUT(type=INPUT_KEYBOARD)
            inp._input.ki.wVk = vk
            inp._input.ki.dwFlags = KEYEVENTF_KEYUP
            inputs.append(inp)

        n = len(inputs)
        arr = (INPUT * n)(*inputs)
        sent = ctypes.windll.user32.SendInput(n, arr, ctypes.sizeof(INPUT))

        if sent != n:
            logger.warning(f"Only sent {sent}/{n} inputs")
            return False

        return True
    except Exception as e:
        logger.error(f"Failed to send keys: {e}")
        return False


def send_combo(combo_str: str) -> bool:
    """发送按键组合

    Args:
        combo_str: 按键组合字符串，如 'ctrl+c'

    Returns:
        成功返回 True
    """
    keys = parse_keys(combo_str)
    return send_keys(keys)


def vk_list_to_str(vk_codes: list[int]) -> str:
    """将虚拟键码列表转换为按键字符串

    Args:
        vk_codes: 虚拟键码列表

    Returns:
        按键组合字符串，如 'ctrl+c'
    """
    parts = []
    modifiers = {0x10, 0x11, 0x12, 0x5B, 0xA0, 0xA1, 0xA2, 0xA3, 0xA4, 0xA5}
    mod_parts = []
    key_parts = []

    for vk in vk_codes:
        name = VK_NAMES.get(vk)
        if name:
            if vk in modifiers:
                if name not in mod_parts:
                    mod_parts.append(name)
            else:
                key_parts.append(name)
        elif 0x30 <= vk <= 0x39:  # 0-9
            key_parts.append(chr(vk))
        elif 0x41 <= vk <= 0x5A:  # A-Z
            key_parts.append(chr(vk).lower())

    parts = mod_parts + key_parts
    return '+'.join(parts) if parts else ''
