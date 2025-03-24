"""
Shared logging utilities for Wagoner Management Corp.'s financial operations.

This module contains shared logging utilities used across different Lambda functions
and modules to ensure consistent logging behavior.
"""

import json
import logging
import sys
from datetime import date, datetime
from typing import Any
from pythonjsonlogger.json import JsonFormatter
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter


class CustomJsonEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime and date objects."""

    def default(self, o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)


class ColorizedJsonFormatter(JsonFormatter):
    """JSON formatter that adds syntax highlighting to the output."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, json_default=CustomJsonEncoder().default)

    def format(self, record: Any) -> str:
        json_str = super().format(record)
        return highlight(json_str, JsonLexer(), TerminalFormatter())


def setup_json_logger():
    """Configure the root logger with JSON formatting and syntax highlighting."""
    json_handler = logging.StreamHandler(sys.stdout)
    json_formatter = ColorizedJsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    json_handler.setFormatter(json_formatter)

    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(json_handler)
    root_logger.setLevel(logging.INFO)
