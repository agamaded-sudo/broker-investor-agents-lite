"""Small deterministic formatting helpers for Markdown reports."""

from typing import Any

from jinja2 import Undefined


def safe_text(value: Any, fallback: str = "Not available") -> str:
    """Return readable text for optional values."""
    if isinstance(value, Undefined) or value in (None, "", [], {}):
        return fallback
    return str(value)


def format_millions(value: Any) -> str:
    """Format a numeric value expressed in millions of USD."""
    if isinstance(value, Undefined) or value in (None, ""):
        return "Not available"
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return str(value)

    billions = numeric_value / 1000
    return f"USD {billions:.1f}B"


def format_percent(value: Any) -> str:
    """Format a percent value from a number or a percent string."""
    if isinstance(value, Undefined) or value in (None, ""):
        return "Not available"
    if isinstance(value, str):
        stripped = value.strip()
        if stripped.endswith("%"):
            return stripped
        try:
            numeric_value = float(stripped)
        except ValueError:
            return stripped
    else:
        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            return str(value)

    if 0 <= numeric_value <= 1:
        numeric_value *= 100
    return f"{numeric_value:.0f}%"


def format_ratio_as_percent(value: Any) -> str:
    """Format a ratio as a percent with one decimal place."""
    if isinstance(value, Undefined) or value in (None, ""):
        return "Not available"
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return str(value)
    if abs(numeric_value) <= 1:
        numeric_value *= 100
    return f"{numeric_value:.1f}%"


def format_multiple(value: Any) -> str:
    """Format a valuation multiple."""
    if isinstance(value, Undefined) or value in (None, ""):
        return "Not available"
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        return str(value)
    return f"{numeric_value:.1f}x"


def format_yield(value: Any) -> str:
    """Format an investment yield."""
    return format_ratio_as_percent(value)
