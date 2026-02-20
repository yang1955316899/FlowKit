"""Token 统计业务卡片"""

from ..widgets.base import BaseCard
from ..widgets.draw import rr_points, rrect, pill
from ..utils.http import HttpClient
from tkinter import Canvas
from typing import Any


class TokenStatsCard(BaseCard):

    def __init__(self, config: dict, theme: dict, http: HttpClient):
        super().__init__("Token 统计", config, theme)
        self.http = http
        self._f = theme['font']
        self._fm = theme['mono']

    def fetch_data(self) -> dict[str, Any] | None:
        stats = self.http.post('/api/stats')
        details = self.http.post('/api/request-details')
        if stats:
            stats['details'] = details.get('details', []) if details else []
            stats['requestCount'] = details.get('count', 0) if details else 0
        return stats

    def render(self, canvas: Canvas, x: int, y: int, w: int) -> int:
        data = self._data or {}
        cy = y
        cy = self._header(canvas, x, cy, w, data)
        cy = self._cost(canvas, x, cy, w, data)
        cy = self._tokens_row(canvas, x, cy, w, data, 'today', 'Today')
        cy = self._tokens_row(canvas, x, cy, w, data, 'total', 'Total')
        cy = self._chart(canvas, x, cy, w, data)
        cy = self._recent(canvas, x, cy, w, data)
        return cy - y

    def _rrect(self, cv, x1, y1, x2, y2, r, **kw):
        rrect(cv, x1, y1, x2, y2, r, **kw)

    def _pill(self, cv, x1, y1, x2, y2, **kw):
        pill(cv, x1, y1, x2, y2, **kw)

    def _header(self, cv, x, y, w, data):
        c = self.theme
        expire = data.get('expireTime', '--')
        days = int(data.get('remainingDays', 0) or 0)
        dc = c['green'] if days > 14 else c['yellow'] if days > 7 else c['red']
        dc_glow = c['green_glow'] if days > 14 else c['yellow_glow'] if days > 7 else c['red_glow']

        self._rrect(cv, x, y, x+w, y+36, 8, fill=c['card'])

        # status dot
        cv.create_oval(x+14, y+14, x+22, y+22, fill=dc, outline='')

        cv.create_text(x+30, y+18, text=expire, fill=c['text'], font=(self._f, 9), anchor='w')

        # days pill
        dt = f"{days}d"
        dpw = len(dt) * 8 + 14
        dpx = x + w - 10 - dpw
        self._pill(cv, dpx, y+10, dpx+dpw, y+26, fill=dc_glow)
        cv.create_text(dpx + dpw//2, y+18, text=dt, fill=dc, font=(self._fm, 9, 'bold'))

        return y + 42

    def _cost(self, cv, x, y, w, data):
        c = self.theme
        today = data.get('today', {})
        cost = today.get('creditUsedFormatted', '$0.00')
        count = data.get('requestCount', 0)

        hw = w // 2
        gap = 6

        # left card — Today Cost
        lw = hw - gap // 2
        self._rrect(cv, x, y, x+lw, y+56, 8, fill=c['card'])
        cv.create_text(x+lw//2, y+16, text="Today Cost", fill=c['dim'], font=(self._f, 7))
        cv.create_text(x+lw//2, y+38, text=cost, fill=c['accent'], font=(self._fm, 15, 'bold'))

        # right card — Requests
        rx = x + hw + gap // 2
        rw = w - hw - gap // 2
        self._rrect(cv, rx, y, rx+rw, y+56, 8, fill=c['card'])
        cv.create_text(rx+rw//2, y+16, text="Requests", fill=c['dim'], font=(self._f, 7))
        cv.create_text(rx+rw//2, y+38, text=str(count), fill=c['accent2'], font=(self._fm, 15, 'bold'))

        return y + 62

    def _tokens_row(self, cv, x, y, w, data, key, label):
        c = self.theme
        section = data.get(key, {})

        cv.create_text(x+4, y+6, text=label, fill=c['dim'], font=(self._f, 7), anchor='w')
        if key == 'total':
            cv.create_text(x+w-4, y+6, text=section.get('totalTokensFormatted', '0'),
                          fill=c['lavender'], font=(self._fm, 7, 'bold'), anchor='e')
        y += 18

        gap = 6
        cw = (w - gap * 2) // 3

        items = [
            ("In", section.get('inputTokensFormatted', '0'), c['green']),
            ("Out", section.get('outputTokensFormatted', '0'), c['peach']),
            ("Cache", section.get('cacheReadTokensFormatted', '0'), c['accent']),
        ]
        for i, (lbl, val, color) in enumerate(items):
            bx = x + i * (cw + gap)
            self._rrect(cv, bx, y, bx+cw, y+44, 8, fill=c['card'])
            cv.create_text(bx+cw//2, y+14, text=lbl, fill=c['dim'], font=(self._f, 7))
            cv.create_text(bx+cw//2, y+32, text=val, fill=color, font=(self._fm, 11, 'bold'))
        return y + 50

    def _chart(self, cv, x, y, w, data):
        c = self.theme
        details = data.get('details', [])

        cv.create_text(x+4, y+6, text="Hourly", fill=c['dim'], font=(self._f, 7), anchor='w')
        y += 18
        h = 108

        hourly = {}
        for req in details:
            ts = req.get('time', '')
            if not ts: continue
            parts = ts.split(' ')
            if len(parts) >= 2:
                hr = parts[1].split(':')[0]
                if hr not in hourly:
                    hourly[hr] = {'i': 0, 'o': 0, 'cc': 0, 'cr': 0}
                hourly[hr]['i'] += req.get('inputTokens', 0)
                hourly[hr]['o'] += req.get('outputTokens', 0)
                hourly[hr]['cc'] += req.get('cacheCreationTokens', 0)
                hourly[hr]['cr'] += req.get('cacheReadTokens', 0)

        self._rrect(cv, x, y, x+w, y+h, 8, fill=c['card'])

        if not hourly:
            cv.create_text(x+w//2, y+h//2, text="No data", fill=c['dim'], font=(self._fm, 8))
            return y + h + 6

        hours = sorted(hourly.keys())
        cx = x + 30; cy = y + 10; cw = w - 40; ch = h - 30

        mx = max((hourly[hr]['i']+hourly[hr]['o']+hourly[hr]['cc']+hourly[hr]['cr']) for hr in hours) or 1

        # grid lines
        for i in range(3):
            gy = cy + ch - (i * ch // 2)
            cv.create_line(cx, gy, cx+cw, gy, fill=c['grid'], dash=(2, 3))
            cv.create_text(cx-4, gy, text=self._fnum(int(mx*i/2)), fill=c['dim'], font=(self._fm, 6), anchor='e')

        colors = {'i': c['green'], 'o': c['peach'], 'cc': c['pink'], 'cr': c['accent']}
        bn = len(hours)
        bw = max(8, (cw - 8) // bn - 2)
        gap = (cw - bw * bn) // (bn + 1)

        for i, hr in enumerate(hours):
            d = hourly[hr]
            bx = cx + gap + i * (bw + gap)
            by = cy + ch
            cur = by
            for k in ['cr', 'cc', 'o', 'i']:
                v = d[k]
                if v > 0:
                    sh = max(1, int((v / mx) * ch))
                    # rounded top for the topmost segment
                    cv.create_rectangle(bx, cur - sh, bx + bw, cur, fill=colors[k], outline='')
                    cur -= sh
            cv.create_text(bx + bw // 2, cy + ch + 9, text=hr, fill=c['dim'], font=(self._fm, 6))

        # legend
        ly = y + 7
        lx = x + w - 10
        for lbl, k in [('CR', 'cr'), ('CW', 'cc'), ('Out', 'o'), ('In', 'i')]:
            cv.create_rectangle(lx - 5, ly, lx, ly + 5, fill=colors[k], outline='')
            cv.create_text(lx - 8, ly + 2, text=lbl, fill=c['dim'], font=(self._fm, 6), anchor='e')
            lx -= 32

        return y + h + 6

    def _fnum(self, n):
        if n >= 1_000_000: return f"{n/1_000_000:.1f}M"
        if n >= 1_000: return f"{n/1_000:.1f}K"
        return str(n)

    def _recent(self, cv, x, y, w, data):
        c = self.theme
        details = data.get('details', [])[:5]

        cv.create_text(x+4, y+6, text="Recent", fill=c['dim'], font=(self._f, 7), anchor='w')
        y += 18

        if not details:
            cv.create_text(x+w//2, y+14, text="No data", fill=c['dim'], font=(self._fm, 8))
            return y + 30

        rh = 24
        total_h = len(details) * rh + 4
        self._rrect(cv, x, y, x+w, y+total_h, 8, fill=c['card'])

        for i, req in enumerate(details):
            ry = y + i * rh + 4

            # alternating stripe
            if i % 2 == 1:
                cv.create_rectangle(x + 4, ry, x + w - 4, ry + rh - 2, fill=c['card2'], outline='')

            ts = req.get('time', '')[-8:]
            model = req.get('model', '')
            if 'opus' in model.lower():
                ms, mc = 'Opus', c['mauve']
            elif 'sonnet' in model.lower():
                ms, mc = 'Sonnet', c['accent']
            else:
                ms, mc = 'Haiku', c['green']

            cost = req.get('creditUsedFormatted', '$0')
            mid_y = ry + rh // 2 - 1

            cv.create_text(x + 12, mid_y, text=ts, fill=c['dim'], font=(self._fm, 7), anchor='w')

            # model pill
            mpw = len(ms) * 6 + 10
            mpx = x + 82
            self._pill(cv, mpx, mid_y - 7, mpx + mpw, mid_y + 7, fill=c['card3'])
            cv.create_text(mpx + mpw // 2, mid_y, text=ms, fill=mc, font=(self._f, 7, 'bold'))

            cv.create_text(x + w - 12, mid_y, text=cost, fill=c['text'], font=(self._fm, 7), anchor='e')

        return y + total_h + 6
