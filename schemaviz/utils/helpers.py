"""
SchemaViz 辅助工具函数
"""

from __future__ import annotations

import os
import re
import shlex
from typing import Tuple, Optional, Dict, Any
from urllib.parse import urlparse, parse_qs


def parse_connection_string(url: str) -> Dict[str, Any]:
    """解析数据库连接字符串。

    支持的格式:
        - sqlite:///path/to/db.sqlite3
        - sqlite:///:memory:
        - postgresql://user:pass@host:port/dbname
        - mysql://user:pass@host:port/dbname
        - mariadb://user:pass@host:port/dbname

    Args:
        url: 数据库连接字符串

    Returns:
        包含连接参数的字典:
            - db_type: 数据库类型 (sqlite, postgresql, mysql, mariadb)
            - host: 主机地址
            - port: 端口号
            - username: 用户名
            - password: 密码
            - database: 数据库名
            - path: 文件路径（仅 SQLite）
    """
    # 处理 SQLite 特殊格式
    if url.startswith("sqlite:///"):
        path = url[len("sqlite:///"):]
        # 如果已经是绝对路径，直接使用；否则基于当前目录解析
        if os.path.isabs(path):
            abs_path = path
        else:
            abs_path = os.path.abspath(path)
        return {
            "db_type": "sqlite",
            "host": "",
            "port": 0,
            "username": "",
            "password": "",
            "database": path,
            "path": abs_path if path != ":memory:" else ":memory:",
        }

    # 处理标准 URL 格式
    parsed = urlparse(url)
    db_type = parsed.scheme.lower()

    # 标准化数据库类型
    if db_type == "postgres":
        db_type = "postgresql"
    elif db_type == "maria":
        db_type = "mariadb"

    port = parsed.port
    if port is None:
        default_ports = {
            "postgresql": 5432,
            "mysql": 3306,
            "mariadb": 3306,
        }
        port = default_ports.get(db_type, 0)

    return {
        "db_type": db_type,
        "host": parsed.hostname or "localhost",
        "port": port,
        "username": parsed.username or "",
        "password": parsed.password or "",
        "database": (parsed.path or "").lstrip("/"),
        "path": "",
    }


def detect_db_type(url: str) -> str:
    """从连接字符串中检测数据库类型。

    Args:
        url: 数据库连接字符串

    Returns:
        数据库类型字符串 (sqlite, postgresql, mysql, mariadb)
    """
    info = parse_connection_string(url)
    return info["db_type"]


def safe_connection_string(url: str) -> str:
    """将连接字符串中的密码隐藏，用于日志输出。

    Args:
        url: 原始连接字符串

    Returns:
        密码被隐藏的连接字符串
    """
    parsed = parse_connection_string(url)
    if parsed["db_type"] == "sqlite":
        return url
    if parsed["password"]:
        return url.replace(f":{parsed['password']}@", ":****@")
    return url


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """截断字符串到指定长度。

    Args:
        text: 原始字符串
        max_length: 最大长度
        suffix: 截断后添加的后缀

    Returns:
        截断后的字符串
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def format_number(n: int) -> str:
    """格式化数字，添加千位分隔符。

    Args:
        n: 要格式化的数字

    Returns:
        带千位分隔符的字符串
    """
    return f"{n:,}"


def get_terminal_size() -> Tuple[int, int]:
    """获取终端尺寸。

    Returns:
        (宽度, 高度) 元组，默认为 (80, 24)
    """
    try:
        size = os.get_terminal_size()
        return (size.columns, size.lines)
    except (OSError, ValueError):
        return (80, 24)


def camel_to_snake(name: str) -> str:
    """将驼峰命名转换为下划线命名。

    Args:
        name: 驼峰命名字符串

    Returns:
        下划线命名字符串
    """
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def normalize_data_type(data_type: str) -> str:
    """标准化数据类型名称。

    将各种数据库特定的类型名称标准化为通用格式。

    Args:
        data_type: 原始数据类型字符串

    Returns:
        标准化后的数据类型字符串
    """
    dt = data_type.strip().upper()
    # 常见别名映射
    aliases = {
        "INT": "INTEGER",
        "INT4": "INTEGER",
        "INT8": "BIGINT",
        "FLOAT4": "REAL",
        "FLOAT8": "DOUBLE PRECISION",
        "BOOL": "BOOLEAN",
        "TIMESTAMPTZ": "TIMESTAMP WITH TIME ZONE",
        "CHARACTER VARYING": "VARCHAR",
    }
    for alias, standard in aliases.items():
        if dt == alias or dt.startswith(alias + "("):
            return dt.replace(alias, standard, 1)
    return dt


def estimate_column_size(data_type: str) -> int:
    """根据数据类型估算列的平均字节大小。

    Args:
        data_type: SQL 数据类型字符串

    Returns:
        估计的平均字节大小
    """
    dt = data_type.upper()
    if any(t in dt for t in ("TINYINT", "SMALLINT")):
        return 2
    elif "INT" in dt:
        return 4
    elif "BIGINT" in dt:
        return 8
    elif any(t in dt for t in ("FLOAT", "REAL")):
        return 4
    elif any(t in dt for t in ("DOUBLE", "DECIMAL", "NUMERIC")):
        return 8
    elif "BOOLEAN" in dt or "BOOL" in dt:
        return 1
    elif "DATE" in dt:
        return 4
    elif "TIMESTAMP" in dt or "DATETIME" in dt:
        return 8
    elif "TIME" in dt:
        return 4
    elif "CHAR" in dt:
        # 提取长度
        match = re.search(r"\((\d+)\)", dt)
        if match:
            return int(match.group(1))
        return 1
    elif "TEXT" in dt or "CLOB" in dt:
        return 256
    elif "BLOB" in dt or "BYTEA" in dt or "BINARY" in dt:
        return 512
    elif "UUID" in dt:
        return 16
    elif "JSON" in dt:
        return 256
    return 64
