# FlowKit

Windows 桌面工具箱 — 快捷启动器 + 可视化流程编排 + API 监控面板。

纯 Python 3.12 + Tkinter Canvas 自绘 UI，ctypes 直调 Win32 API，零原生控件，两个依赖（requests、pyyaml）。

![Python](https://img.shields.io/badge/Python-3.12+-blue)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)
![License](https://img.shields.io/badge/License-MIT-green)

## 功能

**快捷启动器** — 可配置 N×M 网格，支持 10 种动作类型（应用/文件/URL/Shell/快捷键/剪贴板/组合/脚本/分组），拖拽排序、模糊搜索、多页切换、上下文感知（根据前台进程自动切页）。

**流程编排器** — 三栏可视化编辑器（面板/画布/属性），支持变量插值 `{{var}}`、条件分支、循环、鼠标键盘模拟、等待窗口/像素、HTTP 请求、文件读写、截图、Toast 提示。可逐步调试。

**录制回放** — 底层钩子（WH_KEYBOARD_LL + WH_MOUSE_LL）录制键鼠操作，智能合并事件，转为可编辑的组合步骤。

**Token 监控** — 多 Token 概览（日消费进度条）+ 单 Token 详情（费用/请求数/Token 用量/小时柱状图/最近请求表），自动刷新。

**平台 API & 脚本 SDK** — TCP JSON-RPC 服务暴露 50+ API（剪贴板/窗口/HTTP/UI/键鼠/文件/进程/注册表/网络/截屏/定时器），用户脚本通过 `from platform_sdk import ctx` 调用。

**动作商店** — `.mpkg` 格式（ZIP）打包动作和页面，支持发布、浏览、安装。

## 快速开始

```bash
# 安装依赖
uv sync

# 启动
python main.py
```

静默启动（无控制台窗口）：
```bash
start_monitor.vbs
```

开机自启：
```powershell
.\create_startup.ps1
```

## 配置

复制 `config.example.yaml` 为 `config.yaml`，填入你的 API 地址和凭据：

```yaml
api:
  base_url: http://your-api-server:port
  tokens:
  - name: My Token
    credential: sk-YOUR_API_KEY_HERE
    daily_limit: 100.0
```

## 主题

内置 Catppuccin 风格暗色/亮色主题，设置页切换。

## 技术栈

- Python 3.12, Tkinter Canvas 自绘
- ctypes Win32（热键、钩子、托盘、剪贴板、窗口管理、输入模拟、GDI 截屏、注册表、多显示器）
- requests + pyyaml
- uv 包管理

## License

MIT
