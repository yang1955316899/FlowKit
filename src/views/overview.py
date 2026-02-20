"""Overview 视图 - Token 列表 + CRUD"""

from tkinter import Canvas
from .base import BaseView
from ..widgets.draw import rrect, pill


class OverviewView(BaseView):

    def render(self, canvas: Canvas, w: int, y: int) -> int:
        app = self.app
        c = self.theme
        f, fm = self._f, self._fm
        mx = 10
        cw = w - 20

        for i, tok in enumerate(app.tokens):
            if app._delete_confirm_idx == i:
                y = self._draw_del_confirm(canvas, w, y, i, tok)
                continue

            data = app._overview_data.get(i, {})
            name = tok.get('name', f'Token {i+1}')
            days = int(data.get('remainingDays', 0) or 0)
            expire = data.get('expireTime', '--')
            today_data = data.get('today', {})
            cost_str = today_data.get('creditUsedFormatted', '$0.00')
            limit = tok.get('daily_limit', 0)

            try:
                cost_val = float(cost_str.replace('$', '').replace(',', ''))
            except Exception:
                cost_val = 0.0

            dc = c['green'] if days > 14 else c['yellow'] if days > 7 else c['red']
            dc_glow = c['green_glow'] if days > 14 else c['yellow_glow'] if days > 7 else c['red_glow']

            has_bar = limit and limit > 0
            ch = 72 if has_bar else 52

            # card bg
            rrect(canvas, mx, y, mx+cw, y+ch, 10, fill=c['card'])
            canvas.create_line(mx+10, y+1, mx+cw-10, y+1, fill=c['border_subtle'])

            # row 1: dot + name + days + actions
            row1_y = y + 16

            # status dot
            canvas.create_oval(mx+14, row1_y-4, mx+22, row1_y+4, fill=dc, outline='')

            # name
            canvas.create_text(mx+30, row1_y, text=name, fill=c['text'],
                               font=(f, 9, 'bold'), anchor='w', tags=f'ov_go_{i}')
            nw = sum(13 if ord(ch_) > 0x2e80 else 7 for ch_ in name) + 12
            canvas.create_rectangle(mx+28, y+4, mx+28+nw, y+28, fill='', outline='', tags=f'ov_go_{i}')

            # action buttons (right side)
            abx = mx + cw - 14
            # delete ×
            canvas.create_text(abx, row1_y, text="\u00D7", fill=c['dim'],
                               font=(f, 10), anchor='e', tags=f'ov_rm_{i}')
            canvas.create_rectangle(abx-14, y+4, abx+2, y+28, fill='', outline='', tags=f'ov_rm_{i}')
            abx -= 22
            # edit ✎
            canvas.create_text(abx, row1_y, text="\u270E", fill=c['dim'],
                               font=(f, 9), anchor='e', tags=f'ov_ed_{i}')
            canvas.create_rectangle(abx-14, y+4, abx+2, y+28, fill='', outline='', tags=f'ov_ed_{i}')
            abx -= 24

            # days pill
            dt = f"{days}d"
            dpw = len(dt) * 7 + 12
            dpx = abx - dpw
            pill(canvas, dpx, row1_y-8, dpx+dpw, row1_y+8, fill=dc_glow)
            canvas.create_text(dpx + dpw//2, row1_y, text=dt, fill=dc, font=(fm, 7, 'bold'))

            # row 2: progress bar + cost
            if has_bar:
                pct = min(cost_val / limit, 1.0)
                bc = c['red'] if pct > 0.9 else c['yellow'] if pct > 0.7 else c['accent']

                bar_x = mx + 14
                bar_y = y + 34
                bar_w = cw - 28
                bar_h = 4
                pill(canvas, bar_x, bar_y, bar_x+bar_w, bar_y+bar_h, fill=c['bar_bg'])
                fw = max(2, int(bar_w * pct))
                if fw > 3:
                    pill(canvas, bar_x, bar_y, bar_x+fw, bar_y+bar_h, fill=bc)

                info_y = bar_y + bar_h + 10
                canvas.create_text(mx+14, info_y, text=cost_str, fill=c['text'],
                                   font=(fm, 8, 'bold'), anchor='w')
                canvas.create_text(mx+cw//2, info_y, text=f"{pct*100:.1f}%", fill=bc,
                                   font=(fm, 8, 'bold'))
                canvas.create_text(mx+cw-14, info_y, text=f"/ ${limit:.0f}", fill=c['dim'],
                                   font=(fm, 7), anchor='e')

                canvas.create_text(mx+14, y+ch-8, text=expire, fill=c['dim'],
                                   font=(fm, 6), anchor='w')
            else:
                info_y = y + 36
                canvas.create_text(mx+14, info_y, text=cost_str, fill=c['accent'],
                                   font=(fm, 10, 'bold'), anchor='w')
                canvas.create_text(mx+cw-14, info_y, text=expire, fill=c['dim'],
                                   font=(fm, 7), anchor='e')

            y += ch + 8

        # add button
        rrect(canvas, mx, y, mx+cw, y+36, 10, fill='', outline=c['border_subtle'])
        canvas.create_text(mx+cw//2, y+18, text="+  添加 Token", fill=c['dim'],
                           font=(f, 8), tags='ov_add')
        canvas.create_rectangle(mx, y, mx+cw, y+36, fill='', outline='', tags='ov_add')
        y += 44

        return y

    def _draw_del_confirm(self, canvas, w, y, idx, tok):
        c = self.theme
        mx, cw = 10, w - 20
        name = tok.get('name', f'Token {idx+1}')

        rrect(canvas, mx, y, mx+cw, y+44, 10, fill=c['red_glow'])
        canvas.create_text(mx+16, y+15, text=f"删除 {name}?", fill=c['red'],
                           font=(self._f, 8, 'bold'), anchor='w')

        bx = mx + cw - 14
        # Cancel
        cw2 = 50
        pill(canvas, bx-cw2, y+26, bx, y+40, fill=c['card2'])
        canvas.create_text(bx-cw2//2, y+33, text="取消", fill=c['dim'],
                           font=(self._fm, 7), tags='ov_no')
        canvas.create_rectangle(bx-cw2, y+26, bx, y+40, fill='', outline='', tags='ov_no')
        bx -= cw2 + 6
        # OK
        ow = 36
        pill(canvas, bx-ow, y+26, bx, y+40, fill=c['red'])
        canvas.create_text(bx-ow//2, y+33, text="确定", fill='#fff',
                           font=(self._fm, 7, 'bold'), tags=f'ov_ok_{idx}')
        canvas.create_rectangle(bx-ow, y+26, bx, y+40, fill='', outline='', tags=f'ov_ok_{idx}')

        return y + 52

    def on_click(self, canvas: Canvas, event, tags: list[str]) -> bool:
        app = self.app
        for tag in tags:
            if tag.startswith('ov_go_'):
                app._switch_to_detail(int(tag[6:]))
                return True
            if tag.startswith('ov_ed_'):
                app._edit_token(int(tag[6:]))
                return True
            if tag.startswith('ov_rm_'):
                app._request_delete(int(tag[6:]))
                return True
            if tag.startswith('ov_ok_'):
                app._confirm_delete(int(tag[6:]))
                return True
            if tag == 'ov_no':
                app._delete_confirm_idx = None
                app._render()
                return True
            if tag == 'ov_add':
                app._add_token()
                return True
        return False
