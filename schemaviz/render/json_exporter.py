"""
SchemaViz JSON 导出器

将数据库模式导出为结构化的 JSON 格式。
"""

from __future__ import annotations

import json
from typing import Any, Dict

from ..core.models import DatabaseSchema


class JSONExporter:
    """JSON 模式导出器。

    支持完整模式和精简模式两种导出格式。
    """

    def __init__(self, schema: DatabaseSchema):
        """初始化导出器。

        Args:
            schema: 数据库模式对象
        """
        self.schema = schema

    def export(self, indent: int = 2, compact: bool = False) -> str:
        """导出为 JSON 字符串。

        Args:
            indent: 缩进空格数（compact=True 时忽略）
            compact: 是否使用精简模式（仅表名和列名）

        Returns:
            JSON 字符串
        """
        if compact:
            data = self._export_compact()
        else:
            data = self._export_full()

        return json.dumps(data, indent=indent if not compact else None, ensure_ascii=False, default=str)

    def _export_full(self) -> Dict[str, Any]:
        """导出完整的模式信息。

        Returns:
            完整模式字典
        """
        return self.schema.to_dict()

    def _export_compact(self) -> Dict[str, Any]:
        """导出精简的模式信息。

        仅包含表名、列名和类型，不包含约束和索引等详细信息。

        Returns:
            精简模式字典
        """
        tables: list = []
        for table in self.schema.tables:
            columns: list = []
            for col in table.columns:
                columns.append({
                    "name": col.name,
                    "type": col.data_type,
                })
            tables.append({
                "name": table.name,
                "columns": columns,
            })

        return {
            "database": self.schema.name,
            "tables": tables,
        }

    def export_schema_only(self) -> str:
        """仅导出模式结构（DDL-like JSON）。

        Returns:
            DDL 风格的 JSON 字符串
        """
        tables: list = []
        for table in self.schema.tables:
            table_def: Dict[str, Any] = {
                "name": table.name,
                "columns": [],
                "primary_key": [],
                "foreign_keys": [],
                "indexes": [],
            }

            for col in table.columns:
                col_def: Dict[str, Any] = {
                    "name": col.name,
                    "type": col.data_type,
                    "nullable": col.is_nullable,
                }
                if col.default_value is not None:
                    col_def["default"] = col.default_value
                if col.is_auto_increment:
                    col_def["auto_increment"] = True
                table_def["columns"].append(col_def)

                if col.is_primary_key:
                    table_def["primary_key"].append(col.name)

            for fk in table.foreign_keys:
                table_def["foreign_keys"].append({
                    "columns": [fk.from_column],
                    "references": {
                        "table": fk.to_table,
                        "columns": [fk.to_column],
                    },
                    "on_update": fk.on_update,
                    "on_delete": fk.on_delete,
                })

            for idx in table.indexes:
                table_def["indexes"].append({
                    "name": idx.name,
                    "columns": idx.columns,
                    "unique": idx.is_unique,
                    "type": idx.index_type,
                })

            tables.append(table_def)

        data = {
            "database": self.schema.name,
            "tables": tables,
        }

        return json.dumps(data, indent=2, ensure_ascii=False, default=str)
