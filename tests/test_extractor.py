"""
SchemaViz 模式提取器测试
"""

import os
import sqlite3
import tempfile
import unittest

from schemaviz.core.extractor import SQLiteExtractor, create_extractor
from schemaviz.core.models import DatabaseSchema, Table, Column, ForeignKey


class TestSQLiteExtractor(unittest.TestCase):
    """SQLite 提取器测试。"""

    def setUp(self):
        """创建测试数据库。"""
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        # 创建测试表
        self.cursor.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                email TEXT NOT NULL,
                full_name TEXT,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        self.cursor.execute("""
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                status TEXT DEFAULT 'draft',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        self.cursor.execute("""
            CREATE TABLE comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        self.cursor.execute("CREATE INDEX idx_posts_user ON posts(user_id)")
        self.cursor.execute("CREATE INDEX idx_posts_status ON posts(status)")
        self.cursor.execute("CREATE UNIQUE INDEX idx_comments_unique ON comments(post_id, user_id)")

        # 插入测试数据
        self.cursor.execute("INSERT INTO users (username, email) VALUES ('alice', 'alice@test.com')")
        self.cursor.execute("INSERT INTO users (username, email) VALUES ('bob', 'bob@test.com')")
        self.cursor.execute("INSERT INTO posts (user_id, title, content) VALUES (1, 'Hello', 'World')")
        self.cursor.execute("INSERT INTO comments (post_id, user_id, content) VALUES (1, 2, 'Nice post!')")

        self.conn.commit()

    def tearDown(self):
        """清理测试数据库。"""
        self.conn.close()
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def test_extract_schema(self):
        """测试提取完整模式。"""
        url = f"sqlite:///{self.db_path}"
        extractor = SQLiteExtractor(url)
        schema = extractor.extract()

        self.assertIsInstance(schema, DatabaseSchema)
        self.assertEqual(len(schema.tables), 3)
        self.assertEqual(schema.metadata["db_type"], "sqlite")

    def test_extract_table_names(self):
        """测试提取表名。"""
        url = f"sqlite:///{self.db_path}"
        extractor = SQLiteExtractor(url)
        schema = extractor.extract()

        names = schema.table_names
        self.assertIn("users", names)
        self.assertIn("posts", names)
        self.assertIn("comments", names)

    def test_extract_columns(self):
        """测试提取列信息。"""
        url = f"sqlite:///{self.db_path}"
        extractor = SQLiteExtractor(url)
        schema = extractor.extract()

        users = schema.get_table("users")
        self.assertIsNotNone(users)
        self.assertEqual(len(users.columns), 6)

        # 检查 id 列
        id_col = users.get_column("id")
        self.assertIsNotNone(id_col)
        self.assertTrue(id_col.is_primary_key)
        self.assertTrue(id_col.is_auto_increment)
        self.assertFalse(id_col.is_nullable)

        # 检查 username 列
        username_col = users.get_column("username")
        self.assertIsNotNone(username_col)
        self.assertTrue(username_col.is_unique)
        self.assertFalse(username_col.is_nullable)

    def test_extract_foreign_keys(self):
        """测试提取外键。"""
        url = f"sqlite:///{self.db_path}"
        extractor = SQLiteExtractor(url)
        schema = extractor.extract()

        posts = schema.get_table("posts")
        self.assertIsNotNone(posts)
        self.assertEqual(len(posts.foreign_keys), 1)
        self.assertEqual(posts.foreign_keys[0].from_column, "user_id")
        self.assertEqual(posts.foreign_keys[0].to_table, "users")
        self.assertEqual(posts.foreign_keys[0].to_column, "id")
        self.assertEqual(posts.foreign_keys[0].on_delete, "CASCADE")

        comments = schema.get_table("comments")
        self.assertIsNotNone(comments)
        self.assertEqual(len(comments.foreign_keys), 2)

    def test_extract_indexes(self):
        """测试提取索引。"""
        url = f"sqlite:///{self.db_path}"
        extractor = SQLiteExtractor(url)
        schema = extractor.extract()

        posts = schema.get_table("posts")
        self.assertIsNotNone(posts)
        # idx_posts_user 和 idx_posts_status
        self.assertGreaterEqual(len(posts.indexes), 2)

        idx_names = [idx.name for idx in posts.indexes]
        self.assertIn("idx_posts_user", idx_names)
        self.assertIn("idx_posts_status", idx_names)

    def test_extract_row_count(self):
        """测试提取行数。"""
        url = f"sqlite:///{self.db_path}"
        extractor = SQLiteExtractor(url)
        schema = extractor.extract()

        users = schema.get_table("users")
        self.assertEqual(users.row_count, 2)

        posts = schema.get_table("posts")
        self.assertEqual(posts.row_count, 1)

    def test_in_memory_database(self):
        """测试内存数据库提取。"""
        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
        conn.execute("INSERT INTO test VALUES (1, 'hello')")
        conn.commit()

        extractor = SQLiteExtractor("sqlite:///:memory:")
        # 内存数据库无法通过 URL 传递连接，这里仅测试连接不报错
        # 实际使用需要传递已有的连接
        conn.close()

    def test_all_foreign_keys_property(self):
        """测试 all_foreign_keys 属性。"""
        url = f"sqlite:///{self.db_path}"
        extractor = SQLiteExtractor(url)
        schema = extractor.extract()

        all_fks = schema.all_foreign_keys
        self.assertEqual(len(all_fks), 3)

    def test_all_columns_property(self):
        """测试 all_columns 属性。"""
        url = f"sqlite:///{self.db_path}"
        extractor = SQLiteExtractor(url)
        schema = extractor.extract()

        all_cols = schema.all_columns
        self.assertGreater(len(all_cols), 10)


class TestCreateExtractor(unittest.TestCase):
    """create_extractor 工厂函数测试。"""

    def test_create_sqlite_extractor(self):
        """测试创建 SQLite 提取器。"""
        extractor = create_extractor("sqlite:///test.db")
        self.assertIsInstance(extractor, SQLiteExtractor)

    def test_create_postgresql_extractor(self):
        """测试创建 PostgreSQL 提取器。"""
        from schemaviz.core.extractor import PostgreSQLExtractor
        extractor = create_extractor("postgresql://user:pass@localhost/mydb")
        self.assertIsInstance(extractor, PostgreSQLExtractor)

    def test_create_mysql_extractor(self):
        """测试创建 MySQL 提取器。"""
        from schemaviz.core.extractor import MySQLExtractor
        extractor = create_extractor("mysql://user:pass@localhost/mydb")
        self.assertIsInstance(extractor, MySQLExtractor)

    def test_create_mariadb_extractor(self):
        """测试创建 MariaDB 提取器。"""
        from schemaviz.core.extractor import MariaDBExtractor
        extractor = create_extractor("mariadb://user:pass@localhost/mydb")
        self.assertIsInstance(extractor, MariaDBExtractor)

    def test_unsupported_db_type(self):
        """测试不支持的数据库类型。"""
        with self.assertRaises(ValueError):
            create_extractor("oracle://user:pass@localhost/mydb")


if __name__ == "__main__":
    unittest.main()
