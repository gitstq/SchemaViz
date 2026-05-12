"""
SchemaViz 模式提取器

支持从 SQLite、PostgreSQL、MySQL 和 MariaDB 数据库中提取模式信息。
"""

from __future__ import annotations

import sqlite3
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple

from .models import Column, ForeignKey, Index, Table, DatabaseSchema
from ..utils.helpers import parse_connection_string


class SchemaExtractor(ABC):
    """模式提取器基类。

    所有数据库特定的提取器都应继承此类并实现 extract 方法。
    """

    def __init__(self, connection_string: str):
        """初始化提取器。

        Args:
            connection_string: 数据库连接字符串
        """
        self.connection_string = connection_string
        self.connection_info = parse_connection_string(connection_string)
        self._connection = None

    @abstractmethod
    def _connect(self) -> Any:
        """建立数据库连接。

        Returns:
            数据库连接对象
        """
        ...

    @abstractmethod
    def _disconnect(self) -> None:
        """关闭数据库连接。"""
        ...

    @abstractmethod
    def _get_db_version(self) -> str:
        """获取数据库版本信息。

        Returns:
            数据库版本字符串
        """
        ...

    @abstractmethod
    def _extract_tables(self) -> List[Table]:
        """从数据库中提取所有表信息。

        Returns:
            表对象列表
        """
        ...

    def extract(self) -> DatabaseSchema:
        """提取完整的数据库模式。

        Returns:
            DatabaseSchema 对象
        """
        self._connect()
        try:
            version = self._get_db_version()
            tables = self._extract_tables()
            db_name = self.connection_info.get("database") or "unknown"
            schema = DatabaseSchema(
                name=db_name,
                tables=tables,
                metadata={
                    "db_type": self.connection_info["db_type"],
                    "version": version,
                    "extraction_time": datetime.now().isoformat(),
                    "connection_string": self.connection_string,
                },
            )
            return schema
        finally:
            self._disconnect()

    def _execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行 SQL 查询并返回字典列表。

        Args:
            query: SQL 查询语句
            params: 查询参数

        Returns:
            查询结果字典列表
        """
        raise NotImplementedError("子类必须实现 _execute_query 方法")


class SQLiteExtractor(SchemaExtractor):
    """SQLite 数据库模式提取器。"""

    def _connect(self) -> None:
        """建立 SQLite 数据库连接。"""
        path = self.connection_info.get("path", ":memory:")
        self._connection = sqlite3.connect(path)
        self._connection.row_factory = sqlite3.Row

    def _disconnect(self) -> None:
        """关闭 SQLite 连接。"""
        if self._connection:
            self._connection.close()
            self._connection = None

    def _get_db_version(self) -> str:
        """获取 SQLite 版本。"""
        cursor = self._connection.execute("SELECT sqlite_version()")
        return f"SQLite {cursor.fetchone()[0]}"

    def _execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回字典列表。"""
        cursor = self._connection.execute(query, params)
        columns = [description[0] for description in cursor.description] if cursor.description else []
        return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def _extract_tables(self) -> List[Table]:
        """提取 SQLite 表信息。"""
        tables: List[Table] = []

        # 获取所有用户表（排除系统表）
        rows = self._execute_query(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
            "ORDER BY name"
        )

        for row in rows:
            table_name = row["name"]
            table = self._extract_table(table_name)
            if table:
                tables.append(table)

        return tables

    def _extract_table(self, table_name: str) -> Optional[Table]:
        """提取单个表的详细信息。"""
        columns = self._extract_columns(table_name)
        foreign_keys = self._extract_foreign_keys(table_name)
        indexes = self._extract_indexes(table_name)
        row_count = self._get_row_count(table_name)

        return Table(
            name=table_name,
            columns=columns,
            foreign_keys=foreign_keys,
            indexes=indexes,
            row_count=row_count,
        )

    def _extract_columns(self, table_name: str) -> List[Column]:
        """提取表的列信息。"""
        columns: List[Column] = []
        rows = self._execute_query(f"PRAGMA table_info('{table_name}')")

        for row in rows:
            is_pk = bool(row["pk"] > 0)
            col = Column(
                name=row["name"],
                data_type=row["type"] or "TEXT",
                is_nullable=bool(row["notnull"] == 0) and not is_pk,
                is_primary_key=is_pk,
                default_value=row["dflt_value"],
                ordinal_position=row["cid"] + 1,
            )
            columns.append(col)

        # 检查自增属性
        autoinc_rows = self._execute_query(
            f"SELECT name, sql FROM sqlite_master "
            f"WHERE type='table' AND name='{table_name}'"
        )
        if autoinc_rows:
            sql = autoinc_rows[0].get("sql", "")
            if "AUTOINCREMENT" in sql.upper():
                for col in columns:
                    if col.is_primary_key:
                        col.is_auto_increment = True

        # 检查唯一约束（通过索引列表）
        unique_indexes = self._execute_query(
            f"PRAGMA index_list('{table_name}')"
        )
        for idx_row in unique_indexes:
            if idx_row["unique"]:
                idx_name = idx_row["name"]
                idx_info = self._execute_query(
                    f"PRAGMA index_info('{idx_name}')"
                )
                for info_row in idx_info:
                    col_name = info_row["name"]
                    if col_name:
                        for col in columns:
                            if col.name == col_name and not col.is_primary_key:
                                col.is_unique = True

        return columns

    def _extract_foreign_keys(self, table_name: str) -> List[ForeignKey]:
        """提取表的外键信息。"""
        foreign_keys: List[ForeignKey] = []
        rows = self._execute_query(f"PRAGMA foreign_key_list('{table_name}')")

        for row in rows:
            fk = ForeignKey(
                name=f"fk_{table_name}_{row['from']}_{row['table']}",
                from_table=table_name,
                from_column=row["from"],
                to_table=row["table"],
                to_column=row["to"],
                on_update=row.get("on_update", "NO ACTION").upper(),
                on_delete=row.get("on_delete", "NO ACTION").upper(),
            )
            foreign_keys.append(fk)

        return foreign_keys

    def _extract_indexes(self, table_name: str) -> List[Index]:
        """提取表的索引信息。"""
        indexes: List[Index] = []
        rows = self._execute_query(f"PRAGMA index_list('{table_name}')")

        for row in rows:
            index_name = row["name"]
            if index_name.startswith("sqlite_autoindex_"):
                continue

            # 获取索引列
            col_rows = self._execute_query(f"PRAGMA index_info('{index_name}')")
            index_columns = [cr["name"] for cr in col_rows if cr["name"]]

            idx = Index(
                name=index_name,
                table_name=table_name,
                columns=index_columns,
                is_unique=bool(row["unique"]),
                index_type="BTREE",
            )
            indexes.append(idx)

        return indexes

    def _get_row_count(self, table_name: str) -> int:
        """获取表的行数。"""
        try:
            cursor = self._connection.execute(f"SELECT COUNT(*) FROM '{table_name}'")
            return cursor.fetchone()[0]
        except Exception:
            return 0


class PostgreSQLExtractor(SchemaExtractor):
    """PostgreSQL 数据库模式提取器。"""

    def _connect(self) -> None:
        """建立 PostgreSQL 连接。

        注意: PostgreSQL 需要 psycopg2 驱动，这里使用标准库尝试连接。
        如果 psycopg2 不可用，将抛出 ImportError。
        """
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError:
            raise ImportError(
                "PostgreSQL 支持 requires psycopg2 library. "
                "Install it with: pip install psycopg2-binary"
            )

        info = self.connection_info
        self._connection = psycopg2.connect(
            host=info["host"],
            port=info["port"],
            user=info["username"],
            password=info["password"],
            dbname=info["database"],
        )
        self._connection.autocommit = True

    def _disconnect(self) -> None:
        """关闭 PostgreSQL 连接。"""
        if self._connection:
            self._connection.close()
            self._connection = None

    def _get_db_version(self) -> str:
        """获取 PostgreSQL 版本。"""
        cursor = self._connection.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        cursor.close()
        return version

    def _execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回字典列表。"""
        import psycopg2.extras
        cursor = self._connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(query, params)
        results = [dict(row) for row in cursor.fetchall()]
        cursor.close()
        return results

    def _extract_tables(self) -> List[Table]:
        """提取 PostgreSQL 表信息。"""
        tables: List[Table] = []

        # 获取所有用户表
        rows = self._execute_query(
            "SELECT table_schema, table_name, obj_description("
            "  (quote_ident(table_schema) || '.' || quote_ident(table_name))::regclass, 'pg_class'"
            ") as table_comment "
            "FROM information_schema.tables "
            "WHERE table_type = 'BASE TABLE' "
            "AND table_schema NOT IN ('pg_catalog', 'information_schema') "
            "ORDER BY table_schema, table_name"
        )

        for row in rows:
            table_name = row["table_name"]
            schema_name = row["table_schema"]
            comment = row.get("table_comment") or ""

            columns = self._extract_columns(table_name, schema_name)
            foreign_keys = self._extract_foreign_keys(table_name, schema_name)
            indexes = self._extract_indexes(table_name, schema_name)
            row_count = self._get_row_count(table_name, schema_name)

            table = Table(
                name=f"{schema_name}.{table_name}" if schema_name != "public" else table_name,
                columns=columns,
                foreign_keys=foreign_keys,
                indexes=indexes,
                comment=comment or "",
                row_count=row_count,
                schema_name=schema_name,
            )
            tables.append(table)

        return tables

    def _extract_columns(self, table_name: str, schema_name: str = "public") -> List[Column]:
        """提取表的列信息。"""
        columns: List[Column] = []
        rows = self._execute_query(
            "SELECT column_name, data_type, is_nullable, column_default, "
            "character_maximum_length, numeric_precision, numeric_scale, "
            "ordinal_position, col_description("
            "  (quote_ident(%s) || '.' || quote_ident(%s))::regclass, ordinal_position"
            ") as column_comment "
            "FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s "
            "ORDER BY ordinal_position",
            (schema_name, table_name, schema_name, table_name),
        )

        for row in rows:
            data_type = row["data_type"]
            # 构建完整的数据类型字符串
            if row["character_maximum_length"]:
                data_type = f"{data_type}({row['character_maximum_length']})"
            elif row["numeric_precision"] is not None and data_type in (
                "numeric", "decimal"
            ):
                scale = row["numeric_scale"] or 0
                data_type = f"{data_type}({row['numeric_precision']},{scale})"

            # 检查是否自增
            is_auto_increment = False
            default_val = row["column_default"]
            if default_val and "nextval" in str(default_val):
                is_auto_increment = True

            col = Column(
                name=row["column_name"],
                data_type=data_type,
                is_nullable=row["is_nullable"] == "YES",
                default_value=default_val,
                is_auto_increment=is_auto_increment,
                comment=row.get("column_comment") or "",
                ordinal_position=row["ordinal_position"],
            )
            columns.append(col)

        # 获取主键信息
        pk_rows = self._execute_query(
            "SELECT kcu.column_name "
            "FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu "
            "  ON tc.constraint_name = kcu.constraint_name "
            "  AND tc.table_schema = kcu.table_schema "
            "WHERE tc.constraint_type = 'PRIMARY KEY' "
            "AND tc.table_schema = %s AND tc.table_name = %s",
            (schema_name, table_name),
        )
        pk_columns = {r["column_name"] for r in pk_rows}
        for col in columns:
            col.is_primary_key = col.name in pk_columns

        # 获取唯一约束
        uq_rows = self._execute_query(
            "SELECT kcu.column_name "
            "FROM information_schema.table_constraints tc "
            "JOIN information_schema.key_column_usage kcu "
            "  ON tc.constraint_name = kcu.constraint_name "
            "  AND tc.table_schema = kcu.table_schema "
            "WHERE tc.constraint_type = 'UNIQUE' "
            "AND tc.table_schema = %s AND tc.table_name = %s",
            (schema_name, table_name),
        )
        uq_columns = {r["column_name"] for r in uq_rows}
        for col in columns:
            col.is_unique = col.name in uq_columns

        return columns

    def _extract_foreign_keys(self, table_name: str, schema_name: str = "public") -> List[ForeignKey]:
        """提取表的外键信息。"""
        foreign_keys: List[ForeignKey] = []
        rows = self._execute_query(
            "SELECT tc.constraint_name, "
            "  kcu.column_name, "
            "  ccu.table_schema AS foreign_table_schema, "
            "  ccu.table_name AS foreign_table_name, "
            "  ccu.column_name AS foreign_column_name, "
            "  rc.update_rule, "
            "  rc.delete_rule "
            "FROM information_schema.table_constraints AS tc "
            "JOIN information_schema.key_column_usage AS kcu "
            "  ON tc.constraint_name = kcu.constraint_name "
            "  AND tc.table_schema = kcu.table_schema "
            "JOIN information_schema.constraint_column_usage AS ccu "
            "  ON ccu.constraint_name = tc.constraint_name "
            "  AND ccu.table_schema = tc.table_schema "
            "JOIN information_schema.referential_constraints AS rc "
            "  ON rc.constraint_name = tc.constraint_name "
            "WHERE tc.constraint_type = 'FOREIGN KEY' "
            "AND tc.table_schema = %s AND tc.table_name = %s",
            (schema_name, table_name),
        )

        for row in rows:
            to_table = row["foreign_table_name"]
            if row["foreign_table_schema"] != "public":
                to_table = f"{row['foreign_table_schema']}.{to_table}"

            fk = ForeignKey(
                name=row["constraint_name"],
                from_table=table_name,
                from_column=row["column_name"],
                to_table=to_table,
                to_column=row["foreign_column_name"],
                on_update=row.get("update_rule", "NO ACTION").upper(),
                on_delete=row.get("delete_rule", "NO ACTION").upper(),
            )
            foreign_keys.append(fk)

        return foreign_keys

    def _extract_indexes(self, table_name: str, schema_name: str = "public") -> List[Index]:
        """提取表的索引信息。"""
        indexes: List[Index] = []
        rows = self._execute_query(
            "SELECT indexname, indexdef "
            "FROM pg_indexes "
            "WHERE schemaname = %s AND tablename = %s",
            (schema_name, table_name),
        )

        for row in rows:
            index_name = row["indexname"]
            indexdef = row["indexdef"] or ""

            # 跳过主键索引
            if index_name.endswith("_pkey"):
                continue

            # 解析索引列
            is_unique = "UNIQUE " in indexdef.upper()
            index_type = "BTREE"
            if "USING hash" in indexdef.lower():
                index_type = "HASH"
            elif "USING gist" in indexdef.lower():
                index_type = "GIST"
            elif "USING gin" in indexdef.lower():
                index_type = "GIN"
            elif "USING brin" in indexdef.lower():
                index_type = "BRIN"

            # 提取列名
            import re
            col_match = re.search(r"\((.+)\)", indexdef.split("USING")[-1] if "USING" in indexdef else indexdef)
            index_columns = []
            if col_match:
                index_columns = [
                    c.strip().strip('"').split()[0]
                    for c in col_match.group(1).split(",")
                ]

            idx = Index(
                name=index_name,
                table_name=table_name,
                columns=index_columns,
                is_unique=is_unique,
                index_type=index_type,
            )
            indexes.append(idx)

        return indexes

    def _get_row_count(self, table_name: str, schema_name: str = "public") -> int:
        """获取表的估计行数。"""
        try:
            rows = self._execute_query(
                "SELECT reltuples::bigint AS estimate FROM pg_class "
                "WHERE relname = %s AND relnamespace = "
                "(SELECT oid FROM pg_namespace WHERE nspname = %s)",
                (table_name, schema_name),
            )
            if rows and rows[0]["estimate"] >= 0:
                return int(rows[0]["estimate"])
        except Exception:
            pass
        return 0


class MySQLExtractor(SchemaExtractor):
    """MySQL 数据库模式提取器。"""

    def _connect(self) -> None:
        """建立 MySQL 连接。"""
        try:
            import mysql.connector
        except ImportError:
            raise ImportError(
                "MySQL 支持 requires mysql-connector-python library. "
                "Install it with: pip install mysql-connector-python"
            )

        info = self.connection_info
        self._connection = mysql.connector.connect(
            host=info["host"],
            port=info["port"],
            user=info["username"],
            password=info["password"],
            database=info["database"],
        )

    def _disconnect(self) -> None:
        """关闭 MySQL 连接。"""
        if self._connection:
            self._connection.close()
            self._connection = None

    def _get_db_version(self) -> str:
        """获取 MySQL 版本。"""
        cursor = self._connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        cursor.close()
        return f"MySQL {version}"

    def _execute_query(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        """执行查询并返回字典列表。"""
        cursor = self._connection.cursor(dictionary=True)
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return results

    def _extract_tables(self) -> List[Table]:
        """提取 MySQL 表信息。"""
        tables: List[Table] = []
        db_name = self.connection_info["database"]

        rows = self._execute_query(
            "SELECT table_name, table_comment, table_rows "
            "FROM information_schema.tables "
            "WHERE table_schema = %s AND table_type = 'BASE TABLE' "
            "ORDER BY table_name",
            (db_name,),
        )

        for row in rows:
            table_name = row["table_name"]
            columns = self._extract_columns(table_name, db_name)
            foreign_keys = self._extract_foreign_keys(table_name, db_name)
            indexes = self._extract_indexes(table_name, db_name)

            table = Table(
                name=table_name,
                columns=columns,
                foreign_keys=foreign_keys,
                indexes=indexes,
                comment=row.get("table_comment") or "",
                row_count=int(row.get("table_rows") or 0),
            )
            tables.append(table)

        return tables

    def _extract_columns(self, table_name: str, db_name: str) -> List[Column]:
        """提取表的列信息。"""
        columns: List[Column] = []
        rows = self._execute_query(
            "SELECT column_name, column_type, is_nullable, column_default, "
            "column_key, extra, ordinal_position, column_comment "
            "FROM information_schema.columns "
            "WHERE table_schema = %s AND table_name = %s "
            "ORDER BY ordinal_position",
            (db_name, table_name),
        )

        for row in rows:
            col = Column(
                name=row["column_name"],
                data_type=row["column_type"],
                is_nullable=row["is_nullable"] == "YES",
                default_value=row["column_default"],
                is_primary_key=row["column_key"] == "PRI",
                is_unique=row["column_key"] == "UNI",
                is_auto_increment="auto_increment" in (row.get("extra") or "").lower(),
                comment=row.get("column_comment") or "",
                ordinal_position=row["ordinal_position"],
            )
            columns.append(col)

        return columns

    def _extract_foreign_keys(self, table_name: str, db_name: str) -> List[ForeignKey]:
        """提取表的外键信息。"""
        foreign_keys: List[ForeignKey] = []
        rows = self._execute_query(
            "SELECT constraint_name, column_name, "
            "  referenced_table_name, referenced_column_name "
            "FROM information_schema.key_column_usage "
            "WHERE table_schema = %s AND table_name = %s "
            "  AND referenced_table_name IS NOT NULL "
            "ORDER BY ordinal_position",
            (db_name, table_name),
        )

        for row in rows:
            # 获取 ON UPDATE/DELETE 规则
            rule_rows = self._execute_query(
                "SELECT update_rule, delete_rule "
                "FROM information_schema.referential_constraints "
                "WHERE constraint_schema = %s AND constraint_name = %s",
                (db_name, row["constraint_name"]),
            )
            on_update = "NO ACTION"
            on_delete = "NO ACTION"
            if rule_rows:
                on_update = rule_rows[0].get("update_rule", "NO ACTION").upper()
                on_delete = rule_rows[0].get("delete_rule", "NO ACTION").upper()

            fk = ForeignKey(
                name=row["constraint_name"],
                from_table=table_name,
                from_column=row["column_name"],
                to_table=row["referenced_table_name"],
                to_column=row["referenced_column_name"],
                on_update=on_update,
                on_delete=on_delete,
            )
            foreign_keys.append(fk)

        return foreign_keys

    def _extract_indexes(self, table_name: str, db_name: str) -> List[Index]:
        """提取表的索引信息。"""
        indexes: List[Index] = []
        rows = self._execute_query(
            "SELECT index_name, column_name, non_unique, index_type "
            "FROM information_schema.statistics "
            "WHERE table_schema = %s AND table_name = %s "
            "ORDER BY index_name, seq_in_index",
            (db_name, table_name),
        )

        # 按索引名分组
        index_map: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            idx_name = row["index_name"]
            if idx_name == "PRIMARY":
                continue
            if idx_name not in index_map:
                index_map[idx_name] = {
                    "name": idx_name,
                    "table_name": table_name,
                    "columns": [],
                    "is_unique": not bool(row["non_unique"]),
                    "index_type": row["index_type"],
                }
            index_map[idx_name]["columns"].append(row["column_name"])

        for idx_data in index_map.values():
            indexes.append(Index(**idx_data))

        return indexes


class MariaDBExtractor(MySQLExtractor):
    """MariaDB 数据库模式提取器。

    MariaDB 与 MySQL 共享 information_schema，因此大部分逻辑相同。
    此类添加 MariaDB 特有的适配。
    """

    def _get_db_version(self) -> str:
        """获取 MariaDB 版本。"""
        cursor = self._connection.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        cursor.close()
        # MariaDB 版本字符串通常包含 "MariaDB"
        if "mariadb" in version.lower():
            return f"MariaDB {version}"
        return f"MariaDB {version}"

    def _connect(self) -> None:
        """建立 MariaDB 连接。

        MariaDB 可以使用 mysql-connector-python 驱动。
        """
        try:
            import mysql.connector
        except ImportError:
            raise ImportError(
                "MariaDB 支持 requires mysql-connector-python library. "
                "Install it with: pip install mysql-connector-python"
            )

        info = self.connection_info
        self._connection = mysql.connector.connect(
            host=info["host"],
            port=info["port"],
            user=info["username"],
            password=info["password"],
            database=info["database"],
        )


def create_extractor(connection_string: str) -> SchemaExtractor:
    """根据连接字符串自动创建合适的提取器。

    Args:
        connection_string: 数据库连接字符串

    Returns:
        对应数据库类型的 SchemaExtractor 实例

    Raises:
        ValueError: 不支持的数据库类型
    """
    db_type = parse_connection_string(connection_string)["db_type"]

    extractors = {
        "sqlite": SQLiteExtractor,
        "postgresql": PostgreSQLExtractor,
        "mysql": MySQLExtractor,
        "mariadb": MariaDBExtractor,
    }

    extractor_class = extractors.get(db_type)
    if extractor_class is None:
        supported = ", ".join(sorted(extractors.keys()))
        raise ValueError(
            f"不支持的数据库类型: '{db_type}'。支持的类型: {supported}"
        )

    return extractor_class(connection_string)
