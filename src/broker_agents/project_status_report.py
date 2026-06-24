from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


REPORT_NAME = "Project Status Report"
CURRENT_TASK = "Task 144-1 - Minimal Project Status Report Generator"

SAFETY_NOTICE = (
    "This report is a project-status artifact only. It does not run investor "
    "agents, run actual persona reviews, create investor decisions, rankings, "
    "recommendations, allocations, rebalancing instructions, trade signals, "
    "execution instructions, or strategy validation."
)

BLOCKED_SCOPE = [
    "actual persona reviews",
    "investor-agent execution",
    "investor decisions",
    "company recommendations",
    "company rankings",
    "allocations",
    "rebalancing",
    "trade signals",
    "execution instructions",
    "strategy validation",
    "auto-promotion",
]

ALLOWED_SCOPE = [
    "documentation",
    "status reporting",
    "command inventory",
    "workflow mapping",
    "safe local artifact inspection",
    "non-actionable project operations",
]


@dataclass(frozen=True)
class ManifestStatus:
    name: str
    status: str
    path: str
    run_id: str
    details: dict

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ProjectStatusReport:
    project_status_report_run_id: str
    generated_at: str
    report_name: str
    current_task: str
    current_phase: str
    current_phase_status: str
    latest_phase_19_closure_run_id: str
    latest_gatekeeper_review_run_id: str
    closure_status: str
    next_step_decision: str
    recommended_next_safe_task: str
    allowed_scope: list[str]
    blocked_scope: list[str]
    manifest_statuses: list[dict]
    safety_notice: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ProjectStatusReportFiles:
    report: ProjectStatusReport
    markdown_path: Path
    json_path: Path
    output_folder: Path
    latest_manifest_path: Path


def _read_json_if_available(path: Path) -> dict | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def inspect_manifest(
    *,
    name: str,
    path: Path,
    run_id_key: str,
) -> ManifestStatus:
    payload = _read_json_if_available(path)

    if payload is None:
        return ManifestStatus(
            name=name,
            status="missing",
            path=str(path),
            run_id="unavailable",
            details={},
        )

    return ManifestStatus(
        name=name,
        status="available",
        path=str(path),
        run_id=str(payload.get(run_id_key, "unavailable")),
        details=payload,
    )


def build_project_status_report(
    *,
    report_run_id: str,
    generated_at: str,
    outputs_root: Path,
) -> ProjectStatusReport:
    phase_19_manifest = inspect_manifest(
        name="latest_phase_19_closure_manifest",
        path=(
            outputs_root
            / "phase_19_closures"
            / "latest_phase_19_closure_manifest.json"
        ),
        run_id_key="phase_19_closure_run_id",
    )
    gatekeeper_manifest = inspect_manifest(
        name="latest_limited_preparation_gatekeeper_review_manifest",
        path=(
            outputs_root
            / "limited_preparation_gatekeeper_reviews"
            / "latest_limited_preparation_gatekeeper_review_manifest.json"
        ),
        run_id_key="limited_preparation_gatekeeper_review_run_id",
    )

    phase_19_details = phase_19_manifest.details

    return ProjectStatusReport(
        project_status_report_run_id=report_run_id,
        generated_at=generated_at,
        report_name=REPORT_NAME,
        current_task=CURRENT_TASK,
        current_phase="Phase 19 - Limited Preparation Governance Layer",
        current_phase_status=str(
            phase_19_details.get("phase_completion_status", "closed_with_warnings")
        ),
        latest_phase_19_closure_run_id=phase_19_manifest.run_id,
        latest_gatekeeper_review_run_id=gatekeeper_manifest.run_id,
        closure_status=str(
            phase_19_details.get("closure_status", "phase_19_closed_with_warnings")
        ),
        next_step_decision=str(
            phase_19_details.get(
                "next_step_decision",
                "pause_for_human_direction_and_simplified_workflow_selection",
            )
        ),
        recommended_next_safe_task=(
            "Task 144-1 - Generate minimal project status report"
        ),
        allowed_scope=ALLOWED_SCOPE,
        blocked_scope=BLOCKED_SCOPE,
        manifest_statuses=[
            phase_19_manifest.to_dict(),
            gatekeeper_manifest.to_dict(),
        ],
        safety_notice=SAFETY_NOTICE,
    )


def render_project_status_report_markdown(report: ProjectStatusReport) -> str:
    allowed_lines = "\n".join(f"- {item}" for item in report.allowed_scope)
    blocked_lines = "\n".join(f"- {item}" for item in report.blocked_scope)
    manifest_lines = "\n".join(
        (
            f"- {item['name']}: {item['status']} "
            f"(run_id: {item['run_id']})"
        )
        for item in report.manifest_statuses
    )

    return f"""# Project Status Report

## Executive Summary

- Project Status Report Run ID: {report.project_status_report_run_id}
- Current Task: {report.current_task}
- Current Phase: {report.current_phase}
- Current Phase Status: {report.current_phase_status}
- Latest Phase 19 Closure Run ID: {report.latest_phase_19_closure_run_id}
- Latest Gatekeeper Review Run ID: {report.latest_gatekeeper_review_run_id}
- Closure Status: {report.closure_status}
- Next-Step Decision: {report.next_step_decision}
- Recommended Next Safe Task: {report.recommended_next_safe_task}

## أين نحن الآن؟

المرحلة الرئيسية الحالية:

- {report.current_phase}

وضع المرحلة الحالية:

- {report.current_phase_status}

آخر Run مستقر لإغلاق Phase 19:

- {report.latest_phase_19_closure_run_id}

آخر Gatekeeper Review مستقر:

- {report.latest_gatekeeper_review_run_id}

التالي المباشر:

- {report.recommended_next_safe_task}

هل المهمة القادمة آخر مهمة في المرحلة؟

- لا. المهمة القادمة هدفها إنشاء تقرير حالة مبسط للمشروع قبل أي workflow جديد.

المرحلة التالية بعد إغلاق المرحلة الحالية:

- لم يتم تثبيتها بعد. سيتم اختيارها بعد تقرير الحالة وخريطة الأوامر.

## Manifest Statuses

{manifest_lines}

## Allowed Scope

{allowed_lines}

## Blocked Scope

{blocked_lines}

## Important Boundary

{report.safety_notice}

## What This Does Not Suggest

- It does not allow actual persona review.
- It does not run investor agents.
- It does not recommend companies.
- It does not rank companies.
- It does not create allocation or rebalancing.
- It does not create trade signals.
- It does not create execution instructions.
- It does not validate a strategy.
- It does not enable auto-promotion.

## Safety Notice

{report.safety_notice}
"""


def write_project_status_report(
    *,
    outputs_root: Path,
) -> ProjectStatusReportFiles:
    now = datetime.now(timezone.utc)
    report_run_id = now.strftime("%Y%m%d_%H%M%S")
    generated_at = now.isoformat()

    report = build_project_status_report(
        report_run_id=report_run_id,
        generated_at=generated_at,
        outputs_root=outputs_root,
    )

    output_folder = outputs_root / "project_status_reports" / report_run_id
    output_folder.mkdir(parents=True, exist_ok=True)

    markdown_path = output_folder / "project_status_report.md"
    json_path = output_folder / "project_status_report.json"
    latest_manifest_path = (
        outputs_root
        / "project_status_reports"
        / "latest_project_status_report_manifest.json"
    )

    markdown_path.write_text(
        render_project_status_report_markdown(report),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )

    latest_manifest = {
        "project_status_report_run_id": report.project_status_report_run_id,
        "current_phase": report.current_phase,
        "current_phase_status": report.current_phase_status,
        "latest_phase_19_closure_run_id": (
            report.latest_phase_19_closure_run_id
        ),
        "latest_gatekeeper_review_run_id": report.latest_gatekeeper_review_run_id,
        "closure_status": report.closure_status,
        "next_step_decision": report.next_step_decision,
        "recommended_next_safe_task": report.recommended_next_safe_task,
        "output_folder": str(output_folder),
        "markdown_path": str(markdown_path),
        "json_path": str(json_path),
        "safety_notice": report.safety_notice,
    }
    latest_manifest_path.write_text(
        json.dumps(latest_manifest, indent=2),
        encoding="utf-8",
    )

    return ProjectStatusReportFiles(
        report=report,
        markdown_path=markdown_path,
        json_path=json_path,
        output_folder=output_folder,
        latest_manifest_path=latest_manifest_path,
    )
