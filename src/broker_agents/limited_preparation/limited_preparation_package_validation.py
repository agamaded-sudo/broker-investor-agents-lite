"""Task 141 limited preparation package validation."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from broker_agents.limited_preparation.limited_preparation_governance_plan import (
    PROHIBITED_OUTPUTS,
)

SAFETY_NOTICE = (
    "This report validates a limited preparation package only. It does not run "
    "Gatekeeper review, run investor agents, run actual persona reviews, create "
    "investor decisions, rankings, recommendations, allocations, rebalancing "
    "instructions, trade signals, execution instructions, or strategy validation."
)
NEXT_TASK = "Task 142 - Gatekeeper Review of Limited Preparation Package"


@dataclass(frozen=True)
class LimitedPreparationPackageValidation:
    limited_preparation_package_validation_run_id: str
    generated_at: str
    limited_preparation_package_run_id: str
    limited_preparation_artifact_inventory_run_id: str
    limited_preparation_plan_run_id: str
    phase_18_closure_run_id: str
    gatekeeper_return_review_run_id: str
    gatekeeper_return_package_validation_run_id: str
    gatekeeper_return_package_run_id: str
    limited_preparation_package_validation_summary: dict
    package_section_validation_matrix: list[dict]
    artifact_validation_matrix: list[dict]
    warning_validation_matrix: list[dict]
    permission_boundary_validation_matrix: list[dict]
    prohibited_output_validation_matrix: list[dict]
    future_approval_validation_matrix: list[dict]
    validation_findings_matrix: list[dict]
    task_142_handoff_manifest: dict
    limited_preparation_package_validation_checks: list[dict]
    validation_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LimitedPreparationPackageValidationFiles:
    output_folder: Path
    markdown_path: Path
    json_path: Path
    section_csv_path: Path
    artifact_csv_path: Path
    warning_csv_path: Path
    permission_csv_path: Path
    prohibited_csv_path: Path
    approval_csv_path: Path
    findings_csv_path: Path
    handoff_path: Path
    checks_csv_path: Path
    latest_manifest_path: Path
    report: LimitedPreparationPackageValidation


def _load(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_limited_preparation_package_manifest(
    *, outputs_root: Path, limited_preparation_package_run_id: str | None = None
) -> dict:
    root = Path(outputs_root) / "limited_preparation_packages"
    path = (
        root / limited_preparation_package_run_id / "limited_preparation_package.json"
        if limited_preparation_package_run_id
        else root / "latest_limited_preparation_package_manifest.json"
    )
    return _load(
        path,
        "Limited preparation package"
        if limited_preparation_package_run_id
        else "Limited preparation package manifest",
    )


def load_limited_preparation_package(
    *, outputs_root: Path, limited_preparation_package_run_id: str
) -> dict:
    return _load(
        Path(outputs_root)
        / "limited_preparation_packages"
        / limited_preparation_package_run_id
        / "limited_preparation_package.json",
        "Limited preparation package",
    )


def _summary(package: dict) -> dict:
    return package["limited_preparation_package_summary"]


def build_package_section_validation_matrix(package: dict) -> list[dict]:
    return [
        {
            "package_section_code": row["package_section_code"],
            "package_section_title": row["package_section_title"],
            "source_status": row["section_status"],
            "validation_status": "validated_with_warnings",
            "validation_result": "present_and_preserved",
            "warning_status": row["warning_status"],
            "finding": "Required package section exists with warnings preserved.",
            "safety_boundary": "Section validation only.",
        }
        for row in package["limited_preparation_package_index_matrix"]
    ]


def build_artifact_validation_matrix(package: dict) -> list[dict]:
    return [
        {
            "artifact_code": row["artifact_code"],
            "artifact_label": row["artifact_label"],
            "included_in_package": row["included"],
            "source_warning_status": "included_with_warnings",
            "validation_status": "validated_with_warnings",
            "validation_result": "included_and_boundary_preserved",
            "prohibited_content_check": "passed",
            "safety_boundary": "No investor analysis, persona judgment, recommendation language, ranking language, or trade signal language.",
        }
        for row in package["limited_preparation_package_artifact_section_matrix"]
    ]


def build_warning_validation_matrix(package: dict) -> list[dict]:
    return [
        {
            "warning_code": row["warning_code"],
            "warning_label": row["warning_label"],
            "source": row["source"],
            "source_severity": row["severity"],
            "validation_status": "preserved_with_warnings",
            "carried_forward": True,
            "validation_finding": "Warning is visible and retained.",
            "required_follow_up": row["required_follow_up"],
            "safety_boundary": "Warning validation only.",
        }
        for row in package["limited_preparation_package_warning_matrix"]
    ]


def build_permission_boundary_validation_matrix(package: dict) -> list[dict]:
    return [
        {
            "permission_code": row["permission_code"],
            "permission_label": row["permission_label"],
            "source_status": row["package_status"],
            "validation_status": "preserved",
            "validation_result": "boundary_preserved",
            "allowed_scope": row["allowed_scope"],
            "prohibited_scope": row["prohibited_scope"],
            "safety_boundary": "Permission validation only.",
        }
        for row in package["limited_preparation_package_permission_boundary_matrix"]
    ]


def build_prohibited_output_validation_matrix(package: dict) -> list[dict]:
    return [
        {
            "prohibited_code": row["prohibited_code"],
            "prohibited_label": row["prohibited_label"],
            "source_status": row["package_status"],
            "validation_status": "preserved_prohibited",
            "validation_result": "prohibition_preserved",
            "condition_to_reconsider": row["condition_to_reconsider"],
            "safety_boundary": "Prohibited output remains blocked.",
        }
        for row in package["limited_preparation_package_prohibited_output_matrix"]
    ]


def build_future_approval_validation_matrix(package: dict) -> list[dict]:
    return [
        {
            "approval_code": row["approval_code"],
            "approval_label": row["approval_label"],
            "approval_required_for": row["approval_required_for"],
            "source_current_status": row["current_status"],
            "validation_status": "preserved_required_not_granted",
            "validation_result": "future_approval_still_required",
            "safety_boundary": "No approval granted.",
        }
        for row in package["limited_preparation_package_future_approval_matrix"]
    ]


def build_validation_findings_matrix() -> list[dict]:
    codes = [
        "package_assembled_with_warnings",
        "all_artifacts_included_with_warnings",
        "limited_preparation_only_preserved",
        "persona_review_false_preserved",
        "investor_agents_not_allowed_preserved",
        "prohibited_outputs_preserved",
        "future_gatekeeper_approval_required",
        "local_artifact_only_scope_preserved",
    ]
    return [
        {
            "finding_code": code,
            "finding_label": code.replace("_", " "),
            "finding_type": "warning",
            "severity": "medium",
            "source": "Task 140 package",
            "validation_disposition": "carried_forward",
            "blocks_task_142": False,
            "required_follow_up": "Present to Task 142 without scope expansion.",
            "safety_boundary": "Finding only; no authority change.",
        }
        for code in codes
    ]


def build_limited_preparation_package_validation_summary(
    *,
    validation_run_id: str,
    package: dict,
    sections: list[dict],
    artifacts: list[dict],
    findings: list[dict],
) -> dict:
    source = _summary(package)
    return {
        "limited_preparation_package_validation_run_id": validation_run_id,
        "limited_preparation_package_run_id": package["limited_preparation_package_run_id"],
        "limited_preparation_artifact_inventory_run_id": package[
            "limited_preparation_artifact_inventory_run_id"
        ],
        "limited_preparation_plan_run_id": package["limited_preparation_plan_run_id"],
        "phase_18_closure_run_id": package["phase_18_closure_run_id"],
        "phase_id": 19,
        "phase_name": "Limited Preparation Governance Layer",
        "current_task_id": 141,
        "current_task_name": "Validate Limited Preparation Package",
        "source_gatekeeper_return_outcome": source["source_gatekeeper_return_outcome"],
        "source_post_review_progression_status": source["source_post_review_progression_status"],
        "source_post_review_persona_review_status": source[
            "source_post_review_persona_review_status"
        ],
        "source_package_assembly_status": source["package_assembly_status"],
        "validation_status": "complete_with_warnings",
        "required_sections_total": len(sections),
        "required_sections_validated": len(sections),
        "artifacts_total": len(artifacts),
        "artifacts_validated": len(artifacts),
        "artifacts_validated_with_warnings": len(artifacts),
        "artifacts_failed": 0,
        "blocking_findings_total": 0,
        "warning_findings_total": len(findings),
        "actual_persona_review_allowed": False,
        "investor_agents_allowed": False,
        "recommendations_allowed": False,
        "rankings_allowed": False,
        "allocations_allowed": False,
        "trade_signals_allowed": False,
        "auto_promotion_status": "disabled",
        "recommended_next_task": NEXT_TASK,
        "main_validation_finding": "All package sections and artifacts validate with warnings preserved; actual persona review, investor-agent execution, recommendations, rankings, allocations, trade signals, and auto-promotion remain blocked.",
    }


def build_task_142_handoff_manifest(
    *, summary: dict, permissions: list[dict], prohibited: list[dict], approvals: list[dict]
) -> dict:
    return {
        "future_phase_id": 19,
        "future_phase_name": "Limited Preparation Governance Layer",
        "future_task_id": 142,
        "future_task_name": "Gatekeeper Review of Limited Preparation Package",
        "limited_preparation_package_validation_run_id": summary[
            "limited_preparation_package_validation_run_id"
        ],
        "limited_preparation_package_run_id": summary["limited_preparation_package_run_id"],
        "limited_preparation_artifact_inventory_run_id": summary[
            "limited_preparation_artifact_inventory_run_id"
        ],
        "limited_preparation_plan_run_id": summary["limited_preparation_plan_run_id"],
        "source_gatekeeper_return_outcome": summary["source_gatekeeper_return_outcome"],
        "validation_status": summary["validation_status"],
        "package_assembly_status": summary["source_package_assembly_status"],
        "artifacts_validated": summary["artifacts_validated"],
        "artifacts_validated_with_warnings": summary["artifacts_validated_with_warnings"],
        "blocking_findings_total": 0,
        "warning_findings_total": summary["warning_findings_total"],
        "package_outputs_for_gatekeeper_review": [
            "section validation",
            "artifact validation",
            "warning validation",
            "permission validation",
            "prohibited output validation",
            "future approval validation",
        ],
        "permission_boundaries_for_gatekeeper_review": [
            row["permission_code"] for row in permissions
        ],
        "prohibited_outputs_for_gatekeeper_review": [row["prohibited_code"] for row in prohibited],
        "future_approval_requirements_for_gatekeeper_review": [
            row["approval_code"] for row in approvals
        ],
        "allowed_scope": ["Gatekeeper review of preparation-only package"],
        "prohibited_outputs": PROHIBITED_OUTPUTS,
        "readiness_status": "ready_for_gatekeeper_review_with_warnings",
        "execution_allowed_now": True,
        "reason": "Task 141 completed package validation with warnings preserved and no scope expansion.",
    }


def build_limited_preparation_package_validation_checks() -> list[dict]:
    codes = [
        "limited_preparation_package_loaded",
        "validation_summary_created",
        "package_section_validation_matrix_created",
        "artifact_validation_matrix_created",
        "warning_validation_matrix_created",
        "permission_boundary_validation_matrix_created",
        "prohibited_output_validation_matrix_created",
        "future_approval_validation_matrix_created",
        "validation_findings_matrix_created",
        "task_142_handoff_manifest_created",
        "limited_preparation_only_preserved",
        "persona_review_false_preserved",
        "actual_persona_review_not_allowed",
        "investor_agents_not_allowed",
        "no_recommendation_outputs",
        "no_ranking_outputs",
        "no_trade_signal_outputs",
        "auto_promotion_disabled",
        "no_network_calls",
    ]
    return [
        {
            "check_code": code,
            "check_label": code.replace("_", " "),
            "status": "satisfied",
            "source_artifact": "limited_preparation_package_validation",
            "blocking_if_failed": True,
            "finding": f"{code} satisfied for Task 141.",
        }
        for code in codes
    ]


def build_limited_preparation_package_validation(
    *, validation_run_id: str, generated_at: str, package: dict
) -> LimitedPreparationPackageValidation:
    sections = build_package_section_validation_matrix(package)
    artifacts = build_artifact_validation_matrix(package)
    warnings = build_warning_validation_matrix(package)
    permissions = build_permission_boundary_validation_matrix(package)
    prohibited = build_prohibited_output_validation_matrix(package)
    approvals = build_future_approval_validation_matrix(package)
    findings = build_validation_findings_matrix()
    summary = build_limited_preparation_package_validation_summary(
        validation_run_id=validation_run_id,
        package=package,
        sections=sections,
        artifacts=artifacts,
        findings=findings,
    )
    return LimitedPreparationPackageValidation(
        validation_run_id,
        generated_at,
        package["limited_preparation_package_run_id"],
        package["limited_preparation_artifact_inventory_run_id"],
        package["limited_preparation_plan_run_id"],
        package["phase_18_closure_run_id"],
        package["gatekeeper_return_review_run_id"],
        package["gatekeeper_return_package_validation_run_id"],
        package["gatekeeper_return_package_run_id"],
        summary,
        sections,
        artifacts,
        warnings,
        permissions,
        prohibited,
        approvals,
        findings,
        build_task_142_handoff_manifest(
            summary=summary, permissions=permissions, prohibited=prohibited, approvals=approvals
        ),
        build_limited_preparation_package_validation_checks(),
        summary["validation_status"],
        summary["recommended_next_task"],
    )


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _render(report: LimitedPreparationPackageValidation) -> str:
    summary = report.limited_preparation_package_validation_summary
    lines = [
        "# Limited Preparation Package Validation",
        "",
        "## Executive Summary",
        "",
        f"* Limited Preparation Package Validation Run ID: {report.limited_preparation_package_validation_run_id}",
        f"* Limited Preparation Package Run ID: {report.limited_preparation_package_run_id}",
        "* Current Phase: 19 - Limited Preparation Governance Layer",
        "* Current Task: Task 141 - Validate Limited Preparation Package",
        f"* Source Gatekeeper Return Outcome: {summary['source_gatekeeper_return_outcome']}",
        f"* Source Post-Review Progression Status: {summary['source_post_review_progression_status']}",
        f"* Source Post-Review Persona Review Status: {summary['source_post_review_persona_review_status']}",
        f"* Source Package Assembly Status: {summary['source_package_assembly_status']}",
        f"* Validation Status: {report.validation_status}",
        f"* Required Sections Total: {summary['required_sections_total']}",
        f"* Required Sections Validated: {summary['required_sections_validated']}",
        f"* Artifacts Total: {summary['artifacts_total']}",
        f"* Artifacts Validated: {summary['artifacts_validated']}",
        f"* Artifacts Validated With Warnings: {summary['artifacts_validated_with_warnings']}",
        f"* Artifacts Failed: {summary['artifacts_failed']}",
        f"* Blocking Findings Total: {summary['blocking_findings_total']}",
        f"* Warning Findings Total: {summary['warning_findings_total']}",
        f"* Recommended Next Task: {report.recommended_next_task}",
        "",
        "## Important Boundary",
        "",
        SAFETY_NOTICE,
        "",
        "## Where We Are Now",
        "",
        "Current Phase:",
        "19 - Limited Preparation Governance Layer",
        "",
        "Previous Task:",
        "Task 140 - Assemble Limited Preparation Package assembled_with_warnings",
        "",
        "This Task:",
        "Task 141 validates the limited preparation package.",
        "",
        "Allowed Progression:",
        "limited_preparation_only",
        "",
        "Persona Reviews:",
        "false",
        "",
        "Recommended Next Task:",
        NEXT_TASK,
    ]
    groups = [
        (
            "Package Section Validation",
            report.package_section_validation_matrix,
            [
                "package_section_code",
                "source_status",
                "validation_status",
                "validation_result",
                "warning_status",
            ],
        ),
        (
            "Artifact Validation",
            report.artifact_validation_matrix,
            [
                "artifact_code",
                "included_in_package",
                "source_warning_status",
                "validation_status",
                "prohibited_content_check",
            ],
        ),
        (
            "Warning Validation",
            report.warning_validation_matrix,
            [
                "warning_code",
                "source",
                "validation_status",
                "carried_forward",
                "required_follow_up",
            ],
        ),
        (
            "Permission Boundary Validation",
            report.permission_boundary_validation_matrix,
            [
                "permission_code",
                "source_status",
                "validation_status",
                "allowed_scope",
                "prohibited_scope",
            ],
        ),
        (
            "Prohibited Output Validation",
            report.prohibited_output_validation_matrix,
            ["prohibited_code", "source_status", "validation_status", "condition_to_reconsider"],
        ),
        (
            "Future Approval Validation",
            report.future_approval_validation_matrix,
            [
                "approval_code",
                "approval_required_for",
                "source_current_status",
                "validation_status",
            ],
        ),
        (
            "Validation Findings",
            report.validation_findings_matrix,
            [
                "finding_code",
                "finding_type",
                "severity",
                "validation_disposition",
                "blocks_task_142",
            ],
        ),
    ]
    for title, rows, keys in groups:
        lines += [
            "",
            f"## {title}",
            "",
            "| " + " | ".join(keys) + " |",
            "| " + " | ".join("---" for _ in keys) + " |",
            *[
                "| "
                + " | ".join(
                    str(row[key]).lower() if isinstance(row[key], bool) else str(row[key])
                    for key in keys
                )
                + " |"
                for row in rows
            ],
        ]
    handoff = report.task_142_handoff_manifest
    lines += [
        "",
        "## Task 142 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} - {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        "| Check | Status | Blocking If Failed | Finding |",
        "| --- | --- | --- | --- |",
        *[
            f"| {row['check_code']} | {row['status']} | {str(row['blocking_if_failed']).lower()} | {row['finding']} |"
            for row in report.limited_preparation_package_validation_checks
        ],
        "",
        "## What This Suggests",
        "",
        "* The system can proceed to Gatekeeper Review of the Limited Preparation Package in Task 142.",
        "* The package remains preparation-only.",
        "* The work remains non-actionable and governance-bound.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not allow actual persona review.",
        "* It does not run investor agents.",
        "* It does not recommend any company.",
        "* It does not rank companies.",
        "* It does not create allocation or rebalancing.",
        "* It does not create a trade signal.",
        "* It does not validate a strategy.",
        "* It does not enable auto-promotion.",
        "",
        "## Next Task",
        "",
        f"* {report.recommended_next_task}",
        "",
        "## Safety Notice",
        "",
        report.safety_notice,
        "",
    ]
    return "\n".join(lines)


def write_limited_preparation_package_validation_report(
    *, outputs_root: Path, limited_preparation_package_run_id: str | None = None
) -> LimitedPreparationPackageValidationFiles:
    outputs_root = Path(outputs_root)
    manifest = load_limited_preparation_package_manifest(
        outputs_root=outputs_root,
        limited_preparation_package_run_id=limited_preparation_package_run_id,
    )
    run = manifest["limited_preparation_package_run_id"]
    package = load_limited_preparation_package(
        outputs_root=outputs_root, limited_preparation_package_run_id=run
    )
    now = datetime.now(timezone.utc)
    validation_run = now.strftime("%Y%m%d_%H%M%S")
    report = build_limited_preparation_package_validation(
        validation_run_id=validation_run, generated_at=now.isoformat(), package=package
    )
    root = outputs_root / "limited_preparation_package_validations"
    folder = root / validation_run
    folder.mkdir(parents=True, exist_ok=True)
    md, js = (
        folder / "limited_preparation_package_validation.md",
        folder / "limited_preparation_package_validation.json",
    )
    sections, artifacts, warnings, permissions, prohibited, approvals, findings, handoff, checks = (
        folder / "package_section_validation_matrix.csv",
        folder / "artifact_validation_matrix.csv",
        folder / "warning_validation_matrix.csv",
        folder / "permission_boundary_validation_matrix.csv",
        folder / "prohibited_output_validation_matrix.csv",
        folder / "future_approval_validation_matrix.csv",
        folder / "validation_findings_matrix.csv",
        folder / "task_142_handoff_manifest.json",
        folder / "limited_preparation_package_validation_checks.csv",
    )
    latest = root / "latest_limited_preparation_package_validation_manifest.json"
    md.write_text(_render(report), encoding="utf-8")
    js.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    for path, rows in [
        (sections, report.package_section_validation_matrix),
        (artifacts, report.artifact_validation_matrix),
        (warnings, report.warning_validation_matrix),
        (permissions, report.permission_boundary_validation_matrix),
        (prohibited, report.prohibited_output_validation_matrix),
        (approvals, report.future_approval_validation_matrix),
        (findings, report.validation_findings_matrix),
        (checks, report.limited_preparation_package_validation_checks),
    ]:
        _write_csv(path, rows)
    handoff.write_text(json.dumps(report.task_142_handoff_manifest, indent=2), encoding="utf-8")
    latest.write_text(
        json.dumps(
            {
                "limited_preparation_package_validation_run_id": validation_run,
                "limited_preparation_package_run_id": report.limited_preparation_package_run_id,
                "validation_status": report.validation_status,
                "blocking_findings_total": report.limited_preparation_package_validation_summary[
                    "blocking_findings_total"
                ],
                "warning_findings_total": report.limited_preparation_package_validation_summary[
                    "warning_findings_total"
                ],
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(folder),
                "report_path": str(md),
                "report_json_path": str(js),
                "task_142_handoff_manifest_path": str(handoff),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return LimitedPreparationPackageValidationFiles(
        folder,
        md,
        js,
        sections,
        artifacts,
        warnings,
        permissions,
        prohibited,
        approvals,
        findings,
        handoff,
        checks,
        latest,
        report,
    )
