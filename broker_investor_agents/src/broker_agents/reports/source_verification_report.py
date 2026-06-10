"""Markdown reporting for deterministic source verification."""

from pathlib import Path
from typing import Any

import yaml

from broker_agents.backoffice.source_verification import verify_sources
from broker_agents.reports.formatting import safe_text


def _load_pack(path: Path) -> dict:
    """Load a YAML pack, returning an empty dictionary when unavailable."""
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _display_value(value: Any) -> str:
    """Format compact values for Markdown tables."""
    if isinstance(value, (dict, list)):
        return safe_text(str(value))
    return safe_text(value)


def _render_source_verification_results(results: list[dict]) -> str:
    """Render precomputed source-verification results."""
    lines = [
        "# Source Verification Report",
        "",
        "## 1. Important Disclaimer",
        "",
        "This report is not a recommendation, ranking, vote, average score, or consensus. It reviews source quality only.",
        "",
        "## 2. Companies Reviewed",
        "",
        "| Ticker | Company | Overall Source Quality | Source Verification Status |",
        "| --- | --- | --- | --- |",
    ]
    for result in results:
        lines.append(
            f"| {result['ticker']} | {result['company_name']} | "
            f"{result['overall_source_quality']} | "
            f"{result['source_verification_status']} |"
        )

    lines.extend(
        [
            "",
            "## 3. Source Quality by Section",
            "",
            "| Ticker | Section | Quality Label | Verified | Placeholder | Missing | Needs Verification | Calculated |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for result in results:
        for section in result["source_quality_by_section"]:
            lines.append(
                f"| {result['ticker']} | {section['section_name']} | "
                f"{section['section_quality_label']} | {section['verified_count']} | "
                f"{section['placeholder_count']} | {section['missing_count']} | "
                f"{section['needs_verification_count']} | "
                f"{section['calculated_count']} |"
            )

    lines.extend(
        [
            "",
            "## 4. Critical Source Gaps",
            "",
            "| Ticker | Field / Section | Current Status | Why It Matters | Backoffice Action |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for result in results:
        for gap in result["critical_source_gaps"]:
            lines.append(
                f"| {result['ticker']} | {gap['field_or_section']} | "
                f"{gap['current_status']} | {gap['why_it_matters']} | "
                f"{gap['backoffice_action']} |"
            )

    lines.extend(
        [
            "",
            "## 5. Placeholder Fields",
            "",
            "| Ticker | Field / Section | Current Value | Required Verification Source |",
            "| --- | --- | --- | --- |",
        ]
    )
    for result in results:
        for record in result["source_verification_records"]:
            if record["status"] == "manual_placeholder":
                lines.append(
                    f"| {result['ticker']} | {record['field_path']} | "
                    f"{_display_value(record['value'])} | "
                    f"{record['suggested_source']} |"
                )

    lines.extend(
        [
            "",
            "## 6. Missing Fields",
            "",
            "| Ticker | Field / Section | Required For | Suggested Source |",
            "| --- | --- | --- | --- |",
        ]
    )
    for result in results:
        for record in result["source_verification_records"]:
            if record["status"] == "missing":
                lines.append(
                    f"| {result['ticker']} | {record['field_path']} | "
                    f"{record['required_for']} | {record['suggested_source']} |"
                )

    lines.extend(
        [
            "",
            "## 7. Recommended Backoffice Actions",
            "",
            "| Priority | Ticker | Action | Evidence Type | Suggested Source |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for result in results:
        for action in result["recommended_backoffice_actions"]:
            lines.append(
                f"| {action['priority']} | {result['ticker']} | "
                f"{action['action']} | {action['evidence_type']} | "
                f"{action['suggested_source']} |"
            )

    lines.append("")
    return "\n".join(lines)


def generate_source_verification_report_for_pack(pack: dict) -> str:
    """Generate a source verification report for one in-memory pack."""
    return _render_source_verification_results([verify_sources(pack)])


def generate_source_verification_report(
    tickers: list[str],
    examples_root: Path,
) -> str:
    """Generate a non-ranking report of source quality across company packs."""
    results: list[dict] = []
    for raw_ticker in tickers:
        ticker = raw_ticker.strip().upper()
        if not ticker:
            continue
        pack = _load_pack(Path(examples_root) / f"{ticker.lower()}_input.yaml")
        results.append(verify_sources(pack))
    return _render_source_verification_results(results)
