"""Safe report rendering for the Intake-to-Package MVP.

This module renders preparation-only package readiness reports.
It does not run investor agents, produce recommendations, rank companies,
allocate capital, generate trade signals, or create execution instructions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from broker_agents.intake_to_package.readiness import (
    PackageReadiness,
    build_package_readiness,
)


@dataclass(frozen=True)
class PackageReadinessReport:
    """Preparation-only report representation."""

    title: str
    company_name: str
    ticker: str
    exchange: str
    as_of_date: str
    intake_completeness_label: str
    checklist_status: str
    readiness_label: str
    allowed_next_step: str
    human_review_required: bool
    blocker_count: int
    warning_count: int
    blockers: tuple[dict[str, str], ...]
    warnings: tuple[dict[str, str], ...]
    blocked_next_steps: tuple[str, ...]
    safety_boundary: str
    markdown: str


def build_package_readiness_report(
    payload: dict[str, Any],
) -> PackageReadinessReport:
    """Build a safe report from an intake payload."""

    readiness = build_package_readiness(payload)
    return build_package_readiness_report_from_readiness(readiness)


def build_package_readiness_report_from_readiness(
    readiness: PackageReadiness,
) -> PackageReadinessReport:
    """Build a safe report from a readiness object."""

    blockers = tuple(_blocker_to_dict(blocker) for blocker in readiness.blockers)
    warnings = tuple(_warning_to_dict(warning) for warning in readiness.warnings)
    markdown = _render_markdown(readiness, blockers, warnings)

    return PackageReadinessReport(
        title="Intake-to-Package Readiness Report",
        company_name=readiness.company_name,
        ticker=readiness.ticker,
        exchange=readiness.exchange,
        as_of_date=readiness.as_of_date,
        intake_completeness_label=readiness.intake_completeness_label.value,
        checklist_status=readiness.checklist_status.value,
        readiness_label=readiness.readiness_label.value,
        allowed_next_step=readiness.allowed_next_step,
        human_review_required=readiness.human_review_required,
        blocker_count=len(readiness.blockers),
        warning_count=len(readiness.warnings),
        blockers=blockers,
        warnings=warnings,
        blocked_next_steps=readiness.blocked_next_steps,
        safety_boundary=_safety_boundary(),
        markdown=markdown,
    )


def render_package_readiness_markdown(payload: dict[str, Any]) -> str:
    """Render a preparation-only markdown report from an intake payload."""

    return build_package_readiness_report(payload).markdown


def _render_markdown(
    readiness: PackageReadiness,
    blockers: tuple[dict[str, str], ...],
    warnings: tuple[dict[str, str], ...],
) -> str:
    lines = [
        "# Intake-to-Package Readiness Report",
        "",
        "## Status",
        "",
        f"- Company: {_display(readiness.company_name)}",
        f"- Ticker: {_display(readiness.ticker)}",
        f"- Exchange: {_display(readiness.exchange)}",
        f"- As-of date: {_display(readiness.as_of_date)}",
        f"- Intake completeness: {readiness.intake_completeness_label.value}",
        f"- Checklist status: {readiness.checklist_status.value}",
        f"- Readiness label: {readiness.readiness_label.value}",
        f"- Human review required: {readiness.human_review_required}",
        f"- Allowed next step: {readiness.allowed_next_step}",
        "",
        "## Blockers",
        "",
        *_format_records(blockers, "blocker_code", "No blockers."),
        "",
        "## Warnings",
        "",
        *_format_records(warnings, "warning_code", "No warnings."),
        "",
        "## Blocked Next Steps",
        "",
        *_format_values(readiness.blocked_next_steps),
        "",
        "## Safety Boundary",
        "",
        _safety_boundary(),
    ]
    return "\n".join(lines)


def _blocker_to_dict(blocker: Any) -> dict[str, str]:
    return {
        "blocker_code": blocker.blocker_code,
        "blocker_type": blocker.blocker_type,
        "severity": blocker.severity.value,
        "description": blocker.description,
        "related_field": blocker.related_field,
        "related_evidence_category": blocker.related_evidence_category,
        "required_human_action": blocker.required_human_action,
    }


def _warning_to_dict(warning: Any) -> dict[str, str]:
    return {
        "warning_code": warning.warning_code,
        "description": warning.description,
        "related_field": warning.related_field,
        "related_evidence_category": warning.related_evidence_category,
        "suggested_review_action": warning.suggested_review_action,
    }


def _format_records(
    records: tuple[dict[str, str], ...],
    key_field: str,
    empty_text: str,
) -> list[str]:
    if not records:
        return [f"- {empty_text}"]

    lines: list[str] = []
    for record in records:
        key = record[key_field]
        description = record.get("description", "")
        lines.append(f"- {key}: {description}")
    return lines


def _format_values(values: tuple[str, ...]) -> list[str]:
    return [f"- {value}" for value in values]


def _display(value: str) -> str:
    if value:
        return value
    return "missing"


def _safety_boundary() -> str:
    return (
        "Preparation-only report. No investor-agent execution, persona review, "
        "recommendation, ranking, allocation, rebalancing, trade signal, "
        "execution instruction, strategy validation, or auto-promotion."
    )

