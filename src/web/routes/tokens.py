"""Token 相关路由"""

from ..utils.logger import get_logger

logger = get_logger('web.routes.tokens')

# 错误码
ERR_NOT_FOUND = 1001
ERR_MISSING_FIELD = 1004
ERR_CANNOT_DELETE = 1005
ERR_UPSTREAM_ERROR = 1009


class TokenRoutes:
    """Token 路由处理器"""

    def __init__(self, handler):
        self.handler = handler
        self.app = handler.app

    def get_tokens(self):
        """GET /tokens - 获取所有 token"""
        tokens = []
        for i, t in enumerate(self.app.tokens):
            tokens.append({
                'index': i,
                'name': t.get('name', ''),
                'daily_limit': t.get('daily_limit', 0),
                'credential': t.get('credential', '')[:8] + '...',
                '_cached_expire': t.get('_cached_expire', ''),
                '_cached_days': t.get('_cached_days', 0),
            })
        self.handler._ok(tokens)
        self.handler._log_request('GET', '/tokens', 200)

    def get_token_stats(self, idx: int):
        """GET /tokens/{idx}/stats - 获取 token 统计"""
        if idx >= len(self.app.tokens):
            self.handler._err('token not found', ERR_NOT_FOUND, 404)
            self.handler._log_request('GET', f'/tokens/{idx}/stats', 404)
            return

        token = self.app.tokens[idx]
        base = self.app.config.get('api', {}).get('base_url', '')
        from ...utils.http import HttpClient
        client = HttpClient(base, token['credential'])

        try:
            data = client.post('/api/stats')
            self.handler._ok(data)
            self.handler._log_request('GET', f'/tokens/{idx}/stats', 200)
        except Exception as e:
            self.handler._log_error(f"upstream error: {e}")
            self.handler._err('upstream API error', ERR_UPSTREAM_ERROR, 502)
            self.handler._log_request('GET', f'/tokens/{idx}/stats', 502)

    def get_token_details(self, idx: int):
        """GET /tokens/{idx}/details - 获取 token 详情"""
        if idx >= len(self.app.tokens):
            self.handler._err('token not found', ERR_NOT_FOUND, 404)
            self.handler._log_request('GET', f'/tokens/{idx}/details', 404)
            return

        token = self.app.tokens[idx]
        base = self.app.config.get('api', {}).get('base_url', '')
        from ...utils.http import HttpClient
        client = HttpClient(base, token['credential'])

        try:
            data = client.post('/api/request-details')
            self.handler._ok(data)
            self.handler._log_request('GET', f'/tokens/{idx}/details', 200)
        except Exception as e:
            self.handler._log_error(f"upstream error: {e}")
            self.handler._err('upstream API error', ERR_UPSTREAM_ERROR, 502)
            self.handler._log_request('GET', f'/tokens/{idx}/details', 502)

    def add_token(self, body: dict):
        """POST /tokens - 添加 token"""
        name = body.get('name', '').strip()
        credential = body.get('credential', '').strip()

        if not name or not credential:
            self.handler._err('name and credential required', ERR_MISSING_FIELD)
            self.handler._log_request('POST', '/tokens', 400)
            return

        token = {
            'name': name,
            'credential': credential,
            'daily_limit': body.get('daily_limit', 0),
        }
        self.app.tokens.append(token)
        self.app._save_config()
        self.handler._ok({'index': len(self.app.tokens) - 1}, 201)
        self.handler._log_request('POST', '/tokens', 201)

    def update_token(self, idx: int, body: dict):
        """PUT /tokens/{idx} - 更新 token"""
        if idx >= len(self.app.tokens):
            self.handler._err('token not found', ERR_NOT_FOUND, 404)
            self.handler._log_request('PUT', f'/tokens/{idx}', 404)
            return

        token = self.app.tokens[idx]
        if 'name' in body:
            token['name'] = body['name']
        if 'credential' in body:
            token['credential'] = body['credential']
        if 'daily_limit' in body:
            token['daily_limit'] = body['daily_limit']

        self.app._save_config()

        if idx == self.app.current_token_idx:
            self.app.http.set_credential(token['credential'])

        self.handler._ok()
        self.handler._log_request('PUT', f'/tokens/{idx}', 200)

    def delete_token(self, idx: int):
        """DELETE /tokens/{idx} - 删除 token"""
        if idx >= len(self.app.tokens) or len(self.app.tokens) <= 1:
            self.handler._err('cannot delete', ERR_CANNOT_DELETE)
            self.handler._log_request('DELETE', f'/tokens/{idx}', 400)
            return

        self.app.tokens.pop(idx)

        if self.app.current_token_idx >= len(self.app.tokens):
            self.app.current_token_idx = len(self.app.tokens) - 1

        self.app.http.set_credential(
            self.app.tokens[self.app.current_token_idx]['credential'])
        self.app._save_config()
        self.handler._ok()
        self.handler._log_request('DELETE', f'/tokens/{idx}', 200)
