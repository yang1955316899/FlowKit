"""路由模块初始化"""

from .tokens import TokenRoutes
from .actions import ActionRoutes
from .stats import StatsRoutes
from .pages import PageRoutes
from .recorder import RecorderRoutes
from .config import ConfigRoutes

__all__ = [
    'TokenRoutes',
    'ActionRoutes',
    'StatsRoutes',
    'PageRoutes',
    'RecorderRoutes',
    'ConfigRoutes',
]
