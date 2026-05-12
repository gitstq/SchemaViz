"""
SchemaViz CLI 命令解析与处理

提供命令行接口的参数解析和命令执行逻辑。
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from typing import Optional

from . import __version__
from .core.extractor import create_extractor
from .core.models import DatabaseSchema
from .core.analyzer import SchemaAnalyzer
from .core.differ import SchemaDiffer
from .render.html_renderer import HTMLRenderer
from .render.mermaid import MermaidRenderer
from .render.plantuml import PlantUMLRenderer
from .render.json_exporter import JSONExporter
from .render.tui import TUIRenderer
from .utils.colors import Colors, Style


def build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。

    Returns:
        配置好的 ArgumentParser 实例
    """
    parser = argparse.ArgumentParser(
        prog="schemaviz",
        description="SchemaViz - 轻量级终端数据库模式智能可视化引擎",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "示例:\n"
            "  schemaviz extract sqlite:///mydb.sqlite3\n"
            "  schemaviz visualize sqlite:///mydb.sqlite3 -o schema.html\n"
            "  schemaviz export sqlite:///mydb.sqlite3 -f mermaid -o schema.mmd\n"
            "  schemaviz diff sqlite:///old.db sqlite:///new.db\n"
            "  schemaviz analyze sqlite:///mydb.sqlite3\n"
            "  schemaviz demo\n"
        ),
    )
    parser.add_argument("-v", "--version", action="version", version=f"SchemaViz v{__version__}")

    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # extract 命令
    extract_parser = subparsers.add_parser("extract", help="提取并显示数据库模式")
    extract_parser.add_argument("db_url", help="数据库连接字符串")
    extract_parser.add_argument("-t", "--table", help="仅显示指定表的详情")

    # visualize 命令
    viz_parser = subparsers.add_parser("visualize", aliases=["viz"], help="生成交互式 HTML ER 图")
    viz_parser.add_argument("db_url", help="数据库连接字符串")
    viz_parser.add_argument("-o", "--output", default="schema.html", help="输出文件路径 (默认: schema.html)")
    viz_parser.add_argument("--title", default="Database Schema", help="页面标题")

    # export 命令
    export_parser = subparsers.add_parser("export", help="导出模式为指定格式")
    export_parser.add_argument("db_url", help="数据库连接字符串")
    export_parser.add_argument(
        "-f", "--format",
        choices=["mermaid", "plantuml", "json", "html"],
        default="json",
        help="导出格式 (默认: json)",
    )
    export_parser.add_argument("-o", "--output", help="输出文件路径")
    export_parser.add_argument("--compact", action="store_true", help="JSON 精简模式")
    export_parser.add_argument("--mermaid-type", choices=["er", "flowchart", "class"], default="er", help="Mermaid 图表类型")
    export_parser.add_argument("--plantuml-type", choices=["full", "simple", "json"], default="full", help="PlantUML 图表类型")

    # diff 命令
    diff_parser = subparsers.add_parser("diff", help="比较两个数据库模式")
    diff_parser.add_argument("db_url1", help="源数据库连接字符串")
    diff_parser.add_argument("db_url2", help="目标数据库连接字符串")
    diff_parser.add_argument("-o", "--output", help="导出差异报告为 HTML 文件")

    # analyze 命令
    analyze_parser = subparsers.add_parser("analyze", help="分析数据库模式并提供建议")
    analyze_parser.add_argument("db_url", help="数据库连接字符串")

    # demo 命令
    demo_parser = subparsers.add_parser("demo", help="创建演示数据库并可视化")
    demo_parser.add_argument("-o", "--output", default="demo_schema.html", help="输出文件路径 (默认: demo_schema.html)")

    return parser


def cmd_extract(args: argparse.Namespace) -> int:
    """执行 extract 命令。

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    try:
        extractor = create_extractor(args.db_url)
        schema = extractor.extract()
        tui = TUIRenderer(schema)

        if args.table:
            print(tui.render_table_detail(args.table))
        else:
            print(tui.render_dashboard())
        return 0
    except Exception as e:
        print(Style.apply(f"错误: {e}", Style.ERROR), file=sys.stderr)
        return 1


def cmd_visualize(args: argparse.Namespace) -> int:
    """执行 visualize 命令。

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    try:
        extractor = create_extractor(args.db_url)
        schema = extractor.extract()
        renderer = HTMLRenderer(schema)
        html = renderer.render(title=args.title)

        output_path = args.output
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(Style.apply(f"HTML ER 图已生成: {output_path}", Style.SUCCESS))
        print(f"  表数量: {len(schema.tables)}")
        print(f"  外键数量: {len(schema.all_foreign_keys)}")
        return 0
    except Exception as e:
        print(Style.apply(f"错误: {e}", Style.ERROR), file=sys.stderr)
        return 1


def cmd_export(args: argparse.Namespace) -> int:
    """执行 export 命令。

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    try:
        extractor = create_extractor(args.db_url)
        schema = extractor.extract()

        fmt = args.format
        content = ""

        if fmt == "mermaid":
            renderer = MermaidRenderer(schema)
            if args.mermaid_type == "er":
                content = renderer.render_er()
            elif args.mermaid_type == "flowchart":
                content = renderer.render_flowchart()
            elif args.mermaid_type == "class":
                content = renderer.render_class_diagram()
            default_ext = ".mmd"
        elif fmt == "plantuml":
            renderer = PlantUMLRenderer(schema)
            if args.plantuml_type == "full":
                content = renderer.render()
            elif args.plantuml_type == "simple":
                content = renderer.render_simple()
            elif args.plantuml_type == "json":
                content = renderer.render_json_schema()
            default_ext = ".puml"
        elif fmt == "json":
            exporter = JSONExporter(schema)
            if args.compact:
                content = exporter.export(compact=True)
            else:
                content = exporter.export()
            default_ext = ".json"
        elif fmt == "html":
            renderer = HTMLRenderer(schema)
            content = renderer.render()
            default_ext = ".html"
        else:
            print(Style.apply(f"不支持的格式: {fmt}", Style.ERROR), file=sys.stderr)
            return 1

        output_path = args.output
        if not output_path:
            db_name = schema.name or "schema"
            output_path = f"{db_name}{default_ext}"

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(Style.apply(f"已导出 {fmt.upper()} 格式: {output_path}", Style.SUCCESS))
        return 0
    except Exception as e:
        print(Style.apply(f"错误: {e}", Style.ERROR), file=sys.stderr)
        return 1


def cmd_diff(args: argparse.Namespace) -> int:
    """执行 diff 命令。

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    try:
        extractor1 = create_extractor(args.db_url1)
        extractor2 = create_extractor(args.db_url2)
        schema1 = extractor1.extract()
        schema2 = extractor2.extract()

        differ = SchemaDiffer()
        diff_result = differ.diff(schema1, schema2)

        # 终端输出
        print(diff_result.to_terminal())

        # HTML 报告
        if args.output:
            renderer = HTMLRenderer(schema1)
            html = renderer.render_diff(diff_result)
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(html)
            print(Style.apply(f"\n差异报告已导出: {args.output}", Style.SUCCESS))

        return 0
    except Exception as e:
        print(Style.apply(f"错误: {e}", Style.ERROR), file=sys.stderr)
        return 1


def cmd_analyze(args: argparse.Namespace) -> int:
    """执行 analyze 命令。

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    try:
        extractor = create_extractor(args.db_url)
        schema = extractor.extract()
        tui = TUIRenderer(schema)

        # 显示仪表板
        print(tui.render_dashboard())
        print("")

        # 显示分析结果
        print(tui.render_analysis())
        return 0
    except Exception as e:
        print(Style.apply(f"错误: {e}", Style.ERROR), file=sys.stderr)
        return 1


def cmd_demo(args: argparse.Namespace) -> int:
    """执行 demo 命令。

    创建一个包含示例数据的 SQLite 数据库并生成可视化。

    Args:
        args: 命令行参数

    Returns:
        退出码
    """
    try:
        db_path = os.path.join(os.path.dirname(__file__), "_demo.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 创建用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username VARCHAR(50) NOT NULL UNIQUE,
                email VARCHAR(100) NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                full_name VARCHAR(100),
                avatar_url TEXT,
                is_active BOOLEAN DEFAULT 1,
                role VARCHAR(20) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建分类表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                slug VARCHAR(100) NOT NULL UNIQUE,
                description TEXT,
                parent_id INTEGER,
                sort_order INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES categories(id) ON DELETE SET NULL
            )
        """)

        # 创建产品表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) NOT NULL,
                slug VARCHAR(200) NOT NULL UNIQUE,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                compare_price DECIMAL(10,2),
                sku VARCHAR(50) UNIQUE,
                stock_quantity INTEGER DEFAULT 0,
                category_id INTEGER NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                is_featured BOOLEAN DEFAULT 0,
                weight DECIMAL(8,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
            )
        """)

        # 创建订单表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_number VARCHAR(30) NOT NULL UNIQUE,
                user_id INTEGER NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                subtotal DECIMAL(10,2) NOT NULL,
                tax_amount DECIMAL(10,2) DEFAULT 0,
                shipping_amount DECIMAL(10,2) DEFAULT 0,
                discount_amount DECIMAL(10,2) DEFAULT 0,
                total_amount DECIMAL(10,2) NOT NULL,
                shipping_address TEXT,
                billing_address TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # 创建订单项表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                product_name VARCHAR(200) NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price DECIMAL(10,2) NOT NULL,
                total_price DECIMAL(10,2) NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE RESTRICT
            )
        """)

        # 创建支付记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER NOT NULL UNIQUE,
                method VARCHAR(30) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                amount DECIMAL(10,2) NOT NULL,
                transaction_id VARCHAR(100),
                paid_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
            )
        """)

        # 创建评论表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                rating INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
                title VARCHAR(200),
                content TEXT,
                is_verified BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)

        # 创建标签表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) NOT NULL UNIQUE,
                slug VARCHAR(50) NOT NULL UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 创建产品-标签关联表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_tags (
                product_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                PRIMARY KEY (product_id, tag_id),
                FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
            )
        """)

        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_slug ON products(slug)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order ON order_items(order_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_product ON reviews(product_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_user ON reviews(user_id)")

        # 插入示例数据
        cursor.execute("INSERT OR IGNORE INTO users (id, username, email, password_hash, full_name, role) VALUES (1, 'admin', 'admin@example.com', 'hash1', 'Admin User', 'admin')")
        cursor.execute("INSERT OR IGNORE INTO users (id, username, email, password_hash, full_name, role) VALUES (2, 'john_doe', 'john@example.com', 'hash2', 'John Doe', 'user')")
        cursor.execute("INSERT OR IGNORE INTO users (id, username, email, password_hash, full_name, role) VALUES (3, 'jane_smith', 'jane@example.com', 'hash3', 'Jane Smith', 'user')")

        cursor.execute("INSERT OR IGNORE INTO categories (id, name, slug, description) VALUES (1, 'Electronics', 'electronics', 'Electronic devices and accessories')")
        cursor.execute("INSERT OR IGNORE INTO categories (id, name, slug, description, parent_id) VALUES (2, 'Phones', 'phones', 'Mobile phones', 1)")
        cursor.execute("INSERT OR IGNORE INTO categories (id, name, slug, description, parent_id) VALUES (3, 'Laptops', 'laptops', 'Laptop computers', 1)")
        cursor.execute("INSERT OR IGNORE INTO categories (id, name, slug, description) VALUES (4, 'Clothing', 'clothing', 'Apparel and fashion')")

        cursor.execute("INSERT OR IGNORE INTO products (id, name, slug, price, category_id) VALUES (1, 'Smartphone X', 'smartphone-x', 699.99, 2)")
        cursor.execute("INSERT OR IGNORE INTO products (id, name, slug, price, category_id) VALUES (2, 'Laptop Pro', 'laptop-pro', 1299.99, 3)")
        cursor.execute("INSERT OR IGNORE INTO products (id, name, slug, price, category_id) VALUES (3, 'Wireless Headphones', 'wireless-headphones', 149.99, 1)")

        cursor.execute("INSERT OR IGNORE INTO orders (id, order_number, user_id, status, total_amount) VALUES (1, 'ORD-001', 2, 'completed', 849.98)")
        cursor.execute("INSERT OR IGNORE INTO orders (id, order_number, user_id, status, total_amount) VALUES (2, 'ORD-002', 3, 'pending', 699.99)")

        cursor.execute("INSERT OR IGNORE INTO order_items (order_id, product_id, product_name, quantity, unit_price, total_price) VALUES (1, 1, 'Smartphone X', 1, 699.99, 699.99)")
        cursor.execute("INSERT OR IGNORE INTO order_items (order_id, product_id, product_name, quantity, unit_price, total_price) VALUES (1, 3, 'Wireless Headphones', 1, 149.99, 149.99)")
        cursor.execute("INSERT OR IGNORE INTO order_items (order_id, product_id, product_name, quantity, unit_price, total_price) VALUES (2, 1, 'Smartphone X', 1, 699.99, 699.99)")

        cursor.execute("INSERT OR IGNORE INTO tags (id, name, slug) VALUES (1, 'New Arrival', 'new-arrival')")
        cursor.execute("INSERT OR IGNORE INTO tags (id, name, slug) VALUES (2, 'Best Seller', 'best-seller')")
        cursor.execute("INSERT OR IGNORE INTO tags (id, name, slug) VALUES (3, 'Sale', 'sale')")

        cursor.execute("INSERT OR IGNORE INTO product_tags (product_id, tag_id) VALUES (1, 1)")
        cursor.execute("INSERT OR IGNORE INTO product_tags (product_id, tag_id) VALUES (1, 2)")
        cursor.execute("INSERT OR IGNORE INTO product_tags (product_id, tag_id) VALUES (3, 3)")

        conn.commit()
        conn.close()

        # 提取并可视化
        db_url = f"sqlite:///{db_path}"
        extractor = create_extractor(db_url)
        schema = extractor.extract()

        # 终端显示
        tui = TUIRenderer(schema)
        print(tui.render_dashboard())

        # 生成 HTML
        renderer = HTMLRenderer(schema)
        html = renderer.render(title="Demo E-Commerce Schema")

        output_path = args.output
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

        print(Style.apply(f"\nDemo HTML ER 图已生成: {output_path}", Style.SUCCESS))
        print(f"  数据库: {db_path}")
        print(f"  表数量: {len(schema.tables)}")
        print(f"  外键数量: {len(schema.all_foreign_keys)}")

        # 清理临时数据库文件（仅在非绝对路径时清理）
        # 保留数据库文件以便用户后续操作

        return 0
    except Exception as e:
        print(Style.apply(f"错误: {e}", Style.ERROR), file=sys.stderr)
        return 1


def main(argv: Optional[list] = None) -> int:
    """主入口函数。

    Args:
        argv: 命令行参数列表（默认使用 sys.argv）

    Returns:
        退出码
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    commands = {
        "extract": cmd_extract,
        "visualize": cmd_visualize,
        "viz": cmd_visualize,
        "export": cmd_export,
        "diff": cmd_diff,
        "analyze": cmd_analyze,
        "demo": cmd_demo,
    }

    handler = commands.get(args.command)
    if handler is None:
        parser.print_help()
        return 1

    return handler(args)
