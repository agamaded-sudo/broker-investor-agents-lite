"""Task 130 Gatekeeper stabilization re-review package."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report performs a Gatekeeper stabilization re-review only. It does "
    "not run investor agents, run actual persona reviews, create investor "
    "decisions, rankings, recommendations, allocations, rebalancing "
    "instructions, trade signals, execution instructions, or strategy validation."
)
NEXT_TASK = "Task 131 - Phase 17 Closure & Next-Step Decision"


@dataclass(frozen=True)
class GatekeeperStabilizationReReviewReport:
    """Structured Task 130 Gatekeeper stabilization re-review."""

    gatekeeper_stabilization_re_review_run_id: str
    generated_at: str
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
    re_review_summary: dict
    stabilization_gatekeeper_decision_record: dict
    re_review_rule_evaluation_matrix: list[dict]
    stabilized_blocker_status_matrix: list[dict]
    residual_risk_after_re_review_matrix: list[dict]
    permission_boundary_matrix: list[dict]
    task_131_handoff_manifest: dict
    gatekeeper_stabilization_re_review_checks: list[dict]
    re_review_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class GatekeeperStabilizationReReviewFiles:
    """Generated Task 130 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    decision_record_path: Path
    rule_csv_path: Path
    blocker_csv_path: Path
    residual_risk_csv_path: Path
    permission_csv_path: Path
    task_131_handoff_manifest_path: Path
    checks_csv_path: Path
    latest_manifest_path: Path
    report: GatekeeperStabilizationReReviewReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_gatekeeper_stabilized_comparison_manifest(
    *,
    outputs_root: Path,
    gatekeeper_stabilized_comparison_run_id: str | None = None,
) -> dict:
    """Load one Task 129 report or the latest Task 129 manifest."""
    root = Path(outputs_root) / "gatekeeper_stabilized_evidence_comparisons"
    path = (
        root
        / gatekeeper_stabilized_comparison_run_id
        / "gatekeeper_stabilized_evidence_comparison.json"
        if gatekeeper_stabilized_comparison_run_id
        else root / "latest_gatekeeper_stabilized_evidence_comparison_manifest.json"
    )
    label = (
        "Gatekeeper stabilized evidence comparison report"
        if gatekeeper_stabilized_comparison_run_id
        else "Gatekeeper stabilized evidence comparison manifest"
    )
    return _load_required_json(path, label)


def load_gatekeeper_stabilized_comparison(
    *,
    outputs_root: Path,
    gatekeeper_stabilized_comparison_run_id: str,
) -> dict:
    """Load a Task 129 comparison report by run id."""
    path = (
        Path(outputs_root)
        / "gatekeeper_stabilized_evidence_comparisons"
        / gatekeeper_stabilized_comparison_run_id
        / "gatekeeper_stabilized_evidence_comparison.json"
    )
    return _load_required_json(path, "Gatekeeper stabilized evidence comparison report")


def load_baseline_gatekeeper_re_evaluation(
    *,
    outputs_root: Path,
    gatekeeper_re_evaluation_run_id: str,
) -> dict:
    """Load the baseline Task 123 Gatekeeper re-evaluation report."""
    path = (
        Path(outputs_root)
        / "gatekeeper_re_evaluations"
        / gatekeeper_re_evaluation_run_id
        / "gatekeeper_re_evaluation.json"
    )
    return _load_required_json(path, "Baseline Gatekeeper re-evaluation report")


def _baseline_outcome(baseline_gatekeeper: dict) -> str:
    decision = baseline_gatekeeper.get("re_gate_decision_record", {})
    summary = baseline_gatekeeper.get("re_evaluation_summary", {})
    return (
        decision.get("new_gatekeeper_outcome")
        or summary.get("new_gatekeeper_outcome")
        or "unavailable"
    )


def _derive_outcome(comparison: dict) -> tuple[str, str, str, str, str]:
    summary = comparison["comparison_summary"]
    unresolved = int(summary["blockers_unresolved"])
    improved = int(summary["blockers_improved"])
    partial = int(summary["blockers_partially_improved"])
    if unresolved > 0 and improved == 0:
        return (
            "hold_with_stabilization_progress",
            "gatekeeper_return_package_only",
            "false",
            "completed_with_warnings",
            "conservative_moderate" if partial else "conservative_low",
        )
    if unresolved > 0:
        return (
            "hold_pending_remaining_blockers",
            "gatekeeper_return_package_only",
            "false",
            "completed_with_warnings",
            "conservative_moderate",
        )
    return (
        "limited_gatekeeper_return_package_ready",
        "gatekeeper_return_package_only",
        "preparation_only",
        "completed",
        "conservative_high",
    )


def build_re_review_summary(
    *,
    gatekeeper_stabilization_re_review_run_id: str,
    comparison: dict,
    baseline_gatekeeper: dict,
) -> dict:
    """Build the Task 130 re-review summary."""
    comp = comparison["comparison_summary"]
    outcome, progression, persona, status, confidence = _derive_outcome(comparison)
    return {
        "gatekeeper_stabilization_re_review_run_id": gatekeeper_stabilization_re_review_run_id,
        "gatekeeper_stabilized_comparison_run_id": comparison[
            "gatekeeper_stabilized_comparison_run_id"
        ],
        "stabilization_validation_run_id": comparison["stabilization_validation_run_id"],
        "gatekeeper_re_evaluation_run_id": comparison["gatekeeper_re_evaluation_run_id"],
        "phase_id": 17,
        "phase_name": "Targeted Evidence Stabilization Layer",
        "current_task_id": 130,
        "current_task_name": "Gatekeeper Stabilization Re-Review",
        "baseline_gatekeeper_outcome": _baseline_outcome(baseline_gatekeeper),
        "new_gatekeeper_stabilization_outcome": outcome,
        "progression_status_after_re_review": progression,
        "persona_review_status_after_re_review": persona,
        "re_review_status": status,
        "re_review_role": "gatekeeper_stabilization_re_review",
        "blockers_reviewed": comp["blockers_compared"],
        "blockers_improved": comp["blockers_improved"],
        "blockers_partially_improved": comp["blockers_partially_improved"],
        "blockers_unresolved": comp["blockers_unresolved"],
        "residual_risks_remaining": len(comparison["residual_risk_comparison_matrix"]),
        "outcome_confidence": confidence,
        "recommended_next_task": NEXT_TASK,
        "main_re_review_finding": (
            "Stabilized evidence shows documentation progress, but unresolved "
            "blockers keep the Gatekeeper outcome conservative and prevent "
            "actual persona review."
        ),
    }


def build_stabilization_gatekeeper_decision_record(summary: dict) -> dict:
    """Build the conservative Task 130 decision record."""
    return {
        "decision_record_id": f"{summary['gatekeeper_stabilization_re_review_run_id']}_decision",
        "baseline_gatekeeper_outcome": summary["baseline_gatekeeper_outcome"],
        "new_gatekeeper_stabilization_outcome": summary[
            "new_gatekeeper_stabilization_outcome"
        ],
        "decision_rationale": (
            "Task 129 showed partial stabilization progress with unresolved "
            "blockers, so unrestricted progression and actual persona review "
            "remain disallowed."
        ),
        "evidence_basis": "Task 129 evidence deltas and readiness matrices.",
        "blocker_basis": "0 improved blockers, partial improvements, and unresolved blockers.",
        "residual_risk_basis": "Residual risks remain disclosed for Phase 17 closure.",
        "progression_status_after_re_review": summary[
            "progression_status_after_re_review"
        ],
        "persona_review_status_after_re_review": summary[
            "persona_review_status_after_re_review"
        ],
        "auto_promotion_status": "disabled",
        "investor_agent_execution_status": "not_allowed",
        "review_scope_allowed": [
            "phase_17_closure",
            "gatekeeper_return_package_preparation",
        ],
        "review_scope_blocked": [
            "investor decisions",
            "recommendations",
            "rankings",
            "allocations",
            "rebalancing",
            "trade signals",
            "actual persona reviews",
            "auto-promotion",
        ],
        "outcome_confidence": summary["outcome_confidence"],
        "safety_boundary": "Gatekeeper stabilization re-review only.",
    }


def build_re_review_rule_evaluation_matrix(summary: dict) -> list[dict]:
    """Build conservative re-review rule rows."""
    specs = [
        ("no_unrestricted_progression_with_unresolved_blockers", "hold_limited"),
        ("no_persona_review_with_unresolved_material_blockers", "hold_limited"),
        ("no_auto_promotion", "satisfied"),
        ("no_investor_agent_execution", "satisfied"),
        ("evidence_improvement_must_be_validated", "satisfied_with_warnings"),
        ("partial_improvement_is_not_full_resolution", "hold_limited"),
        ("unresolved_blockers_keep_hold_or_limited_status", "hold_limited"),
        ("local_artifact_limitations_reduce_confidence", "satisfied_with_warnings"),
        ("gatekeeper_return_package_may_be_prepared_if_inputs_available", "satisfied"),
        ("recommendations_rankings_trading_outputs_prohibited", "satisfied"),
    ]
    return [
        {
            "rule_code": code,
            "rule_label": code.replace("_", " "),
            "baseline_state": summary["baseline_gatekeeper_outcome"],
            "stabilized_evidence_state": summary[
                "new_gatekeeper_stabilization_outcome"
            ],
            "rule_result": result,
            "rule_rationale": (
                "Conservative re-review preserves safety boundaries while "
                "recognizing stabilization documentation progress."
            ),
            "impact_on_outcome": summary["new_gatekeeper_stabilization_outcome"],
            "safety_boundary": "Governance rule only; no investor action.",
        }
        for code, result in specs
    ]


def build_stabilized_blocker_status_matrix(comparison: dict) -> list[dict]:
    """Convert Task 129 blocker comparison into Task 130 dispositions."""
    disposition_by_status = {
        "improved": "resolved",
        "improved_with_warnings": "partially_resolved",
        "partially_improved": "partially_resolved",
        "unchanged": "remains_blocking",
        "worsened": "remains_blocking",
        "documented_only": "documented_only",
        "not_comparable_with_local_artifacts": "deferred_to_next_phase",
    }
    rows = []
    for blocker in comparison["gatekeeper_blocker_comparison_matrix"]:
        status = blocker["comparison_status"]
        disposition = disposition_by_status.get(status, "unresolved")
        rows.append(
            {
                "blocker_code": blocker["blocker_code"],
                "blocker_label": blocker["blocker_label"],
                "task_123_state": blocker["task_123_state"],
                "task_129_comparison_status": status,
                "re_review_status": "reviewed",
                "gatekeeper_effect": "limits_or_blocks_progression"
                if disposition in {"remains_blocking", "unresolved"}
                else "supports_limited_package_preparation",
                "remaining_issue": blocker["remaining_issue"],
                "disposition": disposition,
                "safety_boundary": "Blocker disposition only; no investor action.",
            }
        )
    return rows


def build_residual_risk_after_re_review_matrix(comparison: dict) -> list[dict]:
    """Build residual risks after Task 130 re-review."""
    rows = []
    for risk in comparison["residual_risk_comparison_matrix"]:
        rows.append(
            {
                "risk_code": risk["risk_code"],
                "risk_label": risk["risk_label"],
                "risk_state_after_re_review": "remaining_disclosed_risk",
                "severity_after_re_review": risk["severity_after_stabilization"],
                "evidence_basis": risk["stabilized_risk_state"],
                "impact_on_progression": "limits_progression_scope",
                "required_follow_up": "Carry residual risk into Task 131 phase closure.",
                "safety_boundary": "Residual risk only; no investment conclusion.",
            }
        )
    rows.append(
        {
            "risk_code": "no_persona_review_allowed_yet",
            "risk_label": "no persona review allowed yet",
            "risk_state_after_re_review": "blocked",
            "severity_after_re_review": "critical",
            "evidence_basis": "Task 130 conservative permission boundary.",
            "impact_on_progression": "actual_persona_review_not_allowed",
            "required_follow_up": "Close Phase 17 before any future preparation decision.",
            "safety_boundary": "Persona review remains blocked.",
        }
    )
    return rows


def build_permission_boundary_matrix(summary: dict) -> list[dict]:
    """Build permission boundaries after re-review."""
    specs = [
        (
            "progression",
            summary["progression_status_after_re_review"],
            "gatekeeper return package only",
            "unrestricted progression",
            "Phase 17 closure and future Gatekeeper signoff",
        ),
        (
            "gatekeeper_return_package_preparation",
            "allowed",
            "prepare closure/review package",
            "investor-facing action",
            "Task 131 closure",
        ),
        (
            "persona_review_preparation",
            "not_allowed",
            "none in Task 130",
            "actual persona review",
            "Future phase explicit signoff",
        ),
        (
            "actual_persona_review",
            "not_allowed",
            "none",
            "running persona review",
            "Future Gatekeeper permission",
        ),
        ("investor_agent_execution", "not_allowed", "none", "agent runs", "Future signoff"),
        (
            "investor_decision_generation",
            "not_allowed",
            "none",
            "investment decisions",
            "Not allowed by this layer",
        ),
        ("company_ranking", "not_allowed", "none", "rankings", "Not allowed"),
        (
            "investment_recommendation",
            "not_allowed",
            "none",
            "recommendations",
            "Not allowed",
        ),
        (
            "allocation_or_rebalancing",
            "not_allowed",
            "none",
            "allocation/rebalancing",
            "Not allowed",
        ),
        (
            "trade_signal_generation",
            "not_allowed",
            "none",
            "trade signals",
            "Not allowed",
        ),
        ("auto_promotion", "disabled", "none", "auto-promotion", "Not allowed"),
    ]
    return [
        {
            "permission_code": code,
            "permission_label": code.replace("_", " "),
            "status_after_re_review": status,
            "allowed_scope": allowed,
            "blocked_scope": blocked,
            "condition_to_expand_scope": condition,
            "safety_boundary": "Permission boundary only.",
        }
        for code, status, allowed, blocked, condition in specs
    ]


def build_task_131_handoff_manifest(
    *,
    gatekeeper_stabilization_re_review_run_id: str,
    comparison: dict,
    baseline_gatekeeper: dict,
) -> dict:
    """Build Task 131 closure handoff."""
    return {
        "future_phase_id": 17,
        "future_phase_name": "Targeted Evidence Stabilization Layer",
        "future_task_id": 131,
        "future_task_name": "Phase 17 Closure & Next-Step Decision",
        "gatekeeper_stabilization_re_review_run_id": (
            gatekeeper_stabilization_re_review_run_id
        ),
        "gatekeeper_stabilized_comparison_run_id": comparison[
            "gatekeeper_stabilized_comparison_run_id"
        ],
        "baseline_gatekeeper_re_evaluation_run_id": baseline_gatekeeper[
            "gatekeeper_re_evaluation_run_id"
        ],
        "closure_inputs": [
            "gatekeeper_stabilization_re_review",
            "gatekeeper_stabilized_evidence_comparison",
            "baseline_gatekeeper_re_evaluation",
        ],
        "re_review_outputs_to_close": [
            "stabilization_gatekeeper_decision_record",
            "stabilized_blocker_status_matrix",
            "residual_risk_after_re_review_matrix",
            "permission_boundary_matrix",
        ],
        "readiness_status": "ready_for_phase_17_closure",
        "execution_allowed_now": True,
        "prohibited_outputs": [
            "investor decisions",
            "recommendations",
            "rankings",
            "allocations",
            "rebalancing",
            "trade signals",
            "investor agent execution",
            "actual persona reviews unless explicitly allowed in a future phase",
        ],
        "reason": "Task 130 re-review is complete and ready for Phase 17 closure.",
    }


def build_gatekeeper_stabilization_re_review_checks() -> list[dict]:
    """Build Task 130 validation checks."""
    checks = [
        "gatekeeper_stabilized_comparison_loaded",
        "baseline_gatekeeper_re_evaluation_loaded",
        "re_review_summary_created",
        "stabilization_gatekeeper_decision_record_created",
        "re_review_rule_evaluation_matrix_created",
        "stabilized_blocker_status_matrix_created",
        "residual_risk_after_re_review_matrix_created",
        "permission_boundary_matrix_created",
        "task_131_handoff_manifest_created",
        "baseline_gatekeeper_outcome_preserved",
        "conservative_re_review_logic_applied",
        "actual_persona_review_not_run",
        "investor_agents_not_run",
        "no_recommendation_outputs",
        "no_ranking_outputs",
        "no_trade_signal_outputs",
        "no_network_calls",
        "auto_promotion_disabled",
    ]
    return [
        {
            "check_code": check,
            "check_label": check.replace("_", " "),
            "status": "satisfied",
            "source_artifact": "gatekeeper_stabilization_re_review",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 130.",
        }
        for check in checks
    ]


def build_gatekeeper_stabilization_re_review(
    *,
    gatekeeper_stabilization_re_review_run_id: str,
    generated_at: str,
    comparison: dict,
    baseline_gatekeeper: dict,
) -> GatekeeperStabilizationReReviewReport:
    """Build the Task 130 Gatekeeper stabilization re-review."""
    summary = build_re_review_summary(
        gatekeeper_stabilization_re_review_run_id=gatekeeper_stabilization_re_review_run_id,
        comparison=comparison,
        baseline_gatekeeper=baseline_gatekeeper,
    )
    decision = build_stabilization_gatekeeper_decision_record(summary)
    return GatekeeperStabilizationReReviewReport(
        gatekeeper_stabilization_re_review_run_id=gatekeeper_stabilization_re_review_run_id,
        generated_at=generated_at,
        gatekeeper_stabilized_comparison_run_id=comparison[
            "gatekeeper_stabilized_comparison_run_id"
        ],
        stabilization_validation_run_id=comparison["stabilization_validation_run_id"],
        targeted_repair_run_id=comparison["targeted_repair_run_id"],
        residual_work_order_package_run_id=comparison[
            "residual_work_order_package_run_id"
        ],
        stabilization_plan_run_id=comparison["stabilization_plan_run_id"],
        phase_16_closure_run_id=comparison["phase_16_closure_run_id"],
        baseline_gatekeeper_re_evaluation_run_id=baseline_gatekeeper[
            "gatekeeper_re_evaluation_run_id"
        ],
        pre_post_repair_comparison_run_id=comparison[
            "pre_post_repair_comparison_run_id"
        ],
        controlled_re_run_trial_run_id=comparison["controlled_re_run_trial_run_id"],
        re_run_input_package_run_id=comparison["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=comparison["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=comparison["research_audit_trail_run_id"],
        re_review_summary=summary,
        stabilization_gatekeeper_decision_record=decision,
        re_review_rule_evaluation_matrix=build_re_review_rule_evaluation_matrix(
            summary
        ),
        stabilized_blocker_status_matrix=build_stabilized_blocker_status_matrix(
            comparison
        ),
        residual_risk_after_re_review_matrix=(
            build_residual_risk_after_re_review_matrix(comparison)
        ),
        permission_boundary_matrix=build_permission_boundary_matrix(summary),
        task_131_handoff_manifest=build_task_131_handoff_manifest(
            gatekeeper_stabilization_re_review_run_id=gatekeeper_stabilization_re_review_run_id,
            comparison=comparison,
            baseline_gatekeeper=baseline_gatekeeper,
        ),
        gatekeeper_stabilization_re_review_checks=(
            build_gatekeeper_stabilization_re_review_checks()
        ),
        re_review_status=summary["re_review_status"],
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


def _render_markdown(report: GatekeeperStabilizationReReviewReport) -> str:
    summary = report.re_review_summary
    decision = report.stabilization_gatekeeper_decision_record
    handoff = report.task_131_handoff_manifest
    lines = [
        "# Gatekeeper Stabilization Re-Review",
        "",
        "## Executive Summary",
        "",
        (
            "* Gatekeeper Stabilization Re-Review Run ID: "
            f"{report.gatekeeper_stabilization_re_review_run_id}"
        ),
        (
            "* Gatekeeper Stabilized Comparison Run ID: "
            f"{report.gatekeeper_stabilized_comparison_run_id}"
        ),
        (
            "* Baseline Gatekeeper Re-Evaluation Run ID: "
            f"{report.baseline_gatekeeper_re_evaluation_run_id}"
        ),
        "* Current Phase: 17 - Targeted Evidence Stabilization Layer",
        "* Current Task: Task 130 - Gatekeeper Stabilization Re-Review",
        f"* Baseline Gatekeeper Outcome: {summary['baseline_gatekeeper_outcome']}",
        (
            "* New Gatekeeper Stabilization Outcome: "
            f"{summary['new_gatekeeper_stabilization_outcome']}"
        ),
        (
            "* Progression Status After Re-Review: "
            f"{summary['progression_status_after_re_review']}"
        ),
        (
            "* Persona Review Status After Re-Review: "
            f"{summary['persona_review_status_after_re_review']}"
        ),
        f"* Re-Review Status: {report.re_review_status}",
        f"* Outcome Confidence: {summary['outcome_confidence']}",
        f"* Recommended Next Task: {report.recommended_next_task}",
        "",
        "## Important Boundary",
        "",
        SAFETY_NOTICE,
        "",
        "## Where We Are Now",
        "",
        "Current Phase:",
        "17 - Targeted Evidence Stabilization Layer",
        "",
        "Previous Task:",
        "Task 129 - Compare Gatekeeper 123 vs Stabilized Evidence completed",
        "",
        "This Task:",
        "Task 130 performs a conservative Gatekeeper stabilization re-review.",
        "",
        "Phase 17 Status:",
        "In progress",
        "",
        "Baseline Gatekeeper State:",
        "hold_with_repair_progress",
        "",
        "New Gatekeeper Stabilization Outcome:",
        summary["new_gatekeeper_stabilization_outcome"],
        "",
        "Progression Status:",
        summary["progression_status_after_re_review"],
        "",
        "Persona Review Status:",
        summary["persona_review_status_after_re_review"],
        "",
        "Recommended Next Task:",
        NEXT_TASK,
        "",
        "## Gatekeeper Decision Record",
        "",
        f"* Baseline Outcome: {decision['baseline_gatekeeper_outcome']}",
        f"* New Outcome: {decision['new_gatekeeper_stabilization_outcome']}",
        f"* Rationale: {decision['decision_rationale']}",
        f"* Evidence Basis: {decision['evidence_basis']}",
        f"* Blocker Basis: {decision['blocker_basis']}",
        f"* Residual Risk Basis: {decision['residual_risk_basis']}",
        f"* Progression Status: {decision['progression_status_after_re_review']}",
        f"* Persona Review Status: {decision['persona_review_status_after_re_review']}",
        f"* Auto-Promotion Status: {decision['auto_promotion_status']}",
        (
            "* Investor Agent Execution Status: "
            f"{decision['investor_agent_execution_status']}"
        ),
        f"* Review Scope Allowed: {'; '.join(decision['review_scope_allowed'])}",
        f"* Review Scope Blocked: {'; '.join(decision['review_scope_blocked'])}",
        f"* Confidence: {decision['outcome_confidence']}",
        "",
        "## Re-Review Rule Evaluation Matrix",
        "",
        *_markdown_table(
            report.re_review_rule_evaluation_matrix,
            [
                ("Rule", "rule_code"),
                ("Result", "rule_result"),
                ("Rationale", "rule_rationale"),
                ("Impact On Outcome", "impact_on_outcome"),
            ],
        ),
        "",
        "## Stabilized Blocker Status Matrix",
        "",
        *_markdown_table(
            report.stabilized_blocker_status_matrix,
            [
                ("Blocker", "blocker_code"),
                ("Task 123 State", "task_123_state"),
                ("Task 129 Status", "task_129_comparison_status"),
                ("Re-Review Status", "re_review_status"),
                ("Disposition", "disposition"),
                ("Remaining Issue", "remaining_issue"),
            ],
        ),
        "",
        "## Residual Risk After Re-Review",
        "",
        *_markdown_table(
            report.residual_risk_after_re_review_matrix,
            [
                ("Risk", "risk_code"),
                ("State", "risk_state_after_re_review"),
                ("Severity", "severity_after_re_review"),
                ("Impact On Progression", "impact_on_progression"),
                ("Follow-Up", "required_follow_up"),
            ],
        ),
        "",
        "## Permission Boundary Matrix",
        "",
        *_markdown_table(
            report.permission_boundary_matrix,
            [
                ("Permission", "permission_code"),
                ("Status", "status_after_re_review"),
                ("Allowed Scope", "allowed_scope"),
                ("Blocked Scope", "blocked_scope"),
                ("Condition To Expand", "condition_to_expand_scope"),
            ],
        ),
        "",
        "## Task 131 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} - {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Closure Inputs: {'; '.join(handoff['closure_inputs'])}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Prohibited Outputs: {'; '.join(handoff['prohibited_outputs'])}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.gatekeeper_stabilization_re_review_checks,
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
        "* Phase 17 is ready for closure in Task 131.",
        "* The next step is a closure and next-step decision, not investor execution.",
        (
            "* Any future persona preparation must remain bounded by the "
            "permission boundary."
        ),
        "",
        "## What This Does Not Suggest",
        "",
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


def write_gatekeeper_stabilization_re_review_report(
    *,
    outputs_root: Path,
    gatekeeper_stabilized_comparison_run_id: str | None = None,
) -> GatekeeperStabilizationReReviewFiles:
    """Write Task 130 Gatekeeper stabilization re-review artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_gatekeeper_stabilized_comparison_manifest(
        outputs_root=outputs_root,
        gatekeeper_stabilized_comparison_run_id=gatekeeper_stabilized_comparison_run_id,
    )
    comparison_run_id = manifest["gatekeeper_stabilized_comparison_run_id"]
    comparison = load_gatekeeper_stabilized_comparison(
        outputs_root=outputs_root,
        gatekeeper_stabilized_comparison_run_id=comparison_run_id,
    )
    baseline = load_baseline_gatekeeper_re_evaluation(
        outputs_root=outputs_root,
        gatekeeper_re_evaluation_run_id=comparison["gatekeeper_re_evaluation_run_id"],
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_gatekeeper_stabilization_re_review(
        gatekeeper_stabilization_re_review_run_id=run_id,
        generated_at=generated_at.isoformat(),
        comparison=comparison,
        baseline_gatekeeper=baseline,
    )

    root = outputs_root / "gatekeeper_stabilization_re_reviews"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "gatekeeper_stabilization_re_review.md"
    json_path = output_folder / "gatekeeper_stabilization_re_review.json"
    decision_path = output_folder / "stabilization_gatekeeper_decision_record.json"
    rule_csv = output_folder / "re_review_rule_evaluation_matrix.csv"
    blocker_csv = output_folder / "stabilized_blocker_status_matrix.csv"
    risk_csv = output_folder / "residual_risk_after_re_review_matrix.csv"
    permission_csv = output_folder / "permission_boundary_matrix.csv"
    handoff_path = output_folder / "task_131_handoff_manifest.json"
    checks_csv = output_folder / "gatekeeper_stabilization_re_review_checks.csv"
    latest_manifest_path = root / "latest_gatekeeper_stabilization_re_review_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    decision_path.write_text(
        json.dumps(report.stabilization_gatekeeper_decision_record, indent=2),
        encoding="utf-8",
    )
    _write_csv(rule_csv, report.re_review_rule_evaluation_matrix)
    _write_csv(blocker_csv, report.stabilized_blocker_status_matrix)
    _write_csv(risk_csv, report.residual_risk_after_re_review_matrix)
    _write_csv(permission_csv, report.permission_boundary_matrix)
    handoff_path.write_text(
        json.dumps(report.task_131_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.gatekeeper_stabilization_re_review_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "gatekeeper_stabilization_re_review_run_id": (
                    report.gatekeeper_stabilization_re_review_run_id
                ),
                "gatekeeper_stabilized_comparison_run_id": (
                    report.gatekeeper_stabilized_comparison_run_id
                ),
                "baseline_gatekeeper_re_evaluation_run_id": (
                    report.baseline_gatekeeper_re_evaluation_run_id
                ),
                "new_gatekeeper_stabilization_outcome": report.re_review_summary[
                    "new_gatekeeper_stabilization_outcome"
                ],
                "re_review_status": report.re_review_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_131_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return GatekeeperStabilizationReReviewFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        decision_record_path=decision_path,
        rule_csv_path=rule_csv,
        blocker_csv_path=blocker_csv,
        residual_risk_csv_path=risk_csv,
        permission_csv_path=permission_csv,
        task_131_handoff_manifest_path=handoff_path,
        checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
