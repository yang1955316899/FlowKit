"""主应用程序"""

import yaml
import threading
import warnings
from tkinter import Tk, Canvas
from pathlib import Path

from .core.window import WindowManager
from .core.scheduler import Scheduler
from .core.actions import ActionExecutor
from .core.platform_api import PlatformAPIServer
from .core.tray import SystemTray
from .themes.dark import DARK
from .utils.http import HttpClient
from .cards.token_stats import TokenStatsCard
from .dialogs.token_dialog import TokenDialog
from .widgets.draw import rrect, pill
from .views.detail import DetailView
from .views.overview import OverviewView

warnings.filterwarnings('ignore')


class App:

    def __init__(self, config_path: str = None):
        self._config_path = config_path or str(Path(__file__).parent.parent / 'config.yaml')
        self.config = self._load_config(self._config_path)
        self.theme = DARK
        self._f = DARK['font']
        self._fm = DARK['mono']

        api_cfg = self.config.get('api', {})
        self.tokens = api_cfg.get('tokens', [])
        if not self.tokens:
            cred = api_cfg.get('credential', '')
            if cred:
                self.tokens = [{'name': '默认', 'credential': cred}]
        self.current_token_idx = 0

        # launcher config
        launcher_cfg = self.config.get('launcher', {})
        default_view = launcher_cfg.get('default_view', 'launcher')
        self.current_view = default_view
        self._overview_data: dict[int, dict] = {}
        self._delete_confirm_idx: int | None = None

        self.root = Tk()
        self._setup_window()
        self.wm = WindowManager(self.root, self.config.get('window', {}))

        self.http = HttpClient(
            api_cfg.get('base_url', ''),
            self.tokens[0]['credential'] if self.tokens else ''
        )

        self.cards = []
        self._init_cards()
        self.canvas = None

        # action executor
        self.executor = ActionExecutor(root=self.root, theme=self.theme)
        self.executor.set_feedback_callback(self._show_toast)

        # platform API server for script actions
        self._api_server = PlatformAPIServer(
            root=self.root, theme=self.theme, feedback_cb=self._show_toast)
        self._api_server.start()
        self.executor.set_api_server(self._api_server)

        # views
        self._views: dict[str, 'BaseView'] = {}
        self._init_views()

        self._build_ui()

        self.scheduler = Scheduler()
        self._setup_scheduler()

        self._copy_toast = None
        self._copy_toast_visible = False
        self._toast_text = "已复制!"

    # ── views ──

    def _init_views(self):
        from .views.launcher import LauncherView
        from .views.settings import SettingsView
        self._views['launcher'] = LauncherView(self)
        self._views['detail'] = DetailView(self)
        self._views['overview'] = OverviewView(self)
        self._views['settings'] = SettingsView(self)

    # ── config ──

    def _load_config(self, path=None):
        try:
            with open(path or self._config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception:
            return {}

    def _save_config(self):
        self.config.setdefault('api', {})['tokens'] = self.tokens
        try:
            with open(self._config_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, allow_unicode=True,
                         default_flow_style=False, sort_keys=False)
        except Exception:
            pass

    # ── window ──

    def _setup_window(self):
        cfg = self.config.get('window', {})
        w = cfg.get('width', 360)
        self.root.title('监控台')
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', cfg.get('opacity', 0.92))
        self.root.configure(bg=self.theme['bg'])
        self.root.geometry(f"{w}x600")

    def _init_cards(self):
        for cfg in self.config.get('cards', []):
            if cfg.get('type') == 'token_stats':
                self.cards.append(TokenStatsCard(cfg, self.theme, self.http))

    def _build_ui(self):
        c = self.theme
        w = self.config.get('window', {}).get('width', 360)
        self.canvas = Canvas(self.root, bg=c['bg'], highlightthickness=0, width=w, height=600)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<Button-3>', self._on_right_click)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<ButtonRelease-1>', self._on_drag_end)
        self.canvas.bind('<MouseWheel>', self._on_scroll)
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        self.root.bind('<Leave>', lambda e: self._on_leave())
        self.root.update_idletasks()
        self.wm.init_position()

    # ── drawing helpers ──

    def _rrect(self, cv, x1, y1, x2, y2, r, **kw):
        rrect(cv, x1, y1, x2, y2, r, **kw)

    def _pill(self, cv, x1, y1, x2, y2, **kw):
        pill(cv, x1, y1, x2, y2, **kw)

    # ── click ──

    def _on_click(self, event):
        items = self.canvas.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)
        for item in items:
            for tag in self.canvas.gettags(item):
                if tag == 'close':
                    self.root.destroy(); return
                if tag == 'btn_refresh':
                    self._do_refresh(); return
                # nav pills
                if tag == 'nav_launcher':
                    self._switch_view('launcher'); return
                if tag == 'nav_detail':
                    self._switch_view('detail'); return
                if tag == 'nav_overview':
                    self._switch_view('overview'); return
                if tag == 'nav_settings':
                    self._switch_view('settings'); return

        # delegate to current view
        all_tags = []
        for item in items:
            for t in self.canvas.gettags(item):
                if t and t != 'current':
                    all_tags.append(t)
        if all_tags:
            view = self._views.get(self.current_view)
            if view and view.on_click(self.canvas, event, all_tags):
                return

        # 只有点击 header 区域才允许拖拽
        if event.y <= 36:
            self._dragging = True
            self.wm.drag_start(event)

    def _on_drag(self, event):
        # 先让视图处理拖拽
        view = self._views.get(self.current_view)
        if view and view.on_drag(self.canvas, event):
            return
        if getattr(self, '_dragging', False):
            self.wm.drag(event)

    def _on_drag_end(self, event):
        # 先让视图处理拖拽结束
        view = self._views.get(self.current_view)
        if view and view.on_drag_end(self.canvas, event):
            pass
        if getattr(self, '_dragging', False):
            self._dragging = False
            self.wm.drag_end(event)

    def _on_right_click(self, event):
        """右键事件委托给当前视图"""
        view = self._views.get(self.current_view)
        if view and hasattr(view, 'on_right_click'):
            items = self.canvas.find_overlapping(event.x-2, event.y-2, event.x+2, event.y+2)
            all_tags = []
            for item in items:
                all_tags.extend(self.canvas.gettags(item))
            if all_tags:
                view.on_right_click(self.canvas, event, all_tags)

    def _on_scroll(self, event):
        """滚轮事件委托给当前视图"""
        view = self._views.get(self.current_view)
        if view:
            view.on_scroll(event)

    # ── view ──

    def _switch_view(self, name: str):
        if name == self.current_view:
            return
        self.current_view = name
        if name == 'overview':
            self._delete_confirm_idx = None
            self._fetch_overview_data()
        self._render()

    def _switch_to_detail(self, idx):
        self.current_view = 'detail'
        if idx != self.current_token_idx and idx < len(self.tokens):
            self.current_token_idx = idx
            self.http.set_credential(self.tokens[idx]['credential'])
            for card in self.cards: card.update({})
            self._render()
            for card in self.cards:
                threading.Thread(target=lambda c=card: self._fetch_and_update(c), daemon=True).start()
        else:
            self._render()

    def _do_refresh(self):
        if self.current_view == 'overview':
            self._overview_data.clear(); self._render(); self._fetch_overview_data()
        elif self.current_view == 'detail':
            for card in self.cards: card.update({})
            self._render()
            for card in self.cards:
                threading.Thread(target=lambda c=card: self._fetch_and_update(c), daemon=True).start()

    def _switch_token(self, idx):
        if idx == self.current_token_idx or idx >= len(self.tokens): return
        self.current_token_idx = idx
        self.http.set_credential(self.tokens[idx]['credential'])
        for card in self.cards: card.update({})
        self._render()
        for card in self.cards:
            threading.Thread(target=lambda c=card: self._fetch_and_update(c), daemon=True).start()

    def _copy_credential(self):
        self.root.clipboard_clear()
        self.root.clipboard_append(self.tokens[self.current_token_idx]['credential'])
        if self._copy_toast: self.root.after_cancel(self._copy_toast)
        self._copy_toast_visible = True; self._render()
        self._copy_toast = self.root.after(1200, self._hide_copy_toast)

    def _hide_copy_toast(self):
        self._copy_toast_visible = False; self._copy_toast = None; self._render()

    def _show_toast(self, msg: str = "完成!"):
        """通用 toast 反馈"""
        if self._copy_toast: self.root.after_cancel(self._copy_toast)
        self._toast_text = msg
        self._copy_toast_visible = True; self._render()
        self._copy_toast = self.root.after(1200, self._hide_copy_toast)

    # ── overview data ──

    def _fetch_overview_data(self):
        base = self.config.get('api', {}).get('base_url', '')
        def fetch(i, cred):
            d = HttpClient(base, cred).post('/api/stats')
            if d: self._overview_data[i] = d
            self.root.after(0, lambda: self.current_view == 'overview' and self._render())
        for i, t in enumerate(self.tokens):
            threading.Thread(target=fetch, args=(i, t['credential']), daemon=True).start()

    # ── CRUD ──

    def _add_token(self):
        r = TokenDialog(self.root, self.theme).show()
        if r:
            self.tokens.append(r); self._save_config()
            self._fetch_overview_data(); self._render()

    def _edit_token(self, idx):
        if idx >= len(self.tokens): return
        r = TokenDialog(self.root, self.theme, token=self.tokens[idx]).show()
        if r:
            self.tokens[idx] = r; self._save_config()
            if idx == self.current_token_idx: self.http.set_credential(r['credential'])
            self._fetch_overview_data(); self._render()

    def _request_delete(self, idx):
        if len(self.tokens) <= 1: return
        self._delete_confirm_idx = idx; self._render()

    def _confirm_delete(self, idx):
        if idx >= len(self.tokens) or len(self.tokens) <= 1: return
        self._delete_confirm_idx = None
        self._overview_data.pop(idx, None); self.tokens.pop(idx)
        nd = {}
        for k, v in self._overview_data.items(): nd[k if k < idx else k-1] = v
        self._overview_data = nd
        if self.current_token_idx >= len(self.tokens):
            self.current_token_idx = len(self.tokens) - 1
        self.http.set_credential(self.tokens[self.current_token_idx]['credential'])
        self._save_config(); self._render()

    # ── scheduler ──

    def _setup_scheduler(self):
        for card in self.cards:
            self.scheduler.add(lambda c=card: self._fetch_and_update(c), card.refresh_interval)

    def _fetch_and_update(self, card):
        data = card.fetch_data()
        if data: card.update(data); self.root.after(0, self._render)

    # ── render ──

    def _render(self):
        self.canvas.delete('all')
        c = self.theme
        w = self.config.get('window', {}).get('width', 360)
        y = self._draw_header(w)

        view = self._views.get(self.current_view)
        if view:
            y = view.render(self.canvas, w, y)

        self.root.geometry(f"{w}x{y + 10}")

    # ── header ──

    def _draw_header(self, w):
        c = self.theme
        cv = self.canvas
        f, fm = self._f, self._fm

        # header bar
        cv.create_rectangle(0, 0, w, 36, fill=c['card'], outline='')
        cv.create_line(0, 36, w, 36, fill=c['border_subtle'])

        # title with accent dot
        cv.create_oval(12, 14, 18, 20, fill=c['accent'], outline='')
        cv.create_text(24, 17, text="监控台", fill=c['text'],
                      font=(f, 10, 'bold'), anchor='w')

        # right-side buttons
        rx = w - 12

        # close ×
        cv.create_text(rx, 18, text="\u00D7", fill=c['dim'], font=(f, 12), anchor='e', tags='close')
        cv.create_rectangle(rx-14, 4, rx+2, 32, fill='', outline='', tags='close')
        rx -= 26

        # refresh ↻
        cv.create_text(rx, 18, text="\u21BB", fill=c['dim'], font=(f, 11), anchor='e', tags='btn_refresh')
        cv.create_rectangle(rx-14, 4, rx+2, 32, fill='', outline='', tags='btn_refresh')
        rx -= 28

        # nav pills: [⊞] [📊] [ALL]
        nav_items = [
            ('ALL', 'nav_overview', 'overview'),
            ('\u2261', 'nav_detail', 'detail'),     # ≡
            ('\u229E', 'nav_launcher', 'launcher'),  # ⊞
            ('\u2699', 'nav_settings', 'settings'),  # ⚙
        ]
        for label, tag, view_name in nav_items:
            active = self.current_view == view_name
            pw = 30 if len(label) <= 2 else 36
            px = rx - pw
            if active:
                pill(cv, px, 10, rx, 26, fill=c['accent'])
                cv.create_text(px + pw//2, 18, text=label, fill='#fff',
                               font=(fm, 7, 'bold'), tags=tag)
            else:
                pill(cv, px, 10, rx, 26, fill='', outline=c['border'])
                cv.create_text(px + pw//2, 18, text=label, fill=c['dim'],
                               font=(fm, 7), tags=tag)
            cv.create_rectangle(px, 10, rx, 26, fill='', outline='', tags=tag)
            rx -= pw + 4

        return 42

    # ── hotkey integration ──

    def toggle_at_cursor(self):
        """热键/中键回调 — 在光标位置弹出/隐藏面板"""
        if self.wm.is_hidden:
            # 上下文感知：检测前台窗口，自动切换页面
            self._apply_context_page()

            mx, my = self.wm.get_mouse_pos()
            w = self.config.get('window', {}).get('width', 360)
            h = self.root.winfo_height()
            self.wm.show_at_position(mx - w // 2, my - 20)
            self.root.focus_force()
            self.root.lift()
        else:
            self.wm.try_hide()

    def _apply_context_page(self):
        """根据前台窗口进程自动切换到匹配的动作页"""
        try:
            from .core.context import get_foreground_process, find_context_page
            process = get_foreground_process()
            if not process:
                return
            pages = self.config.get('launcher', {}).get('pages', [])
            idx = find_context_page(pages, process)
            if idx is not None:
                # 切换到 launcher 视图并设置页面
                if self.current_view != 'launcher':
                    self.current_view = 'launcher'
                launcher = self._views.get('launcher')
                if launcher and launcher._current_page != idx:
                    launcher._current_page = idx
                    self._render()
        except Exception:
            pass

    # ── util ──

    def _on_leave(self):
        self.root.after(500, self.wm.try_hide)

    def _check_mouse(self):
        self.wm.check_mouse(); self.root.after(100, self._check_mouse)

    def run(self):
        # start hotkey manager
        self._start_hotkey()
        # start system tray
        self._tray = SystemTray(
            on_show=lambda: self.root.after(0, self._tray_show),
            on_settings=lambda: self.root.after(0, self._tray_settings),
            on_exit=lambda: self.root.after(0, self.root.destroy),
        )
        self._tray.start()
        self.scheduler.start(); self._check_mouse(); self.root.mainloop()
        self._stop_hotkey()
        self._tray.stop()
        self._api_server.stop()

    def _tray_show(self):
        """托盘双击 — 显示面板"""
        self.wm.show_at_position(
            self.root.winfo_x(), self.root.winfo_y())
        self.root.focus_force()
        self.root.lift()

    def _tray_settings(self):
        """托盘菜单 — 打开设置"""
        self._tray_show()
        self._switch_view('settings')

    def _start_hotkey(self):
        """启动全局热键和鼠标钩子"""
        from .core.hotkey import InputHookManager
        launcher_cfg = self.config.get('launcher', {})
        self._hotkey_mgr = InputHookManager()
        self._action_hotkey_ids = []  # 动作绑定的热键 ID

        hotkey = launcher_cfg.get('hotkey', 'ctrl+space')
        if hotkey:
            self._hotkey_mgr.register_hotkey(hotkey, lambda: self.root.after(0, self.toggle_at_cursor))

        if launcher_cfg.get('middle_click', True):
            self._hotkey_mgr.register_middle_click(lambda: self.root.after(0, self.toggle_at_cursor))

        # 注册动作级快捷键
        self._register_action_hotkeys()

        self._hotkey_mgr.start()

    def _register_action_hotkeys(self):
        """扫描 config 中带 hotkey 字段的动作并注册全局快捷键"""
        # 先清除旧的动作热键
        for hid in self._action_hotkey_ids:
            self._hotkey_mgr.unregister_hotkey(hid)
        self._action_hotkey_ids.clear()

        pages = self.config.get('launcher', {}).get('pages', [])
        for page in pages:
            for action in page.get('actions', []):
                if action and action.get('hotkey'):
                    hk = action['hotkey']
                    act = action  # 闭包捕获
                    hid = self._hotkey_mgr.register_hotkey(
                        hk, lambda a=act: self.root.after(0, self.executor.execute, a))
                    if hid:
                        self._action_hotkey_ids.append(hid)

    def _stop_hotkey(self):
        """停止热键管理器"""
        if hasattr(self, '_hotkey_mgr'):
            self._hotkey_mgr.stop()
