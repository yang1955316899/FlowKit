"""键鼠录制引擎 — WH_KEYBOARD_LL + WH_MOUSE_LL 双 Hook 录制"""

import ctypes
import ctypes.wintypes
import threading
import time
from ..utils.logger import get_logger
from ..utils.keyboard import VK_NAMES, vk_list_to_str

from .hotkey import (
    HOOKPROC, MSLLHOOKSTRUCT, KBDLLHOOKSTRUCT,
    WH_MOUSE_LL, WH_KEYBOARD_LL, HC_ACTION, LLKHF_INJECTED,
    WM_LBUTTONDOWN, WM_LBUTTONUP, WM_RBUTTONDOWN, WM_RBUTTONUP,
    WM_MOUSEMOVE, WM_MOUSEWHEEL, WM_KEYDOWN, WM_KEYUP,
    WM_SYSKEYDOWN, WM_SYSKEYUP,
    user32, kernel32,
)

logger = get_logger('recorder')


class RawEvent:
    """原始输入事件"""
    __slots__ = ('kind', 'time', 'x', 'y', 'vk', 'button', 'delta')

    def __init__(self, kind, timestamp, **kw):
        self.kind = kind        # 'key_down', 'key_up', 'mouse_down', 'mouse_up', 'mouse_move', 'wheel'
        self.time = timestamp
        self.x = kw.get('x', 0)
        self.y = kw.get('y', 0)
        self.vk = kw.get('vk', 0)
        self.button = kw.get('button', '')
        self.delta = kw.get('delta', 0)


class InputRecorder:
    """键鼠录制器"""

    def __init__(self):
        self._events: list[RawEvent] = []
        self._recording = False
        self._paused = False
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self._mouse_hook = None
        self._kb_hook = None
        self._mouse_proc = None  # prevent GC
        self._kb_proc = None
        self._on_event = None  # callback(event_count)

    @property
    def event_count(self) -> int:
        return len(self._events)

    @property
    def is_recording(self) -> bool:
        return self._recording

    def set_event_callback(self, cb):
        self._on_event = cb

    def start(self):
        """开始录制"""
        if self._recording:
            return
        self._events.clear()
        self._recording = True
        self._paused = False
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def pause(self):
        self._paused = not self._paused

    def stop(self):
        """停止录制"""
        self._recording = False
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, 0x0012, 0, 0)  # WM_QUIT

    def _run(self):
        self._thread_id = kernel32.GetCurrentThreadId()

        # 安装键盘 hook
        self._kb_proc = HOOKPROC(self._keyboard_callback)
        self._kb_hook = user32.SetWindowsHookExW(
            WH_KEYBOARD_LL, self._kb_proc, None, 0)

        # 安装鼠标 hook
        self._mouse_proc = HOOKPROC(self._mouse_callback)
        self._mouse_hook = user32.SetWindowsHookExW(
            WH_MOUSE_LL, self._mouse_proc, None, 0)

        # 消息循环
        msg = ctypes.wintypes.MSG()
        while self._recording:
            ret = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret <= 0:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        # 清理
        if self._kb_hook:
            user32.UnhookWindowsHookEx(self._kb_hook)
            self._kb_hook = None
        if self._mouse_hook:
            user32.UnhookWindowsHookEx(self._mouse_hook)
            self._mouse_hook = None

    def _keyboard_callback(self, nCode, wParam, lParam):
        if nCode == HC_ACTION and not self._paused:
            info = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            # 忽略注入事件
            if not (info.flags & LLKHF_INJECTED):
                if wParam in (WM_KEYDOWN, WM_SYSKEYDOWN):
                    self._add_event(RawEvent('key_down', info.time, vk=info.vkCode))
                elif wParam in (WM_KEYUP, WM_SYSKEYUP):
                    self._add_event(RawEvent('key_up', info.time, vk=info.vkCode))
        return user32.CallNextHookEx(self._kb_hook, nCode, wParam, lParam)

    def _mouse_callback(self, nCode, wParam, lParam):
        if nCode == HC_ACTION and not self._paused:
            info = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            # 忽略注入事件
            if not (info.flags & 1):  # LLMHF_INJECTED
                x, y = info.pt.x, info.pt.y
                if wParam == WM_LBUTTONDOWN:
                    self._add_event(RawEvent('mouse_down', info.time, x=x, y=y, button='left'))
                elif wParam == WM_LBUTTONUP:
                    self._add_event(RawEvent('mouse_up', info.time, x=x, y=y, button='left'))
                elif wParam == WM_RBUTTONDOWN:
                    self._add_event(RawEvent('mouse_down', info.time, x=x, y=y, button='right'))
                elif wParam == WM_RBUTTONUP:
                    self._add_event(RawEvent('mouse_up', info.time, x=x, y=y, button='right'))
                elif wParam == WM_MOUSEMOVE:
                    self._add_event(RawEvent('mouse_move', info.time, x=x, y=y))
                elif wParam == WM_MOUSEWHEEL:
                    delta = ctypes.c_short(info.mouseData >> 16).value
                    self._add_event(RawEvent('wheel', info.time, x=x, y=y, delta=delta))
        return user32.CallNextHookEx(self._mouse_hook, nCode, wParam, lParam)

    def _add_event(self, event: RawEvent):
        self._events.append(event)
        if self._on_event:
            try:
                self._on_event(len(self._events))
            except Exception:
                pass

    def to_steps(self) -> list[dict]:
        """将原始事件转换为 combo 步骤格式"""
        if not self._events:
            return []

        # 智能过滤：合并连续鼠标移动
        filtered = self._filter_events()
        steps = []
        i = 0
        last_time = filtered[0].time if filtered else 0

        while i < len(filtered):
            ev = filtered[i]

            # 插入延迟
            dt = ev.time - last_time
            if dt > 100 and steps:
                steps.append({'type': 'delay', 'ms': dt})

            if ev.kind == 'key_down':
                # 收集同时按下的键，配对 key_up 生成 keys 步骤
                combo_keys = [ev.vk]
                j = i + 1
                # 查找紧随的 key_down（50ms 内）
                while j < len(filtered):
                    nev = filtered[j]
                    if nev.kind == 'key_down' and nev.time - ev.time < 50:
                        combo_keys.append(nev.vk)
                        j += 1
                    else:
                        break

                # 生成按键字符串
                key_str = vk_list_to_str(combo_keys)
                if key_str:
                    steps.append({
                        'type': 'keys',
                        'target': key_str,
                        'label': key_str,
                    })

                # 跳过对应的 key_up 事件
                skip_vks = set(combo_keys)
                while j < len(filtered):
                    nev = filtered[j]
                    if nev.kind == 'key_up' and nev.vk in skip_vks:
                        skip_vks.discard(nev.vk)
                        j += 1
                        if not skip_vks:
                            break
                    elif nev.kind == 'key_up':
                        j += 1
                    else:
                        break

                last_time = filtered[j - 1].time if j > i else ev.time
                i = j
                continue

            elif ev.kind == 'mouse_down':
                # 查找配对的 mouse_up
                j = i + 1
                while j < len(filtered):
                    nev = filtered[j]
                    if nev.kind == 'mouse_up' and nev.button == ev.button:
                        break
                    j += 1

                steps.append({
                    'type': 'mouse_click',
                    'x': ev.x,
                    'y': ev.y,
                    'button': ev.button,
                })
                last_time = filtered[j].time if j < len(filtered) else ev.time
                i = j + 1
                continue

            elif ev.kind == 'mouse_move':
                steps.append({
                    'type': 'mouse_move',
                    'x': ev.x,
                    'y': ev.y,
                })

            last_time = ev.time
            i += 1

        return steps

    def _filter_events(self) -> list[RawEvent]:
        """智能过滤：合并相近的鼠标移动（使用距离阈值）"""
        if not self._events:
            return []

        result = []
        i = 0
        while i < len(self._events):
            ev = self._events[i]
            if ev.kind == 'mouse_move':
                # 找到移动距离超过阈值的最后一个
                j = i + 1
                last_ev = ev
                while j < len(self._events):
                    nev = self._events[j]
                    if nev.kind == 'mouse_move':
                        # 距离阈值: 10 像素
                        dist = ((nev.x - last_ev.x)**2 + (nev.y - last_ev.y)**2)**0.5
                        if dist > 10:
                            last_ev = nev
                        j += 1
                    else:
                        break
                result.append(last_ev)
                i = j
            else:
                result.append(ev)
                i += 1
        return result
