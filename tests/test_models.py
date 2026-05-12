"""
SchemaViz 数据模型测试
"""

import unittest
import json
from schemaviz.core.models import Column, ForeignKey, Index, Table, DatabaseSchema


class TestColumn(unittest.TestCase):
    """Column 模型测试。"""

    def test_create_column_defaults(self):
        """测试默认值创建列。"""
        col = Column(name="id")
        self.assertEqual(col.name, "id")
        self.assertEqual(col.data_type, "TEXT")
        self.assertTrue(col.is_nullable)
        self.assertFalse(col.is_primary_key)
        self.assertIsNone(col.default_value)
        self.assertFalse(col.is_unique)
        self.assertFalse(col.is_auto_increment)
        self.assertEqual(col.comment, "")
        self.assertEqual(col.ordinal_position, 0)

    def test_create_column_full(self):
        """测试完整参数创建列。"""
        col = Column(
            name="email",
            data_type="VARCHAR(255)",
            is_nullable=False,
            is_primary_key=False,
            default_value="'user@example.com'",
            is_unique=True,
            is_auto_increment=False,
            comment="User email address",
            ordinal_position=2,
        )
        self.assertEqual(col.name, "email")
        self.assertEqual(col.data_type, "VARCHAR(255)")
        self.assertFalse(col.is_nullable)
        self.assertTrue(col.is_unique)
        self.assertEqual(col.default_value, "'user@example.com'")
        self.assertEqual(col.comment, "User email address")
        self.assertEqual(col.ordinal_position, 2)

    def test_column_to_dict(self):
        """测试列序列化为字典。"""
        col = Column(name="id", data_type="INTEGER", is_primary_key=True)
        d = col.to_dict()
        self.assertEqual(d["name"], "id")
        self.assertEqual(d["data_type"], "INTEGER")
        self.assertTrue(d["is_primary_key"])

    def test_column_str(self):
        """测试列的字符串表示。"""
        col = Column(
            name="id",
            data_type="INTEGER",
            is_nullable=False,
            is_primary_key=True,
            is_auto_increment=True,
        )
        s = str(col)
        self.assertIn("id", s)
        self.assertIn("INTEGER", s)
        self.assertIn("NOT NULL", s)
        self.assertIn("PRIMARY KEY", s)
        self.assertIn("AUTO_INCREMENT", s)


class TestForeignKey(unittest.TestCase):
    """ForeignKey 模型测试。"""

    def test_create_fk_defaults(self):
        """测试默认值创建外键。"""
        fk = ForeignKey()
        self.assertEqual(fk.name, "")
        self.assertEqual(fk.on_update, "NO ACTION")
        self.assertEqual(fk.on_delete, "NO ACTION")

    def test_create_fk_full(self):
        """测试完整参数创建外键。"""
        fk = ForeignKey(
            name="fk_order_user",
            from_table="orders",
            from_column="user_id",
            to_table="users",
            to_column="id",
            on_update="CASCADE",
            on_delete="SET NULL",
        )
        self.assertEqual(fk.name, "fk_order_user")
        self.assertEqual(fk.from_table, "orders")
        self.assertEqual(fk.from_column, "user_id")
        self.assertEqual(fk.to_table, "users")
        self.assertEqual(fk.to_column, "id")
        self.assertEqual(fk.on_update, "CASCADE")
        self.assertEqual(fk.on_delete, "SET NULL")

    def test_fk_to_dict(self):
        """测试外键序列化。"""
        fk = ForeignKey(from_table="t1", from_column="c1", to_table="t2", to_column="c2")
        d = fk.to_dict()
        self.assertEqual(d["from_table"], "t1")
        self.assertEqual(d["to_table"], "t2")


class TestIndex(unittest.TestCase):
    """Index 模型测试。"""

    def test_create_index(self):
        """测试创建索引。"""
        idx = Index(
            name="idx_user_email",
            table_name="users",
            columns=["email"],
            is_unique=True,
            index_type="BTREE",
        )
        self.assertEqual(idx.name, "idx_user_email")
        self.assertTrue(idx.is_unique)
        self.assertEqual(idx.columns, ["email"])

    def test_index_to_dict(self):
        """测试索引序列化。"""
        idx = Index(name="idx_test", columns=["a", "b"])
        d = idx.to_dict()
        self.assertEqual(d["columns"], ["a", "b"])


class TestTable(unittest.TestCase):
    """Table 模型测试。"""

    def _make_table(self) -> Table:
        """创建测试表。"""
        cols = [
            Column(name="id", data_type="INTEGER", is_primary_key=True, is_nullable=False),
            Column(name="name", data_type="TEXT", is_nullable=False),
            Column(name="email", data_type="VARCHAR(255)", is_nullable=False, is_unique=True),
        ]
        fks = [
            ForeignKey(
                name="fk_test_ref",
                from_table="test_table",
                from_column="ref_id",
                to_table="other_table",
                to_column="id",
            )
        ]
        idxs = [
            Index(name="idx_test_name", table_name="test_table", columns=["name"], is_unique=False)
        ]
        return Table(
            name="test_table",
            columns=cols,
            foreign_keys=fks,
            indexes=idxs,
            comment="A test table",
            row_count=42,
        )

    def test_create_table(self):
        """测试创建表。"""
        table = self._make_table()
        self.assertEqual(table.name, "test_table")
        self.assertEqual(len(table.columns), 3)
        self.assertEqual(len(table.foreign_keys), 1)
        self.assertEqual(len(table.indexes), 1)
        self.assertEqual(table.row_count, 42)

    def test_primary_key_columns(self):
        """测试获取主键列。"""
        table = self._make_table()
        pk_cols = table.primary_key_columns
        self.assertEqual(len(pk_cols), 1)
        self.assertEqual(pk_cols[0].name, "id")

    def test_column_names(self):
        """测试获取列名列表。"""
        table = self._make_table()
        names = table.column_names
        self.assertEqual(names, ["id", "name", "email"])

    def test_get_column(self):
        """测试按名称获取列。"""
        table = self._make_table()
        col = table.get_column("email")
        self.assertIsNotNone(col)
        self.assertEqual(col.data_type, "VARCHAR(255)")

    def test_get_column_not_found(self):
        """测试获取不存在的列。"""
        table = self._make_table()
        col = table.get_column("nonexistent")
        self.assertIsNone(col)

    def test_table_to_dict(self):
        """测试表序列化。"""
        table = self._make_table()
        d = table.to_dict()
        self.assertEqual(d["name"], "test_table")
        self.assertEqual(len(d["columns"]), 3)
        self.assertEqual(len(d["foreign_keys"]), 1)
        self.assertEqual(d["row_count"], 42)

    def test_table_str(self):
        """测试表的字符串表示。"""
        table = self._make_table()
        s = str(table)
        self.assertIn("test_table", s)
        self.assertIn("id", s)
        self.assertIn("FOREIGN KEY", s)
        self.assertIn("INDEX", s)


class TestDatabaseSchema(unittest.TestCase):
    """DatabaseSchema 模型测试。"""

    def _make_schema(self) -> DatabaseSchema:
        """创建测试模式。"""
        t1 = Table(
            name="users",
            columns=[
                Column(name="id", data_type="INTEGER", is_primary_key=True),
                Column(name="name", data_type="TEXT"),
            ],
            row_count=10,
        )
        t2 = Table(
            name="orders",
            columns=[
                Column(name="id", data_type="INTEGER", is_primary_key=True),
                Column(name="user_id", data_type="INTEGER"),
            ],
            foreign_keys=[
                ForeignKey(from_table="orders", from_column="user_id", to_table="users", to_column="id"),
            ],
            row_count=5,
        )
        return DatabaseSchema(
            name="test_db",
            tables=[t1, t2],
            metadata={"db_type": "sqlite", "version": "3.40.0"},
        )

    def test_create_schema(self):
        """测试创建模式。"""
        schema = self._make_schema()
        self.assertEqual(schema.name, "test_db")
        self.assertEqual(len(schema.tables), 2)

    def test_table_names(self):
        """测试获取表名列表。"""
        schema = self._make_schema()
        names = schema.table_names
        self.assertEqual(names, ["users", "orders"])

    def test_get_table(self):
        """测试按名称获取表。"""
        schema = self._make_schema()
        table = schema.get_table("users")
        self.assertIsNotNone(table)
        self.assertEqual(table.row_count, 10)

    def test_all_foreign_keys(self):
        """测试获取所有外键。"""
        schema = self._make_schema()
        fks = schema.all_foreign_keys
        self.assertEqual(len(fks), 1)
        self.assertEqual(fks[0].from_table, "orders")

    def test_all_columns(self):
        """测试获取所有列。"""
        schema = self._make_schema()
        cols = schema.all_columns
        self.assertEqual(len(cols), 4)

    def test_to_dict(self):
        """测试模式序列化。"""
        schema = self._make_schema()
        d = schema.to_dict()
        self.assertEqual(d["name"], "test_db")
        self.assertEqual(len(d["tables"]), 2)

    def test_to_json(self):
        """测试模式 JSON 序列化。"""
        schema = self._make_schema()
        j = schema.to_json()
        data = json.loads(j)
        self.assertEqual(data["name"], "test_db")
        self.assertIn("metadata", data)

    def test_str(self):
        """测试模式的字符串表示。"""
        schema = self._make_schema()
        s = str(schema)
        self.assertIn("DATABASE: test_db", s)
        self.assertIn("users", s)
        self.assertIn("orders", s)


if __name__ == "__main__":
    unittest.main()
