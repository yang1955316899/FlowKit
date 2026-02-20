"""数字格式化工具"""


def format_number(n: int | float) -> str:
    """格式化大数字为 K/M/B 形式"""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(int(n))


def format_tokens(n: int | float) -> str:
    """格式化 Token 数量"""
    return format_number(n)
