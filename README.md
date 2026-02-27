# FlowKit

Windows desktop toolkit — Quick Launcher + Visual Flow Orchestrator + API Monitoring Dashboard.

Windows 桌面工具箱 — 快捷启动器 + 可视化流程编排 + API 监控面板。

Pure Python 3.12 + Tkinter Canvas custom-drawn UI, ctypes direct Win32 API calls, zero native widgets, only two dependencies (`requests`, `pyyaml`).

纯 Python 3.12 + Tkinter Canvas 自绘 UI，ctypes 直调 Win32 API，零原生控件，仅两个依赖（`requests`、`pyyaml`）。

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features / 功能

### Quick Launcher / 快捷启动器

Configurable N×M grid supporting 10 action types: app, file, folder, URL, shell command, clipboard snippet, keyboard shortcuts, combo (multi-step macro), script (Python), and group (nested folder). Drag-and-drop reordering, fuzzy search, multi-page switching, and context-aware auto-page-switching based on the foreground process.

可配置 N×M 网格，支持 10 种动作类型（应用/文件/文件夹/URL/Shell/剪贴板/快捷键/组合宏/脚本/分组），拖拽排序、模糊搜索、多页切换、上下文感知（根据前台进程自动切页）。

### Visual Flow Orchestrator / 流程编排器

Three-pane visual editor (palette / canvas / properties) for building automation workflows. Supports variable interpolation `{{var}}`, conditional branching, loops, mouse & keyboard simulation, wait-for-window/pixel, HTTP requests, file I/O, screenshots, and toast notifications. Includes step-by-step debug mode.

三栏可视化编辑器（面板/画布/属性），支持变量插值 `{{var}}`、条件分支、循环、鼠标键盘模拟、等待窗口/像素、HTTP 请求、文件读写、截图、Toast 提示，可逐步调试。

### Record & Replay / 录制回放

Low-level Windows hooks (`WH_KEYBOARD_LL` + `WH_MOUSE_LL`) capture keyboard and mouse events, intelligently merge them, and convert into editable combo steps.

底层钩子（`WH_KEYBOARD_LL` + `WH_MOUSE_LL`）录制键鼠操作，智能合并事件，转为可编辑的组合步骤。

### Token Monitoring / Token 监控

Multi-token overview with daily cost progress bars, plus per-token detail views (cost, request count, token usage, hourly bar charts, recent requests table). Auto-refreshes on a configurable interval.

多 Token 概览（日消费进度条）+ 单 Token 详情（费用/请求数/Token 用量/小时柱状图/最近请求表），自动刷新。

### Platform API & Script SDK / 平台 API & 脚本 SDK

TCP JSON-RPC server exposing 50+ APIs (clipboard, window management, HTTP, UI dialogs, keyboard/mouse, file system, process, registry, network, screen capture, timers). User scripts run in isolated subprocesses and call the main process via `from platform_sdk import ctx`.

TCP JSON-RPC 服务暴露 50+ API（剪贴板/窗口/HTTP/UI/键鼠/文件/进程/注册表/网络/截屏/定时器），用户脚本通过 `from platform_sdk import ctx` 调用。

### Action Store / 动作商店

`.mpkg` format (ZIP archives) for packaging and sharing actions/pages. Supports publish, browse, and install.

`.mpkg` 格式（ZIP）打包动作和页面，支持发布、浏览、安装。

---

## Quick Start / 快速开始

```bash
# Install dependencies / 安装依赖
uv sync

# Run / 启动
python main.py
```

Silent launch (no console window) / 静默启动（无控制台窗口）：

```bash
start_monitor.vbs
```

Auto-start on boot / 开机自启：

```powershell
.\create_startup.ps1
```

## Configuration / 配置

Copy `config.example.yaml` to `config.yaml` and fill in your API endpoint and credentials:

复制 `config.example.yaml` 为 `config.yaml`，填入你的 API 地址和凭据：

```yaml
api:
  base_url: http://your-api-server:port
  tokens:
  - name: My Token
    credential: sk-YOUR_API_KEY_HERE
    daily_limit: 100.0
```

## Project Structure / 项目结构

```
main.py                  # Entry point / 入口
config.example.yaml      # Config template / 配置模板
src/
  app.py                 # Main App class / 主应用类
  core/
    actions.py           # Action executor (10 types) / 动作执行器
    combo_executor.py    # Combo engine (variables, conditions, loops) / 组合引擎
    context.py           # Foreground process detection / 前台进程检测
    hotkey.py            # Global hotkey & mouse hook / 全局热键与鼠标钩子
    platform_api.py      # TCP JSON-RPC server (50+ APIs) / 平台 API 服务
    platform_sdk.py      # Script SDK (ctx.*) / 脚本 SDK
    recorder.py          # Keyboard/mouse recording / 键鼠录制
    window.py            # Window manager (dock, animation) / 窗口管理
    ...
  views/                 # UI views (launcher, overview, detail, settings)
  dialogs/               # Dialog windows (flow editor, combo editor, store...)
  themes/                # Catppuccin dark/light themes / 暗色亮色主题
  widgets/               # Custom canvas widgets / 自绘控件
```

## Tech Stack / 技术栈

- Python 3.12, Tkinter Canvas (fully custom-drawn / 全自绘)
- ctypes Win32 (hotkeys, hooks, tray, clipboard, window management, input simulation, GDI screenshots, registry, multi-monitor DPI)
- `requests` + `pyyaml`
- `uv` package manager

## Themes / 主题

Built-in Catppuccin-style dark and light themes, switchable in settings.

内置 Catppuccin 风格暗色/亮色主题，设置页切换。

## License

MIT
