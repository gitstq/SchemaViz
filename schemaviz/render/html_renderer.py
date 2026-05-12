"""
SchemaViz HTML 渲染器

生成自包含的交互式 HTML ER 图，包含 SVG 可视化、搜索、缩放和平移功能。
"""

from __future__ import annotations

import json
import math
from typing import Optional, List, Dict, Any, Tuple

from ..core.models import DatabaseSchema, Table, Column, ForeignKey


class HTMLRenderer:
    """交互式 HTML ER 图渲染器。

    生成一个自包含的 HTML 文件，包含:
    - SVG 基础的 ER 图（表为方框，外键为箭头线）
    - 交互功能：点击高亮、缩放、平移
    - 搜索功能
    - 统计侧边栏
    - 暗色主题与 CSS 动画
    - 响应式布局
    """

    def __init__(self, schema: DatabaseSchema):
        """初始化渲染器。

        Args:
            schema: 数据库模式对象
        """
        self.schema = schema
        self._table_positions: Dict[str, Dict[str, int]] = {}
        self._table_sizes: Dict[str, Dict[str, int]] = {}

    def render(self, title: str = "Database Schema") -> str:
        """生成完整的 HTML 文件。

        Args:
            title: 页面标题

        Returns:
            完整的 HTML 字符串
        """
        self._calculate_layout()
        tables_html = self._render_tables()
        relationships_html = self._render_relationships()
        stats_html = self._render_stats()
        table_list_html = self._render_table_list()

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self._escape(title)} - SchemaViz</title>
<style>
{self._CSS}
</style>
</head>
<body>
{self._NAV_HTML}
<div class="main-container">
  <aside class="sidebar" id="sidebar">
    <div class="sidebar-section">
      <h3>Statistics</h3>
      {stats_html}
    </div>
    <div class="sidebar-section">
      <h3>Tables ({len(self.schema.tables)})</h3>
      <div class="table-list">
        {table_list_html}
      </div>
    </div>
  </aside>
  <main class="canvas-area">
    <div class="toolbar">
      <div class="search-box">
        <input type="text" id="searchInput" placeholder="Search tables & columns..." />
        <div class="search-results" id="searchResults"></div>
      </div>
      <div class="toolbar-actions">
        <button onclick="zoomIn()" title="Zoom In">+</button>
        <button onclick="zoomOut()" title="Zoom Out">-</button>
        <button onclick="resetView()" title="Reset View">Reset</button>
        <button onclick="toggleSidebar()" title="Toggle Sidebar">Menu</button>
      </div>
    </div>
    <div class="canvas-wrapper" id="canvasWrapper">
      <svg id="svgCanvas" width="100%" height="100%">
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7"
                  refX="10" refY="3.5" orient="auto" fill="#64748b">
            <polygon points="0 0, 10 3.5, 0 7" />
          </marker>
          <marker id="arrowhead-highlight" markerWidth="10" markerHeight="7"
                  refX="10" refY="3.5" orient="auto" fill="#38bdf8">
            <polygon points="0 0, 10 3.5, 0 7" />
          </marker>
          <filter id="shadow" x="-5%" y="-5%" width="110%" height="115%">
            <feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000" flood-opacity="0.3"/>
          </filter>
          <filter id="glow">
            <feGaussianBlur stdDeviation="3" result="blur"/>
            <feMerge>
              <feMergeNode in="blur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>
        <g id="canvasGroup">
          {relationships_html}
          {tables_html}
        </g>
      </svg>
    </div>
  </main>
</div>
<div class="detail-panel" id="detailPanel">
  <div class="detail-header">
    <h2 id="detailTitle">Table Details</h2>
    <button onclick="closeDetail()" class="close-btn">&times;</button>
  </div>
  <div id="detailContent"></div>
</div>
<script>
{self._JS}
</script>
</body>
</html>"""

    def _calculate_layout(self) -> None:
        """计算表的自动布局位置。

        使用力导向布局的简化版本，将表排列成网格。
        """
        tables = self.schema.tables
        if not tables:
            return

        # 计算每个表的大小
        for table in tables:
            header_height = 36
            row_height = 24
            col_count = len(table.columns)
            width = max(220, min(320, max(len(c.name) for c in table.columns) * 9 + 80))
            height = header_height + col_count * row_height + 8
            self._table_sizes[table.name] = {
                "width": width,
                "height": height,
            }

        # 网格布局
        cols = max(1, int(math.ceil(math.sqrt(len(tables)))))
        spacing_x = 360
        spacing_y = 80
        start_x = 60
        start_y = 60

        for i, table in enumerate(tables):
            row = i // cols
            col = i % cols
            x = start_x + col * spacing_x
            y = start_y + row * (max(
                self._table_sizes[t.name]["height"] for t in tables[row * cols:(row + 1) * cols]
            ) + spacing_y) if row * cols < len(tables) else start_y + row * 300
            self._table_positions[table.name] = {"x": x, "y": y}

        # 优化：将有关联的表放得更近
        self._optimize_layout()

    def _optimize_layout(self) -> None:
        """基于外键关系优化表的位置，使关联表更接近。"""
        if not self.schema.all_foreign_keys:
            return

        # 简单的迭代优化
        for _ in range(50):
            moved = False
            for fk in self.schema.all_foreign_keys:
                from_pos = self._table_positions.get(fk.from_table)
                to_pos = self._table_positions.get(fk.to_table)
                if not from_pos or not to_pos:
                    continue

                dx = to_pos["x"] - from_pos["x"]
                dy = to_pos["y"] - from_pos["y"]
                dist = math.sqrt(dx * dx + dy * dy)

                if dist > 500:
                    # 向目标方向移动一小步
                    step = 10
                    from_pos["x"] += int(dx / dist * step)
                    from_pos["y"] += int(dy / dist * step)
                    moved = True

            if not moved:
                break

    def _render_tables(self) -> str:
        """生成 SVG 表元素。"""
        parts: List[str] = []
        for table in self.schema.tables:
            pos = self._table_positions.get(table.name, {"x": 0, "y": 0})
            size = self._table_sizes.get(table.name, {"width": 220, "height": 100})
            parts.append(self._render_table(table, pos["x"], pos["y"], size["width"], size["height"]))
        return "\n".join(parts)

    def _render_table(
        self, table: Table, x: int, y: int, width: int, height: int
    ) -> str:
        """生成单个表的 SVG 元素。"""
        cols_html: List[str] = []
        for i, col in enumerate(table.columns):
            cy = y + 36 + i * 24 + 16
            pk_icon = '<tspan class="pk-icon" fill="#fbbf24">&#x1F511;</tspan>' if col.is_primary_key else ""
            nullable_mark = "" if col.is_nullable else '<tspan fill="#f87171" font-size="10">NN</tspan>'
            fk_mark = ""
            for fk in table.foreign_keys:
                if fk.from_column == col.name:
                    fk_mark = '<tspan fill="#38bdf8" font-size="10">FK</tspan>'
                    break

            cols_html.append(
                f'<text x="{x + 12}" y="{cy}" class="col-name" '
                f'data-table="{self._escape(table.name)}" data-col="{self._escape(col.name)}">'
                f'{pk_icon}{self._escape(col.name)}{fk_mark}{nullable_mark}'
                f'<tspan class="col-type" dx="8">{self._escape(col.data_type)}</tspan>'
                f'</text>'
            )

        cols_str = "\n".join(cols_html)
        col_count = len(table.columns)
        body_height = col_count * 24 + 8

        return (
            f'<g class="table-group" id="table-{self._escape_id(table.name)}" '
            f'data-table="{self._escape(table.name)}" '
            f'transform="translate(0,0)">'
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
            f'rx="8" ry="8" class="table-bg" filter="url(#shadow)" />'
            f'<rect x="{x}" y="{y}" width="{width}" height="36" '
            f'rx="8" ry="8" class="table-header" />'
            f'<rect x="{x}" y="{y + 28}" width="{width}" height="8" '
            f'class="table-header" />'
            f'<text x="{x + 12}" y="{y + 24}" class="table-title">'
            f'{self._escape(table.name)}</text>'
            f'<text x="{x + width - 12}" y="{y + 24}" class="table-count" '
            f'text-anchor="end">{col_count} cols</text>'
            f'{cols_str}'
            f'</g>'
        )

    def _render_relationships(self) -> str:
        """生成外键关系的 SVG 线条。"""
        parts: List[str] = []
        for fk in self.schema.all_foreign_keys:
            line = self._render_relationship(fk)
            if line:
                parts.append(line)
        return "\n".join(parts)

    def _render_relationship(self, fk: ForeignKey) -> Optional[str]:
        """生成单个外键关系的 SVG 线条。"""
        from_pos = self._table_positions.get(fk.from_table)
        to_pos = self._table_positions.get(fk.to_table)
        from_size = self._table_sizes.get(fk.from_table)
        to_size = self._table_sizes.get(fk.to_table)

        if not from_pos or not to_pos or not from_size or not to_size:
            return None

        # 计算连接点
        from_table = self.schema.get_table(fk.from_table)
        to_table = self.schema.get_table(fk.to_table)

        from_col_idx = 0
        if from_table:
            for i, c in enumerate(from_table.columns):
                if c.name == fk.from_column:
                    from_col_idx = i
                    break

        to_col_idx = 0
        if to_table:
            for i, c in enumerate(to_table.columns):
                if c.name == fk.to_column:
                    to_col_idx = i
                    break

        # 从右侧出发，到左侧到达
        x1 = from_pos["x"] + from_size["width"]
        y1 = from_pos["y"] + 36 + from_col_idx * 24 + 16
        x2 = to_pos["x"]
        y2 = to_pos["y"] + 36 + to_col_idx * 24 + 16

        # 使用贝塞尔曲线
        mid_x = (x1 + x2) / 2
        path = (
            f'M {x1} {y1} '
            f'C {mid_x} {y1}, {mid_x} {y2}, {x2} {y2}'
        )

        return (
            f'<path d="{path}" class="fk-line" '
            f'data-from="{self._escape(fk.from_table)}" '
            f'data-to="{self._escape(fk.to_table)}" '
            f'marker-end="url(#arrowhead)" '
            f'fill="none" />'
        )

    def _render_stats(self) -> str:
        """生成统计侧边栏 HTML。"""
        stats = {
            "Tables": len(self.schema.tables),
            "Columns": len(self.schema.all_columns),
            "Foreign Keys": len(self.schema.all_foreign_keys),
            "Indexes": len(self.schema.all_indexes),
        }
        parts: List[str] = []
        for label, value in stats.items():
            parts.append(
                f'<div class="stat-item">'
                f'<span class="stat-value">{value}</span>'
                f'<span class="stat-label">{label}</span>'
                f'</div>'
            )
        return "\n".join(parts)

    def _render_table_list(self) -> str:
        """生成表列表 HTML。"""
        parts: List[str] = []
        for table in self.schema.tables:
            fk_count = len(table.foreign_keys)
            col_count = len(table.columns)
            parts.append(
                f'<div class="table-list-item" '
                f'onclick="focusTable(\'{self._escape(table.name)}\')" '
                f'data-table="{self._escape(table.name)}">'
                f'<span class="tl-name">{self._escape(table.name)}</span>'
                f'<span class="tl-info">{col_count}c / {fk_count}fk</span>'
                f'</div>'
            )
        return "\n".join(parts)

    def render_diff(self, diff_result: Any, title: str = "Schema Diff") -> str:
        """生成差异比较的 HTML 报告。

        Args:
            diff_result: SchemaDiff 对象
            title: 页面标题

        Returns:
            完整的 HTML 字符串
        """
        diff_dict = diff_result.to_dict() if hasattr(diff_result, "to_dict") else diff_result
        summary = diff_dict.get("summary", {})
        table_diffs = diff_dict.get("table_diffs", [])

        summary_rows: List[str] = []
        labels = {
            "added_tables": ("Added Tables", "#4ade80"),
            "removed_tables": ("Removed Tables", "#f87171"),
            "modified_tables": ("Modified Tables", "#fbbf24"),
            "added_columns": ("Added Columns", "#4ade80"),
            "removed_columns": ("Removed Columns", "#f87171"),
            "modified_columns": ("Modified Columns", "#fbbf24"),
            "added_foreign_keys": ("Added FKs", "#4ade80"),
            "removed_foreign_keys": ("Removed FKs", "#f87171"),
        }
        for key, (label, color) in labels.items():
            val = summary.get(key, 0)
            summary_rows.append(
                f'<div class="diff-stat" style="border-left: 3px solid {color}">'
                f'<span class="diff-stat-val">{val}</span>'
                f'<span class="diff-stat-label">{label}</span>'
                f'</div>'
            )

        detail_rows: List[str] = []
        for td in table_diffs:
            change_type = td.get("change_type", "")
            table_name = td.get("table_name", "")
            if change_type == "added":
                detail_rows.append(
                    f'<div class="diff-row diff-added">'
                    f'<span class="diff-badge added">+TABLE</span> '
                    f'<span class="diff-table">{self._escape(table_name)}</span>'
                    f'</div>'
                )
            elif change_type == "removed":
                detail_rows.append(
                    f'<div class="diff-row diff-removed">'
                    f'<span class="diff-badge removed">-TABLE</span> '
                    f'<span class="diff-table">{self._escape(table_name)}</span>'
                    f'</div>'
                )
            elif change_type == "modified":
                detail_rows.append(
                    f'<div class="diff-row diff-modified">'
                    f'<span class="diff-badge modified">~TABLE</span> '
                    f'<span class="diff-table">{self._escape(table_name)}</span>'
                    f'</div>'
                )
                for cd in td.get("column_diffs", []):
                    ct = cd.get("change_type", "")
                    cn = cd.get("column_name", "")
                    badge_class = ct if ct in ("added", "removed") else "modified"
                    symbol = "+" if ct == "added" else "-" if ct == "removed" else "~"
                    detail_rows.append(
                        f'<div class="diff-row diff-sub {ct}">'
                        f'<span class="diff-badge {badge_class}">{symbol}COL</span> '
                        f'<span class="diff-col">{self._escape(cn)}</span>'
                        f'</div>'
                    )

        return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{self._escape(title)} - SchemaViz</title>
<style>
{self._DIFF_CSS}
</style>
</head>
<body>
<div class="diff-container">
  <h1 class="diff-title">Schema Diff Report</h1>
  <div class="diff-sources">
    <span class="diff-source">{self._escape(diff_dict.get('schema1_name', 'Source'))}</span>
    <span class="diff-arrow">&rarr;</span>
    <span class="diff-source">{self._escape(diff_dict.get('schema2_name', 'Target'))}</span>
  </div>
  <div class="diff-summary">
    {"".join(summary_rows)}
  </div>
  <div class="diff-details">
    {"".join(detail_rows)}
  </div>
</div>
</body>
</html>"""

    @staticmethod
    def _escape(text: str) -> str:
        """HTML 转义。"""
        return (text
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))

    @staticmethod
    def _escape_id(text: str) -> str:
        """转义用于 HTML ID 的字符串。"""
        return text.replace(".", "_").replace(" ", "_").replace("/", "_")

    # CSS 样式
    _CSS = """* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; overflow: hidden; height: 100vh; }
.main-container { display: flex; height: calc(100vh - 48px); }
.nav { height: 48px; background: #1e293b; border-bottom: 1px solid #334155; display: flex; align-items: center; padding: 0 20px; }
.nav .logo { font-size: 18px; font-weight: 700; color: #38bdf8; letter-spacing: -0.5px; }
.nav .logo span { color: #818cf8; }
.nav .version { font-size: 12px; color: #64748b; margin-left: 12px; }
.sidebar { width: 280px; min-width: 280px; background: #1e293b; border-right: 1px solid #334155; overflow-y: auto; transition: width 0.3s, min-width 0.3s; }
.sidebar.collapsed { width: 0; min-width: 0; overflow: hidden; }
.sidebar-section { padding: 16px; border-bottom: 1px solid #334155; }
.sidebar-section h3 { font-size: 12px; text-transform: uppercase; color: #64748b; margin-bottom: 12px; letter-spacing: 1px; }
.stat-item { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; }
.stat-value { font-size: 20px; font-weight: 700; color: #38bdf8; }
.stat-label { font-size: 13px; color: #94a3b8; }
.table-list { display: flex; flex-direction: column; gap: 2px; }
.table-list-item { padding: 8px 12px; border-radius: 6px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; transition: background 0.15s; }
.table-list-item:hover { background: #334155; }
.tl-name { font-size: 13px; font-weight: 500; color: #e2e8f0; }
.tl-info { font-size: 11px; color: #64748b; }
.canvas-area { flex: 1; position: relative; overflow: hidden; }
.toolbar { position: absolute; top: 12px; left: 12px; right: 12px; z-index: 10; display: flex; justify-content: space-between; align-items: center; }
.search-box { position: relative; }
.search-box input { background: #1e293b; border: 1px solid #334155; border-radius: 8px; padding: 8px 16px; color: #e2e8f0; font-size: 14px; width: 300px; outline: none; transition: border-color 0.2s; }
.search-box input:focus { border-color: #38bdf8; }
.search-results { position: absolute; top: 100%; left: 0; right: 0; background: #1e293b; border: 1px solid #334155; border-radius: 8px; margin-top: 4px; max-height: 300px; overflow-y: auto; display: none; }
.search-results.active { display: block; }
.search-result-item { padding: 8px 16px; cursor: pointer; font-size: 13px; }
.search-result-item:hover { background: #334155; }
.search-result-item .sr-table { color: #38bdf8; font-weight: 600; }
.search-result-item .sr-col { color: #94a3b8; margin-left: 8px; }
.toolbar-actions { display: flex; gap: 4px; }
.toolbar-actions button { background: #1e293b; border: 1px solid #334155; border-radius: 8px; color: #e2e8f0; width: 36px; height: 36px; cursor: pointer; font-size: 16px; transition: all 0.15s; }
.toolbar-actions button:hover { background: #334155; border-color: #38bdf8; }
.canvas-wrapper { width: 100%; height: 100%; cursor: grab; }
.canvas-wrapper:active { cursor: grabbing; }
.table-bg { fill: #1e293b; stroke: #334155; stroke-width: 1; transition: stroke 0.2s, filter 0.2s; }
.table-group:hover .table-bg { stroke: #38bdf8; }
.table-group.highlighted .table-bg { stroke: #38bdf8; filter: url(#glow); }
.table-group.dimmed { opacity: 0.3; }
.table-header { fill: #334155; }
.table-title { fill: #f1f5f9; font-size: 14px; font-weight: 700; font-family: 'Segoe UI', system-ui, sans-serif; }
.table-count { fill: #64748b; font-size: 11px; font-family: 'Segoe UI', system-ui, sans-serif; }
.col-name { fill: #cbd5e1; font-size: 12px; font-family: 'Fira Code', 'Consolas', monospace; }
.col-name:hover { fill: #f1f5f9; }
.col-type { fill: #64748b; font-size: 11px; }
.pk-icon { font-size: 10px; }
.fk-line { stroke: #475569; stroke-width: 1.5; stroke-dasharray: 6 3; transition: stroke 0.2s; }
.fk-line.highlighted { stroke: #38bdf8; stroke-width: 2; stroke-dasharray: none; }
.fk-line.dimmed { opacity: 0.15; }
.detail-panel { position: fixed; right: -400px; top: 0; bottom: 0; width: 400px; background: #1e293b; border-left: 1px solid #334155; z-index: 100; transition: right 0.3s; overflow-y: auto; }
.detail-panel.open { right: 0; }
.detail-header { padding: 20px; border-bottom: 1px solid #334155; display: flex; justify-content: space-between; align-items: center; }
.detail-header h2 { font-size: 18px; color: #f1f5f9; }
.close-btn { background: none; border: none; color: #64748b; font-size: 24px; cursor: pointer; }
.close-btn:hover { color: #f1f5f9; }
.detail-content { padding: 20px; }
.detail-table { width: 100%; border-collapse: collapse; }
.detail-table th { text-align: left; padding: 8px; font-size: 12px; color: #64748b; text-transform: uppercase; border-bottom: 1px solid #334155; }
.detail-table td { padding: 8px; font-size: 13px; border-bottom: 1px solid #1e293b; }
.badge { display: inline-block; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 600; }
.badge-pk { background: #854d0e; color: #fbbf24; }
.badge-fk { background: #0c4a6e; color: #38bdf8; }
.badge-nn { background: #7f1d1d; color: #f87171; }
.badge-unique { background: #4c1d95; color: #a78bfa; }
.badge-ai { background: #065f46; color: #34d399; }"""

    _NAV_HTML = """<nav class="nav">
  <div class="logo">Schema<span>Viz</span></div>
  <span class="version">v1.0.0</span>
</nav>"""

    _JS = """let scale = 1;
let translateX = 0;
let translateY = 0;
let isDragging = false;
let startX = 0;
let startY = 0;
let lastTranslateX = 0;
let lastTranslateY = 0;

const canvasGroup = document.getElementById('canvasGroup');
const svgCanvas = document.getElementById('svgCanvas');
const wrapper = document.getElementById('canvasWrapper');

function updateTransform() {
  canvasGroup.setAttribute('transform', 'translate(' + translateX + ',' + translateY + ') scale(' + scale + ')');
}

wrapper.addEventListener('mousedown', function(e) {
  if (e.target.closest('.table-group')) return;
  isDragging = true;
  startX = e.clientX;
  startY = e.clientY;
  lastTranslateX = translateX;
  lastTranslateY = translateY;
});

document.addEventListener('mousemove', function(e) {
  if (!isDragging) return;
  translateX = lastTranslateX + (e.clientX - startX);
  translateY = lastTranslateY + (e.clientY - startY);
  updateTransform();
});

document.addEventListener('mouseup', function() { isDragging = false; });

wrapper.addEventListener('wheel', function(e) {
  e.preventDefault();
  const delta = e.deltaY > 0 ? 0.9 : 1.1;
  const rect = wrapper.getBoundingClientRect();
  const mx = e.clientX - rect.left;
  const my = e.clientY - rect.top;
  translateX = mx - (mx - translateX) * delta;
  translateY = my - (my - translateY) * delta;
  scale *= delta;
  scale = Math.max(0.1, Math.min(5, scale));
  updateTransform();
}, { passive: false });

function zoomIn() { scale = Math.min(5, scale * 1.2); updateTransform(); }
function zoomOut() { scale = Math.max(0.1, scale / 1.2); updateTransform(); }
function resetView() { scale = 1; translateX = 0; translateY = 0; updateTransform(); clearHighlights(); }

function toggleSidebar() {
  document.getElementById('sidebar').classList.toggle('collapsed');
}

// Table click
document.querySelectorAll('.table-group').forEach(function(g) {
  g.addEventListener('click', function() {
    const tableName = this.dataset.table;
    highlightTable(tableName);
    showDetail(tableName);
  });
});

function highlightTable(tableName) {
  document.querySelectorAll('.table-group').forEach(function(g) {
    if (g.dataset.table === tableName) {
      g.classList.add('highlighted');
      g.classList.remove('dimmed');
    } else {
      const isConnected = document.querySelector('.fk-line[data-from="' + tableName + '"][data-to="' + g.dataset.table + '"]') ||
                          document.querySelector('.fk-line[data-to="' + tableName + '"][data-from="' + g.dataset.table + '"]');
      if (isConnected) {
        g.classList.add('highlighted');
        g.classList.remove('dimmed');
      } else {
        g.classList.remove('highlighted');
        g.classList.add('dimmed');
      }
    }
  });
  document.querySelectorAll('.fk-line').forEach(function(line) {
    if (line.dataset.from === tableName || line.dataset.to === tableName) {
      line.classList.add('highlighted');
      line.classList.remove('dimmed');
    } else {
      line.classList.remove('highlighted');
      line.classList.add('dimmed');
    }
  });
}

function clearHighlights() {
  document.querySelectorAll('.table-group').forEach(function(g) {
    g.classList.remove('highlighted', 'dimmed');
  });
  document.querySelectorAll('.fk-line').forEach(function(line) {
    line.classList.remove('highlighted', 'dimmed');
  });
}

// Detail panel
function showDetail(tableName) {
  const panel = document.getElementById('detailPanel');
  const title = document.getElementById('detailTitle');
  const content = document.getElementById('detailContent');
  title.textContent = tableName;
  panel.classList.add('open');

  // Collect column info from SVG text elements
  const tableGroup = document.getElementById('table-' + tableName.replace(/\\./g, '_').replace(/\\//g, '_'));
  if (!tableGroup) return;

  let html = '<table class="detail-table"><thead><tr><th>Column</th><th>Type</th><th>Constraints</th></tr></thead><tbody>';
  const texts = tableGroup.querySelectorAll('.col-name');
  texts.forEach(function(t) {
    const colName = t.textContent.trim().replace(/[\\u{1F511}]/u, '').trim();
    const typeSpan = t.querySelector('.col-type');
    const colType = typeSpan ? typeSpan.textContent.trim() : '';
    let badges = '';
    if (t.querySelector('.pk-icon')) badges += '<span class="badge badge-pk">PK</span> ';
    const fullText = t.textContent;
    if (fullText.includes('FK')) badges += '<span class="badge badge-fk">FK</span> ';
    if (fullText.includes('NN')) badges += '<span class="badge badge-nn">NN</span> ';
    html += '<tr><td>' + colName + '</td><td style="color:#64748b">' + colType + '</td><td>' + badges + '</td></tr>';
  });
  html += '</tbody></table>';
  content.innerHTML = html;
}

function closeDetail() {
  document.getElementById('detailPanel').classList.remove('open');
  clearHighlights();
}

// Search
const searchInput = document.getElementById('searchInput');
const searchResults = document.getElementById('searchResults');

searchInput.addEventListener('input', function() {
  const query = this.value.toLowerCase().trim();
  if (!query) { searchResults.classList.remove('active'); return; }
  let html = '';
  document.querySelectorAll('.table-group').forEach(function(g) {
    const tableName = g.dataset.table;
    if (tableName.toLowerCase().includes(query)) {
      html += '<div class="search-result-item" onclick="focusTable(\\'' + tableName + '\\')"><span class="sr-table">' + tableName + '</span></div>';
    }
    g.querySelectorAll('.col-name').forEach(function(t) {
      const colName = t.dataset.col;
      if (colName && colName.toLowerCase().includes(query)) {
        html += '<div class="search-result-item" onclick="focusTable(\\'' + tableName + '\\')"><span class="sr-table">' + tableName + '</span><span class="sr-col">' + colName + '</span></div>';
      }
    });
  });
  if (html) { searchResults.innerHTML = html; searchResults.classList.add('active'); }
  else { searchResults.classList.remove('active'); }
});

searchInput.addEventListener('blur', function() {
  setTimeout(function() { searchResults.classList.remove('active'); }, 200);
});

function focusTable(tableName) {
  searchInput.value = '';
  searchResults.classList.remove('active');
  highlightTable(tableName);
  showDetail(tableName);
  // Pan to table
  const tableGroup = document.getElementById('table-' + tableName.replace(/\\./g, '_').replace(/\\//g, '_'));
  if (tableGroup) {
    const rect = wrapper.getBoundingClientRect();
    const bbox = tableGroup.getBBox();
    translateX = rect.width / 2 - (bbox.x + bbox.width / 2) * scale;
    translateY = rect.height / 2 - (bbox.y + bbox.height / 2) * scale;
    updateTransform();
  }
}

// Click on canvas background to clear
svgCanvas.addEventListener('click', function(e) {
  if (e.target === svgCanvas || e.target.tagName === 'svg') {
    closeDetail();
  }
});"""

    # Diff CSS
    _DIFF_CSS = """* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: #0f172a; color: #e2e8f0; padding: 40px; }
.diff-container { max-width: 900px; margin: 0 auto; }
.diff-title { font-size: 28px; font-weight: 700; color: #f1f5f9; margin-bottom: 8px; }
.diff-sources { display: flex; align-items: center; gap: 12px; margin-bottom: 32px; }
.diff-source { font-size: 16px; color: #38bdf8; background: #1e293b; padding: 8px 16px; border-radius: 8px; }
.diff-arrow { color: #64748b; font-size: 20px; }
.diff-summary { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; margin-bottom: 32px; }
.diff-stat { background: #1e293b; border-radius: 8px; padding: 16px; }
.diff-stat-val { display: block; font-size: 28px; font-weight: 700; color: #f1f5f9; }
.diff-stat-label { display: block; font-size: 12px; color: #64748b; margin-top: 4px; text-transform: uppercase; }
.diff-details { background: #1e293b; border-radius: 8px; overflow: hidden; }
.diff-row { padding: 10px 16px; border-bottom: 1px solid #334155; display: flex; align-items: center; gap: 12px; }
.diff-row:last-child { border-bottom: none; }
.diff-sub { padding-left: 40px; }
.diff-row.diff-added { background: rgba(74, 222, 128, 0.05); }
.diff-row.diff-removed { background: rgba(248, 113, 113, 0.05); }
.diff-row.diff-modified { background: rgba(251, 191, 36, 0.05); }
.diff-badge { font-size: 11px; font-weight: 700; padding: 2px 8px; border-radius: 4px; min-width: 56px; text-align: center; }
.diff-badge.added { background: #14532d; color: #4ade80; }
.diff-badge.removed { background: #7f1d1d; color: #f87171; }
.diff-badge.modified { background: #713f12; color: #fbbf24; }
.diff-table { font-weight: 600; color: #f1f5f9; }
.diff-col { color: #94a3b8; font-family: 'Fira Code', monospace; font-size: 13px; }"""
