"""步骤类型定义和分类 - 从 dialogs 提取的业务逻辑"""

# 步骤类型定义
STEP_TYPES = [
    ('delay', '延迟', '⏱'),
    ('set_var', '设置变量', '📝'),
    ('get_clipboard', '读剪贴板', '📋'),
    ('set_clipboard', '写剪贴板', '📌'),
    ('mouse_click', '鼠标点击', '🖱'),
    ('mouse_double_click', '鼠标双击', '🖱'),
    ('mouse_move', '鼠标移动', '↗'),
    ('mouse_scroll', '鼠标滚轮', '🔄'),
    ('wait_window', '等待窗口', '🪟'),
    ('wait_pixel', '等待像素', '🎨'),
    ('window_activate', '激活窗口', '🪟'),
    ('if_condition', '条件分支', '🔀'),
    ('loop', '循环', '🔁'),
    # 原有动作类型也可作为步骤
    ('app', '打开应用', '📂'),
    ('keys', '按键', '⌨'),
    ('type_text', '打字', '✍'),
    ('snippet', '文本', '📄'),
    ('toast', '提示', '💬'),
    ('shell', '命令', '💻'),
    ('url', '网址', '🌐'),
    ('http_request', 'HTTP请求', '🔗'),
    ('screenshot', '截图', '📸'),
    ('file_read', '读文件', '📖'),
    ('file_write', '写文件', '✏️'),
]

# 条件分支数据源
CONDITION_SOURCES = [
    ('window_title', '窗口标题'),
    ('process_name', '进程名'),
    ('clipboard', '剪贴板'),
    ('variable', '变量'),
]

# 条件分支操作符
CONDITION_OPS = [
    ('contains', '包含'),
    ('equals', '等于'),
    ('starts_with', '开头是'),
    ('not_contains', '不包含'),
]

# 步骤分类（用于前端 API 和 UI 展示）
PALETTE_CATEGORIES = [
    ('基础', [
        ('delay', '延迟', '⏱', '暂停指定毫秒'),
        ('keys', '按键', '⌨', '模拟键盘输入'),
        ('type_text', '打字', '✍', '逐字符输入文本'),
        ('app', '应用', '📂', '启动程序'),
        ('shell', '命令', '💻', '执行脚本'),
        ('url', '网址', '🌐', '打开链接'),
        ('snippet', '文本', '📄', '输入文本'),
        ('toast', '提示', '💬', '显示提示消息'),
    ]),
    ('鼠标', [
        ('mouse_click', '点击', '🖱', '鼠标点击'),
        ('mouse_double_click', '双击', '🖱', '鼠标双击'),
        ('mouse_move', '移动', '↗', '移动鼠标'),
        ('mouse_scroll', '滚轮', '🔄', '鼠标滚轮'),
    ]),
    ('变量', [
        ('set_var', '赋值', '📝', '设置变量'),
        ('get_clipboard', '读剪贴板', '📋', '获取剪贴板'),
        ('set_clipboard', '写剪贴板', '📌', '设置剪贴板'),
    ]),
    ('数据', [
        ('file_read', '读文件', '📖', '读取文件内容'),
        ('file_write', '写文件', '✏️', '写入文件内容'),
    ]),
    ('系统', [
        ('screenshot', '截图', '📸', '截取屏幕区域'),
    ]),
    ('网络', [
        ('http_request', 'HTTP请求', '🔗', 'GET/POST请求'),
    ]),
    ('流程', [
        ('if_condition', '条件', '🔀', '条件分支'),
        ('loop', '循环', '🔁', '循环执行'),
    ]),
    ('等待', [
        ('wait_window', '窗口', '🪟', '等待窗口'),
        ('wait_pixel', '像素', '🎨', '等待像素'),
        ('window_activate', '激活窗口', '🪟', '激活指定窗口'),
    ]),
]

# 步骤类型颜色映射（用于 UI 主题）
STEP_CATEGORY_COLORS = {
    'delay': 'teal',
    'keys': 'lavender', 'type_text': 'lavender',
    'app': 'peach',
    'shell': 'mauve',
    'url': 'accent2', 'http_request': 'accent2', 'screenshot': 'accent2',
    'snippet': 'pink', 'toast': 'pink',
    'mouse_click': 'peach', 'mouse_move': 'peach',
    'mouse_double_click': 'peach', 'mouse_scroll': 'peach',
    'set_var': 'green', 'get_clipboard': 'green', 'set_clipboard': 'green',
    'file_read': 'green', 'file_write': 'green',
    'if_condition': 'mauve', 'loop': 'mauve',
    'wait_window': 'yellow', 'wait_pixel': 'yellow',
    'window_activate': 'yellow',
}
