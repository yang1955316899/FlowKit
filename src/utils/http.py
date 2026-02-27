"""HTTP 请求封装"""

import requests
from typing import Any
from .logger import get_logger

logger = get_logger('http')


class HttpClient:
    """HTTP 客户端（使用 Session 连接池）"""

    def __init__(self, base_url: str, credential: str = '', verify_ssl: bool = True):
        self.base_url = base_url.rstrip('/')
        self.credential = credential
        self.verify_ssl = verify_ssl
        self.headers = {
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache',
        }

        # 使用 Session 复用连接
        self._session = requests.Session()
        self._session.headers.update(self.headers)

        if not verify_ssl:
            logger.warning("SSL verification is disabled")
            # 禁用 SSL 警告
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    def set_credential(self, credential: str):
        """切换 credential"""
        self.credential = credential

    def post(self, endpoint: str, data: dict = None) -> dict[str, Any] | None:
        """发送 POST 请求"""
        url = f"{self.base_url}{endpoint}"
        payload = data or {}
        payload['credential'] = self.credential

        try:
            resp = self._session.post(
                url,
                json=payload,
                timeout=10,
                verify=self.verify_ssl
            )
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL verification failed for {url}: {e}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None

    def close(self):
        """关闭 Session"""
        if self._session:
            self._session.close()

    def __del__(self):
        """析构时关闭 Session"""
        self.close()
