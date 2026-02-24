"""各步骤类型的属性编辑对话框（含坐标拾取器）"""

import ctypes
import ctypes.wintypes
from tkinter import Toplevel, Label, Entry, Frame, Canvas, StringVar
from ..widgets.draw import rr_points
from ..core.hotkey import HOOKPROC, MSLLHOOKSTRUCT, WH_MOUSE_LL, HC_ACTION

# 步骤类型定义
STEP_TYPES = [
    ('delay', '延迟', '⏱'),
    ('set_var', '设置变量', '📝'),
    ('get_clipboard', '读剪贴板', '📋'),
    ('set_clipboard', '写剪贴板', '📌'),
    ('mouse_click', '鼠标点击', '🖱'),
    ('mouse_move', '鼠标移动', '↗'),
    ('wait_window', '等待窗口', '🪟'),
    ('wait_pixel', '等待像素', '🎨'),
    ('if_condition', '条件分支', '🔀'),
    ('loop', '循环', '🔁'),
    # 原有动作类型也可作为步骤
    ('app', '打开应用', '📂'),
    ('keys', '按键', '⌨'),
    ('snippet', '文本', '📄'),
    ('shell', '命令', '💻'),
    ('url', '网址', '🌐'),
]

CONDITION_SOURCES = [
    ('window_title', '窗口标题'),
    ('process_name', '进程名'),
    ('clipboard', '剪贴板'),
    ('variable', '变量'),
]

CONDITION_OPS = [
    ('contains', '包含'),
    ('equals', '等于'),
    ('starts_with', '开头是'),
    ('not_contains', '不包含'),
]


class StepEditor:
    """步骤属性编辑对话框"""

    def __init__(self, parent, theme: dict, step: dict = None, step_type: str = None):
        self.result = None
        self.theme = theme
        self._f = theme['font']
        self._fm = theme['mono']
        self._drag = {'x': 0, 'y': 0}
        self._step_type = step_type or (step.get('type', 'delay') if step else 'delay')
        self._step = step or {}

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

        type_name = dict((t, n) for t, n, _ in STEP_TYPES).get(self._step_type, '步骤')
        Label(tb, text=f"编辑 - {type_name}", fg=theme['sub'], bg=theme['card'],
              font=(self._f, 8, 'bold')).pack(side='left', padx=(6, 0))

        cl = Label(tb, text="\u00D7", fg=theme['dim'], bg=theme['card'],
                   font=(self._f, 11), cursor='hand2')
        cl.pack(side='right', padx=10)
        cl.bind('<Button-1>', lambda e: self.win.destroy())
        tb.bind('<Button-1>', self._ds)
        tb.bind('<B1-Motion>', self._dm)

        Frame(inner, bg=theme['border_subtle'], height=1).pack(fill='x')

        self._form = Frame(inner, bg=theme['bg'])
        self._form.pack(fill='both', expand=True, padx=16, pady=(10, 14))

        self._entries = {}
        self._build_fields()

        # buttons
        bf = Frame(self._form, bg=theme['bg'])
        bf.pack(fill='x', pady=(12, 0))

        sc = Canvas(bf, width=60, height=28, bg=theme['bg'], highlightthickness=0, cursor='hand2')
        sc.pack(side='right')
        pts = rr_points(0, 0, 60, 28, 14)
        sc.create_polygon(pts, fill=theme['accent'], outline='')
        sc.create_text(30, 14, text="确定", fill='#1e1e2e', font=(self._f, 8, 'bold'))
        sc.bind('<Button-1>', lambda e: self._save())

        cc = Canvas(bf, width=60, height=28, bg=theme['bg'], highlightthickness=0, cursor='hand2')
        cc.pack(side='right', padx=(0, 8))
        pts2 = rr_points(0, 0, 60, 28, 14)
        cc.create_polygon(pts2, fill='', outline=theme['border'])
        cc.create_text(30, 14, text="取消", fill=theme['dim'], font=(self._f, 8))
        cc.bind('<Button-1>', lambda e: self.win.destroy())

        self.win.bind('<Return>', lambda e: self._save())
        self.win.bind('<Escape>', lambda e: self.win.destroy())

        dw, dh = 320, self._calc_height()
        self.win.geometry(f"{dw}x{dh}")
        self.win.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - dw) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - dh) // 2
        self.win.geometry(f"+{px}+{py}")
        self.win.grab_set()

    def _make_entry(self, parent, default='', width=None):
        c = self.theme
        kw = {}
        if width:
            kw['width'] = width
        e = Entry(parent, bg=c['card'], fg=c['text'],
                  insertbackground=c['accent'], relief='flat',
                  font=(self._fm, 9), bd=0, highlightthickness=1,
                  highlightbackground=c['border_subtle'],
                  highlightcolor=c['accent'], **kw)
        e.pack(fill='x', ipady=4)
        if default:
            e.insert(0, str(default))
        return e

    def _make_label(self, parent, text):
        Label(parent, text=text, fg=self.theme['dim'], bg=self.theme['bg'],
              font=(self._fm, 7)).pack(anchor='w', pady=(6, 2))

    def _build_fields(self):
        t = self._step_type
        s = self._step

        if t == 'delay':
            self._make_label(self._form, "延迟 (ms)")
            self._entries['ms'] = self._make_entry(self._form, s.get('ms', 1000))

        elif t == 'set_var':
            self._make_label(self._form, "变量名")
            self._entries['name'] = self._make_entry(self._form, s.get('name', ''))
            self._make_label(self._form, "值")
            self._entries['value'] = self._make_entry(self._form, s.get('value', ''))

        elif t == 'get_clipboard':
            self._make_label(self._form, "保存到变量")
            self._entries['var'] = self._make_entry(self._form, s.get('var', 'clip_text'))

        elif t == 'set_clipboard':
            self._make_label(self._form, "内容 (支持 {{变量}})")
            self._entries['value'] = self._make_entry(self._form, s.get('value', ''))

        elif t in ('mouse_click', 'mouse_move'):
            coord_frame = Frame(self._form, bg=self.theme['bg'])
            coord_frame.pack(fill='x')
            self._make_label(coord_frame, "X 坐标")
            self._entries['x'] = self._make_entry(coord_frame, s.get('x', 0))
            self._make_label(coord_frame, "Y 坐标")
            self._entries['y'] = self._make_entry(coord_frame, s.get('y', 0))

            # 坐标拾取按钮
            pick_btn = Label(self._form, text="🎯 拾取坐标", fg=self.theme['accent'],
                             bg=self.theme['card2'], font=(self._f, 8), cursor='hand2',
                             padx=10, pady=4)
            pick_btn.pack(fill='x', pady=(6, 0))
            pick_btn.bind('<Button-1>', lambda e: self._pick_coordinate())

            if t == 'mouse_click':
                self._make_label(self._form, "按钮")
                self._button_var = StringVar(value=s.get('button', 'left'))
                btn_frame = Frame(self._form, bg=self.theme['bg'])
                btn_frame.pack(fill='x')
                self._btn_labels = []
                for btn_name, btn_text in [('left', '左键'), ('right', '右键'), ('middle', '中键')]:
                    lbl = Label(btn_frame, text=btn_text, cursor='hand2',
                                font=(self._fm, 7), padx=6, pady=2)
                    lbl.pack(side='left', padx=(0, 3))
                    lbl._btn_name = btn_name
                    lbl.bind('<Button-1>', lambda e, b=btn_name: self._select_button(b))
                    self._btn_labels.append(lbl)
                self._update_button_pills()

        elif t == 'wait_window':
            self._make_label(self._form, "窗口标题 (模糊匹配)")
            self._entries['title'] = self._make_entry(self._form, s.get('title', ''))
            self._make_label(self._form, "超时 (ms)")
            self._entries['timeout'] = self._make_entry(self._form, s.get('timeout', 5000))

        elif t == 'wait_pixel':
            self._make_label(self._form, "X 坐标")
            self._entries['x'] = self._make_entry(self._form, s.get('x', 0))
            self._make_label(self._form, "Y 坐标")
            self._entries['y'] = self._make_entry(self._form, s.get('y', 0))
            pick_btn = Label(self._form, text="🎯 拾取坐标", fg=self.theme['accent'],
                             bg=self.theme['card2'], font=(self._f, 8), cursor='hand2',
                             padx=10, pady=4)
            pick_btn.pack(fill='x', pady=(6, 0))
            pick_btn.bind('<Button-1>', lambda e: self._pick_coordinate())
            self._make_label(self._form, "目标颜色 (#RRGGBB)")
            self._entries['color'] = self._make_entry(self._form, s.get('color', '#ff0000'))
            self._make_label(self._form, "容差")
            self._entries['tolerance'] = self._make_entry(self._form, s.get('tolerance', 10))
            self._make_label(self._form, "超时 (ms)")
            self._entries['timeout'] = self._make_entry(self._form, s.get('timeout', 5000))

        elif t == 'if_condition':
            self._build_condition_fields(s.get('condition', {}))

        elif t == 'loop':
            self._make_label(self._form, "循环模式")
            self._loop_mode_var = StringVar(value=s.get('mode', 'count'))
            mode_frame = Frame(self._form, bg=self.theme['bg'])
            mode_frame.pack(fill='x')
            self._mode_labels = []
            for mode_id, mode_text in [('count', '固定次数'), ('while_condition', '条件循环')]:
                lbl = Label(mode_frame, text=mode_text, cursor='hand2',
                            font=(self._fm, 7), padx=6, pady=2)
                lbl.pack(side='left', padx=(0, 3))
                lbl._mode_id = mode_id
                lbl.bind('<Button-1>', lambda e, m=mode_id: self._select_loop_mode(m))
                self._mode_labels.append(lbl)
            self._update_mode_pills()

            self._count_frame = Frame(self._form, bg=self.theme['bg'])
            self._make_label(self._count_frame, "循环次数")
            self._entries['count'] = self._make_entry(self._count_frame, s.get('count', 5))

            self._cond_frame = Frame(self._form, bg=self.theme['bg'])
            self._build_condition_fields(s.get('condition', {}), parent=self._cond_frame)

            self._make_label(self._form, "最大迭代次数")
            self._entries['max_iterations'] = self._make_entry(
                self._form, s.get('max_iterations', 100))

            self._update_loop_visibility()

        # 原有动作类型的字段
        elif t == 'app':
            self._make_label(self._form, "程序路径")
            self._entries['target'] = self._make_entry(self._form, s.get('target', ''))
            self._make_label(self._form, "标签")
            self._entries['label'] = self._make_entry(self._form, s.get('label', ''))

        elif t == 'keys':
            self._make_label(self._form, "按键组合 (如 ctrl+shift+a)")
            self._entries['target'] = self._make_entry(self._form, s.get('target', ''))
            self._make_label(self._form, "标签")
            self._entries['label'] = self._make_entry(self._form, s.get('label', ''))

        elif t == 'snippet':
            self._make_label(self._form, "要复制的文本")
            self._entries['target'] = self._make_entry(self._form, s.get('target', ''))
            self._make_label(self._form, "标签")
            self._entries['label'] = self._make_entry(self._form, s.get('label', ''))

        elif t == 'shell':
            self._make_label(self._form, "命令")
            self._entries['target'] = self._make_entry(self._form, s.get('target', ''))
            self._make_label(self._form, "标签")
            self._entries['label'] = self._make_entry(self._form, s.get('label', ''))

        elif t == 'url':
            self._make_label(self._form, "网址")
            self._entries['target'] = self._make_entry(self._form, s.get('target', ''))
            self._make_label(self._form, "标签")
            self._entries['label'] = self._make_entry(self._form, s.get('label', ''))

    def _build_condition_fields(self, cond: dict, parent=None):
        p = parent or self._form
        self._make_label(p, "条件来源")
        self._source_var = StringVar(value=cond.get('source', 'window_title'))
        src_frame = Frame(p, bg=self.theme['bg'])
        src_frame.pack(fill='x')
        self._source_labels = []
        for src_id, src_text in CONDITION_SOURCES:
            lbl = Label(src_frame, text=src_text, cursor='hand2',
                        font=(self._fm, 7), padx=6, pady=2)
            lbl.pack(side='left', padx=(0, 3))
            lbl._src_id = src_id
            lbl.bind('<Button-1>', lambda e, s=src_id: self._select_source(s))
            self._source_labels.append(lbl)
        self._update_source_pills()

        self._make_label(p, "操作")
        self._op_var = StringVar(value=cond.get('op', 'contains'))
        op_frame = Frame(p, bg=self.theme['bg'])
        op_frame.pack(fill='x')
        self._op_labels = []
        for op_id, op_text in CONDITION_OPS:
            lbl = Label(op_frame, text=op_text, cursor='hand2',
                        font=(self._fm, 7), padx=6, pady=2)
            lbl.pack(side='left', padx=(0, 3))
            lbl._op_id = op_id
            lbl.bind('<Button-1>', lambda e, o=op_id: self._select_op(o))
            self._op_labels.append(lbl)
        self._update_op_pills()

        self._make_label(p, "比较值")
        self._entries['cond_value'] = self._make_entry(p, cond.get('value', ''))

        self._make_label(p, "变量名 (来源=变量时)")
        self._entries['cond_var_name'] = self._make_entry(p, cond.get('var_name', ''))

    def _calc_height(self):
        t = self._step_type
        base = 120  # title + buttons
        field_heights = {
            'delay': 60,
            'set_var': 110,
            'get_clipboard': 60,
            'set_clipboard': 60,
            'mouse_click': 200,
            'mouse_move': 160,
            'wait_window': 110,
            'wait_pixel': 260,
            'if_condition': 220,
            'loop': 300,
            'app': 110, 'keys': 110, 'snippet': 110, 'shell': 110, 'url': 110,
        }
        return base + field_heights.get(t, 100)

    # ── pill selectors ──

    def _select_button(self, btn):
        self._button_var.set(btn)
        self._update_button_pills()

    def _update_button_pills(self):
        c = self.theme
        current = self._button_var.get()
        for lbl in self._btn_labels:
            if lbl._btn_name == current:
                lbl.configure(bg=c['accent'], fg='#1e1e2e')
            else:
                lbl.configure(bg=c['card2'], fg=c['dim'])

    def _select_source(self, src):
        self._source_var.set(src)
        self._update_source_pills()

    def _update_source_pills(self):
        c = self.theme
        current = self._source_var.get()
        for lbl in self._source_labels:
            if lbl._src_id == current:
                lbl.configure(bg=c['accent'], fg='#1e1e2e')
            else:
                lbl.configure(bg=c['card2'], fg=c['dim'])

    def _select_op(self, op):
        self._op_var.set(op)
        self._update_op_pills()

    def _update_op_pills(self):
        c = self.theme
        current = self._op_var.get()
        for lbl in self._op_labels:
            if lbl._op_id == current:
                lbl.configure(bg=c['accent'], fg='#1e1e2e')
            else:
                lbl.configure(bg=c['card2'], fg=c['dim'])

    def _select_loop_mode(self, mode):
        self._loop_mode_var.set(mode)
        self._update_mode_pills()
        self._update_loop_visibility()

    def _update_mode_pills(self):
        c = self.theme
        current = self._loop_mode_var.get()
        for lbl in self._mode_labels:
            if lbl._mode_id == current:
                lbl.configure(bg=c['accent'], fg='#1e1e2e')
            else:
                lbl.configure(bg=c['card2'], fg=c['dim'])

    def _update_loop_visibility(self):
        self._count_frame.pack_forget()
        self._cond_frame.pack_forget()
        if self._loop_mode_var.get() == 'count':
            self._count_frame.pack(fill='x')
        else:
            self._cond_frame.pack(fill='x')

    # ── 坐标拾取器 ──

    def _pick_coordinate(self):
        """隐藏对话框 → 安装临时鼠标 hook → 用户点击 → 捕获坐标 → 恢复"""
        self.win.withdraw()
        self.win.update()

        result = [None]
        hook_handle = [None]

        def mouse_proc(nCode, wParam, lParam):
            if nCode == HC_ACTION and wParam == 0x0201:  # WM_LBUTTONDOWN
                info = ctypes.cast(lParam, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
                result[0] = (info.pt.x, info.pt.y)
                # 卸载 hook
                if hook_handle[0]:
                    ctypes.windll.user32.UnhookWindowsHookEx(hook_handle[0])
                    hook_handle[0] = None
                ctypes.windll.user32.PostThreadMessageW(
                    ctypes.windll.kernel32.GetCurrentThreadId(), 0x0012, 0, 0)  # WM_QUIT
                return 1  # 吞掉这次点击
            return ctypes.windll.user32.CallNextHookEx(
                hook_handle[0], nCode, wParam, lParam)

        proc = HOOKPROC(mouse_proc)

        import threading

        def run_hook():
            hook_handle[0] = ctypes.windll.user32.SetWindowsHookExW(
                WH_MOUSE_LL, proc, None, 0)
            msg = ctypes.wintypes.MSG()
            while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
            if hook_handle[0]:
                ctypes.windll.user32.UnhookWindowsHookEx(hook_handle[0])

        t = threading.Thread(target=run_hook, daemon=True)
        t.start()
        t.join(timeout=30)

        self.win.deiconify()
        self.win.lift()
        self.win.focus_force()

        if result[0]:
            x, y = result[0]
            if 'x' in self._entries:
                self._entries['x'].delete(0, 'end')
                self._entries['x'].insert(0, str(x))
            if 'y' in self._entries:
                self._entries['y'].delete(0, 'end')
                self._entries['y'].insert(0, str(y))

    # ── drag ──

    def _ds(self, e):
        self._drag['x'] = e.x_root - self.win.winfo_x()
        self._drag['y'] = e.y_root - self.win.winfo_y()

    def _dm(self, e):
        self.win.geometry(f"+{e.x_root-self._drag['x']}+{e.y_root-self._drag['y']}")

    # ── save ──

    def _save(self):
        t = self._step_type
        result = {'type': t}

        if t == 'delay':
            result['ms'] = self._int_val('ms', 1000)

        elif t == 'set_var':
            result['name'] = self._str_val('name')
            result['value'] = self._str_val('value')

        elif t == 'get_clipboard':
            result['var'] = self._str_val('var', 'clip_text')

        elif t == 'set_clipboard':
            result['value'] = self._str_val('value')

        elif t in ('mouse_click', 'mouse_move'):
            result['x'] = self._int_val('x', 0)
            result['y'] = self._int_val('y', 0)
            if t == 'mouse_click':
                result['button'] = self._button_var.get()

        elif t == 'wait_window':
            result['title'] = self._str_val('title')
            result['timeout'] = self._int_val('timeout', 5000)

        elif t == 'wait_pixel':
            result['x'] = self._int_val('x', 0)
            result['y'] = self._int_val('y', 0)
            result['color'] = self._str_val('color', '#ff0000')
            result['tolerance'] = self._int_val('tolerance', 10)
            result['timeout'] = self._int_val('timeout', 5000)

        elif t == 'if_condition':
            result['condition'] = self._build_condition_result()
            # 保留已有的 then/else 步骤
            result['then_steps'] = self._step.get('then_steps', [])
            result['else_steps'] = self._step.get('else_steps', [])

        elif t == 'loop':
            result['mode'] = self._loop_mode_var.get()
            result['count'] = self._int_val('count', 5)
            result['max_iterations'] = self._int_val('max_iterations', 100)
            if result['mode'] == 'while_condition':
                result['condition'] = self._build_condition_result()
            result['body_steps'] = self._step.get('body_steps', [])

        elif t in ('app', 'keys', 'snippet', 'shell', 'url'):
            result['target'] = self._str_val('target')
            result['label'] = self._str_val('label')

        self.result = result
        self.win.destroy()

    def _build_condition_result(self) -> dict:
        return {
            'source': self._source_var.get(),
            'op': self._op_var.get(),
            'value': self._str_val('cond_value'),
            'var_name': self._str_val('cond_var_name'),
        }

    def _str_val(self, key, default='') -> str:
        e = self._entries.get(key)
        return e.get().strip() if e else default

    def _int_val(self, key, default=0) -> int:
        try:
            return int(self._str_val(key, str(default)))
        except ValueError:
            return default

    def show(self):
        self.win.wait_window()
        return self.result
