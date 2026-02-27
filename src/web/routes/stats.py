"""统计相关路由"""


class StatsRoutes:
    """统计路由"""

    def __init__(self, handler):
        self.handler = handler
        self.app = handler.app

    def get_action_stats(self):
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
        self.handler._ok(result)
        self.handler._log_request('GET', '/stats/actions', 200)

    def get_stats_overview(self):
        """GET /api/v1/stats/overview - 获取总览数据"""
        pages = self.app.config.get('launcher', {}).get('pages', [])
        total_actions = sum(len([a for a in p.get('actions', []) if a]) for p in pages)
        total_pages = len(pages)
        total_tokens = len(self.app.tokens)

        self.handler._ok({
            'total_actions': total_actions,
            'total_pages': total_pages,
            'total_tokens': total_tokens,
        })
        self.handler._log_request('GET', '/stats/overview', 200)
