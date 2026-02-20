# Phase 6+ 实施任务清单

## 批次 1：提交 Phase 6 已完成代码 ✅
- [x] 提交 Python 脚本动作核心代码

## 批次 2：整体代码优化
- [ ] platform_api.py — 清理 type_text 逻辑、异常处理、代码风格统一
- [ ] platform_sdk.py — 添加连接断开重连、错误处理
- [ ] script_runner.py — 临时文件清理、路径处理健壮性
- [ ] script_editor.py — 修复 mode 切换布局、高亮性能优化
- [ ] action_dialog.py — 对话框高度自适应 script 类型
- [ ] actions.py — _exec_script 错误处理完善

## 批次 3：Phase 7.3 搜索框 (P1)
- [ ] 新建 src/views/search_bar.py — 搜索/命令输入框组件
- [ ] 修改 src/views/launcher.py — 集成搜索框到面板顶部
- [ ] 模糊匹配动作名称，回车执行

## 批次 4：Phase 7.4 扩展热键 (P1)
- [ ] 修改 src/core/hotkey.py — 支持多热键注册
- [ ] Config 中动作增加 hotkey 字段
- [ ] 修改 action_dialog.py — 添加热键绑定 UI

## 批次 5：Phase 8.4 系统托盘 (P1)
- [ ] 新建 src/core/tray.py — 系统托盘图标
- [ ] 修改 src/app.py — 最小化到托盘、托盘菜单

## 批次 6：Phase 7.1 上下文感知 (P2)
- [ ] 新建 src/core/context.py — 前台窗口检测
- [ ] Config 页面增加 context 字段
- [ ] 弹出面板时自动切换到匹配页

## 批次 7：Phase 8.1 拖拽排序 (P2)
- [ ] 修改 launcher.py — 长按进入编辑模式、拖拽交换位置

## 批次 8：Phase 9.1-9.2 导入导出 (P2)
- [ ] 新建 src/core/package.py — 动作打包/解包
- [ ] 修改 launcher.py — 右键菜单增加导入/导出
