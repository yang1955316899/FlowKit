"""平台 SDK — 用户脚本在子进程中 import 此模块，通过 IPC 调用主进程 API

用法（在用户脚本中）:
    from monitor_api import ctx
    text = ctx.clipboard.get_text()
    ctx.ui.toast("Hello!")
"""

import json
import os
import socket
import atexit


class _Connection:
    """与主进程 API 服务的 TCP 长连接，支持断线重连"""

    def __init__(self):
        self._sock: socket.socket | None = None
        self._req_id = 0
        self._buf = b''
        self._port = 0

    def _ensure_connected(self):
        if self._sock is not None:
            return
        self._port = int(os.environ.get('MONITOR_API_PORT', '0'))
        if not self._port:
            raise RuntimeError('MONITOR_API_PORT not set — script must be run from monitor')
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect(('127.0.0.1', self._port))
        self._sock.settimeout(60)

    def _reconnect(self):
        """断线后重新连接"""
        self.close()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.connect(('127.0.0.1', self._port))
        self._sock.settimeout(60)
        self._buf = b''

    def call(self, method: str, **params):
        self._ensure_connected()
        self._req_id += 1
        req = {'id': self._req_id, 'method': method, 'params': params}
        data = json.dumps(req, ensure_ascii=False).encode('utf-8') + b'\n'
        try:
            self._sock.sendall(data)
            return self._read_response()
        except (ConnectionError, OSError):
            # 断线重连一次
            try:
                self._reconnect()
                self._sock.sendall(data)
                return self._read_response()
            except Exception:
                raise

    def _read_response(self):
        while True:
            while b'\n' in self._buf:
                line, self._buf = self._buf.split(b'\n', 1)
                if not line.strip():
                    continue
                resp = json.loads(line.decode('utf-8'))
                if 'error' in resp and resp['error']:
                    raise RuntimeError(resp['error'])
                return resp.get('result')
            chunk = self._sock.recv(65536)
            if not chunk:
                raise ConnectionError('connection closed')
            self._buf += chunk

    def close(self):
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass
            self._sock = None


_conn = _Connection()


class _Clipboard:
    def get_text(self) -> str:
        return _conn.call('clipboard.get_text') or ''

    def set_text(self, text: str):
        _conn.call('clipboard.set_text', text=text)

    def get_files(self) -> list[str]:
        return _conn.call('clipboard.get_files') or []


class _Window:
    def get_foreground(self) -> dict:
        return _conn.call('window.get_foreground')

    def find(self, title: str = None, class_name: str = None) -> list[dict]:
        params = {}
        if title is not None:
            params['title'] = title
        if class_name is not None:
            params['class_name'] = class_name
        return _conn.call('window.find', **params) or []

    def activate(self, hwnd: int):
        _conn.call('window.activate', hwnd=hwnd)

    def move(self, hwnd: int, x: int, y: int, w: int, h: int):
        _conn.call('window.move', hwnd=hwnd, x=x, y=y, w=w, h=h)

    def minimize(self, hwnd: int):
        _conn.call('window.minimize', hwnd=hwnd)

    def maximize(self, hwnd: int):
        _conn.call('window.maximize', hwnd=hwnd)

    def close(self, hwnd: int):
        _conn.call('window.close', hwnd=hwnd)

    def set_topmost(self, hwnd: int, topmost: bool = True):
        _conn.call('window.set_topmost', hwnd=hwnd, topmost=topmost)


class _Http:
    def get(self, url: str, headers: dict = None, timeout: int = 10) -> dict:
        return _conn.call('http.get', url=url, headers=headers, timeout=timeout)

    def post(self, url: str, data=None, json_body=None, headers: dict = None,
             timeout: int = 10) -> dict:
        return _conn.call('http.post', url=url, data=data, json_body=json_body,
                          headers=headers, timeout=timeout)

    def download(self, url: str, save_path: str) -> str:
        return _conn.call('http.download', url=url, save_path=save_path)


class _UI:
    def toast(self, msg: str, duration: int = 1500):
        _conn.call('ui.toast', msg=msg, duration=duration)

    def notify(self, title: str, msg: str):
        _conn.call('ui.notify', title=title, msg=msg)

    def input(self, title: str, default: str = '') -> str | None:
        return _conn.call('ui.input', title=title, default=default)

    def confirm(self, title: str, msg: str) -> bool:
        return _conn.call('ui.confirm', title=title, msg=msg)

    def select(self, title: str, options: list[str]) -> str | None:
        return _conn.call('ui.select', title=title, options=options)


class _Keys:
    def send(self, combo: str):
        _conn.call('keys.send', combo=combo)

    def type_text(self, text: str):
        _conn.call('keys.type_text', text=text)


class _Mouse:
    def click(self, x: int, y: int):
        _conn.call('mouse.click', x=x, y=y)

    def move(self, x: int, y: int):
        _conn.call('mouse.move', x=x, y=y)


class _System:
    def env(self, name: str) -> str:
        return _conn.call('system.env', name=name) or ''

    def run(self, cmd: str, shell_type: str = 'cmd') -> str:
        return _conn.call('system.run', cmd=cmd, shell_type=shell_type) or ''

    def open(self, path: str):
        _conn.call('system.open', path=path)


class _Store:
    def get(self, key: str, default=None):
        result = _conn.call('store.get', key=key, default=default)
        return result

    def set(self, key: str, value):
        _conn.call('store.set', key=key, value=value)


class Context:
    """平台 API 上下文 — 用户脚本通过 ctx.xxx 调用"""

    def __init__(self):
        self.clipboard = _Clipboard()
        self.window = _Window()
        self.http = _Http()
        self.ui = _UI()
        self.keys = _Keys()
        self.mouse = _Mouse()
        self.system = _System()
        self.store = _Store()


# 全局单例
ctx = Context()

# 进程退出时关闭连接
atexit.register(_conn.close)
