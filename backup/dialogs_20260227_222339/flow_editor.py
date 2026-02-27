"""可视化流程编排器 — 主编辑器窗口"""

import threading
from tkinter import Toplevel, Label, Frame, Canvas
from ..widgets.draw import rr_points
from .flow_canvas import FlowCanvas
from .flow_palette import FlowPalette
from .flow_properties import FlowProperties
from .step_editor import StepEditor


class FlowEditor:
    """可视化流程编排器 (800×600)"""

    def __init__(self, parent, theme: dict, combo: dict = None, executor=None):
        self.result = None
        self.theme = theme
        self._f = theme['font']
        self._fm = theme['mono']
        self._drag = {'x': 0, 'y': 0}
        self._steps = list(combo.get('steps', [])) if combo else []
        self._delay = combo.get('delay', 500) if combo else 500
        self._executor = executor
        self._debug_running = False

        self.win = Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.configure(bg=theme['border'])

        inner = Frame(self.win, bg=theme['bg'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)

        # title bar
        tb = Frame(inner, bg=theme['card'], height=30)
        tb.pack(fill='x')
        tb.pack_propagate(False)

        dot = Canvas(tb, width=8, height=8, bg=theme['card'], highlightthickness=0)
        dot.pack(side='left', padx=(12, 0))
        dot.create_oval(0, 0, 8, 8, fill=theme['accent'], outline='')

        Label(tb, text="流程编排器", fg=theme['sub'], bg=theme['card'],
              font=(self._f, 8, 'bold')).pack(side='left', padx=(6, 0))

        cl = Label(tb, text="\u00D7", fg=theme['dim'], bg=theme['card'],
                   font=(self._f, 11), cursor='hand2')
        cl.pack(side='right', padx=10)
        cl.bind('<Button-1>', lambda e: self.win.destroy())
        tb.bind('<Button-1>', self._ds)
        tb.bind('<B1-Motion>', self._dm)

        Frame(inner, bg=theme['border_subtle'], height=1).pack(fill='x')

        # 三栏布局
        body = Frame(inner, bg=theme['bg'])
        body.pack(fill='both', expand=True)

        # 左侧面板
        self._palette = FlowPalette(body, theme, on_add=self._add_step_from_palette)

        # 分隔线
        Frame(body, bg=theme['border_subtle'], width=1).pack(side='left', fill='y')

        # 右侧属性面板
        self._properties = FlowProperties(body, theme, on_update=self._update_step)

        # 分隔线
        Frame(body, bg=theme['border_subtle'], width=1).pack(side='right', fill='y')

        # 中间画布
        canvas_frame = Frame(body, bg=theme['bg'])
        canvas_frame.pack(side='left', fill='both', expand=True)

        self._flow_canvas = FlowCanvas(canvas_frame, theme, on_select=self._on_step_select)
        self._flow_canvas.set_steps(self._steps)

        # 底部工具栏
        Frame(inner, bg=theme['border_subtle'], height=1).pack(fill='x')
        toolbar = Frame(inner, bg=theme['card'], height=36)
        toolbar.pack(fill='x')
        toolbar.pack_propagate(False)

        # 运行按钮
        run_btn = Label(toolbar, text="▶ 运行", fg=theme['text'],
                        bg=theme['card2'], font=(self._f, 8), cursor='hand2',
                        padx=8, pady=3)
        run_btn.pack(side='left', padx=(12, 4), pady=4)
        run_btn.bind('<Button-1>', lambda e: self._run())

        # 调试按钮
        debug_btn = Label(toolbar, text="⏸ 调试", fg=theme['text'],
                          bg=theme['card2'], font=(self._f, 8), cursor='hand2',
                          padx=8, pady=3)
        debug_btn.pack(side='left', padx=4, pady=4)
        debug_btn.bind('<Button-1>', lambda e: self._debug())

        # 删除选中
        del_btn = Label(toolbar, text="🗑 删除", fg=theme.get('red', '#f38ba8'),
                        bg=theme['card2'], font=(self._f, 8), cursor='hand2',
                        padx=8, pady=3)
        del_btn.pack(side='left', padx=4, pady=4)
        del_btn.bind('<Button-1>', lambda e: self._delete_selected())

        # 保存/取消
        sc = Canvas(toolbar, width=60, height=26, bg=theme['card'],
                    highlightthickness=0, cursor='hand2')
        sc.pack(side='right', padx=(4, 12), pady=5)
        pts = rr_points(0, 0, 60, 26, 13)
        sc.create_polygon(pts, fill=theme['accent'], outline='')
        sc.create_text(30, 13, text="保存", fill='#1e1e2e', font=(self._f, 8, 'bold'))
        sc.bind('<Button-1>', lambda e: self._save())

        cc = Canvas(toolbar, width=60, height=26, bg=theme['card'],
                    highlightthickness=0, cursor='hand2')
        cc.pack(side='right', padx=4, pady=5)
        pts2 = rr_points(0, 0, 60, 26, 13)
        cc.create_polygon(pts2, fill='', outline=theme['border'])
        cc.create_text(30, 13, text="取消", fill=theme['dim'], font=(self._f, 8))
        cc.bind('<Button-1>', lambda e: self.win.destroy())

        self.win.bind('<Escape>', lambda e: self.win.destroy())
        self.win.bind('<Delete>', lambda e: self._delete_selected())

        # 窗口大小和位置
        dw, dh = 800, 600
        self.win.geometry(f"{dw}x{dh}")
        self.win.update_idletasks()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        px = (sw - dw) // 2
        py = (sh - dh) // 2
        self.win.geometry(f"+{px}+{py}")
        self.win.grab_set()

        # 延迟渲染（等待窗口显示后获取正确尺寸）
        self.win.after(100, self._flow_canvas.render)

    def _add_step_from_palette(self, step_type: str):
        """从面板添加步骤"""
        result = StepEditor(self.win, self.theme, step_type=step_type).show()
        if result:
            self._steps.append(result)
            self._flow_canvas.set_steps(self._steps)

    def _on_step_select(self, step, flat_idx):
        """步骤选中回调"""
        if step:
            self._properties.show_step(step, flat_idx)
        else:
            self._properties.clear()

    def _update_step(self, flat_idx: int, new_step: dict):
        """属性面板更新步骤"""
        if flat_idx < len(self._steps):
            self._steps[flat_idx] = new_step
            self._flow_canvas.set_steps(self._steps)

    def _delete_selected(self):
        """删除选中步骤"""
        idx = self._flow_canvas._selected_idx
        if idx is not None and idx < len(self._steps):
            self._steps.pop(idx)
            self._flow_canvas._selected_idx = None
            self._flow_canvas.set_steps(self._steps)
            self._properties.clear()

    def _run(self):
        """运行流程"""
        if not self._executor or not self._steps:
            return
        action = {
            'type': 'combo',
            'steps': self._steps,
            'delay': self._delay,
        }
        self._executor.execute(action)

    def _debug(self):
        """调试模式 — 逐步执行并高亮"""
        if not self._executor or not self._steps or self._debug_running:
            return
        self._debug_running = True

        def run_debug():
            from ..core.combo_executor import ComboExecutor
            executor = ComboExecutor(self._executor)
            for i, step in enumerate(self._steps):
                if not self._debug_running:
                    break
                # 高亮当前步骤
                try:
                    self.win.after(0, self._highlight_step, i)
                except Exception:
                    break
                import time
                time.sleep(0.5)
                executor._execute_one(step, self._delay / 1000.0)
                time.sleep(0.3)
            self._debug_running = False
            try:
                self.win.after(0, self._flow_canvas.render)
            except Exception:
                pass

        threading.Thread(target=run_debug, daemon=True).start()

    def _highlight_step(self, idx: int):
        self._flow_canvas._selected_idx = idx
        self._flow_canvas.render()

    # ── drag ──

    def _ds(self, e):
        self._drag['x'] = e.x_root - self.win.winfo_x()
        self._drag['y'] = e.y_root - self.win.winfo_y()

    def _dm(self, e):
        self.win.geometry(f"+{e.x_root-self._drag['x']}+{e.y_root-self._drag['y']}")

    # ── save ──

    def _save(self):
        self.result = {
            'steps': self._steps,
            'delay': self._delay,
        }
        self.win.destroy()

    def show(self):
        self.win.wait_window()
        return self.result
