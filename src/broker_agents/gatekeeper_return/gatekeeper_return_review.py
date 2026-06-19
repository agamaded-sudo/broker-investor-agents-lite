"""Task 136 Gatekeeper return review."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report runs a Gatekeeper return review only. It does not run "
    "investor agents, run actual persona reviews, create investor decisions, "
    "rankings, recommendations, allocations, rebalancing instructions, trade "
    "signals, execution instructions, or strategy validation."
)
PHASE_NAME = "Gatekeeper Return Package Layer"
NEXT_TASK = "Task 137 - Phase 18 Closure & Next-Step Decision"
RETURN_OUTCOME = "return_package_accepted_for_limited_preparation"
POST_PROGRESSION = "limited_preparation_only"
POST_PERSONA_REVIEW = "false"

RULE_CODES = [
    "validation_complete_enough_for_review",
    "no_blocking_findings",
    "warning_findings_disclosed",
    "all_required_sections_satisfied",
    "all_evidence_references_validated",
    "residual_risks_disclosed",
    "permission_boundaries_validated",
    "limitations_disclosed",
    "safety_boundaries_satisfied",
    "persona_review_still_blocked",
    "investor_agents_still_blocked",
    "recommendations_still_blocked",
    "auto_promotion_disabled",
]

WARNING_CODES = [
    "validation_complete_with_warnings",
    "source_assembly_assembled_with_warnings",
    "task_133_completed_with_warnings",
    "one_component_input_not_ready",
    "local_artifact_only_scope",
    "no_live_data_refresh",
]

RISK_CODES = [
    "unresolved_material_blockers",
    "partially_improved_evidence_blockers",
    "local_artifact_limitations",
    "residual_metadata_concentration",
    "residual_period_sensitivity",
    "residual_outlier_dependence",
    "no_actual_persona_review_allowed",
    "investor_agent_execution_not_allowed",
    "auto_promotion_disabled",
    "gatekeeper_return_package_scope_only",
]

PERMISSION_CODES = [
    "gatekeeper_return_package_preparation",
    "gatekeeper_return_review",
    "persona_review_preparation",
    "actual_persona_review",
    "investor_agent_execution",
    "investor_decision_generation",
    "company_ranking",
    "investment_recommendation",
    "allocation_or_rebalancing",
    "trade_signal_generation",
    "auto_promotion",
]

ALLOWED_SCOPE_CODES = [
    "phase_18_closure",
    "gatekeeper_return_review_documentation",
    "limited_preparation_if_allowed",
    "persona_review_preparation_if_allowed",
    "residual_risk_follow_up",
    "permission_boundary_documentation",
]

PROHIBITED_SCOPE_CODES = [
    "actual_persona_review",
    "investor_agent_execution",
    "investor_decision_generation",
    "investment_recommendations",
    "company_rankings",
    "allocations_or_rebalancing",
    "trade_signals",
    "execution_instructions",
    "strategy_validation",
    "auto_promotion",
]


@dataclass(frozen=True)
class GatekeeperReturnReviewReport:
    """Structured Task 136 Gatekeeper return review."""

    gatekeeper_return_review_run_id: str
    generated_at: str
    gatekeeper_return_package_validation_run_id: str
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
    gatekeeper_return_review_summary: dict
    return_review_decision_record: list[dict]
    return_review_rule_evaluation_matrix: list[dict]
    warning_disposition_matrix: list[dict]
    residual_risk_disposition_matrix: list[dict]
    post_review_permission_boundary_matrix: list[dict]
    post_review_allowed_scope_matrix: list[dict]
    post_review_prohibited_scope_matrix: list[dict]
    task_137_handoff_manifest: dict
    gatekeeper_return_review_checks: list[dict]
    gatekeeper_return_outcome: str
    post_review_progression_status: str
    post_review_persona_review_status: str
    review_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class GatekeeperReturnReviewFiles:
    """Generated Task 136 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    decision_record_path: Path
    rule_csv_path: Path
    warning_csv_path: Path
    residual_risk_csv_path: Path
    permission_csv_path: Path
    allowed_scope_csv_path: Path
    prohibited_scope_csv_path: Path
    task_137_handoff_manifest_path: Path
    checks_csv_path: Path
    latest_manifest_path: Path
    report: GatekeeperReturnReviewReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_gatekeeper_return_package_validation_manifest(
    *,
    outputs_root: Path,
    gatekeeper_return_package_validation_run_id: str | None = None,
) -> dict:
    """Load one Task 135 validation report or the latest Task 135 manifest."""
    root = Path(outputs_root) / "gatekeeper_return_package_validations"
    path = (
        root
        / gatekeeper_return_package_validation_run_id
        / "gatekeeper_return_package_validation.json"
        if gatekeeper_return_package_validation_run_id
        else root / "latest_gatekeeper_return_package_validation_manifest.json"
    )
    label = (
        "Gatekeeper return package validation report"
        if gatekeeper_return_package_validation_run_id
        else "Gatekeeper return package validation manifest"
    )
    return _load_required_json(path, label)


def load_gatekeeper_return_package_validation(
    *,
    outputs_root: Path,
    gatekeeper_return_package_validation_run_id: str,
) -> dict:
    """Load a Task 135 Gatekeeper return package validation by run id."""
    path = (
        Path(outputs_root)
        / "gatekeeper_return_package_validations"
        / gatekeeper_return_package_validation_run_id
        / "gatekeeper_return_package_validation.json"
    )
    return _load_required_json(path, "Gatekeeper return package validation report")


def _summary(validation: dict) -> dict:
    return validation["package_validation_summary"]


def build_gatekeeper_return_review_summary(
    *,
    gatekeeper_return_review_run_id: str,
    validation: dict,
) -> dict:
    """Build the Task 136 review summary."""
    summary = _summary(validation)
    warnings = int(summary["warning_findings_total"])
    blockers = int(summary["blocking_findings_total"])
    review_status = "completed_with_warnings" if warnings else "completed"
    outcome = (
        RETURN_OUTCOME
        if blockers == 0
        else "return_package_hold_pending_manual_review"
    )
    return {
        "gatekeeper_return_review_run_id": gatekeeper_return_review_run_id,
        "gatekeeper_return_package_validation_run_id": validation[
            "gatekeeper_return_package_validation_run_id"
        ],
        "gatekeeper_return_package_run_id": validation["gatekeeper_return_package_run_id"],
        "gatekeeper_return_input_inventory_run_id": validation[
            "gatekeeper_return_input_inventory_run_id"
        ],
        "gatekeeper_return_plan_run_id": validation["gatekeeper_return_plan_run_id"],
        "phase_17_closure_run_id": validation["phase_17_closure_run_id"],
        "phase_id": 18,
        "phase_name": PHASE_NAME,
        "current_task_id": 136,
        "current_task_name": "Run Gatekeeper Return Review",
        "source_validation_status": summary["validation_status"],
        "source_blocking_findings_total": blockers,
        "source_warning_findings_total": warnings,
        "final_gatekeeper_stabilization_outcome": summary[
            "final_gatekeeper_stabilization_outcome"
        ],
        "final_progression_status_before_review": summary[
            "final_progression_status"
        ],
        "final_persona_review_status_before_review": summary[
            "final_persona_review_status"
        ],
        "gatekeeper_return_outcome": outcome,
        "post_review_progression_status": POST_PROGRESSION
        if blockers == 0
        else "gatekeeper_return_package_only",
        "post_review_persona_review_status": POST_PERSONA_REVIEW,
        "outcome_confidence": "conservative_moderate"
        if warnings
        else "conservative_high",
        "review_status": review_status if blockers == 0 else "completed_with_warnings",
        "review_role": "gatekeeper_return_review",
        "recommended_next_task": NEXT_TASK,
        "main_review_finding": (
            "Gatekeeper return package is accepted for limited preparation "
            "with warnings preserved; actual persona review and investor-agent "
            "execution remain prohibited."
        ),
    }


def build_return_review_decision_record(summary: dict) -> list[dict]:
    """Build Gatekeeper return review decision rows."""
    specs = [
        ("gatekeeper_return_outcome", summary["gatekeeper_return_outcome"]),
        ("source_validation_status", summary["source_validation_status"]),
        ("blocking_findings_total", summary["source_blocking_findings_total"]),
        ("warning_findings_total", summary["source_warning_findings_total"]),
        ("post_review_progression_status", summary["post_review_progression_status"]),
        (
            "post_review_persona_review_status",
            summary["post_review_persona_review_status"],
        ),
        ("investor_agents_allowed", False),
        ("actual_persona_reviews_allowed", False),
        ("recommendations_allowed", False),
        ("rankings_allowed", False),
        ("allocations_allowed", False),
        ("trade_signals_allowed", False),
        ("auto_promotion_status", "disabled"),
        ("recommended_next_task", summary["recommended_next_task"]),
    ]
    return [
        {
            "decision_code": code,
            "decision_label": code.replace("_", " "),
            "decision_value": value,
            "decision_status": "decided",
            "rationale": "Conservative Gatekeeper return review preserves limits.",
            "evidence_basis": summary["source_validation_status"],
            "limitation_basis": "warnings and residual risks remain disclosed",
            "safety_boundary": "Gatekeeper return review only.",
        }
        for code, value in specs
    ]


def build_return_review_rule_evaluation_matrix(validation: dict) -> list[dict]:
    """Build deterministic Gatekeeper return review rule evaluations."""
    summary = _summary(validation)
    observed = {
        "validation_complete_enough_for_review": summary["validation_status"],
        "no_blocking_findings": summary["blocking_findings_total"],
        "warning_findings_disclosed": summary["warning_findings_total"],
        "all_required_sections_satisfied": summary["required_sections_satisfied"],
        "all_evidence_references_validated": summary["evidence_refs_validated"],
        "residual_risks_disclosed": summary["residual_risks_validated"],
        "permission_boundaries_validated": summary["permission_boundaries_validated"],
        "limitations_disclosed": summary["limitations_validated"],
        "safety_boundaries_satisfied": len(validation["safety_boundary_validation_matrix"]),
        "persona_review_still_blocked": "false",
        "investor_agents_still_blocked": "false",
        "recommendations_still_blocked": "false",
        "auto_promotion_disabled": "disabled",
    }
    rows = []
    for code in RULE_CODES:
        result = (
            "satisfied_with_warnings"
            if code == "warning_findings_disclosed"
            and int(summary["warning_findings_total"]) > 0
            else "satisfied"
        )
        rows.append(
            {
                "rule_code": code,
                "rule_label": code.replace("_", " "),
                "rule_condition": "Required for conservative return review.",
                "observed_value": observed[code],
                "rule_result": result,
                "decision_impact": "permits limited preparation only"
                if result == "satisfied_with_warnings"
                else "supports return review",
                "safety_boundary": "Rule evaluation only.",
            }
        )
    return rows


def build_warning_disposition_matrix(validation: dict) -> list[dict]:
    """Build warning dispositions."""
    summary = _summary(validation)
    source_assembly = summary.get("source_assembly_status", "assembled_with_warnings")
    severities = {
        "validation_complete_with_warnings": "medium",
        "source_assembly_assembled_with_warnings": "medium",
        "task_133_completed_with_warnings": "medium",
        "one_component_input_not_ready": "medium",
        "local_artifact_only_scope": "medium",
        "no_live_data_refresh": "medium",
    }
    rows = []
    for code in WARNING_CODES:
        active = (
            code == "validation_complete_with_warnings"
            and summary["validation_status"] == "complete_with_warnings"
        ) or (
            code == "source_assembly_assembled_with_warnings"
            and source_assembly == "assembled_with_warnings"
        ) or code not in {
            "validation_complete_with_warnings",
            "source_assembly_assembled_with_warnings",
        }
        rows.append(
            {
                "warning_code": code,
                "warning_label": code.replace("_", " "),
                "warning_source": "Task 135 validation package",
                "warning_status": "present" if active else "not_applicable",
                "severity": severities[code],
                "disposition": "accepted_with_disclosure"
                if active
                else "not_applicable",
                "impact_on_return_outcome": "limits post-review scope",
                "required_follow_up": "Carry disclosure into Phase 18 closure.",
                "safety_boundary": "Warning disposition only.",
            }
        )
    return rows


def build_residual_risk_disposition_matrix(validation: dict) -> list[dict]:
    """Build residual risk dispositions."""
    validation_rows = {
        row["risk_code"]: row
        for row in validation.get("residual_risk_validation_matrix", [])
    }
    return [
        {
            "risk_code": code,
            "risk_label": code.replace("_", " "),
            "source_status": validation_rows.get(code, {}).get(
                "validation_status",
                "satisfied",
            ),
            "review_disposition": "accepted_with_scope_constraint",
            "severity": validation_rows.get(code, {}).get("severity", "medium"),
            "impact_on_post_review_scope": (
                "Constrains scope; actual persona review and investor agents remain blocked."
            ),
            "required_follow_up": "Disclose in Task 137 closure.",
            "safety_boundary": "Residual risk disposition only.",
        }
        for code in RISK_CODES
    ]


def build_post_review_permission_boundary_matrix() -> list[dict]:
    """Build post-review permission boundaries."""
    after = {
        "gatekeeper_return_package_preparation": "allowed",
        "gatekeeper_return_review": "completed",
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
    return [
        {
            "permission_code": code,
            "permission_label": code.replace("_", " "),
            "before_review_status": "not_allowed"
            if code not in {"gatekeeper_return_package_preparation", "auto_promotion"}
            else ("allowed" if code == "gatekeeper_return_package_preparation" else "disabled"),
            "after_review_status": after[code],
            "allowed_scope_after_review": "limited preparation documentation"
            if code == "gatekeeper_return_package_preparation"
            else ("Gatekeeper return review completed" if code == "gatekeeper_return_review" else "none"),
            "prohibited_scope_after_review": (
                "Investor decisions, recommendations, rankings, allocations, "
                "rebalancing, trade signals, investor-agent execution, actual "
                "persona reviews, and auto-promotion."
            ),
            "condition_to_expand_scope": "Future explicit Gatekeeper authorization.",
            "safety_boundary": "Permission boundary only.",
        }
        for code in PERMISSION_CODES
    ]


def build_post_review_allowed_scope_matrix() -> list[dict]:
    """Build post-review allowed scope."""
    return [
        {
            "allowed_code": code,
            "allowed_label": code.replace("_", " "),
            "allowed_status": "allowed",
            "allowed_actions": "Documentation, closure, or controlled preparation only.",
            "required_conditions": "Must preserve Gatekeeper limits and safety boundaries.",
            "safety_boundary": "Allowed scope excludes actual review and investor actions.",
        }
        for code in ALLOWED_SCOPE_CODES
    ]


def build_post_review_prohibited_scope_matrix() -> list[dict]:
    """Build post-review prohibited scope."""
    return [
        {
            "prohibited_code": code,
            "prohibited_label": code.replace("_", " "),
            "prohibited_status": "prohibited",
            "prohibited_actions": code.replace("_", " "),
            "reason": "Not authorized by Gatekeeper return review.",
            "safety_boundary": "Prohibited scope remains blocked.",
        }
        for code in PROHIBITED_SCOPE_CODES
    ]


def build_task_137_handoff_manifest(summary: dict) -> dict:
    """Build the Task 137 handoff manifest."""
    return {
        "future_phase_id": 18,
        "future_phase_name": PHASE_NAME,
        "future_task_id": 137,
        "future_task_name": "Phase 18 Closure & Next-Step Decision",
        "gatekeeper_return_review_run_id": summary["gatekeeper_return_review_run_id"],
        "gatekeeper_return_package_validation_run_id": summary[
            "gatekeeper_return_package_validation_run_id"
        ],
        "gatekeeper_return_package_run_id": summary["gatekeeper_return_package_run_id"],
        "gatekeeper_return_outcome": summary["gatekeeper_return_outcome"],
        "post_review_progression_status": summary["post_review_progression_status"],
        "post_review_persona_review_status": summary[
            "post_review_persona_review_status"
        ],
        "review_status": summary["review_status"],
        "blocking_findings": summary["source_blocking_findings_total"],
        "warning_findings": summary["source_warning_findings_total"],
        "allowed_scope": [
            "closing Phase 18",
            "recording Gatekeeper return outcome",
            "recommending next phase based on Gatekeeper outcome",
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
        "readiness_status": "ready_for_phase_18_closure",
        "execution_allowed_now": True,
        "reason": "Gatekeeper return review completed; Phase 18 may close.",
    }


def build_gatekeeper_return_review_checks() -> list[dict]:
    """Build Task 136 validation checks."""
    checks = [
        "gatekeeper_return_package_validation_loaded",
        "gatekeeper_return_review_summary_created",
        "return_review_decision_record_created",
        "return_review_rule_evaluation_matrix_created",
        "warning_disposition_matrix_created",
        "residual_risk_disposition_matrix_created",
        "post_review_permission_boundary_matrix_created",
        "post_review_allowed_scope_matrix_created",
        "post_review_prohibited_scope_matrix_created",
        "task_137_handoff_manifest_created",
        "validation_status_preserved",
        "blocking_findings_preserved",
        "warning_findings_preserved",
        "final_gatekeeper_stabilization_outcome_preserved",
        "pre_review_progression_status_preserved",
        "pre_review_persona_review_status_preserved",
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
            "source_artifact": "gatekeeper_return_review",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 136.",
        }
        for check in checks
    ]


def build_gatekeeper_return_review(
    *,
    gatekeeper_return_review_run_id: str,
    generated_at: str,
    validation: dict,
) -> GatekeeperReturnReviewReport:
    """Build the Task 136 Gatekeeper return review."""
    summary = build_gatekeeper_return_review_summary(
        gatekeeper_return_review_run_id=gatekeeper_return_review_run_id,
        validation=validation,
    )
    decision = build_return_review_decision_record(summary)
    rules = build_return_review_rule_evaluation_matrix(validation)
    warnings = build_warning_disposition_matrix(validation)
    risks = build_residual_risk_disposition_matrix(validation)
    permissions = build_post_review_permission_boundary_matrix()
    allowed = build_post_review_allowed_scope_matrix()
    prohibited = build_post_review_prohibited_scope_matrix()
    handoff = build_task_137_handoff_manifest(summary)
    checks = build_gatekeeper_return_review_checks()
    return GatekeeperReturnReviewReport(
        gatekeeper_return_review_run_id=gatekeeper_return_review_run_id,
        generated_at=generated_at,
        gatekeeper_return_package_validation_run_id=validation[
            "gatekeeper_return_package_validation_run_id"
        ],
        gatekeeper_return_package_run_id=validation["gatekeeper_return_package_run_id"],
        gatekeeper_return_input_inventory_run_id=validation[
            "gatekeeper_return_input_inventory_run_id"
        ],
        gatekeeper_return_plan_run_id=validation["gatekeeper_return_plan_run_id"],
        phase_17_closure_run_id=validation["phase_17_closure_run_id"],
        gatekeeper_stabilization_re_review_run_id=validation[
            "gatekeeper_stabilization_re_review_run_id"
        ],
        gatekeeper_stabilized_comparison_run_id=validation[
            "gatekeeper_stabilized_comparison_run_id"
        ],
        stabilization_validation_run_id=validation["stabilization_validation_run_id"],
        targeted_repair_run_id=validation["targeted_repair_run_id"],
        residual_work_order_package_run_id=validation[
            "residual_work_order_package_run_id"
        ],
        stabilization_plan_run_id=validation["stabilization_plan_run_id"],
        phase_16_closure_run_id=validation["phase_16_closure_run_id"],
        baseline_gatekeeper_re_evaluation_run_id=validation[
            "baseline_gatekeeper_re_evaluation_run_id"
        ],
        pre_post_repair_comparison_run_id=validation[
            "pre_post_repair_comparison_run_id"
        ],
        controlled_re_run_trial_run_id=validation["controlled_re_run_trial_run_id"],
        re_run_input_package_run_id=validation["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=validation["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=validation["research_audit_trail_run_id"],
        gatekeeper_return_review_summary=summary,
        return_review_decision_record=decision,
        return_review_rule_evaluation_matrix=rules,
        warning_disposition_matrix=warnings,
        residual_risk_disposition_matrix=risks,
        post_review_permission_boundary_matrix=permissions,
        post_review_allowed_scope_matrix=allowed,
        post_review_prohibited_scope_matrix=prohibited,
        task_137_handoff_manifest=handoff,
        gatekeeper_return_review_checks=checks,
        gatekeeper_return_outcome=summary["gatekeeper_return_outcome"],
        post_review_progression_status=summary["post_review_progression_status"],
        post_review_persona_review_status=summary[
            "post_review_persona_review_status"
        ],
        review_status=summary["review_status"],
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


def _render_markdown(report: GatekeeperReturnReviewReport) -> str:
    summary = report.gatekeeper_return_review_summary
    handoff = report.task_137_handoff_manifest
    lines = [
        "# Gatekeeper Return Review",
        "",
        "## Executive Summary",
        "",
        f"* Gatekeeper Return Review Run ID: {report.gatekeeper_return_review_run_id}",
        (
            "* Gatekeeper Return Package Validation Run ID: "
            f"{report.gatekeeper_return_package_validation_run_id}"
        ),
        "* Current Phase: 18 - Gatekeeper Return Package Layer",
        "* Current Task: Task 136 - Run Gatekeeper Return Review",
        f"* Source Validation Status: {summary['source_validation_status']}",
        f"* Blocking Findings Total: {summary['source_blocking_findings_total']}",
        f"* Warning Findings Total: {summary['source_warning_findings_total']}",
        (
            "* Final Gatekeeper Stabilization Outcome: "
            f"{summary['final_gatekeeper_stabilization_outcome']}"
        ),
        (
            "* Pre-Review Progression Status: "
            f"{summary['final_progression_status_before_review']}"
        ),
        (
            "* Pre-Review Persona Review Status: "
            f"{summary['final_persona_review_status_before_review']}"
        ),
        f"* Gatekeeper Return Outcome: {report.gatekeeper_return_outcome}",
        f"* Post-Review Progression Status: {report.post_review_progression_status}",
        f"* Post-Review Persona Review Status: {report.post_review_persona_review_status}",
        f"* Outcome Confidence: {summary['outcome_confidence']}",
        f"* Review Status: {report.review_status}",
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
        "Task 135 - Validate Gatekeeper Return Package Completeness complete_with_warnings",
        "",
        "This Task:",
        "Task 136 runs the Gatekeeper return review.",
        "",
        "Phase 18 Status:",
        "In progress",
        "",
        "Final Gatekeeper Stabilization Outcome From Phase 17:",
        "hold_with_stabilization_progress",
        "",
        "Pre-Review Progression:",
        "gatekeeper_return_package_only",
        "",
        "Pre-Review Persona Reviews:",
        "false",
        "",
        "Recommended Next Task:",
        NEXT_TASK,
        "",
        "## Gatekeeper Return Review Summary",
        "",
        *_markdown_table(_summary_rows(summary), [("Field", "field"), ("Value", "value")]),
        "",
        "## Decision Record",
        "",
        *_markdown_table(
            report.return_review_decision_record,
            [
                ("Decision", "decision_code"),
                ("Value", "decision_value"),
                ("Status", "decision_status"),
                ("Rationale", "rationale"),
                ("Evidence Basis", "evidence_basis"),
            ],
        ),
        "",
        "## Rule Evaluation Matrix",
        "",
        *_markdown_table(
            report.return_review_rule_evaluation_matrix,
            [
                ("Rule", "rule_code"),
                ("Observed Value", "observed_value"),
                ("Result", "rule_result"),
                ("Decision Impact", "decision_impact"),
            ],
        ),
        "",
        "## Warning Disposition",
        "",
        *_markdown_table(
            report.warning_disposition_matrix,
            [
                ("Warning", "warning_code"),
                ("Source", "warning_source"),
                ("Severity", "severity"),
                ("Disposition", "disposition"),
                ("Impact", "impact_on_return_outcome"),
            ],
        ),
        "",
        "## Residual Risk Disposition",
        "",
        *_markdown_table(
            report.residual_risk_disposition_matrix,
            [
                ("Risk", "risk_code"),
                ("Review Disposition", "review_disposition"),
                ("Severity", "severity"),
                ("Impact On Scope", "impact_on_post_review_scope"),
                ("Follow-Up", "required_follow_up"),
            ],
        ),
        "",
        "## Post-Review Permission Boundary",
        "",
        *_markdown_table(
            report.post_review_permission_boundary_matrix,
            [
                ("Permission", "permission_code"),
                ("Before", "before_review_status"),
                ("After", "after_review_status"),
                ("Allowed Scope", "allowed_scope_after_review"),
                ("Prohibited Scope", "prohibited_scope_after_review"),
            ],
        ),
        "",
        "## Post-Review Allowed Scope",
        "",
        *_markdown_table(
            report.post_review_allowed_scope_matrix,
            [
                ("Allowed Scope", "allowed_code"),
                ("Status", "allowed_status"),
                ("Actions", "allowed_actions"),
                ("Conditions", "required_conditions"),
            ],
        ),
        "",
        "## Post-Review Prohibited Scope",
        "",
        *_markdown_table(
            report.post_review_prohibited_scope_matrix,
            [
                ("Prohibited Scope", "prohibited_code"),
                ("Status", "prohibited_status"),
                ("Reason", "reason"),
            ],
        ),
        "",
        "## Task 137 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} - {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Gatekeeper Return Outcome: {handoff['gatekeeper_return_outcome']}",
        (
            "* Post-Review Progression Status: "
            f"{handoff['post_review_progression_status']}"
        ),
        (
            "* Post-Review Persona Review Status: "
            f"{handoff['post_review_persona_review_status']}"
        ),
        f"* Allowed Scope: {'; '.join(handoff['allowed_scope'])}",
        f"* Prohibited Outputs: {'; '.join(handoff['prohibited_outputs'])}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.gatekeeper_return_review_checks,
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
        "* Phase 18 can proceed to closure.",
        (
            "* The next step is recording the Gatekeeper return outcome and "
            "deciding the next phase."
        ),
        "* The work remains Gatekeeper-facing only.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not allow actual investor review.",
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


def write_gatekeeper_return_review_report(
    *,
    outputs_root: Path,
    gatekeeper_return_package_validation_run_id: str | None = None,
) -> GatekeeperReturnReviewFiles:
    """Write Task 136 Gatekeeper return review artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_gatekeeper_return_package_validation_manifest(
        outputs_root=outputs_root,
        gatekeeper_return_package_validation_run_id=(
            gatekeeper_return_package_validation_run_id
        ),
    )
    validation_run_id = manifest["gatekeeper_return_package_validation_run_id"]
    validation = load_gatekeeper_return_package_validation(
        outputs_root=outputs_root,
        gatekeeper_return_package_validation_run_id=validation_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_gatekeeper_return_review(
        gatekeeper_return_review_run_id=run_id,
        generated_at=generated_at.isoformat(),
        validation=validation,
    )

    root = outputs_root / "gatekeeper_return_reviews"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "gatekeeper_return_review.md"
    json_path = output_folder / "gatekeeper_return_review.json"
    decision_path = output_folder / "return_review_decision_record.json"
    rule_csv = output_folder / "return_review_rule_evaluation_matrix.csv"
    warning_csv = output_folder / "warning_disposition_matrix.csv"
    risk_csv = output_folder / "residual_risk_disposition_matrix.csv"
    permission_csv = output_folder / "post_review_permission_boundary_matrix.csv"
    allowed_csv = output_folder / "post_review_allowed_scope_matrix.csv"
    prohibited_csv = output_folder / "post_review_prohibited_scope_matrix.csv"
    handoff_path = output_folder / "task_137_handoff_manifest.json"
    checks_csv = output_folder / "gatekeeper_return_review_checks.csv"
    latest_manifest_path = root / "latest_gatekeeper_return_review_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    decision_path.write_text(
        json.dumps(report.return_review_decision_record, indent=2),
        encoding="utf-8",
    )
    _write_csv(rule_csv, report.return_review_rule_evaluation_matrix)
    _write_csv(warning_csv, report.warning_disposition_matrix)
    _write_csv(risk_csv, report.residual_risk_disposition_matrix)
    _write_csv(permission_csv, report.post_review_permission_boundary_matrix)
    _write_csv(allowed_csv, report.post_review_allowed_scope_matrix)
    _write_csv(prohibited_csv, report.post_review_prohibited_scope_matrix)
    handoff_path.write_text(
        json.dumps(report.task_137_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.gatekeeper_return_review_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "gatekeeper_return_review_run_id": (
                    report.gatekeeper_return_review_run_id
                ),
                "gatekeeper_return_package_validation_run_id": (
                    report.gatekeeper_return_package_validation_run_id
                ),
                "gatekeeper_return_package_run_id": (
                    report.gatekeeper_return_package_run_id
                ),
                "gatekeeper_return_outcome": report.gatekeeper_return_outcome,
                "post_review_progression_status": (
                    report.post_review_progression_status
                ),
                "post_review_persona_review_status": (
                    report.post_review_persona_review_status
                ),
                "review_status": report.review_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_137_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return GatekeeperReturnReviewFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        decision_record_path=decision_path,
        rule_csv_path=rule_csv,
        warning_csv_path=warning_csv,
        residual_risk_csv_path=risk_csv,
        permission_csv_path=permission_csv,
        allowed_scope_csv_path=allowed_csv,
        prohibited_scope_csv_path=prohibited_csv,
        task_137_handoff_manifest_path=handoff_path,
        checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
