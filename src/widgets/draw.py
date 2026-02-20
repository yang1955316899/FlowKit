"""共享绘图工具"""

import math


def rr_points(x1, y1, x2, y2, r):
    """Generate polygon points for a rounded rectangle using arc sampling."""
    r = min(r, (x2 - x1) // 2, (y2 - y1) // 2)
    if r < 1:
        return [x1, y1, x2, y1, x2, y2, x1, y2]
    n = 8
    pts = []
    for i in range(n + 1):
        a = math.pi / 2 + (math.pi / 2) * i / n
        pts += [x1 + r + int(r * math.cos(a)), y1 + r - int(r * math.sin(a))]
    for i in range(n + 1):
        a = (math.pi / 2) * (1 - i / n)
        pts += [x2 - r + int(r * math.cos(a)), y1 + r - int(r * math.sin(a))]
    for i in range(n + 1):
        a = -(math.pi / 2) * i / n
        pts += [x2 - r + int(r * math.cos(a)), y2 - r - int(r * math.sin(a))]
    for i in range(n + 1):
        a = math.pi + (math.pi / 2) * (1 - i / n)
        pts += [x1 + r + int(r * math.cos(a)), y2 - r - int(r * math.sin(a))]
    return pts


def rrect(cv, x1, y1, x2, y2, r, **kw):
    """Draw a polygon-based rounded rectangle on canvas."""
    pts = rr_points(x1, y1, x2, y2, r)
    cv.create_polygon(pts,
                      fill=kw.get('fill', ''),
                      outline=kw.get('outline', ''),
                      width=kw.get('width', 0),
                      tags=kw.get('tags', ''))


def pill(cv, x1, y1, x2, y2, **kw):
    """Draw a fully rounded pill shape on canvas."""
    r = (y2 - y1) // 2
    rrect(cv, x1, y1, x2, y2, r, **kw)
