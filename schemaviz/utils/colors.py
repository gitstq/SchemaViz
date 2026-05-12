"""
终端颜色工具

提供 ANSI 颜色代码和样式，支持 256 色和真彩色终端。
自动检测终端能力并降级处理。
"""

from __future__ import annotations

import os
import sys
from typing import Optional


def _supports_color() -> bool:
    """检测当前终端是否支持颜色输出。"""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("TERM") in ("dumb", ""):
        return False
    if not hasattr(sys.stdout, "isatty"):
        return False
    if not sys.stdout.isatty():
        if os.environ.get("FORCE_COLOR"):
            return True
        return False
    return True


def _get_color_level() -> int:
    """获取终端颜色级别。

    Returns:
        0 = 不支持颜色
        1 = 基础 16 色
        2 = 256 色
        3 = 真彩色 (24-bit)
    """
    if not _supports_color():
        return 0

    colorterm = os.environ.get("COLORTERM", "").lower()
    if "truecolor" in colorterm or "24bit" in colorterm:
        return 3
    if "256color" in os.environ.get("TERM", ""):
        return 2
    return 1


_COLOR_LEVEL = _get_color_level()


class Colors:
    """ANSI 终端颜色常量。

    所有颜色都定义为 ANSI 转义序列字符串。
    在不支持颜色的终端上，所有值为空字符串。
    """

    # 重置
    RESET = "\033[0m" if _COLOR_LEVEL >= 1 else ""

    # 基础样式
    BOLD = "\033[1m" if _COLOR_LEVEL >= 1 else ""
    DIM = "\033[2m" if _COLOR_LEVEL >= 1 else ""
    UNDERLINE = "\033[4m" if _COLOR_LEVEL >= 1 else ""
    BLINK = "\033[5m" if _COLOR_LEVEL >= 1 else ""
    REVERSE = "\033[7m" if _COLOR_LEVEL >= 1 else ""
    HIDDEN = "\033[8m" if _COLOR_LEVEL >= 1 else ""

    # 前景色 - 标准 16 色
    BLACK = "\033[30m" if _COLOR_LEVEL >= 1 else ""
    RED = "\033[31m" if _COLOR_LEVEL >= 1 else ""
    GREEN = "\033[32m" if _COLOR_LEVEL >= 1 else ""
    YELLOW = "\033[33m" if _COLOR_LEVEL >= 1 else ""
    BLUE = "\033[34m" if _COLOR_LEVEL >= 1 else ""
    MAGENTA = "\033[35m" if _COLOR_LEVEL >= 1 else ""
    CYAN = "\033[36m" if _COLOR_LEVEL >= 1 else ""
    WHITE = "\033[37m" if _COLOR_LEVEL >= 1 else ""

    # 亮色前景
    BRIGHT_BLACK = "\033[90m" if _COLOR_LEVEL >= 1 else ""
    BRIGHT_RED = "\033[91m" if _COLOR_LEVEL >= 1 else ""
    BRIGHT_GREEN = "\033[92m" if _COLOR_LEVEL >= 1 else ""
    BRIGHT_YELLOW = "\033[93m" if _COLOR_LEVEL >= 1 else ""
    BRIGHT_BLUE = "\033[94m" if _COLOR_LEVEL >= 1 else ""
    BRIGHT_MAGENTA = "\033[95m" if _COLOR_LEVEL >= 1 else ""
    BRIGHT_CYAN = "\033[96m" if _COLOR_LEVEL >= 1 else ""
    BRIGHT_WHITE = "\033[97m" if _COLOR_LEVEL >= 1 else ""

    # 背景色
    BG_BLACK = "\033[40m" if _COLOR_LEVEL >= 1 else ""
    BG_RED = "\033[41m" if _COLOR_LEVEL >= 1 else ""
    BG_GREEN = "\033[42m" if _COLOR_LEVEL >= 1 else ""
    BG_YELLOW = "\033[43m" if _COLOR_LEVEL >= 1 else ""
    BG_BLUE = "\033[44m" if _COLOR_LEVEL >= 1 else ""
    BG_MAGENTA = "\033[45m" if _COLOR_LEVEL >= 1 else ""
    BG_CYAN = "\033[46m" if _COLOR_LEVEL >= 1 else ""
    BG_WHITE = "\033[47m" if _COLOR_LEVEL >= 1 else ""

    @staticmethod
    def rgb(r: int, g: int, b: int) -> str:
        """生成真彩色 ANSI 转义序列。

        Args:
            r: 红色分量 (0-255)
            g: 绿色分量 (0-255)
            b: 蓝色分量 (0-255)

        Returns:
            ANSI 转义序列字符串
        """
        if _COLOR_LEVEL < 3:
            return ""
        return f"\033[38;2;{r};{g};{b}m"

    @staticmethod
    def bg_rgb(r: int, g: int, b: int) -> str:
        """生成真彩色背景 ANSI 转义序列。

        Args:
            r: 红色分量 (0-255)
            g: 绿色分量 (0-255)
            b: 蓝色分量 (0-255)

        Returns:
            ANSI 转义序列字符串
        """
        if _COLOR_LEVEL < 3:
            return ""
        return f"\033[48;2;{r};{g};{b}m"

    @staticmethod
    def color_256(code: int) -> str:
        """生成 256 色 ANSI 转义序列。

        Args:
            code: 256 色代码 (0-255)

        Returns:
            ANSI 转义序列字符串
        """
        if _COLOR_LEVEL < 2:
            return ""
        return f"\033[38;5;{code}m"

    @staticmethod
    def bg_256(code: int) -> str:
        """生成 256 色背景 ANSI 转义序列。

        Args:
            code: 256 色代码 (0-255)

        Returns:
            ANSI 转义序列字符串
        """
        if _COLOR_LEVEL < 2:
            return ""
        return f"\033[48;5;{code}m"


class Style:
    """预定义的样式组合，用于常见场景。"""

    # 标题样式
    TITLE = f"{Colors.BOLD}{Colors.BRIGHT_CYAN}"
    SUBTITLE = f"{Colors.BOLD}{Colors.BRIGHT_BLUE}"
    HEADING = f"{Colors.BOLD}{Colors.BRIGHT_WHITE}"

    # 状态样式
    SUCCESS = f"{Colors.BRIGHT_GREEN}"
    ERROR = f"{Colors.BRIGHT_RED}"
    WARNING = f"{Colors.BRIGHT_YELLOW}"
    INFO = f"{Colors.BRIGHT_BLUE}"

    # 数据类型样式
    TYPE_INTEGER = f"{Colors.BRIGHT_YELLOW}"
    TYPE_TEXT = f"{Colors.BRIGHT_GREEN}"
    TYPE_FLOAT = f"{Colors.BRIGHT_MAGENTA}"
    TYPE_BOOLEAN = f"{Colors.BRIGHT_CYAN}"
    TYPE_DATETIME = f"{Colors.BRIGHT_BLUE}"
    TYPE_BINARY = f"{Colors.BRIGHT_RED}"
    TYPE_OTHER = f"{Colors.WHITE}"

    # 约束样式
    PRIMARY_KEY = f"{Colors.BOLD}{Colors.BRIGHT_YELLOW}"
    FOREIGN_KEY = f"{Colors.BRIGHT_CYAN}"
    UNIQUE = f"{Colors.BRIGHT_MAGENTA}"
    NOT_NULL = f"{Colors.BRIGHT_RED}"
    NULLABLE = f"{Colors.DIM}{Colors.WHITE}"

    # 差异样式
    DIFF_ADDED = f"{Colors.BRIGHT_GREEN}"
    DIFF_REMOVED = f"{Colors.BRIGHT_RED}"
    DIFF_MODIFIED = f"{Colors.BRIGHT_YELLOW}"
    DIFF_UNCHANGED = f"{Colors.DIM}"

    @staticmethod
    def apply(text: str, style: str) -> str:
        """将样式应用到文本。

        Args:
            text: 要着色的文本
            style: ANSI 样式字符串

        Returns:
            带有样式和重置序列的文本
        """
        return f"{style}{text}{Colors.RESET}"

    @staticmethod
    def colorize_type(data_type: str) -> str:
        """根据数据类型返回着色后的类型字符串。

        Args:
            data_type: SQL 数据类型字符串

        Returns:
            着色后的类型字符串
        """
        dt = data_type.upper()
        if any(t in dt for t in ("INT", "SERIAL", "BIGINT", "SMALLINT", "TINYINT")):
            return Style.apply(data_type, Style.TYPE_INTEGER)
        elif any(t in dt for t in ("TEXT", "CHAR", "VARCHAR", "CLOB", "BLOB")):
            return Style.apply(data_type, Style.TYPE_TEXT)
        elif any(t in dt for t in ("FLOAT", "DOUBLE", "REAL", "DECIMAL", "NUMERIC")):
            return Style.apply(data_type, Style.TYPE_FLOAT)
        elif any(t in dt for t in ("BOOL", "BOOLEAN", "BIT")):
            return Style.apply(data_type, Style.TYPE_BOOLEAN)
        elif any(t in dt for t in ("DATE", "TIME", "TIMESTAMP", "DATETIME")):
            return Style.apply(data_type, Style.TYPE_DATETIME)
        elif any(t in dt for t in ("BINARY", "BYTEA", "BLOB", "IMAGE")):
            return Style.apply(data_type, Style.TYPE_BINARY)
        return Style.apply(data_type, Style.TYPE_OTHER)
