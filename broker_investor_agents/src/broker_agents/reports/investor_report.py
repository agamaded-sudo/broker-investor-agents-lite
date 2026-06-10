"""Investor report file helpers."""

from pathlib import Path


def save_investor_report(report: str, output_path: Path) -> None:
    """Save an investor report to a Markdown file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
