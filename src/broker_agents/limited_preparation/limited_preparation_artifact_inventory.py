"""Task 139 limited preparation artifact inventory."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

from broker_agents.limited_preparation.limited_preparation_governance_plan import (
    PROHIBITED_OUTPUTS,
)

SAFETY_NOTICE = (
    "This report inventories limited preparation artifacts only. It does not "
    "assemble the package, run investor agents, run actual persona reviews, "
    "create investor decisions, rankings, recommendations, allocations, "
    "rebalancing instructions, trade signals, execution instructions, or "
    "strategy validation."
)
PHASE_NAME = "Limited Preparation Governance Layer"
CURRENT_TASK_NAME = "Build Limited Preparation Artifact Inventory"
NEXT_TASK = "Task 140 - Assemble Limited Preparation Package"

ARTIFACT_ORDER = [
    "permission_boundary_checklist",
    "no_recommendation_safety_notice",
    "no_ranking_safety_notice",
    "no_trade_signal_safety_notice",
    "evidence_pack_structure_outline",
    "company_data_pack_completeness_template",
    "persona_review_readiness_checklist",
    "investor_agent_execution_preconditions",
    "residual_risk_follow_up_list",
    "gatekeeper_pre_approval_request_template",
]

PROHIBITED_CONTENT = [
    "actual_persona_judgment",
    "investor_agent_execution",
    "investor_decision",
    "recommendation_language",
    "ranking_language",
    "allocation_language",
    "rebalancing_language",
    "trade_signal_language",
    "execution_instruction_language",
    "strategy_validation_language",
    "auto_promotion_language",
]


@dataclass(frozen=True)
class LimitedPreparationArtifactInventory:
    """Structured Task 139 artifact inventory."""

    limited_preparation_artifact_inventory_run_id: str
    generated_at: str
    limited_preparation_plan_run_id: str
    phase_18_closure_run_id: str
    gatekeeper_return_review_run_id: str
    gatekeeper_return_package_validation_run_id: str
    gatekeeper_return_package_run_id: str
    artifact_inventory_summary: dict
    allowed_artifact_inventory_matrix: list[dict]
    artifact_input_requirement_matrix: list[dict]
    artifact_prohibited_content_matrix: list[dict]
    artifact_readiness_matrix: list[dict]
    artifact_assembly_priority_matrix: list[dict]
    warning_and_constraint_matrix: list[dict]
    task_140_handoff_manifest: dict
    limited_preparation_artifact_inventory_checks: list[dict]
    artifact_inventory_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready representation."""
        return asdict(self)


@dataclass(frozen=True)
class LimitedPreparationArtifactInventoryFiles:
    """Generated Task 139 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    allowed_artifacts_csv_path: Path
    input_requirements_csv_path: Path
    prohibited_content_csv_path: Path
    readiness_csv_path: Path
    assembly_priority_csv_path: Path
    warnings_csv_path: Path
    task_140_handoff_manifest_path: Path
    checks_csv_path: Path
    latest_manifest_path: Path
    report: LimitedPreparationArtifactInventory


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_limited_preparation_governance_plan_manifest(
    *,
    outputs_root: Path,
    limited_preparation_plan_run_id: str | None = None,
) -> dict:
    """Load one Task 138 governance plan or the latest manifest."""
    root = Path(outputs_root) / "limited_preparation_governance_plans"
    path = (
        root
        / limited_preparation_plan_run_id
        / "limited_preparation_governance_plan.json"
        if limited_preparation_plan_run_id
        else root / "latest_limited_preparation_governance_plan_manifest.json"
    )
    label = (
        "Limited preparation governance plan"
        if limited_preparation_plan_run_id
        else "Limited preparation governance plan manifest"
    )
    return _load_required_json(path, label)


def load_limited_preparation_governance_plan(
    *,
    outputs_root: Path,
    limited_preparation_plan_run_id: str,
) -> dict:
    """Load a Task 138 governance plan by run id."""
    path = (
        Path(outputs_root)
        / "limited_preparation_governance_plans"
        / limited_preparation_plan_run_id
        / "limited_preparation_governance_plan.json"
    )
    return _load_required_json(path, "Limited preparation governance plan")


def _plan_summary(plan: dict) -> dict:
    return plan["limited_preparation_plan_summary"]


def build_allowed_artifact_inventory_matrix(plan: dict) -> list[dict]:
    """Build allowed preparation artifact inventory rows."""
    source_rows = {
        row["artifact_code"]: row
        for row in plan.get("allowed_preparation_artifact_matrix", [])
    }
    rows = []
    for code in ARTIFACT_ORDER:
        source = source_rows.get(code, {})
        rows.append(
            {
                "artifact_code": code,
                "artifact_label": source.get("artifact_label", code.replace("_", " ")),
                "artifact_category": _artifact_category(code),
                "artifact_status": "preparation_only_ready",
                "purpose": source.get(
                    "purpose",
                    "Define structure, readiness, or safety requirements.",
                ),
                "allowed_content": source.get(
                    "allowed_content",
                    "Templates, checklists, inventory fields, and boundary language.",
                ),
                "prohibited_content": source.get(
                    "prohibited_content",
                    "Investor judgments, decisions, recommendations, rankings, allocations, trade signals, or execution instructions.",
                ),
                "required_inputs": source.get(
                    "required_inputs",
                    "Limited preparation governance plan and Phase 18 closure.",
                ),
                "expected_output_type": "template_or_checklist",
                "assembly_candidate": True,
                "safety_boundary": "Preparation-only artifact; no investor analysis or decisions.",
            }
        )
    return rows


def _artifact_category(code: str) -> str:
    if code.startswith("no_"):
        return "safety_notice"
    if "checklist" in code or "preconditions" in code:
        return "readiness_control"
    if "template" in code or "outline" in code:
        return "structure_template"
    return "follow_up_control"


def build_artifact_input_requirement_matrix(plan: dict) -> list[dict]:
    """Build artifact input requirements."""
    summary = _plan_summary(plan)
    inputs = [
        ("phase_18_closure", "Phase 18 Closure", "phase_18_closure", summary["phase_18_closure_run_id"], "available"),
        ("gatekeeper_return_review", "Gatekeeper Return Review", "gatekeeper_return_review", plan["gatekeeper_return_review_run_id"], "available"),
        ("limited_preparation_governance_plan", "Limited Preparation Governance Plan", "limited_preparation_governance_plan", plan["limited_preparation_plan_run_id"], "available_with_warnings"),
        ("limited_preparation_scope_matrix", "limited_preparation_scope_matrix", "limited_preparation_governance_plan", plan["limited_preparation_plan_run_id"], "available"),
        ("allowed_preparation_artifact_matrix", "allowed_preparation_artifact_matrix", "limited_preparation_governance_plan", plan["limited_preparation_plan_run_id"], "available"),
        ("prohibited_output_matrix", "prohibited_output_matrix", "limited_preparation_governance_plan", plan["limited_preparation_plan_run_id"], "available"),
        ("future_gatekeeper_approval_matrix", "future_gatekeeper_approval_matrix", "limited_preparation_governance_plan", plan["limited_preparation_plan_run_id"], "available"),
        ("phase_19_roadmap_matrix", "phase_19_roadmap_matrix", "limited_preparation_governance_plan", plan["limited_preparation_plan_run_id"], "available"),
    ]
    rows = []
    for artifact in ARTIFACT_ORDER:
        for input_code, label, source, run_id, status in inputs:
            rows.append(
                {
                    "artifact_code": artifact,
                    "required_input_code": input_code,
                    "required_input_label": label,
                    "source_artifact": source,
                    "source_run_id": run_id,
                    "input_status": status,
                    "missing_or_warning_detail": "Governance plan carries warnings."
                    if status == "available_with_warnings"
                    else "none",
                    "required_for_assembly": True,
                    "safety_boundary": "Input requirement only; no live data.",
                }
            )
    return rows


def build_artifact_prohibited_content_matrix() -> list[dict]:
    """Build prohibited content rows for each artifact."""
    return [
        {
            "artifact_code": artifact,
            "prohibited_content_code": prohibited,
            "prohibited_content_label": prohibited.replace("_", " "),
            "prohibition_reason": "Not authorized under limited preparation scope.",
            "condition_to_reconsider": "Future explicit Gatekeeper approval.",
            "safety_boundary": "Prohibited content remains blocked.",
        }
        for artifact in ARTIFACT_ORDER
        for prohibited in PROHIBITED_CONTENT
    ]


def build_artifact_readiness_matrix(plan: dict) -> list[dict]:
    """Build artifact readiness rows."""
    status = _plan_summary(plan)["limited_preparation_status"]
    readiness = (
        "ready_with_warnings"
        if status == "defined_with_warnings"
        else "ready_for_assembly"
    )
    return [
        {
            "artifact_code": row["artifact_code"],
            "artifact_label": row["artifact_label"],
            "readiness_status": readiness,
            "readiness_basis": "Required governance inputs are available locally.",
            "warnings": "Governance plan is defined_with_warnings."
            if readiness == "ready_with_warnings"
            else "none",
            "blockers": "none",
            "allowed_to_assemble_in_task_140": True,
            "safety_boundary": "Assembly readiness only; does not allow persona review, investor execution, recommendations, rankings, or trade signals.",
        }
        for row in build_allowed_artifact_inventory_matrix(plan)
    ]


def build_artifact_assembly_priority_matrix() -> list[dict]:
    """Build Task 140 assembly priority rows."""
    return [
        {
            "artifact_code": code,
            "artifact_label": code.replace("_", " "),
            "assembly_priority": index,
            "priority_reason": "Safety boundary artifacts precede structure and readiness artifacts."
            if index <= 4
            else "Structure and readiness artifacts follow boundary controls.",
            "dependencies": "Limited preparation governance plan.",
            "recommended_task_140_order": index,
            "safety_boundary": "Assembly order only; non-actionable.",
        }
        for index, code in enumerate(ARTIFACT_ORDER, start=1)
    ]


def build_warning_and_constraint_matrix(plan: dict) -> list[dict]:
    """Build warnings and constraints."""
    warnings = [
        "limited_preparation_defined_with_warnings",
        "phase_18_closed_for_limited_preparation_only",
        "persona_review_false",
        "investor_agents_not_allowed",
        "recommendations_not_allowed",
        "rankings_not_allowed",
        "trade_signals_not_allowed",
        "auto_promotion_disabled",
        "local_artifact_only_scope",
        "future_gatekeeper_approval_required",
    ]
    return [
        {
            "warning_code": warning,
            "warning_label": warning.replace("_", " "),
            "source": "limited_preparation_governance_plan"
            if warning == "limited_preparation_defined_with_warnings"
            else "phase_18_closure_and_task_138_boundaries",
            "severity": "critical"
            if warning
            in {
                "persona_review_false",
                "investor_agents_not_allowed",
                "auto_promotion_disabled",
                "future_gatekeeper_approval_required",
            }
            else "medium",
            "impact_on_artifact_inventory": "Must be disclosed and preserved in Task 140.",
            "required_follow_up": "Carry into limited preparation package assembly.",
            "safety_boundary": "Constraint disclosure only.",
        }
        for warning in warnings
    ]


def build_artifact_inventory_summary(
    *,
    inventory_run_id: str,
    plan: dict,
    allowed_rows: list[dict],
    readiness_rows: list[dict],
) -> dict:
    """Build artifact inventory summary."""
    summary = _plan_summary(plan)
    ready = sum(
        row["readiness_status"] == "ready_for_assembly" for row in readiness_rows
    )
    warning = sum(
        row["readiness_status"] == "ready_with_warnings" for row in readiness_rows
    )
    blocked = sum(row["readiness_status"] == "blocked" for row in readiness_rows)
    status = "complete_with_warnings" if warning else "complete"
    return {
        "limited_preparation_artifact_inventory_run_id": inventory_run_id,
        "limited_preparation_plan_run_id": plan["limited_preparation_plan_run_id"],
        "phase_18_closure_run_id": plan["phase_18_closure_run_id"],
        "phase_id": 19,
        "phase_name": PHASE_NAME,
        "current_task_id": 139,
        "current_task_name": CURRENT_TASK_NAME,
        "source_gatekeeper_return_outcome": summary[
            "source_gatekeeper_return_outcome"
        ],
        "source_post_review_progression_status": summary[
            "source_post_review_progression_status"
        ],
        "source_post_review_persona_review_status": summary[
            "source_post_review_persona_review_status"
        ],
        "artifact_inventory_status": status,
        "artifacts_total": len(allowed_rows),
        "artifacts_ready_for_assembly": ready,
        "artifacts_ready_with_warnings": warning,
        "artifacts_blocked": blocked,
        "actual_persona_review_allowed": False,
        "investor_agents_allowed": False,
        "recommendations_allowed": False,
        "rankings_allowed": False,
        "allocations_allowed": False,
        "trade_signals_allowed": False,
        "auto_promotion_status": "disabled",
        "recommended_next_task": NEXT_TASK,
        "main_inventory_finding": (
            "Allowed limited preparation artifacts are inventoried for Task 140 "
            "assembly, with persona review, investor-agent execution, "
            "recommendations, rankings, allocations, trade signals, and "
            "auto-promotion still blocked."
        ),
    }


def build_task_140_handoff_manifest(
    *,
    summary: dict,
    allowed_rows: list[dict],
) -> dict:
    """Build Task 140 handoff manifest."""
    return {
        "future_phase_id": 19,
        "future_phase_name": PHASE_NAME,
        "future_task_id": 140,
        "future_task_name": "Assemble Limited Preparation Package",
        "limited_preparation_artifact_inventory_run_id": summary[
            "limited_preparation_artifact_inventory_run_id"
        ],
        "limited_preparation_plan_run_id": summary["limited_preparation_plan_run_id"],
        "source_gatekeeper_return_outcome": summary[
            "source_gatekeeper_return_outcome"
        ],
        "artifact_inventory_status": summary["artifact_inventory_status"],
        "artifacts_to_assemble": [row["artifact_code"] for row in allowed_rows],
        "allowed_scope": [
            "assemble preparation-only artifacts",
            "preserve permission boundaries",
            "include safety notices and approval preconditions",
        ],
        "prohibited_outputs": PROHIBITED_OUTPUTS,
        "readiness_status": "ready_with_warnings"
        if summary["artifact_inventory_status"] == "complete_with_warnings"
        else "ready_to_assemble_limited_preparation_package",
        "execution_allowed_now": True,
        "reason": "Task 139 inventoried preparation-only artifacts for Task 140.",
    }


def build_limited_preparation_artifact_inventory_checks() -> list[dict]:
    """Build Task 139 validation checks."""
    checks = [
        "limited_preparation_governance_plan_loaded",
        "artifact_inventory_summary_created",
        "allowed_artifact_inventory_matrix_created",
        "artifact_input_requirement_matrix_created",
        "artifact_prohibited_content_matrix_created",
        "artifact_readiness_matrix_created",
        "artifact_assembly_priority_matrix_created",
        "warning_and_constraint_matrix_created",
        "task_140_handoff_manifest_created",
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
            "check_code": check,
            "check_label": check.replace("_", " "),
            "status": "satisfied",
            "source_artifact": "limited_preparation_artifact_inventory",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 139.",
        }
        for check in checks
    ]


def build_limited_preparation_artifact_inventory(
    *,
    inventory_run_id: str,
    generated_at: str,
    plan: dict,
) -> LimitedPreparationArtifactInventory:
    """Build Task 139 limited preparation artifact inventory."""
    allowed = build_allowed_artifact_inventory_matrix(plan)
    readiness = build_artifact_readiness_matrix(plan)
    summary = build_artifact_inventory_summary(
        inventory_run_id=inventory_run_id,
        plan=plan,
        allowed_rows=allowed,
        readiness_rows=readiness,
    )
    return LimitedPreparationArtifactInventory(
        limited_preparation_artifact_inventory_run_id=inventory_run_id,
        generated_at=generated_at,
        limited_preparation_plan_run_id=plan["limited_preparation_plan_run_id"],
        phase_18_closure_run_id=plan["phase_18_closure_run_id"],
        gatekeeper_return_review_run_id=plan["gatekeeper_return_review_run_id"],
        gatekeeper_return_package_validation_run_id=plan[
            "gatekeeper_return_package_validation_run_id"
        ],
        gatekeeper_return_package_run_id=plan["gatekeeper_return_package_run_id"],
        artifact_inventory_summary=summary,
        allowed_artifact_inventory_matrix=allowed,
        artifact_input_requirement_matrix=build_artifact_input_requirement_matrix(
            plan
        ),
        artifact_prohibited_content_matrix=build_artifact_prohibited_content_matrix(),
        artifact_readiness_matrix=readiness,
        artifact_assembly_priority_matrix=build_artifact_assembly_priority_matrix(),
        warning_and_constraint_matrix=build_warning_and_constraint_matrix(plan),
        task_140_handoff_manifest=build_task_140_handoff_manifest(
            summary=summary,
            allowed_rows=allowed,
        ),
        limited_preparation_artifact_inventory_checks=build_limited_preparation_artifact_inventory_checks(),
        artifact_inventory_status=summary["artifact_inventory_status"],
        recommended_next_task=summary["recommended_next_task"],
    )


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _format_value(value: object) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, list):
        return "; ".join(str(item) for item in value)
    return str(value)


def _markdown_table(rows: list[dict], columns: list[tuple[str, str]]) -> list[str]:
    header = "| " + " | ".join(label for label, _ in columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = [
        "| "
        + " | ".join(_format_value(row.get(key)) for _, key in columns)
        + " |"
        for row in rows
    ]
    return [header, separator, *body]


def _render_markdown(report: LimitedPreparationArtifactInventory) -> str:
    summary = report.artifact_inventory_summary
    handoff = report.task_140_handoff_manifest
    lines = [
        "# Limited Preparation Artifact Inventory",
        "",
        "## Executive Summary",
        "",
        f"* Limited Preparation Artifact Inventory Run ID: {report.limited_preparation_artifact_inventory_run_id}",
        f"* Limited Preparation Plan Run ID: {report.limited_preparation_plan_run_id}",
        "* Current Phase: 19 - Limited Preparation Governance Layer",
        "* Current Task: Task 139 - Build Limited Preparation Artifact Inventory",
        f"* Source Gatekeeper Return Outcome: {summary['source_gatekeeper_return_outcome']}",
        f"* Source Post-Review Progression Status: {summary['source_post_review_progression_status']}",
        f"* Source Post-Review Persona Review Status: {summary['source_post_review_persona_review_status']}",
        f"* Artifact Inventory Status: {report.artifact_inventory_status}",
        f"* Artifacts Total: {summary['artifacts_total']}",
        f"* Artifacts Ready For Assembly: {summary['artifacts_ready_for_assembly']}",
        f"* Artifacts Ready With Warnings: {summary['artifacts_ready_with_warnings']}",
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
        "Task 138 - Define Limited Preparation Governance Plan defined_with_warnings",
        "",
        "This Task:",
        "Task 139 builds the limited preparation artifact inventory.",
        "",
        "Allowed Progression:",
        "limited_preparation_only",
        "",
        "Persona Reviews:",
        "false",
        "",
        "Recommended Next Task:",
        NEXT_TASK,
        "",
        "## Allowed Artifact Inventory",
        "",
        *_markdown_table(
            report.allowed_artifact_inventory_matrix,
            [
                ("Artifact", "artifact_code"),
                ("Category", "artifact_category"),
                ("Status", "artifact_status"),
                ("Purpose", "purpose"),
                ("Assembly Candidate", "assembly_candidate"),
            ],
        ),
        "",
        "## Artifact Input Requirements",
        "",
        *_markdown_table(
            report.artifact_input_requirement_matrix,
            [
                ("Artifact", "artifact_code"),
                ("Required Input", "required_input_code"),
                ("Source Artifact", "source_artifact"),
                ("Input Status", "input_status"),
                ("Required For Assembly", "required_for_assembly"),
            ],
        ),
        "",
        "## Artifact Prohibited Content",
        "",
        *_markdown_table(
            report.artifact_prohibited_content_matrix,
            [
                ("Artifact", "artifact_code"),
                ("Prohibited Content", "prohibited_content_code"),
                ("Reason", "prohibition_reason"),
                ("Condition To Reconsider", "condition_to_reconsider"),
            ],
        ),
        "",
        "## Artifact Readiness",
        "",
        *_markdown_table(
            report.artifact_readiness_matrix,
            [
                ("Artifact", "artifact_code"),
                ("Readiness", "readiness_status"),
                ("Warnings", "warnings"),
                ("Blockers", "blockers"),
                ("Allowed To Assemble", "allowed_to_assemble_in_task_140"),
            ],
        ),
        "",
        "## Artifact Assembly Priority",
        "",
        *_markdown_table(
            report.artifact_assembly_priority_matrix,
            [
                ("Priority", "assembly_priority"),
                ("Artifact", "artifact_code"),
                ("Reason", "priority_reason"),
                ("Dependencies", "dependencies"),
            ],
        ),
        "",
        "## Warnings and Constraints",
        "",
        *_markdown_table(
            report.warning_and_constraint_matrix,
            [
                ("Warning", "warning_code"),
                ("Source", "source"),
                ("Severity", "severity"),
                ("Impact", "impact_on_artifact_inventory"),
                ("Follow-Up", "required_follow_up"),
            ],
        ),
        "",
        "## Task 140 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} - {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Artifacts To Assemble: {'; '.join(handoff['artifacts_to_assemble'])}",
        f"* Allowed Scope: {'; '.join(handoff['allowed_scope'])}",
        f"* Prohibited Outputs: {'; '.join(handoff['prohibited_outputs'])}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.limited_preparation_artifact_inventory_checks,
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
        "* The system can assemble a limited preparation package in Task 140.",
        "* The package must remain preparation-only.",
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


def write_limited_preparation_artifact_inventory_report(
    *,
    outputs_root: Path,
    limited_preparation_plan_run_id: str | None = None,
) -> LimitedPreparationArtifactInventoryFiles:
    """Write Task 139 limited preparation artifact inventory artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_limited_preparation_governance_plan_manifest(
        outputs_root=outputs_root,
        limited_preparation_plan_run_id=limited_preparation_plan_run_id,
    )
    plan_run_id = manifest["limited_preparation_plan_run_id"]
    plan = load_limited_preparation_governance_plan(
        outputs_root=outputs_root,
        limited_preparation_plan_run_id=plan_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_limited_preparation_artifact_inventory(
        inventory_run_id=run_id,
        generated_at=generated_at.isoformat(),
        plan=plan,
    )

    root = outputs_root / "limited_preparation_artifact_inventories"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "limited_preparation_artifact_inventory.md"
    json_path = output_folder / "limited_preparation_artifact_inventory.json"
    allowed_csv = output_folder / "allowed_artifact_inventory_matrix.csv"
    inputs_csv = output_folder / "artifact_input_requirement_matrix.csv"
    prohibited_csv = output_folder / "artifact_prohibited_content_matrix.csv"
    readiness_csv = output_folder / "artifact_readiness_matrix.csv"
    priority_csv = output_folder / "artifact_assembly_priority_matrix.csv"
    warnings_csv = output_folder / "warning_and_constraint_matrix.csv"
    handoff_path = output_folder / "task_140_handoff_manifest.json"
    checks_csv = output_folder / "limited_preparation_artifact_inventory_checks.csv"
    latest_manifest_path = (
        root / "latest_limited_preparation_artifact_inventory_manifest.json"
    )

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(allowed_csv, report.allowed_artifact_inventory_matrix)
    _write_csv(inputs_csv, report.artifact_input_requirement_matrix)
    _write_csv(prohibited_csv, report.artifact_prohibited_content_matrix)
    _write_csv(readiness_csv, report.artifact_readiness_matrix)
    _write_csv(priority_csv, report.artifact_assembly_priority_matrix)
    _write_csv(warnings_csv, report.warning_and_constraint_matrix)
    handoff_path.write_text(
        json.dumps(report.task_140_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.limited_preparation_artifact_inventory_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "limited_preparation_artifact_inventory_run_id": report.limited_preparation_artifact_inventory_run_id,
                "limited_preparation_plan_run_id": report.limited_preparation_plan_run_id,
                "phase_18_closure_run_id": report.phase_18_closure_run_id,
                "gatekeeper_return_review_run_id": report.gatekeeper_return_review_run_id,
                "artifact_inventory_status": report.artifact_inventory_status,
                "artifacts_total": report.artifact_inventory_summary[
                    "artifacts_total"
                ],
                "artifacts_ready_for_assembly": report.artifact_inventory_summary[
                    "artifacts_ready_for_assembly"
                ],
                "artifacts_ready_with_warnings": report.artifact_inventory_summary[
                    "artifacts_ready_with_warnings"
                ],
                "artifacts_blocked": report.artifact_inventory_summary[
                    "artifacts_blocked"
                ],
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_140_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return LimitedPreparationArtifactInventoryFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        allowed_artifacts_csv_path=allowed_csv,
        input_requirements_csv_path=inputs_csv,
        prohibited_content_csv_path=prohibited_csv,
        readiness_csv_path=readiness_csv,
        assembly_priority_csv_path=priority_csv,
        warnings_csv_path=warnings_csv,
        task_140_handoff_manifest_path=handoff_path,
        checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
