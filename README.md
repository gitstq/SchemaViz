<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue.svg" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Dependencies-Zero-success.svg" alt="Zero Dependencies">
  <img src="https://img.shields.io/badge/Tests-52%20Passing-brightgreen.svg" alt="52 Tests">
</p>

<h1 align="center">🗂️ SchemaViz</h1>

<p align="center">
  <strong>Lightweight Database Schema Intelligent Visualization Engine</strong><br>
  轻量级数据库 Schema 智能可视化引擎
</p>

<p align="center">
  <a href="#-简体中文">简体中文</a> ·
  <a href="#-繁體中文">繁體中文</a> ·
  <a href="#-english">English</a>
</p>

---

<a id="-简体中文"></a>

## 🎉 项目介绍

**SchemaViz** 是一款轻量级、零依赖的数据库 Schema 智能可视化引擎，专为开发者快速理解、分析和文档化数据库结构而设计。

### 💡 解决的痛点

- 📊 **数据库结构黑盒**：接手新项目时，面对数十张表、上百个字段，难以快速理解数据库整体架构
- 🔄 **Schema 变更追踪困难**：团队协作中数据库结构频繁变更，缺乏直观的差异对比工具
- 📝 **文档维护成本高**：手动编写和维护数据库文档耗时耗力，且容易与实际结构脱节
- 🔧 **工具依赖重**：现有数据库可视化工具体积庞大、依赖复杂、安装配置繁琐

### 🌟 自研差异化亮点

- **零外部依赖**：纯 Python 标准库实现，无需安装任何第三方包，`pip install` 即可使用
- **终端原生 TUI**：精美的终端仪表板界面，使用 Unicode 制表符和 ANSI 色彩，无需 GUI 环境
- **交互式 HTML ER 图**：生成自包含的 HTML 文件，支持缩放、平移、搜索、表详情查看
- **智能分析引擎**：自动检测孤立表、循环引用、缺失索引，提供拓扑排序建议
- **多格式导出**：支持 Mermaid、PlantUML、JSON 等多种格式，无缝集成到现有文档流程

---

## ✨ 核心特性

| 特性 | 描述 |
|------|------|
| 🗄️ **多数据库支持** | 支持 **SQLite**、**PostgreSQL**、**MySQL**、**MariaDB** 四种主流数据库 |
| 📊 **Schema 自动提取** | 自动提取表、列、类型、约束、外键、索引等完整结构信息 |
| 🎨 **交互式 HTML ER 图** | SVG 可视化，支持缩放、平移、搜索、表详情面板，暗色主题 |
| 📟 **终端 TUI 仪表板** | 精美的终端界面，使用 Unicode 制表符和 ANSI 色彩渲染 |
| 🔍 **智能分析引擎** | 孤立表检测、循环引用检测、缺失索引建议、拓扑排序 |
| 📐 **Schema 差异对比** | 对比两个数据库的结构差异，支持终端彩色输出和 HTML 报告 |
| 📤 **多格式导出** | **HTML**、**Mermaid**、**PlantUML**、**JSON** 四种导出格式 |
| ⚡ **零外部依赖** | 纯 Python 3.8+ 标准库实现，SQLite 开箱即用 |
| 🧪 **完整测试覆盖** | 52 个单元测试，覆盖数据模型、提取器、分析器核心模块 |

---

## 🚀 快速开始

### 环境要求

- **Python** 3.8 或更高版本
- SQLite 支持：无需额外安装（Python 内置）
- PostgreSQL 支持：需安装 `psycopg2-binary`（`pip install psycopg2-binary`）
- MySQL/MariaDB 支持：需安装 `mysql-connector-python`（`pip install mysql-connector-python`）

### 安装

```bash
# 克隆仓库
git clone https://github.com/gitstq/SchemaViz.git
cd SchemaViz

# 安装（开发模式）
pip install -e .
```

### 一键体验 Demo

```bash
# 创建演示数据库并生成可视化（零配置，即刻体验）
schemaviz demo
```

### 基本使用

```bash
# 提取并显示数据库 Schema
schemaviz extract sqlite:///mydb.sqlite3

# 生成交互式 HTML ER 图
schemaviz visualize sqlite:///mydb.sqlite3 -o schema.html

# 导出为 Mermaid 格式
schemaviz export sqlite:///mydb.sqlite3 -f mermaid -o schema.mmd

# 导出为 PlantUML 格式
schemaviz export sqlite:///mydb.sqlite3 -f plantuml -o schema.puml

# 导出为 JSON 格式
schemaviz export sqlite:///mydb.sqlite3 -f json -o schema.json

# 对比两个数据库 Schema
schemaviz diff sqlite:///old.db sqlite:///new.db

# 分析 Schema 并获取优化建议
schemaviz analyze sqlite:///mydb.sqlite3
```

### 连接字符串格式

```bash
# SQLite（文件路径）
sqlite:///path/to/database.db
sqlite:///:memory:

# PostgreSQL
postgresql://user:password@localhost:5432/mydb

# MySQL
mysql://user:password@localhost:3306/mydb

# MariaDB
mariadb://user:password@localhost:3306/mydb
```

---

## 📖 详细使用指南

### 1. Schema 提取与终端展示

```bash
# 显示完整 Schema 概览
schemaviz extract sqlite:///mydb.sqlite3

# 查看指定表的详细信息
schemaviz extract sqlite:///mydb.sqlite3 -t users
```

终端输出包含：统计面板、表列表、外键关系图。

### 2. 交互式 HTML ER 图

```bash
# 生成默认 ER 图
schemaviz visualize sqlite:///mydb.sqlite3 -o schema.html

# 自定义标题
schemaviz visualize sqlite:///mydb.sqlite3 -o schema.html --title "My Project Schema"
```

生成的 HTML 文件特性：
- 🎨 暗色主题，精美 UI 设计
- 🔍 实时搜索表和列
- 🖱️ 鼠标拖拽平移、滚轮缩放
- 📋 点击表查看详细列信息
- 📊 左侧统计面板

### 3. Schema 智能分析

```bash
schemaviz analyze sqlite:///mydb.sqlite3
```

分析报告包含：
- 🏝️ **孤立表检测**：没有外键关联的独立表
- 🔄 **循环引用检测**：外键形成的循环依赖
- 💡 **索引建议**：外键列缺少索引的高优先级建议
- 📋 **拓扑排序**：推荐的表创建顺序（考虑依赖关系）
- 📦 **存储估算**：基于列类型的粗略存储空间估算

### 4. Schema 差异对比

```bash
# 终端彩色差异输出
schemaviz diff sqlite:///v1.db sqlite:///v2.db

# 同时生成 HTML 差异报告
schemaviz diff sqlite:///v1.db sqlite:///v2.db -o diff_report.html
```

### 5. 多格式导出

```bash
# Mermaid ER 图
schemaviz export sqlite:///mydb.sqlite3 -f mermaid --mermaid-type er -o schema_er.mmd

# Mermaid 流程图（展示外键关系）
schemaviz export sqlite:///mydb.sqlite3 -f mermaid --mermaid-type flowchart -o schema_flow.mmd

# Mermaid 类图
schemaviz export sqlite:///mydb.sqlite3 -f mermaid --mermaid-type class -o schema_class.mmd

# PlantUML（完整版）
schemaviz export sqlite:///mydb.sqlite3 -f plantuml --plantuml-type full -o schema.puml

# JSON（精简模式）
schemaviz export sqlite:///mydb.sqlite3 -f json --compact -o schema.json
```

---

## 💡 设计思路与迭代规划

### 设计理念

SchemaViz 的核心理念是 **"零门槛、零依赖、开箱即用"**：

1. **纯标准库实现**：不依赖任何第三方包，避免版本冲突和安装问题
2. **终端优先**：TUI 界面让开发者在最熟悉的环境中查看数据库结构
3. **自包含输出**：HTML 文件无需服务器，双击即可在浏览器中查看
4. **智能分析**：不仅展示结构，更提供有价值的优化建议

### 技术选型

| 组件 | 选型 | 原因 |
|------|------|------|
| 语言 | Python 3.8+ | 数据库生态最成熟，开发者基数最大 |
| 终端 UI | ANSI + Unicode | 零依赖实现精美终端界面 |
| HTML 渲染 | 内联 CSS/JS + SVG | 自包含，无需构建工具 |
| 数据提取 | 各数据库原生查询 | 最准确、最完整的 Schema 信息 |

### 后续迭代计划

- [ ] **v1.1**：支持 SQL Server、Oracle、ClickHouse 等更多数据库
- [ ] **v1.2**：添加 DDL 生成功能（根据 Schema 生成建表 SQL）
- [ ] **v1.3**：支持从 DDL 文件直接解析 Schema（无需连接数据库）
- [ ] **v1.4**：添加 Web UI 服务器模式（在线查看 Schema）
- [ ] **v2.0**：支持 Schema 版本管理和变更历史追踪

---

## 📦 安装与部署

### 从源码安装

```bash
git clone https://github.com/gitstq/SchemaViz.git
cd SchemaViz
pip install -e .
```

### 作为 Python 模块使用

```python
from schemaviz.core.extractor import create_extractor
from schemaviz.render.html_renderer import HTMLRenderer

# 提取 Schema
extractor = create_extractor("sqlite:///mydb.sqlite3")
schema = extractor.extract()

# 生成 HTML ER 图
renderer = HTMLRenderer(schema)
html = renderer.render(title="My Database Schema")
with open("schema.html", "w") as f:
    f.write(html)
```

### 运行测试

```bash
cd SchemaViz
python -m unittest discover tests -v
```

---

## 🤝 贡献指南

欢迎社区贡献！请遵循以下规范：

### 提交规范

使用 Angular 提交规范：

```
feat: 新增功能
fix: 修复问题
docs: 文档更新
refactor: 代码重构
test: 测试相关
chore: 构建/工具链相关
```

### Issue 反馈

提交 Issue 时请包含：
1. Python 版本和操作系统
2. 数据库类型和版本
3. 完整的错误信息和复现步骤

### PR 流程

1. Fork 本仓库
2. 创建特性分支（`git checkout -b feature/amazing-feature`）
3. 提交更改（`git commit -m 'feat: add amazing feature'`）
4. 推送到分支（`git push origin feature/amazing-feature`）
5. 提交 Pull Request

---

## 📄 开源协议

本项目基于 [MIT License](LICENSE) 开源。

---

<a id="-繁體中文"></a>

## 🎉 專案介紹

**SchemaViz** 是一款輕量級、零依賴的資料庫 Schema 智慧視覺化引擎，專為開發者快速理解、分析與文件化資料庫結構而設計。

### 💡 解決的痛點

- 📊 **資料庫結構黑盒**：接手新專案時，面對數十張表、上百個欄位，難以快速理解資料庫整體架構
- 🔄 **Schema 變更追蹤困難**：團隊協作中資料庫結構頻繁變更，缺乏直觀的差異對比工具
- 📝 **文件維護成本高**：手動撰寫與維護資料庫文件耗時耗力，且容易與實際結構脫節
- 🔧 **工具依賴重**：現有資料庫視覺化工具體積龐大、依賴複雜、安裝配置繁瑣

### 🌟 自研差異化亮點

- **零外部依賴**：純 Python 標準庫實現，無需安裝任何第三方套件，`pip install` 即可使用
- **終端原生 TUI**：精美的終端儀表板介面，使用 Unicode 表格繪製字元與 ANSI 色彩，無需 GUI 環境
- **互動式 HTML ER 圖**：產生自包含的 HTML 檔案，支援縮放、平移、搜尋、表詳情查看
- **智慧分析引擎**：自動偵測孤立表、循環引用、缺失索引，提供拓撲排序建議
- **多格式匯出**：支援 Mermaid、PlantUML、JSON 等多種格式，無縫整合到現有文件流程

---

## ✨ 核心特性

| 特性 | 描述 |
|------|------|
| 🗄️ **多資料庫支援** | 支援 **SQLite**、**PostgreSQL**、**MySQL**、**MariaDB** 四種主流資料庫 |
| 📊 **Schema 自動提取** | 自動提取表、欄位、型別、約束、外鍵、索引等完整結構資訊 |
| 🎨 **互動式 HTML ER 圖** | SVG 視覺化，支援縮放、平移、搜尋、表詳情面板，暗色主題 |
| 📟 **終端 TUI 儀表板** | 精美的終端介面，使用 Unicode 表格繪製字元與 ANSI 色彩渲染 |
| 🔍 **智慧分析引擎** | 孤立表偵測、循環引用偵測、缺失索引建議、拓撲排序 |
| 📐 **Schema 差異對比** | 對比兩個資料庫的結構差異，支援終端彩色輸出與 HTML 報告 |
| 📤 **多格式匯出** | **HTML**、**Mermaid**、**PlantUML**、**JSON** 四種匯出格式 |
| ⚡ **零外部依賴** | 純 Python 3.8+ 標準庫實現，SQLite 開箱即用 |
| 🧪 **完整測試覆蓋** | 52 個單元測試，覆蓋資料模型、提取器、分析器核心模組 |

---

## 🚀 快速開始

### 環境需求

- **Python** 3.8 或更高版本
- SQLite 支援：無需額外安裝（Python 內建）
- PostgreSQL 支援：需安裝 `psycopg2-binary`（`pip install psycopg2-binary`）
- MySQL/MariaDB 支援：需安裝 `mysql-connector-python`（`pip install mysql-connector-python`）

### 安裝

```bash
# 克隆倉庫
git clone https://github.com/gitstq/SchemaViz.git
cd SchemaViz

# 安裝（開發模式）
pip install -e .
```

### 一鍵體驗 Demo

```bash
# 建立演示資料庫並產生視覺化（零配置，即刻體驗）
schemaviz demo
```

### 基本使用

```bash
# 提取並顯示資料庫 Schema
schemaviz extract sqlite:///mydb.sqlite3

# 產生互動式 HTML ER 圖
schemaviz visualize sqlite:///mydb.sqlite3 -o schema.html

# 匯出為 Mermaid 格式
schemaviz export sqlite:///mydb.sqlite3 -f mermaid -o schema.mmd

# 匯出為 PlantUML 格式
schemaviz export sqlite:///mydb.sqlite3 -f plantuml -o schema.puml

# 匯出為 JSON 格式
schemaviz export sqlite:///mydb.sqlite3 -f json -o schema.json

# 對比兩個資料庫 Schema
schemaviz diff sqlite:///old.db sqlite:///new.db

# 分析 Schema 並取得優化建議
schemaviz analyze sqlite:///mydb.sqlite3
```

### 連線字串格式

```bash
# SQLite（檔案路徑）
sqlite:///path/to/database.db
sqlite:///:memory:

# PostgreSQL
postgresql://user:password@localhost:5432/mydb

# MySQL
mysql://user:password@localhost:3306/mydb

# MariaDB
mariadb://user:password@localhost:3306/mydb
```

---

## 📖 詳細使用指南

### 1. Schema 提取與終端展示

```bash
# 顯示完整 Schema 概覽
schemaviz extract sqlite:///mydb.sqlite3

# 查看指定表的詳細資訊
schemaviz extract sqlite:///mydb.sqlite3 -t users
```

終端輸出包含：統計面板、表列表、外鍵關係圖。

### 2. 互動式 HTML ER 圖

```bash
# 產生預設 ER 圖
schemaviz visualize sqlite:///mydb.sqlite3 -o schema.html

# 自訂標題
schemaviz visualize sqlite:///mydb.sqlite3 -o schema.html --title "My Project Schema"
```

產生的 HTML 檔案特性：
- 🎨 暗色主題，精美 UI 設計
- 🔍 即時搜尋表與欄位
- 🖱️ 滑鼠拖曳平移、滾輪縮放
- 📋 點擊表查看詳細欄位資訊
- 📊 左側統計面板

### 3. Schema 智慧分析

```bash
schemaviz analyze sqlite:///mydb.sqlite3
```

分析報告包含：
- 🏝️ **孤立表偵測**：沒有外鍵關聯的獨立表
- 🔄 **循環引用偵測**：外鍵形成的循環依賴
- 💡 **索引建議**：外鍵欄位缺少索引的高優先級建議
- 📋 **拓撲排序**：推薦的表建立順序（考慮依賴關係）
- 📦 **儲存估算**：基於欄位型別的粗略儲存空間估算

### 4. Schema 差異對比

```bash
# 終端彩色差異輸出
schemaviz diff sqlite:///v1.db sqlite:///v2.db

# 同時產生 HTML 差異報告
schemaviz diff sqlite:///v1.db sqlite:///v2.db -o diff_report.html
```

### 5. 多格式匯出

```bash
# Mermaid ER 圖
schemaviz export sqlite:///mydb.sqlite3 -f mermaid --mermaid-type er -o schema_er.mmd

# Mermaid 流程圖（展示外鍵關係）
schemaviz export sqlite:///mydb.sqlite3 -f mermaid --mermaid-type flowchart -o schema_flow.mmd

# Mermaid 類別圖
schemaviz export sqlite:///mydb.sqlite3 -f mermaid --mermaid-type class -o schema_class.mmd

# PlantUML（完整版）
schemaviz export sqlite:///mydb.sqlite3 -f plantuml --plantuml-type full -o schema.puml

# JSON（精簡模式）
schemaviz export sqlite:///mydb.sqlite3 -f json --compact -o schema.json
```

---

## 💡 設計思路與迭代規劃

### 設計理念

SchemaViz 的核心理念是 **「零門檻、零依賴、開箱即用」**：

1. **純標準庫實現**：不依賴任何第三方套件，避免版本衝突與安裝問題
2. **終端優先**：TUI 介面讓開發者在最熟悉的環境中查看資料庫結構
3. **自包含輸出**：HTML 檔案無需伺服器，雙擊即可在瀏覽器中查看
4. **智慧分析**：不僅展示結構，更提供有價值的優化建議

### 技術選型

| 元件 | 選型 | 原因 |
|------|------|------|
| 語言 | Python 3.8+ | 資料庫生態最成熟，開發者基數最大 |
| 終端 UI | ANSI + Unicode | 零依賴實現精美終端介面 |
| HTML 渲染 | 內嵌 CSS/JS + SVG | 自包含，無需建置工具 |
| 資料提取 | 各資料庫原生查詢 | 最準確、最完整的 Schema 資訊 |

### 後續迭代計畫

- [ ] **v1.1**：支援 SQL Server、Oracle、ClickHouse 等更多資料庫
- [ ] **v1.2**：新增 DDL 產生功能（根據 Schema 產生建表 SQL）
- [ ] **v1.3**：支援從 DDL 檔案直接解析 Schema（無需連接資料庫）
- [ ] **v1.4**：新增 Web UI 伺服器模式（線上查看 Schema）
- [ ] **v2.0**：支援 Schema 版本管理與變更歷史追蹤

---

## 📦 安裝與部署

### 從原始碼安裝

```bash
git clone https://github.com/gitstq/SchemaViz.git
cd SchemaViz
pip install -e .
```

### 作為 Python 模組使用

```python
from schemaviz.core.extractor import create_extractor
from schemaviz.render.html_renderer import HTMLRenderer

# 提取 Schema
extractor = create_extractor("sqlite:///mydb.sqlite3")
schema = extractor.extract()

# 產生 HTML ER 圖
renderer = HTMLRenderer(schema)
html = renderer.render(title="My Database Schema")
with open("schema.html", "w") as f:
    f.write(html)
```

### 執行測試

```bash
cd SchemaViz
python -m unittest discover tests -v
```

---

## 🤝 貢獻指南

歡迎社群貢獻！請遵循以下規範：

### 提交規範

使用 Angular 提交規範：

```
feat: 新增功能
fix: 修復問題
docs: 文件更新
refactor: 程式碼重構
test: 測試相關
chore: 建置/工具鏈相關
```

### Issue 回饋

提交 Issue 時請包含：
1. Python 版本與作業系統
2. 資料庫型別與版本
3. 完整的錯誤資訊與重現步驟

### PR 流程

1. Fork 本倉庫
2. 建立特性分支（`git checkout -b feature/amazing-feature`）
3. 提交變更（`git commit -m 'feat: add amazing feature'`）
4. 推送到分支（`git push origin feature/amazing-feature`）
5. 提交 Pull Request

---

## 📄 開源協議

本專案基於 [MIT License](LICENSE) 開源。

---

<a id="-english"></a>

## 🎉 Introduction

**SchemaViz** is a lightweight, zero-dependency database schema intelligent visualization engine designed for developers to quickly understand, analyze, and document database structures.

### 💡 Pain Points Solved

- 📊 **Database Structure Black Box**: When taking over a new project, it's hard to quickly understand the overall architecture with dozens of tables and hundreds of columns
- 🔄 **Schema Change Tracking**: Database structures change frequently during team collaboration, lacking intuitive diff tools
- 📝 **Documentation Maintenance**: Manually writing and maintaining database docs is time-consuming and easily outdated
- 🔧 **Heavy Tool Dependencies**: Existing database visualization tools are bloated, complex to configure, and cumbersome to install

### 🌟 Differentiation Highlights

- **Zero External Dependencies**: Pure Python standard library — no third-party packages needed
- **Native Terminal TUI**: Beautiful terminal dashboard with Unicode box-drawing and ANSI colors
- **Interactive HTML ER Diagrams**: Self-contained HTML files with zoom, pan, search, and table detail panels
- **Intelligent Analysis Engine**: Auto-detect orphan tables, circular references, missing indexes, and suggest topological ordering
- **Multi-format Export**: Mermaid, PlantUML, JSON — seamlessly integrate into your existing documentation workflow

---

## ✨ Core Features

| Feature | Description |
|---------|-------------|
| 🗄️ **Multi-Database Support** | **SQLite**, **PostgreSQL**, **MySQL**, **MariaDB** |
| 📊 **Auto Schema Extraction** | Tables, columns, types, constraints, foreign keys, indexes |
| 🎨 **Interactive HTML ER Diagrams** | SVG visualization with zoom, pan, search, detail panels, dark theme |
| 📟 **Terminal TUI Dashboard** | Beautiful terminal UI with Unicode box-drawing and ANSI colors |
| 🔍 **Intelligent Analysis** | Orphan table detection, circular reference detection, index suggestions, topological sort |
| 📐 **Schema Diff** | Compare two database schemas with colored terminal output and HTML reports |
| 📤 **Multi-format Export** | **HTML**, **Mermaid**, **PlantUML**, **JSON** |
| ⚡ **Zero Dependencies** | Pure Python 3.8+ standard library, SQLite works out of the box |
| 🧪 **Full Test Coverage** | 52 unit tests covering models, extractors, and analyzers |

---

## 🚀 Quick Start

### Requirements

- **Python** 3.8 or higher
- SQLite support: No extra installation needed (built into Python)
- PostgreSQL support: Requires `psycopg2-binary` (`pip install psycopg2-binary`)
- MySQL/MariaDB support: Requires `mysql-connector-python` (`pip install mysql-connector-python`)

### Installation

```bash
# Clone the repository
git clone https://github.com/gitstq/SchemaViz.git
cd SchemaViz

# Install (development mode)
pip install -e .
```

### One-command Demo

```bash
# Create a demo database and visualize it (zero config, instant experience)
schemaviz demo
```

### Basic Usage

```bash
# Extract and display database schema
schemaviz extract sqlite:///mydb.sqlite3

# Generate interactive HTML ER diagram
schemaviz visualize sqlite:///mydb.sqlite3 -o schema.html

# Export to Mermaid format
schemaviz export sqlite:///mydb.sqlite3 -f mermaid -o schema.mmd

# Export to PlantUML format
schemaviz export sqlite:///mydb.sqlite3 -f plantuml -o schema.puml

# Export to JSON format
schemaviz export sqlite:///mydb.sqlite3 -f json -o schema.json

# Compare two database schemas
schemaviz diff sqlite:///old.db sqlite:///new.db

# Analyze schema and get optimization suggestions
schemaviz analyze sqlite:///mydb.sqlite3
```

### Connection String Formats

```bash
# SQLite (file path)
sqlite:///path/to/database.db
sqlite:///:memory:

# PostgreSQL
postgresql://user:password@localhost:5432/mydb

# MySQL
mysql://user:password@localhost:3306/mydb

# MariaDB
mariadb://user:password@localhost:3306/mydb
```

---

## 📖 Detailed Usage Guide

### 1. Schema Extraction & Terminal Display

```bash
# Display full schema overview
schemaviz extract sqlite:///mydb.sqlite3

# View specific table details
schemaviz extract sqlite:///mydb.sqlite3 -t users
```

Terminal output includes: statistics panel, table list, and foreign key relationship diagram.

### 2. Interactive HTML ER Diagrams

```bash
# Generate default ER diagram
schemaviz visualize sqlite:///mydb.sqlite3 -o schema.html

# Custom title
schemaviz visualize sqlite:///mydb.sqlite3 -o schema.html --title "My Project Schema"
```

Generated HTML file features:
- 🎨 Dark theme with polished UI design
- 🔍 Real-time search for tables and columns
- 🖱️ Mouse drag to pan, scroll to zoom
- 📋 Click tables to view detailed column info
- 📊 Statistics sidebar panel

### 3. Schema Analysis

```bash
schemaviz analyze sqlite:///mydb.sqlite3
```

Analysis report includes:
- 🏝️ **Orphan Table Detection**: Tables with no foreign key relationships
- 🔄 **Circular Reference Detection**: Circular dependencies formed by foreign keys
- 💡 **Index Suggestions**: High-priority recommendations for missing indexes on FK columns
- 📋 **Topological Sort**: Recommended table creation order (considering dependencies)
- 📦 **Storage Estimation**: Rough storage space estimation based on column types

### 4. Schema Diff

```bash
# Colored terminal diff output
schemaviz diff sqlite:///v1.db sqlite:///v2.db

# Also generate HTML diff report
schemaviz diff sqlite:///v1.db sqlite:///v2.db -o diff_report.html
```

### 5. Multi-format Export

```bash
# Mermaid ER diagram
schemaviz export sqlite:///mydb.sqlite3 -f mermaid --mermaid-type er -o schema_er.mmd

# Mermaid flowchart (showing FK relationships)
schemaviz export sqlite:///mydb.sqlite3 -f mermaid --mermaid-type flowchart -o schema_flow.mmd

# Mermaid class diagram
schemaviz export sqlite:///mydb.sqlite3 -f mermaid --mermaid-type class -o schema_class.mmd

# PlantUML (full version)
schemaviz export sqlite:///mydb.sqlite3 -f plantuml --plantuml-type full -o schema.puml

# JSON (compact mode)
schemaviz export sqlite:///mydb.sqlite3 -f json --compact -o schema.json
```

---

## 💡 Design Philosophy & Roadmap

### Design Philosophy

SchemaViz's core principle is **"Zero Barrier, Zero Dependencies, Ready to Use"**:

1. **Pure Standard Library**: No third-party packages, avoiding version conflicts and installation issues
2. **Terminal First**: TUI interface lets developers view database structures in their most familiar environment
3. **Self-contained Output**: HTML files need no server — just double-click to open in a browser
4. **Intelligent Analysis**: Not just displaying structure, but providing valuable optimization suggestions

### Tech Stack

| Component | Choice | Reason |
|-----------|--------|--------|
| Language | Python 3.8+ | Most mature database ecosystem, largest developer base |
| Terminal UI | ANSI + Unicode | Zero-dependency beautiful terminal interface |
| HTML Rendering | Inline CSS/JS + SVG | Self-contained, no build tools needed |
| Data Extraction | Native DB queries | Most accurate and complete schema information |

### Roadmap

- [ ] **v1.1**: Support SQL Server, Oracle, ClickHouse and more databases
- [ ] **v1.2**: Add DDL generation (generate CREATE TABLE SQL from schema)
- [ ] **v1.3**: Support parsing Schema directly from DDL files (no DB connection needed)
- [ ] **v1.4**: Add Web UI server mode (view schemas online)
- [ ] **v2.0**: Schema version management and change history tracking

---

## 📦 Installation & Deployment

### Install from Source

```bash
git clone https://github.com/gitstq/SchemaViz.git
cd SchemaViz
pip install -e .
```

### Use as Python Module

```python
from schemaviz.core.extractor import create_extractor
from schemaviz.render.html_renderer import HTMLRenderer

# Extract schema
extractor = create_extractor("sqlite:///mydb.sqlite3")
schema = extractor.extract()

# Generate HTML ER diagram
renderer = HTMLRenderer(schema)
html = renderer.render(title="My Database Schema")
with open("schema.html", "w") as f:
    f.write(html)
```

### Run Tests

```bash
cd SchemaViz
python -m unittest discover tests -v
```

---

## 🤝 Contributing

Community contributions are welcome! Please follow these guidelines:

### Commit Convention

Using Angular commit convention:

```
feat: new feature
fix: bug fix
docs: documentation update
refactor: code refactoring
test: test related
chore: build/toolchain related
```

### Issue Reporting

When submitting an issue, please include:
1. Python version and operating system
2. Database type and version
3. Full error message and reproduction steps

### PR Workflow

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'feat: add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Submit a Pull Request

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
