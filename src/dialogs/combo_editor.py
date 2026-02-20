"""组合动作编辑器"""

from tkinter import Toplevel, Label, Entry, Frame, Canvas
from ..widgets.draw import rr_points, rrect, pill


class ComboEditor:

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
        tb = Frame(inner, bg=theme['card'], height=30)
        tb.pack(fill='x')
        tb.pack_propagate(False)

        dot = Canvas(tb, width=8, height=8, bg=theme['card'], highlightthickness=0)
        dot.pack(side='left', padx=(12, 0))
        dot.create_oval(0, 0, 8, 8, fill=theme['accent'], outline='')

        Label(tb, text="Combo Editor", fg=theme['sub'], bg=theme['card'],
              font=(self._f, 8, 'bold')).pack(side='left', padx=(6, 0))

        cl = Label(tb, text="\u00D7", fg=theme['dim'], bg=theme['card'],
                   font=(self._f, 11), cursor='hand2')
        cl.pack(side='right', padx=10)
        cl.bind('<Button-1>', lambda e: self.win.destroy())
        tb.bind('<Button-1>', self._ds)
        tb.bind('<B1-Motion>', self._dm)

        Frame(inner, bg=theme['border_subtle'], height=1).pack(fill='x')

        # content
        self._content = Frame(inner, bg=theme['bg'])
        self._content.pack(fill='both', expand=True, padx=16, pady=(10, 14))

        # delay
        delay_frame = Frame(self._content, bg=theme['bg'])
        delay_frame.pack(fill='x', pady=(0, 8))
        Label(delay_frame, text="DELAY (ms)", fg=theme['dim'], bg=theme['bg'],
              font=(self._fm, 7)).pack(side='left')
        self._delay_entry = Entry(delay_frame, bg=theme['card'], fg=theme['text'],
                                   insertbackground=theme['accent'], relief='flat',
                                   font=(self._fm, 9), bd=0, width=8,
                                   highlightthickness=1,
                                   highlightbackground=theme['border_subtle'],
                                   highlightcolor=theme['accent'])
        self._delay_entry.pack(side='left', padx=(8, 0), ipady=3)
        self._delay_entry.insert(0, str(self._delay))

        # steps list
        self._steps_frame = Frame(self._content, bg=theme['bg'])
        self._steps_frame.pack(fill='both', expand=True)
        self._rebuild_steps()

        # add step button
        add_frame = Frame(self._content, bg=theme['bg'])
        add_frame.pack(fill='x', pady=(8, 0))
        add_btn = Label(add_frame, text="+ Add Step", fg=theme['accent'],
                        bg=theme['card2'], font=(self._f, 8), cursor='hand2',
                        padx=10, pady=4)
        add_btn.pack(fill='x')
        add_btn.bind('<Button-1>', lambda e: self._add_step())

        # buttons
        bf = Frame(self._content, bg=theme['bg'])
        bf.pack(fill='x', pady=(12, 0))

        sc = Canvas(bf, width=60, height=28, bg=theme['bg'], highlightthickness=0, cursor='hand2')
        sc.pack(side='right')
        pts = rr_points(0, 0, 60, 28, 14)
        sc.create_polygon(pts, fill=theme['accent'], outline='')
        sc.create_text(30, 14, text="Save", fill='#1e1e2e', font=(self._f, 8, 'bold'))
        sc.bind('<Button-1>', lambda e: self._save())

        cc = Canvas(bf, width=60, height=28, bg=theme['bg'], highlightthickness=0, cursor='hand2')
        cc.pack(side='right', padx=(0, 8))
        pts2 = rr_points(0, 0, 60, 28, 14)
        cc.create_polygon(pts2, fill='', outline=theme['border'])
        cc.create_text(30, 14, text="Cancel", fill=theme['dim'], font=(self._f, 8))
        cc.bind('<Button-1>', lambda e: self.win.destroy())

        self.win.bind('<Escape>', lambda e: self.win.destroy())

        dw, dh = 320, 400
        self.win.geometry(f"{dw}x{dh}")
        self.win.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - dw) // 2
        py = parent.winfo_rooty() + (parent.winfo_height() - dh) // 2
        self.win.geometry(f"+{px}+{py}")
        self.win.grab_set()

    def _rebuild_steps(self):
        for w in self._steps_frame.winfo_children():
            w.destroy()

        c = self.theme
        for i, step in enumerate(self._steps):
            row = Frame(self._steps_frame, bg=c['card'], padx=8, pady=4)
            row.pack(fill='x', pady=(0, 4))

            Label(row, text=f"#{i+1}", fg=c['dim'], bg=c['card'],
                  font=(self._fm, 7)).pack(side='left')
            Label(row, text=step.get('type', '?'), fg=c['accent'], bg=c['card'],
                  font=(self._fm, 7, 'bold')).pack(side='left', padx=(6, 0))
            Label(row, text=step.get('label', step.get('target', '')),
                  fg=c['text'], bg=c['card'],
                  font=(self._f, 7)).pack(side='left', padx=(6, 0))

            # move up
            if i > 0:
                up = Label(row, text="▲", fg=c['dim'], bg=c['card'],
                           font=(self._fm, 7), cursor='hand2')
                up.pack(side='right', padx=2)
                up.bind('<Button-1>', lambda e, idx=i: self._move_step(idx, -1))

            # move down
            if i < len(self._steps) - 1:
                dn = Label(row, text="▼", fg=c['dim'], bg=c['card'],
                           font=(self._fm, 7), cursor='hand2')
                dn.pack(side='right', padx=2)
                dn.bind('<Button-1>', lambda e, idx=i: self._move_step(idx, 1))

            # delete
            dl = Label(row, text="×", fg=c['red'], bg=c['card'],
                       font=(self._f, 9), cursor='hand2')
            dl.pack(side='right', padx=2)
            dl.bind('<Button-1>', lambda e, idx=i: self._remove_step(idx))

    def _add_step(self):
        from .action_dialog import ActionDialog
        result = ActionDialog(self.win, self.theme).show()
        if result and result.get('type') != 'combo':  # prevent nesting
            self._steps.append(result)
            self._rebuild_steps()

    def _remove_step(self, idx):
        if idx < len(self._steps):
            self._steps.pop(idx)
            self._rebuild_steps()

    def _move_step(self, idx, direction):
        new_idx = idx + direction
        if 0 <= new_idx < len(self._steps):
            self._steps[idx], self._steps[new_idx] = self._steps[new_idx], self._steps[idx]
            self._rebuild_steps()

    def _ds(self, e):
        self._drag['x'] = e.x_root - self.win.winfo_x()
        self._drag['y'] = e.y_root - self.win.winfo_y()

    def _dm(self, e):
        self.win.geometry(f"+{e.x_root-self._drag['x']}+{e.y_root-self._drag['y']}")

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
