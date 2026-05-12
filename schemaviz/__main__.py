"""
SchemaViz CLI 入口点

支持通过 python -m schemaviz 方式运行。
"""

import sys
from .cli import main


if __name__ == "__main__":
    sys.exit(main())
