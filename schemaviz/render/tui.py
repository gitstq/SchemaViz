"""
SchemaViz 终端 UI 渲染器

使用 ANSI 转义码和制表符绘制字符生成美观的终端仪表板。
"""

from __future__ import annotations

from typing import List, Dict, Any, Optional, Tuple

from ..core.models import DatabaseSchema, Table, Column, ForeignKey
from ..core.analyzer import SchemaAnalyzer
from ..utils.colors import Colors, Style
from ..utils.helpers import format_number, truncate_string, get_terminal_size


class TUIRenderer:
    """终端 UI 渲染器。

    使用 ANSI 转义码和 Unicode 制表符绘制字符生成专业的终端界面。
    """

    # Box-drawing characters
    TL = "\u250c"  # ┌
    TR = "\u2510"  # ┐
    BL = "\u2514"  # └
    BR = "\u2518"  # ┘
    H = "\u2500"   # ─
    V = "\u2502"   # │
    LT = "\u251c"  # ├
    RT = "\u2524"  # ┤
    TT = "\u252c"  # ┬
    BT = "\u2534"  # ┴
    X = "\u253c"   # ┼
    TITLE_L = "\u2554"  # ╔
    TITLE_R = "\u2557"  # ╗
    TITLE_BL = "\u255a"  # ╚
    TITLE_BR = "\u255d"  # ╝
    TITLE_H = "\u2550"  # ═
    TITLE_V = "\u2551"  # ║

    def __init__(self, schema: DatabaseSchema):
        """初始化渲染器。

        Args:
            schema: 数据库模式对象
        """
        self.schema = schema
        self.analyzer = SchemaAnalyzer()
        self._term_width, self._term_height = get_terminal_size()

    def render_dashboard(self) -> str:
        """渲染完整的终端仪表板。

        Returns:
            终端输出字符串
        """
        self._term_width, self._term_height = get_terminal_size()
        w = min(self._term_width, 120)
        r = Colors.RESET

        lines: List[str] = []

        # 标题
        lines.append(self._render_title_bar(w))
        lines.append("")

        # 统计面板
        lines.append(self._render_stats_panel(w))
        lines.append("")

        # 表列表
        lines.append(self._render_table_list(w))
        lines.append("")

        # 外键关系图
        if self.schema.all_foreign_keys:
            lines.append(self._render_relationship_map(w))
            lines.append("")

        return "\n".join(lines)

    def _render_title_bar(self, width: int) -> str:
        """渲染标题栏。

        Args:
            width: 栏宽

        Returns:
            标题栏字符串
        """
        r = Colors.RESET
        title = " SchemaViz - Database Schema Visualization "
        db_type = self.schema.metadata.get("db_type", "unknown").upper()
        db_name = self.schema.name
        right_text = f" {db_type} | {db_name} "

        inner_width = width - 4
        title_len = len(title)
        right_len = len(right_text)
        padding = inner_width - title_len - right_len

        if padding < 0:
            padding = 0
            right_text = truncate_string(right_text, max(1, inner_width - title_len))

        padding_str = " " * padding

        return (
            f"{Style.TITLE}{self.TITLE_L}{self.TITLE_H * (width - 2)}{self.TITLE_R}{r}\n"
            f"{Style.TITLE}{self.TITLE_V}{r}"
            f"{Style.TITLE}{title}{r}"
            f"{Colors.DIM}{padding_str}{r}"
            f"{Colors.BRIGHT_CYAN}{right_text}{r}"
            f"{Style.TITLE}{self.TITLE_V}{r}\n"
            f"{Style.TITLE}{self.TITLE_BL}{self.TITLE_H * (width - 2)}{self.TITLE_BR}{r}"
        )

    def _render_stats_panel(self, width: int) -> str:
        """渲染统计面板。

        Args:
            width: 面板宽度

        Returns:
            统计面板字符串
        """
        stats = self.analyzer.get_statistics(self.schema)
        r = Colors.RESET

        items = [
            ("Tables", stats["table_count"], Style.DIFF_ADDED),
            ("Columns", stats["column_count"], Style.INFO),
            ("Foreign Keys", stats["foreign_key_count"], Style.FOREIGN_KEY),
            ("Indexes", stats["index_count"], Style.TYPE_INTEGER),
            ("Primary Keys", stats["primary_key_count"], Style.PRIMARY_KEY),
            ("Total Rows", stats["total_rows"], Style.TYPE_DATETIME),
        ]

        inner_width = width - 4

        lines: List[str] = []
        lines.append(f"{Colors.BRIGHT_WHITE}{self.TL}{self.H * (width - 2)}{self.TR}{r}")
        lines.append(f"{Colors.BRIGHT_WHITE}{self.V}{r} {Style.HEADING}SCHEMA STATISTICS{' ' * (inner_width - 18)}{r} {Colors.BRIGHT_WHITE}{self.V}{r}")

        # 每行两个统计项
        col_width = inner_width // 2
        for i in range(0, len(items), 2):
            left = items[i]
            right = items[i + 1] if i + 1 < len(items) else None

            left_str = f"  {left[0]}: {Style.apply(format_number(left[1]), left[2])}"
            if right:
                right_str = f"  {right[0]}: {Style.apply(format_number(right[1]), right[2])}"
            else:
                right_str = ""

            left_padded = left_str.ljust(col_width)
            line = f"{Colors.BRIGHT_WHITE}{self.V}{r}{left_padded}{right_str}{' ' * (inner_width - len(left_padded) - len(right_str))}{r} {Colors.BRIGHT_WHITE}{self.V}{r}"
            lines.append(line)

        lines.append(f"{Colors.BRIGHT_WHITE}{self.BL}{self.H * (width - 2)}{self.BR}{r}")
        return "\n".join(lines)

    def _render_table_list(self, width: int) -> str:
        """渲染表列表。

        Args:
            width: 面板宽度

        Returns:
            表列表字符串
        """
        r = Colors.RESET
        inner_width = width - 4

        lines: List[str] = []
        lines.append(f"{Colors.BRIGHT_WHITE}{self.TL}{self.H * (width - 2)}{self.TR}{r}")
        lines.append(f"{Colors.BRIGHT_WHITE}{self.V}{r} {Style.HEADING}TABLES ({len(self.schema.tables)}){' ' * (inner_width - 10 - len(str(len(self.schema.tables))))}{r} {Colors.BRIGHT_WHITE}{self.V}{r}")

        # 表头
        header = f"  {'Table Name':<30} {'Columns':>8} {'FKs':>6} {'Rows':>10} {'Comment'}"
        sep = f"  {'-' * 30} {'-' * 8} {'-' * 6} {'-' * 10} {'-' * 10}"
        lines.append(f"{Colors.BRIGHT_WHITE}{self.V}{r}{Colors.DIM}{header.ljust(inner_width)}{r} {Colors.BRIGHT_WHITE}{self.V}{r}")
        lines.append(f"{Colors.BRIGHT_WHITE}{self.V}{r}{Colors.DIM}{sep.ljust(inner_width)}{r} {Colors.BRIGHT_WHITE}{self.V}{r}")

        for table in self.schema.tables:
            name = truncate_string(table.name, 28)
            col_count = len(table.columns)
            fk_count = len(table.foreign_keys)
            row_count = format_number(table.row_count)
            comment = truncate_string(table.comment, inner_width - 68) if table.comment else ""

            name_str = Style.apply(name.ljust(30), Colors.BRIGHT_WHITE)
            col_str = Style.apply(str(col_count).rjust(8), Style.TYPE_TEXT)
            fk_str = Style.apply(str(fk_count).rjust(6), Style.FOREIGN_KEY)
            row_str = Style.apply(row_count.rjust(10), Style.TYPE_DATETIME)
            comment_str = f"{Colors.DIM}{comment}{r}" if comment else ""

            line = f"{Colors.BRIGHT_WHITE}{self.V}{r}  {name_str}{col_str}{fk_str}{row_str} {comment_str}"
            # 填充到完整宽度
            used = 2 + 30 + 8 + 6 + 10 + 1 + len(comment)
            if used < inner_width:
                line += " " * (inner_width - used)
            line += f"{r} {Colors.BRIGHT_WHITE}{self.V}{r}"
            lines.append(line)

        lines.append(f"{Colors.BRIGHT_WHITE}{self.BL}{self.H * (width - 2)}{self.BR}{r}")
        return "\n".join(lines)

    def _render_relationship_map(self, width: int) -> str:
        """渲染外键关系图。

        Args:
            width: 面板宽度

        Returns:
            关系图字符串
        """
        r = Colors.RESET
        inner_width = width - 4

        lines: List[str] = []
        lines.append(f"{Colors.BRIGHT_WHITE}{self.TL}{self.H * (width - 2)}{self.TR}{r}")
        lines.append(f"{Colors.BRIGHT_WHITE}{self.V}{r} {Style.HEADING}FOREIGN KEY RELATIONSHIPS{' ' * (inner_width - 26)}{r} {Colors.BRIGHT_WHITE}{self.V}{r}")

        for fk in self.schema.all_foreign_keys:
            from_str = Style.apply(fk.from_table, Colors.BRIGHT_GREEN)
            col_str = Style.apply(fk.from_column, Colors.WHITE)
            arrow = f"{Colors.BRIGHT_CYAN}{self.H}{self.H}{self.H}>{r}"
            to_str = Style.apply(fk.to_table, Colors.BRIGHT_MAGENTA)
            to_col_str = Style.apply(fk.to_column, Colors.WHITE)

            on_delete_str = ""
            if fk.on_delete != "NO ACTION":
                on_delete_str = f" {Colors.DIM}[ON DELETE {fk.on_delete}]{r}"

            line = f"  {from_str}.{col_str} {arrow} {to_str}.{to_col_str}{on_delete_str}"
            line_padded = line.ljust(inner_width)
            lines.append(f"{Colors.BRIGHT_WHITE}{self.V}{r}{line_padded}{r} {Colors.BRIGHT_WHITE}{self.V}{r}")

        lines.append(f"{Colors.BRIGHT_WHITE}{self.BL}{self.H * (width - 2)}{self.BR}{r}")
        return "\n".join(lines)

    def render_table_detail(self, table_name: str) -> str:
        """渲染单个表的详细信息。

        Args:
            table_name: 表名

        Returns:
            表详情字符串
        """
        table = self.schema.get_table(table_name)
        if not table:
            return Style.apply(f"Table '{table_name}' not found.", Style.ERROR)

        r = Colors.RESET
        w = min(self._term_width, 100)
        inner_w = w - 4

        lines: List[str] = []

        # 表标题
        title = f"TABLE: {table.name}"
        if table.comment:
            title += f"  -- {table.comment}"
        lines.append(self._render_box_title(title, w))
        lines.append("")

        # 列信息
        lines.append(f"{Colors.BRIGHT_WHITE}{self.TL}{self.H * (w - 2)}{self.TR}{r}")
        header = f"  {'Column':<25} {'Type':<20} {'Null':>5} {'Key':>5} {'Default':<15} {'Extra'}"
        lines.append(f"{Colors.BRIGHT_WHITE}{self.V}{r}{Style.HEADING}{header.ljust(inner_w)}{r} {Colors.BRIGHT_WHITE}{self.V}{r}")
        lines.append(f"{Colors.BRIGHT_WHITE}{self.V}{r}{Colors.DIM}{'-' * inner_w}{r} {Colors.BRIGHT_WHITE}{self.V}{r}")

        for col in table.columns:
            name = truncate_string(col.name, 23)
            name_str = Style.apply(name.ljust(25), Colors.BRIGHT_WHITE)
            type_str = Style.colorize_type(col.data_type).ljust(20)

            null_str = "YES" if col.is_nullable else "NO"
            null_color = Style.NULLABLE if col.is_nullable else Style.NOT_NULL
            null_formatted = Style.apply(null_str.rjust(5), null_color)

            key_parts: List[str] = []
            if col.is_primary_key:
                key_parts.append("PK")
            if col.is_unique:
                key_parts.append("UQ")
            key_str = ",".join(key_parts) if key_parts else ""
            key_formatted = Style.apply(key_str.rjust(5), Style.PRIMARY_KEY) if key_str else "     "

            default = col.default_value or ""
            if default:
                default = truncate_string(str(default), 13)
            default_formatted = f"{Colors.DIM}{default:<15}{r}"

            extra_parts: List[str] = []
            if col.is_auto_increment:
                extra_parts.append("auto_increment")
            extra_str = f"{Colors.DIM}{', '.join(extra_parts)}{r}"

            line = f"{Colors.BRIGHT_WHITE}{self.V}{r}  {name_str}{type_str}{null_formatted}{key_formatted}{default_formatted}{extra_str}"
            used = 2 + 25 + 20 + 5 + 5 + 15 + len(', '.join(extra_parts))
            if used < inner_w:
                line += " " * (inner_w - used)
            line += f"{r} {Colors.BRIGHT_WHITE}{self.V}{r}"
            lines.append(line)

        lines.append(f"{Colors.BRIGHT_WHITE}{self.BL}{self.H * (w - 2)}{self.BR}{r}")
        lines.append("")

        # 外键
        if table.foreign_keys:
            lines.append(f"{Colors.BRIGHT_WHITE}{self.TL}{self.H * (w - 2)}{self.TR}{r}")
            lines.append(f"{Colors.BRIGHT_WHITE}{self.V}{r} {Style.HEADING}FOREIGN KEYS ({len(table.foreign_keys)}){r} {Colors.BRIGHT_WHITE}{self.V}{r}")

            for fk in table.foreign_keys:
                line = (
                    f"  {Colors.BRIGHT_CYAN}{fk.from_column}{r} -> "
                    f"{Colors.BRIGHT_MAGENTA}{fk.to_table}.{fk.to_column}{r}"
                    f"  {Colors.DIM}ON UPDATE {fk.on_update} ON DELETE {fk.on_delete}{r}"
                )
                lines.append(f"{Colors.BRIGHT_WHITE}{self.V}{r}{line.ljust(inner_w)}{r} {Colors.BRIGHT_WHITE}{self.V}{r}")

            lines.append(f"{Colors.BRIGHT_WHITE}{self.BL}{self.H * (w - 2)}{self.BR}{r}")
            lines.append("")

        # 索引
        if table.indexes:
            lines.append(f"{Colors.BRIGHT_WHITE}{self.TL}{self.H * (w - 2)}{self.TR}{r}")
            lines.append(f"{Colors.BRIGHT_WHITE}{self.V}{r} {Style.HEADING}INDEXES ({len(table.indexes)}){r} {Colors.BRIGHT_WHITE}{self.V}{r}")

            for idx in table.indexes:
                unique = "UNIQUE " if idx.is_unique else ""
                cols = ", ".join(idx.columns)
                line = f"  {Style.TYPE_INTEGER}{unique}INDEX{r} {Colors.BRIGHT_WHITE}{idx.name}{r} ({cols}) [{idx.index_type}]"
                lines.append(f"{Colors.BRIGHT_WHITE}{self.V}{r}{line.ljust(inner_w)}{r} {Colors.BRIGHT_WHITE}{self.V}{r}")

            lines.append(f"{Colors.BRIGHT_WHITE}{self.BL}{self.H * (w - 2)}{self.BR}{r}")

        return "\n".join(lines)

    def _render_box_title(self, title: str, width: int) -> str:
        """渲染带标题的方框。

        Args:
            title: 标题文本
            width: 方框宽度

        Returns:
            方框字符串
        """
        r = Colors.RESET
        inner_w = width - 4
        return (
            f"{Style.TITLE}{self.TITLE_L}{self.TITLE_H * (width - 2)}{self.TITLE_R}{r}\n"
            f"{Style.TITLE}{self.TITLE_V}{r} {Style.HEADING}{title.ljust(inner_w)}{r} {Style.TITLE}{self.TITLE_V}{r}\n"
            f"{Style.TITLE}{self.TITLE_BL}{self.TITLE_H * (width - 2)}{self.TITLE_BR}{r}"
        )

    def render_analysis(self) -> str:
        """渲染模式分析结果。

        Returns:
            分析结果字符串
        """
        r = Colors.RESET
        w = min(self._term_width, 100)
        inner_w = w - 4

        lines: List[str] = []

        # 孤立表
        orphans = self.analyzer.find_orphan_tables(self.schema)
        if orphans:
            lines.append(self._render_box_title("ORPHAN TABLES (no FK relationships)", w))
            for table in orphans:
                lines.append(f"  {Style.WARNING}* {table.name} ({len(table.columns)} columns){r}")
            lines.append("")

        # 循环引用
        cycles = self.analyzer.find_circular_references(self.schema)
        if cycles:
            lines.append(self._render_box_title("CIRCULAR REFERENCES DETECTED", w))
            for cycle in cycles:
                path = " -> ".join(cycle)
                lines.append(f"  {Style.ERROR}* {path}{r}")
            lines.append("")

        # 索引建议
        suggestions = self.analyzer.suggest_indexes(self.schema)
        if suggestions:
            lines.append(self._render_box_title("INDEX SUGGESTIONS", w))
            for sug in suggestions:
                priority_color = Style.ERROR if sug["priority"] == "high" else Style.WARNING
                lines.append(
                    f"  {Style.apply('[HIGH]' if sug['priority'] == 'high' else '[MED]', priority_color)} "
                    f"{sug['table']}.{sug['column']}: {Colors.DIM}{sug['reason']}{r}"
                )
            lines.append("")

        # 拓扑排序
        topo = self.analyzer.topological_sort(self.schema)
        lines.append(self._render_box_title("TABLE CREATION ORDER (topological)", w))
        for i, name in enumerate(topo):
            lines.append(f"  {Colors.DIM}{i + 1:>3}.{r} {Colors.BRIGHT_WHITE}{name}{r}")

        return "\n".join(lines)
