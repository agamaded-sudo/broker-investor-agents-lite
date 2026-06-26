"""Markdown report rendering helpers."""

from importlib.resources import files
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

# Locate the bundled templates directory via importlib.resources so this works
# whether the package is installed (wheel/pip) or run directly from source.
_TEMPLATES_DIR: Path = Path(
    str(files("broker_agents").joinpath("reports/report_templates"))
)


def render_markdown_template(template_path: Path, context: dict) -> str:
    """Render a Jinja2 Markdown template with the provided context."""
    template_path = Path(template_path)

    # Build search path: importlib-resolved dir first, then the caller-supplied
    # parent as a fallback (covers direct source-tree invocations).
    search_dirs: list[str] = [str(_TEMPLATES_DIR)]
    if template_path.parent != _TEMPLATES_DIR:
        search_dirs.append(str(template_path.parent))

    environment = Environment(
        loader=FileSystemLoader(search_dirs),
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
