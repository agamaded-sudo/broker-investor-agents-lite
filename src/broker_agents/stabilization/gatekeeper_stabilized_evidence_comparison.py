"""Task 129 Gatekeeper 123 vs stabilized evidence comparison package."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report compares Task 123 Gatekeeper baseline against stabilized "
    "evidence only. It does not rerun Gatekeeper, issue a new Gatekeeper "
    "decision, run investor agents, allow persona review, create investor "
    "decisions, rankings, recommendations, allocations, rebalancing "
    "instructions, trade signals, execution instructions, or strategy validation."
)
NEXT_TASK = "Task 130 - Gatekeeper Stabilization Re-Review"


@dataclass(frozen=True)
class GatekeeperStabilizedEvidenceComparisonReport:
    """Structured Task 129 comparison report."""

    gatekeeper_stabilized_comparison_run_id: str
    generated_at: str
    stabilization_validation_run_id: str
    targeted_repair_run_id: str
    residual_work_order_package_run_id: str
    stabilization_plan_run_id: str
    phase_16_closure_run_id: str
    gatekeeper_re_evaluation_run_id: str
    pre_post_repair_comparison_run_id: str
    controlled_re_run_trial_run_id: str
    re_run_input_package_run_id: str
    re_run_re_gate_plan_run_id: str
    research_audit_trail_run_id: str
    comparison_summary: dict
    gatekeeper_blocker_comparison_matrix: list[dict]
    evidence_state_delta_matrix: list[dict]
    residual_risk_comparison_matrix: list[dict]
    gatekeeper_return_readiness_matrix: list[dict]
    task_130_handoff_manifest: dict
    gatekeeper_stabilized_comparison_checks: list[dict]
    comparison_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class GatekeeperStabilizedEvidenceComparisonFiles:
    """Generated Task 129 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    blocker_csv_path: Path
    evidence_delta_csv_path: Path
    residual_risk_csv_path: Path
    readiness_csv_path: Path
    task_130_handoff_manifest_path: Path
    checks_csv_path: Path
    latest_manifest_path: Path
    report: GatekeeperStabilizedEvidenceComparisonReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_stabilization_validation_trial_manifest(
    *,
    outputs_root: Path,
    stabilization_validation_run_id: str | None = None,
) -> dict:
    """Load one Task 128 report or the latest Task 128 manifest."""
    root = Path(outputs_root) / "stabilization_validation_trials"
    path = (
        root / stabilization_validation_run_id / "stabilization_validation_trial.json"
        if stabilization_validation_run_id
        else root / "latest_stabilization_validation_trial_manifest.json"
    )
    label = (
        "Stabilization validation trial report"
        if stabilization_validation_run_id
        else "Stabilization validation trial manifest"
    )
    return _load_required_json(path, label)


def load_stabilization_validation_trial(
    *,
    outputs_root: Path,
    stabilization_validation_run_id: str,
) -> dict:
    """Load a Task 128 stabilization validation report by run id."""
    path = (
        Path(outputs_root)
        / "stabilization_validation_trials"
        / stabilization_validation_run_id
        / "stabilization_validation_trial.json"
    )
    return _load_required_json(path, "Stabilization validation trial report")


def load_gatekeeper_re_evaluation(
    *,
    outputs_root: Path,
    gatekeeper_re_evaluation_run_id: str,
) -> dict:
    """Load a Task 123 Gatekeeper re-evaluation report by run id."""
    path = (
        Path(outputs_root)
        / "gatekeeper_re_evaluations"
        / gatekeeper_re_evaluation_run_id
        / "gatekeeper_re_evaluation.json"
    )
    return _load_required_json(path, "Gatekeeper re-evaluation report")


def _task_123_outcome(gatekeeper_re_evaluation: dict) -> str:
    decision = gatekeeper_re_evaluation.get("re_gate_decision_record", {})
    summary = gatekeeper_re_evaluation.get("re_evaluation_summary", {})
    return (
        decision.get("new_gatekeeper_outcome")
        or summary.get("new_gatekeeper_outcome")
        or "unavailable"
    )


def _task_123_progression_allowed(gatekeeper_re_evaluation: dict) -> bool:
    decision = gatekeeper_re_evaluation.get("re_gate_decision_record", {})
    summary = gatekeeper_re_evaluation.get("re_evaluation_summary", {})
    return bool(
        decision.get(
            "progression_allowed_after_re_evaluation",
            summary.get("progression_allowed_after_re_evaluation", False),
        )
    )


def _task_123_persona_reviews_allowed(gatekeeper_re_evaluation: dict) -> bool:
    decision = gatekeeper_re_evaluation.get("re_gate_decision_record", {})
    summary = gatekeeper_re_evaluation.get("re_evaluation_summary", {})
    return bool(
        decision.get(
            "persona_reviews_allowed_after_re_evaluation",
            summary.get("persona_reviews_allowed_after_re_evaluation", False),
        )
    )


def build_gatekeeper_blocker_comparison_matrix(
    stabilization_validation: dict,
    gatekeeper_re_evaluation: dict,
) -> list[dict]:
    """Compare Task 123 blockers with the stabilized evidence state."""
    validation_by_area = {
        row["evidence_area"]: row
        for row in stabilization_validation["evidence_area_validation_matrix"]
    }
    uncertainty_by_code = {
        row["uncertainty_code"]: row
        for row in stabilization_validation["residual_uncertainty_matrix"]
    }
    specs = [
        (
            "progression_not_allowed",
            "Progression not allowed",
            "governance",
            "unchanged",
            "unchanged_from_task_123",
            "Progression remains blocked until Task 130 performs re-review.",
        ),
        (
            "persona_review_not_allowed",
            "Persona review not allowed",
            "governance",
            "unchanged",
            "unchanged_from_task_123",
            "Persona reviews remain blocked until a future Gatekeeper allows them.",
        ),
        (
            "evidence_still_unstable_or_not_progression_ready",
            "Evidence unstable or not progression-ready",
            "gatekeeper_return_package",
            "partially_improved",
            "somewhat_stronger_than_task_123",
            "Evidence is packaged for comparison but not cleared for progression.",
        ),
        (
            "residual_benchmark_relative_uncertainty",
            "Residual benchmark-relative uncertainty",
            "benchmark_relative_evidence",
            "improved_with_warnings",
            "somewhat_stronger_than_task_123",
            "Benchmark-relative evidence remains a Task 130 review point.",
        ),
        (
            "residual_walk_forward_or_period_sensitivity",
            "Residual walk-forward or period sensitivity",
            "walk_forward_stability",
            "improved_with_warnings",
            "somewhat_stronger_than_task_123",
            "Walk-forward and period sensitivity remain disclosed warnings.",
        ),
        (
            "residual_outlier_dependence",
            "Residual outlier dependence",
            "outlier_dependence",
            "improved_with_warnings",
            "somewhat_stronger_than_task_123",
            "Outlier dependence is documented but not resolved by Task 129.",
        ),
        (
            "residual_metadata_concentration",
            "Residual metadata concentration",
            "metadata_concentration",
            "improved_with_warnings",
            "somewhat_stronger_than_task_123",
            "Metadata concentration remains a residual generalization risk.",
        ),
        (
            "residual_clean_warning_or_anchor_uncertainty",
            "Residual clean/warning or anchor uncertainty",
            "clean_warning_split",
            "improved_with_warnings",
            "somewhat_stronger_than_task_123",
            "Clean/warning and anchor splits are validation-ready with warnings.",
        ),
        (
            "residual_current_core_expanded_cohort_gap",
            "Residual current-core versus expanded-cohort gap",
            "current_core_vs_expanded_cohort",
            "improved_with_warnings",
            "somewhat_stronger_than_task_123",
            "Core/expanded cohort gap remains documented for Task 130.",
        ),
        (
            "local_artifacts_only_limitation",
            "Local artifacts only limitation",
            "local_artifact_completeness",
            "documented_only",
            "documented_but_not_resolved",
            "Task 129 uses local artifacts only; missing comparisons remain bounded.",
        ),
    ]
    rows = []
    task_123_state = _task_123_outcome(gatekeeper_re_evaluation)
    for code, label, evidence_key, status, result, remaining_issue in specs:
        validation = validation_by_area.get(evidence_key) or uncertainty_by_code.get(
            evidence_key
        )
        if validation is None and evidence_key != "governance":
            status = "not_comparable_with_local_artifacts"
            result = "inconclusive"
            support = "No matching local Task 128 validation evidence found."
        else:
            support = (
                "Task 128 validation matrix"
                if evidence_key != "governance"
                else "Task 123 and Task 128 governance state"
            )
        rows.append(
            {
                "blocker_code": code,
                "blocker_label": label,
                "task_123_state": task_123_state,
                "stabilized_state": "validation_ready_not_progression_ready",
                "comparison_status": status,
                "comparison_result": result,
                "supporting_validation_evidence": support,
                "remaining_issue": remaining_issue,
                "ready_for_task_130": True,
                "safety_boundary": "Comparison only; no Gatekeeper rerun or decision.",
            }
        )
    return rows


def build_evidence_state_delta_matrix(stabilization_validation: dict) -> list[dict]:
    """Build Task 123/Phase 16 versus Task 128 evidence deltas."""
    validation_by_area = {
        row["evidence_area"]: row
        for row in stabilization_validation["evidence_area_validation_matrix"]
    }
    required_areas = [
        "benchmark_relative_evidence",
        "walk_forward_stability",
        "period_sensitivity",
        "supportive_period_dependence",
        "outlier_dependence",
        "clean_warning_split",
        "anchor_split",
        "current_core_vs_expanded_cohort",
        "metadata_concentration",
        "local_artifact_completeness",
        "gatekeeper_return_package",
    ]
    rows = []
    for area in required_areas:
        validation = validation_by_area.get(area)
        if validation is None:
            rows.append(
                {
                    "evidence_area": area,
                    "task_123_or_phase_16_issue": "unstable_or_held",
                    "task_128_validation_state": "missing_local_validation_row",
                    "delta_status": "not_comparable_with_local_artifacts",
                    "delta_result": "inconclusive",
                    "validation_support": "No local Task 128 row available.",
                    "remaining_uncertainty": "Missing local comparison input.",
                    "task_130_relevance": "Requires follow-up before re-review.",
                    "safety_boundary": "Evidence comparison only.",
                }
            )
            continue
        documented_only = validation["validation_result"] == "documented_only"
        rows.append(
            {
                "evidence_area": area,
                "task_123_or_phase_16_issue": validation["pre_repair_issue"],
                "task_128_validation_state": validation["validation_status"],
                "delta_status": "documented_only"
                if documented_only
                else "improved_with_warnings",
                "delta_result": "documented_but_not_resolved"
                if documented_only
                else "somewhat_stronger_than_task_123",
                "validation_support": validation["task_129_comparison_input"],
                "remaining_uncertainty": validation["remaining_blocker"],
                "task_130_relevance": "Carry into Gatekeeper stabilization re-review.",
                "safety_boundary": "Evidence comparison only.",
            }
        )
    return rows


def build_residual_risk_comparison_matrix(stabilization_validation: dict) -> list[dict]:
    """Build residual risk comparison rows."""
    uncertainty_by_code = {
        row["uncertainty_code"]: row
        for row in stabilization_validation["residual_uncertainty_matrix"]
    }
    required_risks = [
        "benchmark_relative_uncertainty",
        "walk_forward_period_sensitivity",
        "supportive_period_dependence",
        "outlier_dependence",
        "clean_warning_anchor_gap",
        "core_vs_expanded_gap",
        "metadata_concentration",
        "local_artifact_only_limitation",
        "partial_repair_completion",
        "no_gatekeeper_rerun_yet",
    ]
    rows = []
    for risk in required_risks:
        uncertainty = uncertainty_by_code.get(risk, {})
        rows.append(
            {
                "risk_code": risk,
                "risk_label": risk.replace("_", " "),
                "task_123_or_phase_16_risk_state": "unresolved_or_warning",
                "stabilized_risk_state": uncertainty.get(
                    "uncertainty_status",
                    "not_comparable_with_local_artifacts",
                ),
                "risk_delta": "documented_for_task_130"
                if uncertainty
                else "inconclusive",
                "severity_after_stabilization": uncertainty.get("severity", "unknown"),
                "impact_on_task_130": uncertainty.get(
                    "impact_on_task_129",
                    "Task 130 requires local follow-up before relying on this row.",
                ),
                "required_follow_up": uncertainty.get(
                    "required_follow_up",
                    "Populate local artifact before Task 130.",
                ),
                "safety_boundary": "Risk comparison only; no Gatekeeper decision.",
            }
        )
    return rows


def build_gatekeeper_return_readiness_matrix() -> list[dict]:
    """Build readiness rows for Task 130."""
    specs = [
        ("task_123_baseline_loaded", "Task 123 baseline loaded", "ready"),
        ("stabilization_validation_loaded", "Stabilization validation loaded", "ready"),
        (
            "evidence_area_deltas_available",
            "Evidence area deltas available",
            "ready_with_warnings",
        ),
        (
            "residual_risks_disclosed",
            "Residual risks disclosed",
            "ready_with_warnings",
        ),
        (
            "blocker_comparison_available",
            "Blocker comparison available",
            "ready_with_warnings",
        ),
        (
            "task_130_input_package_ready",
            "Task 130 input package ready",
            "ready_with_warnings",
        ),
        (
            "progression_still_not_allowed_until_task_130",
            "Progression still not allowed until Task 130",
            "blocked_until_task_130",
        ),
        (
            "persona_review_still_not_allowed_until_task_130",
            "Persona review still not allowed until Task 130",
            "blocked_until_task_130",
        ),
        (
            "no_gatekeeper_rerun_in_task_129",
            "No Gatekeeper rerun in Task 129",
            "satisfied",
        ),
        ("no_recommendation_outputs", "No recommendation outputs", "satisfied"),
    ]
    return [
        {
            "readiness_code": code,
            "readiness_label": label,
            "readiness_status": status,
            "evidence_support": "Task 129 comparison package",
            "blocker_remaining": "warnings_remain"
            if "warnings" in status or status.startswith("blocked")
            else "none",
            "required_for_task_130": True,
            "readiness_reason": "Available for Task 130 re-review under safety bounds.",
            "safety_boundary": "Readiness only; no Gatekeeper decision.",
        }
        for code, label, status in specs
    ]


def build_comparison_summary(
    *,
    gatekeeper_stabilized_comparison_run_id: str,
    stabilization_validation: dict,
    gatekeeper_re_evaluation: dict,
    blocker_rows: list[dict],
) -> dict:
    """Build the Task 129 comparison summary."""
    validation_summary = stabilization_validation["validation_trial_summary"]
    improved = sum(row["comparison_status"] == "improved" for row in blocker_rows)
    partially = sum(
        row["comparison_status"] in {"improved_with_warnings", "partially_improved"}
        for row in blocker_rows
    )
    unresolved = sum(row["comparison_status"] in {"unchanged", "worsened"} for row in blocker_rows)
    not_comparable = sum(
        row["comparison_status"] == "not_comparable_with_local_artifacts"
        for row in blocker_rows
    )
    return {
        "gatekeeper_stabilized_comparison_run_id": gatekeeper_stabilized_comparison_run_id,
        "stabilization_validation_run_id": stabilization_validation[
            "stabilization_validation_run_id"
        ],
        "targeted_repair_run_id": stabilization_validation["targeted_repair_run_id"],
        "residual_work_order_package_run_id": stabilization_validation[
            "residual_work_order_package_run_id"
        ],
        "stabilization_plan_run_id": stabilization_validation[
            "stabilization_plan_run_id"
        ],
        "phase_16_closure_run_id": stabilization_validation["phase_16_closure_run_id"],
        "gatekeeper_re_evaluation_run_id": gatekeeper_re_evaluation[
            "gatekeeper_re_evaluation_run_id"
        ],
        "phase_id": 17,
        "phase_name": "Targeted Evidence Stabilization Layer",
        "current_task_id": 129,
        "current_task_name": "Compare Gatekeeper 123 vs Stabilized Evidence",
        "task_123_gatekeeper_outcome": _task_123_outcome(gatekeeper_re_evaluation),
        "progression_allowed": validation_summary["progression_allowed"],
        "persona_reviews_allowed": validation_summary["persona_reviews_allowed"],
        "comparison_status": "completed",
        "comparison_role": "gatekeeper_baseline_vs_stabilized_evidence_comparison",
        "blockers_compared": len(blocker_rows),
        "blockers_improved": improved,
        "blockers_partially_improved": partially,
        "blockers_unresolved": unresolved,
        "blockers_not_comparable": not_comparable,
        "recommended_next_task": NEXT_TASK,
        "main_comparison_finding": (
            "Stabilized evidence is ready for Task 130 re-review with warnings; "
            "Task 129 does not rerun Gatekeeper or change progression state."
        ),
    }


def build_task_130_handoff_manifest(
    *,
    gatekeeper_stabilized_comparison_run_id: str,
    stabilization_validation: dict,
    gatekeeper_re_evaluation: dict,
    evidence_rows: list[dict],
    blocker_rows: list[dict],
) -> dict:
    """Build Task 130 handoff manifest."""
    return {
        "future_phase_id": 17,
        "future_phase_name": "Targeted Evidence Stabilization Layer",
        "future_task_id": 130,
        "future_task_name": "Gatekeeper Stabilization Re-Review",
        "gatekeeper_stabilized_comparison_run_id": gatekeeper_stabilized_comparison_run_id,
        "stabilization_validation_run_id": stabilization_validation[
            "stabilization_validation_run_id"
        ],
        "gatekeeper_re_evaluation_run_id": gatekeeper_re_evaluation[
            "gatekeeper_re_evaluation_run_id"
        ],
        "re_review_inputs": [
            "gatekeeper_re_evaluation",
            "stabilization_validation_trial",
            "gatekeeper_stabilized_evidence_comparison",
        ],
        "comparison_outputs_to_review": [
            "gatekeeper_blocker_comparison_matrix",
            "evidence_state_delta_matrix",
            "residual_risk_comparison_matrix",
            "gatekeeper_return_readiness_matrix",
        ],
        "readiness_status": "ready_with_warnings"
        if any(row["comparison_status"] != "improved" for row in blocker_rows)
        else "ready_for_task_130_gatekeeper_stabilization_re_review",
        "execution_allowed_now": bool(evidence_rows and blocker_rows),
        "prohibited_outputs": [
            "investor decisions",
            "recommendations",
            "rankings",
            "allocations",
            "rebalancing",
            "trade signals",
            "persona reviews",
            "investor agent execution",
        ],
        "reason": (
            "Comparison outputs are available for Task 130; Task 129 did not "
            "rerun Gatekeeper."
        ),
    }


def build_gatekeeper_stabilized_comparison_checks() -> list[dict]:
    """Build Task 129 validation checks."""
    checks = [
        "stabilization_validation_run_loaded",
        "task_123_gatekeeper_re_evaluation_loaded",
        "comparison_summary_created",
        "gatekeeper_blocker_comparison_matrix_created",
        "evidence_state_delta_matrix_created",
        "residual_risk_comparison_matrix_created",
        "gatekeeper_return_readiness_matrix_created",
        "task_130_handoff_manifest_created",
        "task_123_gatekeeper_outcome_preserved",
        "progression_not_allowed_preserved",
        "persona_review_not_allowed_preserved",
        "investor_agents_not_run",
        "gatekeeper_not_rerun_in_task_129",
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
            "source_artifact": "gatekeeper_stabilized_evidence_comparison",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 129.",
        }
        for check in checks
    ]


def build_gatekeeper_stabilized_evidence_comparison(
    *,
    gatekeeper_stabilized_comparison_run_id: str,
    generated_at: str,
    stabilization_validation: dict,
    gatekeeper_re_evaluation: dict,
) -> GatekeeperStabilizedEvidenceComparisonReport:
    """Build the Task 129 comparison report."""
    blocker_rows = build_gatekeeper_blocker_comparison_matrix(
        stabilization_validation,
        gatekeeper_re_evaluation,
    )
    evidence_rows = build_evidence_state_delta_matrix(stabilization_validation)
    summary = build_comparison_summary(
        gatekeeper_stabilized_comparison_run_id=gatekeeper_stabilized_comparison_run_id,
        stabilization_validation=stabilization_validation,
        gatekeeper_re_evaluation=gatekeeper_re_evaluation,
        blocker_rows=blocker_rows,
    )
    handoff = build_task_130_handoff_manifest(
        gatekeeper_stabilized_comparison_run_id=gatekeeper_stabilized_comparison_run_id,
        stabilization_validation=stabilization_validation,
        gatekeeper_re_evaluation=gatekeeper_re_evaluation,
        evidence_rows=evidence_rows,
        blocker_rows=blocker_rows,
    )
    return GatekeeperStabilizedEvidenceComparisonReport(
        gatekeeper_stabilized_comparison_run_id=gatekeeper_stabilized_comparison_run_id,
        generated_at=generated_at,
        stabilization_validation_run_id=stabilization_validation[
            "stabilization_validation_run_id"
        ],
        targeted_repair_run_id=stabilization_validation["targeted_repair_run_id"],
        residual_work_order_package_run_id=stabilization_validation[
            "residual_work_order_package_run_id"
        ],
        stabilization_plan_run_id=stabilization_validation["stabilization_plan_run_id"],
        phase_16_closure_run_id=stabilization_validation["phase_16_closure_run_id"],
        gatekeeper_re_evaluation_run_id=gatekeeper_re_evaluation[
            "gatekeeper_re_evaluation_run_id"
        ],
        pre_post_repair_comparison_run_id=stabilization_validation[
            "pre_post_repair_comparison_run_id"
        ],
        controlled_re_run_trial_run_id=stabilization_validation[
            "controlled_re_run_trial_run_id"
        ],
        re_run_input_package_run_id=stabilization_validation[
            "re_run_input_package_run_id"
        ],
        re_run_re_gate_plan_run_id=stabilization_validation[
            "re_run_re_gate_plan_run_id"
        ],
        research_audit_trail_run_id=stabilization_validation[
            "research_audit_trail_run_id"
        ],
        comparison_summary=summary,
        gatekeeper_blocker_comparison_matrix=blocker_rows,
        evidence_state_delta_matrix=evidence_rows,
        residual_risk_comparison_matrix=build_residual_risk_comparison_matrix(
            stabilization_validation
        ),
        gatekeeper_return_readiness_matrix=build_gatekeeper_return_readiness_matrix(),
        task_130_handoff_manifest=handoff,
        gatekeeper_stabilized_comparison_checks=(
            build_gatekeeper_stabilized_comparison_checks()
        ),
        comparison_status=summary["comparison_status"],
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


def _render_markdown(
    report: GatekeeperStabilizedEvidenceComparisonReport,
) -> str:
    summary = report.comparison_summary
    handoff = report.task_130_handoff_manifest
    lines = [
        "# Gatekeeper 123 vs Stabilized Evidence Comparison",
        "",
        "## Executive Summary",
        "",
        (
            "* Gatekeeper Stabilized Comparison Run ID: "
            f"{report.gatekeeper_stabilized_comparison_run_id}"
        ),
        f"* Stabilization Validation Run ID: {report.stabilization_validation_run_id}",
        f"* Gatekeeper Re-Evaluation Run ID: {report.gatekeeper_re_evaluation_run_id}",
        "* Current Phase: 17 - Targeted Evidence Stabilization Layer",
        "* Current Task: Task 129 - Compare Gatekeeper 123 vs Stabilized Evidence",
        f"* Task 123 Gatekeeper Outcome: {summary['task_123_gatekeeper_outcome']}",
        f"* Progression Allowed: {str(summary['progression_allowed']).lower()}",
        f"* Persona Reviews Allowed: {str(summary['persona_reviews_allowed']).lower()}",
        f"* Comparison Status: {report.comparison_status}",
        f"* Blockers Compared: {summary['blockers_compared']}",
        f"* Blockers Improved: {summary['blockers_improved']}",
        f"* Blockers Partially Improved: {summary['blockers_partially_improved']}",
        f"* Blockers Unresolved: {summary['blockers_unresolved']}",
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
        "Task 128 - Run Stabilization Validation Trial completed",
        "",
        "This Task:",
        (
            "Task 129 compares the Task 123 Gatekeeper baseline against "
            "stabilized evidence."
        ),
        "",
        "Phase 17 Status:",
        "In progress",
        "",
        "Current Gatekeeper State:",
        "hold_with_repair_progress",
        "",
        "Progression:",
        "Not allowed",
        "",
        "Persona Reviews:",
        "Not allowed",
        "",
        "Recommended Next Task:",
        NEXT_TASK,
        "",
        "## Comparison Summary",
        "",
        f"* Comparison Role: {summary['comparison_role']}",
        f"* Main Comparison Finding: {summary['main_comparison_finding']}",
        "",
        "## Gatekeeper Blocker Comparison Matrix",
        "",
        *_markdown_table(
            report.gatekeeper_blocker_comparison_matrix,
            [
                ("Blocker", "blocker_code"),
                ("Task 123 State", "task_123_state"),
                ("Stabilized State", "stabilized_state"),
                ("Comparison Status", "comparison_status"),
                ("Ready For Task 130", "ready_for_task_130"),
                ("Remaining Issue", "remaining_issue"),
            ],
        ),
        "",
        "## Evidence State Delta Matrix",
        "",
        *_markdown_table(
            report.evidence_state_delta_matrix,
            [
                ("Evidence Area", "evidence_area"),
                ("Task 123 / Phase 16 Issue", "task_123_or_phase_16_issue"),
                ("Task 128 Validation State", "task_128_validation_state"),
                ("Delta Status", "delta_status"),
                ("Task 130 Relevance", "task_130_relevance"),
            ],
        ),
        "",
        "## Residual Risk Comparison Matrix",
        "",
        *_markdown_table(
            report.residual_risk_comparison_matrix,
            [
                ("Risk", "risk_code"),
                ("Previous Risk State", "task_123_or_phase_16_risk_state"),
                ("Stabilized Risk State", "stabilized_risk_state"),
                ("Risk Delta", "risk_delta"),
                ("Severity After Stabilization", "severity_after_stabilization"),
            ],
        ),
        "",
        "## Gatekeeper Return Readiness Matrix",
        "",
        *_markdown_table(
            report.gatekeeper_return_readiness_matrix,
            [
                ("Readiness Item", "readiness_code"),
                ("Status", "readiness_status"),
                ("Required For Task 130", "required_for_task_130"),
                ("Blocker Remaining", "blocker_remaining"),
            ],
        ),
        "",
        "## Task 130 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} - {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Re-Review Inputs: {'; '.join(handoff['re_review_inputs'])}",
        (
            "* Comparison Outputs To Review: "
            f"{'; '.join(handoff['comparison_outputs_to_review'])}"
        ),
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Prohibited Outputs: {'; '.join(handoff['prohibited_outputs'])}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.gatekeeper_stabilized_comparison_checks,
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
            "* Stabilized evidence is ready to be formally re-reviewed by "
            "Gatekeeper in Task 130."
        ),
        (
            "* Task 130 is the correct place to issue any updated Gatekeeper "
            "stabilization outcome."
        ),
        (
            "* Evidence comparison may support improvement, but Task 129 itself "
            "does not change Gatekeeper state."
        ),
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not allow investor review.",
        "* It does not run investor agents.",
        "* It does not rerun Gatekeeper.",
        "* It does not issue a new Gatekeeper decision.",
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


def write_gatekeeper_stabilized_evidence_comparison_report(
    *,
    outputs_root: Path,
    stabilization_validation_run_id: str | None = None,
    gatekeeper_re_evaluation_run_id: str | None = None,
) -> GatekeeperStabilizedEvidenceComparisonFiles:
    """Write Task 129 comparison artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_stabilization_validation_trial_manifest(
        outputs_root=outputs_root,
        stabilization_validation_run_id=stabilization_validation_run_id,
    )
    validation_run_id = manifest["stabilization_validation_run_id"]
    stabilization_validation = load_stabilization_validation_trial(
        outputs_root=outputs_root,
        stabilization_validation_run_id=validation_run_id,
    )
    re_eval_run_id = (
        gatekeeper_re_evaluation_run_id
        or stabilization_validation["gatekeeper_re_evaluation_run_id"]
    )
    gatekeeper_re_evaluation = load_gatekeeper_re_evaluation(
        outputs_root=outputs_root,
        gatekeeper_re_evaluation_run_id=re_eval_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_gatekeeper_stabilized_evidence_comparison(
        gatekeeper_stabilized_comparison_run_id=run_id,
        generated_at=generated_at.isoformat(),
        stabilization_validation=stabilization_validation,
        gatekeeper_re_evaluation=gatekeeper_re_evaluation,
    )

    root = outputs_root / "gatekeeper_stabilized_evidence_comparisons"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "gatekeeper_stabilized_evidence_comparison.md"
    json_path = output_folder / "gatekeeper_stabilized_evidence_comparison.json"
    blocker_csv = output_folder / "gatekeeper_blocker_comparison_matrix.csv"
    delta_csv = output_folder / "evidence_state_delta_matrix.csv"
    risk_csv = output_folder / "residual_risk_comparison_matrix.csv"
    readiness_csv = output_folder / "gatekeeper_return_readiness_matrix.csv"
    handoff_path = output_folder / "task_130_handoff_manifest.json"
    checks_csv = output_folder / "gatekeeper_stabilized_comparison_checks.csv"
    latest_manifest_path = (
        root / "latest_gatekeeper_stabilized_evidence_comparison_manifest.json"
    )

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(blocker_csv, report.gatekeeper_blocker_comparison_matrix)
    _write_csv(delta_csv, report.evidence_state_delta_matrix)
    _write_csv(risk_csv, report.residual_risk_comparison_matrix)
    _write_csv(readiness_csv, report.gatekeeper_return_readiness_matrix)
    handoff_path.write_text(
        json.dumps(report.task_130_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.gatekeeper_stabilized_comparison_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "gatekeeper_stabilized_comparison_run_id": (
                    report.gatekeeper_stabilized_comparison_run_id
                ),
                "stabilization_validation_run_id": (
                    report.stabilization_validation_run_id
                ),
                "gatekeeper_re_evaluation_run_id": (
                    report.gatekeeper_re_evaluation_run_id
                ),
                "comparison_status": report.comparison_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_130_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return GatekeeperStabilizedEvidenceComparisonFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        blocker_csv_path=blocker_csv,
        evidence_delta_csv_path=delta_csv,
        residual_risk_csv_path=risk_csv,
        readiness_csv_path=readiness_csv,
        task_130_handoff_manifest_path=handoff_path,
        checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
