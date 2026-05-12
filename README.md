# SchemaViz

A lightweight terminal database schema intelligent visualization engine.

## Features

- Pure Python 3.8+, zero external dependencies
- Support SQLite, PostgreSQL, MySQL, MariaDB
- Auto-extract schema (tables, columns, types, constraints, foreign keys, indexes)
- Generate interactive HTML ER diagrams with SVG visualization
- Schema diff/comparison between two databases
- Export to HTML, JSON, Mermaid, PlantUML formats
- Beautiful TUI terminal dashboard

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Extract and display schema
schemaviz extract sqlite:///mydb.sqlite3

# Generate interactive HTML ER diagram
schemaviz visualize sqlite:///mydb.sqlite3 -o schema.html

# Export to various formats
schemaviz export sqlite:///mydb.sqlite3 -f mermaid -o schema.mmd
schemaviz export sqlite:///mydb.sqlite3 -f plantuml -o schema.puml
schemaviz export sqlite:///mydb.sqlite3 -f json -o schema.json

# Compare two schemas
schemaviz diff sqlite:///old.db sqlite:///new.db

# Analyze schema and get suggestions
schemaviz analyze sqlite:///mydb.sqlite3

# Create a demo database and visualize it
schemaviz demo
```

## License

MIT
