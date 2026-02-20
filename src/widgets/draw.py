"""共享绘图工具 — 用四角圆弧+矩形拼合，避免多边形撕裂"""


def rrect(cv, x1, y1, x2, y2, r, **kw):
    """用 oval 四角 + rectangle 中间拼出圆角矩形，无撕裂。"""
    fill = kw.get('fill', '')
    outline = kw.get('outline', '')
    tags = kw.get('tags', '')
    ow = kw.get('width', 0)

    w = x2 - x1
    h = y2 - y1
    r = min(r, w // 2, h // 2)

    if r < 1:
        cv.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline,
                            width=ow, tags=tags)
        return

    d = r * 2

    # 四个角的圆弧（用 arc）
    # top-left
    cv.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90,
                  fill=fill, outline='', style='pieslice', tags=tags)
    # top-right
    cv.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90,
                  fill=fill, outline='', style='pieslice', tags=tags)
    # bottom-right
    cv.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90,
                  fill=fill, outline='', style='pieslice', tags=tags)
    # bottom-left
    cv.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90,
                  fill=fill, outline='', style='pieslice', tags=tags)

    # 三个矩形填充中间区域
    # 水平中间带（全宽，去掉上下圆角高度）
    cv.create_rectangle(x1, y1 + r, x2, y2 - r,
                        fill=fill, outline='', tags=tags)
    # 上方中间带（去掉左右圆角宽度）
    cv.create_rectangle(x1 + r, y1, x2 - r, y1 + r,
                        fill=fill, outline='', tags=tags)
    # 下方中间带
    cv.create_rectangle(x1 + r, y2 - r, x2 - r, y2,
                        fill=fill, outline='', tags=tags)

    # 描边（如果有）
    if outline and ow:
        # 用 arc 画四角描边
        cv.create_arc(x1, y1, x1 + d, y1 + d, start=90, extent=90,
                      style='arc', outline=outline, width=ow, tags=tags)
        cv.create_arc(x2 - d, y1, x2, y1 + d, start=0, extent=90,
                      style='arc', outline=outline, width=ow, tags=tags)
        cv.create_arc(x2 - d, y2 - d, x2, y2, start=270, extent=90,
                      style='arc', outline=outline, width=ow, tags=tags)
        cv.create_arc(x1, y2 - d, x1 + d, y2, start=180, extent=90,
                      style='arc', outline=outline, width=ow, tags=tags)
        # 四条直线边
        cv.create_line(x1 + r, y1, x2 - r, y1,
                       fill=outline, width=ow, tags=tags)
        cv.create_line(x1 + r, y2, x2 - r, y2,
                       fill=outline, width=ow, tags=tags)
        cv.create_line(x1, y1 + r, x1, y2 - r,
                       fill=outline, width=ow, tags=tags)
        cv.create_line(x2, y1 + r, x2, y2 - r,
                       fill=outline, width=ow, tags=tags)


def pill(cv, x1, y1, x2, y2, **kw):
    """Draw a fully rounded pill shape on canvas."""
    r = (y2 - y1) // 2
    rrect(cv, x1, y1, x2, y2, r, **kw)


def rr_points(x1, y1, x2, y2, r):
    """保留兼容：生成圆角矩形多边形点（仅 token_dialog 按钮用）。"""
    import math
    w = x2 - x1
    h = y2 - y1
    r = min(r, w // 2, h // 2)
    if r < 1:
        return [x1, y1, x2, y1, x2, y2, x1, y2]
    n = 8
    pts = []
    corners = [
        (x1 + r, y1 + r, math.pi / 2, math.pi / 2),
        (x2 - r, y1 + r, 0, math.pi / 2),
        (x2 - r, y2 - r, -math.pi / 2, math.pi / 2),
        (x1 + r, y2 - r, math.pi, math.pi / 2),
    ]
    for cx, cy, start, sweep in corners:
        for i in range(n + 1):
            a = start + sweep * i / n
            pts.append(round(cx + r * math.cos(a)))
            pts.append(round(cy - r * math.sin(a)))
    return pts
