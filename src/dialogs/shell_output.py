"""Shell 命令输出窗口"""

import subprocess
import threading
from tkinter import Toplevel, Label, Frame, Canvas, Text, Scrollbar


class ShellOutputDialog:

    def __init__(self, parent, theme: dict, title: str = "Output", command: str = "",
                 shell_type: str = "cmd"):
        self.theme = theme
        self._f = theme['font']
        self._fm = theme['mono']
        self._drag = {'x': 0, 'y': 0}
        self._process = None

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
        dot.create_oval(0, 0, 8, 8, fill=theme['green'], outline='')

        Label(tb, text=title, fg=theme['sub'], bg=theme['card'],
              font=(self._f, 8, 'bold')).pack(side='left', padx=(6, 0))

        cl = Label(tb, text="\u00D7", fg=theme['dim'], bg=theme['card'],
                   font=(self._f, 11), cursor='hand2')
        cl.pack(side='right', padx=10)
        cl.bind('<Button-1>', lambda e: self._close())
        tb.bind('<Button-1>', self._ds)
        tb.bind('<B1-Motion>', self._dm)

        Frame(inner, bg=theme['border_subtle'], height=1).pack(fill='x')

        # output area
        text_frame = Frame(inner, bg=theme['bg'])
        text_frame.pack(fill='both', expand=True, padx=8, pady=8)

        self._text = Text(text_frame, bg=theme['card'], fg=theme['text'],
                          font=(self._fm, 8), relief='flat', bd=0,
                          insertbackground=theme['accent'],
                          selectbackground=theme['accent_glow'],
                          selectforeground=theme['text'],
                          highlightthickness=1,
                          highlightbackground=theme['border_subtle'],
                          highlightcolor=theme['border'],
                          wrap='word', state='disabled')

        scrollbar = Scrollbar(text_frame, command=self._text.yview,
                              bg=theme['card'], troughcolor=theme['bg'],
                              highlightthickness=0, bd=0)
        self._text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y')
        self._text.pack(side='left', fill='both', expand=True)

        # status bar
        self._status = Label(inner, text="Running...", fg=theme['yellow'],
                             bg=theme['bg'], font=(self._fm, 7), anchor='w')
        self._status.pack(fill='x', padx=12, pady=(0, 6))

        self.win.bind('<Escape>', lambda e: self._close())

        dw, dh = 420, 320
        self.win.geometry(f"{dw}x{dh}")
        self.win.update_idletasks()
        px = parent.winfo_rootx() + (parent.winfo_width() - dw) // 2
        py = parent.winfo_rooty() + max(0, (parent.winfo_height() - dh) // 2)
        self.win.geometry(f"+{px}+{py}")

        # start command
        if command:
            self._run_command(command, shell_type)

    def _run_command(self, command: str, shell_type: str):
        def run():
            try:
                if shell_type == 'powershell':
                    cmd = ['powershell', '-Command', command]
                elif shell_type == 'python':
                    cmd = ['python', '-c', command]
                else:
                    cmd = command

                self._process = subprocess.Popen(
                    cmd, shell=(shell_type == 'cmd'),
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, encoding='utf-8', errors='replace',
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                for line in self._process.stdout:
                    self.win.after(0, self._append_text, line)

                self._process.wait()
                code = self._process.returncode
                self.win.after(0, self._set_status, code)
            except Exception as e:
                self.win.after(0, self._append_text, f"\nError: {e}\n")
                self.win.after(0, self._set_status, -1)

        threading.Thread(target=run, daemon=True).start()

    def _append_text(self, text: str):
        try:
            self._text.configure(state='normal')
            self._text.insert('end', text)
            self._text.see('end')
            self._text.configure(state='disabled')
        except Exception:
            pass

    def _set_status(self, code: int):
        try:
            c = self.theme
            if code == 0:
                self._status.configure(text="Done (exit 0)", fg=c['green'])
            else:
                self._status.configure(text=f"Exit code: {code}", fg=c['red'])
        except Exception:
            pass

    def _close(self):
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
            except Exception:
                pass
        self.win.destroy()

    def _ds(self, e):
        self._drag['x'] = e.x_root - self.win.winfo_x()
        self._drag['y'] = e.y_root - self.win.winfo_y()

    def _dm(self, e):
        self.win.geometry(f"+{e.x_root-self._drag['x']}+{e.y_root-self._drag['y']}")
