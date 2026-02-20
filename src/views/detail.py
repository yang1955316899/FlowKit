"""Detail 视图 - Token 详情 + tabs + copy toast"""

import threading
from tkinter import Canvas
from .base import BaseView
from ..widgets.draw import pill


class DetailView(BaseView):

    def render(self, canvas: Canvas, w: int, y: int) -> int:
        app = self.app
        c = self.theme

        # token tabs
        if len(app.tokens) > 1:
            tx = 12
            for i, tok in enumerate(app.tokens):
                name = tok.get('name', f'T{i+1}')
                short = name[:5] + '..' if len(name) > 6 else name
                active = i == app.current_token_idx

                cjk = sum(1 for ch in short if ord(ch) > 0x2e80)
                ascii_n = len(short) - cjk
                tw = cjk * 12 + ascii_n * 7 + 16
                th = 22

                if active:
                    pill(canvas, tx, y, tx+tw, y+th, fill=c['accent'])
                    canvas.create_text(tx+tw//2, y+th//2, text=short, fill='#fff',
                                       font=(self._f, 8, 'bold'), tags=f'tok_{i}')
                else:
                    pill(canvas, tx, y, tx+tw, y+th, fill=c['card2'])
                    canvas.create_text(tx+tw//2, y+th//2, text=short, fill=c['dim'],
                                       font=(self._f, 8), tags=f'tok_{i}')
                canvas.create_rectangle(tx, y, tx+tw, y+th, fill='', outline='', tags=f'tok_{i}')
                tx += tw + 4

            # copy icon
            cix = w - 18
            pill(canvas, cix-12, y+2, cix+12, y+20, fill=c['card2'])
            canvas.create_text(cix, y+11, text="\u2398", fill=c['dim'],
                               font=(self._f, 10), tags='copy_btn')
            canvas.create_rectangle(cix-12, y, cix+12, y+22, fill='', outline='', tags='copy_btn')
            y += 30
        else:
            y += 4

        # cards
        for card in app.cards:
            y += card.render(canvas, 12, y, w - 24) + 6

        # copy toast
        if app._copy_toast_visible:
            tw = 70
            tx = (w - tw) // 2
            pill(canvas, tx, y+2, tx+tw, y+20, fill=c['green_glow'])
            canvas.create_text(w // 2, y + 11, text="Copied!", fill=c['green'],
                               font=(self._fm, 7, 'bold'))
            y += 26

        return y

    def on_click(self, canvas: Canvas, event, tags: list[str]) -> bool:
        app = self.app
        for tag in tags:
            if tag.startswith('tok_'):
                app._switch_token(int(tag[4:]))
                return True
            if tag == 'copy_btn':
                app._copy_credential()
                return True
        return False
