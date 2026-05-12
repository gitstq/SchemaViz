"""
SchemaViz 模式分析器测试
"""

import os
import sqlite3
import tempfile
import unittest

from schemaviz.core.extractor import SQLiteExtractor
from schemaviz.core.analyzer import SchemaAnalyzer
from schemaviz.core.models import Table, Column, ForeignKey, Index, DatabaseSchema


class TestSchemaAnalyzer(unittest.TestCase):
    """SchemaAnalyzer 测试。"""

    def _create_test_schema(self) -> DatabaseSchema:
        """创建测试用的模式对象。"""
        users = Table(
            name="users",
            columns=[
                Column(name="id", data_type="INTEGER", is_primary_key=True, is_nullable=False),
                Column(name="username", data_type="TEXT", is_nullable=False, is_unique=True),
                Column(name="email", data_type="TEXT", is_nullable=False),
                Column(name="created_at", data_type="TIMESTAMP"),
            ],
            row_count=100,
        )
        posts = Table(
            name="posts",
            columns=[
                Column(name="id", data_type="INTEGER", is_primary_key=True, is_nullable=False),
                Column(name="user_id", data_type="INTEGER", is_nullable=False),
                Column(name="title", data_type="TEXT", is_nullable=False),
                Column(name="content", data_type="TEXT"),
                Column(name="status", data_type="TEXT", default_value="'draft'"),
            ],
            foreign_keys=[
                ForeignKey(from_table="posts", from_column="user_id", to_table="users", to_column="id"),
            ],
            indexes=[
                Index(name="idx_posts_user", table_name="posts", columns=["user_id"]),
            ],
            row_count=500,
        )
        comments = Table(
            name="comments",
            columns=[
                Column(name="id", data_type="INTEGER", is_primary_key=True, is_nullable=False),
                Column(name="post_id", data_type="INTEGER", is_nullable=False),
                Column(name="user_id", data_type="INTEGER", is_nullable=False),
                Column(name="content", data_type="TEXT", is_nullable=False),
            ],
            foreign_keys=[
                ForeignKey(from_table="comments", from_column="post_id", to_table="posts", to_column="id"),
                ForeignKey(from_table="comments", from_column="user_id", to_table="users", to_column="id"),
            ],
            row_count=2000,
        )
        tags = Table(
            name="tags",
            columns=[
                Column(name="id", data_type="INTEGER", is_primary_key=True, is_nullable=False),
                Column(name="name", data_type="TEXT", is_nullable=False, is_unique=True),
            ],
            row_count=20,
        )
        # 孤立表 - 没有任何外键关系
        settings = Table(
            name="settings",
            columns=[
                Column(name="key", data_type="TEXT", is_primary_key=True, is_nullable=False),
                Column(name="value", data_type="TEXT"),
            ],
            row_count=15,
        )

        return DatabaseSchema(
            name="test_blog",
            tables=[users, posts, comments, tags, settings],
            metadata={"db_type": "sqlite"},
        )

    def setUp(self):
        """初始化分析器和测试模式。"""
        self.schema = self._create_test_schema()
        self.analyzer = SchemaAnalyzer()

    def test_get_statistics(self):
        """测试统计信息。"""
        stats = self.analyzer.get_statistics(self.schema)

        self.assertEqual(stats["table_count"], 5)
        self.assertEqual(stats["column_count"], 17)
        self.assertEqual(stats["foreign_key_count"], 3)
        self.assertEqual(stats["index_count"], 1)
        self.assertEqual(stats["primary_key_count"], 5)
        self.assertEqual(stats["total_rows"], 2635)
        self.assertIn("type_distribution", stats)

    def test_find_orphan_tables(self):
        """测试查找孤立表。"""
        orphans = self.analyzer.find_orphan_tables(self.schema)
        orphan_names = [t.name for t in orphans]
        self.assertIn("settings", orphan_names)
        self.assertIn("tags", orphan_names)
        self.assertNotIn("users", orphan_names)
        self.assertNotIn("posts", orphan_names)

    def test_find_root_tables(self):
        """测试查找根表。"""
        roots = self.analyzer.find_root_tables(self.schema)
        root_names = [t.name for t in roots]
        self.assertIn("users", root_names)
        # posts 被 comments 引用，同时也引用了 users，所以不是纯根表

    def test_find_leaf_tables(self):
        """测试查找叶子表。"""
        leaves = self.analyzer.find_leaf_tables(self.schema)
        leaf_names = [t.name for t in leaves]
        self.assertIn("comments", leaf_names)
        # posts 引用了 users，同时也被 comments 引用，所以不是纯叶子表

    def test_find_circular_references_no_cycle(self):
        """测试无循环引用的情况。"""
        cycles = self.analyzer.find_circular_references(self.schema)
        self.assertEqual(len(cycles), 0)

    def test_find_circular_references_with_cycle(self):
        """测试有循环引用的情况。"""
        # 创建有循环的模式
        t1 = Table(
            name="a",
            columns=[Column(name="id", data_type="INTEGER", is_primary_key=True)],
            foreign_keys=[ForeignKey(from_table="a", from_column="id", to_table="b", to_column="id")],
        )
        t2 = Table(
            name="b",
            columns=[Column(name="id", data_type="INTEGER", is_primary_key=True)],
            foreign_keys=[ForeignKey(from_table="b", from_column="id", to_table="a", to_column="id")],
        )
        cycle_schema = DatabaseSchema(name="cycle_db", tables=[t1, t2])
        cycles = self.analyzer.find_circular_references(cycle_schema)
        self.assertGreater(len(cycles), 0)

    def test_get_table_dependency_graph(self):
        """测试依赖关系图。"""
        graph = self.analyzer.get_table_dependency_graph(self.schema)

        self.assertIn("users", graph)
        self.assertEqual(graph["users"], [])
        self.assertIn("posts", graph)
        self.assertIn("users", graph["posts"])
        self.assertIn("comments", graph)
        self.assertIn("posts", graph["comments"])
        self.assertIn("users", graph["comments"])

    def test_topological_sort(self):
        """测试拓扑排序。"""
        order = self.analyzer.topological_sort(self.schema)

        # users 应该在 posts 之前
        self.assertLess(order.index("users"), order.index("posts"))
        # posts 应该在 comments 之前
        self.assertLess(order.index("posts"), order.index("comments"))

    def test_suggest_indexes(self):
        """测试索引建议。"""
        suggestions = self.analyzer.suggest_indexes(self.schema)

        # comments 表的 post_id 和 user_id 有外键但没有索引
        comment_suggestions = [s for s in suggestions if s["table"] == "comments"]
        self.assertGreater(len(comment_suggestions), 0)

        # posts 表的 user_id 已经有索引
        post_suggestions = [s for s in suggestions if s["table"] == "posts" and s["column"] == "user_id"]
        self.assertEqual(len(post_suggestions), 0)

    def test_estimate_storage(self):
        """测试存储估算。"""
        storage = self.analyzer.estimate_storage(self.schema)

        self.assertIn("tables", storage)
        self.assertIn("total_estimated_bytes", storage)
        self.assertIn("total_estimated_mb", storage)
        self.assertGreater(storage["total_estimated_bytes"], 0)

    def test_get_relationship_summary(self):
        """测试关系摘要。"""
        summary = self.analyzer.get_relationship_summary(self.schema)

        self.assertEqual(summary["total_relationships"], 3)
        self.assertGreater(len(summary["one_to_many"]), 0)

    def test_empty_schema(self):
        """测试空模式。"""
        empty_schema = DatabaseSchema(name="empty")
        stats = self.analyzer.get_statistics(empty_schema)
        self.assertEqual(stats["table_count"], 0)
        self.assertEqual(stats["column_count"], 0)

        orphans = self.analyzer.find_orphan_tables(empty_schema)
        self.assertEqual(len(orphans), 0)

        cycles = self.analyzer.find_circular_references(empty_schema)
        self.assertEqual(len(cycles), 0)


class TestSchemaAnalyzerWithRealDB(unittest.TestCase):
    """使用真实 SQLite 数据库的分析器测试。"""

    def setUp(self):
        """创建测试数据库。"""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        c.execute("""
            CREATE TABLE departments (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE employees (
                id INTEGER PRIMARY KEY,
                dept_id INTEGER NOT NULL,
                manager_id INTEGER,
                name TEXT NOT NULL,
                salary REAL,
                FOREIGN KEY (dept_id) REFERENCES departments(id),
                FOREIGN KEY (manager_id) REFERENCES employees(id)
            )
        """)
        c.execute("INSERT INTO departments VALUES (1, 'Engineering'), (2, 'Sales')")
        c.execute("INSERT INTO employees VALUES (1, 1, NULL, 'Alice', 100000)")
        c.execute("INSERT INTO employees VALUES (2, 1, 1, 'Bob', 90000)")
        c.execute("INSERT INTO employees VALUES (3, 2, NULL, 'Charlie', 80000)")
        conn.commit()
        conn.close()

    def tearDown(self):
        """清理。"""
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_analyze_real_db(self):
        """测试分析真实数据库。"""
        url = f"sqlite:///{self.db_path}"
        extractor = SQLiteExtractor(url)
        schema = extractor.extract()

        analyzer = SchemaAnalyzer()
        stats = analyzer.get_statistics(schema)

        self.assertEqual(stats["table_count"], 2)
        self.assertEqual(stats["foreign_key_count"], 2)
        self.assertEqual(stats["total_rows"], 5)

    def test_self_referencing_fk(self):
        """测试自引用外键检测。"""
        url = f"sqlite:///{self.db_path}"
        extractor = SQLiteExtractor(url)
        schema = extractor.extract()

        employees = schema.get_table("employees")
        self.assertIsNotNone(employees)
        fk_tables = [fk.to_table for fk in employees.foreign_keys]
        self.assertIn("employees", fk_tables)
        self.assertIn("departments", fk_tables)


if __name__ == "__main__":
    unittest.main()
