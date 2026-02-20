"""动作导入/导出 — .mpkg 打包与解包"""

import os
import json
import yaml
import uuid
import zipfile
import tempfile
from pathlib import Path


class ActionPackage:
    """动作包管理器

    .mpkg 格式（实际为 ZIP）：
    ├── action.yaml      # 动作定义（单个动作或整页）
    ├── scripts/          # 脚本文件（type: script + mode: file 时）
    └── icon.png          # 可选图标
    """

    @staticmethod
    def export_action(action: dict, save_path: str) -> bool:
        """导出单个动作为 .mpkg 文件

        Args:
            action: 动作配置字典
            save_path: 保存路径（.mpkg）

        Returns:
            是否成功
        """
        try:
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                # 写入动作定义
                export_data = {
                    'version': 1,
                    'type': 'action',
                    'action': _clean_action(action),
                }
                zf.writestr('action.yaml',
                            yaml.dump(export_data, allow_unicode=True,
                                      default_flow_style=False, sort_keys=False))

                # 如果是脚本动作且引用外部文件，打包脚本
                if action.get('type') == 'script' and action.get('mode') == 'file':
                    script_path = action.get('path', '')
                    if script_path and os.path.isfile(script_path):
                        zf.write(script_path, f'scripts/{os.path.basename(script_path)}')

            return True
        except Exception:
            return False

    @staticmethod
    def export_page(page: dict, save_path: str) -> bool:
        """导出整个页面为 .mpkg 文件

        Args:
            page: 页面配置字典（含 name, actions, context 等）
            save_path: 保存路径

        Returns:
            是否成功
        """
        try:
            with zipfile.ZipFile(save_path, 'w', zipfile.ZIP_DEFLATED) as zf:
                clean_actions = []
                script_files = []

                for action in page.get('actions', []):
                    if action is not None:
                        clean_actions.append(_clean_action(action))
                        # 收集脚本文件
                        if (action.get('type') == 'script'
                                and action.get('mode') == 'file'):
                            sp = action.get('path', '')
                            if sp and os.path.isfile(sp):
                                script_files.append(sp)
                    else:
                        clean_actions.append(None)

                export_data = {
                    'version': 1,
                    'type': 'page',
                    'page': {
                        'name': page.get('name', '未命名'),
                        'context': page.get('context', ''),
                        'actions': clean_actions,
                    },
                }
                zf.writestr('action.yaml',
                            yaml.dump(export_data, allow_unicode=True,
                                      default_flow_style=False, sort_keys=False))

                # 打包脚本文件
                for sp in script_files:
                    zf.write(sp, f'scripts/{os.path.basename(sp)}')

            return True
        except Exception:
            return False

    @staticmethod
    def import_package(mpkg_path: str, scripts_dir: str = None
                       ) -> dict | None:
        """导入 .mpkg 文件

        Args:
            mpkg_path: .mpkg 文件路径
            scripts_dir: 脚本文件解压目标目录（默认为 mpkg 同级 scripts/）

        Returns:
            解析后的数据字典，包含 type ('action'/'page') 和对应内容
            失败返回 None
        """
        try:
            if not zipfile.is_zipfile(mpkg_path):
                return None

            with zipfile.ZipFile(mpkg_path, 'r') as zf:
                # 读取动作定义
                if 'action.yaml' not in zf.namelist():
                    return None

                data = yaml.safe_load(zf.read('action.yaml').decode('utf-8'))
                if not data or data.get('version') != 1:
                    return None

                # 解压脚本文件
                if scripts_dir is None:
                    scripts_dir = str(
                        Path(mpkg_path).parent / 'scripts')

                script_entries = [n for n in zf.namelist()
                                  if n.startswith('scripts/') and not n.endswith('/')]
                if script_entries:
                    os.makedirs(scripts_dir, exist_ok=True)
                    for entry in script_entries:
                        fname = os.path.basename(entry)
                        target = os.path.join(scripts_dir, fname)
                        with open(target, 'wb') as f:
                            f.write(zf.read(entry))

                        # 更新动作中的脚本路径
                        _update_script_paths(data, fname, target)

                # 为导入的动作生成新 ID
                pkg_type = data.get('type', 'action')
                if pkg_type == 'action' and 'action' in data:
                    data['action']['id'] = str(uuid.uuid4())[:8]
                elif pkg_type == 'page' and 'page' in data:
                    for act in data['page'].get('actions', []):
                        if act is not None:
                            act['id'] = str(uuid.uuid4())[:8]

                return data

        except Exception:
            return None


def _clean_action(action: dict) -> dict:
    """清理动作字典，移除内部字段"""
    cleaned = {}
    for k, v in action.items():
        # 跳过内部字段（以 _ 开头的）
        if k.startswith('_'):
            continue
        cleaned[k] = v
    return cleaned


def _update_script_paths(data: dict, filename: str, new_path: str):
    """更新导入数据中的脚本文件路径"""
    pkg_type = data.get('type', 'action')

    if pkg_type == 'action':
        act = data.get('action', {})
        if (act.get('type') == 'script' and act.get('mode') == 'file'
                and os.path.basename(act.get('path', '')) == filename):
            act['path'] = new_path

    elif pkg_type == 'page':
        for act in data.get('page', {}).get('actions', []):
            if act is None:
                continue
            if (act.get('type') == 'script' and act.get('mode') == 'file'
                    and os.path.basename(act.get('path', '')) == filename):
                act['path'] = new_path
