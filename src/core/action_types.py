"""动作类型枚举"""

from enum import Enum


class ActionType(str, Enum):
    """动作类型枚举"""
    APP = 'app'
    FILE = 'file'
    FOLDER = 'folder'
    URL = 'url'
    SHELL = 'shell'
    SNIPPET = 'snippet'
    KEYS = 'keys'
    COMBO = 'combo'
    SCRIPT = 'script'


class StepType(str, Enum):
    """步骤类型枚举（用于 combo 流程）"""
    # 基础步骤
    DELAY = 'delay'
    KEYS = 'keys'
    SNIPPET = 'snippet'

    # 变量操作
    SET_VAR = 'set_var'
    GET_CLIPBOARD = 'get_clipboard'
    SET_CLIPBOARD = 'set_clipboard'

    # 鼠标操作
    MOUSE_CLICK = 'mouse_click'
    MOUSE_DOUBLE_CLICK = 'mouse_double_click'
    MOUSE_MOVE = 'mouse_move'
    MOUSE_SCROLL = 'mouse_scroll'

    # 窗口操作
    WAIT_WINDOW = 'wait_window'
    WAIT_PIXEL = 'wait_pixel'
    WINDOW_ACTIVATE = 'window_activate'

    # 流程控制
    IF_CONDITION = 'if_condition'
    LOOP = 'loop'

    # 高级操作
    TYPE_TEXT = 'type_text'
    TOAST = 'toast'
    SCREENSHOT = 'screenshot'
    HTTP_REQUEST = 'http_request'
    FILE_READ = 'file_read'
    FILE_WRITE = 'file_write'

    # 原有动作类型（委托）
    APP = 'app'
    FILE = 'file'
    FOLDER = 'folder'
    URL = 'url'
    SHELL = 'shell'
    SCRIPT = 'script'


class ShellType(str, Enum):
    """Shell 类型枚举"""
    CMD = 'cmd'
    POWERSHELL = 'powershell'
    PYTHON = 'python'


class ScriptMode(str, Enum):
    """脚本模式枚举"""
    INLINE = 'inline'
    FILE = 'file'
