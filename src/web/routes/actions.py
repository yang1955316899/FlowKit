"""Actions 相关路由"""

import threading
import uuid
from ...utils.logger import get_logger

logger = get_logger('web.routes.actions')

# 错误码
ERR_NOT_FOUND = 1001
ERR_MISSING_FIELD = 1004
ERR_INVALID_ACTION = 1006


class ActionRoutes:
    """Action 路由处理器"""

    def __init__(self, handler):
        self.handler = handler
        self.app = handler.app

    def get_actions(self, query: dict):
        """GET /actions - 获取当前页所有动作"""
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

        self.handler._ok({
            'page': current_page,
            'pageName': page.get('name', ''),
            'totalPages': len(pages),
            'actions': result,
        })
        self.handler._log_request('GET', '/actions', 200)

    def execute_action(self, body: dict):
        """POST /actions/execute - 执行动作"""
        if not body.get('type'):
            self.handler._err('action type required', ERR_MISSING_FIELD)
            self.handler._log_request('POST', '/actions/execute', 400)
            return

        threading.Thread(
            target=self.app.executor.execute, args=(body,), daemon=True
        ).start()
        self.handler._ok()
        self.handler._log_request('POST', '/actions/execute', 200)

    def execute_action_by_idx(self, idx: int):
        """POST /actions/{idx}/execute - 执行指定索引的动作"""
        launcher_cfg = self.app.config.get('launcher', {})
        pages = launcher_cfg.get('pages', [])
        current_page = launcher_cfg.get('current_page', 0)

        if current_page >= len(pages):
            self.handler._err('no pages', ERR_NOT_FOUND, 404)
            self.handler._log_request('POST', f'/actions/{idx}/execute', 404)
            return

        actions = pages[current_page].get('actions', [])
        if idx >= len(actions) or actions[idx] is None:
            self.handler._err('action not found', ERR_NOT_FOUND, 404)
            self.handler._log_request('POST', f'/actions/{idx}/execute', 404)
            return

        action = actions[idx]
        threading.Thread(
            target=self.app.executor.execute, args=(action,), daemon=True
        ).start()
        self.handler._ok({'message': 'action started'})
        self.handler._log_request('POST', f'/actions/{idx}/execute', 200)

    def add_action(self, body: dict):
        """POST /actions - 新增动作"""
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

        self.handler._ok({'index': len(actions) - 1, 'id': action['id']}, 201)
        self.handler._log_request('POST', '/actions', 201)

    def update_action(self, idx: int, body: dict):
        """PUT /actions/{idx} - 更新指定索引的动作"""
        launcher_cfg = self.app.config.get('launcher', {})
        pages = launcher_cfg.get('pages', [])
        current_page = launcher_cfg.get('current_page', 0)

        if current_page >= len(pages):
            self.handler._err('page not found', ERR_NOT_FOUND, 404)
            self.handler._log_request('PUT', f'/actions/{idx}', 404)
            return

        actions = pages[current_page].get('actions', [])
        if idx >= len(actions) or actions[idx] is None:
            self.handler._err('action not found', ERR_NOT_FOUND, 404)
            self.handler._log_request('PUT', f'/actions/{idx}', 404)
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

        self.handler._ok()
        self.handler._log_request('PUT', f'/actions/{idx}', 200)

    def delete_action(self, idx: int):
        """DELETE /actions/{idx} - 删除指定索引的动作"""
        launcher_cfg = self.app.config.get('launcher', {})
        pages = launcher_cfg.get('pages', [])
        current_page = launcher_cfg.get('current_page', 0)

        if current_page >= len(pages):
            self.handler._err('page not found', ERR_NOT_FOUND, 404)
            self.handler._log_request('DELETE', f'/actions/{idx}', 404)
            return

        actions = pages[current_page].get('actions', [])
        if idx >= len(actions):
            self.handler._err('action not found', ERR_NOT_FOUND, 404)
            self.handler._log_request('DELETE', f'/actions/{idx}', 404)
            return

        actions[idx] = None
        # 清理尾部 None
        while actions and actions[-1] is None:
            actions.pop()

        self.app._save_config()

        # 刷新热键注册
        if hasattr(self.app, '_register_action_hotkeys'):
            self.app._register_action_hotkeys()

        self.handler._ok()
        self.handler._log_request('DELETE', f'/actions/{idx}', 200)

    def reorder_actions(self, body: dict):
        """POST /actions/reorder - 拖拽重排序动作"""
        from_idx = body.get('from')
        to_idx = body.get('to')

        if from_idx is None or to_idx is None:
            self.handler._err('from and to required', ERR_MISSING_FIELD)
            self.handler._log_request('POST', '/actions/reorder', 400)
            return

        launcher_cfg = self.app.config.get('launcher', {})
        pages = launcher_cfg.get('pages', [])
        current_page = launcher_cfg.get('current_page', 0)

        if current_page >= len(pages):
            self.handler._err('page not found', ERR_NOT_FOUND, 404)
            self.handler._log_request('POST', '/actions/reorder', 404)
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
        self.handler._ok()
        self.handler._log_request('POST', '/actions/reorder', 200)

    def update_page_action(self, pidx: int, aidx: int, body: dict):
        """PUT /pages/{pidx}/actions/{aidx} - 更新指定页面的动作"""
        pages = self.app.config.get('launcher', {}).get('pages', [])

        if pidx >= len(pages):
            self.handler._err('page not found', ERR_NOT_FOUND, 404)
            self.handler._log_request('PUT', f'/pages/{pidx}/actions/{aidx}', 404)
            return

        actions = pages[pidx].get('actions', [])
        if aidx >= len(actions):
            self.handler._err('action not found', ERR_NOT_FOUND, 404)
            self.handler._log_request('PUT', f'/pages/{pidx}/actions/{aidx}', 404)
            return

        action = actions[aidx]
        if action and action.get('type') == 'combo':
            if 'steps' in body:
                action['steps'] = body['steps']
            if 'delay' in body:
                action['delay'] = body['delay']
            self.app._save_config()
            self.handler._ok()
            self.handler._log_request('PUT', f'/pages/{pidx}/actions/{aidx}', 200)
        else:
            self.handler._err('not a combo action', ERR_INVALID_ACTION)
            self.handler._log_request('PUT', f'/pages/{pidx}/actions/{aidx}', 400)
