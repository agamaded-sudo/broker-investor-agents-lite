"""Runtime artifact writer for the Intake-to-Package MVP.

This module writes preparation-only report artifacts.
It does not run investor agents, produce recommendations, rank companies,
allocate capital, generate trade signals, or create execution instructions.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from json import dumps
from pathlib import Path
from typing import Any

from broker_agents.intake_to_package.reporting import (
    PackageReadinessReport,
    build_package_readiness_report,
)

DEFAULT_OUTPUT_ROOT = Path("data") / "outputs" / "intake_to_package"
LATEST_MANIFEST_NAME = "latest_package_readiness_manifest.json"


@dataclass(frozen=True)
class PackageReadinessArtifactBundle:
    """Paths for preparation-only package readiness artifacts."""

    run_id: str
    output_dir: str
    markdown_path: str
    json_path: str
    manifest_path: str
    report: PackageReadinessReport


def write_package_readiness_artifacts(
    payload: dict[str, Any],
    output_root: str | Path = DEFAULT_OUTPUT_ROOT,
    run_id: str | None = None,
) -> PackageReadinessArtifactBundle:
    """Write safe package readiness markdown, JSON, and latest manifest."""

    resolved_run_id = _resolve_run_id(run_id)
    root = Path(output_root)
    output_dir = root / resolved_run_id
    output_dir.mkdir(parents=True, exist_ok=True)

    report = build_package_readiness_report(payload)
    markdown_path = output_dir / "package_readiness_report.md"
    json_path = output_dir / "package_readiness_report.json"
    manifest_path = root / LATEST_MANIFEST_NAME

    markdown_path.write_text(report.markdown, encoding="utf-8")
    json_path.write_text(
        dumps(_report_to_dict(report), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    manifest_path.write_text(
        dumps(
            _manifest_dict(
                run_id=resolved_run_id,
                report=report,
                markdown_path=markdown_path,
                json_path=json_path,
            ),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    return PackageReadinessArtifactBundle(
        run_id=resolved_run_id,
        output_dir=str(output_dir),
        markdown_path=str(markdown_path),
        json_path=str(json_path),
        manifest_path=str(manifest_path),
        report=report,
    )


def _resolve_run_id(run_id: str | None) -> str:
    if run_id:
        return run_id
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _report_to_dict(report: PackageReadinessReport) -> dict[str, Any]:
    return asdict(report)


def _manifest_dict(
    run_id: str,
    report: PackageReadinessReport,
    markdown_path: Path,
    json_path: Path,
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "company_name": report.company_name,
        "ticker": report.ticker,
        "exchange": report.exchange,
        "as_of_date": report.as_of_date,
        "readiness_label": report.readiness_label,
        "human_review_required": report.human_review_required,
        "allowed_next_step": report.allowed_next_step,
        "blocked_next_steps": report.blocked_next_steps,
        "markdown_path": str(markdown_path),
        "json_path": str(json_path),
        "safety_boundary": report.safety_boundary,
    }

