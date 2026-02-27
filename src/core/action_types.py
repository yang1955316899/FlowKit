"""动作类型定义 - 从 dialogs/action_dialog.py 提取"""

# 动作类型定义
ACTION_TYPES = [
    ('app', '应用'),
    ('file', '文件'),
    ('folder', '文件夹'),
    ('url', '网址'),
    ('shell', '脚本'),
    ('snippet', '文本'),
    ('keys', '按键'),
    ('combo', '组合'),
    ('script', 'Python'),
    ('group', '分组'),
]

# target 字段的标签随类型变化
TARGET_LABELS = {
    'app': '程序路径',
    'file': '文件路径',
    'folder': '文件夹路径',
    'url': '网址',
    'shell': '命令',
    'snippet': '要复制的文本',
    'keys': '按键组合 (如 ctrl+shift+a)',
    'combo': '描述',
    'script': '描述',
    'group': '分组描述',
}

# target 字段的占位符文本
PLACEHOLDERS = {
    'app': 'C:\\Program Files\\App\\app.exe',
    'file': 'C:\\path\\to\\file.txt',
    'folder': 'C:\\path\\to\\folder',
    'url': 'https://example.com',
    'shell': 'echo Hello',
    'snippet': '要复制的文本内容',
    'keys': 'ctrl+shift+a',
    'combo': '组合动作描述',
    'script': 'Python 脚本描述',
    'group': '分组名称',
}
