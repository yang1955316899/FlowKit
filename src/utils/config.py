"""配置管理和验证"""

import yaml
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Optional
from .logger import get_logger

logger = get_logger('config')


@dataclass
class WindowConfig:
    """窗口配置"""
    width: int = 360
    height: int = 600
    theme: str = 'dark'
    edge_threshold: int = 8
    hidden_visible: int = 4
    show_trigger: int = 8
    animation_speed: int = 8
    animation_step: int = 40


@dataclass
class TokenConfig:
    """Token 配置"""
    name: str
    credential: str
    daily_limit: int = 0
    _cached_expire: str = ''
    _cached_days: int = 0


@dataclass
class APIConfig:
    """API 配置"""
    base_url: str = ''
    tokens: list[TokenConfig] = field(default_factory=list)
    verify_ssl: bool = True  # 新增：SSL 验证开关


@dataclass
class LauncherConfig:
    """启动器配置"""
    default_view: str = 'launcher'
    current_page: int = 0
    hotkey: str = 'ctrl+space'
    middle_click: bool = True
    selection_popup: bool = False
    pages: list[dict] = field(default_factory=list)


@dataclass
class WebConfig:
    """Web UI 配置"""
    enabled: bool = True
    port: int = 18900
    allowed_origins: list[str] = field(default_factory=list)


@dataclass
class AppConfig:
    """应用配置"""
    window: WindowConfig = field(default_factory=WindowConfig)
    api: APIConfig = field(default_factory=APIConfig)
    launcher: LauncherConfig = field(default_factory=LauncherConfig)
    web: WebConfig = field(default_factory=WebConfig)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_path: str):
        self.config_path = Path(config_path)
        self._config: Optional[AppConfig] = None

    def load(self) -> AppConfig:
        """加载配置文件

        Returns:
            AppConfig 实例
        """
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            self._config = self._default_config()
            self.save()
            return self._config

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                raw = yaml.safe_load(f) or {}

            self._config = self._parse_config(raw)
            logger.info(f"Config loaded from {self.config_path}")
            return self._config

        except yaml.YAMLError as e:
            logger.error(f"Failed to parse config: {e}")
            self._config = self._default_config()
            return self._config
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = self._default_config()
            return self._config

    def save(self) -> bool:
        """保存配置到文件

        Returns:
            成功返回 True
        """
        if not self._config:
            logger.error("No config to save")
            return False

        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # 转换为字典
            data = self._to_dict(self._config)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True,
                         default_flow_style=False, sort_keys=False)

            logger.info(f"Config saved to {self.config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def get(self) -> AppConfig:
        """获取当前配置"""
        if not self._config:
            return self.load()
        return self._config

    def update(self, **kwargs) -> bool:
        """更新配置

        Args:
            **kwargs: 要更新的配置字段

        Returns:
            成功返回 True
        """
        if not self._config:
            self.load()

        try:
            for key, value in kwargs.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)
                else:
                    logger.warning(f"Unknown config key: {key}")

            return self.save()
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return False

    def _default_config(self) -> AppConfig:
        """返回默认配置"""
        return AppConfig()

    def _parse_config(self, raw: dict) -> AppConfig:
        """解析原始配置字典

        Args:
            raw: 从 YAML 加载的原始字典

        Returns:
            AppConfig 实例
        """
        # 解析 window
        window_raw = raw.get('window', {})
        window = WindowConfig(
            width=window_raw.get('width', 360),
            height=window_raw.get('height', 600),
            theme=window_raw.get('theme', 'dark'),
            edge_threshold=window_raw.get('edge_threshold', 8),
            hidden_visible=window_raw.get('hidden_visible', 4),
            show_trigger=window_raw.get('show_trigger', 8),
            animation_speed=window_raw.get('animation_speed', 8),
            animation_step=window_raw.get('animation_step', 40),
        )

        # 解析 api
        api_raw = raw.get('api', {})
        tokens = []
        for t in api_raw.get('tokens', []):
            if isinstance(t, dict):
                tokens.append(TokenConfig(
                    name=t.get('name', ''),
                    credential=t.get('credential', ''),
                    daily_limit=t.get('daily_limit', 0),
                    _cached_expire=t.get('_cached_expire', ''),
                    _cached_days=t.get('_cached_days', 0),
                ))

        # 兼容旧的 credential 字段
        if not tokens and api_raw.get('credential'):
            tokens.append(TokenConfig(
                name='默认',
                credential=api_raw['credential']
            ))

        api = APIConfig(
            base_url=api_raw.get('base_url', ''),
            tokens=tokens,
            verify_ssl=api_raw.get('verify_ssl', True),
        )

        # 解析 launcher
        launcher_raw = raw.get('launcher', {})
        launcher = LauncherConfig(
            default_view=launcher_raw.get('default_view', 'launcher'),
            current_page=launcher_raw.get('current_page', 0),
            hotkey=launcher_raw.get('hotkey', 'ctrl+space'),
            middle_click=launcher_raw.get('middle_click', True),
            selection_popup=launcher_raw.get('selection_popup', False),
            pages=launcher_raw.get('pages', []),
        )

        # 解析 web
        web_raw = raw.get('web', {})
        web = WebConfig(
            enabled=web_raw.get('enabled', True),
            port=web_raw.get('port', 18900),
            allowed_origins=web_raw.get('allowed_origins', []),
        )

        return AppConfig(
            window=window,
            api=api,
            launcher=launcher,
            web=web,
        )

    def _to_dict(self, config: AppConfig) -> dict:
        """将配置转换为字典

        Args:
            config: AppConfig 实例

        Returns:
            配置字典
        """
        result = {}

        # window
        result['window'] = asdict(config.window)

        # api
        api_dict = {
            'base_url': config.api.base_url,
            'verify_ssl': config.api.verify_ssl,
            'tokens': [asdict(t) for t in config.api.tokens],
        }
        result['api'] = api_dict

        # launcher
        result['launcher'] = asdict(config.launcher)

        # web
        result['web'] = asdict(config.web)

        return result
