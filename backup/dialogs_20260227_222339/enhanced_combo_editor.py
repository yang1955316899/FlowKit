"""增强组合编辑器 — 支持流程控制步骤、嵌套块、变量系统"""

from tkinter import (Toplevel, Label, Entry, Frame, Canvas, Menu, Scrollbar)
from ..widgets.draw import rr_points, rrect
from .step_editor import StepEditor, STEP_TYPES


def _step_summary(step: dict) -> str:
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


def _step_type_name(stype: str) -> str:
    return dict((t, n) for t, n, _ in STEP_TYPES).get(stype, stype)


def _step_icon(stype: str) -> str:
    return dict((t, i) for t, _, i in STEP_TYPES).get(stype, '▸')


class EnhancedComboEditor:

    def __init__(self, parent, theme: dict, combo: dict = None):
        self.result = None
        self.theme = theme
        self._f = theme['font']
        self._fm = theme['mono']
        self._drag = {'x': 0, 'y': 0}
        self._steps = list(combo.get('steps', [])) if combo else []
        self._delay = combo.get('delay', 500) if combo else 500

        self.win = Toplevel(parent)
        self.win.overrideredirect(True)
        self.win.attributes('-topmost', True)
        self.win.configure(bg=theme['border'])

        inner = Frame(self.win, bg=theme['bg'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)

        # title bar
        tb = Frame(inner, bg=theme['card'], height=38)
        tb.pack(fill='x')
        tb.pack_propagate(False)

        dot = Canvas(tb, width=10, height=10, bg=theme['card'], highlightthickness=0)
        dot.pack(side='left', padx=(14, 0))
        dot.create_oval(0, 0, 10, 10, fill=theme['accent'], outline='')

        Label(tb, text="组合编辑器", fg=theme['text'], bg=theme['card'],
              font=(self._f, 10, 'bold')).pack(side='left', padx=(8, 0))

        cl = Label(tb, text="\u00D7", fg=theme['dim'], bg=theme['card'],
                   font=(self._f, 13), cursor='hand2')
        cl.pack(side='right', padx=12)
        cl.bind('<Button-1>', lambda e: self.win.destroy())
        tb.bind('<Button-1>', self._ds)
        tb.bind('<B1-Motion>', self._dm)

        Frame(inner, bg=theme['border_subtle'], height=1).pack(fill='x')

        # content
        self._content = Frame(inner, bg=theme['bg'])
        self._content.pack(fill='both', expand=True, padx=16, pady=(10, 12))

        # delay
        delay_frame = Frame(self._content, bg=theme['bg'])
        delay_frame.pack(fill='x', pady=(0, 8))
        Label(delay_frame, text="延迟 (ms)", fg=theme['sub'], bg=theme['bg'],
              font=(self._f, 9)).pack(side='left')
        self._delay_entry = Entry(delay_frame, bg=theme['card'], fg=theme['text'],
                                   insertbackground=theme['accent'], relief='flat',
                                   font=(self._fm, 10), bd=0, width=8,
                                   highlightthickness=1,
                                   highlightbackground=theme['border_subtle'],
                                   highlightcolor=theme['accent'])
        self._delay_entry.pack(side='left', padx=(10, 0), ipady=5)
        self._delay_entry.insert(0, str(self._delay))

        # scrollable steps area
        steps_outer = Frame(self._content, bg=theme['bg'])
        steps_outer.pack(fill='both', expand=True)

        self._steps_canvas = Canvas(steps_outer, bg=theme['bg'], highlightthickness=0)
        scrollbar = Scrollbar(steps_outer, orient='vertical', command=self._steps_canvas.yview)
        self._steps_frame = Frame(self._steps_canvas, bg=theme['bg'])

        self._steps_frame.bind('<Configure>',
                                lambda e: self._steps_canvas.configure(
                                    scrollregion=self._steps_canvas.bbox('all')))
        self._steps_canvas.create_window((0, 0), window=self._steps_frame, anchor='nw')
        self._steps_canvas.configure(yscrollcommand=scrollbar.set)

        self._steps_canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # bind mousewheel
        self._steps_canvas.bind('<Enter>',
                                 lambda e: self._steps_canvas.bind_all('<MouseWheel>', self._on_scroll))
        self._steps_canvas.bind('<Leave>',
                                 lambda e: self._steps_canvas.unbind_all('<MouseWheel>'))

        self._rebuild_steps()

        # add step button
        add_frame = Frame(self._content, bg=theme['bg'])
        add_frame.pack(fill='x', pady=(8, 0))
        add_btn = Label(add_frame, text="+ 添加步骤 ▾", fg=theme['accent'],
                        bg=theme['card'], font=(self._f, 10), cursor='hand2',
                        padx=12, pady=6)
        add_btn.pack(fill='x')
        add_btn.bind('<Button-1>', lambda e: self._show_add_menu(e))

        # buttons
        bf = Frame(self._content, bg=theme['bg'])
        bf.pack(fill='x', pady=(12, 0))

        sc = Canvas(bf, width=80, height=34, bg=theme['bg'], highlightthickness=0, cursor='hand2')
        sc.pack(side='right')
        pts = rr_points(0, 0, 80, 34, 17)
        sc.create_polygon(pts, fill=theme['accent'], outline='')
        sc.create_text(40, 17, text="保存", fill='#1e1e2e', font=(self._f, 10, 'bold'))
        sc.bind('<Button-1>', lambda e: self._save())

        cc = Canvas(bf, width=80, height=34, bg=theme['bg'], highlightthickness=0, cursor='hand2')
        cc.pack(side='right', padx=(0, 10))
        pts2 = rr_points(0, 0, 80, 34, 17)
        cc.create_polygon(pts2, fill='', outline=theme['border'])
        cc.create_text(40, 17, text="取消", fill=theme['dim'], font=(self._f, 10))
        cc.bind('<Button-1>', lambda e: self.win.destroy())

        self.win.bind('<Escape>', lambda e: self.win.destroy())

        dw, dh = 420, 580
        self.win.geometry(f"{dw}x{dh}")
        self.win.update_idletasks()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()
        px = (sw - dw) // 2
        py = (sh - dh) // 2
        self.win.geometry(f"+{px}+{py}")
        self.win.grab_set()

    def _on_scroll(self, event):
        self._steps_canvas.yview_scroll(-1 * (event.delta // 120), 'units')

    def _rebuild_steps(self):
        for w in self._steps_frame.winfo_children():
            w.destroy()
        self._render_step_list(self._steps_frame, self._steps, prefix='')

    def _render_step_list(self, parent, steps: list, prefix: str, indent: int = 0):
        """递归渲染步骤列表，支持嵌套"""
        c = self.theme
        for i, step in enumerate(steps):
            if not step:
                continue
            stype = step.get('type', '?')
            num = f"{prefix}{i+1}" if prefix else f"{i+1}"

            row = Frame(parent, bg=c['card'], padx=8, pady=5)
            row.pack(fill='x', padx=(indent * 18, 0), pady=(0, 3))

            # number
            Label(row, text=f"#{num}", fg=c['dim'], bg=c['card'],
                  font=(self._fm, 7)).pack(side='left')

            # icon + type
            icon = _step_icon(stype)
            Label(row, text=icon, fg=c['text'], bg=c['card'],
                  font=('Segoe UI Emoji', 9)).pack(side='left', padx=(6, 0))
            Label(row, text=_step_type_name(stype), fg=c['accent'], bg=c['card'],
                  font=(self._f, 9, 'bold')).pack(side='left', padx=(3, 0))

            # summary
            summary = _step_summary(step)
            if summary:
                Label(row, text=summary, fg=c['sub'], bg=c['card'],
                      font=(self._f, 8)).pack(side='left', padx=(6, 0))

            # action buttons
            btns = Frame(row, bg=c['card'])
            btns.pack(side='right')

            # edit
            ed = Label(btns, text="✎", fg=c['sub'], bg=c['card'],
                       font=(self._f, 10), cursor='hand2')
            ed.pack(side='left', padx=2)
            ed.bind('<Button-1>', lambda e, s=steps, idx=i: self._edit_step(s, idx))

            # move up
            if i > 0:
                up = Label(btns, text="▲", fg=c['sub'], bg=c['card'],
                           font=(self._fm, 7), cursor='hand2')
                up.pack(side='left', padx=2)
                up.bind('<Button-1>', lambda e, s=steps, idx=i: self._move_step(s, idx, -1))

            # move down
            if i < len(steps) - 1:
                dn = Label(btns, text="▼", fg=c['sub'], bg=c['card'],
                           font=(self._fm, 7), cursor='hand2')
                dn.pack(side='left', padx=2)
                dn.bind('<Button-1>', lambda e, s=steps, idx=i: self._move_step(s, idx, 1))

            # delete
            dl = Label(btns, text="×", fg=c['red'], bg=c['card'],
                       font=(self._f, 10), cursor='hand2')
            dl.pack(side='left', padx=2)
            dl.bind('<Button-1>', lambda e, s=steps, idx=i: self._remove_step(s, idx))

            # 嵌套块
            if stype == 'if_condition':
                then_steps = step.setdefault('then_steps', [])
                else_steps = step.setdefault('else_steps', [])

                then_header = Frame(parent, bg=c['bg'])
                then_header.pack(fill='x', padx=((indent + 1) * 18, 0), pady=(1, 1))
                Label(then_header, text="then:", fg=c['green'], bg=c['bg'],
                      font=(self._f, 8, 'bold')).pack(side='left')
                add_then = Label(then_header, text="+", fg=c['accent'], bg=c['bg'],
                                 font=(self._f, 9), cursor='hand2')
                add_then.pack(side='left', padx=(6, 0))
                add_then.bind('<Button-1>',
                              lambda e, s=then_steps: self._show_add_menu_for(e, s))

                if then_steps:
                    self._render_step_list(parent, then_steps,
                                           prefix=f"{num}.", indent=indent + 1)

                else_header = Frame(parent, bg=c['bg'])
                else_header.pack(fill='x', padx=((indent + 1) * 18, 0), pady=(1, 1))
                Label(else_header, text="else:", fg=c['yellow'], bg=c['bg'],
                      font=(self._f, 8, 'bold')).pack(side='left')
                add_else = Label(else_header, text="+", fg=c['accent'], bg=c['bg'],
                                 font=(self._f, 9), cursor='hand2')
                add_else.pack(side='left', padx=(6, 0))
                add_else.bind('<Button-1>',
                              lambda e, s=else_steps: self._show_add_menu_for(e, s))

                if else_steps:
                    self._render_step_list(parent, else_steps,
                                           prefix=f"{num}.", indent=indent + 1)

            elif stype == 'loop':
                body_steps = step.setdefault('body_steps', [])

                body_header = Frame(parent, bg=c['bg'])
                body_header.pack(fill='x', padx=((indent + 1) * 18, 0), pady=(1, 1))
                Label(body_header, text="body:", fg=c['accent'], bg=c['bg'],
                      font=(self._f, 8, 'bold')).pack(side='left')
                add_body = Label(body_header, text="+", fg=c['accent'], bg=c['bg'],
                                 font=(self._f, 9), cursor='hand2')
                add_body.pack(side='left', padx=(6, 0))
                add_body.bind('<Button-1>',
                              lambda e, s=body_steps: self._show_add_menu_for(e, s))

                if body_steps:
                    self._render_step_list(parent, body_steps,
                                           prefix=f"{num}.", indent=indent + 1)

    def _show_add_menu(self, event):
        """显示步骤类型选择菜单"""
        self._show_add_menu_for(event, self._steps)

    def _show_add_menu_for(self, event, target_list: list):
        """显示步骤类型选择菜单，添加到指定列表"""
        c = self.theme
        menu = Menu(self.win, tearoff=0,
                    bg=c['card'], fg=c['text'],
                    activebackground=c['accent'],
                    activeforeground='#fff',
                    font=(self._f, 9))

        for type_id, type_name, icon in STEP_TYPES:
            menu.add_command(
                label=f"{icon} {type_name}",
                command=lambda t=type_id, tl=target_list: self._add_step(t, tl))

        menu.tk_popup(event.x_root, event.y_root)

    def _add_step(self, step_type: str, target_list: list):
        """添加新步骤"""
        result = StepEditor(self.win, self.theme, step_type=step_type).show()
        if result:
            target_list.append(result)
            self._rebuild_steps()

    def _edit_step(self, steps_list: list, idx: int):
        """编辑步骤"""
        if idx >= len(steps_list):
            return
        step = steps_list[idx]
        result = StepEditor(self.win, self.theme, step=step,
                            step_type=step.get('type')).show()
        if result:
            # 保留嵌套步骤
            if step.get('type') == 'if_condition':
                result.setdefault('then_steps', step.get('then_steps', []))
                result.setdefault('else_steps', step.get('else_steps', []))
            elif step.get('type') == 'loop':
                result.setdefault('body_steps', step.get('body_steps', []))
            steps_list[idx] = result
            self._rebuild_steps()

    def _remove_step(self, steps_list: list, idx: int):
        if idx < len(steps_list):
            steps_list.pop(idx)
            self._rebuild_steps()

    def _move_step(self, steps_list: list, idx: int, direction: int):
        new_idx = idx + direction
        if 0 <= new_idx < len(steps_list):
            steps_list[idx], steps_list[new_idx] = steps_list[new_idx], steps_list[idx]
            self._rebuild_steps()

    # ── drag ──

    def _ds(self, e):
        self._drag['x'] = e.x_root - self.win.winfo_x()
        self._drag['y'] = e.y_root - self.win.winfo_y()

    def _dm(self, e):
        self.win.geometry(f"+{e.x_root-self._drag['x']}+{e.y_root-self._drag['y']}")

    # ── save ──

    def _save(self):
        try:
            delay = int(self._delay_entry.get().strip())
        except ValueError:
            delay = 500
        self.result = {
            'steps': self._steps,
            'delay': delay,
        }
        self.win.destroy()

    def show(self):
        self.win.wait_window()
        return self.result
