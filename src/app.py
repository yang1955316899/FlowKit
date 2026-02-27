"""主应用程序"""

import warnings
from pathlib import Path

from .core.scheduler import Scheduler
from .core.actions import ActionExecutor
from .core.platform_api import PlatformAPIServer
from .core.tray import SystemTray
from .core.stats import ActionStats
from .core.selection import SelectionWatcher
from .core.store import ActionStore
from .themes.dark import DARK
from .themes.light import LIGHT
from .utils.http import HttpClient
from .utils.logger import setup_logger, get_logger
from .utils.config import ConfigManager

warnings.filterwarnings('ignore')

# 设置日志
logger = setup_logger('flowkit', log_file='logs/flowkit.log')
app_logger = get_logger('app')


class App:

    def __init__(self, config_path: str = None):
        config_path = config_path or str(Path(__file__).parent.parent / 'config.yaml')

        # 使用新的配置管理器
        self._config_mgr = ConfigManager(config_path)
        self._app_config = self._config_mgr.load()

        # 兼容旧代码：保留 self.config 字典访问
        self.config = self._config_to_dict()

        self.theme = self._resolve_theme()
        self._f = self.theme['font']
        self._fm = self.theme['mono']

        # tokens
        self.tokens = [t.__dict__ for t in self._app_config.api.tokens]
        self.current_token_idx = 0

        # launcher config
        self.current_view = self._app_config.launcher.default_view
        self._overview_data: dict[int, dict] = {}
        self._delete_confirm_idx: int | None = None

        # pywebview window (set later)
        self.window = None

        self.http = HttpClient(
            self._app_config.api.base_url,
            self.tokens[0]['credential'] if self.tokens else '',
            self._app_config.api.verify_ssl
        )

        self.cards = []

        # action executor
        self.executor = ActionExecutor(root=None, theme=self.theme)
        self.executor.set_feedback_callback(self._show_toast)

        # usage stats
        self.stats = ActionStats()
        self.executor.set_stats(self.stats)

        # action store
        self.store = ActionStore()

        # platform API server for script actions
        self._api_server = PlatformAPIServer(
            root=None, theme=self.theme, feedback_cb=self._show_toast)
        self._api_server.start()
        self.executor.set_api_server(self._api_server)

        # web UI server
        self._web_server = None
        if self._app_config.web.enabled:
            from .web.server import WebServer
            self._web_port = self._app_config.web.port
            self._web_server = WebServer(
                self,
                port=self._web_port,
                allowed_origins=self._app_config.web.allowed_origins
            )
            self._web_server.start()

        self.scheduler = Scheduler()

        self._toast_text = "完成!"
        self._is_hidden = True

        app_logger.info("FlowKit initialized")

    # ── config ──

    def _config_to_dict(self) -> dict:
        """将 AppConfig 转换为字典（兼容旧代码）"""
        return self._config_mgr._to_dict(self._app_config)

    def _save_config(self):
        """保存配置"""
        # 更新 tokens
        from .utils.config import TokenConfig
        self._app_config.api.tokens = [
            TokenConfig(**t) if isinstance(t, dict) else t
            for t in self.tokens
        ]

        # 保存
        if self._config_mgr.save():
            # 同步字典版本
            self.config = self._config_to_dict()
            app_logger.info("Config saved")
        else:
            app_logger.error("Failed to save config")

    def _resolve_theme(self):
        """根据 config 中的 theme 字段选择主题"""
        name = self._app_config.window.theme
        return LIGHT if name == 'light' else DARK

    def switch_theme(self, name: str):
        """切换主题"""
        self._app_config.window.theme = name
        self.theme = self._resolve_theme()
        self._f = self.theme['font']
        self._fm = self.theme['mono']
        self.executor._theme = self.theme
        self._save_config()
        app_logger.info(f"Theme switched to {name}")

    # ── toast ──

    def _show_toast(self, msg: str = "完成!"):
        """通用 toast 反馈"""
        self._toast_text = msg
        # 通过日志输出
        print(f"[Toast] {msg}")

    # ── scheduler ──

    def _setup_scheduler(self):
        for card in self.cards:
            self.scheduler.add(lambda c=card: self._fetch_and_update(c), card.refresh_interval)

    def _fetch_and_update(self, card):
        data = card.fetch_data()
        if data:
            card.update(data)

    # ── hotkey integration ──

    def toggle_window(self):
        """热键/中键回调 — 显示/隐藏窗口（Electron 模式下无效）"""
        print("[Hotkey] Toggle window (handled by Electron)")

    def show_window(self):
        """显示窗口（Electron 模式下无效）"""
        print("[Hotkey] Show window (handled by Electron)")

    # ── tray callbacks ──

    def _tray_show(self):
        """托盘双击 — 显示窗口（Electron 处理）"""
        print("[Tray] Show window (handled by Electron)")

    def _tray_settings(self):
        """托盘菜单 — 打开设置（Electron 处理）"""
        print("[Tray] Open settings (handled by Electron)")

    def _tray_webui(self):
        """托盘菜单 — 打开 Web UI（浏览器）"""
        import webbrowser
        port = getattr(self, '_web_port', 18900)
        webbrowser.open(f'http://localhost:{port}')

    # ── run ──

    def run(self):
        """运行应用（仅启动后端服务，不创建窗口）"""
        # start hotkey manager
        self._start_hotkey()

        # start system tray
        self._tray = SystemTray(
            on_show=self._tray_show,
            on_settings=self._tray_settings,
            on_webui=self._tray_webui,
            on_exit=self._exit_app,
        )
        self._tray.start()

        # start selection watcher (optional)
        self._selection_watcher = None
        if self.config.get('launcher', {}).get('selection_popup', False):
            self._start_selection_watcher()

        self.scheduler.start()

        print(f"FlowKit backend started on http://127.0.0.1:{self._web_port}")
        print("Press Ctrl+C to exit")

        # Keep running
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")
            self._cleanup()

    def _cleanup(self):
        """Cleanup resources on exit"""
        app_logger.info("Cleaning up resources...")

        # 定义清理任务列表
        cleanup_tasks = [
            ('hotkey manager', lambda: self._stop_hotkey()),
            ('system tray', lambda: self._tray.stop()),
            ('selection watcher', lambda: self._selection_watcher.stop() if self._selection_watcher else None),
            ('API server', lambda: self._api_server.stop()),
            ('web server', lambda: self._web_server.stop() if self._web_server else None),
        ]

        # 统一执行清理
        for name, cleanup_fn in cleanup_tasks:
            try:
                cleanup_fn()
                app_logger.debug(f"Successfully stopped {name}")
            except Exception as e:
                app_logger.error(f"Error stopping {name}: {e}")

        app_logger.info("Cleanup complete")

    def _exit_app(self):
        """退出应用"""
        import sys
        sys.exit(0)

    def _start_selection_watcher(self):
        """启动文本选中浮窗（pywebview 模式下暂不支持）"""
        pass

    def _start_hotkey(self):
        """启动全局热键和鼠标钩子"""
        from .core.hotkey import InputHookManager
        launcher_cfg = self.config.get('launcher', {})
        self._hotkey_mgr = InputHookManager()
        self._action_hotkey_ids = []

        hotkey = launcher_cfg.get('hotkey', 'ctrl+space')
        if hotkey:
            self._hotkey_mgr.register_hotkey(hotkey, self.toggle_window)

        if launcher_cfg.get('middle_click', True):
            self._hotkey_mgr.register_middle_click(self.toggle_window)

        # 注册动作级快捷键
        self._register_action_hotkeys()

        self._hotkey_mgr.start()

    def _register_action_hotkeys(self):
        """扫描 config 中带 hotkey 字段的动作并注册全局快捷键"""
        for hid in self._action_hotkey_ids:
            self._hotkey_mgr.unregister_hotkey(hid)
        self._action_hotkey_ids.clear()

        pages = self.config.get('launcher', {}).get('pages', [])
        for page in pages:
            for action in page.get('actions', []):
                if action and action.get('hotkey'):
                    hk = action['hotkey']
                    act = action
                    hid = self._hotkey_mgr.register_hotkey(
                        hk, lambda a=act: self.executor.execute(a))
                    if hid:
                        self._action_hotkey_ids.append(hid)

    def _stop_hotkey(self):
        """停止热键管理器"""
        if hasattr(self, '_hotkey_mgr'):
            self._hotkey_mgr.stop()
