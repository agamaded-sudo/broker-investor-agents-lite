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

# Build a prioritised list of directories to search for .j2 templates.
# Checked in order; first directory that exists and contains templates wins.
#
# 1. Repo-root templates/ — always present as plain files tracked in git.
#    Works on Streamlit Cloud (/mount/src/<repo>/templates/) and locally.
#    Derived by walking up from this file: reports/ → broker_agents/ → src/ → repo root.
# 2. Streamlit Cloud hardcoded mount path — belt-and-suspenders fallback if
#    the relative walk lands somewhere unexpected after pip install.
# 3. The package-relative report_templates/ dir — works in source-tree runs.

_THIS_FILE = Path(__file__).resolve()
_SRC_RELATIVE_ROOT = _THIS_FILE.parents[3]   # …/src/broker_agents/reports/markdown_report.py → repo root
_STREAMLIT_CLOUD_ROOT = Path("/mount/src/broker-investor-agents-lite")
_PACKAGE_TEMPLATES = _THIS_FILE.parent / "report_templates"

_CANDIDATE_DIRS: list[Path] = [
    _SRC_RELATIVE_ROOT / "templates",
    _STREAMLIT_CLOUD_ROOT / "templates",
    _PACKAGE_TEMPLATES,
]


def _resolve_search_dirs(template_name: str) -> list[str]:
    """Return existing candidate dirs that actually contain the template."""
    found = [str(d) for d in _CANDIDATE_DIRS if (d / template_name).exists()]
    if not found:
        # Last resort: return all candidate paths so Jinja2 gives a clear error.
        return [str(d) for d in _CANDIDATE_DIRS]
    return found


def render_markdown_template(template_path: Path, context: dict) -> str:
    """Render a Jinja2 Markdown template with the provided context."""
    template_path = Path(template_path)
    search_dirs = _resolve_search_dirs(template_path.name)
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
