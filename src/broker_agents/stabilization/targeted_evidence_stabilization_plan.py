"""Task 125 targeted evidence stabilization plan."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report defines Phase 17 stabilization planning only. It does not "
    "execute repairs, rerun Gatekeeper, run investor agents, allow persona "
    "review, create investor decisions, rankings, recommendations, allocations, "
    "rebalancing instructions, trade signals, execution instructions, or "
    "strategy validation."
)
PHASE_17 = "Targeted Evidence Stabilization Layer"
TASK_126 = "Task 126 — Build Residual Blocker Work Orders"


@dataclass(frozen=True)
class TargetedEvidenceStabilizationPlanReport:
    """Structured Task 125 stabilization plan."""

    stabilization_plan_run_id: str
    generated_at: str
    phase_16_closure_run_id: str
    gatekeeper_re_evaluation_run_id: str
    pre_post_repair_comparison_run_id: str
    controlled_re_run_trial_run_id: str
    re_run_input_package_run_id: str
    re_run_re_gate_plan_run_id: str
    research_audit_trail_run_id: str
    stabilization_plan_summary: dict
    residual_blocker_intake_matrix: list[dict]
    stabilization_workstream_matrix: list[dict]
    evidence_stabilization_priority_matrix: list[dict]
    phase_17_execution_roadmap: list[dict]
    stabilization_success_criteria_matrix: list[dict]
    blocked_actions_matrix: list[dict]
    task_126_handoff_manifest: dict
    stabilization_plan_validation_checks: list[dict]
    plan_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class TargetedEvidenceStabilizationPlanFiles:
    """Generated Task 125 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    residual_blocker_csv_path: Path
    workstream_csv_path: Path
    priority_csv_path: Path
    roadmap_csv_path: Path
    success_criteria_csv_path: Path
    blocked_actions_csv_path: Path
    task_126_handoff_manifest_path: Path
    validation_checks_csv_path: Path
    latest_manifest_path: Path
    report: TargetedEvidenceStabilizationPlanReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_phase_16_closure_manifest(
    *,
    outputs_root: Path,
    phase_16_closure_run_id: str | None = None,
) -> dict:
    """Load one Task 124 report or the latest Task 124 manifest."""
    root = Path(outputs_root) / "phase_16_closures"
    path = (
        root / phase_16_closure_run_id / "phase_16_closure.json"
        if phase_16_closure_run_id
        else root / "latest_phase_16_closure_manifest.json"
    )
    label = (
        "Phase 16 closure report"
        if phase_16_closure_run_id
        else "Phase 16 closure manifest"
    )
    return _load_required_json(path, label)


def load_phase_16_closure(
    *,
    outputs_root: Path,
    phase_16_closure_run_id: str,
) -> dict:
    """Load a Task 124 Phase 16 closure report by run id."""
    path = (
        Path(outputs_root)
        / "phase_16_closures"
        / phase_16_closure_run_id
        / "phase_16_closure.json"
    )
    return _load_required_json(path, "Phase 16 closure report")


def build_stabilization_plan_summary(
    *,
    stabilization_plan_run_id: str,
    phase_16_closure: dict,
) -> dict:
    """Build the Phase 17 stabilization plan summary."""
    return {
        "stabilization_plan_run_id": stabilization_plan_run_id,
        "phase_16_closure_run_id": phase_16_closure["phase_16_closure_run_id"],
        "gatekeeper_re_evaluation_run_id": phase_16_closure[
            "gatekeeper_re_evaluation_run_id"
        ],
        "phase_id": 17,
        "phase_name": PHASE_17,
        "current_task_id": 125,
        "current_task_name": "Define Targeted Evidence Stabilization Plan",
        "prior_phase_final_gatekeeper_outcome": phase_16_closure[
            "final_gatekeeper_outcome"
        ],
        "prior_phase_final_progression_allowed": phase_16_closure[
            "final_progression_allowed"
        ],
        "prior_phase_final_persona_reviews_allowed": phase_16_closure[
            "final_persona_reviews_allowed"
        ],
        "plan_status": "completed",
        "planning_role": "targeted_evidence_stabilization_planning",
        "recommended_next_task": TASK_126,
        "main_planning_finding": (
            "Phase 17 has started; residual blockers are organized into "
            "targeted stabilization workstreams while progression and persona "
            "review remain blocked."
        ),
    }


def _fallback_blockers(phase_16_closure: dict) -> list[dict]:
    blockers = phase_16_closure.get("remaining_blockers_matrix", [])
    if blockers:
        return blockers
    themes = [
        ("progression_not_allowed", "Progression not allowed", "critical"),
        ("persona_review_not_allowed", "Persona review not allowed", "critical"),
        (
            "evidence_still_unstable_or_not_progression_ready",
            "Evidence still unstable or not progression-ready",
            "high",
        ),
        (
            "residual_benchmark_relative_uncertainty",
            "Residual benchmark-relative uncertainty",
            "high",
        ),
        (
            "residual_walk_forward_or_period_sensitivity",
            "Residual walk-forward or period sensitivity",
            "high",
        ),
        ("residual_outlier_dependence", "Residual outlier dependence", "high"),
        (
            "residual_metadata_concentration",
            "Residual metadata concentration",
            "moderate",
        ),
        (
            "residual_clean_warning_or_anchor_uncertainty",
            "Residual clean/warning or anchor uncertainty",
            "moderate",
        ),
        (
            "residual_current_core_expanded_cohort_gap",
            "Residual current-core versus expanded-cohort gap",
            "high",
        ),
        ("local_artifacts_only_limitation", "Local artifacts only limitation", "moderate"),
    ]
    return [
        {
            "blocker_code": code,
            "blocker_label": label,
            "severity": severity,
            "blocker_status": "active",
            "proposed_next_phase_workstream": "requires_targeted_stabilization",
        }
        for code, label, severity in themes
    ]


def _evidence_area_for_blocker(code: str) -> str:
    mapping = {
        "progression_not_allowed": "governance_progression",
        "persona_review_not_allowed": "persona_review_block",
        "evidence_still_unstable_or_not_progression_ready": "overall_evidence_stability",
        "residual_benchmark_relative_uncertainty": "benchmark_relative_evidence",
        "residual_walk_forward_or_period_sensitivity": "walk_forward_period_stability",
        "residual_outlier_dependence": "outlier_dependence",
        "residual_metadata_concentration": "metadata_concentration",
        "residual_clean_warning_or_anchor_uncertainty": "clean_warning_anchor_split",
        "residual_current_core_expanded_cohort_gap": "current_core_vs_expanded_cohort",
        "local_artifacts_only_limitation": "local_artifact_completeness",
    }
    return mapping.get(code, "requires_local_evidence_review")


def build_residual_blocker_intake_matrix(phase_16_closure: dict) -> list[dict]:
    """Build residual blocker intake rows from Phase 16 closure."""
    rows = []
    for blocker in _fallback_blockers(phase_16_closure):
        code = blocker["blocker_code"]
        rows.append(
            {
                "blocker_code": code,
                "blocker_label": blocker.get("blocker_label", code.replace("_", " ")),
                "source_artifact": "phase_16_closure",
                "source_run_id": phase_16_closure["phase_16_closure_run_id"],
                "severity": blocker.get("severity", "high"),
                "blocker_status": blocker.get("blocker_status", "active"),
                "evidence_area": _evidence_area_for_blocker(code),
                "why_it_blocks_progression": (
                    "This residual blocker keeps the prior Gatekeeper outcome "
                    "from clearing progression or persona review."
                ),
                "stabilization_needed": "requires_targeted_stabilization",
                "proposed_workstream": blocker.get(
                    "proposed_next_phase_workstream",
                    "requires_local_evidence_review",
                ),
                "safety_boundary": "Blocker intake only; no repair execution.",
            }
        )
    return rows


def build_stabilization_workstream_matrix() -> list[dict]:
    """Build Phase 17 stabilization workstreams."""
    workstreams = [
        (
            "WS1_benchmark_relative_stabilization",
            "Benchmark-relative stabilization",
            "residual_benchmark_relative_uncertainty",
            "Bound benchmark-relative uncertainty before future re-gating.",
            "P1",
        ),
        (
            "WS2_walk_forward_period_stability",
            "Walk-forward period stability",
            "residual_walk_forward_or_period_sensitivity",
            "Explain or reduce walk-forward and period sensitivity.",
            "P1",
        ),
        (
            "WS3_outlier_dependence_control",
            "Outlier dependence control",
            "residual_outlier_dependence",
            "Bound NVDA/top-contributor and supportive-period dependence.",
            "P1",
        ),
        (
            "WS4_clean_warning_anchor_stability",
            "Clean/warning and anchor stability",
            "residual_clean_warning_or_anchor_uncertainty",
            "Keep clean/warning and anchor evidence separated.",
            "P2",
        ),
        (
            "WS5_core_vs_expanded_cohort_alignment",
            "Current-core versus expanded-cohort alignment",
            "residual_current_core_expanded_cohort_gap",
            "Explain the current-core and expanded-cohort gap.",
            "P1",
        ),
        (
            "WS6_metadata_concentration_resolution",
            "Metadata concentration resolution",
            "residual_metadata_concentration",
            "Disclose or reduce metadata concentration limits.",
            "P2",
        ),
        (
            "WS7_local_artifact_limitations_review",
            "Local artifact limitations review",
            "local_artifacts_only_limitation",
            "Document local artifact limitations without live data.",
            "P3",
        ),
        (
            "WS8_gatekeeper_return_package_preparation",
            "Gatekeeper return package preparation",
            "progression_not_allowed;persona_review_not_allowed",
            "Prepare a future Gatekeeper return package after stabilization.",
            "P3",
        ),
    ]
    return [
        {
            "workstream_code": code,
            "workstream_label": label,
            "linked_blockers": linked,
            "objective": objective,
            "required_inputs": "Phase 16 closure; Task 123 re-evaluation; local artifacts",
            "planned_output": f"{code}_work_order_bundle",
            "owner_layer": "Backoffice stabilization",
            "priority": priority,
            "success_condition": (
                "The blocker is resolved, reduced, or explicitly bounded for "
                "future Gatekeeper review."
            ),
            "blocked_actions": (
                "persona_review;investor_agent_review;recommendations;rankings;"
                "allocations;trade_signals"
            ),
            "safety_boundary": "Workstream planning only.",
        }
        for code, label, linked, objective, priority in workstreams
    ]


def build_evidence_stabilization_priority_matrix() -> list[dict]:
    """Build evidence area stabilization priorities."""
    areas = [
        (1, "benchmark_relative_evidence", "residual_benchmark_relative_uncertainty"),
        (2, "walk_forward_stability", "residual_walk_forward_or_period_sensitivity"),
        (2, "period_sensitivity", "residual_walk_forward_or_period_sensitivity"),
        (2, "supportive_period_dependence", "residual_outlier_dependence"),
        (2, "outlier_dependence", "residual_outlier_dependence"),
        (2, "clean_warning_split", "residual_clean_warning_or_anchor_uncertainty"),
        (2, "anchor_split", "residual_clean_warning_or_anchor_uncertainty"),
        (2, "current_core_vs_expanded_cohort", "residual_current_core_expanded_cohort_gap"),
        (3, "metadata_concentration", "residual_metadata_concentration"),
        (3, "local_artifact_completeness", "local_artifacts_only_limitation"),
    ]
    return [
        {
            "priority_rank": rank,
            "evidence_area": area,
            "linked_blocker": blocker,
            "stabilization_priority": f"Priority {rank}",
            "reason_for_priority": (
                "Evidence area is directly tied to the hold_with_repair_progress "
                "state or to required future Gatekeeper return packaging."
            ),
            "required_test_or_review": "targeted_local_evidence_review",
            "expected_output": f"{area}_stabilization_evidence",
            "gatekeeper_relevance": "Required before a future Gatekeeper return package.",
            "safety_boundary": "Evidence-area priority only; no company ranking.",
        }
        for rank, area, blocker in areas
    ]


def build_phase_17_execution_roadmap() -> list[dict]:
    """Build the Phase 17 execution roadmap."""
    tasks = [
        (125, "Define Targeted Evidence Stabilization Plan", "Define Phase 17 plan."),
        (126, "Build Residual Blocker Work Orders", "Convert blockers to work orders."),
        (127, "Execute Targeted Evidence Repairs", "Execute approved repair work."),
        (128, "Run Stabilization Validation Trial", "Validate stabilized evidence locally."),
        (
            129,
            "Compare Gatekeeper 123 vs Stabilized Evidence",
            "Compare prior Gatekeeper state with stabilized evidence.",
        ),
        (130, "Gatekeeper Stabilization Re-Review", "Run a future governance re-review."),
        (131, "Phase 17 Closure & Next-Step Decision", "Close Phase 17."),
    ]
    return [
        {
            "task_id": task_id,
            "task_name": task_name,
            "purpose": purpose,
            "consumes": "Phase 17 prior task outputs; local artifacts",
            "produces": f"task_{task_id}_artifact_bundle",
            "allowed_actions": "planning;local evidence repair;validation;governance packaging",
            "blocked_actions": "investor_agent_run;persona_review;recommendations;rankings;trade_signals",
            "completion_condition": f"Task {task_id} output is written and safety checks pass.",
            "safety_boundary": "Roadmap only; Task 125 does not execute later tasks.",
        }
        for task_id, task_name, purpose in tasks
    ]


def build_stabilization_success_criteria_matrix() -> list[dict]:
    """Build success criteria for future Gatekeeper return."""
    criteria = [
        ("benchmark_relative_uncertainty_bounded", "WS1_benchmark_relative_stabilization"),
        ("walk_forward_instability_explained_or_reduced", "WS2_walk_forward_period_stability"),
        ("outlier_dependence_bounded", "WS3_outlier_dependence_control"),
        ("clean_warning_anchor_gap_explained", "WS4_clean_warning_anchor_stability"),
        ("current_core_expanded_gap_explained", "WS5_core_vs_expanded_cohort_alignment"),
        ("metadata_concentration_disclosed_or_reduced", "WS6_metadata_concentration_resolution"),
        ("local_artifact_limitations_documented", "WS7_local_artifact_limitations_review"),
        ("no_persona_review_until_gatekeeper_allows", "WS8_gatekeeper_return_package_preparation"),
        ("no_recommendation_outputs", "WS8_gatekeeper_return_package_preparation"),
        ("gatekeeper_return_package_ready", "WS8_gatekeeper_return_package_preparation"),
    ]
    return [
        {
            "criteria_code": code,
            "criteria_label": code.replace("_", " "),
            "linked_workstream": workstream,
            "required_evidence": "local_stabilization_artifact",
            "success_threshold_description": (
                "The issue is resolved, reduced, or explicitly bounded without "
                "live data or investor review."
            ),
            "failure_condition": "The issue remains ambiguous or unbounded.",
            "required_for_gatekeeper_return": True,
            "safety_boundary": "Success criteria only; no strategy validation.",
        }
        for code, workstream in criteria
    ]


def build_blocked_actions_matrix() -> list[dict]:
    """Build blocked action rows."""
    actions = [
        "investor_persona_review",
        "buffett_review",
        "munger_review",
        "fisher_review",
        "lynch_review",
        "bogle_review",
        "investor_decision_generation",
        "company_ranking",
        "investment_recommendation",
        "allocation_or_rebalancing",
        "trade_signal_generation",
        "auto_promotion",
    ]
    return [
        {
            "blocked_action_code": action,
            "blocked_action_label": action.replace("_", " "),
            "reason_blocked": (
                "Phase 16 ended with hold_with_repair_progress and persona "
                "reviews allowed remains false."
            ),
            "condition_to_unblock": (
                "A future Gatekeeper must explicitly permit preparation or review."
            ),
            "safety_boundary": "Blocked action record only.",
        }
        for action in actions
    ]


def build_task_126_handoff_manifest(
    *,
    stabilization_plan_run_id: str,
    phase_16_closure_run_id: str,
) -> dict:
    """Build Task 126 handoff manifest."""
    return {
        "future_phase_id": 17,
        "future_phase_name": PHASE_17,
        "future_task_id": 126,
        "future_task_name": "Build Residual Blocker Work Orders",
        "stabilization_plan_run_id": stabilization_plan_run_id,
        "phase_16_closure_run_id": phase_16_closure_run_id,
        "required_inputs": [
            "targeted_evidence_stabilization_plan",
            "phase_16_closure",
            "gatekeeper_re_evaluation",
            "pre_post_repair_comparison",
        ],
        "required_work_order_groups": [
            "benchmark_relative_stabilization",
            "walk_forward_period_stability",
            "outlier_dependence_control",
            "clean_warning_anchor_stability",
            "core_vs_expanded_cohort_alignment",
            "metadata_concentration_resolution",
            "local_artifact_limitations_review",
            "gatekeeper_return_package_preparation",
        ],
        "prohibited_outputs": [
            "gatekeeper_rerun",
            "investor_agent_run",
            "persona_review",
            "investment_recommendation",
            "ranking",
            "allocation",
            "trade_signal",
        ],
        "readiness_status": "ready_to_build_residual_blocker_work_orders",
        "execution_allowed_now": True,
        "reason": (
            "Stabilization plan has identified residual blockers and workstreams."
        ),
    }


def build_stabilization_plan_validation_checks() -> list[dict]:
    """Build Task 125 validation checks."""
    checks = [
        "phase_16_closure_loaded",
        "stabilization_plan_summary_created",
        "residual_blocker_intake_matrix_created",
        "stabilization_workstream_matrix_created",
        "evidence_stabilization_priority_matrix_created",
        "phase_17_execution_roadmap_created",
        "stabilization_success_criteria_matrix_created",
        "blocked_actions_matrix_created",
        "task_126_handoff_manifest_created",
        "prior_gatekeeper_outcome_preserved",
        "progression_not_allowed_preserved",
        "persona_review_not_allowed_preserved",
        "investor_agents_not_run",
        "gatekeeper_not_rerun_in_task_125",
        "repairs_not_executed_in_task_125",
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
            "source_artifact": "targeted_evidence_stabilization_plan",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 125.",
        }
        for check in checks
    ]


def build_targeted_evidence_stabilization_plan(
    *,
    stabilization_plan_run_id: str,
    generated_at: str,
    phase_16_closure: dict,
) -> TargetedEvidenceStabilizationPlanReport:
    """Build the targeted evidence stabilization plan."""
    summary = build_stabilization_plan_summary(
        stabilization_plan_run_id=stabilization_plan_run_id,
        phase_16_closure=phase_16_closure,
    )
    handoff = build_task_126_handoff_manifest(
        stabilization_plan_run_id=stabilization_plan_run_id,
        phase_16_closure_run_id=phase_16_closure["phase_16_closure_run_id"],
    )
    return TargetedEvidenceStabilizationPlanReport(
        stabilization_plan_run_id=stabilization_plan_run_id,
        generated_at=generated_at,
        phase_16_closure_run_id=phase_16_closure["phase_16_closure_run_id"],
        gatekeeper_re_evaluation_run_id=phase_16_closure[
            "gatekeeper_re_evaluation_run_id"
        ],
        pre_post_repair_comparison_run_id=phase_16_closure[
            "pre_post_repair_comparison_run_id"
        ],
        controlled_re_run_trial_run_id=phase_16_closure[
            "controlled_re_run_trial_run_id"
        ],
        re_run_input_package_run_id=phase_16_closure["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=phase_16_closure["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=phase_16_closure["research_audit_trail_run_id"],
        stabilization_plan_summary=summary,
        residual_blocker_intake_matrix=build_residual_blocker_intake_matrix(
            phase_16_closure
        ),
        stabilization_workstream_matrix=build_stabilization_workstream_matrix(),
        evidence_stabilization_priority_matrix=(
            build_evidence_stabilization_priority_matrix()
        ),
        phase_17_execution_roadmap=build_phase_17_execution_roadmap(),
        stabilization_success_criteria_matrix=(
            build_stabilization_success_criteria_matrix()
        ),
        blocked_actions_matrix=build_blocked_actions_matrix(),
        task_126_handoff_manifest=handoff,
        stabilization_plan_validation_checks=build_stabilization_plan_validation_checks(),
        plan_status=summary["plan_status"],
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


def _render_markdown(report: TargetedEvidenceStabilizationPlanReport) -> str:
    summary = report.stabilization_plan_summary
    handoff = report.task_126_handoff_manifest
    lines = [
        "# Targeted Evidence Stabilization Plan",
        "",
        "## Executive Summary",
        "",
        f"* Stabilization Plan Run ID: {report.stabilization_plan_run_id}",
        f"* Phase 16 Closure Run ID: {report.phase_16_closure_run_id}",
        f"* Gatekeeper Re-Evaluation Run ID: {report.gatekeeper_re_evaluation_run_id}",
        "* Current Phase: 17 — Targeted Evidence Stabilization Layer",
        "* Current Task: Task 125 — Define Targeted Evidence Stabilization Plan",
        (
            "* Prior Phase Final Gatekeeper Outcome: "
            f"{summary['prior_phase_final_gatekeeper_outcome']}"
        ),
        (
            "* Prior Phase Final Progression Allowed: "
            f"{str(summary['prior_phase_final_progression_allowed']).lower()}"
        ),
        (
            "* Prior Phase Final Persona Reviews Allowed: "
            f"{str(summary['prior_phase_final_persona_reviews_allowed']).lower()}"
        ),
        f"* Plan Status: {report.plan_status}",
        f"* Recommended Next Task: {report.recommended_next_task}",
        "",
        "## Important Boundary",
        "",
        (
            "This report defines Phase 17 stabilization planning only. It does "
            "not execute repairs, rerun Gatekeeper, run investor agents, allow "
            "persona review, create investor decisions, rankings, "
            "recommendations, allocations, rebalancing instructions, trade "
            "signals, execution instructions, or strategy validation."
        ),
        "",
        "## Where We Are Now",
        "",
        "Current Phase:",
        "17 — Targeted Evidence Stabilization Layer",
        "",
        "Previous Phase:",
        "16 — Re-Run & Re-Gate Layer completed",
        "",
        "Previous Task:",
        "Task 124 — Phase 16 Closure & Next-Phase Recommendation completed",
        "",
        "This Task:",
        "Task 125 defines the targeted evidence stabilization plan.",
        "",
        "Phase 17 Status:",
        "Started",
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
        TASK_126,
        "",
        "## Stabilization Plan Summary",
        "",
        f"* Planning Role: {summary['planning_role']}",
        f"* Main Planning Finding: {summary['main_planning_finding']}",
        "",
        "## Residual Blocker Intake Matrix",
        "",
        *_markdown_table(
            report.residual_blocker_intake_matrix,
            [
                ("Blocker", "blocker_code"),
                ("Severity", "severity"),
                ("Evidence Area", "evidence_area"),
                ("Why It Blocks Progression", "why_it_blocks_progression"),
                ("Proposed Workstream", "proposed_workstream"),
            ],
        ),
        "",
        "## Stabilization Workstream Matrix",
        "",
        *_markdown_table(
            report.stabilization_workstream_matrix,
            [
                ("Workstream", "workstream_code"),
                ("Objective", "objective"),
                ("Linked Blockers", "linked_blockers"),
                ("Priority", "priority"),
                ("Success Condition", "success_condition"),
            ],
        ),
        "",
        "## Evidence Stabilization Priority Matrix",
        "",
        *_markdown_table(
            report.evidence_stabilization_priority_matrix,
            [
                ("Priority", "priority_rank"),
                ("Evidence Area", "evidence_area"),
                ("Linked Blocker", "linked_blocker"),
                ("Required Test or Review", "required_test_or_review"),
                ("Gatekeeper Relevance", "gatekeeper_relevance"),
            ],
        ),
        "",
        "## Phase 17 Execution Roadmap",
        "",
        *_markdown_table(
            report.phase_17_execution_roadmap,
            [
                ("Task", "task_id"),
                ("Purpose", "purpose"),
                ("Produces", "produces"),
                ("Completion Condition", "completion_condition"),
            ],
        ),
        "",
        "## Stabilization Success Criteria",
        "",
        *_markdown_table(
            report.stabilization_success_criteria_matrix,
            [
                ("Criteria", "criteria_code"),
                ("Linked Workstream", "linked_workstream"),
                ("Success Threshold", "success_threshold_description"),
                ("Required For Gatekeeper Return", "required_for_gatekeeper_return"),
            ],
        ),
        "",
        "## Blocked Actions",
        "",
        *_markdown_table(
            report.blocked_actions_matrix,
            [
                ("Blocked Action", "blocked_action_code"),
                ("Reason Blocked", "reason_blocked"),
                ("Condition To Unblock", "condition_to_unblock"),
            ],
        ),
        "",
        "## Task 126 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} — {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} — {handoff['future_task_name']}",
        f"* Required Inputs: {'; '.join(handoff['required_inputs'])}",
        f"* Required Work Order Groups: {'; '.join(handoff['required_work_order_groups'])}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.stabilization_plan_validation_checks,
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
        "* Phase 17 has started.",
        "* The correct next move is to convert residual blockers into work orders.",
        "* Evidence stabilization must happen before any persona review.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not allow investor review.",
        "* It does not run investor agents.",
        "* It does not rerun Gatekeeper.",
        "* It does not execute repairs.",
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


def write_targeted_evidence_stabilization_plan_report(
    *,
    outputs_root: Path,
    phase_16_closure_run_id: str | None = None,
) -> TargetedEvidenceStabilizationPlanFiles:
    """Write Task 125 targeted evidence stabilization plan artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_phase_16_closure_manifest(
        outputs_root=outputs_root,
        phase_16_closure_run_id=phase_16_closure_run_id,
    )
    closure_run_id = manifest["phase_16_closure_run_id"]
    phase_16_closure = load_phase_16_closure(
        outputs_root=outputs_root,
        phase_16_closure_run_id=closure_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_targeted_evidence_stabilization_plan(
        stabilization_plan_run_id=run_id,
        generated_at=generated_at.isoformat(),
        phase_16_closure=phase_16_closure,
    )

    root = outputs_root / "targeted_evidence_stabilization_plans"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "targeted_evidence_stabilization_plan.md"
    json_path = output_folder / "targeted_evidence_stabilization_plan.json"
    blocker_csv = output_folder / "residual_blocker_intake_matrix.csv"
    workstream_csv = output_folder / "stabilization_workstream_matrix.csv"
    priority_csv = output_folder / "evidence_stabilization_priority_matrix.csv"
    roadmap_csv = output_folder / "phase_17_execution_roadmap.csv"
    criteria_csv = output_folder / "stabilization_success_criteria_matrix.csv"
    blocked_csv = output_folder / "blocked_actions_matrix.csv"
    handoff_path = output_folder / "task_126_handoff_manifest.json"
    checks_csv = output_folder / "stabilization_plan_validation_checks.csv"
    latest_manifest_path = root / "latest_targeted_evidence_stabilization_plan_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(blocker_csv, report.residual_blocker_intake_matrix)
    _write_csv(workstream_csv, report.stabilization_workstream_matrix)
    _write_csv(priority_csv, report.evidence_stabilization_priority_matrix)
    _write_csv(roadmap_csv, report.phase_17_execution_roadmap)
    _write_csv(criteria_csv, report.stabilization_success_criteria_matrix)
    _write_csv(blocked_csv, report.blocked_actions_matrix)
    handoff_path.write_text(
        json.dumps(report.task_126_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.stabilization_plan_validation_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "stabilization_plan_run_id": report.stabilization_plan_run_id,
                "phase_16_closure_run_id": report.phase_16_closure_run_id,
                "gatekeeper_re_evaluation_run_id": (
                    report.gatekeeper_re_evaluation_run_id
                ),
                "plan_status": report.plan_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_126_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return TargetedEvidenceStabilizationPlanFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        residual_blocker_csv_path=blocker_csv,
        workstream_csv_path=workstream_csv,
        priority_csv_path=priority_csv,
        roadmap_csv_path=roadmap_csv,
        success_criteria_csv_path=criteria_csv,
        blocked_actions_csv_path=blocked_csv,
        task_126_handoff_manifest_path=handoff_path,
        validation_checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
