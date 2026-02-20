"""启动器网格视图"""

import uuid
from tkinter import Canvas, Menu, Toplevel, Entry, Frame, Label, StringVar
from .base import BaseView
from ..widgets.draw import rrect, pill


class LauncherView(BaseView):

    def __init__(self, app):
        super().__init__(app)
        launcher_cfg = app.config.get('launcher', {})
        grid = launcher_cfg.get('grid', [4, 7])
        self._cols = grid[0]
        self._rows = grid[1]
        self._current_page = 0
        self._search_active = False
        # 拖拽排序状态
        self._drag_idx = None       # 正在拖拽的动作索引
        self._drag_start_xy = None  # 按下时的坐标
        self._drag_active = False   # 是否已进入拖拽模式
        self._grid_origin = (0, 0)  # 网格左上角坐标
        self._cell_size = (0, 0)    # 单元格尺寸（含间距）

    @property
    def _pages(self):
        return self.app.config.get('launcher', {}).get('pages', [])

    def render(self, canvas: Canvas, w: int, y: int) -> int:
        c = self.theme
        pages = self._pages
        if not pages:
            return self._draw_empty(canvas, w, y)

        if self._current_page >= len(pages):
            self._current_page = len(pages) - 1

        page = pages[self._current_page]
        actions = page.get('actions', [])

        mx = 10
        cw = w - 20

        # search bar
        sb_h = 24
        rrect(canvas, mx, y, mx + cw, y + sb_h, 12,
              fill=c['card'], outline=c['border_subtle'], tags='lnch_search')
        canvas.create_text(mx + 14, y + sb_h // 2, text="🔍",
                           font=('Segoe UI Emoji', 7), fill=c['dim'],
                           anchor='w', tags='lnch_search')
        canvas.create_text(mx + 30, y + sb_h // 2, text="搜索动作...",
                           font=(self._f, 7), fill=c['dim'],
                           anchor='w', tags='lnch_search')
        canvas.create_rectangle(mx, y, mx + cw, y + sb_h,
                                fill='', outline='', tags='lnch_search')
        y += sb_h + 6
        cell_gap = 6
        cell_w = (cw - (self._cols - 1) * cell_gap) // self._cols
        cell_h = 52

        # 记录网格布局信息（供拖拽使用）
        self._grid_origin = (mx, y + 20)  # 网格起始 y 在 page title 之后
        self._cell_size = (cell_w + cell_gap, cell_h + cell_gap)

        # page title
        page_name = page.get('name', f'第 {self._current_page + 1} 页')
        canvas.create_text(mx + 4, y + 4, text=page_name, fill=c['dim'],
                           font=(self._f, 7), anchor='w')
        y += 20

        # grid
        for row in range(self._rows):
            for col in range(self._cols):
                idx = row * self._cols + col
                cx = mx + col * (cell_w + cell_gap)
                cy = y + row * (cell_h + cell_gap)

                # 拖拽时高亮目标位置
                is_drag_source = self._drag_active and idx == self._drag_idx
                is_drag_target = (self._drag_active and idx == getattr(self, '_drag_target', None)
                                  and idx != self._drag_idx)

                if idx < len(actions) and actions[idx] is not None:
                    action = actions[idx]
                    if is_drag_source:
                        # 被拖拽的格子半透明效果
                        rrect(canvas, cx, cy, cx + cell_w, cy + cell_h, 8,
                              fill=c['card2'], outline=c['accent'], tags=f'act_{idx}')
                        canvas.create_rectangle(cx, cy, cx + cell_w, cy + cell_h,
                                                fill='', outline='', tags=f'act_{idx}')
                    else:
                        if is_drag_target:
                            rrect(canvas, cx, cy, cx + cell_w, cy + cell_h, 8,
                                  fill=c['accent_glow'], outline=c['accent'])
                        self._draw_cell(canvas, cx, cy, cell_w, cell_h, action, idx)
                else:
                    outline = c['accent'] if is_drag_target else c['border_subtle']
                    fill = c['accent_glow'] if is_drag_target else c['card']
                    rrect(canvas, cx, cy, cx + cell_w, cy + cell_h, 8,
                          fill=fill, outline=outline, tags='lnch_grid')
                    canvas.create_rectangle(cx, cy, cx + cell_w, cy + cell_h,
                                            fill='', outline='', tags='lnch_grid')

        grid_h = self._rows * (cell_h + cell_gap) - cell_gap
        y += grid_h + 12

        # page indicator dots
        if len(pages) > 1:
            y = self._draw_page_dots(canvas, w, y, len(pages))

        # toast
        if self.app._copy_toast_visible:
            msg = getattr(self.app, '_toast_text', '完成!')
            tw = max(70, len(msg) * 8 + 20)
            tx = (w - tw) // 2
            pill(canvas, tx, y+2, tx+tw, y+20, fill=c['green_glow'])
            canvas.create_text(w // 2, y + 11, text=msg, fill=c['green'],
                               font=(self._fm, 7, 'bold'))
            y += 26

        return y

    def _draw_cell(self, canvas, x, y, w, h, action, idx):
        c = self.theme
        tag = f'act_{idx}'

        # cell background
        rrect(canvas, x, y, x + w, y + h, 8, fill=c['btn_bg'], tags=tag)

        # icon (emoji)
        icon = action.get('icon', '\u2726')  # ✦ default
        canvas.create_text(x + w // 2, y + h // 2 - 6, text=icon,
                           font=('Segoe UI Emoji', 14), fill=c['text'], tags=tag)

        # label
        label = action.get('label', '')
        if label:
            # CJK chars are ~2x width, so calculate visual length
            vlen = sum(2 if ord(ch) > 0x2e80 else 1 for ch in label)
            if vlen > 10:
                # truncate to ~10 visual units
                short, vl = '', 0
                for ch in label:
                    cw_ = 2 if ord(ch) > 0x2e80 else 1
                    if vl + cw_ > 8:
                        short += '..'
                        break
                    short += ch
                    vl += cw_
            else:
                short = label
            canvas.create_text(x + w // 2, y + h - 8, text=short,
                               fill=c['dim'], font=(self._f, 6), tags=tag)

        # invisible click area
        canvas.create_rectangle(x, y, x + w, y + h, fill='', outline='', tags=tag)

    def _draw_page_dots(self, canvas, w, y, total):
        c = self.theme
        dot_r = 3
        dot_gap = 10
        total_w = total * (dot_r * 2 + dot_gap) - dot_gap
        sx = (w - total_w) // 2

        for i in range(total):
            dx = sx + i * (dot_r * 2 + dot_gap)
            if i == self._current_page:
                canvas.create_oval(dx, y, dx + dot_r * 2, y + dot_r * 2,
                                   fill=c['accent'], outline='')
            else:
                canvas.create_oval(dx, y, dx + dot_r * 2, y + dot_r * 2,
                                   fill=c['dim'], outline='')
        return y + dot_r * 2 + 8

    def _draw_empty(self, canvas, w, y):
        c = self.theme
        mx = 10
        cw = w - 20

        rrect(canvas, mx, y, mx + cw, y + 80, 10, fill=c['card'])
        canvas.create_text(mx + cw // 2, y + 30, text="\u229E",
                           fill=c['dim'], font=(self._f, 18))
        canvas.create_text(mx + cw // 2, y + 55, text="右键添加操作",
                           fill=c['dim'], font=(self._f, 8))

        # add button
        y += 90
        rrect(canvas, mx, y, mx + cw, y + 36, 10, fill='', outline=c['border_subtle'])
        canvas.create_text(mx + cw // 2, y + 18, text="+  添加操作",
                           fill=c['dim'], font=(self._f, 8), tags='lnch_add')
        canvas.create_rectangle(mx, y, mx + cw, y + 36, fill='', outline='', tags='lnch_add')
        y += 44

        return y

    def on_click(self, canvas: Canvas, event, tags: list[str]) -> bool:
        for tag in tags:
            if tag.startswith('act_'):
                idx = int(tag[4:])
                # 记录按下位置，可能开始拖拽
                self._drag_idx = idx
                self._drag_start_xy = (event.x, event.y)
                self._drag_active = False
                self._execute_action(idx)
                return True
            if tag == 'lnch_add':
                self._add_action()
                return True
            if tag == 'lnch_grid':
                return True  # 空格子吞掉点击，不触发拖拽
            if tag == 'lnch_search':
                self._open_search()
                return True
        return False

    def on_drag(self, canvas: Canvas, event) -> bool:
        """拖拽中 — 检测是否进入拖拽模式并更新目标"""
        if self._drag_idx is None or self._drag_start_xy is None:
            return False

        dx = abs(event.x - self._drag_start_xy[0])
        dy = abs(event.y - self._drag_start_xy[1])

        # 移动超过 10px 才进入拖拽模式
        if not self._drag_active and (dx > 10 or dy > 10):
            self._drag_active = True

        if not self._drag_active:
            return False

        # 计算鼠标所在的格子索引
        target = self._pos_to_idx(event.x, event.y)
        if target != getattr(self, '_drag_target', None):
            self._drag_target = target
            self.app._render()
        return True

    def on_drag_end(self, canvas: Canvas, event) -> bool:
        """拖拽结束 — 交换动作位置"""
        if not self._drag_active or self._drag_idx is None:
            self._drag_idx = None
            self._drag_start_xy = None
            self._drag_active = False
            return False

        target = self._pos_to_idx(event.x, event.y)
        source = self._drag_idx

        # 重置状态
        self._drag_idx = None
        self._drag_start_xy = None
        self._drag_active = False
        self._drag_target = None

        if target is not None and target != source:
            self._swap_actions(source, target)

        self.app._render()
        return True

    def _pos_to_idx(self, x: int, y: int) -> int | None:
        """将画布坐标转换为格子索引"""
        gx, gy = self._grid_origin
        cw, ch = self._cell_size
        if cw <= 0 or ch <= 0:
            return None
        col = int((x - gx) / cw)
        row = int((y - gy) / ch)
        if 0 <= col < self._cols and 0 <= row < self._rows:
            return row * self._cols + col
        return None

    def _swap_actions(self, src: int, dst: int):
        """交换两个动作的位置"""
        pages = self._pages
        if self._current_page >= len(pages):
            return
        actions = pages[self._current_page].get('actions', [])
        # 确保列表足够长
        max_idx = max(src, dst)
        while len(actions) <= max_idx:
            actions.append(None)
        actions[src], actions[dst] = actions[dst], actions[src]
        # 清理尾部 None
        while actions and actions[-1] is None:
            actions.pop()
        self.app._save_config()

    def on_right_click(self, canvas: Canvas, event, tags: list[str]):
        """右键菜单：编辑/删除操作"""
        action_idx = None
        for tag in tags:
            if tag.startswith('act_'):
                action_idx = int(tag[4:])
                break

        menu = Menu(self.app.root, tearoff=0,
                    bg=self.theme['card'], fg=self.theme['text'],
                    activebackground=self.theme['accent'],
                    activeforeground='#fff',
                    font=(self._f, 9))

        if action_idx is not None:
            menu.add_command(label="编辑", command=lambda: self._edit_action(action_idx))
            menu.add_command(label="删除", command=lambda: self._delete_action(action_idx))
            menu.add_separator()

        menu.add_command(label="添加操作", command=self._add_action)
        menu.add_separator()
        menu.add_command(label="添加页面", command=self._add_page)
        if len(self._pages) > 1:
            menu.add_command(label="删除页面", command=self._delete_page)

        menu.tk_popup(event.x_root, event.y_root)

    def on_scroll(self, event):
        """鼠标滚轮切换分页"""
        pages = self._pages
        if len(pages) <= 1:
            return
        if event.delta > 0:
            self._current_page = max(0, self._current_page - 1)
        else:
            self._current_page = min(len(pages) - 1, self._current_page + 1)
        self.app._render()

    def _execute_action(self, idx):
        pages = self._pages
        if self._current_page >= len(pages):
            return
        actions = pages[self._current_page].get('actions', [])
        if idx < len(actions) and actions[idx] is not None:
            self.app.executor.execute(actions[idx])

    def _add_action(self):
        from ..dialogs.action_dialog import ActionDialog
        result = ActionDialog(self.app.root, self.theme,
                              executor=self.app.executor).show()
        if result:
            result['id'] = str(uuid.uuid4())[:8]
            self._ensure_page()
            pages = self._pages
            page = pages[self._current_page]
            actions = page.setdefault('actions', [])
            # find first empty slot or append
            placed = False
            for i in range(len(actions)):
                if actions[i] is None:
                    actions[i] = result
                    placed = True
                    break
            if not placed:
                actions.append(result)
            self.app._save_config()
            self._refresh_hotkeys()
            self.app._render()

    def _edit_action(self, idx):
        pages = self._pages
        if self._current_page >= len(pages):
            return
        actions = pages[self._current_page].get('actions', [])
        if idx >= len(actions) or actions[idx] is None:
            return
        from ..dialogs.action_dialog import ActionDialog
        result = ActionDialog(self.app.root, self.theme, action=actions[idx],
                              executor=self.app.executor).show()
        if result:
            result['id'] = actions[idx].get('id', str(uuid.uuid4())[:8])
            actions[idx] = result
            self.app._save_config()
            self._refresh_hotkeys()
            self.app._render()

    def _delete_action(self, idx):
        pages = self._pages
        if self._current_page >= len(pages):
            return
        actions = pages[self._current_page].get('actions', [])
        if idx < len(actions):
            actions[idx] = None
            # trim trailing Nones
            while actions and actions[-1] is None:
                actions.pop()
            self.app._save_config()
            self.app._render()

    def _add_page(self):
        pages = self.app.config.setdefault('launcher', {}).setdefault('pages', [])
        pages.append({'name': f'第 {len(pages) + 1} 页', 'actions': []})
        self._current_page = len(pages) - 1
        self.app._save_config()
        self.app._render()

    def _delete_page(self):
        pages = self._pages
        if len(pages) <= 1:
            return
        pages.pop(self._current_page)
        if self._current_page >= len(pages):
            self._current_page = len(pages) - 1
        self.app._save_config()
        self.app._render()

    def _ensure_page(self):
        """确保至少有一个页面"""
        launcher = self.app.config.setdefault('launcher', {})
        pages = launcher.setdefault('pages', [])
        if not pages:
            pages.append({'name': '工具', 'actions': []})
            self._current_page = 0

    def _refresh_hotkeys(self):
        """动作变更后刷新全局快捷键注册"""
        if hasattr(self.app, '_register_action_hotkeys'):
            self.app._register_action_hotkeys()

    # ── 搜索 ──

    def _get_all_actions(self) -> list[dict]:
        """收集所有页面的动作（带页面索引）"""
        results = []
        for pi, page in enumerate(self._pages):
            for ai, action in enumerate(page.get('actions', [])):
                if action is not None:
                    results.append({**action, '_page': pi, '_idx': ai})
        return results

    def _fuzzy_match(self, query: str, text: str) -> bool:
        """简单模糊匹配：query 的每个字符按顺序出现在 text 中"""
        query = query.lower()
        text = text.lower()
        qi = 0
        for ch in text:
            if qi < len(query) and ch == query[qi]:
                qi += 1
        return qi == len(query)

    def _open_search(self):
        """打开搜索浮窗"""
        if self._search_active:
            return
        self._search_active = True
        c = self.theme
        root = self.app.root

        dlg = Toplevel(root)
        dlg.overrideredirect(True)
        dlg.attributes('-topmost', True)
        dlg.configure(bg=c['border'])

        inner = Frame(dlg, bg=c['bg'])
        inner.pack(fill='both', expand=True, padx=1, pady=1)

        # 搜索输入框
        search_var = StringVar()
        entry = Entry(inner, bg=c['card'], fg=c['text'],
                      insertbackground=c['accent'], relief='flat',
                      font=(self._f, 10), bd=0, highlightthickness=1,
                      highlightbackground=c['border_subtle'],
                      highlightcolor=c['accent'],
                      textvariable=search_var)
        entry.pack(fill='x', padx=8, pady=(8, 4), ipady=6)

        # 结果列表
        results_frame = Frame(inner, bg=c['bg'])
        results_frame.pack(fill='both', expand=True, padx=8, pady=(0, 8))

        result_labels = []
        selected_idx = [0]
        matched_actions = []

        def update_results(*_):
            query = search_var.get().strip()
            # 清除旧结果
            for lbl in result_labels:
                lbl.destroy()
            result_labels.clear()
            matched_actions.clear()
            selected_idx[0] = 0

            if not query:
                dlg.geometry(f'300x50')
                return

            all_actions = self._get_all_actions()
            for act in all_actions:
                label = act.get('label', '')
                if self._fuzzy_match(query, label):
                    matched_actions.append(act)
                if len(matched_actions) >= 8:
                    break

            for i, act in enumerate(matched_actions):
                icon = act.get('icon', '✦')
                label = act.get('label', '')
                atype = act.get('type', '')
                lbl = Label(results_frame, text=f"  {icon}  {label}",
                            fg=c['text'], bg=c['card'] if i != 0 else c['accent_glow'],
                            font=(self._f, 9), anchor='w', padx=8, pady=4,
                            cursor='hand2')
                lbl.pack(fill='x', pady=1)
                lbl.bind('<Button-1>', lambda e, idx=i: execute_result(idx))
                lbl.bind('<Enter>', lambda e, idx=i: highlight_result(idx))
                result_labels.append(lbl)

            h = 50 + len(matched_actions) * 30
            dlg.geometry(f'300x{h}')

        def highlight_result(idx):
            selected_idx[0] = idx
            for i, lbl in enumerate(result_labels):
                if i == idx:
                    lbl.configure(bg=c['accent_glow'])
                else:
                    lbl.configure(bg=c['card'])

        def execute_result(idx=None):
            if idx is None:
                idx = selected_idx[0]
            if 0 <= idx < len(matched_actions):
                act = matched_actions[idx]
                close()
                self.app.executor.execute(act)

        def on_key(event):
            if event.keysym == 'Down':
                new_idx = min(selected_idx[0] + 1, len(matched_actions) - 1)
                highlight_result(new_idx)
                return 'break'
            elif event.keysym == 'Up':
                new_idx = max(selected_idx[0] - 1, 0)
                highlight_result(new_idx)
                return 'break'
            elif event.keysym == 'Return':
                execute_result()
                return 'break'

        def close(event=None):
            self._search_active = False
            dlg.destroy()

        search_var.trace_add('write', update_results)
        entry.bind('<KeyPress>', on_key)
        dlg.bind('<Escape>', close)
        dlg.bind('<FocusOut>', lambda e: dlg.after(200, close))

        # 定位到面板上方居中
        dw = 300
        dlg.geometry(f'{dw}x50')
        dlg.update_idletasks()
        px = root.winfo_rootx() + (root.winfo_width() - dw) // 2
        py = root.winfo_rooty() + 42
        dlg.geometry(f"+{px}+{py}")
        entry.focus_set()
