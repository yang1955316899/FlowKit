"""Emoji 图标注册表"""

# 常用 emoji 图标，按分类组织
ICON_CATEGORIES = {
    'Apps': [
        ('💻', 'Computer'), ('📝', 'Editor'), ('🌐', 'Browser'), ('📁', 'Folder'),
        ('📂', 'Open Folder'), ('🔧', 'Settings'), ('⚙️', 'Gear'), ('🛠️', 'Tools'),
        ('📊', 'Chart'), ('📈', 'Graph'), ('🎮', 'Game'), ('🎵', 'Music'),
        ('🎬', 'Video'), ('📷', 'Camera'), ('🖥️', 'Desktop'), ('📱', 'Phone'),
    ],
    'Actions': [
        ('▶️', 'Play'), ('⏸️', 'Pause'), ('⏹️', 'Stop'), ('🔄', 'Refresh'),
        ('⬆️', 'Upload'), ('⬇️', 'Download'), ('📋', 'Clipboard'), ('✂️', 'Cut'),
        ('📌', 'Pin'), ('🔗', 'Link'), ('🔍', 'Search'), ('💾', 'Save'),
        ('🗑️', 'Delete'), ('✏️', 'Edit'), ('➕', 'Add'), ('➖', 'Remove'),
    ],
    'Dev': [
        ('🐍', 'Python'), ('☕', 'Java'), ('🦀', 'Rust'), ('💎', 'Ruby'),
        ('🐳', 'Docker'), ('🔥', 'Firebase'), ('☁️', 'Cloud'), ('🗄️', 'Database'),
        ('🔑', 'Key'), ('🔒', 'Lock'), ('🔓', 'Unlock'), ('🐛', 'Bug'),
        ('🧪', 'Test'), ('📦', 'Package'), ('🚀', 'Deploy'), ('⚡', 'Fast'),
    ],
    'Symbols': [
        ('⭐', 'Star'), ('❤️', 'Heart'), ('💡', 'Idea'), ('🎯', 'Target'),
        ('🏠', 'Home'), ('📧', 'Email'), ('💬', 'Chat'), ('🔔', 'Bell'),
        ('⚠️', 'Warning'), ('❌', 'Error'), ('✅', 'Check'), ('ℹ️', 'Info'),
        ('🕐', 'Clock'), ('📅', 'Calendar'), ('🌙', 'Moon'), ('☀️', 'Sun'),
    ],
}

# 扁平列表
ALL_ICONS = []
for cat, icons in ICON_CATEGORIES.items():
    for emoji, name in icons:
        ALL_ICONS.append((emoji, name, cat))
