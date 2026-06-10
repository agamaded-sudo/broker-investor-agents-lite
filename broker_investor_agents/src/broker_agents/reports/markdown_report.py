"""Markdown report rendering helpers."""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from broker_agents.reports.formatting import (
    format_millions,
    format_multiple,
    format_percent,
    format_ratio_as_percent,
    format_yield,
    safe_text,
)


def render_markdown_template(template_path: Path, context: dict) -> str:
    """Render a Jinja2 Markdown template with the provided context."""
    template_path = Path(template_path)
    environment = Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(disabled_extensions=("md", "j2")),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    environment.filters["millions"] = format_millions
    environment.filters["multiple"] = format_multiple
    environment.filters["percent"] = format_percent
    environment.filters["ratio_percent"] = format_ratio_as_percent
    environment.filters["yield"] = format_yield
    environment.filters["safe_text"] = safe_text
    template = environment.get_template(template_path.name)
    return template.render(**context)
