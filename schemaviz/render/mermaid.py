"""
SchemaViz Mermaid 图表生成器

生成 Mermaid ER 图和流程图语法。
"""

from __future__ import annotations

from typing import List, Optional

from ..core.models import DatabaseSchema, Table, Column, ForeignKey


class MermaidRenderer:
    """Mermaid 图表渲染器。

    支持生成 ER 图和流程图两种格式。
    """

    def __init__(self, schema: DatabaseSchema):
        """初始化渲染器。

        Args:
            schema: 数据库模式对象
        """
        self.schema = schema

    def render_er(self) -> str:
        """生成 Mermaid ER 图语法。

        Returns:
            Mermaid ER 图字符串
        """
        lines: List[str] = ["erDiagram"]
        tables = self.schema.tables

        for table in tables:
            lines.append(f'    {self._sanitize(table.name)} {{')

            for col in table.columns:
                col_type = self._map_type(col.data_type)
                constraints: List[str] = []
                if col.is_primary_key:
                    constraints.append("PK")
                if col.is_unique:
                    constraints.append("UK")
                if not col.is_nullable:
                    constraints.append("NN")

                key_str = ""
                if constraints:
                    key_str = " " + ", ".join(constraints)

                col_def = f'        {col_type} {self._sanitize(col.name)}{key_str}'
                lines.append(col_def)

            lines.append("    }")
            lines.append("")

        # 添加关系
        for fk in self.schema.all_foreign_keys:
            from_tbl = self._sanitize(fk.from_table)
            to_tbl = self._sanitize(fk.to_table)
            from_col = self._sanitize(fk.from_column)
            to_col = self._sanitize(fk.to_column)

            # 确定关系类型
            rel_type = "||--o{"
            if fk.on_delete == "CASCADE":
                rel_type = "||--|{"
            elif fk.on_delete == "SET NULL":
                rel_type = "||--o{"

            lines.append(f'    {from_tbl} {rel_type} {to_tbl} : "{from_col} -> {to_col}"')

        return "\n".join(lines)

    def render_flowchart(self) -> str:
        """生成 Mermaid 流程图语法，展示外键关系。

        Returns:
            Mermaid 流程图字符串
        """
        lines: List[str] = ["graph LR"]

        # 为每个表创建节点
        for table in self.schema.tables:
            col_list = "\\n".join(
                f"{col.name}: {col.data_type}" for col in table.columns[:5]
            )
            if len(table.columns) > 5:
                col_list += f"\\n...+{len(table.columns) - 5} more"
            lines.append(
                f'    {self._sanitize_id(table.name)}'
                f'["<b>{table.name}</b>\\n({len(table.columns)} cols)"]'
            )

        lines.append("")

        # 添加关系线
        for fk in self.schema.all_foreign_keys:
            from_id = self._sanitize_id(fk.from_table)
            to_id = self._sanitize_id(fk.to_table)
            label = f"{fk.from_column} → {fk.to_column}"
            lines.append(f'    {from_id} -->|"{label}"| {to_id}')

        return "\n".join(lines)

    def render_class_diagram(self) -> str:
        """生成 Mermaid 类图语法。

        Returns:
            Mermaid 类图字符串
        """
        lines: List[str] = ["classDiagram"]

        for table in self.schema.tables:
            lines.append(f'    class {self._sanitize_id(table.name)} {{')
            for col in table.columns:
                type_str = self._map_type(col.data_type)
                prefix = "+" if col.is_primary_key else "-"
                lines.append(f'        {prefix}{col.name} : {type_str}')
            lines.append("    }")
            lines.append("")

        # 添加关系
        for fk in self.schema.all_foreign_keys:
            from_id = self._sanitize_id(fk.from_table)
            to_id = self._sanitize_id(fk.to_table)
            lines.append(f'    {from_id} --> {to_id} : {fk.from_column}')

        return "\n".join(lines)

    @staticmethod
    def _sanitize(name: str) -> str:
        """清理名称以符合 Mermaid 语法。

        Args:
            name: 原始名称

        Returns:
            清理后的名称
        """
        return name.replace(" ", "_").replace("-", "_").replace(".", "_")

    @staticmethod
    def _sanitize_id(name: str) -> str:
        """清理名称用于 Mermaid 节点 ID。

        Args:
            name: 原始名称

        Returns:
            清理后的 ID
        """
        return MermaidRenderer._sanitize(name).lower()

    @staticmethod
    def _map_type(data_type: str) -> str:
        """将数据库类型映射为 Mermaid 支持的类型。

        Args:
            data_type: SQL 数据类型

        Returns:
            Mermaid 类型字符串
        """
        dt = data_type.upper()
        if any(t in dt for t in ("INT", "SERIAL", "BIGINT", "SMALLINT", "TINYINT")):
            return "int"
        elif any(t in dt for t in ("FLOAT", "DOUBLE", "REAL", "DECIMAL", "NUMERIC")):
            return "float"
        elif any(t in dt for t in ("BOOL", "BOOLEAN", "BIT")):
            return "boolean"
        elif any(t in dt for t in ("DATE", "TIME", "TIMESTAMP", "DATETIME")):
            return "datetime"
        elif any(t in dt for t in ("TEXT", "CHAR", "VARCHAR", "CLOB")):
            return "string"
        elif any(t in dt for t in ("BLOB", "BYTEA", "BINARY")):
            return "blob"
        return "string"
