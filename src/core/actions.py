"""操作执行引擎"""

import os
import time
import ctypes
import ctypes.wintypes
import subprocess
import webbrowser
import threading
from ..utils.logger import get_logger
from ..utils.clipboard import set_text as clipboard_set_text
from ..utils.keyboard import parse_keys, send_keys

logger = get_logger('executor')


class ActionExecutor:
    """执行各类快捷操作"""

    def __init__(self, root=None, theme=None):
        self._root = root
        self._theme = theme
        self._on_feedback = None  # callback(msg) for toast
        self._api_server = None
        self._script_runner = None
        self._stats = None

    def set_feedback_callback(self, cb):
        self._on_feedback = cb

    def set_stats(self, stats):
        """注入统计实例"""
        self._stats = stats

    def set_api_server(self, server):
        """注入平台 API 服务实例"""
        self._api_server = server
        if server:
            from .script_runner import ScriptRunner
            self._script_runner = ScriptRunner(api_port=server.port)

    def execute(self, action: dict):
        """按 type 分发执行"""
        if not action:
            logger.warning("Empty action, skipping")
            return
        # 记录统计
        if self._stats and action.get('id'):
            self._stats.record(action['id'])
        t = action.get('type', '')
        logger.info(f"Executing action: {action.get('label', 'unnamed')} (type={t})")
        handler = {
            'app': self._exec_app,
            'file': self._exec_file,
            'folder': self._exec_folder,
            'url': self._exec_url,
            'shell': self._exec_shell,
            'snippet': self._exec_snippet,
            'keys': self._exec_keys,
            'combo': self._exec_combo,
            'script': self._exec_script,
        }.get(t)
        if handler:
            threading.Thread(target=handler, args=(action,), daemon=True).start()
        else:
            logger.warning(f"Unknown action type: {t}")

    def _feedback(self, msg: str):
        if self._on_feedback:
            if self._root:
                self._root.after(0, self._on_feedback, msg)
            else:
                # pywebview mode: call directly
                self._on_feedback(msg)

    def _exec_app(self, action: dict):
        """启动应用程序"""
        target = action.get('target', '')
        if not target:
            logger.warning("No target for app action")
            return
        args = action.get('args', '')
        logger.debug(f"Launching app: {target} with args: {args}")
        try:
            if action.get('admin'):
                ctypes.windll.shell32.ShellExecuteW(
                    None, 'runas', target, args, None, 1
                )
                logger.info(f"Launched {target} as admin")
            else:
                if args:
                    ctypes.windll.shell32.ShellExecuteW(
                        None, 'open', target, args, None, 1
                    )
                else:
                    os.startfile(target)
                logger.info(f"Launched {target}")
            self._feedback("已启动!")
        except FileNotFoundError:
            logger.error(f"File not found: {target}")
            self._feedback(f"文件不存在")
        except PermissionError:
            logger.error(f"Permission denied: {target}")
            self._feedback("权限不足")
        except OSError as e:
            logger.error(f"OS error launching {target}: {e}")
            self._feedback(f"系统错误: {e.winerror if hasattr(e, 'winerror') else 'unknown'}")
        except Exception as e:
            logger.error(f"Failed to launch {target}: {e}")
            error_msg = str(e)[:30] if str(e) else "未知错误"
            self._feedback(f"启动失败: {error_msg}")

    def _exec_file(self, action: dict):
        """打开文件"""
        target = action.get('target', '')
        if not target:
            logger.warning("No target for file action")
            return
        logger.debug(f"Opening file: {target}")
        try:
            os.startfile(target)
            logger.info(f"Opened file: {target}")
        except FileNotFoundError:
            logger.error(f"File not found: {target}")
            self._feedback("文件不存在")
        except PermissionError:
            logger.error(f"Permission denied: {target}")
            self._feedback("权限不足")
        except Exception as e:
            logger.error(f"Failed to open file {target}: {e}")
            self._feedback(f"打开失败: {str(e)[:20]}")

    def _exec_folder(self, action: dict):
        """打开文件夹"""
        target = action.get('target', '')
        if not target:
            logger.warning("No target for folder action")
            return
        # Expand environment variables
        target = os.path.expandvars(target)
        logger.debug(f"Opening folder: {target}")
        try:
            os.startfile(target)
            logger.info(f"Opened folder: {target}")
        except FileNotFoundError:
            logger.error(f"Folder not found: {target}")
            self._feedback("文件夹不存在")
        except PermissionError:
            logger.error(f"Permission denied: {target}")
            self._feedback("权限不足")
        except Exception as e:
            logger.error(f"Failed to open folder {target}: {e}")
            self._feedback(f"打开失败: {str(e)[:20]}")

    def _exec_url(self, action: dict):
        """打开 URL"""
        target = action.get('target', '')
        if not target:
            logger.warning("No target for URL action")
            return
        logger.debug(f"Opening URL: {target}")
        try:
            webbrowser.open(target)
            logger.info(f"Opened URL: {target}")
        except Exception as e:
            logger.error(f"Failed to open URL {target}: {e}")

    def _exec_shell(self, action: dict):
        """执行 shell 命令"""
        target = action.get('target', '')
        if not target:
            return
        shell_type = action.get('shell_type', 'cmd')

        if action.get('show_output') and self._root and self._theme:
            self._root.after(0, self._show_shell_output,
                             action.get('label', 'Shell'), target, shell_type)
            return

        if shell_type == 'powershell':
            subprocess.Popen(
                ['powershell', '-Command', target],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        elif shell_type == 'python':
            subprocess.Popen(
                ['python', '-c', target],
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            subprocess.Popen(
                target, shell=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )

    def _show_shell_output(self, title, command, shell_type):
        from ..dialogs.shell_output import ShellOutputDialog
        ShellOutputDialog(self._root, self._theme, title=title,
                          command=command, shell_type=shell_type)

    def _exec_snippet(self, action: dict):
        """复制文本到剪贴板"""
        target = action.get('target', '')
        if not target:
            logger.warning("No target for snippet action")
            return

        if clipboard_set_text(target):
            self._feedback("已复制!")
        else:
            logger.error("Failed to set clipboard")
            self._feedback("复制失败!")

    def _exec_keys(self, action: dict):
        """模拟按键"""
        target = action.get('target', '')
        if not target:
            logger.warning("No target for keys action")
            return

        keys = parse_keys(target)
        if send_keys(keys):
            self._feedback("已发送!")
        else:
            logger.error("Failed to send keys")
            self._feedback("发送失败!")

    def _exec_combo(self, action: dict):
        """顺序执行组合动作（委托给 ComboExecutor）"""
        from .combo_executor import ComboExecutor
        executor = ComboExecutor(self)
        executor.execute(action)

    def _exec_script(self, action: dict):
        """执行 Python 脚本"""
        if not self._script_runner:
            self._feedback("脚本引擎未初始化!")
            return

        mode = action.get('mode', 'inline')
        timeout = action.get('timeout', 30)
        show_output = action.get('show_output', True)

        # 基本校验
        if mode == 'file' and not action.get('path', '').strip():
            self._feedback("未指定脚本文件!")
            return
        if mode == 'inline' and not action.get('code', '').strip():
            self._feedback("脚本代码为空!")
            return

        if show_output and self._root and self._theme:
            self._root.after(0, self._show_script_output, action)
            return

        # 静默执行
        try:
            if mode == 'file':
                result = self._script_runner.run_file(action['path'], timeout=timeout)
            else:
                result = self._script_runner.run(action['code'], timeout=timeout)

            if result.success:
                self._feedback("脚本完成!")
            else:
                self._feedback("脚本失败!")
        except Exception:
            self._feedback("脚本执行异常!")

    def _show_script_output(self, action):
        """在输出窗口中运行脚本"""
        from ..dialogs.shell_output import ShellOutputDialog
        title = action.get('label', '脚本')
        mode = action.get('mode', 'inline')
        timeout = action.get('timeout', 30)

        dlg = ShellOutputDialog(self._root, self._theme, title=title)

        def run():
            try:
                def on_output(line):
                    try:
                        dlg.win.after(0, dlg._append_text, line)
                    except Exception:
                        pass

                if mode == 'file':
                    result = self._script_runner.run_file(
                        action.get('path', ''), timeout=timeout, on_output=on_output)
                else:
                    result = self._script_runner.run(
                        action.get('code', ''), timeout=timeout, on_output=on_output)

                if result.stderr:
                    dlg.win.after(0, dlg._append_text, f'\n{result.stderr}')
                dlg.win.after(0, dlg._set_status, result.returncode)
            except Exception as e:
                try:
                    dlg.win.after(0, dlg._append_text, f'\n执行异常: {e}\n')
                    dlg.win.after(0, dlg._set_status, -1)
                except Exception:
                    pass

        threading.Thread(target=run, daemon=True).start()
