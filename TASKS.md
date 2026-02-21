# Phase 6+ 实施任务清单

## 批次 1：提交 Phase 6 已完成代码 ✅
- [x] 提交 Python 脚本动作核心代码

## 批次 2：整体代码优化 ✅
- [x] platform_api.py — 清理 type_text 逻辑、异常处理、代码风格统一
- [x] platform_sdk.py — 添加连接断开重连、错误处理
- [x] script_runner.py — 临时文件清理、路径处理健壮性
- [x] script_editor.py — 修复 mode 切换布局、高亮性能优化
- [x] action_dialog.py — 对话框高度自适应 script 类型
- [x] actions.py — _exec_script 错误处理完善

## 批次 3：Phase 7.3 搜索框 (P1) ✅
- [x] 修改 src/views/launcher.py — 集成搜索框到面板顶部
- [x] 模糊匹配动作名称，回车执行

## 批次 4：Phase 7.4 扩展热键 (P1) ✅
- [x] 修改 src/core/hotkey.py — 支持多热键注册
- [x] Config 中动作增加 hotkey 字段
- [x] 修改 action_dialog.py — 添加热键绑定 UI

## 批次 5：Phase 8.4 系统托盘 (P1) ✅
- [x] 新建 src/core/tray.py — 系统托盘图标
- [x] 修改 src/app.py — 最小化到托盘、托盘菜单

## 批次 6：Phase 7.1 上下文感知 (P2) ✅
- [x] 新建 src/core/context.py — 前台窗口检测
- [x] Config 页面增加 context 字段
- [x] 弹出面板时自动切换到匹配页

## 批次 7：Phase 8.1 拖拽排序 (P2) ✅
- [x] 修改 launcher.py — 长按进入编辑模式、拖拽交换位置

## 批次 8：Phase 9.1-9.2 导入导出 (P2) ✅
- [x] 新建 src/core/package.py — 动作打包/解包
- [x] 修改 launcher.py — 右键菜单增加导入/导出

## 批次 9：Phase 8.5 使用统计 (P3) ✅
- [x] 新建 src/core/stats.py — 执行次数/时间记录
- [x] 修改 actions.py — 执行时自动记录统计
- [x] 修改 settings.py — 设置页展示 Top 5 常用动作

## 批次 10：Phase 8.3 自定义主题 (P3) ✅
- [x] 新建 src/themes/light.py — 浅色主题
- [x] 修改 app.py — 主题切换逻辑
- [x] 修改 settings.py — 主题切换 UI

## 批次 11：Phase 8.2 动作分组 (P2) ✅
- [x] 修改 launcher.py — group 类型展开子面板
- [x] 修改 action_dialog.py — 添加 group 类型
- [x] 分组内子动作增删改

## 批次 12：Phase 7.2 文本选中浮窗 (P3) ✅
- [x] 新建 src/core/selection.py — 鼠标抬起检测选中文本
- [x] 新建 src/dialogs/selection_popup.py — 浮窗 UI（复制/搜索/翻译）
- [x] 修改 app.py/settings.py — 集成开关

## 批次 13：Phase 10 — 高级平台 API (P4) ✅
- [x] 扩展 platform_api.py — fs/process/registry/network/screen/timer
- [x] 扩展 platform_sdk.py — 对应客户端 SDK 类

## 批次 14：Phase 9.3-9.4 — 动作商店 (P3) ✅
- [x] 新建 src/core/store.py — 本地商店仓库管理
- [x] 新建 src/dialogs/store_dialog.py — 商店浏览/安装界面
- [x] 新建 src/dialogs/publish_dialog.py — 发布对话框
- [x] 修改 launcher.py — 右键菜单集成商店入口
- [x] 修改 app.py — 初始化商店实例

## 🎉 全部 Phase 6-10 已完成！
