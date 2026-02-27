"""内嵌 Web UI — HTTP 服务 + API 路由"""

import json
import time
import uuid
import logging
import threading
import mimetypes
import urllib.parse
from pathlib import Path
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from ..utils.http_cache import HttpClientCache

STATIC_DIR = Path(__file__).parent / 'static'
API_PREFIX = '/api/v1'

# MIME 补充
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/css', '.css')

# ── 错误码 ──
ERR_BAD_REQUEST = 1000
ERR_NOT_FOUND = 1001
ERR_FORBIDDEN = 1002
ERR_INVALID_INDEX = 1003
ERR_MISSING_FIELD = 1004
ERR_CANNOT_DELETE = 1005
ERR_INVALID_ACTION = 1006
ERR_NOT_IMPLEMENTED = 1007
ERR_PARSE_ERROR = 1008
ERR_UPSTREAM_ERROR = 1009

# ── 日志 ──
logger = logging.getLogger('flowkit.web')
logger.setLevel(logging.INFO)


class WebHandler(BaseHTTPRequestHandler):
    """路由分发：静态文件 + API v1"""

    server: 'WebServer'

    @property
    def app(self):
        return self.server.app

    @property
    def _http_client_cache(self):
        """HttpClient 实例缓存"""
        if not hasattr(self.server, '_client_cache'):
            self.server._client_cache = HttpClientCache()
        return self.server._client_cache

    def _get_http_client(self, token_idx: int):
        """获取或创建 HttpClient 实例（带缓存）"""
        cache_key = f'token_{token_idx}'

        def factory():
            if token_idx >= len(self.app.tokens):
                return None
            token = self.app.tokens[token_idx]
            base = self.app.config.get('api', {}).get('base_url', '')
            from ..utils.http import HttpClient
            return HttpClient(base, token['credential'])

        return self._http_client_cache.get(cache_key, factory)

    def _invalidate_http_client_cache(self, token_idx: int = None):
        """清除 HttpClient 缓存"""
        if token_idx is None:
            self._http_client_cache.invalidate()
        else:
            cache_key = f'token_{token_idx}'
            self._http_client_cache.invalidate(cache_key)

    # ── 统一响应 {"code": 0, "data": ..., "error": ""} ──

    def _ok(self, data=None, http_code: int = 200):
        """成功 → code=0"""
        self._send_json(http_code, {'code': 0, 'data': data, 'error': ''})

    def _err(self, error: str, err_code: int = ERR_BAD_REQUEST, http_code: int = 400):
        """失败 → code=非零错误码"""
        self._send_json(http_code, {'code': err_code, 'data': None, 'error': error})

    def _send_json(self, code: int, obj):
        body = json.dumps(obj, ensure_ascii=False, default=str).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(body)

    # ── 请求追踪 ──

    def _start_request(self) -> str:
        """开始请求，返回 request_id"""
        rid = uuid.uuid4().hex[:8]
        self._request_id = rid
        self._request_start = time.time()
        return rid

    def _log_request(self, method: str, path: str, status: int):
        """记录请求日志"""
        elapsed = (time.time() - self._request_start) * 1000
        rid = getattr(self, '_request_id', '?')
        logger.info(f"[{rid}] {method} {path} → {status} ({elapsed:.1f}ms)")

    def _log_error(self, msg: str):
        """记录错误日志"""
        rid = getattr(self, '_request_id', '?')
        logger.warning(f"[{rid}] {msg}")

    # ── 静态文件 ──

    def _serve_static(self, rel_path: str):
        if not rel_path or rel_path == '/':
            rel_path = '/index.html'
        safe = Path(STATIC_DIR / rel_path.lstrip('/')).resolve()
        if not str(safe).startswith(str(STATIC_DIR.resolve())):
            return self._err('forbidden', ERR_FORBIDDEN, 403)
        if not safe.is_file():
            return self._err('not found', ERR_NOT_FOUND, 404)
        mime = mimetypes.guess_type(str(safe))[0] or 'application/octet-stream'
        data = safe.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(data)))
        self._cors_headers()
        self.end_headers()
        self.wfile.write(data)

    # ── 辅助 ──

    def _read_body(self) -> dict:
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except json.JSONDecodeError as e:
            self._log_error(f"JSON parse error: {e}")
            return None  # 调用方检查 None

    def _cors_headers(self):
        """CORS 头 — 仅允许 localhost 和配置的白名单"""
        origin = self.headers.get('Origin', '')
        allowed = ['http://localhost', 'http://127.0.0.1']
        # 从配置读取额外白名单
        extra = self.server.allowed_origins if hasattr(self.server, 'allowed_origins') else []
        allowed.extend(extra)
        if any(origin.startswith(a) for a in allowed):
            self.send_header('Access-Control-Allow-Origin', origin)
        else:
            self.send_header('Access-Control-Allow-Origin', 'http://localhost')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def _parse_idx(self, path: str, prefix: str, suffix: str = '') -> int | None:
        try:
            seg = path[len(prefix):]
            if suffix:
                seg = seg[:-len(suffix)]
            return int(seg)
        except (ValueError, IndexError):
            self._err('invalid index', ERR_INVALID_INDEX)
            return None

    def _strip_api_prefix(self, path: str) -> str | None:
        """提取 API_PREFIX 之后的路径部分，不匹配返回 None"""
        if path.startswith(API_PREFIX):
            return path[len(API_PREFIX):]
        # 兼容旧 /api/ 前缀 → 重定向到 /api/v1/
        if path.startswith('/api/') and not path.startswith('/api/v1'):
            new_path = API_PREFIX + path[4:]  # /api/xxx → /api/v1/xxx
            self.send_response(308)
            self.send_header('Location', new_path)
            self._cors_headers()
            self.end_headers()
            return None  # 已处理
        return None

    def log_message(self, format, *args):
        pass  # 使用自定义日志

    # ── 路由 ──

    def do_OPTIONS(self):
        self._start_request()
        self.send_response(204)
        self._cors_headers()
        self.end_headers()
        self._log_request('OPTIONS', self.path, 204)

    def do_GET(self):
        rid = self._start_request()
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # WebSocket 升级检测（预留）
        if self.headers.get('Upgrade', '').lower() == 'websocket':
            self._handle_websocket_upgrade()
            return

        route = self._strip_api_prefix(path)
        if route is not None:
            self._route_get(route)
        elif not path.startswith('/api/'):
            # 非 API 路径 → 静态文件
            self._serve_static(path)
            self._log_request('GET', path, 200)

    def do_POST(self):
        self._start_request()
        path = urllib.parse.urlparse(self.path).path
        body = self._read_body()
        if body is None:
            self._err('invalid JSON body', ERR_PARSE_ERROR)
            self._log_request('POST', path, 400)
            return
        route = self._strip_api_prefix(path)
        if route is not None:
            self._route_post(route, body)
        if not path.startswith('/api/'):
            self._err('not found', ERR_NOT_FOUND, 404)
            self._log_request('POST', path, 404)

    def do_PUT(self):
        self._start_request()
        path = urllib.parse.urlparse(self.path).path
        body = self._read_body()
        if body is None:
            self._err('invalid JSON body', ERR_PARSE_ERROR)
            self._log_request('PUT', path, 400)
            return
        route = self._strip_api_prefix(path)
        if route is not None:
            self._route_put(route, body)
        if not path.startswith('/api/'):
            self._err('not found', ERR_NOT_FOUND, 404)
            self._log_request('PUT', path, 404)

    def do_DELETE(self):
        self._start_request()
        path = urllib.parse.urlparse(self.path).path
        route = self._strip_api_prefix(path)
        if route is not None:
            self._route_delete(route)
        if not path.startswith('/api/'):
            self._err('not found', ERR_NOT_FOUND, 404)
            self._log_request('DELETE', path, 404)

    # ── GET 路由 ──

    def _route_get(self, route: str):
        parsed = urllib.parse.urlparse(route)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if route == '/health':
            return self._api_health()
        if route == '/tokens':
            return self._api_get_tokens()
        if route.startswith('/tokens/') and route.endswith('/stats'):
            idx = self._parse_idx(route, '/tokens/', '/stats')
            if idx is not None:
                return self._api_get_token_stats(idx)
            return
        if route.startswith('/tokens/') and route.endswith('/details'):
            idx = self._parse_idx(route, '/tokens/', '/details')
            if idx is not None:
                return self._api_get_token_details(idx)
            return
        if route == '/flows/step-types':
            return self._api_get_step_types()
        if route == '/pages':
            return self._api_get_pages()
        if route == '/actions':
            return self._api_get_actions(query)
        if route == '/config':
            return self._api_get_config()
        if route == '/recorder/status':
            return self._api_recorder_status()
        if route == '/stats/actions':
            return self._api_get_action_stats()
        if route == '/stats/overview':
            return self._api_get_stats_overview()
        if route == '/scripts':
            return self._api_get_scripts()
        if path == '/search':
            return self._api_search(query.get('q', [''])[0])
        self._err('not found', ERR_NOT_FOUND, 404)
        self._log_request('GET', route, 404)

    # ── POST 路由 ──

    def _route_post(self, route: str, body: dict):
        if route == '/tokens':
            return self._api_add_token(body)
        if route == '/flows/execute':
            return self._api_execute_flow(body)
        if route == '/actions/execute':
            return self._api_execute_action(body)
        if route == '/actions':
            return self._api_add_action(body)
        if route == '/actions/reorder':
            return self._api_reorder_actions(body)
        if route == '/recorder/start':
            return self._api_recorder_start()
        if route == '/recorder/stop':
            return self._api_recorder_stop()
        if route == '/recorder/pause':
            return self._api_recorder_pause()
        if route == '/input/pick-coordinate':
            return self._api_pick_coordinate(body)
        if route == '/pages':
            return self._api_create_page(body)
        if route == '/scripts/execute':
            return self._api_execute_script(body)
        if route.startswith('/actions/') and route.endswith('/execute'):
            idx = self._parse_idx(route, '/actions/', '/execute')
            if idx is not None:
                return self._api_execute_action_by_idx(idx)
            return
        self._err('not found', ERR_NOT_FOUND, 404)
        self._log_request('POST', route, 404)

    # ── PUT 路由 ──

    def _route_put(self, route: str, body: dict):
        if route.startswith('/tokens/'):
            idx = self._parse_idx(route, '/tokens/')
            if idx is not None:
                return self._api_update_token(idx, body)
            return

        if route.startswith('/actions/'):
            idx = self._parse_idx(route, '/actions/')
            if idx is not None:
                return self._api_update_action_by_idx(idx, body)
            return

        if route == '/config':
            return self._api_update_config(body)

        if route == '/theme':
            return self._api_update_theme(body)

        if route.startswith('/pages/'):
            idx = self._parse_idx(route, '/pages/')
            if idx is not None:
                return self._api_update_page(idx, body)
            return

        # PUT /pages/{pidx}/actions/{aidx}
        parts = route.strip('/').split('/')
        if len(parts) == 4 and parts[0] == 'pages' and parts[2] == 'actions':
            try:
                pidx, aidx = int(parts[1]), int(parts[3])
                return self._api_update_action(pidx, aidx, body)
            except (ValueError, IndexError):
                pass

        self._err('not found', ERR_NOT_FOUND, 404)
        self._log_request('PUT', route, 404)

    # ── DELETE 路由 ──

    def _route_delete(self, route: str):
        if route.startswith('/tokens/'):
            idx = self._parse_idx(route, '/tokens/')
            if idx is not None:
                return self._api_delete_token(idx)
            return
        if route.startswith('/actions/'):
            idx = self._parse_idx(route, '/actions/')
            if idx is not None:
                return self._api_delete_action(idx)
            return
        if route.startswith('/pages/'):
            idx = self._parse_idx(route, '/pages/')
            if idx is not None:
                return self._api_delete_page(idx)
            return
        self._err('not found', ERR_NOT_FOUND, 404)
        self._log_request('DELETE', route, 404)

    # ── Health API ──

    def _api_health(self):
        """健康检查端点"""
        self._ok({
            'status': 'ok',
            'uptime': time.time() - self.server._start_time,
        })
        self._log_request('GET', '/health', 200)

    # ── Token API ──

    def _api_get_tokens(self):
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
        self._ok(tokens)
        self._log_request('GET', '/tokens', 200)

    def _api_get_token_stats(self, idx: int):
        if idx >= len(self.app.tokens):
            self._err('token not found', ERR_NOT_FOUND, 404)
            self._log_request('GET', f'/tokens/{idx}/stats', 404)
            return
        client = self._get_http_client(idx)
        if not client:
            self._err('failed to create http client', ERR_UPSTREAM_ERROR, 500)
            self._log_request('GET', f'/tokens/{idx}/stats', 500)
            return
        try:
            data = client.post('/api/stats')
            self._ok(data)
            self._log_request('GET', f'/tokens/{idx}/stats', 200)
        except Exception as e:
            self._log_error(f"upstream error: {e}")
            self._err('upstream API error', ERR_UPSTREAM_ERROR, 502)
            self._log_request('GET', f'/tokens/{idx}/stats', 502)

    def _api_get_token_details(self, idx: int):
        if idx >= len(self.app.tokens):
            self._err('token not found', ERR_NOT_FOUND, 404)
            self._log_request('GET', f'/tokens/{idx}/details', 404)
            return
        client = self._get_http_client(idx)
        if not client:
            self._err('failed to create http client', ERR_UPSTREAM_ERROR, 500)
            self._log_request('GET', f'/tokens/{idx}/details', 500)
            return
        try:
            data = client.post('/api/request-details')
            self._ok(data)
            self._log_request('GET', f'/tokens/{idx}/details', 200)
        except Exception as e:
            self._log_error(f"upstream error: {e}")
            self._err('upstream API error', ERR_UPSTREAM_ERROR, 502)
            self._log_request('GET', f'/tokens/{idx}/details', 502)

    def _api_add_token(self, body: dict):
        name = body.get('name', '').strip()
        credential = body.get('credential', '').strip()
        if not name or not credential:
            self._err('name and credential required', ERR_MISSING_FIELD)
            self._log_request('POST', '/tokens', 400)
            return
        token = {
            'name': name,
            'credential': credential,
            'daily_limit': body.get('daily_limit', 0),
        }
        self.app.tokens.append(token)
        self.app._save_config()
        self._ok({'index': len(self.app.tokens) - 1}, 201)
        self._log_request('POST', '/tokens', 201)

    def _api_update_token(self, idx: int, body: dict):
        if idx >= len(self.app.tokens):
            self._err('token not found', ERR_NOT_FOUND, 404)
            self._log_request('PUT', f'/tokens/{idx}', 404)
            return
        token = self.app.tokens[idx]
        if 'name' in body:
            token['name'] = body['name']
        if 'credential' in body:
            token['credential'] = body['credential']
            # 清除缓存，下次请求时重新创建
            self._invalidate_http_client_cache(idx)
        if 'daily_limit' in body:
            token['daily_limit'] = body['daily_limit']
        self.app._save_config()
        if idx == self.app.current_token_idx:
            self.app.http.set_credential(token['credential'])
        self._ok()
        self._log_request('PUT', f'/tokens/{idx}', 200)

    def _api_delete_token(self, idx: int):
        if idx >= len(self.app.tokens) or len(self.app.tokens) <= 1:
            self._err('cannot delete', ERR_CANNOT_DELETE)
            self._log_request('DELETE', f'/tokens/{idx}', 400)
            return
        self.app.tokens.pop(idx)
        if self.app.current_token_idx >= len(self.app.tokens):
            self.app.current_token_idx = len(self.app.tokens) - 1
        self.app.http.set_credential(
            self.app.tokens[self.app.current_token_idx]['credential'])
        self.app._save_config()
        self._ok()
        self._log_request('DELETE', f'/tokens/{idx}', 200)

    # ── Flow API ──

    def _api_get_step_types(self):
        from ..core.step_types import PALETTE_CATEGORIES, STEP_CATEGORY_COLORS
        result = []
        for cat_name, items in PALETTE_CATEGORIES:
            steps = []
            for type_id, type_name, icon, desc in items:
                steps.append({
                    'type': type_id,
                    'name': type_name,
                    'icon': icon,
                    'desc': desc,
                    'color': STEP_CATEGORY_COLORS.get(type_id, 'accent'),
                })
            result.append({'category': cat_name, 'steps': steps})
        self._ok(result)
        self._log_request('GET', '/flows/step-types', 200)

    def _api_get_pages(self):
        pages = self.app.config.get('launcher', {}).get('pages', [])
        result = []
        for i, page in enumerate(pages):
            actions = []
            for j, act in enumerate(page.get('actions', [])):
                if act:
                    actions.append({
                        'index': j,
                        'type': act.get('type', ''),
                        'label': act.get('label', ''),
                        'icon': act.get('icon', ''),
                        'steps': act.get('steps', []) if act.get('type') == 'combo' else [],
                        'delay': act.get('delay', 500) if act.get('type') == 'combo' else 500,
                    })
            result.append({
                'index': i,
                'name': page.get('name', ''),
                'actions': actions,
            })
        self._ok(result)
        self._log_request('GET', '/pages', 200)

    def _api_execute_flow(self, body: dict):
        steps = body.get('steps', [])
        delay = body.get('delay', 500)
        if not steps:
            self._err('no steps', ERR_MISSING_FIELD)
            self._log_request('POST', '/flows/execute', 400)
            return
        action = {'type': 'combo', 'steps': steps, 'delay': delay}
        threading.Thread(
            target=self.app.executor.execute, args=(action,), daemon=True
        ).start()
        self._ok({'message': 'flow started'})
        self._log_request('POST', '/flows/execute', 200)

    def _api_execute_action(self, body: dict):
        if not body.get('type'):
            self._err('action type required', ERR_MISSING_FIELD)
            self._log_request('POST', '/actions/execute', 400)
            return
        threading.Thread(
            target=self.app.executor.execute, args=(body,), daemon=True
        ).start()
        self._ok()
        self._log_request('POST', '/actions/execute', 200)

    def _api_update_action(self, pidx: int, aidx: int, body: dict):
        pages = self.app.config.get('launcher', {}).get('pages', [])
        if pidx >= len(pages):
            self._err('page not found', ERR_NOT_FOUND, 404)
            self._log_request('PUT', f'/pages/{pidx}/actions/{aidx}', 404)
            return
        actions = pages[pidx].get('actions', [])
        if aidx >= len(actions):
            self._err('action not found', ERR_NOT_FOUND, 404)
            self._log_request('PUT', f'/pages/{pidx}/actions/{aidx}', 404)
            return
        action = actions[aidx]
        if action and action.get('type') == 'combo':
            if 'steps' in body:
                action['steps'] = body['steps']
            if 'delay' in body:
                action['delay'] = body['delay']
            self.app._save_config()
            self._ok()
            self._log_request('PUT', f'/pages/{pidx}/actions/{aidx}', 200)
        else:
            self._err('not a combo action', ERR_INVALID_ACTION)
            self._log_request('PUT', f'/pages/{pidx}/actions/{aidx}', 400)

    # ── Launcher API ──

    def _api_get_actions(self, query: dict):
        """获取当前页所有动作"""
        launcher_cfg = self.app.config.get('launcher', {})
        pages = launcher_cfg.get('pages', [])
        current_page = launcher_cfg.get('current_page', 0)

        # 支持查询参数指定页面
        if 'page' in query:
            try:
                current_page = int(query['page'][0])
            except (ValueError, IndexError):
                pass

        if current_page >= len(pages):
            current_page = 0

        page = pages[current_page] if pages else {'actions': []}
        actions = page.get('actions', [])

        result = []
        for i, act in enumerate(actions):
            if act is not None:
                result.append({
                    'index': i,
                    'id': act.get('id', ''),
                    'type': act.get('type', ''),
                    'label': act.get('label', ''),
                    'icon': act.get('icon', ''),
                    'hotkey': act.get('hotkey', ''),
                    'steps': act.get('steps', []) if act.get('type') == 'combo' else [],
                    'delay': act.get('delay', 500) if act.get('type') == 'combo' else 500,
                })

        self._ok({
            'page': current_page,
            'pageName': page.get('name', ''),
            'totalPages': len(pages),
            'actions': result,
        })
        self._log_request('GET', '/actions', 200)

    def _api_execute_action_by_idx(self, idx: int):
        """执行指定索引的动作"""
        launcher_cfg = self.app.config.get('launcher', {})
        pages = launcher_cfg.get('pages', [])
        current_page = launcher_cfg.get('current_page', 0)

        if current_page >= len(pages):
            self._err('no pages', ERR_NOT_FOUND, 404)
            self._log_request('POST', f'/actions/{idx}/execute', 404)
            return

        actions = pages[current_page].get('actions', [])
        if idx >= len(actions) or actions[idx] is None:
            self._err('action not found', ERR_NOT_FOUND, 404)
            self._log_request('POST', f'/actions/{idx}/execute', 404)
            return

        action = actions[idx]
        threading.Thread(
            target=self.app.executor.execute, args=(action,), daemon=True
        ).start()
        self._ok({'message': 'action started'})
        self._log_request('POST', f'/actions/{idx}/execute', 200)

    def _api_add_action(self, body: dict):
        """新增动作"""
        import uuid
        launcher_cfg = self.app.config.get('launcher', {})
        pages = launcher_cfg.setdefault('pages', [])

        if not pages:
            pages.append({'name': '工具', 'actions': []})

        current_page = launcher_cfg.get('current_page', 0)
        if current_page >= len(pages):
            current_page = 0

        action = {
            'id': str(uuid.uuid4())[:8],
            'type': body.get('type', 'combo'),
            'label': body.get('label', ''),
            'icon': body.get('icon', '✦'),
            'target': body.get('target', ''),
        }
        if action['type'] == 'combo':
            action['steps'] = body.get('steps', [])
            action['delay'] = body.get('delay', 500)

        actions = pages[current_page].setdefault('actions', [])

        # 找空位或追加
        placed = False
        for i in range(len(actions)):
            if actions[i] is None:
                actions[i] = action
                placed = True
                break
        if not placed:
            actions.append(action)

        self.app._save_config()
        self.app.config['launcher'] = launcher_cfg

        # 刷新热键注册
        if hasattr(self.app, '_register_action_hotkeys'):
            self.app._register_action_hotkeys()

        self._ok({'index': len(actions) - 1, 'id': action['id']}, 201)
        self._log_request('POST', '/actions', 201)

    def _api_update_action_by_idx(self, idx: int, body: dict):
        """更新指定索引的动作"""
        launcher_cfg = self.app.config.get('launcher', {})
        pages = launcher_cfg.get('pages', [])
        current_page = launcher_cfg.get('current_page', 0)

        if current_page >= len(pages):
            self._err('page not found', ERR_NOT_FOUND, 404)
            self._log_request('PUT', f'/actions/{idx}', 404)
            return

        actions = pages[current_page].get('actions', [])
        if idx >= len(actions) or actions[idx] is None:
            self._err('action not found', ERR_NOT_FOUND, 404)
            self._log_request('PUT', f'/actions/{idx}', 404)
            return

        action = actions[idx]
        if 'label' in body:
            action['label'] = body['label']
        if 'icon' in body:
            action['icon'] = body['icon']
        if 'hotkey' in body:
            action['hotkey'] = body['hotkey']
        if action.get('type') == 'combo':
            if 'steps' in body:
                action['steps'] = body['steps']
            if 'delay' in body:
                action['delay'] = body['delay']

        self.app._save_config()

        # 刷新热键注册
        if hasattr(self.app, '_register_action_hotkeys'):
            self.app._register_action_hotkeys()

        self._ok()
        self._log_request('PUT', f'/actions/{idx}', 200)

    def _api_delete_action(self, idx: int):
        """删除指定索引的动作"""
        launcher_cfg = self.app.config.get('launcher', {})
        pages = launcher_cfg.get('pages', [])
        current_page = launcher_cfg.get('current_page', 0)

        if current_page >= len(pages):
            self._err('page not found', ERR_NOT_FOUND, 404)
            self._log_request('DELETE', f'/actions/{idx}', 404)
            return

        actions = pages[current_page].get('actions', [])
        if idx >= len(actions):
            self._err('action not found', ERR_NOT_FOUND, 404)
            self._log_request('DELETE', f'/actions/{idx}', 404)
            return

        actions[idx] = None
        # 清理尾部 None
        while actions and actions[-1] is None:
            actions.pop()

        self.app._save_config()

        # 刷新热键注册
        if hasattr(self.app, '_register_action_hotkeys'):
            self.app._register_action_hotkeys()

        self._ok()
        self._log_request('DELETE', f'/actions/{idx}', 200)

    def _api_reorder_actions(self, body: dict):
        """拖拽重排序动作"""
        from_idx = body.get('from')
        to_idx = body.get('to')

        if from_idx is None or to_idx is None:
            self._err('from and to required', ERR_MISSING_FIELD)
            self._log_request('POST', '/actions/reorder', 400)
            return

        launcher_cfg = self.app.config.get('launcher', {})
        pages = launcher_cfg.get('pages', [])
        current_page = launcher_cfg.get('current_page', 0)

        if current_page >= len(pages):
            self._err('page not found', ERR_NOT_FOUND, 404)
            self._log_request('POST', '/actions/reorder', 404)
            return

        actions = pages[current_page].get('actions', [])

        # 确保列表足够长
        max_idx = max(from_idx, to_idx)
        while len(actions) <= max_idx:
            actions.append(None)

        # 交换
        actions[from_idx], actions[to_idx] = actions[to_idx], actions[from_idx]

        # 清理尾部 None
        while actions and actions[-1] is None:
            actions.pop()

        self.app._save_config()
        self._ok()
        self._log_request('POST', '/actions/reorder', 200)

    def _api_get_config(self):
        """获取配置"""
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

        self._ok(cfg)
        self._log_request('GET', '/config', 200)

    def _deep_merge(self, target: dict, source: dict):
        """深度合并字典"""
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._deep_merge(target[key], value)
            else:
                target[key] = value

    def _api_update_config(self, body: dict):
        """更新配置（支持深度合并）"""
        # 允许更新的顶级字段
        allowed_keys = ['window', 'launcher', 'web']

        for key in allowed_keys:
            if key in body:
                if key not in self.app.config:
                    self.app.config[key] = {}
                # 深度合并而非覆盖
                self._deep_merge(self.app.config[key], body[key])

        self.app._save_config()

        # 如果更新了主题，通知应用切换主题
        if 'window' in body and 'theme' in body['window']:
            theme_name = body['window']['theme']
            if hasattr(self.app, 'switch_theme'):
                self.app.switch_theme(theme_name)

        self._ok()
        self._log_request('PUT', '/config', 200)

    def _api_search(self, query: str):
        """搜索动作"""
        if not query:
            self._ok([])
            self._log_request('GET', '/search', 200)
            return

        query = query.lower()
        results = []
        pages = self.app.config.get('launcher', {}).get('pages', [])

        for pi, page in enumerate(pages):
            for ai, action in enumerate(page.get('actions', [])):
                if action is None:
                    continue
                label = action.get('label', '').lower()
                # 模糊匹配
                if self._fuzzy_match(query, label):
                    results.append({
                        'page': pi,
                        'pageName': page.get('name', ''),
                        'index': ai,
                        'id': action.get('id', ''),
                        'type': action.get('type', ''),
                        'label': action.get('label', ''),
                        'icon': action.get('icon', '✦'),
                    })
                if len(results) >= 20:
                    break
            if len(results) >= 20:
                break

        self._ok(results)
        self._log_request('GET', '/search', 200)

    def _fuzzy_match(self, query: str, text: str) -> bool:
        """简单模糊匹配"""
        qi = 0
        for ch in text:
            if qi < len(query) and ch == query[qi]:
                qi += 1
        return qi == len(query)

    # ── Recorder API ──

    def _api_recorder_start(self):
        """POST /api/v1/recorder/start - 开始录制"""
        if not hasattr(self.app, '_recorder'):
            from ..core.recorder import InputRecorder
            self.app._recorder = InputRecorder()
        self.app._recorder.start()
        self._ok({'status': 'recording'})
        self._log_request('POST', '/recorder/start', 200)

    def _api_recorder_stop(self):
        """POST /api/v1/recorder/stop - 停止录制并返回步骤"""
        if not hasattr(self.app, '_recorder'):
            self._ok({'steps': [], 'count': 0})
            self._log_request('POST', '/recorder/stop', 200)
            return
        self.app._recorder.stop()
        steps = self.app._recorder.to_steps()
        self._ok({'steps': steps, 'count': len(steps)})
        self._log_request('POST', '/recorder/stop', 200)

    def _api_recorder_pause(self):
        """POST /api/v1/recorder/pause - 暂停/恢复录制"""
        if hasattr(self.app, '_recorder'):
            self.app._recorder.pause()
        self._ok({'status': 'paused' if self.app._recorder._paused else 'recording'})
        self._log_request('POST', '/recorder/pause', 200)

    def _api_recorder_status(self):
        """GET /api/v1/recorder/status - 获取录制状态"""
        if not hasattr(self.app, '_recorder'):
            self._ok({'recording': False, 'paused': False, 'event_count': 0})
            self._log_request('GET', '/recorder/status', 200)
            return
        self._ok({
            'recording': self.app._recorder.is_recording,
            'paused': self.app._recorder._paused,
            'event_count': self.app._recorder.event_count
        })
        self._log_request('GET', '/recorder/status', 200)

    # ── Input Capture API ──

    def _api_pick_coordinate(self, body: dict):
        """POST /api/v1/input/pick-coordinate - 拾取屏幕坐标"""
        from ..core.input_capture import CoordinatePicker
        picker = CoordinatePicker()
        timeout = body.get('timeout', 30)
        result = picker.pick(timeout=timeout)
        if result:
            self._ok({'x': result[0], 'y': result[1]})
            self._log_request('POST', '/input/pick-coordinate', 200)
        else:
            self._err('timeout or cancelled', 'ERR_TIMEOUT', 408)
            self._log_request('POST', '/input/pick-coordinate', 408)

    # ── Stats API ──

    def _api_get_action_stats(self):
        """GET /api/v1/stats/actions - 获取动作使用统计"""
        pages = self.app.config.get('launcher', {}).get('pages', [])
        stats = {}
        for page in pages:
            for action in page.get('actions', []):
                if action:
                    action_type = action.get('type', 'unknown')
                    stats[action_type] = stats.get(action_type, 0) + 1

        result = [{'type': k, 'count': v} for k, v in stats.items()]
        result.sort(key=lambda x: x['count'], reverse=True)
        self._ok(result)
        self._log_request('GET', '/stats/actions', 200)

    def _api_get_stats_overview(self):
        """GET /api/v1/stats/overview - 获取总览数据"""
        pages = self.app.config.get('launcher', {}).get('pages', [])
        total_actions = sum(len([a for a in p.get('actions', []) if a]) for p in pages)
        total_pages = len(pages)
        total_tokens = len(self.app.tokens)

        self._ok({
            'total_actions': total_actions,
            'total_pages': total_pages,
            'total_tokens': total_tokens,
        })
        self._log_request('GET', '/stats/overview', 200)

    # ── Pages CRUD API ──

    def _api_create_page(self, body: dict):
        """POST /api/v1/pages - 创建新页面"""
        pages = self.app.config.get('launcher', {}).get('pages', [])
        new_page = {
            'name': body.get('name', '新页面'),
            'actions': []
        }
        pages.append(new_page)
        self.app._save_config()
        self._ok({'index': len(pages) - 1, 'page': new_page})
        self._log_request('POST', '/pages', 200)

    def _api_update_page(self, idx: int, body: dict):
        """PUT /api/v1/pages/{idx} - 更新页面"""
        pages = self.app.config.get('launcher', {}).get('pages', [])
        if idx < 0 or idx >= len(pages):
            self._err('page not found', ERR_NOT_FOUND, 404)
            self._log_request('PUT', f'/pages/{idx}', 404)
            return

        if 'name' in body:
            pages[idx]['name'] = body['name']
        if 'actions' in body:
            pages[idx]['actions'] = body['actions']

        self.app._save_config()
        self._ok(pages[idx])
        self._log_request('PUT', f'/pages/{idx}', 200)

    def _api_delete_page(self, idx: int):
        """DELETE /api/v1/pages/{idx} - 删除页面"""
        pages = self.app.config.get('launcher', {}).get('pages', [])
        if idx < 0 or idx >= len(pages):
            self._err('page not found', ERR_NOT_FOUND, 404)
            self._log_request('DELETE', f'/pages/{idx}', 404)
            return

        pages.pop(idx)
        self.app._save_config()
        self._ok({'deleted': idx})
        self._log_request('DELETE', f'/pages/{idx}', 200)

    # ── Scripts API ──

    def _api_get_scripts(self):
        """GET /api/v1/scripts - 获取脚本列表"""
        pages = self.app.config.get('launcher', {}).get('pages', [])
        scripts = []
        for page_idx, page in enumerate(pages):
            for action_idx, action in enumerate(page.get('actions', [])):
                if action and action.get('type') == 'script':
                    scripts.append({
                        'page_idx': page_idx,
                        'action_idx': action_idx,
                        'label': action.get('label', ''),
                        'mode': action.get('mode', 'inline'),
                    })
        self._ok(scripts)
        self._log_request('GET', '/scripts', 200)

    def _api_execute_script(self, body: dict):
        """POST /api/v1/scripts/execute - 执行脚本"""
        code = body.get('code', '')
        if not code:
            self._err('code is required', ERR_BAD_REQUEST)
            self._log_request('POST', '/scripts/execute', 400)
            return

        # 使用 actions 模块执行脚本
        try:
            import io
            import sys
            from contextlib import redirect_stdout, redirect_stderr

            stdout_buffer = io.StringIO()
            stderr_buffer = io.StringIO()

            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                exec(code, {'__name__': '__main__'})

            self._ok({
                'stdout': stdout_buffer.getvalue(),
                'stderr': stderr_buffer.getvalue(),
                'success': True
            })
            self._log_request('POST', '/scripts/execute', 200)
        except Exception as e:
            self._ok({
                'stdout': '',
                'stderr': str(e),
                'success': False
            })
            self._log_request('POST', '/scripts/execute', 200)

    # ── Theme API ──

    def _api_update_theme(self, body: dict):
        """PUT /api/v1/theme - 切换主题"""
        theme_name = body.get('theme', 'dark')
        if 'launcher' not in self.app.config:
            self.app.config['launcher'] = {}
        self.app.config['launcher']['theme'] = theme_name
        self.app._save_config()
        self._ok({'theme': theme_name})
        self._log_request('PUT', '/theme', 200)

    # ── WebSocket 预留 ──

    def _handle_websocket_upgrade(self):
        """WebSocket 握手（预留，当前返回 501）"""
        key = self.headers.get('Sec-WebSocket-Key', '')
        if not key:
            self._err('missing websocket key', ERR_BAD_REQUEST)
            return
        # 握手实现预留 — 后续可用 wsproto 或手写帧解析
        # 当前返回 501 告知客户端尚未支持
        self._err('WebSocket not yet implemented', ERR_NOT_IMPLEMENTED, 501)
        self._log_request('GET', '/websocket-upgrade', 501)


class WebServer:
    """内嵌 HTTP 服务器"""

    def __init__(self, app, port: int = 18900, allowed_origins: list[str] = None):
        self.app = app
        self.port = port
        self.allowed_origins = allowed_origins or []
        self._httpd = None
        self._thread = None
        self._start_time = time.time()

    def start(self):
        self._httpd = ThreadingHTTPServer(('127.0.0.1', self.port), WebHandler)
        self._httpd.app = self.app  # 注入 app 引用
        self._httpd.allowed_origins = self.allowed_origins
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        logger.info(f"Web server started on http://127.0.0.1:{self.port}")

    def stop(self):
        if self._httpd:
            self._httpd.shutdown()
            logger.info("Web server stopped")
