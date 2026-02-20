"""脚本执行引擎 — 在隔离子进程中运行用户 Python 脚本"""

import os
import sys
import subprocess
import threading
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ScriptResult:
    """脚本执行结果"""
    success: bool = False
    stdout: str = ''
    stderr: str = ''
    returncode: int = -1


class ScriptRunner:
    """在隔离子进程中执行用户 Python 脚本"""

    def __init__(self, api_port: int = 0):
        self._api_port = api_port
        # SDK 文件路径 — 子进程需要能 import 到
        self._sdk_path = str(Path(__file__).parent)

    def run(self, code: str, timeout: int = 30,
            on_output: callable = None) -> ScriptResult:
        """执行内嵌代码

        Args:
            code: Python 代码字符串
            timeout: 超时秒数
            on_output: 实时输出回调 fn(line: str)
        """
        # 写入临时文件执行（避免 -c 的转义问题）
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False,
                                          encoding='utf-8')
        try:
            # 注入 SDK import 前缀
            wrapper = self._wrap_code(code)
            tmp.write(wrapper)
            tmp.close()
            return self._execute(tmp.name, timeout, on_output)
        finally:
            try:
                os.unlink(tmp.name)
            except Exception:
                pass

    def run_file(self, path: str, timeout: int = 30,
                 on_output: callable = None) -> ScriptResult:
        """执行外部 .py 文件"""
        if not os.path.isfile(path):
            return ScriptResult(success=False, stderr=f'文件不存在: {path}')
        return self._execute(path, timeout, on_output)

    def _wrap_code(self, code: str) -> str:
        """为用户代码添加 SDK import 前缀"""
        return (
            "import sys as _sys\n"
            f"_sys.path.insert(0, {self._sdk_path!r})\n"
            "from platform_sdk import ctx\n"
            "del _sys\n"
            "\n"
            f"{code}\n"
        )

    def _execute(self, script_path: str, timeout: int,
                 on_output: callable = None) -> ScriptResult:
        """实际执行脚本文件"""
        env = os.environ.copy()
        env['MONITOR_API_PORT'] = str(self._api_port)
        # 确保子进程能 import SDK
        env['PYTHONPATH'] = self._sdk_path + os.pathsep + env.get('PYTHONPATH', '')

        try:
            proc = subprocess.Popen(
                [sys.executable, script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
        except Exception as e:
            return ScriptResult(success=False, stderr=str(e))

        stdout_lines = []
        stderr_lines = []

        def read_stdout():
            for line in proc.stdout:
                stdout_lines.append(line)
                if on_output:
                    on_output(line)

        def read_stderr():
            for line in proc.stderr:
                stderr_lines.append(line)
                if on_output:
                    on_output(f'[stderr] {line}')

        t1 = threading.Thread(target=read_stdout, daemon=True)
        t2 = threading.Thread(target=read_stderr, daemon=True)
        t1.start()
        t2.start()

        try:
            proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            return ScriptResult(
                success=False,
                stdout=''.join(stdout_lines),
                stderr=f'脚本超时 ({timeout}s)\n' + ''.join(stderr_lines),
                returncode=-1,
            )

        t1.join(timeout=2)
        t2.join(timeout=2)

        return ScriptResult(
            success=proc.returncode == 0,
            stdout=''.join(stdout_lines),
            stderr=''.join(stderr_lines),
            returncode=proc.returncode,
        )
