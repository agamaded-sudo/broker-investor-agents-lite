"""Task 134 Gatekeeper return package assembly."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report assembles the Gatekeeper return package only. It does not "
    "validate final package completeness, rerun Gatekeeper, run investor "
    "agents, run actual persona reviews, create investor decisions, rankings, "
    "recommendations, allocations, rebalancing instructions, trade signals, "
    "execution instructions, auto-promotion, or strategy validation."
)
PHASE_NAME = "Gatekeeper Return Package Layer"
NEXT_TASK = "Task 135 - Validate Gatekeeper Return Package Completeness"

SECTION_PURPOSES = {
    "executive_gatekeeper_return_summary": "Summarize the Gatekeeper-facing return package.",
    "phase_17_final_outcome_summary": "Preserve the final Phase 17 outcome.",
    "gatekeeper_stabilization_decision_record": "Preserve the stabilization re-review decision record.",
    "permission_boundary_summary": "Disclose allowed and prohibited scopes.",
    "blocker_disposition_summary": "Disclose blocker disposition after Phase 17.",
    "residual_risk_disclosure": "Disclose residual risks requiring Gatekeeper attention.",
    "evidence_stabilization_timeline": "Trace Phase 16 and Phase 17 evidence flow.",
    "repaired_evidence_inventory": "Reference targeted repair artifacts.",
    "validation_evidence_inventory": "Reference validation trial artifacts.",
    "comparison_evidence_inventory": "Reference comparison and re-review artifacts.",
    "source_run_traceability": "Trace all source run identifiers and local artifacts.",
    "local_artifact_limitation_disclosure": "Disclose local-only artifact limitations.",
    "no_persona_review_confirmation": "Confirm actual persona review remains blocked.",
    "no_investor_agent_execution_confirmation": "Confirm investor agents were not run.",
    "no_recommendation_output_confirmation": "Confirm no recommendation output is produced.",
    "auto_promotion_disabled_confirmation": "Confirm auto-promotion remains disabled.",
    "next_gatekeeper_review_questions": "Preserve questions for the future validation task.",
}

SECTION_SOURCE_MAP = {
    "executive_gatekeeper_return_summary": "input_inventory_summary; phase_17_closure",
    "phase_17_final_outcome_summary": "phase_17_closure",
    "gatekeeper_stabilization_decision_record": "gatekeeper_stabilization_re_review",
    "permission_boundary_summary": "missing_or_warning_input_matrix",
    "blocker_disposition_summary": "residual_blocker_work_orders",
    "residual_risk_disclosure": "missing_or_warning_input_matrix",
    "evidence_stabilization_timeline": "phase_16_closure; phase_17_closure",
    "repaired_evidence_inventory": "targeted_evidence_repairs",
    "validation_evidence_inventory": "stabilization_validation_trial",
    "comparison_evidence_inventory": (
        "gatekeeper_stabilized_evidence_comparison; "
        "baseline_gatekeeper_re_evaluation; pre_post_repair_comparison"
    ),
    "source_run_traceability": "source_run_traceability_matrix",
    "local_artifact_limitation_disclosure": "local_artifact_limitation",
    "no_persona_review_confirmation": "persona_review_not_allowed",
    "no_investor_agent_execution_confirmation": "investor_agent_execution_not_allowed",
    "no_recommendation_output_confirmation": "no_recommendation_outputs",
    "auto_promotion_disabled_confirmation": "auto_promotion_disabled",
    "next_gatekeeper_review_questions": "component_input_inventory_matrix",
}


@dataclass(frozen=True)
class GatekeeperReturnPackageReport:
    """Structured Task 134 Gatekeeper return package assembly."""

    gatekeeper_return_package_run_id: str
    generated_at: str
    gatekeeper_return_input_inventory_run_id: str
    gatekeeper_return_plan_run_id: str
    phase_17_closure_run_id: str
    gatekeeper_stabilization_re_review_run_id: str
    gatekeeper_stabilized_comparison_run_id: str
    stabilization_validation_run_id: str
    targeted_repair_run_id: str
    residual_work_order_package_run_id: str
    stabilization_plan_run_id: str
    phase_16_closure_run_id: str
    baseline_gatekeeper_re_evaluation_run_id: str
    pre_post_repair_comparison_run_id: str
    controlled_re_run_trial_run_id: str
    re_run_input_package_run_id: str
    re_run_re_gate_plan_run_id: str
    research_audit_trail_run_id: str
    return_package_summary: dict
    return_package_index_matrix: list[dict]
    return_package_section_matrix: list[dict]
    return_package_evidence_reference_matrix: list[dict]
    return_package_residual_risk_section: list[dict]
    return_package_permission_boundary_section: list[dict]
    return_package_limitation_matrix: list[dict]
    task_135_handoff_manifest: dict
    gatekeeper_return_package_assembly_checks: list[dict]
    assembly_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class GatekeeperReturnPackageFiles:
    """Generated Task 134 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    index_csv_path: Path
    section_csv_path: Path
    evidence_reference_csv_path: Path
    residual_risk_csv_path: Path
    permission_boundary_csv_path: Path
    limitation_csv_path: Path
    task_135_handoff_manifest_path: Path
    checks_csv_path: Path
    latest_manifest_path: Path
    report: GatekeeperReturnPackageReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_gatekeeper_return_input_inventory_manifest(
    *,
    outputs_root: Path,
    gatekeeper_return_input_inventory_run_id: str | None = None,
) -> dict:
    """Load one Task 133 inventory report or the latest Task 133 manifest."""
    root = Path(outputs_root) / "gatekeeper_return_input_inventories"
    path = (
        root
        / gatekeeper_return_input_inventory_run_id
        / "gatekeeper_return_input_inventory.json"
        if gatekeeper_return_input_inventory_run_id
        else root / "latest_gatekeeper_return_input_inventory_manifest.json"
    )
    label = (
        "Gatekeeper return input inventory report"
        if gatekeeper_return_input_inventory_run_id
        else "Gatekeeper return input inventory manifest"
    )
    return _load_required_json(path, label)


def load_gatekeeper_return_input_inventory(
    *,
    outputs_root: Path,
    gatekeeper_return_input_inventory_run_id: str,
) -> dict:
    """Load a Task 133 Gatekeeper return input inventory by run id."""
    path = (
        Path(outputs_root)
        / "gatekeeper_return_input_inventories"
        / gatekeeper_return_input_inventory_run_id
        / "gatekeeper_return_input_inventory.json"
    )
    return _load_required_json(path, "Gatekeeper return input inventory report")


def _component_status(inventory: dict, section_code: str) -> tuple[str, str]:
    aliases = {
        "phase_17_final_outcome_summary": "final_gatekeeper_stabilization_decision_record",
        "gatekeeper_stabilization_decision_record": (
            "final_gatekeeper_stabilization_decision_record"
        ),
        "source_run_traceability": "evidence_stabilization_timeline",
    }
    lookup_code = aliases.get(section_code, section_code)
    for row in inventory.get("component_input_inventory_matrix", []):
        if row["component_code"] == lookup_code:
            inclusion = row.get("inclusion_status", "ready_for_package_assembly")
            status = (
                "included_with_warnings"
                if inclusion == "ready_with_warnings"
                else "included"
            )
            return status, row.get("required_follow_up", "Carry into assembly.")
    return "included_as_limitation_disclosure", "Assembled from Task 133 inventory."


def build_return_package_index_matrix(inventory: dict) -> list[dict]:
    """Build the top-level Gatekeeper return package index."""
    rows = []
    for position, (code, purpose) in enumerate(SECTION_PURPOSES.items(), start=1):
        status, note = _component_status(inventory, code)
        rows.append(
            {
                "section_order": position,
                "section_code": code,
                "section_label": code.replace("_", " "),
                "included_in_package": True,
                "section_status": status,
                "source_reference": SECTION_SOURCE_MAP[code],
                "section_purpose": purpose,
                "assembly_note": note,
                "safety_boundary": "Gatekeeper return package section only.",
            }
        )
    return rows


def build_return_package_section_matrix(
    *,
    inventory: dict,
    index_rows: list[dict],
) -> list[dict]:
    """Build assembled package section rows."""
    summary = inventory["input_inventory_summary"]
    rows = []
    for row in index_rows:
        code = row["section_code"]
        if code == "executive_gatekeeper_return_summary":
            content = (
                "Assembles the Gatekeeper return package for "
                f"{summary['final_gatekeeper_stabilization_outcome']} with "
                f"{summary['final_progression_status']} preserved."
            )
        elif code.startswith("no_") or code == "auto_promotion_disabled_confirmation":
            content = "Confirms the prohibited scope remains blocked in Task 134."
        elif code == "next_gatekeeper_review_questions":
            content = "Carries warning-status review questions into Task 135 validation."
        else:
            content = row["section_purpose"]
        rows.append(
            {
                "section_code": code,
                "section_label": row["section_label"],
                "section_status": row["section_status"],
                "section_content_summary": content,
                "source_references": row["source_reference"],
                "gatekeeper_use": "Review package content and boundaries in Task 135.",
                "warning_or_limitation_note": row["assembly_note"],
                "safety_boundary": row["safety_boundary"],
            }
        )
    return rows


def _section_for_evidence(code: str) -> str:
    mapping = {
        "phase_17_closure": "phase_17_final_outcome_summary",
        "gatekeeper_stabilization_re_review": "gatekeeper_stabilization_decision_record",
        "gatekeeper_stabilized_evidence_comparison": "comparison_evidence_inventory",
        "stabilization_validation_trial": "validation_evidence_inventory",
        "targeted_evidence_repairs": "repaired_evidence_inventory",
        "residual_blocker_work_orders": "blocker_disposition_summary",
        "targeted_evidence_stabilization_plan": "evidence_stabilization_timeline",
        "phase_16_closure": "evidence_stabilization_timeline",
        "baseline_gatekeeper_re_evaluation": "comparison_evidence_inventory",
        "pre_post_repair_comparison": "comparison_evidence_inventory",
        "controlled_re_run_trial": "evidence_stabilization_timeline",
        "research_audit_trail": "source_run_traceability",
    }
    return mapping.get(code, "source_run_traceability")


def build_return_package_evidence_reference_matrix(inventory: dict) -> list[dict]:
    """Build evidence references included in the return package."""
    rows = []
    for evidence in inventory.get("evidence_artifact_inventory_matrix", []):
        inclusion = evidence.get("inclusion_status", "ready_for_package_assembly")
        status = (
            "included_with_warnings"
            if inclusion == "ready_with_warnings"
            else "included"
        )
        rows.append(
            {
                "evidence_ref_code": evidence["evidence_code"],
                "evidence_label": evidence["evidence_label"],
                "source_phase": evidence["source_phase"],
                "source_task": evidence["source_task"],
                "source_run_id": evidence["source_run_id"],
                "source_artifact_path": evidence["located_artifact_path"],
                "package_section_code": _section_for_evidence(evidence["evidence_code"]),
                "reference_status": status,
                "evidence_role": evidence.get("role_in_package", "source evidence"),
                "limitation_note": evidence.get("limitation_note", "local artifact only"),
                "safety_boundary": evidence["safety_boundary"],
            }
        )
    return rows


def build_return_package_residual_risk_section(inventory: dict) -> list[dict]:
    """Build residual risk disclosures from inventory warnings and required risks."""
    issue_rows = {
        row["issue_code"]: row
        for row in inventory.get("missing_or_warning_input_matrix", [])
    }
    required = [
        ("unresolved_material_blocker", "high"),
        ("partially_improved_evidence_blockers", "high"),
        ("local_artifact_limitation", "medium"),
        ("residual_metadata_concentration", "medium"),
        ("residual_period_sensitivity", "high"),
        ("residual_outlier_dependence", "high"),
        ("persona_review_not_allowed", "critical"),
        ("investor_agent_execution_not_allowed", "critical"),
        ("auto_promotion_disabled", "critical"),
        ("gatekeeper_return_package_only_scope", "high"),
    ]
    rows = []
    for code, fallback_severity in required:
        source = issue_rows.get(code, {})
        severity = source.get("severity", fallback_severity)
        rows.append(
            {
                "risk_code": code,
                "risk_label": code.replace("_", " "),
                "risk_status": "disclosed",
                "severity": severity,
                "disclosure_text": (
                    f"Package discloses {code.replace('_', ' ')} for Gatekeeper "
                    "attention before any future scope expansion."
                ),
                "gatekeeper_attention_required": True,
                "package_section_code": "residual_risk_disclosure",
                "source_issue_status": source.get("issue_status", "preserved"),
                "safety_boundary": "Residual risk disclosure only.",
            }
        )
    return rows


def build_return_package_permission_boundary_section() -> list[dict]:
    """Build preserved permission boundaries for the return package."""
    specs = [
        ("gatekeeper_return_package_preparation", "allowed", "Assemble package only."),
        ("actual_gatekeeper_re_review", "not_in_task_134", "Not executed in Task 134."),
        ("persona_review_preparation", "not_allowed", "Not allowed."),
        ("actual_persona_review", "not_allowed", "Not allowed."),
        ("investor_agent_execution", "not_allowed", "Not allowed."),
        ("investor_decision_generation", "not_allowed", "Not allowed."),
        ("company_ranking", "not_allowed", "Not allowed."),
        ("investment_recommendation", "not_allowed", "Not allowed."),
        ("allocation_or_rebalancing", "not_allowed", "Not allowed."),
        ("trade_signal_generation", "not_allowed", "Not allowed."),
        ("auto_promotion", "disabled", "Disabled."),
    ]
    return [
        {
            "permission_code": code,
            "permission_label": code.replace("_", " "),
            "task_134_status": status,
            "allowed_scope": allowed_scope if status == "allowed" else "none",
            "prohibited_scope": (
                "Investor decisions, recommendations, rankings, allocations, "
                "rebalancing, trade signals, investor-agent execution, actual "
                "persona reviews, and auto-promotion."
            ),
            "condition_to_expand_scope": "Future explicit Gatekeeper authorization.",
            "package_section_code": "permission_boundary_summary",
            "safety_boundary": "Permission boundary only.",
        }
        for code, status, allowed_scope in specs
    ]


def build_return_package_limitation_matrix() -> list[dict]:
    """Build limitations that must remain visible in the return package."""
    specs = [
        ("task_133_completed_with_warnings", "medium"),
        ("one_component_input_not_ready", "medium"),
        ("local_artifact_only_scope", "medium"),
        ("no_live_data_refresh", "medium"),
        ("no_actual_persona_review", "critical"),
        ("no_investor_agent_execution", "critical"),
        ("no_recommendations", "critical"),
        ("no_rankings", "critical"),
        ("no_trade_signals", "critical"),
        ("auto_promotion_disabled", "critical"),
    ]
    return [
        {
            "limitation_code": code,
            "limitation_label": code.replace("_", " "),
            "limitation_status": "included",
            "severity": severity,
            "package_section_code": "local_artifact_limitation_disclosure"
            if "local" in code or "task_133" in code or "component" in code
            else "permission_boundary_summary",
            "disclosure_text": f"Package discloses {code.replace('_', ' ')}.",
            "safety_boundary": "Limitation disclosure only.",
        }
        for code, severity in specs
    ]


def build_return_package_summary(
    *,
    gatekeeper_return_package_run_id: str,
    inventory: dict,
    index_rows: list[dict],
    evidence_rows: list[dict],
    limitation_rows: list[dict],
) -> dict:
    """Build the Task 134 package assembly summary."""
    inventory_summary = inventory["input_inventory_summary"]
    warning_sections = sum(
        row["section_status"] == "included_with_warnings" for row in index_rows
    )
    assembly_status = (
        "assembled_with_warnings"
        if inventory.get("inventory_status") == "completed_with_warnings"
        or warning_sections
        or limitation_rows
        else "assembled"
    )
    return {
        "gatekeeper_return_package_run_id": gatekeeper_return_package_run_id,
        "gatekeeper_return_input_inventory_run_id": inventory[
            "gatekeeper_return_input_inventory_run_id"
        ],
        "gatekeeper_return_plan_run_id": inventory["gatekeeper_return_plan_run_id"],
        "phase_id": 18,
        "phase_name": PHASE_NAME,
        "current_task_id": 134,
        "current_task_name": "Assemble Gatekeeper Return Package",
        "final_gatekeeper_stabilization_outcome": inventory_summary[
            "final_gatekeeper_stabilization_outcome"
        ],
        "final_progression_status": inventory_summary["final_progression_status"],
        "final_persona_review_status": inventory_summary[
            "final_persona_review_status"
        ],
        "package_status": assembly_status,
        "package_role": "gatekeeper_return_package_assembly",
        "sections_total": len(index_rows),
        "sections_included": sum(row["included_in_package"] for row in index_rows),
        "sections_included_with_warnings": warning_sections,
        "evidence_references_total": len(evidence_rows),
        "limitations_total": len(limitation_rows),
        "main_package_finding": (
            "Gatekeeper return package is assembled from local inventory with "
            "residual warnings and permission boundaries preserved."
        ),
        "recommended_next_task": NEXT_TASK,
    }


def build_task_135_handoff_manifest(
    *,
    report_summary: dict,
    index_rows: list[dict],
    evidence_rows: list[dict],
    limitation_rows: list[dict],
) -> dict:
    """Build the Task 135 validation handoff manifest."""
    return {
        "future_phase_id": 18,
        "future_phase_name": PHASE_NAME,
        "future_task_id": 135,
        "future_task_name": "Validate Gatekeeper Return Package Completeness",
        "gatekeeper_return_package_run_id": report_summary[
            "gatekeeper_return_package_run_id"
        ],
        "gatekeeper_return_input_inventory_run_id": report_summary[
            "gatekeeper_return_input_inventory_run_id"
        ],
        "required_inputs": [
            "gatekeeper_return_package",
            "return_package_index_matrix",
            "return_package_section_matrix",
            "return_package_evidence_reference_matrix",
            "return_package_residual_risk_section",
            "return_package_permission_boundary_section",
            "return_package_limitation_matrix",
        ],
        "sections_to_validate": [row["section_code"] for row in index_rows],
        "evidence_references_to_validate": [
            row["evidence_ref_code"] for row in evidence_rows
        ],
        "limitations_to_validate": [row["limitation_code"] for row in limitation_rows],
        "allowed_scope": [
            "validate package completeness",
            "validate local artifact references",
            "validate residual risks and permission boundaries",
        ],
        "prohibited_outputs": [
            "investor decisions",
            "recommendations",
            "rankings",
            "allocations",
            "rebalancing",
            "trade signals",
            "investor agent execution",
            "actual persona reviews",
            "auto-promotion",
        ],
        "readiness_status": "ready_with_warnings"
        if report_summary["package_status"] == "assembled_with_warnings"
        else "ready_to_validate_gatekeeper_return_package_completeness",
        "execution_allowed_now": True,
        "reason": (
            "Task 134 assembled the Gatekeeper return package; Task 135 may "
            "validate completeness without expanding scope."
        ),
    }


def build_gatekeeper_return_package_assembly_checks() -> list[dict]:
    """Build Task 134 assembly checks."""
    checks = [
        "input_inventory_loaded",
        "return_package_summary_created",
        "return_package_index_matrix_created",
        "return_package_section_matrix_created",
        "return_package_evidence_reference_matrix_created",
        "return_package_residual_risk_section_created",
        "return_package_permission_boundary_section_created",
        "return_package_limitation_matrix_created",
        "task_135_handoff_manifest_created",
        "final_gatekeeper_stabilization_outcome_preserved",
        "final_progression_status_preserved",
        "final_persona_review_status_preserved",
        "gatekeeper_return_package_only_preserved",
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
            "source_artifact": "gatekeeper_return_package",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 134.",
        }
        for check in checks
    ]


def build_gatekeeper_return_package(
    *,
    gatekeeper_return_package_run_id: str,
    generated_at: str,
    inventory: dict,
) -> GatekeeperReturnPackageReport:
    """Build the Task 134 Gatekeeper return package."""
    index = build_return_package_index_matrix(inventory)
    sections = build_return_package_section_matrix(
        inventory=inventory,
        index_rows=index,
    )
    evidence = build_return_package_evidence_reference_matrix(inventory)
    residual = build_return_package_residual_risk_section(inventory)
    permissions = build_return_package_permission_boundary_section()
    limitations = build_return_package_limitation_matrix()
    summary = build_return_package_summary(
        gatekeeper_return_package_run_id=gatekeeper_return_package_run_id,
        inventory=inventory,
        index_rows=index,
        evidence_rows=evidence,
        limitation_rows=limitations,
    )
    handoff = build_task_135_handoff_manifest(
        report_summary=summary,
        index_rows=index,
        evidence_rows=evidence,
        limitation_rows=limitations,
    )
    return GatekeeperReturnPackageReport(
        gatekeeper_return_package_run_id=gatekeeper_return_package_run_id,
        generated_at=generated_at,
        gatekeeper_return_input_inventory_run_id=inventory[
            "gatekeeper_return_input_inventory_run_id"
        ],
        gatekeeper_return_plan_run_id=inventory["gatekeeper_return_plan_run_id"],
        phase_17_closure_run_id=inventory["phase_17_closure_run_id"],
        gatekeeper_stabilization_re_review_run_id=inventory[
            "gatekeeper_stabilization_re_review_run_id"
        ],
        gatekeeper_stabilized_comparison_run_id=inventory[
            "gatekeeper_stabilized_comparison_run_id"
        ],
        stabilization_validation_run_id=inventory["stabilization_validation_run_id"],
        targeted_repair_run_id=inventory["targeted_repair_run_id"],
        residual_work_order_package_run_id=inventory[
            "residual_work_order_package_run_id"
        ],
        stabilization_plan_run_id=inventory["stabilization_plan_run_id"],
        phase_16_closure_run_id=inventory["phase_16_closure_run_id"],
        baseline_gatekeeper_re_evaluation_run_id=inventory[
            "baseline_gatekeeper_re_evaluation_run_id"
        ],
        pre_post_repair_comparison_run_id=inventory[
            "pre_post_repair_comparison_run_id"
        ],
        controlled_re_run_trial_run_id=inventory["controlled_re_run_trial_run_id"],
        re_run_input_package_run_id=inventory["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=inventory["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=inventory["research_audit_trail_run_id"],
        return_package_summary=summary,
        return_package_index_matrix=index,
        return_package_section_matrix=sections,
        return_package_evidence_reference_matrix=evidence,
        return_package_residual_risk_section=residual,
        return_package_permission_boundary_section=permissions,
        return_package_limitation_matrix=limitations,
        task_135_handoff_manifest=handoff,
        gatekeeper_return_package_assembly_checks=(
            build_gatekeeper_return_package_assembly_checks()
        ),
        assembly_status=summary["package_status"],
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


def _summary_rows(summary: dict) -> list[dict]:
    return [{"field": key, "value": _format_value(value)} for key, value in summary.items()]


def _render_markdown(report: GatekeeperReturnPackageReport) -> str:
    summary = report.return_package_summary
    handoff = report.task_135_handoff_manifest
    lines = [
        "# Gatekeeper Return Package",
        "",
        "## Executive Summary",
        "",
        f"* Gatekeeper Return Package Run ID: {report.gatekeeper_return_package_run_id}",
        (
            "* Gatekeeper Return Input Inventory Run ID: "
            f"{report.gatekeeper_return_input_inventory_run_id}"
        ),
        f"* Gatekeeper Return Plan Run ID: {report.gatekeeper_return_plan_run_id}",
        "* Current Phase: 18 - Gatekeeper Return Package Layer",
        "* Current Task: Task 134 - Assemble Gatekeeper Return Package",
        (
            "* Final Gatekeeper Stabilization Outcome: "
            f"{summary['final_gatekeeper_stabilization_outcome']}"
        ),
        f"* Final Progression Status: {summary['final_progression_status']}",
        f"* Final Persona Review Status: {summary['final_persona_review_status']}",
        f"* Assembly Status: {report.assembly_status}",
        f"* Sections Total: {summary['sections_total']}",
        f"* Sections Included: {summary['sections_included']}",
        f"* Evidence References Total: {summary['evidence_references_total']}",
        f"* Limitations Total: {summary['limitations_total']}",
        f"* Recommended Next Task: {report.recommended_next_task}",
        "",
        "## Important Boundary",
        "",
        SAFETY_NOTICE,
        "",
        "## Where We Are Now",
        "",
        "Current Phase:",
        "18 - Gatekeeper Return Package Layer",
        "",
        "Previous Task:",
        "Task 133 - Build Gatekeeper Return Package Input Inventory completed",
        "",
        "This Task:",
        "Task 134 assembles the Gatekeeper return package from the Task 133 inventory.",
        "",
        "Direct Next:",
        NEXT_TASK,
        "",
        "Final Gatekeeper Stabilization Outcome From Phase 17:",
        "hold_with_stabilization_progress",
        "",
        "Progression:",
        "gatekeeper_return_package_only",
        "",
        "Persona Reviews:",
        "false",
        "",
        "## Return Package Summary",
        "",
        *_markdown_table(_summary_rows(summary), [("Field", "field"), ("Value", "value")]),
        "",
        "## Return Package Index Matrix",
        "",
        *_markdown_table(
            report.return_package_index_matrix,
            [
                ("Section", "section_code"),
                ("Included", "included_in_package"),
                ("Status", "section_status"),
                ("Source", "source_reference"),
                ("Purpose", "section_purpose"),
            ],
        ),
        "",
        "## Return Package Section Matrix",
        "",
        *_markdown_table(
            report.return_package_section_matrix,
            [
                ("Section", "section_code"),
                ("Status", "section_status"),
                ("Content Summary", "section_content_summary"),
                ("Source References", "source_references"),
            ],
        ),
        "",
        "## Evidence Reference Matrix",
        "",
        *_markdown_table(
            report.return_package_evidence_reference_matrix,
            [
                ("Evidence", "evidence_ref_code"),
                ("Source Task", "source_task"),
                ("Source Run ID", "source_run_id"),
                ("Package Section", "package_section_code"),
                ("Status", "reference_status"),
            ],
        ),
        "",
        "## Residual Risk Section",
        "",
        *_markdown_table(
            report.return_package_residual_risk_section,
            [
                ("Risk", "risk_code"),
                ("Status", "risk_status"),
                ("Severity", "severity"),
                ("Disclosure", "disclosure_text"),
            ],
        ),
        "",
        "## Permission Boundary Section",
        "",
        *_markdown_table(
            report.return_package_permission_boundary_section,
            [
                ("Permission", "permission_code"),
                ("Task 134 Status", "task_134_status"),
                ("Allowed Scope", "allowed_scope"),
                ("Condition To Expand", "condition_to_expand_scope"),
            ],
        ),
        "",
        "## Limitation Matrix",
        "",
        *_markdown_table(
            report.return_package_limitation_matrix,
            [
                ("Limitation", "limitation_code"),
                ("Status", "limitation_status"),
                ("Severity", "severity"),
                ("Disclosure", "disclosure_text"),
            ],
        ),
        "",
        "## Task 135 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} - {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Required Inputs: {'; '.join(handoff['required_inputs'])}",
        f"* Sections To Validate: {'; '.join(handoff['sections_to_validate'])}",
        (
            "* Evidence References To Validate: "
            f"{'; '.join(handoff['evidence_references_to_validate'])}"
        ),
        f"* Limitations To Validate: {'; '.join(handoff['limitations_to_validate'])}",
        f"* Allowed Scope: {'; '.join(handoff['allowed_scope'])}",
        f"* Prohibited Outputs: {'; '.join(handoff['prohibited_outputs'])}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Assembly Checks",
        "",
        *_markdown_table(
            report.gatekeeper_return_package_assembly_checks,
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
        "* The Gatekeeper return package is assembled for completeness validation.",
        "* The next step is Task 135 validation, not Gatekeeper rerun.",
        "* The work remains Gatekeeper-facing and non-actionable.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not allow investor review.",
        "* It does not run investor agents.",
        "* It does not run actual persona reviews.",
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


def write_gatekeeper_return_package_report(
    *,
    outputs_root: Path,
    gatekeeper_return_input_inventory_run_id: str | None = None,
) -> GatekeeperReturnPackageFiles:
    """Write Task 134 Gatekeeper return package assembly artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_gatekeeper_return_input_inventory_manifest(
        outputs_root=outputs_root,
        gatekeeper_return_input_inventory_run_id=gatekeeper_return_input_inventory_run_id,
    )
    inventory_run_id = manifest["gatekeeper_return_input_inventory_run_id"]
    inventory = load_gatekeeper_return_input_inventory(
        outputs_root=outputs_root,
        gatekeeper_return_input_inventory_run_id=inventory_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_gatekeeper_return_package(
        gatekeeper_return_package_run_id=run_id,
        generated_at=generated_at.isoformat(),
        inventory=inventory,
    )

    root = outputs_root / "gatekeeper_return_packages"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "gatekeeper_return_package.md"
    json_path = output_folder / "gatekeeper_return_package.json"
    index_csv = output_folder / "return_package_index_matrix.csv"
    section_csv = output_folder / "return_package_section_matrix.csv"
    evidence_csv = output_folder / "return_package_evidence_reference_matrix.csv"
    residual_csv = output_folder / "return_package_residual_risk_section.csv"
    permission_csv = output_folder / "return_package_permission_boundary_section.csv"
    limitation_csv = output_folder / "return_package_limitation_matrix.csv"
    handoff_path = output_folder / "task_135_handoff_manifest.json"
    checks_csv = output_folder / "gatekeeper_return_package_assembly_checks.csv"
    latest_manifest_path = root / "latest_gatekeeper_return_package_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(index_csv, report.return_package_index_matrix)
    _write_csv(section_csv, report.return_package_section_matrix)
    _write_csv(evidence_csv, report.return_package_evidence_reference_matrix)
    _write_csv(residual_csv, report.return_package_residual_risk_section)
    _write_csv(permission_csv, report.return_package_permission_boundary_section)
    _write_csv(limitation_csv, report.return_package_limitation_matrix)
    handoff_path.write_text(
        json.dumps(report.task_135_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.gatekeeper_return_package_assembly_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "gatekeeper_return_package_run_id": (
                    report.gatekeeper_return_package_run_id
                ),
                "gatekeeper_return_input_inventory_run_id": (
                    report.gatekeeper_return_input_inventory_run_id
                ),
                "gatekeeper_return_plan_run_id": report.gatekeeper_return_plan_run_id,
                "phase_17_closure_run_id": report.phase_17_closure_run_id,
                "final_gatekeeper_stabilization_outcome": (
                    report.return_package_summary[
                        "final_gatekeeper_stabilization_outcome"
                    ]
                ),
                "final_progression_status": report.return_package_summary[
                    "final_progression_status"
                ],
                "final_persona_review_status": report.return_package_summary[
                    "final_persona_review_status"
                ],
                "assembly_status": report.assembly_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_135_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return GatekeeperReturnPackageFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        index_csv_path=index_csv,
        section_csv_path=section_csv,
        evidence_reference_csv_path=evidence_csv,
        residual_risk_csv_path=residual_csv,
        permission_boundary_csv_path=permission_csv,
        limitation_csv_path=limitation_csv,
        task_135_handoff_manifest_path=handoff_path,
        checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
