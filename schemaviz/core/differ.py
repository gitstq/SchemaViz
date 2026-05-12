"""
SchemaViz 模式差异比较引擎

比较两个数据库模式之间的差异，生成结构化的差异报告。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

from .models import DatabaseSchema, Table, Column, ForeignKey, Index
from ..utils.colors import Colors, Style


@dataclass
class ColumnDiff:
    """列级别的差异。"""
    table_name: str
    column_name: str
    change_type: str  # "added", "removed", "modified"
    old_column: Optional[Column] = None
    new_column: Optional[Column] = None
    changes: Dict[str, Tuple[str, str]] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {
            "table_name": self.table_name,
            "column_name": self.column_name,
            "change_type": self.change_type,
            "old_column": self.old_column.to_dict() if self.old_column else None,
            "new_column": self.new_column.to_dict() if self.new_column else None,
            "changes": self.changes,
        }


@dataclass
class TableDiff:
    """表级别的差异。"""
    table_name: str
    change_type: str  # "added", "removed", "modified"
    old_table: Optional[Table] = None
    new_table: Optional[Table] = None
    column_diffs: List[ColumnDiff] = field(default_factory=list)
    added_fks: List[ForeignKey] = field(default_factory=list)
    removed_fks: List[ForeignKey] = field(default_factory=list)
    added_indexes: List[Index] = field(default_factory=list)
    removed_indexes: List[Index] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {
            "table_name": self.table_name,
            "change_type": self.change_type,
            "old_table": self.old_table.to_dict() if self.old_table else None,
            "new_table": self.new_table.to_dict() if self.new_table else None,
            "column_diffs": [cd.to_dict() for cd in self.column_diffs],
            "added_fks": [fk.to_dict() for fk in self.added_fks],
            "removed_fks": [fk.to_dict() for fk in self.removed_fks],
            "added_indexes": [idx.to_dict() for idx in self.added_indexes],
            "removed_indexes": [idx.to_dict() for idx in self.removed_indexes],
        }


@dataclass
class SchemaDiff:
    """两个数据库模式之间的完整差异。"""
    schema1_name: str = ""
    schema2_name: str = ""
    table_diffs: List[TableDiff] = field(default_factory=list)
    added_tables: List[Table] = field(default_factory=list)
    removed_tables: List[Table] = field(default_factory=list)
    modified_tables: List[TableDiff] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """计算差异摘要。"""
        self.added_tables = [td.new_table for td in self.table_diffs if td.change_type == "added" and td.new_table]
        self.removed_tables = [td.old_table for td in self.table_diffs if td.change_type == "removed" and td.old_table]
        self.modified_tables = [td for td in self.table_diffs if td.change_type == "modified"]

        added_cols = sum(
            len([cd for cd in td.column_diffs if cd.change_type == "added"])
            for td in self.modified_tables
        )
        removed_cols = sum(
            len([cd for cd in td.column_diffs if cd.change_type == "removed"])
            for td in self.modified_tables
        )
        modified_cols = sum(
            len([cd for cd in td.column_diffs if cd.change_type == "modified"])
            for td in self.modified_tables
        )
        added_fks = sum(len(td.added_fks) for td in self.modified_tables)
        removed_fks = sum(len(td.removed_fks) for td in self.modified_tables)

        self.summary = {
            "added_tables": len(self.added_tables),
            "removed_tables": len(self.removed_tables),
            "modified_tables": len(self.modified_tables),
            "added_columns": added_cols,
            "removed_columns": removed_cols,
            "modified_columns": modified_cols,
            "added_foreign_keys": added_fks,
            "removed_foreign_keys": removed_fks,
        }

    @property
    def has_differences(self) -> bool:
        """是否存在差异。"""
        return any(v > 0 for v in self.summary.values())

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。"""
        return {
            "schema1_name": self.schema1_name,
            "schema2_name": self.schema2_name,
            "summary": self.summary,
            "table_diffs": [td.to_dict() for td in self.table_diffs],
        }

    def to_terminal(self) -> str:
        """生成终端彩色差异报告。"""
        lines: List[str] = []
        w = Colors.RESET

        # 标题
        lines.append(f"\n{Style.TITLE}{'=' * 60}{w}")
        lines.append(f"{Style.TITLE}  SchemaViz - 模式差异报告{w}")
        lines.append(f"{Style.TITLE}{'=' * 60}{w}")
        lines.append(f"  {Style.INFO}源:{w} {self.schema1_name}")
        lines.append(f"  {Style.INFO}目标:{w} {self.schema2_name}")
        lines.append("")

        # 摘要
        lines.append(f"  {Style.HEADING}--- 差异摘要 ---{w}")
        s = self.summary
        lines.append(f"  {Style.DIFF_ADDED}+ 新增表: {s['added_tables']}{w}")
        lines.append(f"  {Style.DIFF_REMOVED}- 删除表: {s['removed_tables']}{w}")
        lines.append(f"  {Style.DIFF_MODIFIED}~ 修改表: {s['modified_tables']}{w}")
        lines.append(f"  {Style.DIFF_ADDED}+ 新增列: {s['added_columns']}{w}")
        lines.append(f"  {Style.DIFF_REMOVED}- 删除列: {s['removed_columns']}{w}")
        lines.append(f"  {Style.DIFF_MODIFIED}~ 修改列: {s['modified_columns']}{w}")
        lines.append(f"  {Style.DIFF_ADDED}+ 新增外键: {s['added_foreign_keys']}{w}")
        lines.append(f"  {Style.DIFF_REMOVED}- 删除外键: {s['removed_foreign_keys']}{w}")
        lines.append("")

        if not self.has_differences:
            lines.append(f"  {Style.SUCCESS}两个模式完全相同，没有差异。{w}")
            return "\n".join(lines)

        # 详细差异
        lines.append(f"  {Style.HEADING}--- 详细差异 ---{w}")

        for td in self.table_diffs:
            if td.change_type == "added":
                lines.append(f"\n  {Style.DIFF_ADDED}+ TABLE {td.table_name}{w}")
                if td.new_table:
                    for col in td.new_table.columns:
                        lines.append(f"    {Style.DIFF_ADDED}+ {col.name} {col.data_type}{w}")

            elif td.change_type == "removed":
                lines.append(f"\n  {Style.DIFF_REMOVED}- TABLE {td.table_name}{w}")
                if td.old_table:
                    for col in td.old_table.columns:
                        lines.append(f"    {Style.DIFF_REMOVED}- {col.name} {col.data_type}{w}")

            elif td.change_type == "modified":
                lines.append(f"\n  {Style.DIFF_MODIFIED}~ TABLE {td.table_name}{w}")

                for cd in td.column_diffs:
                    if cd.change_type == "added":
                        lines.append(
                            f"    {Style.DIFF_ADDED}+ {cd.column_name} "
                            f"{cd.new_column.data_type if cd.new_column else ''}{w}"
                        )
                    elif cd.change_type == "removed":
                        lines.append(
                            f"    {Style.DIFF_REMOVED}- {cd.column_name} "
                            f"{cd.old_column.data_type if cd.old_column else ''}{w}"
                        )
                    elif cd.change_type == "modified":
                        lines.append(f"    {Style.DIFF_MODIFIED}~ {cd.column_name}{w}")
                        for field_name, (old_val, new_val) in cd.changes.items():
                            lines.append(
                                f"      {Style.DIFF_REMOVED}- {field_name}: {old_val}{w}"
                                f" {Style.DIFF_ADDED}+ {field_name}: {new_val}{w}"
                            )

                for fk in td.added_fks:
                    lines.append(
                        f"    {Style.DIFF_ADDED}+ FK {fk.from_column} -> "
                        f"{fk.to_table}.{fk.to_column}{w}"
                    )
                for fk in td.removed_fks:
                    lines.append(
                        f"    {Style.DIFF_REMOVED}- FK {fk.from_column} -> "
                        f"{fk.to_table}.{fk.to_column}{w}"
                    )

        lines.append(f"\n{Style.TITLE}{'=' * 60}{w}")
        return "\n".join(lines)


class SchemaDiffer:
    """数据库模式差异比较器。"""

    def diff(self, schema1: DatabaseSchema, schema2: DatabaseSchema) -> SchemaDiff:
        """比较两个数据库模式。

        Args:
            schema1: 源模式（旧）
            schema2: 目标模式（新）

        Returns:
            SchemaDiff 差异结果
        """
        table_diffs: List[TableDiff] = []

        tables1 = {t.name: t for t in schema1.tables}
        tables2 = {t.name: t for t in schema2.tables}

        all_table_names = sorted(set(list(tables1.keys()) + list(tables2.keys())))

        for name in all_table_names:
            if name not in tables1:
                # 新增的表
                table_diffs.append(TableDiff(
                    table_name=name,
                    change_type="added",
                    new_table=tables2[name],
                ))
            elif name not in tables2:
                # 删除的表
                table_diffs.append(TableDiff(
                    table_name=name,
                    change_type="removed",
                    old_table=tables1[name],
                ))
            else:
                # 修改的表
                table_diff = self._diff_tables(tables1[name], tables2[name])
                if table_diff:
                    table_diffs.append(table_diff)

        return SchemaDiff(
            schema1_name=schema1.name,
            schema2_name=schema2.name,
            table_diffs=table_diffs,
        )

    def _diff_tables(self, table1: Table, table2: Table) -> Optional[TableDiff]:
        """比较两个表的差异。

        Args:
            table1: 旧表
            table2: 新表

        Returns:
            TableDiff 如果有差异，否则 None
        """
        column_diffs = self._diff_columns(table1, table2)
        added_fks, removed_fks = self._diff_foreign_keys(table1, table2)
        added_indexes, removed_indexes = self._diff_indexes(table1, table2)

        has_changes = (
            column_diffs or added_fks or removed_fks
            or added_indexes or removed_indexes
        )

        if not has_changes:
            return None

        return TableDiff(
            table_name=table1.name,
            change_type="modified",
            old_table=table1,
            new_table=table2,
            column_diffs=column_diffs,
            added_fks=added_fks,
            removed_fks=removed_fks,
            added_indexes=added_indexes,
            removed_indexes=removed_indexes,
        )

    def _diff_columns(
        self, table1: Table, table2: Table
    ) -> List[ColumnDiff]:
        """比较两个表的列差异。

        Args:
            table1: 旧表
            table2: 新表

        Returns:
            ColumnDiff 列表
        """
        diffs: List[ColumnDiff] = []
        cols1 = {c.name: c for c in table1.columns}
        cols2 = {c.name: c for c in table2.columns}

        all_col_names = sorted(set(list(cols1.keys()) + list(cols2.keys())))

        for name in all_col_names:
            if name not in cols1:
                diffs.append(ColumnDiff(
                    table_name=table1.name,
                    column_name=name,
                    change_type="added",
                    new_column=cols2[name],
                ))
            elif name not in cols2:
                diffs.append(ColumnDiff(
                    table_name=table1.name,
                    column_name=name,
                    change_type="removed",
                    old_column=cols1[name],
                ))
            else:
                # 检查列属性变化
                changes = self._compare_column_properties(cols1[name], cols2[name])
                if changes:
                    diffs.append(ColumnDiff(
                        table_name=table1.name,
                        column_name=name,
                        change_type="modified",
                        old_column=cols1[name],
                        new_column=cols2[name],
                        changes=changes,
                    ))

        return diffs

    def _compare_column_properties(
        self, col1: Column, col2: Column
    ) -> Dict[str, Tuple[str, str]]:
        """比较两个列的属性差异。

        Args:
            col1: 旧列
            col2: 新列

        Returns:
            属性变更字典 {属性名: (旧值, 新值)}
        """
        changes: Dict[str, Tuple[str, str]] = {}

        properties = [
            ("data_type", lambda c: c.data_type),
            ("is_nullable", lambda c: str(c.is_nullable)),
            ("default_value", lambda c: str(c.default_value) if c.default_value is not None else "NULL"),
            ("is_primary_key", lambda c: str(c.is_primary_key)),
            ("is_unique", lambda c: str(c.is_unique)),
            ("is_auto_increment", lambda c: str(c.is_auto_increment)),
        ]

        for prop_name, getter in properties:
            old_val = getter(col1)
            new_val = getter(col2)
            if old_val != new_val:
                changes[prop_name] = (old_val, new_val)

        return changes

    def _diff_foreign_keys(
        self, table1: Table, table2: Table
    ) -> Tuple[List[ForeignKey], List[ForeignKey]]:
        """比较两个表的外键差异。

        Args:
            table1: 旧表
            table2: 新表

        Returns:
            (新增的外键列表, 删除的外键列表)
        """
        def fk_key(fk: ForeignKey) -> str:
            return f"{fk.from_column}->{fk.to_table}.{fk.to_column}"

        fks1 = {fk_key(fk): fk for fk in table1.foreign_keys}
        fks2 = {fk_key(fk): fk for fk in table2.foreign_keys}

        added = [fks2[k] for k in fks2 if k not in fks1]
        removed = [fks1[k] for k in fks1 if k not in fks2]

        return added, removed

    def _diff_indexes(
        self, table1: Table, table2: Table
    ) -> Tuple[List[Index], List[Index]]:
        """比较两个表的索引差异。

        Args:
            table1: 旧表
            table2: 新表

        Returns:
            (新增的索引列表, 删除的索引列表)
        """
        def idx_key(idx: Index) -> str:
            return f"{idx.name}({','.join(idx.columns)})"

        idxs1 = {idx_key(idx): idx for idx in table1.indexes}
        idxs2 = {idx_key(idx): idx for idx in table2.indexes}

        added = [idxs2[k] for k in idxs2 if k not in idxs1]
        removed = [idxs1[k] for k in idxs1 if k not in idxs2]

        return added, removed
