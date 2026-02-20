"""Python 脚本编辑器对话框"""

import re
from tkinter import Toplevel, Label, Frame, Canvas, Text, Scrollbar, Entry, StringVar, filedialog
from ..widgets.draw import rr_points


# Python 关键字
_KEYWORDS = {
    'False', 'None', 'True', 'and', 'as', 'assert', 'async', 'await',
    'break', 'class', 'continue', 'def', 'del', 'elif', 'else', 'except',
    'finally', 'for', 'from', 'global', 'if', 'import', 'in', 'is',
    'lambda', 'nonlocal', 'not', 'or', 'pass', 'raise', 'return',
    'try', 'while', 'with', 'yield',
}

_BUILTINS = {
    'print', 'len', 'range', 'int', 'str', 'float', 'list', 'dict',
    'set', 'tuple', 'bool', 'type', 'isinstance', 'enumerate', 'zip',
    'map', 'filter', 'sorted', 'reversed', 'open', 'input', 'super',
    'property', 'staticmethod', 'classmethod', 'abs', 'max', 'min',
    'sum', 'any', 'all', 'hasattr', 'getattr', 'setattr',
}


class ScriptEditorDialog:
    """Python 脚本编辑器"""

    def __init__(self, parent, theme: dict, code: str = '', mode: str = 'inline',
                 file_path: str = '', timeout: int = 30, show_output: bool = True,
                 run_callback=None):
        """
        Args:
            parent: 父窗口
            theme: 主题字典
            code: 初始代码
            mode: 'inline' 或 'file'
            file_path: 外部文件路径
            timeout: 超时秒数
            show_output: 是否显示输出
            run_callback: 运行回调 fn(code, mode, path) -> None
        """
        self.result = None
        self.theme = theme
        self._f = theme['font']
        self._fm = theme['mono']
        self._drag = {'x': 0, 'y': 0}
        self._run_callback = run_callback
        self._highlight_job = None

        self.win = Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.configure(bg=theme['border'])

        inner = Frame(self.win, bg=theme['bg'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)

        # ── title bar ──
        tb = Frame(inner, bg=theme['card'], height=30)
        tb.pack(fill='x')
        tb.pack_propagate(False)

        dot = Canvas(tb, width=8, height=8, bg=theme['card'], highlightthickness=0)
        dot.pack(side='left', padx=(12, 0))
        dot.create_oval(0, 0, 8, 8, fill=theme['mauve'], outline='')

        Label(tb, text="脚本编辑器", fg=theme['sub'], bg=theme['card'],
              font=(self._f, 8, 'bold')).pack(side='left', padx=(6, 0))

        cl = Label(tb, text="\u00D7", fg=theme['dim'], bg=theme['card'],
                   font=(self._f, 11), cursor='hand2')
        cl.pack(side='right', padx=10)
        cl.bind('<Button-1>', lambda e: self.win.destroy())
        tb.bind('<Button-1>', self._ds)
        tb.bind('<B1-Motion>', self._dm)

        Frame(inner, bg=theme['border_subtle'], height=1).pack(fill='x')

        body = Frame(inner, bg=theme['bg'])
        body.pack(fill='both', expand=True, padx=12, pady=8)

        # ── mode switch ──
        mode_frame = Frame(body, bg=theme['bg'])
        mode_frame.pack(fill='x', pady=(0, 6))

        self._mode_var = StringVar(value=mode)
        self._mode_labels = []
        for m, label in [('inline', '内嵌代码'), ('file', '外部文件')]:
            lbl = Label(mode_frame, text=label, cursor='hand2',
                        font=(self._fm, 7), padx=6, pady=2)
            lbl.pack(side='left', padx=(0, 3))
            lbl._mode = m
            lbl.bind('<Button-1>', lambda e, mv=m: self._switch_mode(mv))
            self._mode_labels.append(lbl)

        # ── file path frame (file mode) ──
        self._file_frame = Frame(body, bg=theme['bg'])
        Label(self._file_frame, text="脚本路径", fg=theme['dim'], bg=theme['bg'],
              font=(self._fm, 7)).pack(anchor='w', pady=(0, 4))
        path_row = Frame(self._file_frame, bg=theme['bg'])
        path_row.pack(fill='x')
        self._path_entry = Entry(path_row, bg=theme['card'], fg=theme['text'],
                                  insertbackground=theme['accent'], relief='flat',
                                  font=(self._f, 9), bd=0, highlightthickness=1,
                                  highlightbackground=theme['border_subtle'],
                                  highlightcolor=theme['accent'])
        self._path_entry.pack(side='left', fill='x', expand=True, ipady=5)
        self._path_entry.insert(0, file_path)

        browse_btn = Label(path_row, text="...", fg=theme['accent'], bg=theme['card2'],
                           font=(self._fm, 8), cursor='hand2', padx=8, pady=4)
        browse_btn.pack(side='right', padx=(4, 0))
        browse_btn.bind('<Button-1>', self._browse_file)

        # ── code editor frame (inline mode) ──
        self._code_frame = Frame(body, bg=theme['bg'])

        editor_frame = Frame(self._code_frame, bg=theme['card'])
        editor_frame.pack(fill='both', expand=True)

        # 行号
        self._line_nums = Text(editor_frame, width=4, bg=theme['card2'], fg=theme['dim'],
                                font=(self._fm, 9), relief='flat', bd=0,
                                highlightthickness=0, state='disabled',
                                takefocus=0, padx=4, pady=4)
        self._line_nums.pack(side='left', fill='y')

        # 代码区
        self._code = Text(editor_frame, bg=theme['card'], fg=theme['text'],
                          font=(self._fm, 9), relief='flat', bd=0,
                          insertbackground=theme['accent'],
                          selectbackground=theme['accent_glow'],
                          selectforeground=theme['text'],
                          highlightthickness=1,
                          highlightbackground=theme['border_subtle'],
                          highlightcolor=theme['border'],
                          wrap='none', undo=True, padx=4, pady=4,
                          tabs=('4c',))

        scrollbar = Scrollbar(editor_frame, command=self._on_scroll,
                              bg=theme['card'], troughcolor=theme['bg'],
                              highlightthickness=0, bd=0)
        self._code.configure(yscrollcommand=self._on_code_scroll)

        scrollbar.pack(side='right', fill='y')
        self._code.pack(side='left', fill='both', expand=True)

        # 配置语法高亮 tag
        self._code.tag_configure('keyword', foreground=theme['mauve'])
        self._code.tag_configure('builtin', foreground=theme['yellow'])
        self._code.tag_configure('string', foreground=theme['green'])
        self._code.tag_configure('comment', foreground=theme['dim'])
        self._code.tag_configure('number', foreground=theme['peach'])
        self._code.tag_configure('ctx', foreground=theme['accent'])

        if code:
            self._code.insert('1.0', code)

        self._code.bind('<KeyRelease>', self._on_key)
        self._code.bind('<Tab>', self._on_tab)
        self._scrollbar = scrollbar

        # ── options row ──
        opts = Frame(body, bg=theme['bg'])
        opts.pack(fill='x', pady=(6, 0))

        Label(opts, text="超时(秒)", fg=theme['dim'], bg=theme['bg'],
              font=(self._fm, 7)).pack(side='left')
        self._timeout_entry = Entry(opts, bg=theme['card'], fg=theme['text'],
                                     insertbackground=theme['accent'], relief='flat',
                                     font=(self._fm, 8), bd=0, width=5,
                                     highlightthickness=1,
                                     highlightbackground=theme['border_subtle'],
                                     highlightcolor=theme['accent'])
        self._timeout_entry.pack(side='left', padx=(4, 12), ipady=2)
        self._timeout_entry.insert(0, str(timeout))

        self._show_output_var = StringVar(value='1' if show_output else '0')
        self._output_label = Label(opts, text="☑ 显示输出" if show_output else "☐ 显示输出",
                                    fg=theme['accent'] if show_output else theme['dim'],
                                    bg=theme['bg'], font=(self._fm, 7), cursor='hand2')
        self._output_label.pack(side='left')
        self._output_label.bind('<Button-1>', self._toggle_output)

        # ── output panel ──
        Label(body, text="输出", fg=theme['dim'], bg=theme['bg'],
              font=(self._fm, 7)).pack(anchor='w', pady=(6, 2))

        out_frame = Frame(body, bg=theme['card'])
        out_frame.pack(fill='x')

        self._output = Text(out_frame, bg=theme['card'], fg=theme['sub'],
                            font=(self._fm, 8), relief='flat', bd=0, height=5,
                            highlightthickness=1,
                            highlightbackground=theme['border_subtle'],
                            highlightcolor=theme['border'],
                            wrap='word', state='disabled', padx=4, pady=4)
        out_scroll = Scrollbar(out_frame, command=self._output.yview,
                               bg=theme['card'], troughcolor=theme['bg'],
                               highlightthickness=0, bd=0)
        self._output.configure(yscrollcommand=out_scroll.set)
        out_scroll.pack(side='right', fill='y')
        self._output.pack(side='left', fill='both', expand=True)

        # ── buttons ──
        bf = Frame(body, bg=theme['bg'])
        bf.pack(fill='x', pady=(8, 0))

        # 运行按钮
        run_btn = Canvas(bf, width=60, height=28, bg=theme['bg'], highlightthickness=0,
                         cursor='hand2')
        run_btn.pack(side='left')
        pts = rr_points(0, 0, 60, 28, 14)
        run_btn.create_polygon(pts, fill=theme['green'], outline='')
        run_btn.create_text(30, 14, text="运行", fill='#1e1e2e', font=(self._f, 8, 'bold'))
        run_btn.bind('<Button-1>', lambda e: self._run())

        # 保存按钮
        save_btn = Canvas(bf, width=60, height=28, bg=theme['bg'], highlightthickness=0,
                          cursor='hand2')
        save_btn.pack(side='right')
        pts2 = rr_points(0, 0, 60, 28, 14)
        save_btn.create_polygon(pts2, fill=theme['accent'], outline='')
        save_btn.create_text(30, 14, text="保存", fill='#1e1e2e', font=(self._f, 8, 'bold'))
        save_btn.bind('<Button-1>', lambda e: self._save())

        cancel_btn = Canvas(bf, width=60, height=28, bg=theme['bg'], highlightthickness=0,
                            cursor='hand2')
        cancel_btn.pack(side='right', padx=(0, 8))
        pts3 = rr_points(0, 0, 60, 28, 14)
        cancel_btn.create_polygon(pts3, fill='', outline=theme['border'])
        cancel_btn.create_text(30, 14, text="取消", fill=theme['dim'], font=(self._f, 8))
        cancel_btn.bind('<Button-1>', lambda e: self.win.destroy())

        self.win.bind('<Escape>', lambda e: self.win.destroy())

        # 初始化
        self._update_mode_pills()
        self._update_mode_visibility()
        self._update_line_numbers()
        self._apply_highlight()

        dw, dh = 520, 560
        self.win.geometry(f"{dw}x{dh}")
        self.win.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - dw) // 2
        py = parent.winfo_rooty() + max(0, (parent.winfo_height() - dh) // 2)
        self.win.geometry(f"+{px}+{py}")
        self.win.grab_set()
        self._code.focus_set()

    # ── mode ──

    def _switch_mode(self, mode):
        self._mode_var.set(mode)
        self._update_mode_pills()
        self._update_mode_visibility()

    def _update_mode_pills(self):
        c = self.theme
        current = self._mode_var.get()
        for lbl in self._mode_labels:
            if lbl._mode == current:
                lbl.configure(bg=c['accent'], fg='#1e1e2e')
            else:
                lbl.configure(bg=c['card2'], fg=c['dim'])

    def _update_mode_visibility(self):
        mode = self._mode_var.get()
        self._file_frame.pack_forget()
        self._code_frame.pack_forget()
        if mode == 'file':
            self._file_frame.pack(fill='x', pady=(0, 6))
        else:
            self._code_frame.pack(fill='both', expand=True)

    def _browse_file(self, event=None):
        path = filedialog.askopenfilename(
            parent=self.win,
            title="选择 Python 脚本",
            filetypes=[("Python 文件", "*.py"), ("所有文件", "*.*")]
        )
        if path:
            self._path_entry.delete(0, 'end')
            self._path_entry.insert(0, path)

    # ── syntax highlight ──

    def _on_key(self, event=None):
        if self._highlight_job:
            self.win.after_cancel(self._highlight_job)
        self._highlight_job = self.win.after(200, self._apply_highlight)
        self._update_line_numbers()

    def _on_tab(self, event):
        self._code.insert('insert', '    ')
        return 'break'

    def _apply_highlight(self):
        self._highlight_job = None
        code = self._code.get('1.0', 'end-1c')
        # 清除所有 tag
        for tag in ('keyword', 'builtin', 'string', 'comment', 'number', 'ctx'):
            self._code.tag_remove(tag, '1.0', 'end')

        # tag 优先级：string > comment > keyword/builtin/ctx > number
        self._code.tag_raise('string')
        self._code.tag_raise('comment')

        for i, line in enumerate(code.split('\n'), 1):
            # 先找字符串区域，用于排除误判
            str_ranges = []
            for m in re.finditer(r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"[^"\\]*(?:\\.[^"\\]*)*"|\'[^\'\\]*(?:\\.[^\'\\]*)*\')', line):
                self._code.tag_add('string', f'{i}.{m.start()}', f'{i}.{m.end()}')
                str_ranges.append((m.start(), m.end()))

            def in_string(pos):
                return any(s <= pos < e for s, e in str_ranges)

            # 注释 — 跳过字符串内的 #
            for j, ch in enumerate(line):
                if ch == '#' and not in_string(j):
                    self._code.tag_add('comment', f'{i}.{j}', f'{i}.end')
                    break

            # 关键字和内置函数
            for m in re.finditer(r'\b(\w+)\b', line):
                if in_string(m.start()):
                    continue
                word = m.group(1)
                if word in _KEYWORDS:
                    self._code.tag_add('keyword', f'{i}.{m.start()}', f'{i}.{m.end()}')
                elif word in _BUILTINS:
                    self._code.tag_add('builtin', f'{i}.{m.start()}', f'{i}.{m.end()}')
                elif word == 'ctx':
                    self._code.tag_add('ctx', f'{i}.{m.start()}', f'{i}.{m.end()}')

            # 数字
            for m in re.finditer(r'\b\d+\.?\d*\b', line):
                if not in_string(m.start()):
                    self._code.tag_add('number', f'{i}.{m.start()}', f'{i}.{m.end()}')

    def _update_line_numbers(self):
        self._line_nums.configure(state='normal')
        self._line_nums.delete('1.0', 'end')
        line_count = int(self._code.index('end-1c').split('.')[0])
        nums = '\n'.join(str(i) for i in range(1, line_count + 1))
        self._line_nums.insert('1.0', nums)
        self._line_nums.configure(state='disabled')

    def _on_scroll(self, *args):
        self._code.yview(*args)
        self._line_nums.yview(*args)

    def _on_code_scroll(self, *args):
        self._scrollbar.set(*args)
        self._line_nums.yview_moveto(args[0])

    # ── toggle ──

    def _toggle_output(self, event=None):
        v = '0' if self._show_output_var.get() == '1' else '1'
        self._show_output_var.set(v)
        if v == '1':
            self._output_label.configure(text="☑ 显示输出", fg=self.theme['accent'])
        else:
            self._output_label.configure(text="☐ 显示输出", fg=self.theme['dim'])

    # ── output ──

    def _append_output(self, text: str):
        try:
            self._output.configure(state='normal')
            self._output.insert('end', text)
            self._output.see('end')
            self._output.configure(state='disabled')
        except Exception:
            pass

    def _clear_output(self):
        self._output.configure(state='normal')
        self._output.delete('1.0', 'end')
        self._output.configure(state='disabled')

    # ── run ──

    def _run(self):
        """即时测试运行"""
        self._clear_output()
        mode = self._mode_var.get()
        if mode == 'inline':
            code = self._code.get('1.0', 'end-1c').strip()
            if not code:
                return
            if self._run_callback:
                self._run_callback(code, 'inline', '', self._append_output)
        else:
            path = self._path_entry.get().strip()
            if not path:
                return
            if self._run_callback:
                self._run_callback('', 'file', path, self._append_output)

    # ── save ──

    def _save(self):
        mode = self._mode_var.get()
        timeout = 30
        try:
            timeout = int(self._timeout_entry.get().strip())
        except ValueError:
            pass

        self.result = {
            'mode': mode,
            'timeout': timeout,
            'show_output': self._show_output_var.get() == '1',
        }

        if mode == 'inline':
            self.result['code'] = self._code.get('1.0', 'end-1c')
        else:
            self.result['path'] = self._path_entry.get().strip()

        self.win.destroy()

    # ── drag ──

    def _ds(self, e):
        self._drag['x'] = e.x_root - self.win.winfo_x()
        self._drag['y'] = e.y_root - self.win.winfo_y()

    def _dm(self, e):
        self.win.geometry(f"+{e.x_root-self._drag['x']}+{e.y_root-self._drag['y']}")

    def show(self):
        self.win.wait_window()
        return self.result
