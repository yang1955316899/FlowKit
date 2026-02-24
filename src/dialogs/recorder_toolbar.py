"""录制浮动工具条 — 录制/暂停/停止控制"""

from tkinter import Toplevel, Label, Frame, Canvas
from ..widgets.draw import rr_points


class RecorderToolbar:
    """录制浮动工具条，屏幕顶部居中"""

    def __init__(self, parent, theme: dict, on_stop=None):
        self.theme = theme
        self._f = theme['font']
        self._fm = theme['mono']
        self._on_stop = on_stop
        self._recorder = None
        self._event_count = 0
        self._paused = False

        self.win = Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.configure(bg=theme['border'])

        inner = Frame(self.win, bg=theme['card'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)

        # 状态行
        status_frame = Frame(inner, bg=theme['card'])
        status_frame.pack(fill='x', padx=12, pady=(8, 4))

        self._status_dot = Label(status_frame, text="●", fg='#f38ba8',
                                  bg=theme['card'], font=(self._f, 10))
        self._status_dot.pack(side='left')

        self._status_label = Label(status_frame, text="录制中...",
                                    fg=theme['text'], bg=theme['card'],
                                    font=(self._f, 8, 'bold'))
        self._status_label.pack(side='left', padx=(4, 0))

        self._count_label = Label(status_frame, text="0 个事件",
                                   fg=theme['dim'], bg=theme['card'],
                                   font=(self._fm, 7))
        self._count_label.pack(side='right')

        # 按钮行
        btn_frame = Frame(inner, bg=theme['card'])
        btn_frame.pack(fill='x', padx=12, pady=(0, 8))

        # 暂停按钮
        self._pause_btn = Label(btn_frame, text="⏸ 暂停", fg=theme['text'],
                                 bg=theme['card2'], font=(self._f, 8),
                                 cursor='hand2', padx=10, pady=3)
        self._pause_btn.pack(side='left', padx=(0, 6))
        self._pause_btn.bind('<Button-1>', lambda e: self._toggle_pause())

        # 停止按钮
        stop_btn = Label(btn_frame, text="⏹ 停止", fg='#f38ba8',
                         bg=theme['card2'], font=(self._f, 8),
                         cursor='hand2', padx=10, pady=3)
        stop_btn.pack(side='left')
        stop_btn.bind('<Button-1>', lambda e: self._stop())

        # F9 提示
        Label(btn_frame, text="F9 停止", fg=theme['dim'], bg=theme['card'],
              font=(self._fm, 6)).pack(side='right')

        # 定位到屏幕顶部居中
        dw, dh = 240, 70
        self.win.geometry(f"{dw}x{dh}")
        self.win.update_idletasks()
        sw = self.win.winfo_screenwidth()
        px = (sw - dw) // 2
        self.win.geometry(f"+{px}+10")

        # 闪烁动画
        self._blink_state = True
        self._blink()

    def set_recorder(self, recorder):
        self._recorder = recorder
        recorder.set_event_callback(self._on_event)

    def _on_event(self, count):
        """录制事件回调（从 hook 线程调用）"""
        self._event_count = count
        try:
            self.win.after(0, self._update_count)
        except Exception:
            pass

    def _update_count(self):
        try:
            self._count_label.configure(text=f"{self._event_count} 个事件")
        except Exception:
            pass

    def _toggle_pause(self):
        if not self._recorder:
            return
        self._recorder.pause()
        self._paused = not self._paused
        if self._paused:
            self._pause_btn.configure(text="▶ 继续")
            self._status_label.configure(text="已暂停")
            self._status_dot.configure(fg=self.theme['dim'])
        else:
            self._pause_btn.configure(text="⏸ 暂停")
            self._status_label.configure(text="录制中...")
            self._status_dot.configure(fg='#f38ba8')

    def _stop(self):
        if self._recorder:
            self._recorder.stop()
        steps = self._recorder.to_steps() if self._recorder else []
        try:
            self.win.destroy()
        except Exception:
            pass
        if self._on_stop:
            self._on_stop(steps)

    def _blink(self):
        """录制指示灯闪烁"""
        if self._paused:
            self.win.after(500, self._blink)
            return
        try:
            if self._blink_state:
                self._status_dot.configure(fg='#f38ba8')
            else:
                self._status_dot.configure(fg=self.theme['card'])
            self._blink_state = not self._blink_state
            self.win.after(500, self._blink)
        except Exception:
            pass

    def destroy(self):
        try:
            self.win.destroy()
        except Exception:
            pass
