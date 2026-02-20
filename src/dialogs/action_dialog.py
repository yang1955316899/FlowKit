"""操作增删改对话框"""

from tkinter import Toplevel, Label, Entry, Frame, Canvas, StringVar
from ..widgets.draw import rr_points, pill
from ..utils.icons import ICON_CATEGORIES


ACTION_TYPES = [
    ('app', '应用'),
    ('file', '文件'),
    ('folder', '文件夹'),
    ('url', '网址'),
    ('shell', '脚本'),
    ('snippet', '文本'),
    ('keys', '按键'),
    ('combo', '组合'),
    ('script', 'Python'),
]

# target 字段的标签随类型变化
TARGET_LABELS = {
    'app': '程序路径',
    'file': '文件路径',
    'folder': '文件夹路径',
    'url': '网址',
    'shell': '命令',
    'snippet': '要复制的文本',
    'keys': '按键组合 (如 ctrl+shift+a)',
    'combo': '描述',
    'script': '描述',
}


class ActionDialog:

    def __init__(self, parent, theme: dict, action: dict = None, executor=None):
        self.result = None
        self.theme = theme
        self._executor = executor
        self._f = theme['font']
        self._fm = theme['mono']
        self._drag = {'x': 0, 'y': 0}
        self._type_labels = []
        self._action_type = StringVar(value=action.get('type', 'app') if action else 'app')

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

        title = "编辑操作" if action else "添加操作"
        Label(tb, text=title, fg=theme['sub'], bg=theme['card'],
              font=(self._f, 8, 'bold')).pack(side='left', padx=(6, 0))

        cl = Label(tb, text="\u00D7", fg=theme['dim'], bg=theme['card'],
                   font=(self._f, 11), cursor='hand2')
        cl.pack(side='right', padx=10)
        cl.bind('<Button-1>', lambda e: self.win.destroy())
        tb.bind('<Button-1>', self._ds)
        tb.bind('<B1-Motion>', self._dm)

        Frame(inner, bg=theme['border_subtle'], height=1).pack(fill='x')

        # form area
        self._form = Frame(inner, bg=theme['bg'])
        self._form.pack(fill='both', expand=True, padx=16, pady=(10, 14))

        # type selector row
        type_frame = Frame(self._form, bg=theme['bg'])
        type_frame.pack(fill='x', pady=(0, 8))

        for type_id, type_label in ACTION_TYPES:
            btn = Label(type_frame, text=type_label, cursor='hand2',
                        font=(self._fm, 7), padx=6, pady=2)
            btn.pack(side='left', padx=(0, 3))
            btn._type_id = type_id
            btn.bind('<Button-1>', lambda e, t=type_id: self._select_type(t))
            self._type_labels.append(btn)

        # ── fields container ──
        self._fields_frame = Frame(self._form, bg=theme['bg'])
        self._fields_frame.pack(fill='both', expand=True)

        self._entries = {}

        # Label field (always visible)
        Label(self._fields_frame, text="标签", fg=theme['dim'], bg=theme['bg'],
              font=(self._fm, 7)).pack(anchor='w', pady=(0, 4))
        self._entries['label'] = self._make_entry(self._fields_frame)
        if action:
            self._entries['label'].insert(0, action.get('label', ''))

        # Target field (always visible, label changes per type)
        self._target_label = Label(self._fields_frame, text="目标", fg=theme['dim'],
                                    bg=theme['bg'], font=(self._fm, 7))
        self._target_label.pack(anchor='w', pady=(8, 4))
        self._entries['target'] = self._make_entry(self._fields_frame)
        if action:
            self._entries['target'].insert(0, action.get('target', ''))

        # Args field (app only)
        self._args_frame = Frame(self._fields_frame, bg=theme['bg'])
        Label(self._args_frame, text="参数", fg=theme['dim'], bg=theme['bg'],
              font=(self._fm, 7)).pack(anchor='w', pady=(0, 4))
        self._entries['args'] = self._make_entry(self._args_frame)
        if action:
            self._entries['args'].insert(0, action.get('args', ''))

        # Admin toggle (app only)
        self._admin_var = StringVar(value='1' if action and action.get('admin') else '0')
        self._admin_frame = Frame(self._fields_frame, bg=theme['bg'])
        self._admin_label = Label(self._admin_frame, text="☐ 以管理员运行", fg=theme['dim'],
                                   bg=theme['bg'], font=(self._fm, 7), cursor='hand2')
        self._admin_label.pack(anchor='w')
        self._admin_label.bind('<Button-1>', self._toggle_admin)

        # Shell type (shell only)
        self._shell_frame = Frame(self._fields_frame, bg=theme['bg'])
        Label(self._shell_frame, text="脚本类型", fg=theme['dim'], bg=theme['bg'],
              font=(self._fm, 7)).pack(anchor='w', pady=(0, 4))
        self._shell_type_var = StringVar(value=action.get('shell_type', 'cmd') if action else 'cmd')
        shell_opts = Frame(self._shell_frame, bg=theme['bg'])
        shell_opts.pack(fill='x')
        self._shell_labels = []
        for st in ['cmd', 'powershell', 'python']:
            lbl = Label(shell_opts, text=st, cursor='hand2',
                        font=(self._fm, 7), padx=6, pady=2)
            lbl.pack(side='left', padx=(0, 3))
            lbl.bind('<Button-1>', lambda e, s=st: self._select_shell(s))
            self._shell_labels.append(lbl)

        # Show output toggle (shell only)
        self._show_output_var = StringVar(
            value='1' if action and action.get('show_output') else '0')
        self._output_frame = Frame(self._fields_frame, bg=theme['bg'])
        self._output_label = Label(self._output_frame, text="☐ 显示输出",
                                    fg=theme['dim'], bg=theme['bg'],
                                    font=(self._fm, 7), cursor='hand2')
        self._output_label.pack(anchor='w')
        self._output_label.bind('<Button-1>', self._toggle_output)

        # Combo edit button (combo only)
        self._combo_frame = Frame(self._fields_frame, bg=theme['bg'])
        self._combo_steps = list(action.get('steps', [])) if action else []
        self._combo_delay = action.get('delay', 500) if action else 500
        combo_btn = Label(self._combo_frame, text="编辑步骤...", fg=theme['accent'],
                          bg=theme['card2'], font=(self._f, 8), cursor='hand2',
                          padx=10, pady=4)
        combo_btn.pack(fill='x')
        combo_btn.bind('<Button-1>', lambda e: self._edit_combo())
        self._combo_info = Label(self._combo_frame, text=f"{len(self._combo_steps)} 个步骤",
                                  fg=theme['dim'], bg=theme['bg'], font=(self._fm, 7))
        self._combo_info.pack(anchor='w', pady=(4, 0))

        # Script editor button (script only)
        self._script_frame = Frame(self._fields_frame, bg=theme['bg'])
        self._script_code = action.get('code', '') if action else ''
        self._script_mode = action.get('mode', 'inline') if action else 'inline'
        self._script_path = action.get('path', '') if action else ''
        self._script_timeout = action.get('timeout', 30) if action else 30
        self._script_show_output = action.get('show_output', True) if action else True

        script_btn = Label(self._script_frame, text="编辑脚本...", fg=theme['accent'],
                           bg=theme['card2'], font=(self._f, 8), cursor='hand2',
                           padx=10, pady=4)
        script_btn.pack(fill='x')
        script_btn.bind('<Button-1>', lambda e: self._edit_script())
        self._script_info = Label(self._script_frame,
                                   text=self._get_script_info(),
                                   fg=theme['dim'], bg=theme['bg'], font=(self._fm, 7))
        self._script_info.pack(anchor='w', pady=(4, 0))

        # icon picker
        self._icon_var = StringVar(value=action.get('icon', '\u2726') if action else '\u2726')
        icon_frame = Frame(self._form, bg=theme['bg'])
        icon_frame.pack(fill='x', pady=(8, 0))
        Label(icon_frame, text="图标", fg=theme['dim'], bg=theme['bg'],
              font=(self._fm, 7)).pack(side='left')
        self._icon_display = Label(icon_frame, text=self._icon_var.get(),
                                    font=('Segoe UI Emoji', 14),
                                    fg=theme['text'], bg=theme['bg'], cursor='hand2')
        self._icon_display.pack(side='left', padx=(8, 0))
        self._icon_display.bind('<Button-1>', self._show_icon_picker)

        # buttons
        bf = Frame(self._form, bg=theme['bg'])
        bf.pack(fill='x', pady=(12, 0))

        sc = Canvas(bf, width=60, height=28, bg=theme['bg'], highlightthickness=0, cursor='hand2')
        sc.pack(side='right')
        pts = rr_points(0, 0, 60, 28, 14)
        sc.create_polygon(pts, fill=theme['accent'], outline='')
        sc.create_text(30, 14, text="保存", fill='#1e1e2e', font=(self._f, 8, 'bold'))
        sc.bind('<Button-1>', lambda e: self._save())

        cc = Canvas(bf, width=60, height=28, bg=theme['bg'], highlightthickness=0, cursor='hand2')
        cc.pack(side='right', padx=(0, 8))
        pts2 = rr_points(0, 0, 60, 28, 14)
        cc.create_polygon(pts2, fill='', outline=theme['border'])
        cc.create_text(30, 14, text="取消", fill=theme['dim'], font=(self._f, 8))
        cc.bind('<Button-1>', lambda e: self.win.destroy())

        self.win.bind('<Return>', lambda e: self._save())
        self.win.bind('<Escape>', lambda e: self.win.destroy())

        # apply initial state
        self._update_type_pills()
        self._update_field_visibility()
        self._update_admin_display()
        self._update_shell_pills()
        self._update_output_display()

        dw, dh = 340, 420
        self.win.geometry(f"{dw}x{dh}")
        self.win.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - dw) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - dh) // 2
        self.win.geometry(f"+{px}+{py}")
        self.win.grab_set()
        self._entries['label'].focus_set()

    def _make_entry(self, parent):
        c = self.theme
        e = Entry(parent, bg=c['card'], fg=c['text'],
                  insertbackground=c['accent'], relief='flat',
                  font=(self._f, 9), bd=0, highlightthickness=1,
                  highlightbackground=c['border_subtle'],
                  highlightcolor=c['accent'])
        e.pack(fill='x', ipady=5)
        return e

    # ── type switching ──

    def _select_type(self, type_id):
        self._action_type.set(type_id)
        self._update_type_pills()
        self._update_field_visibility()

    def _update_type_pills(self):
        c = self.theme
        current = self._action_type.get()
        for lbl in self._type_labels:
            if lbl._type_id == current:
                lbl.configure(bg=c['accent'], fg='#1e1e2e')
            else:
                lbl.configure(bg=c['card2'], fg=c['dim'])

    def _update_field_visibility(self):
        t = self._action_type.get()

        # update target label
        self._target_label.configure(text=TARGET_LABELS.get(t, '目标'))

        # hide all optional frames
        self._args_frame.pack_forget()
        self._admin_frame.pack_forget()
        self._shell_frame.pack_forget()
        self._output_frame.pack_forget()
        self._combo_frame.pack_forget()
        self._script_frame.pack_forget()

        # show relevant ones
        if t == 'app':
            self._args_frame.pack(fill='x', pady=(8, 0))
            self._admin_frame.pack(fill='x', pady=(6, 0))
        elif t == 'shell':
            self._shell_frame.pack(fill='x', pady=(8, 0))
            self._output_frame.pack(fill='x', pady=(6, 0))
        elif t == 'combo':
            self._combo_frame.pack(fill='x', pady=(8, 0))
        elif t == 'script':
            self._script_frame.pack(fill='x', pady=(8, 0))

    # ── shell type ──

    def _select_shell(self, shell_type):
        self._shell_type_var.set(shell_type)
        self._update_shell_pills()

    def _update_shell_pills(self):
        c = self.theme
        current = self._shell_type_var.get()
        for lbl in self._shell_labels:
            if lbl.cget('text') == current:
                lbl.configure(bg=c['accent'], fg='#1e1e2e')
            else:
                lbl.configure(bg=c['card2'], fg=c['dim'])

    # ── toggles ──

    def _toggle_admin(self, event=None):
        self._admin_var.set('0' if self._admin_var.get() == '1' else '1')
        self._update_admin_display()

    def _update_admin_display(self):
        if self._admin_var.get() == '1':
            self._admin_label.configure(text="☑ 以管理员运行", fg=self.theme['accent'])
        else:
            self._admin_label.configure(text="☐ 以管理员运行", fg=self.theme['dim'])

    def _toggle_output(self, event=None):
        self._show_output_var.set('0' if self._show_output_var.get() == '1' else '1')
        self._update_output_display()

    def _update_output_display(self):
        if self._show_output_var.get() == '1':
            self._output_label.configure(text="☑ 显示输出", fg=self.theme['accent'])
        else:
            self._output_label.configure(text="☐ 显示输出", fg=self.theme['dim'])

    # ── combo editor ──

    def _edit_combo(self):
        from .combo_editor import ComboEditor
        result = ComboEditor(self.win, self.theme,
                             combo={'steps': self._combo_steps,
                                    'delay': self._combo_delay}).show()
        if result:
            self._combo_steps = result['steps']
            self._combo_delay = result['delay']
            self._combo_info.configure(text=f"{len(self._combo_steps)} 个步骤, {self._combo_delay}ms 延迟")

    # ── script editor ──

    def _edit_script(self):
        from .script_editor import ScriptEditorDialog

        run_cb = None
        if self._executor and self._executor._script_runner:
            runner = self._executor._script_runner

            def run_cb(code, mode, path, on_output):
                import threading

                def do_run():
                    if mode == 'file':
                        result = runner.run_file(path, timeout=30, on_output=on_output)
                    else:
                        result = runner.run(code, timeout=30, on_output=on_output)
                    if result.stderr:
                        on_output(f'\n{result.stderr}')
                    status = '完成' if result.success else f'失败 (退出码 {result.returncode})'
                    on_output(f'\n--- {status} ---\n')

                threading.Thread(target=do_run, daemon=True).start()

        result = ScriptEditorDialog(
            self.win, self.theme,
            code=self._script_code,
            mode=self._script_mode,
            file_path=self._script_path,
            timeout=self._script_timeout,
            show_output=self._script_show_output,
            run_callback=run_cb,
        ).show()
        if result:
            self._script_mode = result.get('mode', 'inline')
            self._script_code = result.get('code', '')
            self._script_path = result.get('path', '')
            self._script_timeout = result.get('timeout', 30)
            self._script_show_output = result.get('show_output', True)
            self._script_info.configure(text=self._get_script_info())

    def _get_script_info(self):
        if self._script_mode == 'file':
            p = self._script_path or '未选择'
            return f"文件: {p}"
        lines = len(self._script_code.split('\n')) if self._script_code else 0
        return f"内嵌代码, {lines} 行"

    # ── icon picker ──

    def _show_icon_picker(self, event=None):
        c = self.theme
        picker = Toplevel(self.win)
        picker.overrideredirect(True)
        picker.attributes('-topmost', True)
        picker.configure(bg=c['border'])

        inner = Frame(picker, bg=c['bg'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)

        for cat_name, icons in ICON_CATEGORIES.items():
            Label(inner, text=cat_name, fg=c['dim'], bg=c['bg'],
                  font=(self._fm, 7)).pack(anchor='w', padx=8, pady=(6, 2))
            row = Frame(inner, bg=c['bg'])
            row.pack(fill='x', padx=8)
            for emoji, name in icons:
                lbl = Label(row, text=emoji, font=('Segoe UI Emoji', 12),
                            bg=c['bg'], cursor='hand2')
                lbl.pack(side='left', padx=2, pady=2)
                lbl.bind('<Button-1>', lambda e, em=emoji: self._pick_icon(em, picker))

        pw, ph = 320, 280
        picker.geometry(f"{pw}x{ph}")
        px = self.win.winfo_x() + 10
        py = self.win.winfo_y() + self.win.winfo_height() - ph - 10
        picker.geometry(f"+{px}+{py}")
        picker.grab_set()

    def _pick_icon(self, emoji, picker):
        self._icon_var.set(emoji)
        self._icon_display.configure(text=emoji)
        picker.destroy()

    # ── drag ──

    def _ds(self, e):
        self._drag['x'] = e.x_root - self.win.winfo_x()
        self._drag['y'] = e.y_root - self.win.winfo_y()

    def _dm(self, e):
        self.win.geometry(f"+{e.x_root-self._drag['x']}+{e.y_root-self._drag['y']}")

    # ── save ──

    def _save(self):
        label = self._entries['label'].get().strip()
        target = self._entries['target'].get().strip()
        action_type = self._action_type.get()

        if not label:
            return

        result = {
            'type': action_type,
            'label': label,
            'icon': self._icon_var.get(),
            'target': target,
        }

        if action_type == 'app':
            args = self._entries['args'].get().strip()
            if args:
                result['args'] = args
            if self._admin_var.get() == '1':
                result['admin'] = True

        if action_type == 'shell':
            result['shell_type'] = self._shell_type_var.get()
            if self._show_output_var.get() == '1':
                result['show_output'] = True

        if action_type == 'combo':
            result['steps'] = self._combo_steps
            result['delay'] = self._combo_delay

        if action_type == 'script':
            result['mode'] = self._script_mode
            result['timeout'] = self._script_timeout
            if self._script_show_output:
                result['show_output'] = True
            if self._script_mode == 'inline':
                result['code'] = self._script_code
            else:
                result['path'] = self._script_path

        self.result = result
        self.win.destroy()

    def show(self):
        self.win.wait_window()
        return self.result
