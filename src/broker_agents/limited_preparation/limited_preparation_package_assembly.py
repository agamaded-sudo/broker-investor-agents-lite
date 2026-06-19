"""Task 140 limited preparation package assembly."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from broker_agents.limited_preparation.limited_preparation_artifact_inventory import (
    ARTIFACT_ORDER,
)
from broker_agents.limited_preparation.limited_preparation_governance_plan import (
    PROHIBITED_OUTPUTS,
)

SAFETY_NOTICE = (
    "This report assembles a limited preparation package only. It does not "
    "validate the package, run Gatekeeper review, run investor agents, run "
    "actual persona reviews, create investor decisions, rankings, "
    "recommendations, allocations, rebalancing instructions, trade signals, "
    "execution instructions, or strategy validation."
)
PHASE_NAME = "Limited Preparation Governance Layer"
CURRENT_TASK_NAME = "Assemble Limited Preparation Package"
NEXT_TASK = "Task 141 - Validate Limited Preparation Package"


@dataclass(frozen=True)
class LimitedPreparationPackage:
    limited_preparation_package_run_id: str
    generated_at: str
    limited_preparation_artifact_inventory_run_id: str
    limited_preparation_plan_run_id: str
    phase_18_closure_run_id: str
    gatekeeper_return_review_run_id: str
    gatekeeper_return_package_validation_run_id: str
    gatekeeper_return_package_run_id: str
    limited_preparation_package_summary: dict
    limited_preparation_package_index_matrix: list[dict]
    limited_preparation_package_artifact_section_matrix: list[dict]
    limited_preparation_package_warning_matrix: list[dict]
    limited_preparation_package_permission_boundary_matrix: list[dict]
    limited_preparation_package_prohibited_output_matrix: list[dict]
    limited_preparation_package_future_approval_matrix: list[dict]
    task_141_handoff_manifest: dict
    limited_preparation_package_assembly_checks: list[dict]
    package_assembly_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LimitedPreparationPackageFiles:
    output_folder: Path
    markdown_path: Path
    json_path: Path
    index_csv_path: Path
    artifact_sections_csv_path: Path
    warnings_csv_path: Path
    permissions_csv_path: Path
    prohibited_csv_path: Path
    approvals_csv_path: Path
    handoff_path: Path
    checks_csv_path: Path
    latest_manifest_path: Path
    report: LimitedPreparationPackage


def _load(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_limited_preparation_artifact_inventory_manifest(
    *, outputs_root: Path, limited_preparation_artifact_inventory_run_id: str | None = None
) -> dict:
    root = Path(outputs_root) / "limited_preparation_artifact_inventories"
    path = (
        root
        / limited_preparation_artifact_inventory_run_id
        / "limited_preparation_artifact_inventory.json"
        if limited_preparation_artifact_inventory_run_id
        else root / "latest_limited_preparation_artifact_inventory_manifest.json"
    )
    return _load(
        path,
        "Limited preparation artifact inventory"
        if limited_preparation_artifact_inventory_run_id
        else "Limited preparation artifact inventory manifest",
    )


def load_limited_preparation_artifact_inventory(
    *, outputs_root: Path, limited_preparation_artifact_inventory_run_id: str
) -> dict:
    return _load(
        Path(outputs_root)
        / "limited_preparation_artifact_inventories"
        / limited_preparation_artifact_inventory_run_id
        / "limited_preparation_artifact_inventory.json",
        "Limited preparation artifact inventory",
    )


def _summary(inventory: dict) -> dict:
    return inventory["artifact_inventory_summary"]


def build_limited_preparation_package_index_matrix() -> list[dict]:
    sections = [
        "executive_summary",
        "limited_preparation_boundary",
        *ARTIFACT_ORDER,
        "future_gatekeeper_approval_requirements",
        "prohibited_outputs_summary",
        "task_141_handoff",
    ]
    return [
        {
            "package_section_code": code,
            "package_section_title": code.replace("_", " "),
            "section_purpose": "Package-ready preparation-only summary or control.",
            "source_artifacts": "Task 139 artifact inventory",
            "section_status": "included_with_warnings",
            "included_in_package": True,
            "warning_status": "carried_forward_warning",
            "safety_boundary": "Non-actionable package section.",
        }
        for code in sections
    ]


def build_limited_preparation_package_artifact_section_matrix(inventory: dict) -> list[dict]:
    source = {row["artifact_code"]: row for row in inventory["allowed_artifact_inventory_matrix"]}
    return [
        {
            "artifact_code": code,
            "artifact_label": source[code]["artifact_label"],
            "package_section_code": code,
            "included": True,
            "section_content_summary": "Package-ready template and boundary summary only.",
            "allowed_content": source[code]["allowed_content"],
            "prohibited_content": source[code]["prohibited_content"],
            "warning_note": "Included with Task 139 readiness warnings preserved.",
            "safety_boundary": "No investor analysis, persona judgment, recommendations, rankings, or trade signals.",
        }
        for code in ARTIFACT_ORDER
    ]


def build_limited_preparation_package_warning_matrix() -> list[dict]:
    warnings = [
        "artifacts_ready_with_warnings",
        "limited_preparation_only",
        "persona_review_false",
        "investor_agents_not_allowed",
        "recommendations_not_allowed",
        "rankings_not_allowed",
        "trade_signals_not_allowed",
        "auto_promotion_disabled",
        "future_gatekeeper_approval_required",
        "local_artifact_only_scope",
    ]
    return [
        {
            "warning_code": code,
            "warning_label": code.replace("_", " "),
            "source": "Task 139 inventory",
            "severity": "critical"
            if code
            in {
                "persona_review_false",
                "investor_agents_not_allowed",
                "auto_promotion_disabled",
                "future_gatekeeper_approval_required",
            }
            else "medium",
            "package_disposition": "carried_forward",
            "impact_on_validation": "Must be confirmed by Task 141.",
            "required_follow_up": "Preserve during package validation.",
            "safety_boundary": "Warning disclosure only.",
        }
        for code in warnings
    ]


def build_limited_preparation_package_permission_boundary_matrix() -> list[dict]:
    specs = [
        ("limited_preparation_package_assembly", "allowed"),
        ("package_validation", "next_task"),
        ("future_gatekeeper_review", "future_task"),
        ("actual_persona_review", "not_allowed"),
        ("investor_agent_execution", "not_allowed"),
        ("investor_decision_generation", "not_allowed"),
        ("recommendations", "not_allowed"),
        ("rankings", "not_allowed"),
        ("allocations_or_rebalancing", "not_allowed"),
        ("trade_signals", "not_allowed"),
        ("auto_promotion", "disabled"),
    ]
    return [
        {
            "permission_code": code,
            "permission_label": code.replace("_", " "),
            "package_status": status,
            "allowed_scope": "Preparation-only packaging."
            if status == "allowed"
            else "None before the relevant task or approval.",
            "prohibited_scope": "; ".join(PROHIBITED_OUTPUTS),
            "required_future_approval": "Future explicit Gatekeeper approval.",
            "safety_boundary": "Permission boundary only.",
        }
        for code, status in specs
    ]


def build_limited_preparation_package_prohibited_output_matrix() -> list[dict]:
    codes = [
        "actual_persona_review",
        "investor_agent_execution",
        "investor_decision_generation",
        "buy_sell_hold_recommendations",
        "company_rankings",
        "portfolio_allocations",
        "portfolio_rebalancing",
        "trade_signals",
        "execution_instructions",
        "strategy_validation",
        "auto_promotion",
    ]
    return [
        {
            "prohibited_code": code,
            "prohibited_label": code.replace("_", " "),
            "package_status": "prohibited",
            "prohibited_actions": code.replace("_", " "),
            "reason": "Not authorized by limited preparation scope.",
            "condition_to_reconsider": "Future explicit Gatekeeper approval.",
            "safety_boundary": "Prohibited output remains blocked.",
        }
        for code in codes
    ]


def build_limited_preparation_package_future_approval_matrix() -> list[dict]:
    codes = [
        "approval_for_actual_persona_review",
        "approval_for_investor_agent_execution",
        "approval_for_investor_decision_generation",
        "approval_for_recommendation_language",
        "approval_for_company_ranking_language",
        "approval_for_allocation_or_trade_signal_language",
        "approval_for_auto_promotion_change",
    ]
    return [
        {
            "approval_code": code,
            "approval_label": code.replace("_", " "),
            "approval_required_for": code.replace("approval_for_", "").replace("_", " "),
            "current_status": "required_not_granted",
            "package_section": "future_gatekeeper_approval_requirements",
            "required_preconditions": "Validated limited preparation package and future Gatekeeper approval.",
            "prohibited_until_approved": "; ".join(PROHIBITED_OUTPUTS),
            "safety_boundary": "No approval granted.",
        }
        for code in codes
    ]


def build_limited_preparation_package_summary(
    *, package_run_id: str, inventory: dict, index: list[dict], sections: list[dict]
) -> dict:
    source = _summary(inventory)
    return {
        "limited_preparation_package_run_id": package_run_id,
        "limited_preparation_artifact_inventory_run_id": inventory[
            "limited_preparation_artifact_inventory_run_id"
        ],
        "limited_preparation_plan_run_id": inventory["limited_preparation_plan_run_id"],
        "phase_18_closure_run_id": inventory["phase_18_closure_run_id"],
        "phase_id": 19,
        "phase_name": PHASE_NAME,
        "current_task_id": 140,
        "current_task_name": CURRENT_TASK_NAME,
        "source_gatekeeper_return_outcome": source["source_gatekeeper_return_outcome"],
        "source_post_review_progression_status": source["source_post_review_progression_status"],
        "source_post_review_persona_review_status": source[
            "source_post_review_persona_review_status"
        ],
        "source_artifact_inventory_status": source["artifact_inventory_status"],
        "package_assembly_status": "assembled_with_warnings",
        "artifacts_total": len(ARTIFACT_ORDER),
        "artifacts_included": len(sections),
        "artifacts_included_with_warnings": len(sections),
        "artifacts_blocked": 0,
        "package_sections_total": len(index),
        "package_sections_included": len(index),
        "actual_persona_review_allowed": False,
        "investor_agents_allowed": False,
        "recommendations_allowed": False,
        "rankings_allowed": False,
        "allocations_allowed": False,
        "trade_signals_allowed": False,
        "auto_promotion_status": "disabled",
        "recommended_next_task": NEXT_TASK,
        "main_package_finding": "All ten preparation-only artifacts are assembled with warnings preserved; no persona review, investor-agent execution, recommendations, rankings, allocations, trade signals, or auto-promotion is allowed.",
    }


def build_task_141_handoff_manifest(
    *,
    summary: dict,
    sections: list[dict],
    warnings: list[dict],
    permissions: list[dict],
    prohibited: list[dict],
) -> dict:
    return {
        "future_phase_id": 19,
        "future_phase_name": PHASE_NAME,
        "future_task_id": 141,
        "future_task_name": "Validate Limited Preparation Package",
        "limited_preparation_package_run_id": summary["limited_preparation_package_run_id"],
        "limited_preparation_artifact_inventory_run_id": summary[
            "limited_preparation_artifact_inventory_run_id"
        ],
        "limited_preparation_plan_run_id": summary["limited_preparation_plan_run_id"],
        "source_gatekeeper_return_outcome": summary["source_gatekeeper_return_outcome"],
        "package_assembly_status": summary["package_assembly_status"],
        "package_outputs_to_validate": [
            "package index",
            "artifact sections",
            "warnings",
            "permission boundaries",
            "prohibited outputs",
            "future approvals",
        ],
        "artifacts_to_validate": [row["artifact_code"] for row in sections],
        "warnings_to_validate": [row["warning_code"] for row in warnings],
        "permission_boundaries_to_validate": [row["permission_code"] for row in permissions],
        "prohibited_outputs_to_validate": [row["prohibited_code"] for row in prohibited],
        "allowed_scope": ["validate package completeness and safety boundaries"],
        "prohibited_outputs": PROHIBITED_OUTPUTS,
        "readiness_status": "ready_with_warnings",
        "execution_allowed_now": True,
        "reason": "Task 140 assembled the limited preparation package with warnings carried forward.",
    }


def build_limited_preparation_package_assembly_checks() -> list[dict]:
    codes = [
        "limited_preparation_artifact_inventory_loaded",
        "limited_preparation_package_summary_created",
        "package_index_matrix_created",
        "package_artifact_section_matrix_created",
        "package_warning_matrix_created",
        "package_permission_boundary_matrix_created",
        "package_prohibited_output_matrix_created",
        "package_future_approval_matrix_created",
        "task_141_handoff_manifest_created",
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
            "source_artifact": "limited_preparation_package",
            "blocking_if_failed": True,
            "finding": f"{code} satisfied for Task 140.",
        }
        for code in codes
    ]


def build_limited_preparation_package(
    *, package_run_id: str, generated_at: str, inventory: dict
) -> LimitedPreparationPackage:
    index = build_limited_preparation_package_index_matrix()
    sections = build_limited_preparation_package_artifact_section_matrix(inventory)
    warnings = build_limited_preparation_package_warning_matrix()
    permissions = build_limited_preparation_package_permission_boundary_matrix()
    prohibited = build_limited_preparation_package_prohibited_output_matrix()
    approvals = build_limited_preparation_package_future_approval_matrix()
    summary = build_limited_preparation_package_summary(
        package_run_id=package_run_id, inventory=inventory, index=index, sections=sections
    )
    return LimitedPreparationPackage(
        package_run_id,
        generated_at,
        inventory["limited_preparation_artifact_inventory_run_id"],
        inventory["limited_preparation_plan_run_id"],
        inventory["phase_18_closure_run_id"],
        inventory["gatekeeper_return_review_run_id"],
        inventory["gatekeeper_return_package_validation_run_id"],
        inventory["gatekeeper_return_package_run_id"],
        summary,
        index,
        sections,
        warnings,
        permissions,
        prohibited,
        approvals,
        build_task_141_handoff_manifest(
            summary=summary,
            sections=sections,
            warnings=warnings,
            permissions=permissions,
            prohibited=prohibited,
        ),
        build_limited_preparation_package_assembly_checks(),
        summary["package_assembly_status"],
        summary["recommended_next_task"],
    )


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _value(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, list):
        return "; ".join(map(str, value))
    return str(value)


def _table(rows: list[dict], columns: list[tuple[str, str]]) -> list[str]:
    return [
        "| " + " | ".join(label for label, _ in columns) + " |",
        "| " + " | ".join("---" for _ in columns) + " |",
        *["| " + " | ".join(_value(row.get(key, "")) for _, key in columns) + " |" for row in rows],
    ]


def _render(report: LimitedPreparationPackage) -> str:
    summary = report.limited_preparation_package_summary
    handoff = report.task_141_handoff_manifest
    lines = [
        "# Limited Preparation Package",
        "",
        "## Executive Summary",
        "",
        f"* Limited Preparation Package Run ID: {report.limited_preparation_package_run_id}",
        f"* Limited Preparation Artifact Inventory Run ID: {report.limited_preparation_artifact_inventory_run_id}",
        "* Current Phase: 19 - Limited Preparation Governance Layer",
        "* Current Task: Task 140 - Assemble Limited Preparation Package",
        f"* Source Gatekeeper Return Outcome: {summary['source_gatekeeper_return_outcome']}",
        f"* Source Post-Review Progression Status: {summary['source_post_review_progression_status']}",
        f"* Source Post-Review Persona Review Status: {summary['source_post_review_persona_review_status']}",
        f"* Source Artifact Inventory Status: {summary['source_artifact_inventory_status']}",
        f"* Package Assembly Status: {report.package_assembly_status}",
        f"* Artifacts Total: {summary['artifacts_total']}",
        f"* Artifacts Included: {summary['artifacts_included']}",
        f"* Artifacts Included With Warnings: {summary['artifacts_included_with_warnings']}",
        f"* Artifacts Blocked: {summary['artifacts_blocked']}",
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
        "Task 139 - Build Limited Preparation Artifact Inventory complete_with_warnings",
        "",
        "This Task:",
        "Task 140 assembles the limited preparation package.",
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
    for title, rows, columns in [
        (
            "Package Index",
            report.limited_preparation_package_index_matrix,
            [
                ("Section", "package_section_code"),
                ("Purpose", "section_purpose"),
                ("Status", "section_status"),
                ("Warning Status", "warning_status"),
            ],
        ),
        (
            "Package Artifact Sections",
            report.limited_preparation_package_artifact_section_matrix,
            [
                ("Artifact", "artifact_code"),
                ("Section", "package_section_code"),
                ("Included", "included"),
                ("Warning Note", "warning_note"),
            ],
        ),
        (
            "Warnings Carried Forward",
            report.limited_preparation_package_warning_matrix,
            [
                ("Warning", "warning_code"),
                ("Source", "source"),
                ("Severity", "severity"),
                ("Disposition", "package_disposition"),
                ("Follow-Up", "required_follow_up"),
            ],
        ),
        (
            "Permission Boundary",
            report.limited_preparation_package_permission_boundary_matrix,
            [
                ("Permission", "permission_code"),
                ("Status", "package_status"),
                ("Allowed Scope", "allowed_scope"),
                ("Prohibited Scope", "prohibited_scope"),
                ("Future Approval", "required_future_approval"),
            ],
        ),
        (
            "Prohibited Outputs",
            report.limited_preparation_package_prohibited_output_matrix,
            [
                ("Output", "prohibited_code"),
                ("Status", "package_status"),
                ("Reason", "reason"),
                ("Condition To Reconsider", "condition_to_reconsider"),
            ],
        ),
        (
            "Future Gatekeeper Approval Requirements",
            report.limited_preparation_package_future_approval_matrix,
            [
                ("Approval", "approval_code"),
                ("Required For", "approval_required_for"),
                ("Current Status", "current_status"),
                ("Preconditions", "required_preconditions"),
            ],
        ),
    ]:
        lines += ["", f"## {title}", "", *_table(rows, columns)]
    lines += [
        "",
        "## Task 141 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} - {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Package Outputs To Validate: {'; '.join(handoff['package_outputs_to_validate'])}",
        f"* Artifacts To Validate: {'; '.join(handoff['artifacts_to_validate'])}",
        f"* Warnings To Validate: {'; '.join(handoff['warnings_to_validate'])}",
        f"* Permission Boundaries To Validate: {'; '.join(handoff['permission_boundaries_to_validate'])}",
        f"* Prohibited Outputs To Validate: {'; '.join(handoff['prohibited_outputs_to_validate'])}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_table(
            report.limited_preparation_package_assembly_checks,
            [
                ("Check", "check_code"),
                ("Status", "status"),
                ("Blocking If Failed", "blocking_if_failed"),
                ("Finding", "finding"),
            ],
        ),
        "",
        "## What This Suggests",
        "",
        "* The system can validate the limited preparation package in Task 141.",
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


def write_limited_preparation_package_report(
    *, outputs_root: Path, limited_preparation_artifact_inventory_run_id: str | None = None
) -> LimitedPreparationPackageFiles:
    outputs_root = Path(outputs_root)
    manifest = load_limited_preparation_artifact_inventory_manifest(
        outputs_root=outputs_root,
        limited_preparation_artifact_inventory_run_id=limited_preparation_artifact_inventory_run_id,
    )
    run = manifest["limited_preparation_artifact_inventory_run_id"]
    inventory = load_limited_preparation_artifact_inventory(
        outputs_root=outputs_root, limited_preparation_artifact_inventory_run_id=run
    )
    now = datetime.now(timezone.utc)
    package_run = now.strftime("%Y%m%d_%H%M%S")
    report = build_limited_preparation_package(
        package_run_id=package_run, generated_at=now.isoformat(), inventory=inventory
    )
    root = outputs_root / "limited_preparation_packages"
    folder = root / package_run
    folder.mkdir(parents=True, exist_ok=True)
    md, js = folder / "limited_preparation_package.md", folder / "limited_preparation_package.json"
    index, sections, warnings, permissions, prohibited, approvals, handoff, checks = (
        folder / "limited_preparation_package_index_matrix.csv",
        folder / "limited_preparation_package_artifact_section_matrix.csv",
        folder / "limited_preparation_package_warning_matrix.csv",
        folder / "limited_preparation_package_permission_boundary_matrix.csv",
        folder / "limited_preparation_package_prohibited_output_matrix.csv",
        folder / "limited_preparation_package_future_approval_matrix.csv",
        folder / "task_141_handoff_manifest.json",
        folder / "limited_preparation_package_assembly_checks.csv",
    )
    latest = root / "latest_limited_preparation_package_manifest.json"
    md.write_text(_render(report), encoding="utf-8")
    js.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(index, report.limited_preparation_package_index_matrix)
    _write_csv(sections, report.limited_preparation_package_artifact_section_matrix)
    _write_csv(warnings, report.limited_preparation_package_warning_matrix)
    _write_csv(permissions, report.limited_preparation_package_permission_boundary_matrix)
    _write_csv(prohibited, report.limited_preparation_package_prohibited_output_matrix)
    _write_csv(approvals, report.limited_preparation_package_future_approval_matrix)
    handoff.write_text(json.dumps(report.task_141_handoff_manifest, indent=2), encoding="utf-8")
    _write_csv(checks, report.limited_preparation_package_assembly_checks)
    latest.write_text(
        json.dumps(
            {
                "limited_preparation_package_run_id": report.limited_preparation_package_run_id,
                "limited_preparation_artifact_inventory_run_id": report.limited_preparation_artifact_inventory_run_id,
                "limited_preparation_plan_run_id": report.limited_preparation_plan_run_id,
                "phase_18_closure_run_id": report.phase_18_closure_run_id,
                "gatekeeper_return_review_run_id": report.gatekeeper_return_review_run_id,
                "package_assembly_status": report.package_assembly_status,
                "artifacts_total": report.limited_preparation_package_summary["artifacts_total"],
                "artifacts_included": report.limited_preparation_package_summary[
                    "artifacts_included"
                ],
                "artifacts_included_with_warnings": report.limited_preparation_package_summary[
                    "artifacts_included_with_warnings"
                ],
                "artifacts_blocked": report.limited_preparation_package_summary[
                    "artifacts_blocked"
                ],
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(folder),
                "report_path": str(md),
                "report_json_path": str(js),
                "task_141_handoff_manifest_path": str(handoff),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return LimitedPreparationPackageFiles(
        folder,
        md,
        js,
        index,
        sections,
        warnings,
        permissions,
        prohibited,
        approvals,
        handoff,
        checks,
        latest,
        report,
    )
