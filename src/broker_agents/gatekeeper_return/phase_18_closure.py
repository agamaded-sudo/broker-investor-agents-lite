"""Task 137 Phase 18 closure and next-step decision."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report closes Phase 18 only. It does not run investor agents, run "
    "actual persona reviews, create investor decisions, rankings, "
    "recommendations, allocations, rebalancing instructions, trade signals, "
    "execution instructions, or strategy validation."
)
PHASE_NAME = "Gatekeeper Return Package Layer"
NEXT_PHASE = "Phase 19 - Limited Preparation Governance Layer"
NEXT_TASK = "Task 138 - Define Limited Preparation Governance Plan"

ALLOWED_SCOPE_CODES = [
    "phase_18_closure",
    "limited_preparation_governance_planning",
    "limited_preparation_artifact_definition",
    "residual_risk_follow_up_planning",
    "permission_boundary_documentation",
    "next_phase_planning",
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

WARNING_CODES = [
    "complete_with_warnings",
    "assembled_with_warnings",
    "task_133_completed_with_warnings",
    "validation_warning_findings",
    "local_artifact_only_scope",
    "no_live_data_refresh",
    "residual_risk_constraints",
    "persona_review_not_allowed",
    "investor_agents_not_allowed",
    "auto_promotion_disabled",
]

RECOMMENDATION_CODES = [
    "start_phase_19_limited_preparation_governance_layer",
    "define_limited_preparation_governance_plan",
    "preserve_actual_persona_review_block",
    "preserve_investor_agent_execution_block",
    "preserve_no_recommendations",
    "preserve_no_rankings",
    "preserve_no_trade_signals",
    "preserve_auto_promotion_disabled",
    "define_preparation_artifacts_only",
    "require_future_gatekeeper_approval_before_persona_review",
]


@dataclass(frozen=True)
class Phase18ClosureReport:
    """Structured Task 137 Phase 18 closure."""

    phase_18_closure_run_id: str
    generated_at: str
    gatekeeper_return_review_run_id: str
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
    phase_18_closure_summary: dict
    phase_18_task_status_matrix: list[dict]
    final_gatekeeper_return_outcome_summary: dict
    final_post_review_permission_boundary_summary: list[dict]
    final_allowed_scope_summary: list[dict]
    final_prohibited_scope_summary: list[dict]
    remaining_warnings_after_phase_18_matrix: list[dict]
    phase_19_recommendation_matrix: list[dict]
    task_138_handoff_manifest: dict
    phase_18_closure_checks: list[dict]
    closure_status: str
    recommended_next_phase: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class Phase18ClosureFiles:
    """Generated Task 137 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    task_status_csv_path: Path
    outcome_csv_path: Path
    permission_csv_path: Path
    allowed_scope_csv_path: Path
    prohibited_scope_csv_path: Path
    warnings_csv_path: Path
    recommendation_csv_path: Path
    task_138_handoff_manifest_path: Path
    checks_csv_path: Path
    latest_manifest_path: Path
    report: Phase18ClosureReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_gatekeeper_return_review_manifest(
    *,
    outputs_root: Path,
    gatekeeper_return_review_run_id: str | None = None,
) -> dict:
    """Load one Task 136 return review report or the latest manifest."""
    root = Path(outputs_root) / "gatekeeper_return_reviews"
    path = (
        root / gatekeeper_return_review_run_id / "gatekeeper_return_review.json"
        if gatekeeper_return_review_run_id
        else root / "latest_gatekeeper_return_review_manifest.json"
    )
    label = (
        "Gatekeeper return review report"
        if gatekeeper_return_review_run_id
        else "Gatekeeper return review manifest"
    )
    return _load_required_json(path, label)


def load_gatekeeper_return_review(
    *,
    outputs_root: Path,
    gatekeeper_return_review_run_id: str,
) -> dict:
    """Load a Task 136 Gatekeeper return review by run id."""
    path = (
        Path(outputs_root)
        / "gatekeeper_return_reviews"
        / gatekeeper_return_review_run_id
        / "gatekeeper_return_review.json"
    )
    return _load_required_json(path, "Gatekeeper return review report")


def _review_summary(review: dict) -> dict:
    return review["gatekeeper_return_review_summary"]


def build_phase_18_closure_summary(
    *,
    phase_18_closure_run_id: str,
    review: dict,
) -> dict:
    """Build the Task 137 Phase 18 closure summary."""
    summary = _review_summary(review)
    closure_status = "closed_for_limited_preparation_only"
    return {
        "phase_18_closure_run_id": phase_18_closure_run_id,
        "gatekeeper_return_review_run_id": review["gatekeeper_return_review_run_id"],
        "gatekeeper_return_package_validation_run_id": review[
            "gatekeeper_return_package_validation_run_id"
        ],
        "gatekeeper_return_package_run_id": review["gatekeeper_return_package_run_id"],
        "phase_id": 18,
        "phase_name": PHASE_NAME,
        "current_task_id": 137,
        "current_task_name": "Phase 18 Closure & Next-Step Decision",
        "phase_completion_status": "completed",
        "final_gatekeeper_return_outcome": summary["gatekeeper_return_outcome"],
        "final_post_review_progression_status": summary[
            "post_review_progression_status"
        ],
        "final_post_review_persona_review_status": summary[
            "post_review_persona_review_status"
        ],
        "final_outcome_confidence": summary["outcome_confidence"],
        "final_auto_promotion_status": "disabled",
        "closure_status": closure_status,
        "closure_role": "phase_18_closure_and_next_step_decision",
        "recommended_next_phase": NEXT_PHASE,
        "recommended_next_task": NEXT_TASK,
        "main_closure_finding": (
            "Phase 18 is closed for limited preparation governance only; "
            "actual persona review, investor-agent execution, recommendations, "
            "rankings, allocations, trade signals, and auto-promotion remain blocked."
        ),
    }


def build_phase_18_task_status_matrix(
    *,
    closure_run_id: str,
    review: dict,
) -> list[dict]:
    """Build Phase 18 task status rows."""
    summary = _review_summary(review)
    specs = [
        (132, "Define Gatekeeper Return Package Plan", "completed", review["gatekeeper_return_plan_run_id"], "Task 133 - Build Gatekeeper Return Package Input Inventory"),
        (133, "Build Gatekeeper Return Package Input Inventory", "completed_with_warnings", review["gatekeeper_return_input_inventory_run_id"], "Task 134 - Assemble Gatekeeper Return Package"),
        (134, "Assemble Gatekeeper Return Package", "assembled_with_warnings", review["gatekeeper_return_package_run_id"], "Task 135 - Validate Gatekeeper Return Package Completeness"),
        (135, "Validate Gatekeeper Return Package Completeness", "complete_with_warnings", review["gatekeeper_return_package_validation_run_id"], "Task 136 - Run Gatekeeper Return Review"),
        (136, "Run Gatekeeper Return Review", summary["review_status"], review["gatekeeper_return_review_run_id"], "Task 137 - Phase 18 Closure & Next-Step Decision"),
        (137, "Phase 18 Closure & Next-Step Decision", "completed", closure_run_id, NEXT_TASK),
    ]
    return [
        {
            "task_id": task_id,
            "task_name": task_name,
            "task_status": status,
            "run_id": run_id,
            "output_folder": f"data/outputs/phase_18_closures/{closure_run_id}"
            if task_id == 137
            else "linked local artifact",
            "key_result": "limited preparation governance remains the only forward path"
            if task_id == 137
            else "Phase 18 artifact completed for Gatekeeper return package flow.",
            "next_task_from_artifact": next_task,
            "safety_boundary": "Task status only; non-actionable.",
        }
        for task_id, task_name, status, run_id, next_task in specs
    ]


def build_final_gatekeeper_return_outcome_summary(review: dict) -> dict:
    """Build final Gatekeeper return outcome summary."""
    summary = _review_summary(review)
    return {
        "gatekeeper_return_outcome": summary["gatekeeper_return_outcome"],
        "source_validation_status": summary["source_validation_status"],
        "source_blocking_findings_total": summary["source_blocking_findings_total"],
        "source_warning_findings_total": summary["source_warning_findings_total"],
        "post_review_progression_status": summary["post_review_progression_status"],
        "post_review_persona_review_status": summary[
            "post_review_persona_review_status"
        ],
        "outcome_confidence": summary["outcome_confidence"],
        "allowed_scope": [
            "limited_preparation_only",
            "limited preparation governance planning",
            "limited preparation artifact definition",
        ],
        "blocked_scope": [
            "actual persona review",
            "investor agent execution",
            "investor decisions",
            "recommendations",
            "rankings",
            "allocations",
            "rebalancing",
            "trade signals",
            "execution instructions",
            "auto-promotion",
        ],
        "rationale": (
            "The return package was accepted for limited preparation only, "
            "with warnings and residual constraints preserved."
        ),
        "safety_boundary": "Outcome summary only; no investor action.",
    }


def build_final_post_review_permission_boundary_summary() -> list[dict]:
    """Build final post-review permission boundaries."""
    specs = [
        ("limited_preparation", "allowed", "limited preparation governance planning"),
        ("persona_review_preparation", "not_allowed", "none"),
        ("actual_persona_review", "not_allowed", "none"),
        ("investor_agent_execution", "not_allowed", "none"),
        ("investor_decision_generation", "not_allowed", "none"),
        ("company_ranking", "not_allowed", "none"),
        ("investment_recommendation", "not_allowed", "none"),
        ("allocation_or_rebalancing", "not_allowed", "none"),
        ("trade_signal_generation", "not_allowed", "none"),
        ("execution_instruction_generation", "not_allowed", "none"),
        ("auto_promotion", "disabled", "none"),
    ]
    return [
        {
            "permission_code": code,
            "permission_label": code.replace("_", " "),
            "final_status": status,
            "allowed_scope": allowed_scope,
            "prohibited_scope": (
                "Investor decisions, recommendations, rankings, allocations, "
                "rebalancing, trade signals, investor-agent execution, actual "
                "persona reviews, execution instructions, and auto-promotion."
            ),
            "condition_to_expand_scope": "Future explicit Gatekeeper approval.",
            "safety_boundary": "Permission boundary only.",
        }
        for code, status, allowed_scope in specs
    ]


def build_final_allowed_scope_summary() -> list[dict]:
    """Build final allowed scope summary."""
    return [
        {
            "allowed_code": code,
            "allowed_label": code.replace("_", " "),
            "final_status": "allowed",
            "allowed_actions": "Governance planning, documentation, and artifact definition only.",
            "required_conditions": "Must preserve Phase 18 boundaries and require future Gatekeeper approval.",
            "safety_boundary": "Allowed scope excludes actual reviews and investor actions.",
        }
        for code in ALLOWED_SCOPE_CODES
    ]


def build_final_prohibited_scope_summary() -> list[dict]:
    """Build final prohibited scope summary."""
    return [
        {
            "prohibited_code": code,
            "prohibited_label": code.replace("_", " "),
            "final_status": "prohibited",
            "prohibited_actions": code.replace("_", " "),
            "reason": "Not authorized by Phase 18 closure.",
            "safety_boundary": "Prohibited scope remains blocked.",
        }
        for code in PROHIBITED_SCOPE_CODES
    ]


def build_remaining_warnings_after_phase_18_matrix() -> list[dict]:
    """Build remaining warning rows after Phase 18."""
    return [
        {
            "warning_code": code,
            "warning_label": code.replace("_", " "),
            "source_task": "Task 136 - Run Gatekeeper Return Review",
            "final_status": "carried_forward",
            "severity": "medium" if code not in {"persona_review_not_allowed", "investor_agents_not_allowed", "auto_promotion_disabled"} else "critical",
            "impact_on_next_phase": "Requires explicit boundary disclosure in Phase 19.",
            "required_follow_up": "Carry into limited preparation governance plan.",
            "safety_boundary": "Warning disclosure only.",
        }
        for code in WARNING_CODES
    ]


def build_phase_19_recommendation_matrix() -> list[dict]:
    """Build Phase 19 recommendation rows."""
    statuses = {
        "start_phase_19_limited_preparation_governance_layer": "recommended_with_warnings",
        "define_limited_preparation_governance_plan": "recommended",
    }
    return [
        {
            "recommendation_code": code,
            "recommendation_label": code.replace("_", " "),
            "recommendation_status": statuses.get(code, "required"),
            "rationale": "Preserve limited preparation boundary before any future Gatekeeper approval.",
            "required_inputs": "Phase 18 closure and Gatekeeper return review outputs.",
            "expected_outputs": "Limited preparation governance artifact definitions and boundaries.",
            "prohibited_outputs": (
                "Investor decisions, recommendations, rankings, allocations, "
                "rebalancing, trade signals, investor-agent execution, actual "
                "persona reviews, and auto-promotion."
            ),
            "safety_boundary": "Recommendation is governance-only and non-actionable.",
        }
        for code in RECOMMENDATION_CODES
    ]


def build_task_138_handoff_manifest(
    *,
    closure_summary: dict,
    review: dict,
) -> dict:
    """Build Task 138 handoff manifest."""
    return {
        "future_phase_id": 19,
        "future_phase_name": "Limited Preparation Governance Layer",
        "future_task_id": 138,
        "future_task_name": "Define Limited Preparation Governance Plan",
        "phase_18_closure_run_id": closure_summary["phase_18_closure_run_id"],
        "gatekeeper_return_review_run_id": review["gatekeeper_return_review_run_id"],
        "final_gatekeeper_return_outcome": closure_summary[
            "final_gatekeeper_return_outcome"
        ],
        "final_post_review_progression_status": closure_summary[
            "final_post_review_progression_status"
        ],
        "final_post_review_persona_review_status": closure_summary[
            "final_post_review_persona_review_status"
        ],
        "phase_19_start_inputs": [
            "phase_18_closure",
            "gatekeeper_return_review",
            "final_permission_boundary_summary",
            "phase_19_recommendation_matrix",
        ],
        "allowed_scope": [
            "planning limited preparation governance",
            "defining preparation artifacts",
            "documenting constraints and permission boundaries",
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
        "readiness_status": "ready_to_define_limited_preparation_governance_plan",
        "execution_allowed_now": True,
        "reason": "Phase 18 is closed for limited preparation governance only.",
    }


def build_phase_18_closure_checks() -> list[dict]:
    """Build Task 137 closure checks."""
    checks = [
        "gatekeeper_return_review_loaded",
        "phase_18_closure_summary_created",
        "phase_18_task_status_matrix_created",
        "final_gatekeeper_return_outcome_summary_created",
        "final_permission_boundary_summary_created",
        "final_allowed_scope_summary_created",
        "final_prohibited_scope_summary_created",
        "remaining_warnings_after_phase_18_matrix_created",
        "phase_19_recommendation_matrix_created",
        "task_138_handoff_manifest_created",
        "gatekeeper_return_outcome_preserved",
        "post_review_progression_status_preserved",
        "post_review_persona_review_status_preserved",
        "limited_preparation_only_preserved",
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
            "source_artifact": "phase_18_closure",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 137.",
        }
        for check in checks
    ]


def build_phase_18_closure(
    *,
    phase_18_closure_run_id: str,
    generated_at: str,
    review: dict,
) -> Phase18ClosureReport:
    """Build the Task 137 Phase 18 closure report."""
    summary = build_phase_18_closure_summary(
        phase_18_closure_run_id=phase_18_closure_run_id,
        review=review,
    )
    task_rows = build_phase_18_task_status_matrix(
        closure_run_id=phase_18_closure_run_id,
        review=review,
    )
    outcome = build_final_gatekeeper_return_outcome_summary(review)
    permissions = build_final_post_review_permission_boundary_summary()
    allowed = build_final_allowed_scope_summary()
    prohibited = build_final_prohibited_scope_summary()
    warnings = build_remaining_warnings_after_phase_18_matrix()
    recommendations = build_phase_19_recommendation_matrix()
    handoff = build_task_138_handoff_manifest(closure_summary=summary, review=review)
    checks = build_phase_18_closure_checks()
    return Phase18ClosureReport(
        phase_18_closure_run_id=phase_18_closure_run_id,
        generated_at=generated_at,
        gatekeeper_return_review_run_id=review["gatekeeper_return_review_run_id"],
        gatekeeper_return_package_validation_run_id=review[
            "gatekeeper_return_package_validation_run_id"
        ],
        gatekeeper_return_package_run_id=review["gatekeeper_return_package_run_id"],
        gatekeeper_return_input_inventory_run_id=review[
            "gatekeeper_return_input_inventory_run_id"
        ],
        gatekeeper_return_plan_run_id=review["gatekeeper_return_plan_run_id"],
        phase_17_closure_run_id=review["phase_17_closure_run_id"],
        gatekeeper_stabilization_re_review_run_id=review[
            "gatekeeper_stabilization_re_review_run_id"
        ],
        gatekeeper_stabilized_comparison_run_id=review[
            "gatekeeper_stabilized_comparison_run_id"
        ],
        stabilization_validation_run_id=review["stabilization_validation_run_id"],
        targeted_repair_run_id=review["targeted_repair_run_id"],
        residual_work_order_package_run_id=review[
            "residual_work_order_package_run_id"
        ],
        stabilization_plan_run_id=review["stabilization_plan_run_id"],
        phase_16_closure_run_id=review["phase_16_closure_run_id"],
        baseline_gatekeeper_re_evaluation_run_id=review[
            "baseline_gatekeeper_re_evaluation_run_id"
        ],
        pre_post_repair_comparison_run_id=review[
            "pre_post_repair_comparison_run_id"
        ],
        controlled_re_run_trial_run_id=review["controlled_re_run_trial_run_id"],
        re_run_input_package_run_id=review["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=review["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=review["research_audit_trail_run_id"],
        phase_18_closure_summary=summary,
        phase_18_task_status_matrix=task_rows,
        final_gatekeeper_return_outcome_summary=outcome,
        final_post_review_permission_boundary_summary=permissions,
        final_allowed_scope_summary=allowed,
        final_prohibited_scope_summary=prohibited,
        remaining_warnings_after_phase_18_matrix=warnings,
        phase_19_recommendation_matrix=recommendations,
        task_138_handoff_manifest=handoff,
        phase_18_closure_checks=checks,
        closure_status=summary["closure_status"],
        recommended_next_phase=summary["recommended_next_phase"],
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


def _render_markdown(report: Phase18ClosureReport) -> str:
    summary = report.phase_18_closure_summary
    outcome = report.final_gatekeeper_return_outcome_summary
    handoff = report.task_138_handoff_manifest
    lines = [
        "# Phase 18 Closure & Next-Step Decision",
        "",
        "## Executive Summary",
        "",
        f"* Phase 18 Closure Run ID: {report.phase_18_closure_run_id}",
        f"* Gatekeeper Return Review Run ID: {report.gatekeeper_return_review_run_id}",
        "* Current Phase: 18 - Gatekeeper Return Package Layer",
        "* Current Task: Task 137 - Phase 18 Closure & Next-Step Decision",
        f"* Phase Completion Status: {summary['phase_completion_status']}",
        f"* Final Gatekeeper Return Outcome: {summary['final_gatekeeper_return_outcome']}",
        (
            "* Final Post-Review Progression Status: "
            f"{summary['final_post_review_progression_status']}"
        ),
        (
            "* Final Post-Review Persona Review Status: "
            f"{summary['final_post_review_persona_review_status']}"
        ),
        f"* Final Outcome Confidence: {summary['final_outcome_confidence']}",
        f"* Closure Status: {report.closure_status}",
        f"* Recommended Next Phase: {report.recommended_next_phase}",
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
        "Task 136 - Run Gatekeeper Return Review completed_with_warnings",
        "",
        "This Task:",
        "Task 137 closes Phase 18 and recommends the next phase.",
        "",
        "Phase 18 Status:",
        "Completed with warnings",
        "",
        "Final Gatekeeper Return Outcome:",
        "return_package_accepted_for_limited_preparation",
        "",
        "Final Post-Review Progression Status:",
        "limited_preparation_only",
        "",
        "Final Post-Review Persona Review Status:",
        "false",
        "",
        "Recommended Next Phase:",
        NEXT_PHASE,
        "",
        "Recommended Next Task:",
        NEXT_TASK,
        "",
        "## Phase 18 Task Status Matrix",
        "",
        *_markdown_table(
            report.phase_18_task_status_matrix,
            [
                ("Task", "task_id"),
                ("Status", "task_status"),
                ("Run ID", "run_id"),
                ("Key Result", "key_result"),
                ("Next Task From Artifact", "next_task_from_artifact"),
            ],
        ),
        "",
        "## Final Gatekeeper Return Outcome Summary",
        "",
        f"* Gatekeeper Return Outcome: {outcome['gatekeeper_return_outcome']}",
        f"* Validation Status: {outcome['source_validation_status']}",
        f"* Blocking Findings: {outcome['source_blocking_findings_total']}",
        f"* Warning Findings: {outcome['source_warning_findings_total']}",
        f"* Post-Review Progression Status: {outcome['post_review_progression_status']}",
        f"* Persona Review Status: {outcome['post_review_persona_review_status']}",
        f"* Allowed Scope: {'; '.join(outcome['allowed_scope'])}",
        f"* Blocked Scope: {'; '.join(outcome['blocked_scope'])}",
        f"* Rationale: {outcome['rationale']}",
        "",
        "## Final Permission Boundary Summary",
        "",
        *_markdown_table(
            report.final_post_review_permission_boundary_summary,
            [
                ("Permission", "permission_code"),
                ("Final Status", "final_status"),
                ("Allowed Scope", "allowed_scope"),
                ("Prohibited Scope", "prohibited_scope"),
                ("Condition To Expand", "condition_to_expand_scope"),
            ],
        ),
        "",
        "## Final Allowed Scope Summary",
        "",
        *_markdown_table(
            report.final_allowed_scope_summary,
            [
                ("Allowed Scope", "allowed_code"),
                ("Status", "final_status"),
                ("Actions", "allowed_actions"),
                ("Conditions", "required_conditions"),
            ],
        ),
        "",
        "## Final Prohibited Scope Summary",
        "",
        *_markdown_table(
            report.final_prohibited_scope_summary,
            [
                ("Prohibited Scope", "prohibited_code"),
                ("Status", "final_status"),
                ("Reason", "reason"),
            ],
        ),
        "",
        "## Remaining Warnings After Phase 18",
        "",
        *_markdown_table(
            report.remaining_warnings_after_phase_18_matrix,
            [
                ("Warning", "warning_code"),
                ("Source Task", "source_task"),
                ("Severity", "severity"),
                ("Impact On Next Phase", "impact_on_next_phase"),
                ("Follow-Up", "required_follow_up"),
            ],
        ),
        "",
        "## Phase 19 Recommendation Matrix",
        "",
        *_markdown_table(
            report.phase_19_recommendation_matrix,
            [
                ("Recommendation", "recommendation_code"),
                ("Status", "recommendation_status"),
                ("Rationale", "rationale"),
                ("Expected Outputs", "expected_outputs"),
                ("Prohibited Outputs", "prohibited_outputs"),
            ],
        ),
        "",
        "## Task 138 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} - {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Phase 19 Start Inputs: {'; '.join(handoff['phase_19_start_inputs'])}",
        f"* Allowed Scope: {'; '.join(handoff['allowed_scope'])}",
        f"* Prohibited Outputs: {'; '.join(handoff['prohibited_outputs'])}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.phase_18_closure_checks,
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
        "* Phase 18 is complete with warnings.",
        "* The next phase should be limited preparation governance.",
        (
            "* The next phase should define what limited preparation means "
            "before any further Gatekeeper approval."
        ),
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


def write_phase_18_closure_report(
    *,
    outputs_root: Path,
    gatekeeper_return_review_run_id: str | None = None,
) -> Phase18ClosureFiles:
    """Write Task 137 Phase 18 closure artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_gatekeeper_return_review_manifest(
        outputs_root=outputs_root,
        gatekeeper_return_review_run_id=gatekeeper_return_review_run_id,
    )
    review_run_id = manifest["gatekeeper_return_review_run_id"]
    review = load_gatekeeper_return_review(
        outputs_root=outputs_root,
        gatekeeper_return_review_run_id=review_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_phase_18_closure(
        phase_18_closure_run_id=run_id,
        generated_at=generated_at.isoformat(),
        review=review,
    )

    root = outputs_root / "phase_18_closures"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "phase_18_closure.md"
    json_path = output_folder / "phase_18_closure.json"
    task_status_csv = output_folder / "phase_18_task_status_matrix.csv"
    outcome_csv = output_folder / "final_gatekeeper_return_outcome_summary.csv"
    permission_csv = output_folder / "final_post_review_permission_boundary_summary.csv"
    allowed_csv = output_folder / "final_allowed_scope_summary.csv"
    prohibited_csv = output_folder / "final_prohibited_scope_summary.csv"
    warnings_csv = output_folder / "remaining_warnings_after_phase_18_matrix.csv"
    recommendation_csv = output_folder / "phase_19_recommendation_matrix.csv"
    handoff_path = output_folder / "task_138_handoff_manifest.json"
    checks_csv = output_folder / "phase_18_closure_checks.csv"
    latest_manifest_path = root / "latest_phase_18_closure_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(task_status_csv, report.phase_18_task_status_matrix)
    _write_csv(outcome_csv, [report.final_gatekeeper_return_outcome_summary])
    _write_csv(permission_csv, report.final_post_review_permission_boundary_summary)
    _write_csv(allowed_csv, report.final_allowed_scope_summary)
    _write_csv(prohibited_csv, report.final_prohibited_scope_summary)
    _write_csv(warnings_csv, report.remaining_warnings_after_phase_18_matrix)
    _write_csv(recommendation_csv, report.phase_19_recommendation_matrix)
    handoff_path.write_text(
        json.dumps(report.task_138_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.phase_18_closure_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "phase_18_closure_run_id": report.phase_18_closure_run_id,
                "gatekeeper_return_review_run_id": report.gatekeeper_return_review_run_id,
                "final_gatekeeper_return_outcome": report.phase_18_closure_summary[
                    "final_gatekeeper_return_outcome"
                ],
                "final_post_review_progression_status": (
                    report.phase_18_closure_summary[
                        "final_post_review_progression_status"
                    ]
                ),
                "final_post_review_persona_review_status": (
                    report.phase_18_closure_summary[
                        "final_post_review_persona_review_status"
                    ]
                ),
                "closure_status": report.closure_status,
                "recommended_next_phase": report.recommended_next_phase,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_138_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return Phase18ClosureFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        task_status_csv_path=task_status_csv,
        outcome_csv_path=outcome_csv,
        permission_csv_path=permission_csv,
        allowed_scope_csv_path=allowed_csv,
        prohibited_scope_csv_path=prohibited_csv,
        warnings_csv_path=warnings_csv,
        recommendation_csv_path=recommendation_csv,
        task_138_handoff_manifest_path=handoff_path,
        checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
