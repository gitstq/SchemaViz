"""
SchemaViz 核心数据模型

定义数据库模式的所有数据结构，包括列、外键、索引、表和数据库模式。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class Column:
    """表示数据库表中的列。

    Attributes:
        name: 列名
        data_type: 数据类型（如 VARCHAR(255), INTEGER 等）
        is_nullable: 是否允许为 NULL
        is_primary_key: 是否为主键
        default_value: 默认值
        is_unique: 是否有唯一约束
        is_auto_increment: 是否自增
        comment: 列注释
        ordinal_position: 列在表中的位置（从 1 开始）
    """
    name: str
    data_type: str = "TEXT"
    is_nullable: bool = True
    is_primary_key: bool = False
    default_value: Optional[str] = None
    is_unique: bool = False
    is_auto_increment: bool = False
    comment: str = ""
    ordinal_position: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """将列转换为字典。"""
        return asdict(self)

    def __str__(self) -> str:
        nullable = "NULL" if self.is_nullable else "NOT NULL"
        parts = [f"  {self.name} {self.data_type} {nullable}"]
        if self.is_primary_key:
            parts.append("PRIMARY KEY")
        if self.is_auto_increment:
            parts.append("AUTO_INCREMENT")
        if self.is_unique:
            parts.append("UNIQUE")
        if self.default_value is not None:
            parts.append(f"DEFAULT {self.default_value}")
        return " ".join(parts)


@dataclass
class ForeignKey:
    """表示外键约束。

    Attributes:
        name: 外键约束名称
        from_table: 外键所在的表
        from_column: 外键列
        to_table: 引用的目标表
        to_column: 引用的目标列
        on_update: 更新时的行为（CASCADE, SET NULL, RESTRICT, NO ACTION）
        on_delete: 删除时的行为（CASCADE, SET NULL, RESTRICT, NO ACTION）
    """
    name: str = ""
    from_table: str = ""
    from_column: str = ""
    to_table: str = ""
    to_column: str = ""
    on_update: str = "NO ACTION"
    on_delete: str = "NO ACTION"

    def to_dict(self) -> Dict[str, Any]:
        """将外键转换为字典。"""
        return asdict(self)

    def __str__(self) -> str:
        return (f"  FOREIGN KEY ({self.from_column}) "
                f"REFERENCES {self.to_table}({self.to_column}) "
                f"ON UPDATE {self.on_update} ON DELETE {self.on_delete}")


@dataclass
class Index:
    """表示数据库索引。

    Attributes:
        name: 索引名称
        table_name: 索引所在的表
        columns: 索引包含的列列表
        is_unique: 是否为唯一索引
        index_type: 索引类型（BTREE, HASH, FULLTEXT 等）
    """
    name: str = ""
    table_name: str = ""
    columns: List[str] = field(default_factory=list)
    is_unique: bool = False
    index_type: str = "BTREE"

    def to_dict(self) -> Dict[str, Any]:
        """将索引转换为字典。"""
        return asdict(self)

    def __str__(self) -> str:
        unique = "UNIQUE " if self.is_unique else ""
        cols = ", ".join(self.columns)
        return f"  {unique}INDEX {self.name} ({cols}) USING {self.index_type}"


@dataclass
class Table:
    """表示数据库表。

    Attributes:
        name: 表名
        columns: 列列表
        foreign_keys: 外键列表
        indexes: 索引列表
        comment: 表注释
        row_count: 估计的行数
        schema_name: 所属的模式名（用于 PostgreSQL 等支持模式的数据库）
    """
    name: str = ""
    columns: List[Column] = field(default_factory=list)
    foreign_keys: List[ForeignKey] = field(default_factory=list)
    indexes: List[Index] = field(default_factory=list)
    comment: str = ""
    row_count: int = 0
    schema_name: str = ""

    @property
    def primary_key_columns(self) -> List[Column]:
        """获取所有主键列。"""
        return [c for c in self.columns if c.is_primary_key]

    @property
    def column_names(self) -> List[str]:
        """获取所有列名。"""
        return [c.name for c in self.columns]

    def get_column(self, name: str) -> Optional[Column]:
        """根据名称获取列。"""
        for col in self.columns:
            if col.name == name:
                return col
        return None

    def to_dict(self) -> Dict[str, Any]:
        """将表转换为字典。"""
        return {
            "name": self.name,
            "columns": [c.to_dict() for c in self.columns],
            "foreign_keys": [fk.to_dict() for fk in self.foreign_keys],
            "indexes": [idx.to_dict() for idx in self.indexes],
            "comment": self.comment,
            "row_count": self.row_count,
            "schema_name": self.schema_name,
        }

    def __str__(self) -> str:
        lines = [f"TABLE {self.name}"]
        if self.comment:
            lines.append(f"  -- {self.comment}")
        for col in self.columns:
            lines.append(str(col))
        for fk in self.foreign_keys:
            lines.append(str(fk))
        for idx in self.indexes:
            lines.append(str(idx))
        return "\n".join(lines)


@dataclass
class DatabaseSchema:
    """表示完整的数据库模式。

    Attributes:
        name: 数据库名称
        tables: 表列表
        metadata: 数据库元数据
    """
    name: str = ""
    tables: List[Table] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后确保 metadata 中有基本字段。"""
        if "extraction_time" not in self.metadata:
            self.metadata["extraction_time"] = datetime.now().isoformat()
        if "db_type" not in self.metadata:
            self.metadata["db_type"] = "unknown"
        if "version" not in self.metadata:
            self.metadata["version"] = "unknown"

    @property
    def table_names(self) -> List[str]:
        """获取所有表名。"""
        return [t.name for t in self.tables]

    def get_table(self, name: str) -> Optional[Table]:
        """根据名称获取表。"""
        for table in self.tables:
            if table.name == name:
                return table
        return None

    @property
    def all_foreign_keys(self) -> List[ForeignKey]:
        """获取所有外键。"""
        fks: List[ForeignKey] = []
        for table in self.tables:
            fks.extend(table.foreign_keys)
        return fks

    @property
    def all_indexes(self) -> List[Index]:
        """获取所有索引。"""
        indexes: List[Index] = []
        for table in self.tables:
            indexes.extend(table.indexes)
        return indexes

    @property
    def all_columns(self) -> List[Column]:
        """获取所有列。"""
        cols: List[Column] = []
        for table in self.tables:
            cols.extend(table.columns)
        return cols

    def to_dict(self) -> Dict[str, Any]:
        """将数据库模式转换为字典。"""
        return {
            "name": self.name,
            "tables": [t.to_dict() for t in self.tables],
            "metadata": self.metadata,
        }

    def to_json(self, indent: int = 2) -> str:
        """将数据库模式序列化为 JSON 字符串。"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False, default=str)

    def __str__(self) -> str:
        lines = [f"DATABASE: {self.name}", ""]
        for table in self.tables:
            lines.append(str(table))
            lines.append("")
        return "\n".join(lines)
