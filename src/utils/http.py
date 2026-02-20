"""HTTP 请求封装"""

import requests
from typing import Any


class HttpClient:
    """HTTP 客户端"""

    def __init__(self, base_url: str, credential: str = ''):
        self.base_url = base_url.rstrip('/')
        self.credential = credential
        self.headers = {
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
        }

    def set_credential(self, credential: str):
        """切换 credential"""
        self.credential = credential

    def post(self, endpoint: str, data: dict = None) -> dict[str, Any] | None:
        """发送 POST 请求"""
        url = f"{self.base_url}{endpoint}"
        payload = data or {}
        payload['credential'] = self.credential

        try:
            resp = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=10,
                verify=False
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None
