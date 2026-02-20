"""窗口管理器 - 拖拽、吸附、隐藏"""

import ctypes
import ctypes.wintypes
from tkinter import Tk, Toplevel, Canvas
from .monitor import get_monitors


class EdgeGlow:
    """边缘发光指示条"""

    def __init__(self, root: Tk, color: str = '#6366f1'):
        self.root = root
        self.color = color
        self._window: Toplevel | None = None
        self._canvas: Canvas | None = None
        self._glow_phase = 0
        self._animating = False

    def show(self, edge: str, monitor: tuple, window_y: int, window_h: int, window_w: int):
        """显示发光条"""
        if self._window:
            self._window.destroy()

        self._window = Toplevel(self.root)
        self._window.overrideredirect(True)
        self._window.attributes('-topmost', True)
        self._window.attributes('-alpha', 0.9)
        self._window.configure(bg='black')

        # 根据边缘方向设置位置和大小
        m_left, m_top, m_right, m_bottom = monitor
        thickness = 3

        if edge == 'L':
            x, y = m_left, window_y
            w, h = thickness, window_h
        elif edge == 'R':
            x, y = m_right - thickness, window_y
            w, h = thickness, window_h
        elif edge == 'T':
            x, y = m_left + (m_right - m_left - window_w) // 2, m_top
            w, h = window_w, thickness
        else:
            return

        self._window.geometry(f"{w}x{h}+{x}+{y}")

        self._canvas = Canvas(self._window, bg='black', highlightthickness=0, width=w, height=h)
        self._canvas.pack(fill='both', expand=True)

        self._edge = edge
        self._w = w
        self._h = h
        self._animating = True
        self._glow_phase = 0
        self._animate_glow()

    def _animate_glow(self):
        """发光动画"""
        if not self._animating or not self._canvas:
            return

        self._canvas.delete('all')

        # 呼吸效果：亮度在 0.4 ~ 1.0 之间变化
        import math
        brightness = 0.7 + 0.3 * math.sin(self._glow_phase * 0.15)

        # 计算当前颜色
        base_r, base_g, base_b = 99, 102, 241  # #6366f1
        r = int(base_r * brightness)
        g = int(base_g * brightness)
        b = int(base_b * brightness)
        color = f'#{r:02x}{g:02x}{b:02x}'

        self._canvas.create_rectangle(0, 0, self._w, self._h, fill=color, outline='')

        self._glow_phase += 1
        self._window.after(50, self._animate_glow)

    def hide(self):
        """隐藏发光条"""
        self._animating = False
        if self._window:
            self._window.destroy()
            self._window = None
            self._canvas = None


class WindowManager:
    """窗口行为管理"""

    def __init__(self, root: Tk, config: dict):
        self.root = root
        self.width = config.get('width', 360)
        self.edge_threshold = config.get('edge_threshold', 8)
        self.hidden_visible = config.get('hidden_visible', 4)
        self.show_trigger = config.get('show_trigger', 8)
        self.anim_speed = config.get('animation_speed', 8)
        self.anim_step = config.get('animation_step', 40)

        self._drag_x = 0
        self._drag_y = 0
        self._docked = None  # 'L', 'R', 'T' or None
        self._hidden = False
        self._animating = False
        self._monitors = get_monitors()
        self._current_monitor = self._monitors[0]

        # 边缘发光指示条
        self._edge_glow = EdgeGlow(root)

    def get_mouse_pos(self) -> tuple[int, int]:
        """获取鼠标位置"""
        try:
            pt = ctypes.wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            return pt.x, pt.y
        except Exception:
            return 0, 0

    def get_mouse_monitor(self) -> tuple[int, int, int, int]:
        """获取鼠标所在显示器"""
        mx, my = self.get_mouse_pos()
        for m in self._monitors:
            if m[0] <= mx < m[2] and m[1] <= my < m[3]:
                return m
        return self._monitors[0]

    def init_position(self):
        """初始化窗口位置到鼠标所在显示器右上角"""
        m = self.get_mouse_monitor()
        self._current_monitor = m
        h = self.root.winfo_height()
        x = m[2] - self.width - 20
        y = m[1] + 20
        self.root.geometry(f"+{x}+{y}")

    def drag_start(self, event):
        """开始拖拽"""
        self._drag_x = event.x
        self._drag_y = event.y
        self._docked = None
        self._hidden = False
        self._edge_glow.hide()

    def drag(self, event):
        """拖拽中"""
        x = self.root.winfo_x() + event.x - self._drag_x
        y = self.root.winfo_y() + event.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def drag_end(self, event):
        """拖拽结束，检测边缘吸附"""
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        h = self.root.winfo_height()

        # 更新当前显示器
        for m in self._monitors:
            if m[0] <= x < m[2] and m[1] <= y < m[3]:
                self._current_monitor = m
                break

        m = self._current_monitor
        th = self.edge_threshold

        # 检测左边缘
        if x - m[0] < th:
            self._docked = 'L'
            self.root.geometry(f"+{m[0]}+{y}")
        # 检测右边缘
        elif m[2] - (x + self.width) < th:
            self._docked = 'R'
            self.root.geometry(f"+{m[2] - self.width}+{y}")
        # 检测上边缘
        elif y - m[1] < th:
            self._docked = 'T'
            self.root.geometry(f"+{x}+{m[1]}")

    def try_hide(self):
        """尝试隐藏窗口"""
        if self._docked and not self._hidden and not self._animating:
            self._hide()

    def _hide(self):
        """执行隐藏动画"""
        if self._animating:
            return
        self._animating = True
        self._anim_hide()

    def _anim_hide(self):
        """隐藏动画帧"""
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        h = self.root.winfo_height()
        m = self._current_monitor
        done = False

        if self._docked == 'L':
            nx = x - self.anim_step
            if nx <= m[0] - self.width + self.hidden_visible:
                nx = m[0] - self.width + self.hidden_visible
                done = True
            self.root.geometry(f"+{nx}+{y}")
        elif self._docked == 'R':
            nx = x + self.anim_step
            if nx >= m[2] - self.hidden_visible:
                nx = m[2] - self.hidden_visible
                done = True
            self.root.geometry(f"+{nx}+{y}")
        elif self._docked == 'T':
            ny = y - self.anim_step
            if ny <= m[1] - h + self.hidden_visible:
                ny = m[1] - h + self.hidden_visible
                done = True
            self.root.geometry(f"+{x}+{ny}")

        if done:
            self._hidden = True
            self._animating = False
            # 显示边缘发光条
            self._edge_glow.show(self._docked, m, y, h, self.width)
        else:
            self.root.after(self.anim_speed, self._anim_hide)

    def show(self):
        """显示窗口"""
        if not self._hidden or self._animating:
            return
        self._edge_glow.hide()
        self._animating = True
        self._anim_show()

    def show_at_position(self, x: int, y: int):
        """移动窗口到指定位置并显示"""
        self._edge_glow.hide()
        self._docked = None
        self._hidden = False
        self._animating = False
        self.root.geometry(f"+{x}+{y}")
        self.root.deiconify()

    def force_show(self):
        """无条件显示（忽略 dock 状态）"""
        self._edge_glow.hide()
        self._hidden = False
        self._animating = False
        self.root.deiconify()

    def _anim_show(self):
        """显示动画帧"""
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        h = self.root.winfo_height()
        m = self._current_monitor
        done = False

        if self._docked == 'L':
            nx = x + self.anim_step
            if nx >= m[0]:
                nx = m[0]
                done = True
            self.root.geometry(f"+{nx}+{y}")
        elif self._docked == 'R':
            nx = x - self.anim_step
            if nx <= m[2] - self.width:
                nx = m[2] - self.width
                done = True
            self.root.geometry(f"+{nx}+{y}")
        elif self._docked == 'T':
            ny = y + self.anim_step
            if ny >= m[1]:
                ny = m[1]
                done = True
            self.root.geometry(f"+{x}+{ny}")

        if done:
            self._hidden = False
            self._animating = False
        else:
            self.root.after(self.anim_speed, self._anim_show)

    def check_mouse(self):
        """检测鼠标是否在触发区域"""
        if not self._hidden or self._animating:
            return

        mx, my = self.get_mouse_pos()
        m = self._current_monitor
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        h = self.root.winfo_height()
        trigger = self.show_trigger

        should_show = False
        if self._docked == 'L':
            if mx <= m[0] + trigger and m[1] <= my <= m[3]:
                should_show = True
        elif self._docked == 'R':
            if mx >= m[2] - trigger and m[1] <= my <= m[3]:
                should_show = True
        elif self._docked == 'T':
            if my <= m[1] + trigger and m[0] <= mx <= m[2]:
                should_show = True

        if should_show:
            self.show()

    @property
    def is_docked(self) -> bool:
        return self._docked is not None

    @property
    def is_hidden(self) -> bool:
        return self._hidden
