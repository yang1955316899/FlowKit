"""页面管理路由"""


class PageRoutes:
    """页面管理路由"""

    def __init__(self, handler):
        self.handler = handler
        self.app = handler.app

    def get_pages(self):
        """GET /api/v1/pages - 获取所有页面"""
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
        self.handler._ok(result)
        self.handler._log_request('GET', '/pages', 200)

    def create_page(self, body: dict):
        """POST /api/v1/pages - 创建新页面"""
        pages = self.app.config.get('launcher', {}).get('pages', [])
        new_page = {
            'name': body.get('name', '新页面'),
            'actions': []
        }
        pages.append(new_page)
        self.app._save_config()
        self.handler._ok({'index': len(pages) - 1, 'page': new_page})
        self.handler._log_request('POST', '/pages', 200)

    def update_page(self, idx: int, body: dict):
        """PUT /api/v1/pages/{idx} - 更新页面"""
        from ..server import ERR_NOT_FOUND
        pages = self.app.config.get('launcher', {}).get('pages', [])
        if idx < 0 or idx >= len(pages):
            self.handler._err('page not found', ERR_NOT_FOUND, 404)
            self.handler._log_request('PUT', f'/pages/{idx}', 404)
            return

        if 'name' in body:
            pages[idx]['name'] = body['name']
        if 'actions' in body:
            pages[idx]['actions'] = body['actions']

        self.app._save_config()
        self.handler._ok(pages[idx])
        self.handler._log_request('PUT', f'/pages/{idx}', 200)

    def delete_page(self, idx: int):
        """DELETE /api/v1/pages/{idx} - 删除页面"""
        from ..server import ERR_NOT_FOUND
        pages = self.app.config.get('launcher', {}).get('pages', [])
        if idx < 0 or idx >= len(pages):
            self.handler._err('page not found', ERR_NOT_FOUND, 404)
            self.handler._log_request('DELETE', f'/pages/{idx}', 404)
            return

        pages.pop(idx)
        self.app._save_config()
        self.handler._ok({'deleted': idx})
        self.handler._log_request('DELETE', f'/pages/{idx}', 200)
