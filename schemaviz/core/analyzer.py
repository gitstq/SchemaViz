"""
SchemaViz 模式分析器

提供数据库模式的统计分析、依赖关系分析和优化建议。
"""

from __future__ import annotations

from collections import defaultdict
from typing import List, Dict, Any, Set, Tuple, Optional

from .models import DatabaseSchema, Table, Column, ForeignKey, Index
from ..utils.helpers import estimate_column_size


class SchemaAnalyzer:
    """数据库模式分析器。

    提供模式统计、依赖图分析、循环检测和索引建议等功能。
    """

    def get_statistics(self, schema: DatabaseSchema) -> Dict[str, Any]:
        """获取模式的完整统计信息。

        Args:
            schema: 数据库模式对象

        Returns:
            包含各种统计指标的字典
        """
        tables = schema.tables
        all_columns = schema.all_columns
        all_fks = schema.all_foreign_keys
        all_indexes = schema.all_indexes

        # 数据类型分布
        type_distribution: Dict[str, int] = defaultdict(int)
        for col in all_columns:
            base_type = col.data_type.split("(")[0].upper()
            type_distribution[base_type] += 1

        # 表大小分布
        table_sizes = [t.row_count for t in tables]
        total_rows = sum(table_sizes)

        # 约束统计
        pk_count = sum(1 for c in all_columns if c.is_primary_key)
        unique_count = sum(1 for c in all_columns if c.is_unique)
        nullable_count = sum(1 for c in all_columns if c.is_nullable)
        auto_inc_count = sum(1 for c in all_columns if c.is_auto_increment)

        # 有外键的表数量
        tables_with_fks = sum(1 for t in tables if t.foreign_keys)
        tables_with_indexes = sum(1 for t in tables if t.indexes)

        # 最大/最小表
        largest_table = max(tables, key=lambda t: t.row_count) if tables else None
        smallest_table = min(tables, key=lambda t: t.row_count) if tables else None
        widest_table = max(tables, key=lambda t: len(t.columns)) if tables else None

        # 平均列数
        avg_columns = (
            sum(len(t.columns) for t in tables) / len(tables) if tables else 0
        )

        return {
            "table_count": len(tables),
            "column_count": len(all_columns),
            "foreign_key_count": len(all_fks),
            "index_count": len(all_indexes),
            "primary_key_count": pk_count,
            "unique_constraint_count": unique_count,
            "nullable_column_count": nullable_count,
            "auto_increment_count": auto_inc_count,
            "tables_with_foreign_keys": tables_with_fks,
            "tables_with_indexes": tables_with_indexes,
            "total_rows": total_rows,
            "avg_columns_per_table": round(avg_columns, 1),
            "type_distribution": dict(type_distribution),
            "largest_table": largest_table.name if largest_table else None,
            "largest_table_rows": largest_table.row_count if largest_table else 0,
            "smallest_table": smallest_table.name if smallest_table else None,
            "smallest_table_rows": smallest_table.row_count if smallest_table else 0,
            "widest_table": widest_table.name if widest_table else None,
            "widest_table_columns": len(widest_table.columns) if widest_table else 0,
        }

    def find_orphan_tables(self, schema: DatabaseSchema) -> List[Table]:
        """查找没有任何外键关系的孤立表。

        孤立表既不引用其他表，也不被其他表引用。

        Args:
            schema: 数据库模式对象

        Returns:
            孤立表列表
        """
        referenced_tables: Set[str] = set()
        referencing_tables: Set[str] = set()

        for fk in schema.all_foreign_keys:
            referenced_tables.add(fk.to_table)
            referencing_tables.add(fk.from_table)

        connected_tables = referenced_tables | referencing_tables
        return [t for t in schema.tables if t.name not in connected_tables]

    def find_root_tables(self, schema: DatabaseSchema) -> List[Table]:
        """查找根表（被其他表引用但不引用其他表的表）。

        Args:
            schema: 数据库模式对象

        Returns:
            根表列表
        """
        referenced_tables: Set[str] = set()
        referencing_tables: Set[str] = set()

        for fk in schema.all_foreign_keys:
            referenced_tables.add(fk.to_table)
            referencing_tables.add(fk.from_table)

        # 根表：被引用但不引用其他表
        root_names = referenced_tables - referencing_tables
        return [t for t in schema.tables if t.name in root_names]

    def find_leaf_tables(self, schema: DatabaseSchema) -> List[Table]:
        """查找叶子表（引用其他表但不被其他表引用的表）。

        Args:
            schema: 数据库模式对象

        Returns:
            叶子表列表
        """
        referenced_tables: Set[str] = set()
        referencing_tables: Set[str] = set()

        for fk in schema.all_foreign_keys:
            referenced_tables.add(fk.to_table)
            referencing_tables.add(fk.from_table)

        # 叶子表：引用其他表但不被引用
        leaf_names = referencing_tables - referenced_tables
        return [t for t in schema.tables if t.name in leaf_names]

    def find_circular_references(self, schema: DatabaseSchema) -> List[List[str]]:
        """检测外键循环依赖。

        使用深度优先搜索检测图中的环。

        Args:
            schema: 数据库模式对象

        Returns:
            循环路径列表，每条路径是一个表名列表
        """
        # 构建邻接表
        graph: Dict[str, Set[str]] = defaultdict(set)
        for fk in schema.all_foreign_keys:
            graph[fk.from_table].add(fk.to_table)

        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        def dfs(node: str) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # 找到环
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            path.pop()
            rec_stack.remove(node)

        for table in schema.table_names:
            if table not in visited:
                dfs(table)

        return cycles

    def get_table_dependency_graph(self, schema: DatabaseSchema) -> Dict[str, List[str]]:
        """获取表的依赖关系图。

        返回每个表及其依赖的表列表（拓扑排序）。

        Args:
            schema: 数据库模式对象

        Returns:
            依赖关系字典 {表名: [依赖的表名列表]}
        """
        graph: Dict[str, List[str]] = {}
        for table in schema.tables:
            dependencies: List[str] = []
            for fk in table.foreign_keys:
                if fk.to_table not in dependencies:
                    dependencies.append(fk.to_table)
            graph[table.name] = dependencies
        return graph

    def topological_sort(self, schema: DatabaseSchema) -> List[str]:
        """对表进行拓扑排序，确定安全的创建/删除顺序。

        Args:
            schema: 数据库模式对象

        Returns:
            拓扑排序后的表名列表
        """
        graph = self.get_table_dependency_graph(schema)
        in_degree: Dict[str, int] = defaultdict(int)
        all_tables = set(schema.table_names)

        # 计算入度
        for table in all_tables:
            if table not in in_degree:
                in_degree[table] = 0
            for dep in graph.get(table, []):
                if dep in all_tables:
                    pass  # dep 被 table 依赖

        # 反转图：从依赖关系构建被依赖关系
        reverse_graph: Dict[str, List[str]] = defaultdict(list)
        for table, deps in graph.items():
            for dep in deps:
                reverse_graph[dep].append(table)

        # 计算入度（被依赖的次数）
        in_degree = {t: 0 for t in all_tables}
        for table, deps in graph.items():
            in_degree[table] = len([d for d in deps if d in all_tables])

        # Kahn 算法
        queue: List[str] = [t for t in all_tables if in_degree[t] == 0]
        queue.sort()
        result: List[str] = []

        while queue:
            node = queue.pop(0)
            result.append(node)
            for neighbor in sorted(reverse_graph.get(node, [])):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
            queue.sort()

        # 如果有循环依赖，添加剩余的表
        remaining = [t for t in all_tables if t not in result]
        result.extend(sorted(remaining))

        return result

    def suggest_indexes(self, schema: DatabaseSchema) -> List[Dict[str, Any]]:
        """建议缺失的索引。

        基于外键列检查是否有对应的索引。

        Args:
            schema: 数据库模式对象

        Returns:
            索引建议列表，每项包含表名、列名和建议原因
        """
        suggestions: List[Dict[str, Any]] = []

        for table in schema.tables:
            # 获取所有已索引的列
            indexed_columns: Set[str] = set()
            for idx in table.indexes:
                for col in idx.columns:
                    indexed_columns.add(col)

            # 检查主键列
            for col in table.primary_key_columns:
                indexed_columns.add(col.name)

            # 检查唯一约束列
            for col in table.columns:
                if col.is_unique:
                    indexed_columns.add(col.name)

            # 检查外键列是否有索引
            for fk in table.foreign_keys:
                if fk.from_column not in indexed_columns:
                    suggestions.append({
                        "table": table.name,
                        "column": fk.from_column,
                        "reason": f"外键列 '{fk.from_column}' 引用 '{fk.to_table}.{fk.to_column}' 但没有索引",
                        "suggested_index": f"idx_{table.name}_{fk.from_column}",
                        "priority": "high",
                    })

            # 检查频繁查询模式的候选列（有唯一约束但不是主键的列）
            for col in table.columns:
                if (col.is_unique and not col.is_primary_key
                        and col.name not in indexed_columns):
                    suggestions.append({
                        "table": table.name,
                        "column": col.name,
                        "reason": f"唯一列 '{col.name}' 没有索引",
                        "suggested_index": f"idx_{table.name}_{col.name}",
                        "priority": "medium",
                    })

        return suggestions

    def estimate_storage(self, schema: DatabaseSchema) -> Dict[str, Any]:
        """估算数据库存储空间。

        基于列类型和行数进行粗略估算。

        Args:
            schema: 数据库模式对象

        Returns:
            存储估算字典
        """
        table_estimates: List[Dict[str, Any]] = []

        for table in schema.tables:
            if not table.columns:
                continue

            # 估算每行大小
            row_size = sum(estimate_column_size(col.data_type) for col in table.columns)
            # 加上一些开销（行头、对齐等）
            row_size = int(row_size * 1.2)

            # 估算表大小
            table_bytes = row_size * table.row_count

            table_estimates.append({
                "table": table.name,
                "row_count": table.row_count,
                "avg_row_size_bytes": row_size,
                "estimated_total_bytes": table_bytes,
                "estimated_total_mb": round(table_bytes / (1024 * 1024), 2),
            })

        total_bytes = sum(t["estimated_total_bytes"] for t in table_estimates)
        total_mb = round(total_bytes / (1024 * 1024), 2)

        return {
            "tables": table_estimates,
            "total_estimated_bytes": total_bytes,
            "total_estimated_mb": total_mb,
            "note": "此为粗略估算值，实际存储大小取决于数据库引擎、压缩、碎片等因素",
        }

    def get_relationship_summary(self, schema: DatabaseSchema) -> Dict[str, Any]:
        """获取表间关系的摘要信息。

        Args:
            schema: 数据库模式对象

        Returns:
            关系摘要字典
        """
        one_to_many: List[Dict[str, str]] = []
        many_to_many: List[Dict[str, str]] = []

        # 构建引用关系图
        ref_count: Dict[str, int] = defaultdict(int)
        for fk in schema.all_foreign_keys:
            ref_count[fk.to_table] += 1

        for fk in schema.all_foreign_keys:
            rel = {
                "from_table": fk.from_table,
                "from_column": fk.from_column,
                "to_table": fk.to_table,
                "to_column": fk.to_column,
            }

            # 简单判断：如果目标表被多个表引用，可能是多对多中间表
            if ref_count[fk.to_table] > 1:
                many_to_many.append(rel)
            else:
                one_to_many.append(rel)

        return {
            "one_to_many": one_to_many,
            "many_to_many": many_to_many,
            "total_relationships": len(schema.all_foreign_keys),
        }
