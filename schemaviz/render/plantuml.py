"""
SchemaViz PlantUML 生成器

生成 PlantUML ER 图代码。
"""

from __future__ import annotations

from typing import List

from ..core.models import DatabaseSchema, Table, Column, ForeignKey


class PlantUMLRenderer:
    """PlantUML ER 图渲染器。"""

    def __init__(self, schema: DatabaseSchema):
        """初始化渲染器。

        Args:
            schema: 数据库模式对象
        """
        self.schema = schema

    def render(self) -> str:
        """生成 PlantUML ER 图代码。

        Returns:
            PlantUML 代码字符串
        """
        lines: List[str] = [
            "@startuml",
            "",
            "!theme darkshadow",
            "",
            "skinparam roundCorner 8",
            "skinparam shadowing true",
            "skinparam monochrome false",
            "",
            "skinparam tableHeaderBackgroundColor #334155",
            "skinparam tableBorderColor #475569",
            "skinparam backgroundColor #0f172a",
            "",
            "hide circle",
            "hide empty members",
            "",
        ]

        # 定义实体（表）
        for table in self.schema.tables:
            lines.append(f'entity "{table.name}" as {self._sanitize(table.name)} {{')
            for col in table.columns:
                col_str = self._format_column(col)
                lines.append(f"  {col_str}")
            lines.append("}")
            lines.append("")

        # 定义关系
        for fk in self.schema.all_foreign_keys:
            from_id = self._sanitize(fk.from_table)
            to_id = self._sanitize(fk.to_table)
            from_col = fk.from_column
            to_col = fk.to_column

            # 确定关系类型
            if fk.on_delete == "CASCADE":
                rel = f'{from_id} ||--|{ to_id} : "{from_col} -> {to_col}"'
            elif fk.on_delete == "SET NULL":
                rel = f'{from_id} ||--o{ to_id} : "{from_col} -> {to_col}"'
            else:
                rel = f'{from_id} ||--o{ to_id} : "{from_col} -> {to_col}"'
            lines.append(rel)

        lines.append("")
        lines.append("@enduml")
        return "\n".join(lines)

    def render_simple(self) -> str:
        """生成简化的 PlantUML 图（仅表名和关系）。

        Returns:
            PlantUML 代码字符串
        """
        lines: List[str] = [
            "@startuml",
            "",
            "!theme darkshadow",
            "skinparam backgroundColor #0f172a",
            "skinparam arrowColor #64748b",
            "skinparam entityBackgroundColor #1e293b",
            "skinparam entityBorderColor #475569",
            "skinparam entityFontColor #e2e8f0",
            "",
            "hide circle",
            "",
        ]

        for table in self.schema.tables:
            lines.append(f'entity "{table.name}" as {self._sanitize(table.name)}')

        lines.append("")

        for fk in self.schema.all_foreign_keys:
            from_id = self._sanitize(fk.from_table)
            to_id = self._sanitize(fk.to_table)
            lines.append(f'{from_id} --> {to_id} : "{fk.from_column}"')

        lines.append("")
        lines.append("@enduml")
        return "\n".join(lines)

    def render_json_schema(self) -> str:
        """生成 PlantUML JSON 模式图。

        Returns:
            PlantUML JSON 模式代码字符串
        """
        lines: List[str] = [
            "@startuml",
            "",
            "!theme darkshadow",
            "skinparam backgroundColor #0f172a",
            "",
        ]

        for table in self.schema.tables:
            lines.append(f'object "{table.name}" as {self._sanitize(table.name)} {{')
            for col in table.columns:
                type_str = col.data_type
                if col.is_primary_key:
                    type_str = f"[PK] {type_str}"
                elif not col.is_nullable:
                    type_str = f"[NN] {type_str}"
                lines.append(f'  {col.name} = {type_str}')
            lines.append("}")
            lines.append("")

        for fk in self.schema.all_foreign_keys:
            from_id = self._sanitize(fk.from_table)
            to_id = self._sanitize(fk.to_table)
            lines.append(f'{from_id} --> {to_id} : "{fk.from_column} -> {fk.to_column}"')

        lines.append("")
        lines.append("@enduml")
        return "\n".join(lines)

    def _format_column(self, col: Column) -> str:
        """格式化列为 PlantUML 语法。

        Args:
            col: 列对象

        Returns:
            PlantUML 列定义字符串
        """
        parts: List[str] = []

        # 键标记
        if col.is_primary_key:
            parts.append("<<PK>>")
        elif not col.is_nullable:
            parts.append("<<NN>>")

        if col.is_auto_increment:
            parts.append("<<AI>>")

        # 列名和类型
        name = col.name
        if col.is_unique and not col.is_primary_key:
            name = f"*{name}"

        parts.append(f"{name} : {col.data_type}")

        return " ".join(parts)

    @staticmethod
    def _sanitize(name: str) -> str:
        """清理名称以符合 PlantUML 语法。

        Args:
            name: 原始名称

        Returns:
            清理后的名称
        """
        return name.replace(" ", "_").replace("-", "_").replace(".", "_")
