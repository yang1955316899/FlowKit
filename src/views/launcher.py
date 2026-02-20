"""启动器网格视图"""

import uuid
from tkinter import Canvas, Menu
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
        cell_gap = 6
        cell_w = (cw - (self._cols - 1) * cell_gap) // self._cols
        cell_h = 52

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

                if idx < len(actions) and actions[idx] is not None:
                    action = actions[idx]
                    self._draw_cell(canvas, cx, cy, cell_w, cell_h, action, idx)
                else:
                    # empty slot — tagged to prevent click-through to drag
                    rrect(canvas, cx, cy, cx + cell_w, cy + cell_h, 8,
                          fill=c['card'], outline=c['border_subtle'], tags='lnch_grid')
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
                self._execute_action(idx)
                return True
            if tag == 'lnch_add':
                self._add_action()
                return True
            if tag == 'lnch_grid':
                return True  # 空格子吞掉点击，不触发拖拽
        return False

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
        result = ActionDialog(self.app.root, self.theme).show()
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
            self.app._render()

    def _edit_action(self, idx):
        pages = self._pages
        if self._current_page >= len(pages):
            return
        actions = pages[self._current_page].get('actions', [])
        if idx >= len(actions) or actions[idx] is None:
            return
        from ..dialogs.action_dialog import ActionDialog
        result = ActionDialog(self.app.root, self.theme, action=actions[idx]).show()
        if result:
            result['id'] = actions[idx].get('id', str(uuid.uuid4())[:8])
            actions[idx] = result
            self.app._save_config()
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
