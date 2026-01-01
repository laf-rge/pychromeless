"""
Shared logging utilities for Wagoner Management Corp.'s financial operations.

This module contains shared logging utilities used across different Lambda functions
and modules to ensure consistent logging behavior.
"""

import json
import logging
import os
import sys
from datetime import date, datetime
from decimal import Decimal
from typing import Any


class CustomJsonEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime, date, and Decimal objects."""

    def default(self, o: Any) -> Any:
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        elif isinstance(o, Decimal):
            # Convert Decimal to float for JSON serialization
            # This preserves precision for financial calculations while allowing serialization
            return float(o)
        return super().default(o)


def setup_json_logger() -> None:
    """Configure the root logger with JSON formatting and syntax highlighting.

    Only imports pygments and pythonjsonlogger when needed (local development).
    These dependencies are not available in Lambda.
    """
    # Only import these when we're not in Lambda (they're dev dependencies)
    if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
        from pygments import highlight
        from pygments.formatters import TerminalFormatter
        from pygments.lexers import JsonLexer
        from pythonjsonlogger.json import JsonFormatter

        class ColorizedJsonFormatter(JsonFormatter):
            """JSON formatter that adds syntax highlighting to the output."""

            def __init__(self, *args: Any, **kwargs: Any) -> None:
                super().__init__(
                    *args, **kwargs, json_default=CustomJsonEncoder().default
                )

            def format(self, record: Any) -> str:
                json_str = super().format(record)
                result: str = highlight(json_str, JsonLexer(), TerminalFormatter())
                return result

        json_handler = logging.StreamHandler(sys.stdout)
        json_formatter = ColorizedJsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s"
        )
        json_handler.setFormatter(json_formatter)

        root_logger = logging.getLogger()
        root_logger.handlers = []
        root_logger.addHandler(json_handler)
        root_logger.setLevel(logging.INFO)
    else:
        # In Lambda, just use basic logging (CloudWatch handles the rest)
        logging.basicConfig(level=logging.INFO)
