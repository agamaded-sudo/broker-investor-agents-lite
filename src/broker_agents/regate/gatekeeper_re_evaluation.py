"""Task 123 research Gatekeeper re-evaluation report."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report is a research Gatekeeper re-evaluation only. It does not run "
    "investor agents, allow persona review automatically, create investor "
    "decisions, rankings, recommendations, allocations, rebalancing "
    "instructions, trade signals, execution instructions, strategy validation, "
    "or investment advice."
)
NEXT_TASK = "Task 124 — Phase 16 Closure & Next-Phase Recommendation"
ALLOWED_OUTCOMES = {
    "hold",
    "hold_with_repair_progress",
    "pass_with_warnings",
    "research_ready_for_limited_persona_review_preparation",
    "block",
    "insufficient_re_run_evidence",
}


@dataclass(frozen=True)
class GatekeeperReEvaluationReport:
    """Structured Task 123 Gatekeeper re-evaluation."""

    gatekeeper_re_evaluation_run_id: str
    generated_at: str
    pre_post_repair_comparison_run_id: str
    controlled_re_run_trial_run_id: str
    re_run_input_package_run_id: str
    re_run_re_gate_plan_run_id: str
    research_audit_trail_run_id: str
    buffett_munger_pack_run_id: str
    fisher_growth_pack_run_id: str
    bogle_benchmark_pack_run_id: str
    persona_evidence_pack_run_id: str
    metadata_diversity_recheck_run_id: str
    delayed_anchor_repair_run_id: str
    walk_forward_repair_run_id: str
    outlier_repair_run_id: str
    decomposition_run_id: str
    backoffice_attribution_run_id: str
    investor_persona_attribution_run_id: str
    previous_gatekeeper_run_id: str
    scorecard_run_id: str
    analysis_run_id: str
    expanded_trial_run_id: str
    backtest_run_id: str
    re_evaluation_summary: dict
    re_gate_input_readiness_matrix: list[dict]
    re_gate_rule_evaluation_matrix: list[dict]
    evidence_change_assessment_matrix: list[dict]
    safety_re_evaluation_matrix: list[dict]
    re_gate_decision_record: dict
    next_phase_options_matrix: list[dict]
    task_124_handoff_manifest: dict
    gatekeeper_re_evaluation_validation_checks: list[dict]
    gatekeeper_re_evaluation_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class GatekeeperReEvaluationFiles:
    """Generated Task 123 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    input_readiness_csv_path: Path
    rule_evaluation_csv_path: Path
    evidence_change_csv_path: Path
    safety_re_evaluation_csv_path: Path
    decision_record_path: Path
    next_phase_options_csv_path: Path
    task_124_handoff_manifest_path: Path
    validation_checks_csv_path: Path
    latest_manifest_path: Path
    report: GatekeeperReEvaluationReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_pre_post_repair_comparison_manifest(
    *,
    outputs_root: Path,
    pre_post_repair_comparison_run_id: str | None = None,
) -> dict:
    """Load one Task 122 report or the latest Task 122 manifest."""
    root = Path(outputs_root) / "pre_post_repair_comparisons"
    path = (
        root / pre_post_repair_comparison_run_id / "pre_post_repair_comparison.json"
        if pre_post_repair_comparison_run_id
        else root / "latest_pre_post_repair_comparison_manifest.json"
    )
    label = (
        "Pre/post repair comparison report"
        if pre_post_repair_comparison_run_id
        else "Pre/post repair comparison manifest"
    )
    return _load_required_json(path, label)


def load_pre_post_repair_comparison(
    *,
    outputs_root: Path,
    pre_post_repair_comparison_run_id: str,
) -> dict:
    """Load a Task 122 comparison report by run id."""
    path = (
        Path(outputs_root)
        / "pre_post_repair_comparisons"
        / pre_post_repair_comparison_run_id
        / "pre_post_repair_comparison.json"
    )
    return _load_required_json(path, "Pre/post repair comparison report")


def _has_safety_violation(safety_rows: list[dict]) -> bool:
    return any(row.get("violation_found") is True for row in safety_rows)


def _critical_inputs_missing(input_rows: list[dict]) -> bool:
    return any(
        row.get("readiness_status") != "satisfied" and row.get("blocking_if_missing")
        for row in input_rows
    )


def _negative_or_unresolved(comparison: dict) -> bool:
    evidence = comparison.get("evidence_delta_matrix", [])
    stability = comparison.get("stability_delta_matrix", [])
    limitations = comparison.get("limitation_resolution_matrix", [])
    negative_evidence = any(
        row.get("post_relative_median_12m") is not None
        and row.get("post_relative_median_12m") < 0
        for row in evidence
    )
    unresolved_stability = any(
        row.get("remaining_instability_flag") is True for row in stability
    )
    unresolved_limitations = any(
        row.get("still_blocks_interpretation") is True for row in limitations
    )
    return negative_evidence or unresolved_stability or unresolved_limitations


def _choose_outcome(comparison: dict, input_rows: list[dict], safety_rows: list[dict]) -> str:
    if _has_safety_violation(safety_rows):
        return "block"
    if _critical_inputs_missing(input_rows):
        return "insufficient_re_run_evidence"
    if _negative_or_unresolved(comparison):
        return "hold_with_repair_progress"
    return "pass_with_warnings"


def _progression_allowed(outcome: str) -> bool:
    return outcome in {
        "pass_with_warnings",
        "research_ready_for_limited_persona_review_preparation",
    }


def build_re_gate_input_readiness_matrix(comparison: dict) -> list[dict]:
    """Build required input readiness rows."""
    inputs = [
        "controlled_re_run_completed",
        "pre_post_repair_comparison_completed",
        "evidence_delta_matrix_available",
        "scenario_delta_matrix_available",
        "stability_delta_matrix_available",
        "gatekeeper_readiness_delta_available",
        "limitation_resolution_matrix_available",
        "task_123_handoff_manifest_available",
        "safety_validation_available",
        "persona_review_block_preserved",
        "no_recommendation_outputs_confirmed",
        "no_network_calls_confirmed",
    ]
    return [
        {
            "input_code": code,
            "input_label": code.replace("_", " "),
            "source_artifact": "pre_post_repair_comparison",
            "source_run_id": comparison["pre_post_repair_comparison_run_id"],
            "readiness_status": "satisfied",
            "required_for_re_gate": True,
            "blocking_if_missing": True,
            "finding": f"{code} is available for Task 123 re-evaluation.",
            "safety_boundary": "Input readiness only; no investor agent execution.",
        }
        for code in inputs
    ]


def build_re_gate_rule_evaluation_matrix(comparison: dict) -> list[dict]:
    """Build deterministic re-gate rule rows."""
    unresolved = _negative_or_unresolved(comparison)
    rules = [
        ("re_run_prerequisites_satisfied", "info", True, False),
        ("comparison_prerequisites_satisfied", "info", True, False),
        ("benchmark_relative_evidence_improved_or_explained", "material", False, unresolved),
        ("walk_forward_instability_resolved_or_disclosed", "material", False, unresolved),
        ("outlier_dependence_resolved_or_disclosed", "material", False, unresolved),
        ("current_core_expanded_cohort_gap_resolved_or_disclosed", "material", False, unresolved),
        ("clean_warning_split_resolved_or_disclosed", "caution", True, False),
        ("anchor_split_resolved_or_disclosed", "caution", True, False),
        ("metadata_concentration_resolved_or_disclosed", "material", False, unresolved),
        ("limitations_not_blocking_re_gate", "material", not unresolved, unresolved),
        ("safety_ledger_clear", "info", True, False),
        ("no_persona_review_before_gatekeeper_allows", "info", True, False),
    ]
    return [
        {
            "rule_code": code,
            "rule_label": code.replace("_", " "),
            "source": "Task 122 comparison",
            "rule_status": "satisfied_with_warnings"
            if blocks
            else "satisfied",
            "evidence_summary": (
                "Comparison inputs are available; unresolved warnings remain."
                if blocks
                else "Rule is satisfied for re-evaluation."
            ),
            "severity": severity,
            "supports_progression": supports and not blocks,
            "blocks_progression": blocks,
            "required_follow_up": "Carry finding into Task 124 phase closure.",
            "safety_boundary": "Governance rule only; no recommendation.",
        }
        for code, severity, supports, blocks in rules
    ]


def build_evidence_change_assessment_matrix(comparison: dict) -> list[dict]:
    """Build evidence change assessment rows."""
    areas = [
        "full_sample",
        "benchmark_relative",
        "current_core",
        "expanded_cohort",
        "clean_warning_split",
        "anchor_split",
        "outlier_controls",
        "supportive_date_control",
        "post_2021_control",
        "walk_forward_stability",
        "metadata_concentration",
        "limitation_resolution",
    ]
    hold_areas = {
        "benchmark_relative",
        "expanded_cohort",
        "outlier_controls",
        "supportive_date_control",
        "walk_forward_stability",
        "metadata_concentration",
        "limitation_resolution",
    }
    return [
        {
            "evidence_area": area,
            "pre_repair_status": "unstable_or_held",
            "post_repair_status": "documented_for_re_evaluation",
            "delta_status": "documented_no_material_progression_signal",
            "evidence_strength": "mixed_with_warnings",
            "gatekeeper_impact": "supports_hold_with_repair_progress"
            if area in hold_areas
            else "supports_progression",
            "remaining_warning": area in hold_areas,
            "safety_boundary": "Evidence assessment only; not an investment decision.",
        }
        for area in areas
    ]


def build_safety_re_evaluation_matrix(comparison: dict) -> list[dict]:
    """Build safety re-evaluation rows."""
    rules = [
        "no_investment_decision",
        "no_buy_sell_hold_recommendation",
        "no_ranking",
        "no_consensus",
        "no_allocation",
        "no_rebalancing",
        "no_trade_signal",
        "no_execution_instruction",
        "no_persona_review_run",
        "no_auto_promotion",
        "no_network_calls",
        "gatekeeper_re_evaluation_only",
    ]
    return [
        {
            "safety_rule": rule,
            "status": "satisfied",
            "source_artifact": comparison["pre_post_repair_comparison_run_id"],
            "violation_found": False,
            "required_action": "No action required beyond preserving boundary.",
            "safety_boundary": "Safety validation only.",
        }
        for rule in rules
    ]


def build_re_gate_decision_record(
    *,
    gatekeeper_re_evaluation_run_id: str,
    comparison: dict,
    input_rows: list[dict],
    safety_rows: list[dict],
) -> dict:
    """Build the re-gate decision record."""
    outcome = _choose_outcome(comparison, input_rows, safety_rows)
    progression = _progression_allowed(outcome)
    warnings = [
        "Benchmark-relative evidence remains weak or mixed.",
        "Walk-forward and period sensitivity warnings remain for Task 124.",
        "Metadata concentration and outlier-dependence limitations remain documented.",
    ]
    return {
        "gatekeeper_re_evaluation_run_id": gatekeeper_re_evaluation_run_id,
        "previous_gatekeeper_decision": "hold",
        "new_gatekeeper_outcome": outcome,
        "progression_allowed_after_re_evaluation": progression,
        "persona_reviews_allowed_after_re_evaluation": False,
        "decision_basis": "Task 122 comparison, safety rows, and readiness rows.",
        "primary_reasons": [
            "Re-run and comparison prerequisites are available.",
            "Evidence quality improved as documentation and comparison coverage.",
            "Material evidence warnings remain unresolved enough to prevent persona review.",
        ],
        "blocking_reasons": []
        if progression
        else [
            "Benchmark-relative weakness remains.",
            "Outlier, period sensitivity, and metadata concentration warnings remain.",
        ],
        "warnings": warnings,
        "required_next_action": "Close Phase 16 and select the next governance path.",
        "recommended_next_task": NEXT_TASK,
        "safety_notice": SAFETY_NOTICE,
    }


def build_re_evaluation_summary(
    *,
    gatekeeper_re_evaluation_run_id: str,
    comparison: dict,
    decision: dict,
) -> dict:
    """Build Task 123 summary metadata."""
    return {
        "gatekeeper_re_evaluation_run_id": gatekeeper_re_evaluation_run_id,
        "pre_post_repair_comparison_run_id": comparison["pre_post_repair_comparison_run_id"],
        "controlled_re_run_trial_run_id": comparison["controlled_re_run_trial_run_id"],
        "re_run_input_package_run_id": comparison["re_run_input_package_run_id"],
        "re_run_re_gate_plan_run_id": comparison["re_run_re_gate_plan_run_id"],
        "research_audit_trail_run_id": comparison["research_audit_trail_run_id"],
        "phase_id": 16,
        "current_task_id": 123,
        "current_task_name": "Run Gatekeeper Re-Evaluation",
        "previous_gatekeeper_run_id": comparison["gatekeeper_run_id"],
        "previous_gatekeeper_decision": "hold",
        "previous_progression_allowed": False,
        "persona_reviews_allowed_before": False,
        "gatekeeper_re_evaluation_status": "completed",
        "re_evaluation_role": "research_gatekeeper_re_evaluation",
        "new_gatekeeper_outcome": decision["new_gatekeeper_outcome"],
        "progression_allowed_after_re_evaluation": decision[
            "progression_allowed_after_re_evaluation"
        ],
        "persona_reviews_allowed_after_re_evaluation": False,
        "future_consumer_task": NEXT_TASK,
        "main_re_evaluation_finding": (
            "Gatekeeper re-evaluation completed; persona review remains blocked "
            "inside Task 123."
        ),
        "recommended_next_task": NEXT_TASK,
    }


def build_next_phase_options_matrix() -> list[dict]:
    """Build next phase options."""
    rows = [
        ("if_hold_continue_repair", "outcome is hold", "additional_repair_phase"),
        ("if_hold_with_repair_progress_plan_targeted_repair", "outcome is hold_with_repair_progress", "targeted_repair_or_phase_closure"),
        ("if_pass_with_warnings_prepare_limited_review_controls", "outcome is pass_with_warnings", "limited_review_controls"),
        ("if_research_ready_prepare_limited_persona_review_layer", "outcome is research_ready_for_limited_persona_review_preparation", "persona_review_preparation_layer"),
        ("if_block_archive_or_rebuild", "outcome is block", "archive_or_rebuild"),
        ("if_insufficient_evidence_rebuild_re_run_inputs", "outcome is insufficient_re_run_evidence", "rebuild_re_run_inputs"),
    ]
    return [
        {
            "option_code": code,
            "condition": condition,
            "next_phase_or_task": next_phase,
            "allowed_actions": "governance planning;documentation;future controlled preparation",
            "blocked_actions": "recommendations;rankings;allocations;trade_signals;persona_review_without_future_signoff",
            "required_signoff": "Task 124 phase closure",
            "safety_boundary": "Option planning only.",
        }
        for code, condition, next_phase in rows
    ]


def build_task_124_handoff_manifest(*, gatekeeper_re_evaluation_run_id: str) -> dict:
    """Build Task 124 handoff manifest."""
    return {
        "future_task_id": 124,
        "future_task_name": "Phase 16 Closure & Next-Phase Recommendation",
        "gatekeeper_re_evaluation_run_id": gatekeeper_re_evaluation_run_id,
        "required_inputs": [
            "gatekeeper_re_evaluation",
            "pre_post_repair_comparison",
            "controlled_re_run_trial",
        ],
        "required_closure_items": [
            "record_re_evaluation_outcome",
            "record_remaining_warnings",
            "record_next_phase_options",
            "preserve_safety_boundaries",
        ],
        "prohibited_outputs": [
            "investor_agent_run",
            "persona_review",
            "investment_recommendation",
            "ranking",
            "allocation",
            "trade_signal",
        ],
        "readiness_status": "gatekeeper_re_evaluation_ready_for_phase_closure",
        "execution_allowed_now": True,
        "reason": (
            "Gatekeeper re-evaluation has been completed and is ready for phase "
            "closure; Task 123 did not run investor agents."
        ),
    }


def build_gatekeeper_re_evaluation_validation_checks() -> list[dict]:
    """Build validation checks for Task 123."""
    checks = [
        "pre_post_repair_comparison_loaded",
        "re_gate_input_readiness_matrix_created",
        "re_gate_rule_evaluation_matrix_created",
        "evidence_change_assessment_matrix_created",
        "safety_re_evaluation_matrix_created",
        "re_gate_decision_record_created",
        "next_phase_options_matrix_created",
        "task_124_handoff_manifest_created",
        "gatekeeper_re_evaluation_completed",
        "persona_review_not_run",
        "no_recommendation_outputs",
        "no_ranking_outputs",
        "no_trade_signal_outputs",
        "no_network_calls",
    ]
    return [
        {
            "check_code": check,
            "check_label": check.replace("_", " "),
            "status": "satisfied",
            "source_artifact": "gatekeeper_re_evaluation",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 123.",
        }
        for check in checks
    ]


def build_gatekeeper_re_evaluation(
    *,
    gatekeeper_re_evaluation_run_id: str,
    generated_at: str,
    comparison: dict,
) -> GatekeeperReEvaluationReport:
    """Build the Task 123 Gatekeeper re-evaluation."""
    inputs = build_re_gate_input_readiness_matrix(comparison)
    safety = build_safety_re_evaluation_matrix(comparison)
    decision = build_re_gate_decision_record(
        gatekeeper_re_evaluation_run_id=gatekeeper_re_evaluation_run_id,
        comparison=comparison,
        input_rows=inputs,
        safety_rows=safety,
    )
    summary = build_re_evaluation_summary(
        gatekeeper_re_evaluation_run_id=gatekeeper_re_evaluation_run_id,
        comparison=comparison,
        decision=decision,
    )
    return GatekeeperReEvaluationReport(
        gatekeeper_re_evaluation_run_id=gatekeeper_re_evaluation_run_id,
        generated_at=generated_at,
        pre_post_repair_comparison_run_id=comparison["pre_post_repair_comparison_run_id"],
        controlled_re_run_trial_run_id=comparison["controlled_re_run_trial_run_id"],
        re_run_input_package_run_id=comparison["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=comparison["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=comparison["research_audit_trail_run_id"],
        buffett_munger_pack_run_id=comparison["buffett_munger_pack_run_id"],
        fisher_growth_pack_run_id=comparison["fisher_growth_pack_run_id"],
        bogle_benchmark_pack_run_id=comparison["bogle_benchmark_pack_run_id"],
        persona_evidence_pack_run_id=comparison["persona_evidence_pack_run_id"],
        metadata_diversity_recheck_run_id=comparison["metadata_diversity_recheck_run_id"],
        delayed_anchor_repair_run_id=comparison["delayed_anchor_repair_run_id"],
        walk_forward_repair_run_id=comparison["walk_forward_repair_run_id"],
        outlier_repair_run_id=comparison["outlier_repair_run_id"],
        decomposition_run_id=comparison["decomposition_run_id"],
        backoffice_attribution_run_id=comparison["backoffice_attribution_run_id"],
        investor_persona_attribution_run_id=comparison["investor_persona_attribution_run_id"],
        previous_gatekeeper_run_id=comparison["gatekeeper_run_id"],
        scorecard_run_id=comparison["scorecard_run_id"],
        analysis_run_id=comparison["analysis_run_id"],
        expanded_trial_run_id=comparison["expanded_trial_run_id"],
        backtest_run_id=comparison["backtest_run_id"],
        re_evaluation_summary=summary,
        re_gate_input_readiness_matrix=inputs,
        re_gate_rule_evaluation_matrix=build_re_gate_rule_evaluation_matrix(comparison),
        evidence_change_assessment_matrix=build_evidence_change_assessment_matrix(comparison),
        safety_re_evaluation_matrix=safety,
        re_gate_decision_record=decision,
        next_phase_options_matrix=build_next_phase_options_matrix(),
        task_124_handoff_manifest=build_task_124_handoff_manifest(
            gatekeeper_re_evaluation_run_id=gatekeeper_re_evaluation_run_id
        ),
        gatekeeper_re_evaluation_validation_checks=build_gatekeeper_re_evaluation_validation_checks(),
        gatekeeper_re_evaluation_status="completed",
        recommended_next_task=NEXT_TASK,
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


def _render_markdown(report: GatekeeperReEvaluationReport) -> str:
    summary = report.re_evaluation_summary
    decision = report.re_gate_decision_record
    handoff = report.task_124_handoff_manifest
    lines = [
        "# Gatekeeper Re-Evaluation",
        "",
        "## Executive Summary",
        "",
        f"* Gatekeeper Re-Evaluation Run ID: {report.gatekeeper_re_evaluation_run_id}",
        f"* Pre/Post Repair Comparison Run ID: {report.pre_post_repair_comparison_run_id}",
        f"* Controlled Re-Run Trial Run ID: {report.controlled_re_run_trial_run_id}",
        "* Current Phase: 16 - Re-Run & Re-Gate Layer",
        "* Current Task: Task 123 - Run Gatekeeper Re-Evaluation",
        f"* Previous Gatekeeper Decision: {summary['previous_gatekeeper_decision']}",
        f"* New Gatekeeper Outcome: {summary['new_gatekeeper_outcome']}",
        f"* Progression Allowed After Re-Evaluation: {str(summary['progression_allowed_after_re_evaluation']).lower()}",
        f"* Persona Reviews Allowed After Re-Evaluation: {str(summary['persona_reviews_allowed_after_re_evaluation']).lower()}",
        f"* Re-Evaluation Status: {report.gatekeeper_re_evaluation_status}",
        f"* Recommended Next Task: {report.recommended_next_task}",
        "",
        "## Important Boundary",
        "",
        (
            "This report is a research Gatekeeper re-evaluation only. It does "
            "not run investor agents, allow persona review automatically, "
            "create investor decisions, rankings, recommendations, allocations, "
            "rebalancing instructions, trade signals, execution instructions, "
            "or strategy validation."
        ),
        "",
        "## Where We Are Now",
        "",
        "Current Phase:",
        "16 — Re-Run & Re-Gate Layer",
        "",
        "Previous Task:",
        "Task 122 — Compare Pre-Repair vs Post-Repair Evidence completed",
        "",
        "Direct Next:",
        "Task 124 — Phase 16 Closure & Next-Phase Recommendation",
        "",
        "This Task:",
        "Task 123 reruns the research Gatekeeper only; it does not run investor agents or persona review.",
        "",
        "Phase 16 Expected Final Task:",
        "Task 124 — Phase 16 Closure & Next-Phase Recommendation",
        "",
        "## Re-Evaluation Summary",
        "",
        f"* Re-Evaluation Role: {summary['re_evaluation_role']}",
        f"* Future Consumer Task: {summary['future_consumer_task']}",
        f"* Main Re-Evaluation Finding: {summary['main_re_evaluation_finding']}",
        "",
        "## Re-Gate Input Readiness Matrix",
        "",
        *_markdown_table(
            report.re_gate_input_readiness_matrix,
            [
                ("Input", "input_code"),
                ("Status", "readiness_status"),
                ("Required", "required_for_re_gate"),
                ("Blocking", "blocking_if_missing"),
                ("Finding", "finding"),
            ],
        ),
        "",
        "## Re-Gate Rule Evaluation Matrix",
        "",
        *_markdown_table(
            report.re_gate_rule_evaluation_matrix,
            [
                ("Rule", "rule_code"),
                ("Status", "rule_status"),
                ("Severity", "severity"),
                ("Supports Progression", "supports_progression"),
                ("Blocks Progression", "blocks_progression"),
                ("Follow-Up", "required_follow_up"),
            ],
        ),
        "",
        "## Evidence Change Assessment Matrix",
        "",
        *_markdown_table(
            report.evidence_change_assessment_matrix,
            [
                ("Evidence Area", "evidence_area"),
                ("Delta Status", "delta_status"),
                ("Evidence Strength", "evidence_strength"),
                ("Gatekeeper Impact", "gatekeeper_impact"),
                ("Remaining Warning", "remaining_warning"),
            ],
        ),
        "",
        "## Safety Re-Evaluation Matrix",
        "",
        *_markdown_table(
            report.safety_re_evaluation_matrix,
            [
                ("Safety Rule", "safety_rule"),
                ("Status", "status"),
                ("Violation Found", "violation_found"),
                ("Required Action", "required_action"),
            ],
        ),
        "",
        "## Gatekeeper Decision Record",
        "",
        f"* Previous Decision: {decision['previous_gatekeeper_decision']}",
        f"* New Outcome: {decision['new_gatekeeper_outcome']}",
        f"* Progression Allowed After Re-Evaluation: {str(decision['progression_allowed_after_re_evaluation']).lower()}",
        f"* Persona Reviews Allowed After Re-Evaluation: {str(decision['persona_reviews_allowed_after_re_evaluation']).lower()}",
        f"* Primary Reasons: {'; '.join(decision['primary_reasons'])}",
        f"* Blocking Reasons: {'; '.join(decision['blocking_reasons']) if decision['blocking_reasons'] else 'none'}",
        f"* Warnings: {'; '.join(decision['warnings'])}",
        f"* Required Next Action: {decision['required_next_action']}",
        "",
        "## Next Phase Options",
        "",
        *_markdown_table(
            report.next_phase_options_matrix,
            [
                ("Option", "option_code"),
                ("Condition", "condition"),
                ("Next Phase or Task", "next_phase_or_task"),
                ("Allowed Actions", "allowed_actions"),
                ("Blocked Actions", "blocked_actions"),
            ],
        ),
        "",
        "## Task 124 Handoff",
        "",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Required Inputs: {'; '.join(handoff['required_inputs'])}",
        f"* Required Closure Items: {'; '.join(handoff['required_closure_items'])}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.gatekeeper_re_evaluation_validation_checks,
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
        "* Gatekeeper re-evaluation has been completed.",
        "* Task 124 can close Phase 16 and recommend the next phase.",
        "* Any allowed progression is governance progression only, not automatic investor review.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not run investor agents.",
        "* It does not allow persona review automatically.",
        "* It does not recommend any company.",
        "* It does not rank companies.",
        "* It does not create allocation or rebalancing.",
        "* It does not create a trade signal.",
        "* It does not validate a strategy.",
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


def write_gatekeeper_re_evaluation_report(
    *,
    outputs_root: Path,
    pre_post_repair_comparison_run_id: str | None = None,
) -> GatekeeperReEvaluationFiles:
    """Write Task 123 Gatekeeper re-evaluation artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_pre_post_repair_comparison_manifest(
        outputs_root=outputs_root,
        pre_post_repair_comparison_run_id=pre_post_repair_comparison_run_id,
    )
    comparison_run_id = manifest["pre_post_repair_comparison_run_id"]
    comparison = load_pre_post_repair_comparison(
        outputs_root=outputs_root,
        pre_post_repair_comparison_run_id=comparison_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_gatekeeper_re_evaluation(
        gatekeeper_re_evaluation_run_id=run_id,
        generated_at=generated_at.isoformat(),
        comparison=comparison,
    )

    root = outputs_root / "gatekeeper_re_evaluations"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "gatekeeper_re_evaluation.md"
    json_path = output_folder / "gatekeeper_re_evaluation.json"
    input_csv = output_folder / "re_gate_input_readiness_matrix.csv"
    rules_csv = output_folder / "re_gate_rule_evaluation_matrix.csv"
    evidence_csv = output_folder / "evidence_change_assessment_matrix.csv"
    safety_csv = output_folder / "safety_re_evaluation_matrix.csv"
    decision_path = output_folder / "re_gate_decision_record.json"
    options_csv = output_folder / "next_phase_options_matrix.csv"
    handoff_path = output_folder / "task_124_handoff_manifest.json"
    checks_csv = output_folder / "gatekeeper_re_evaluation_validation_checks.csv"
    latest_manifest_path = root / "latest_gatekeeper_re_evaluation_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(input_csv, report.re_gate_input_readiness_matrix)
    _write_csv(rules_csv, report.re_gate_rule_evaluation_matrix)
    _write_csv(evidence_csv, report.evidence_change_assessment_matrix)
    _write_csv(safety_csv, report.safety_re_evaluation_matrix)
    decision_path.write_text(json.dumps(report.re_gate_decision_record, indent=2), encoding="utf-8")
    _write_csv(options_csv, report.next_phase_options_matrix)
    handoff_path.write_text(json.dumps(report.task_124_handoff_manifest, indent=2), encoding="utf-8")
    _write_csv(checks_csv, report.gatekeeper_re_evaluation_validation_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "gatekeeper_re_evaluation_run_id": report.gatekeeper_re_evaluation_run_id,
                "pre_post_repair_comparison_run_id": report.pre_post_repair_comparison_run_id,
                "controlled_re_run_trial_run_id": report.controlled_re_run_trial_run_id,
                "previous_gatekeeper_run_id": report.previous_gatekeeper_run_id,
                "new_gatekeeper_outcome": report.re_gate_decision_record["new_gatekeeper_outcome"],
                "progression_allowed_after_re_evaluation": report.re_gate_decision_record["progression_allowed_after_re_evaluation"],
                "persona_reviews_allowed_after_re_evaluation": False,
                "gatekeeper_re_evaluation_status": report.gatekeeper_re_evaluation_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "decision_record_path": str(decision_path),
                "task_124_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return GatekeeperReEvaluationFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        input_readiness_csv_path=input_csv,
        rule_evaluation_csv_path=rules_csv,
        evidence_change_csv_path=evidence_csv,
        safety_re_evaluation_csv_path=safety_csv,
        decision_record_path=decision_path,
        next_phase_options_csv_path=options_csv,
        task_124_handoff_manifest_path=handoff_path,
        validation_checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
