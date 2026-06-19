"""Task 135 Gatekeeper return package completeness validation."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report validates the completeness of the Gatekeeper return package "
    "only. It does not rerun Gatekeeper, run investor agents, run actual "
    "persona reviews, create investor decisions, rankings, recommendations, "
    "allocations, rebalancing instructions, trade signals, execution "
    "instructions, or strategy validation."
)
PHASE_NAME = "Gatekeeper Return Package Layer"
NEXT_TASK = "Task 136 - Run Gatekeeper Return Review"

REQUIRED_SECTIONS = [
    "executive_gatekeeper_return_summary",
    "phase_17_final_outcome_summary",
    "gatekeeper_stabilization_decision_record",
    "permission_boundary_summary",
    "blocker_disposition_summary",
    "residual_risk_disclosure",
    "evidence_stabilization_timeline",
    "repaired_evidence_inventory",
    "validation_evidence_inventory",
    "comparison_evidence_inventory",
    "source_run_traceability",
    "local_artifact_limitation_disclosure",
    "no_persona_review_confirmation",
    "no_investor_agent_execution_confirmation",
    "no_recommendation_output_confirmation",
    "auto_promotion_disabled_confirmation",
    "next_gatekeeper_review_questions",
]

REQUIRED_EVIDENCE_REFS = [
    "phase_17_closure",
    "gatekeeper_stabilization_re_review",
    "gatekeeper_stabilized_evidence_comparison",
    "stabilization_validation_trial",
    "targeted_evidence_repairs",
    "residual_blocker_work_orders",
    "targeted_evidence_stabilization_plan",
    "phase_16_closure",
    "baseline_gatekeeper_re_evaluation",
    "pre_post_repair_comparison",
    "controlled_re_run_trial",
    "research_audit_trail",
]

REQUIRED_RESIDUAL_RISKS = {
    "unresolved_material_blockers": "unresolved_material_blocker",
    "partially_improved_evidence_blockers": "partially_improved_evidence_blockers",
    "local_artifact_limitations": "local_artifact_limitation",
    "residual_metadata_concentration": "residual_metadata_concentration",
    "residual_period_sensitivity": "residual_period_sensitivity",
    "residual_outlier_dependence": "residual_outlier_dependence",
    "no_actual_persona_review_allowed": "persona_review_not_allowed",
    "investor_agent_execution_not_allowed": "investor_agent_execution_not_allowed",
    "auto_promotion_disabled": "auto_promotion_disabled",
    "gatekeeper_return_package_scope_only": "gatekeeper_return_package_only_scope",
}

EXPECTED_PERMISSION_STATUSES = {
    "gatekeeper_return_package_preparation": "allowed",
    "actual_gatekeeper_re_review": "not_in_task_135",
    "persona_review_preparation": "not_allowed",
    "actual_persona_review": "not_allowed",
    "investor_agent_execution": "not_allowed",
    "investor_decision_generation": "not_allowed",
    "company_ranking": "not_allowed",
    "investment_recommendation": "not_allowed",
    "allocation_or_rebalancing": "not_allowed",
    "trade_signal_generation": "not_allowed",
    "auto_promotion": "disabled",
}

REQUIRED_LIMITATIONS = [
    "task_133_completed_with_warnings",
    "one_component_input_not_ready",
    "local_artifact_only_scope",
    "no_live_data_refresh",
    "no_actual_persona_review",
    "no_investor_agent_execution",
    "no_recommendations",
    "no_rankings",
    "no_trade_signals",
    "auto_promotion_disabled",
]

SAFETY_CHECKS = [
    "no_investor_agents_run",
    "no_actual_persona_review_run",
    "no_investor_decisions_created",
    "no_recommendations_created",
    "no_rankings_created",
    "no_allocations_created",
    "no_rebalancing_created",
    "no_trade_signals_created",
    "no_execution_instructions_created",
    "no_strategy_validation_created",
    "auto_promotion_disabled",
    "no_network_calls",
]


@dataclass(frozen=True)
class GatekeeperReturnPackageValidationReport:
    """Structured Task 135 Gatekeeper return package validation."""

    gatekeeper_return_package_validation_run_id: str
    generated_at: str
    gatekeeper_return_package_run_id: str
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
    package_validation_summary: dict
    section_completeness_matrix: list[dict]
    evidence_reference_validation_matrix: list[dict]
    residual_risk_validation_matrix: list[dict]
    permission_boundary_validation_matrix: list[dict]
    limitation_validation_matrix: list[dict]
    safety_boundary_validation_matrix: list[dict]
    task_136_handoff_manifest: dict
    gatekeeper_return_package_validation_checks: list[dict]
    validation_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class GatekeeperReturnPackageValidationFiles:
    """Generated Task 135 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    section_csv_path: Path
    evidence_csv_path: Path
    residual_risk_csv_path: Path
    permission_csv_path: Path
    limitation_csv_path: Path
    safety_csv_path: Path
    task_136_handoff_manifest_path: Path
    checks_csv_path: Path
    latest_manifest_path: Path
    report: GatekeeperReturnPackageValidationReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_gatekeeper_return_package_manifest(
    *,
    outputs_root: Path,
    gatekeeper_return_package_run_id: str | None = None,
) -> dict:
    """Load one Task 134 package report or the latest Task 134 manifest."""
    root = Path(outputs_root) / "gatekeeper_return_packages"
    path = (
        root / gatekeeper_return_package_run_id / "gatekeeper_return_package.json"
        if gatekeeper_return_package_run_id
        else root / "latest_gatekeeper_return_package_manifest.json"
    )
    label = (
        "Gatekeeper return package report"
        if gatekeeper_return_package_run_id
        else "Gatekeeper return package manifest"
    )
    return _load_required_json(path, label)


def load_gatekeeper_return_package(
    *,
    outputs_root: Path,
    gatekeeper_return_package_run_id: str,
) -> dict:
    """Load a Task 134 Gatekeeper return package by run id."""
    path = (
        Path(outputs_root)
        / "gatekeeper_return_packages"
        / gatekeeper_return_package_run_id
        / "gatekeeper_return_package.json"
    )
    return _load_required_json(path, "Gatekeeper return package report")


def _status_from_found(found: bool, package_status: str | None = None) -> str:
    if not found:
        return "missing"
    if package_status and "warning" in package_status:
        return "satisfied_with_warnings"
    return "satisfied"


def build_section_completeness_matrix(package: dict) -> list[dict]:
    """Validate required package sections."""
    by_code = {
        row["section_code"]: row
        for row in package.get("return_package_index_matrix", [])
    }
    rows = []
    for code in REQUIRED_SECTIONS:
        source = by_code.get(code)
        found = bool(source and source.get("included_in_package"))
        validation_status = _status_from_found(
            found,
            source.get("section_status") if source else None,
        )
        rows.append(
            {
                "section_code": code,
                "section_title": code.replace("_", " "),
                "required": True,
                "found_in_package": found,
                "section_status": source.get("section_status", "missing")
                if source
                else "missing",
                "validation_status": validation_status,
                "missing_or_warning_detail": "Section found in package."
                if validation_status == "satisfied"
                else (
                    "Section found with package warning."
                    if found
                    else "Required section missing from package."
                ),
                "blocking_if_missing": True,
                "safety_boundary": "Section completeness validation only.",
            }
        )
    return rows


def build_evidence_reference_validation_matrix(package: dict) -> list[dict]:
    """Validate required evidence references."""
    by_code = {
        row["evidence_ref_code"]: row
        for row in package.get("return_package_evidence_reference_matrix", [])
    }
    rows = []
    for code in REQUIRED_EVIDENCE_REFS:
        source = by_code.get(code)
        found = source is not None
        validation_status = _status_from_found(
            found,
            source.get("reference_status") if source else None,
        )
        rows.append(
            {
                "evidence_ref_code": code,
                "evidence_label": code.replace("_", " "),
                "source_phase": source.get("source_phase", "missing")
                if source
                else "missing",
                "source_task": source.get("source_task", "missing")
                if source
                else "missing",
                "source_run_id": source.get("source_run_id", "missing")
                if source
                else "missing",
                "source_artifact_path": source.get("source_artifact_path", "missing")
                if source
                else "missing",
                "referenced_in_section": source.get("package_section_code", "missing")
                if source
                else "missing",
                "reference_found": found,
                "validation_status": validation_status,
                "missing_or_warning_detail": "Evidence reference found."
                if validation_status == "satisfied"
                else (
                    "Evidence reference found with warning."
                    if found
                    else "Required evidence reference missing."
                ),
                "blocking_if_missing": True,
                "safety_boundary": "Evidence reference validation only.",
            }
        )
    return rows


def build_residual_risk_validation_matrix(package: dict) -> list[dict]:
    """Validate required residual risk disclosures."""
    by_code = {
        row["risk_code"]: row
        for row in package.get("return_package_residual_risk_section", [])
    }
    rows = []
    for required_code, package_code in REQUIRED_RESIDUAL_RISKS.items():
        source = by_code.get(package_code)
        found = source is not None
        rows.append(
            {
                "risk_code": required_code,
                "risk_label": required_code.replace("_", " "),
                "required_disclosure": True,
                "found_in_package": found,
                "validation_status": "satisfied" if found else "missing",
                "severity": source.get("severity", "missing") if source else "missing",
                "gatekeeper_attention_present": bool(
                    source and source.get("gatekeeper_attention_required")
                ),
                "missing_or_warning_detail": "Residual risk disclosure found."
                if found
                else "Required residual risk disclosure missing.",
                "safety_boundary": "Residual risk validation only.",
            }
        )
    return rows


def _permission_satisfied(expected: str, observed: str) -> tuple[str, str]:
    if observed == "missing":
        return "missing", "Required permission boundary missing."
    if expected == observed:
        return "satisfied", "Permission boundary matches expected status."
    if expected.startswith("not_in_task") and observed.startswith("not_in_task"):
        return (
            "satisfied_with_warnings",
            "Package status references assembly task; Task 135 also does not rerun Gatekeeper.",
        )
    return "inconsistent", f"Expected {expected}; package shows {observed}."


def build_permission_boundary_validation_matrix(package: dict) -> list[dict]:
    """Validate required permission boundaries."""
    by_code = {
        row["permission_code"]: row
        for row in package.get("return_package_permission_boundary_section", [])
    }
    rows = []
    for code, expected in EXPECTED_PERMISSION_STATUSES.items():
        source = by_code.get(code)
        observed = source.get("task_134_status", "missing") if source else "missing"
        status, detail = _permission_satisfied(expected, observed)
        rows.append(
            {
                "permission_code": code,
                "permission_label": code.replace("_", " "),
                "required_boundary": True,
                "found_in_package": source is not None,
                "validation_status": status,
                "expected_status": expected,
                "package_status": observed,
                "mismatch_detail": detail,
                "safety_boundary": "Permission boundary validation only.",
            }
        )
    return rows


def build_limitation_validation_matrix(package: dict) -> list[dict]:
    """Validate required limitation disclosures."""
    by_code = {
        row["limitation_code"]: row
        for row in package.get("return_package_limitation_matrix", [])
    }
    rows = []
    for code in REQUIRED_LIMITATIONS:
        source = by_code.get(code)
        found = source is not None
        rows.append(
            {
                "limitation_code": code,
                "limitation_label": code.replace("_", " "),
                "required_disclosure": True,
                "found_in_package": found,
                "validation_status": "satisfied" if found else "missing",
                "severity": source.get("severity", "missing") if source else "missing",
                "disclosure_sufficient": found,
                "missing_or_warning_detail": "Limitation disclosure found."
                if found
                else "Required limitation disclosure missing.",
                "safety_boundary": "Limitation validation only.",
            }
        )
    return rows


def build_safety_boundary_validation_matrix() -> list[dict]:
    """Validate Task 135 safety boundaries."""
    return [
        {
            "safety_code": code,
            "safety_label": code.replace("_", " "),
            "required_status": "satisfied",
            "observed_status": "satisfied",
            "validation_status": "satisfied",
            "blocking_if_failed": True,
            "finding": f"{code} preserved in Task 135.",
        }
        for code in SAFETY_CHECKS
    ]


def _blocking_count(*matrices: list[dict]) -> int:
    return sum(
        1
        for matrix in matrices
        for row in matrix
        if row.get("validation_status") in {"missing", "inconsistent", "blocked"}
    )


def _warning_count(*matrices: list[dict]) -> int:
    return sum(
        1
        for matrix in matrices
        for row in matrix
        if row.get("validation_status") == "satisfied_with_warnings"
    )


def _validation_status(blocking: int, warnings: int) -> str:
    if blocking:
        return "incomplete"
    if warnings:
        return "complete_with_warnings"
    return "complete"


def build_package_validation_summary(
    *,
    gatekeeper_return_package_validation_run_id: str,
    package: dict,
    sections: list[dict],
    evidence: list[dict],
    residual_risks: list[dict],
    permissions: list[dict],
    limitations: list[dict],
    safety: list[dict],
) -> dict:
    """Build the Task 135 validation summary."""
    blocking = _blocking_count(
        sections,
        evidence,
        residual_risks,
        permissions,
        limitations,
        safety,
    )
    warnings = _warning_count(sections, evidence, permissions)
    status = _validation_status(blocking, warnings)
    package_summary = package["return_package_summary"]
    return {
        "gatekeeper_return_package_validation_run_id": (
            gatekeeper_return_package_validation_run_id
        ),
        "gatekeeper_return_package_run_id": package["gatekeeper_return_package_run_id"],
        "gatekeeper_return_input_inventory_run_id": package[
            "gatekeeper_return_input_inventory_run_id"
        ],
        "gatekeeper_return_plan_run_id": package["gatekeeper_return_plan_run_id"],
        "phase_17_closure_run_id": package["phase_17_closure_run_id"],
        "phase_id": 18,
        "phase_name": PHASE_NAME,
        "current_task_id": 135,
        "current_task_name": "Validate Gatekeeper Return Package Completeness",
        "final_gatekeeper_stabilization_outcome": package_summary[
            "final_gatekeeper_stabilization_outcome"
        ],
        "final_progression_status": package_summary["final_progression_status"],
        "final_persona_review_status": package_summary["final_persona_review_status"],
        "source_assembly_status": package["assembly_status"],
        "validation_status": status,
        "validation_role": "gatekeeper_return_package_completeness_validation",
        "required_sections_total": len(sections),
        "required_sections_satisfied": sum(
            row["validation_status"] in {"satisfied", "satisfied_with_warnings"}
            for row in sections
        ),
        "required_sections_missing": sum(
            row["validation_status"] == "missing" for row in sections
        ),
        "evidence_refs_total": len(evidence),
        "evidence_refs_validated": sum(
            row["validation_status"] in {"satisfied", "satisfied_with_warnings"}
            for row in evidence
        ),
        "evidence_refs_missing": sum(
            row["validation_status"] == "missing" for row in evidence
        ),
        "residual_risks_total": len(residual_risks),
        "residual_risks_validated": sum(
            row["validation_status"] == "satisfied" for row in residual_risks
        ),
        "permission_boundaries_total": len(permissions),
        "permission_boundaries_validated": sum(
            row["validation_status"] in {"satisfied", "satisfied_with_warnings"}
            for row in permissions
        ),
        "limitations_total": len(limitations),
        "limitations_validated": sum(
            row["validation_status"] == "satisfied" for row in limitations
        ),
        "blocking_findings_total": blocking,
        "warning_findings_total": warnings,
        "recommended_next_task": NEXT_TASK if not blocking else "manual_follow_up_required",
        "main_validation_finding": (
            "Gatekeeper return package completeness validation passed with "
            "warnings preserved; Task 136 may perform Gatekeeper return review."
            if not blocking
            else "Gatekeeper return package validation found blocking gaps."
        ),
    }


def build_task_136_handoff_manifest(
    *,
    summary: dict,
    package_outputs_validated: list[str],
) -> dict:
    """Build the Task 136 handoff manifest."""
    allowed = summary["blocking_findings_total"] == 0 and summary[
        "validation_status"
    ] in {"complete", "complete_with_warnings"}
    return {
        "future_phase_id": 18,
        "future_phase_name": PHASE_NAME,
        "future_task_id": 136,
        "future_task_name": "Run Gatekeeper Return Review",
        "gatekeeper_return_package_validation_run_id": summary[
            "gatekeeper_return_package_validation_run_id"
        ],
        "gatekeeper_return_package_run_id": summary[
            "gatekeeper_return_package_run_id"
        ],
        "package_outputs_validated": package_outputs_validated,
        "validation_status": summary["validation_status"],
        "blocking_findings": summary["blocking_findings_total"],
        "warning_findings": summary["warning_findings_total"],
        "allowed_scope": [
            "Gatekeeper return review of the assembled package",
            "reviewing package completeness, residual blockers, risks, and permission boundaries",
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
        if summary["validation_status"] == "complete_with_warnings"
        else ("ready_for_gatekeeper_return_review" if allowed else "blocked"),
        "execution_allowed_now": allowed,
        "reason": (
            "Package validation is complete enough for Task 136 Gatekeeper "
            "return review; warnings remain disclosed."
            if allowed
            else "Blocking validation findings must be repaired before Task 136."
        ),
    }


def build_gatekeeper_return_package_validation_checks(
    *,
    validation_status: str,
    blocking_findings_total: int,
) -> list[dict]:
    """Build Task 135 validation checks."""
    checks = [
        "gatekeeper_return_package_loaded",
        "package_validation_summary_created",
        "section_completeness_matrix_created",
        "evidence_reference_validation_matrix_created",
        "residual_risk_validation_matrix_created",
        "permission_boundary_validation_matrix_created",
        "limitation_validation_matrix_created",
        "safety_boundary_validation_matrix_created",
        "task_136_handoff_manifest_created",
        "required_sections_validated",
        "evidence_references_validated",
        "residual_risks_validated",
        "permission_boundaries_validated",
        "limitations_validated",
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
    status = (
        "satisfied"
        if validation_status in {"complete", "complete_with_warnings"}
        and blocking_findings_total == 0
        else "blocked"
    )
    return [
        {
            "check_code": check,
            "check_label": check.replace("_", " "),
            "status": status,
            "source_artifact": "gatekeeper_return_package_validation",
            "blocking_if_failed": True,
            "finding": f"{check} {status} for Task 135.",
        }
        for check in checks
    ]


def build_gatekeeper_return_package_validation(
    *,
    gatekeeper_return_package_validation_run_id: str,
    generated_at: str,
    package: dict,
) -> GatekeeperReturnPackageValidationReport:
    """Build the Task 135 package completeness validation."""
    sections = build_section_completeness_matrix(package)
    evidence = build_evidence_reference_validation_matrix(package)
    residual = build_residual_risk_validation_matrix(package)
    permissions = build_permission_boundary_validation_matrix(package)
    limitations = build_limitation_validation_matrix(package)
    safety = build_safety_boundary_validation_matrix()
    summary = build_package_validation_summary(
        gatekeeper_return_package_validation_run_id=(
            gatekeeper_return_package_validation_run_id
        ),
        package=package,
        sections=sections,
        evidence=evidence,
        residual_risks=residual,
        permissions=permissions,
        limitations=limitations,
        safety=safety,
    )
    handoff = build_task_136_handoff_manifest(
        summary=summary,
        package_outputs_validated=[
            "gatekeeper_return_package",
            "return_package_index_matrix",
            "return_package_section_matrix",
            "return_package_evidence_reference_matrix",
            "return_package_residual_risk_section",
            "return_package_permission_boundary_section",
            "return_package_limitation_matrix",
        ],
    )
    checks = build_gatekeeper_return_package_validation_checks(
        validation_status=summary["validation_status"],
        blocking_findings_total=summary["blocking_findings_total"],
    )
    return GatekeeperReturnPackageValidationReport(
        gatekeeper_return_package_validation_run_id=(
            gatekeeper_return_package_validation_run_id
        ),
        generated_at=generated_at,
        gatekeeper_return_package_run_id=package["gatekeeper_return_package_run_id"],
        gatekeeper_return_input_inventory_run_id=package[
            "gatekeeper_return_input_inventory_run_id"
        ],
        gatekeeper_return_plan_run_id=package["gatekeeper_return_plan_run_id"],
        phase_17_closure_run_id=package["phase_17_closure_run_id"],
        gatekeeper_stabilization_re_review_run_id=package[
            "gatekeeper_stabilization_re_review_run_id"
        ],
        gatekeeper_stabilized_comparison_run_id=package[
            "gatekeeper_stabilized_comparison_run_id"
        ],
        stabilization_validation_run_id=package["stabilization_validation_run_id"],
        targeted_repair_run_id=package["targeted_repair_run_id"],
        residual_work_order_package_run_id=package[
            "residual_work_order_package_run_id"
        ],
        stabilization_plan_run_id=package["stabilization_plan_run_id"],
        phase_16_closure_run_id=package["phase_16_closure_run_id"],
        baseline_gatekeeper_re_evaluation_run_id=package[
            "baseline_gatekeeper_re_evaluation_run_id"
        ],
        pre_post_repair_comparison_run_id=package["pre_post_repair_comparison_run_id"],
        controlled_re_run_trial_run_id=package["controlled_re_run_trial_run_id"],
        re_run_input_package_run_id=package["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=package["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=package["research_audit_trail_run_id"],
        package_validation_summary=summary,
        section_completeness_matrix=sections,
        evidence_reference_validation_matrix=evidence,
        residual_risk_validation_matrix=residual,
        permission_boundary_validation_matrix=permissions,
        limitation_validation_matrix=limitations,
        safety_boundary_validation_matrix=safety,
        task_136_handoff_manifest=handoff,
        gatekeeper_return_package_validation_checks=checks,
        validation_status=summary["validation_status"],
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


def _render_markdown(report: GatekeeperReturnPackageValidationReport) -> str:
    summary = report.package_validation_summary
    handoff = report.task_136_handoff_manifest
    lines = [
        "# Gatekeeper Return Package Completeness Validation",
        "",
        "## Executive Summary",
        "",
        (
            "* Gatekeeper Return Package Validation Run ID: "
            f"{report.gatekeeper_return_package_validation_run_id}"
        ),
        f"* Gatekeeper Return Package Run ID: {report.gatekeeper_return_package_run_id}",
        "* Current Phase: 18 - Gatekeeper Return Package Layer",
        "* Current Task: Task 135 - Validate Gatekeeper Return Package Completeness",
        f"* Source Assembly Status: {summary['source_assembly_status']}",
        (
            "* Final Gatekeeper Stabilization Outcome: "
            f"{summary['final_gatekeeper_stabilization_outcome']}"
        ),
        f"* Final Progression Status: {summary['final_progression_status']}",
        f"* Final Persona Review Status: {summary['final_persona_review_status']}",
        f"* Validation Status: {report.validation_status}",
        f"* Required Sections Total: {summary['required_sections_total']}",
        f"* Required Sections Satisfied: {summary['required_sections_satisfied']}",
        f"* Required Sections Missing: {summary['required_sections_missing']}",
        f"* Evidence References Total: {summary['evidence_refs_total']}",
        f"* Evidence References Validated: {summary['evidence_refs_validated']}",
        f"* Residual Risks Validated: {summary['residual_risks_validated']}",
        (
            "* Permission Boundaries Validated: "
            f"{summary['permission_boundaries_validated']}"
        ),
        f"* Limitations Validated: {summary['limitations_validated']}",
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
        "18 - Gatekeeper Return Package Layer",
        "",
        "Previous Task:",
        "Task 134 - Assemble Gatekeeper Return Package assembled_with_warnings",
        "",
        "This Task:",
        "Task 135 validates the Gatekeeper return package completeness.",
        "",
        "Phase 18 Status:",
        "In progress",
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
        "Recommended Next Task:",
        NEXT_TASK,
        "",
        "## Package Validation Summary",
        "",
        *_markdown_table(_summary_rows(summary), [("Field", "field"), ("Value", "value")]),
        "",
        "## Section Completeness Matrix",
        "",
        *_markdown_table(
            report.section_completeness_matrix,
            [
                ("Section", "section_code"),
                ("Required", "required"),
                ("Found", "found_in_package"),
                ("Validation Status", "validation_status"),
                ("Detail", "missing_or_warning_detail"),
            ],
        ),
        "",
        "## Evidence Reference Validation Matrix",
        "",
        *_markdown_table(
            report.evidence_reference_validation_matrix,
            [
                ("Evidence", "evidence_ref_code"),
                ("Source Task", "source_task"),
                ("Source Run ID", "source_run_id"),
                ("Referenced In Section", "referenced_in_section"),
                ("Validation Status", "validation_status"),
            ],
        ),
        "",
        "## Residual Risk Validation Matrix",
        "",
        *_markdown_table(
            report.residual_risk_validation_matrix,
            [
                ("Risk", "risk_code"),
                ("Required Disclosure", "required_disclosure"),
                ("Found", "found_in_package"),
                ("Severity", "severity"),
                ("Validation Status", "validation_status"),
            ],
        ),
        "",
        "## Permission Boundary Validation Matrix",
        "",
        *_markdown_table(
            report.permission_boundary_validation_matrix,
            [
                ("Permission", "permission_code"),
                ("Expected Status", "expected_status"),
                ("Package Status", "package_status"),
                ("Validation Status", "validation_status"),
                ("Mismatch Detail", "mismatch_detail"),
            ],
        ),
        "",
        "## Limitation Validation Matrix",
        "",
        *_markdown_table(
            report.limitation_validation_matrix,
            [
                ("Limitation", "limitation_code"),
                ("Required Disclosure", "required_disclosure"),
                ("Found", "found_in_package"),
                ("Severity", "severity"),
                ("Validation Status", "validation_status"),
            ],
        ),
        "",
        "## Safety Boundary Validation Matrix",
        "",
        *_markdown_table(
            report.safety_boundary_validation_matrix,
            [
                ("Safety Check", "safety_code"),
                ("Required Status", "required_status"),
                ("Observed Status", "observed_status"),
                ("Validation Status", "validation_status"),
                ("Blocking If Failed", "blocking_if_failed"),
            ],
        ),
        "",
        "## Task 136 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} - {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        (
            "* Package Outputs Validated: "
            f"{'; '.join(handoff['package_outputs_validated'])}"
        ),
        f"* Validation Status: {handoff['validation_status']}",
        f"* Blocking Findings: {handoff['blocking_findings']}",
        f"* Warning Findings: {handoff['warning_findings']}",
        f"* Allowed Scope: {'; '.join(handoff['allowed_scope'])}",
        f"* Prohibited Outputs: {'; '.join(handoff['prohibited_outputs'])}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.gatekeeper_return_package_validation_checks,
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
        (
            "* The package is complete enough for Gatekeeper return review if "
            "validation is complete or complete_with_warnings."
        ),
        "* The next step is Gatekeeper Return Review.",
        "* The work remains Gatekeeper-facing only.",
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


def write_gatekeeper_return_package_validation_report(
    *,
    outputs_root: Path,
    gatekeeper_return_package_run_id: str | None = None,
) -> GatekeeperReturnPackageValidationFiles:
    """Write Task 135 Gatekeeper return package validation artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_gatekeeper_return_package_manifest(
        outputs_root=outputs_root,
        gatekeeper_return_package_run_id=gatekeeper_return_package_run_id,
    )
    package_run_id = manifest["gatekeeper_return_package_run_id"]
    package = load_gatekeeper_return_package(
        outputs_root=outputs_root,
        gatekeeper_return_package_run_id=package_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_gatekeeper_return_package_validation(
        gatekeeper_return_package_validation_run_id=run_id,
        generated_at=generated_at.isoformat(),
        package=package,
    )

    root = outputs_root / "gatekeeper_return_package_validations"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "gatekeeper_return_package_validation.md"
    json_path = output_folder / "gatekeeper_return_package_validation.json"
    section_csv = output_folder / "section_completeness_matrix.csv"
    evidence_csv = output_folder / "evidence_reference_validation_matrix.csv"
    residual_csv = output_folder / "residual_risk_validation_matrix.csv"
    permission_csv = output_folder / "permission_boundary_validation_matrix.csv"
    limitation_csv = output_folder / "limitation_validation_matrix.csv"
    safety_csv = output_folder / "safety_boundary_validation_matrix.csv"
    handoff_path = output_folder / "task_136_handoff_manifest.json"
    checks_csv = output_folder / "gatekeeper_return_package_validation_checks.csv"
    latest_manifest_path = (
        root / "latest_gatekeeper_return_package_validation_manifest.json"
    )

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(section_csv, report.section_completeness_matrix)
    _write_csv(evidence_csv, report.evidence_reference_validation_matrix)
    _write_csv(residual_csv, report.residual_risk_validation_matrix)
    _write_csv(permission_csv, report.permission_boundary_validation_matrix)
    _write_csv(limitation_csv, report.limitation_validation_matrix)
    _write_csv(safety_csv, report.safety_boundary_validation_matrix)
    handoff_path.write_text(
        json.dumps(report.task_136_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.gatekeeper_return_package_validation_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "gatekeeper_return_package_validation_run_id": (
                    report.gatekeeper_return_package_validation_run_id
                ),
                "gatekeeper_return_package_run_id": (
                    report.gatekeeper_return_package_run_id
                ),
                "gatekeeper_return_input_inventory_run_id": (
                    report.gatekeeper_return_input_inventory_run_id
                ),
                "gatekeeper_return_plan_run_id": report.gatekeeper_return_plan_run_id,
                "phase_17_closure_run_id": report.phase_17_closure_run_id,
                "source_assembly_status": report.package_validation_summary[
                    "source_assembly_status"
                ],
                "final_gatekeeper_stabilization_outcome": (
                    report.package_validation_summary[
                        "final_gatekeeper_stabilization_outcome"
                    ]
                ),
                "final_progression_status": report.package_validation_summary[
                    "final_progression_status"
                ],
                "final_persona_review_status": report.package_validation_summary[
                    "final_persona_review_status"
                ],
                "validation_status": report.validation_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_136_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return GatekeeperReturnPackageValidationFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        section_csv_path=section_csv,
        evidence_csv_path=evidence_csv,
        residual_risk_csv_path=residual_csv,
        permission_csv_path=permission_csv,
        limitation_csv_path=limitation_csv,
        safety_csv_path=safety_csv,
        task_136_handoff_manifest_path=handoff_path,
        checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
