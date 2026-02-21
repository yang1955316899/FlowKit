"""动作商店 — 本地仓库 + 分享功能"""

import json
import os
import time
import uuid
from pathlib import Path
from .package import ActionPackage


class ActionStore:
    """动作商店管理器

    使用本地 JSON 文件作为仓库索引，.mpkg 文件作为动作包。
    支持发布（上传到本地仓库）和浏览/安装。
    """

    def __init__(self, store_dir: str = None):
        self._dir = store_dir or str(
            Path(__file__).parent.parent.parent / 'store')
        self._index_path = os.path.join(self._dir, 'index.json')
        self._packages_dir = os.path.join(self._dir, 'packages')
        os.makedirs(self._packages_dir, exist_ok=True)
        self._index: list[dict] = []
        self._load_index()

    def _load_index(self):
        try:
            if os.path.exists(self._index_path):
                with open(self._index_path, 'r', encoding='utf-8') as f:
                    self._index = json.load(f)
        except Exception:
            self._index = []

    def _save_index(self):
        try:
            with open(self._index_path, 'w', encoding='utf-8') as f:
                json.dump(self._index, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def list_items(self, category: str = None, keyword: str = None) -> list[dict]:
        """浏览商店列表

        Returns:
            [{id, name, description, author, category, icon, downloads, created}, ...]
        """
        items = self._index
        if category:
            items = [i for i in items if i.get('category') == category]
        if keyword:
            kw = keyword.lower()
            items = [i for i in items
                     if kw in i.get('name', '').lower()
                     or kw in i.get('description', '').lower()]
        return items

    def get_categories(self) -> list[str]:
        """获取所有分类"""
        cats = set()
        for item in self._index:
            cat = item.get('category', '')
            if cat:
                cats.add(cat)
        return sorted(cats)

    def publish(self, action: dict = None, page: dict = None,
                name: str = '', description: str = '',
                author: str = '', category: str = '通用',
                icon: str = '📦') -> str | None:
        """发布动作/页面到商店

        Args:
            action: 单个动作字典（与 page 二选一）
            page: 页面字典
            name: 商店显示名称
            description: 描述
            author: 作者
            category: 分类
            icon: 图标

        Returns:
            发布的 item ID，失败返回 None
        """
        item_id = str(uuid.uuid4())[:8]
        pkg_filename = f'{item_id}.mpkg'
        pkg_path = os.path.join(self._packages_dir, pkg_filename)

        if action:
            ok = ActionPackage.export_action(action, pkg_path)
            pkg_type = 'action'
        elif page:
            ok = ActionPackage.export_page(page, pkg_path)
            pkg_type = 'page'
        else:
            return None

        if not ok:
            return None

        entry = {
            'id': item_id,
            'name': name or (action or {}).get('label', '未命名'),
            'description': description,
            'author': author or '匿名',
            'category': category,
            'icon': icon,
            'type': pkg_type,
            'filename': pkg_filename,
            'downloads': 0,
            'created': time.time(),
        }
        self._index.append(entry)
        self._save_index()
        return item_id

    def install(self, item_id: str, scripts_dir: str = None) -> dict | None:
        """从商店安装动作/页面

        Args:
            item_id: 商店条目 ID
            scripts_dir: 脚本解压目录

        Returns:
            导入的数据字典（同 ActionPackage.import_package 返回值）
        """
        entry = None
        for item in self._index:
            if item.get('id') == item_id:
                entry = item
                break
        if not entry:
            return None

        pkg_path = os.path.join(self._packages_dir, entry['filename'])
        if not os.path.exists(pkg_path):
            return None

        data = ActionPackage.import_package(pkg_path, scripts_dir)
        if data:
            entry['downloads'] = entry.get('downloads', 0) + 1
            self._save_index()
        return data

    def delete(self, item_id: str) -> bool:
        """从商店删除条目"""
        for i, item in enumerate(self._index):
            if item.get('id') == item_id:
                # 删除包文件
                pkg_path = os.path.join(self._packages_dir, item['filename'])
                try:
                    os.remove(pkg_path)
                except Exception:
                    pass
                self._index.pop(i)
                self._save_index()
                return True
        return False

    def get_package_path(self, item_id: str) -> str | None:
        """获取包文件路径（用于分享）"""
        for item in self._index:
            if item.get('id') == item_id:
                path = os.path.join(self._packages_dir, item['filename'])
                if os.path.exists(path):
                    return path
        return None
