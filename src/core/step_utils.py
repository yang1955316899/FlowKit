"""步骤工具函数 - 从 dialogs/enhanced_combo_editor.py 提取"""

from .step_types import STEP_TYPES


def step_summary(step: dict) -> str:
    """生成步骤的简短描述"""
    t = step.get('type', '?')
    if t == 'delay':
        return f"{step.get('ms', 0)}ms"
    elif t == 'set_var':
        return f"{step.get('name', '')} = {step.get('value', '')}"
    elif t == 'get_clipboard':
        return f"→ {step.get('var', '')}"
    elif t == 'set_clipboard':
        v = step.get('value', '')
        return v[:20] + ('...' if len(v) > 20 else '')
    elif t in ('mouse_click', 'mouse_move', 'mouse_double_click'):
        btn = f" {step.get('button', '')}" if t == 'mouse_click' else ''
        return f"({step.get('x', 0)}, {step.get('y', 0)}){btn}"
    elif t == 'mouse_scroll':
        return f"({step.get('x', 0)}, {step.get('y', 0)}) delta={step.get('delta', 0)}"
    elif t == 'wait_window':
        return f'"{step.get("title", "")}"'
    elif t == 'wait_pixel':
        return f"({step.get('x', 0)},{step.get('y', 0)}) {step.get('color', '')}"
    elif t == 'if_condition':
        cond = step.get('condition', {})
        src = cond.get('source', '')
        op = cond.get('op', '')
        val = cond.get('value', '')
        return f'{src} {op} "{val}"'
    elif t == 'loop':
        mode = step.get('mode', 'count')
        if mode == 'count':
            return f"{step.get('count', 0)} 次"
        return "条件循环"
    elif t in ('app', 'keys', 'snippet', 'shell', 'url'):
        label = step.get('label', '') or step.get('target', '')
        return label[:20] + ('...' if len(label) > 20 else '')
    elif t == 'type_text':
        txt = step.get('text', '')
        return txt[:20] + ('...' if len(txt) > 20 else '')
    elif t == 'toast':
        msg = step.get('message', '')
        return msg[:20] + ('...' if len(msg) > 20 else '')
    elif t == 'window_activate':
        return f'"{step.get("title", "")}"'
    elif t == 'screenshot':
        return step.get('path', '') or '截屏'
    elif t == 'http_request':
        m = step.get('method', 'GET')
        u = step.get('url', '')
        return f"{m} {u[:16]}{'...' if len(u) > 16 else ''}"
    elif t == 'file_read':
        return step.get('path', '')[:20]
    elif t == 'file_write':
        return step.get('path', '')[:20]
    return ''


def step_type_name(stype: str) -> str:
    """获取步骤类型的中文名称"""
    return dict((t, n) for t, n, _ in STEP_TYPES).get(stype, stype)


def step_icon(stype: str) -> str:
    """获取步骤类型的图标"""
    return dict((t, i) for t, _, i in STEP_TYPES).get(stype, '▸')
