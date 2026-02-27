"""配置相关路由"""


class ConfigRoutes:
    """配置管理路由"""

    def __init__(self, handler):
        self.handler = handler
        self.app = handler.app

    def get_config(self):
        """GET /api/v1/config - 获取配置"""
        cfg = self.app.config.copy()
        # 移除敏感信息
        if 'api' in cfg:
            api_cfg = cfg['api'].copy()
            if 'credential' in api_cfg:
                api_cfg['credential'] = api_cfg['credential'][:8] + '...'
            if 'tokens' in api_cfg:
                for token in api_cfg['tokens']:
                    if 'credential' in token:
                        token['credential'] = token['credential'][:8] + '...'
            cfg['api'] = api_cfg

        self.handler._ok(cfg)
        self.handler._log_request('GET', '/config', 200)

    def update_config(self, body: dict):
        """PUT /api/v1/config - 更新配置（支持深度合并）"""
        # 允许更新的顶级字段
        allowed_keys = ['window', 'launcher', 'web']

        for key in allowed_keys:
            if key in body:
                if key not in self.app.config:
                    self.app.config[key] = {}
                # 深度合并而非覆盖
                self.handler._deep_merge(self.app.config[key], body[key])

        self.app._save_config()

        # 如果更新了主题，通知应用切换主题
        if 'window' in body and 'theme' in body['window']:
            theme_name = body['window']['theme']
            if hasattr(self.app, 'switch_theme'):
                self.app.switch_theme(theme_name)

        self.handler._ok()
        self.handler._log_request('PUT', '/config', 200)

    def update_theme(self, body: dict):
        """PUT /api/v1/theme - 切换主题"""
        theme_name = body.get('theme', 'dark')
        if 'launcher' not in self.app.config:
            self.app.config['launcher'] = {}
        self.app.config['launcher']['theme'] = theme_name
        self.app._save_config()
        self.handler._ok({'theme': theme_name})
        self.handler._log_request('PUT', '/theme', 200)
