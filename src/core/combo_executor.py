"""增强组合执行引擎 — 支持流程控制、变量系统、条件分支、循环"""

import re
import time
import ctypes
import ctypes.wintypes


class ComboExecutor:
    """执行增强型 combo 步骤列表，支持变量、条件、循环等流程控制"""

    def __init__(self, action_executor):
        self._executor = action_executor
        self._variables: dict[str, str] = {}
        self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    def execute(self, action: dict):
        """执行 combo 动作"""
        self._variables.clear()
        self._stop_flag = False
        steps = action.get('steps', [])
        delay = action.get('delay', 500) / 1000.0
        self._execute_steps(steps, delay)

    def _execute_steps(self, steps: list, delay: float):
        for i, step in enumerate(steps):
            if self._stop_flag:
                return
            if i > 0:
                time.sleep(delay)
            self._execute_one(step, delay)

    def _execute_one(self, step: dict, delay: float):
        if not step or self._stop_flag:
            return
        stype = step.get('type', '')

        # 新增流程控制步骤
        handler = {
            'delay': self._exec_delay,
            'set_var': self._exec_set_var,
            'get_clipboard': self._exec_get_clipboard,
            'set_clipboard': self._exec_set_clipboard,
            'mouse_click': self._exec_mouse_click,
            'mouse_move': self._exec_mouse_move,
            'wait_window': self._exec_wait_window,
            'wait_pixel': self._exec_wait_pixel,
            'if_condition': self._exec_if_condition,
            'loop': self._exec_loop,
        }.get(stype)

        if handler:
            handler(step, delay)
        else:
            # 委托给原有动作处理器
            interpolated = self._interpolate_step(step)
            self._exec_legacy(interpolated)

    def _exec_legacy(self, step: dict):
        """委托给 ActionExecutor 的原有处理器"""
        t = step.get('type', '')
        handler_map = {
            'app': self._executor._exec_app,
            'file': self._executor._exec_file,
            'folder': self._executor._exec_folder,
            'url': self._executor._exec_url,
            'shell': self._executor._exec_shell,
            'snippet': self._executor._exec_snippet,
            'keys': self._executor._exec_keys,
            'script': self._executor._exec_script,
        }
        handler = handler_map.get(t)
        if handler:
            handler(step)

    # ── 变量插值 ──

    def _interpolate(self, text: str) -> str:
        if not text or '{{' not in text:
            return text
        return re.sub(r'\{\{(\w+)\}\}',
                      lambda m: self._variables.get(m.group(1), m.group(0)),
                      text)

    def _interpolate_step(self, step: dict) -> dict:
        """对步骤中所有字符串字段进行变量插值"""
        result = {}
        for k, v in step.items():
            if isinstance(v, str):
                result[k] = self._interpolate(v)
            else:
                result[k] = v
        return result

    # ── 流程控制步骤 ──

    def _exec_delay(self, step: dict, delay: float):
        ms = step.get('ms', 1000)
        time.sleep(ms / 1000.0)

    def _exec_set_var(self, step: dict, delay: float):
        name = step.get('name', '')
        value = self._interpolate(str(step.get('value', '')))
        if name:
            self._variables[name] = value

    def _exec_get_clipboard(self, step: dict, delay: float):
        var_name = step.get('var', '')
        if not var_name:
            return
        text = self._clipboard_get_text()
        self._variables[var_name] = text

    def _exec_set_clipboard(self, step: dict, delay: float):
        value = self._interpolate(str(step.get('value', '')))
        self._clipboard_set_text(value)

    def _exec_mouse_click(self, step: dict, delay: float):
        x = int(self._interpolate(str(step.get('x', 0))))
        y = int(self._interpolate(str(step.get('y', 0))))
        button = step.get('button', 'left')
        ctypes.windll.user32.SetCursorPos(x, y)
        time.sleep(0.05)
        if button == 'right':
            ctypes.windll.user32.mouse_event(0x0008, 0, 0, 0, 0)  # RIGHTDOWN
            ctypes.windll.user32.mouse_event(0x0010, 0, 0, 0, 0)  # RIGHTUP
        elif button == 'middle':
            ctypes.windll.user32.mouse_event(0x0020, 0, 0, 0, 0)  # MIDDLEDOWN
            ctypes.windll.user32.mouse_event(0x0040, 0, 0, 0, 0)  # MIDDLEUP
        else:
            ctypes.windll.user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
            ctypes.windll.user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP

    def _exec_mouse_move(self, step: dict, delay: float):
        x = int(self._interpolate(str(step.get('x', 0))))
        y = int(self._interpolate(str(step.get('y', 0))))
        ctypes.windll.user32.SetCursorPos(x, y)

    def _exec_wait_window(self, step: dict, delay: float):
        title = self._interpolate(step.get('title', ''))
        timeout = step.get('timeout', 5000)
        start = time.time()
        while not self._stop_flag:
            current_title = self._get_foreground_title()
            if title.lower() in current_title.lower():
                return
            if (time.time() - start) * 1000 >= timeout:
                return
            time.sleep(0.1)

    def _exec_wait_pixel(self, step: dict, delay: float):
        x = step.get('x', 0)
        y = step.get('y', 0)
        target_color = step.get('color', '#000000').lower()
        tolerance = step.get('tolerance', 10)
        timeout = step.get('timeout', 5000)
        start = time.time()
        while not self._stop_flag:
            current = self._get_pixel_color(x, y)
            if self._color_match(current, target_color, tolerance):
                return
            if (time.time() - start) * 1000 >= timeout:
                return
            time.sleep(0.1)

    def _exec_if_condition(self, step: dict, delay: float):
        condition = step.get('condition', {})
        if self._eval_condition(condition):
            then_steps = step.get('then_steps', [])
            self._execute_steps(then_steps, delay)
        else:
            else_steps = step.get('else_steps', [])
            self._execute_steps(else_steps, delay)

    def _exec_loop(self, step: dict, delay: float):
        mode = step.get('mode', 'count')
        max_iter = step.get('max_iterations', 100)
        body = step.get('body_steps', [])

        if mode == 'count':
            count = step.get('count', 1)
            for i in range(min(count, max_iter)):
                if self._stop_flag:
                    return
                self._variables['_loop_index'] = str(i)
                self._execute_steps(body, delay)
        elif mode == 'while_condition':
            condition = step.get('condition', {})
            iterations = 0
            while not self._stop_flag and iterations < max_iter:
                if not self._eval_condition(condition):
                    break
                self._variables['_loop_index'] = str(iterations)
                self._execute_steps(body, delay)
                iterations += 1

    # ── 条件求值 ──

    def _eval_condition(self, cond: dict) -> bool:
        source = cond.get('source', '')
        op = cond.get('op', 'contains')
        value = self._interpolate(str(cond.get('value', '')))

        # 获取当前值
        if source == 'window_title':
            current = self._get_foreground_title()
        elif source == 'process_name':
            current = self._get_foreground_process()
        elif source == 'clipboard':
            current = self._clipboard_get_text()
        elif source == 'variable':
            var_name = cond.get('var_name', '')
            current = self._variables.get(var_name, '')
        else:
            current = ''

        # 比较
        if op == 'contains':
            return value.lower() in current.lower()
        elif op == 'equals':
            return current.lower() == value.lower()
        elif op == 'starts_with':
            return current.lower().startswith(value.lower())
        elif op == 'not_contains':
            return value.lower() not in current.lower()
        return False

    # ── 平台工具方法 ──

    @staticmethod
    def _get_foreground_title() -> str:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if not hwnd:
            return ''
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, 256)
        return buf.value

    @staticmethod
    def _get_foreground_process() -> str:
        from .context import get_foreground_process
        return get_foreground_process()

    @staticmethod
    def _clipboard_get_text() -> str:
        CF_UNICODETEXT = 13
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        if not user32.OpenClipboard(0):
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
            finally:
                kernel32.GlobalUnlock(h)
        finally:
            user32.CloseClipboard()

    @staticmethod
    def _clipboard_set_text(text: str):
        CF_UNICODETEXT = 13
        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        if not user32.OpenClipboard(0):
            return
        try:
            user32.EmptyClipboard()
            data = text.encode('utf-16-le') + b'\x00\x00'
            h = kernel32.GlobalAlloc(0x0042, len(data))
            if h:
                p = kernel32.GlobalLock(h)
                ctypes.memmove(p, data, len(data))
                kernel32.GlobalUnlock(h)
                user32.SetClipboardData(CF_UNICODETEXT, h)
        finally:
            user32.CloseClipboard()

    @staticmethod
    def _get_pixel_color(x: int, y: int) -> str:
        hdc = ctypes.windll.user32.GetDC(0)
        color = ctypes.windll.gdi32.GetPixel(hdc, x, y)
        ctypes.windll.user32.ReleaseDC(0, hdc)
        r = color & 0xFF
        g = (color >> 8) & 0xFF
        b = (color >> 16) & 0xFF
        return f'#{r:02x}{g:02x}{b:02x}'

    @staticmethod
    def _color_match(c1: str, c2: str, tolerance: int) -> bool:
        try:
            r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
            r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
            return (abs(r1 - r2) <= tolerance and
                    abs(g1 - g2) <= tolerance and
                    abs(b1 - b2) <= tolerance)
        except (ValueError, IndexError):
            return False
