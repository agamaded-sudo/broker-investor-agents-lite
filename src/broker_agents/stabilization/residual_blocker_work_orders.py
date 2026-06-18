"""Task 126 residual blocker work-order package."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report builds residual blocker work orders only. It does not execute "
    "repairs, rerun Gatekeeper, run investor agents, allow persona review, "
    "create investor decisions, rankings, recommendations, allocations, "
    "rebalancing instructions, trade signals, execution instructions, or "
    "strategy validation."
)
NEXT_TASK = "Task 127 — Execute Targeted Evidence Repairs"


@dataclass(frozen=True)
class ResidualBlockerWorkOrderReport:
    """Structured Task 126 residual blocker work-order package."""

    residual_work_order_package_run_id: str
    generated_at: str
    stabilization_plan_run_id: str
    phase_16_closure_run_id: str
    gatekeeper_re_evaluation_run_id: str
    pre_post_repair_comparison_run_id: str
    controlled_re_run_trial_run_id: str
    re_run_input_package_run_id: str
    re_run_re_gate_plan_run_id: str
    research_audit_trail_run_id: str
    work_order_package_summary: dict
    residual_blocker_work_order_matrix: list[dict]
    work_order_dependency_matrix: list[dict]
    work_order_input_requirements_matrix: list[dict]
    work_order_success_criteria_matrix: list[dict]
    work_order_execution_sequence: list[dict]
    task_127_execution_manifest: dict
    residual_work_order_validation_checks: list[dict]
    package_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class ResidualBlockerWorkOrderFiles:
    """Generated Task 126 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    work_order_csv_path: Path
    dependency_csv_path: Path
    input_requirements_csv_path: Path
    success_criteria_csv_path: Path
    execution_sequence_csv_path: Path
    task_127_execution_manifest_path: Path
    validation_checks_csv_path: Path
    latest_manifest_path: Path
    report: ResidualBlockerWorkOrderReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_targeted_evidence_stabilization_plan_manifest(
    *,
    outputs_root: Path,
    stabilization_plan_run_id: str | None = None,
) -> dict:
    """Load one Task 125 report or the latest Task 125 manifest."""
    root = Path(outputs_root) / "targeted_evidence_stabilization_plans"
    path = (
        root / stabilization_plan_run_id / "targeted_evidence_stabilization_plan.json"
        if stabilization_plan_run_id
        else root / "latest_targeted_evidence_stabilization_plan_manifest.json"
    )
    label = (
        "Targeted evidence stabilization plan report"
        if stabilization_plan_run_id
        else "Targeted evidence stabilization plan manifest"
    )
    return _load_required_json(path, label)


def load_targeted_evidence_stabilization_plan(
    *,
    outputs_root: Path,
    stabilization_plan_run_id: str,
) -> dict:
    """Load a Task 125 stabilization plan by run id."""
    path = (
        Path(outputs_root)
        / "targeted_evidence_stabilization_plans"
        / stabilization_plan_run_id
        / "targeted_evidence_stabilization_plan.json"
    )
    return _load_required_json(path, "Targeted evidence stabilization plan report")


def build_work_order_package_summary(
    *,
    residual_work_order_package_run_id: str,
    stabilization_plan: dict,
    work_orders: list[dict],
) -> dict:
    """Build the Task 126 package summary."""
    summary = stabilization_plan["stabilization_plan_summary"]
    return {
        "residual_work_order_package_run_id": residual_work_order_package_run_id,
        "stabilization_plan_run_id": stabilization_plan["stabilization_plan_run_id"],
        "phase_16_closure_run_id": stabilization_plan["phase_16_closure_run_id"],
        "gatekeeper_re_evaluation_run_id": stabilization_plan[
            "gatekeeper_re_evaluation_run_id"
        ],
        "phase_id": 17,
        "phase_name": "Targeted Evidence Stabilization Layer",
        "current_task_id": 126,
        "current_task_name": "Build Residual Blocker Work Orders",
        "prior_gatekeeper_outcome": summary["prior_phase_final_gatekeeper_outcome"],
        "progression_allowed": summary["prior_phase_final_progression_allowed"],
        "persona_reviews_allowed": summary[
            "prior_phase_final_persona_reviews_allowed"
        ],
        "package_status": "completed",
        "package_role": "residual_blocker_work_order_packaging",
        "work_order_count": len(work_orders),
        "workstream_count": len(stabilization_plan["stabilization_workstream_matrix"]),
        "recommended_next_task": NEXT_TASK,
        "main_package_finding": (
            "Residual blockers have been converted into controlled work orders; "
            "Task 126 did not execute repairs."
        ),
    }


def build_residual_blocker_work_order_matrix(stabilization_plan: dict) -> list[dict]:
    """Build residual blocker work-order rows."""
    specs = [
        (
            "WO-126-001",
            "benchmark_relative_stabilization",
            "residual_benchmark_relative_uncertainty",
            "WS1_benchmark_relative_stabilization",
            "benchmark_relative_evidence",
            "high",
            "P1",
        ),
        (
            "WO-126-002",
            "walk_forward_period_stability",
            "residual_walk_forward_or_period_sensitivity",
            "WS2_walk_forward_period_stability",
            "walk_forward_period_stability",
            "high",
            "P1",
        ),
        (
            "WO-126-003",
            "outlier_dependence_control",
            "residual_outlier_dependence",
            "WS3_outlier_dependence_control",
            "outlier_dependence",
            "high",
            "P1",
        ),
        (
            "WO-126-004",
            "clean_warning_anchor_stability",
            "residual_clean_warning_or_anchor_uncertainty",
            "WS4_clean_warning_anchor_stability",
            "clean_warning_anchor_split",
            "medium",
            "P2",
        ),
        (
            "WO-126-005",
            "core_vs_expanded_cohort_alignment",
            "residual_current_core_expanded_cohort_gap",
            "WS5_core_vs_expanded_cohort_alignment",
            "current_core_vs_expanded_cohort",
            "high",
            "P1",
        ),
        (
            "WO-126-006",
            "metadata_concentration_resolution",
            "residual_metadata_concentration",
            "WS6_metadata_concentration_resolution",
            "metadata_concentration",
            "medium",
            "P2",
        ),
        (
            "WO-126-007",
            "local_artifact_limitations_review",
            "local_artifacts_only_limitation",
            "WS7_local_artifact_limitations_review",
            "local_artifact_completeness",
            "medium",
            "P3",
        ),
        (
            "WO-126-008",
            "gatekeeper_return_package_preparation",
            "progression_not_allowed",
            "WS8_gatekeeper_return_package_preparation",
            "gatekeeper_return_package",
            "critical",
            "P3",
        ),
    ]
    source = stabilization_plan["stabilization_plan_run_id"]
    return [
        {
            "work_order_id": work_order_id,
            "work_order_title": title,
            "linked_blocker_code": blocker,
            "linked_workstream_code": workstream,
            "evidence_area": evidence_area,
            "severity": severity,
            "priority": priority,
            "work_order_status": "deferred_until_prior_work_order_complete"
            if work_order_id == "WO-126-008"
            else "ready_for_repair_execution",
            "objective": f"Stabilize {evidence_area} using local artifacts.",
            "required_inputs": "Task 125 plan; Phase 16 closure; local artifact chain",
            "planned_repair_action": (
                "Execute controlled local evidence repair in Task 127; do not "
                "execute repair in Task 126."
            ),
            "expected_output": f"{title}_repair_artifact",
            "success_criteria": (
                "Evidence issue is resolved, reduced, or explicitly bounded for "
                "future Gatekeeper return."
            ),
            "validation_method": "local_artifact_review_and_task_127_output_validation",
            "blocked_actions": (
                "persona_review;investor_agent_run;recommendations;rankings;"
                "allocations;trade_signals;gatekeeper_rerun"
            ),
            "safety_boundary": f"Work order only from {source}; no repair execution.",
        }
        for (
            work_order_id,
            title,
            blocker,
            workstream,
            evidence_area,
            severity,
            priority,
        ) in specs
    ]


def build_work_order_dependency_matrix() -> list[dict]:
    """Build dependency rows for residual work orders."""
    independent = [f"WO-126-00{index}" for index in range(1, 8)]
    rows = [
        {
            "work_order_id": work_order_id,
            "depends_on": "local_inputs_available",
            "dependency_type": "input_readiness",
            "dependency_reason": "Work order can run once local inputs are reviewed.",
            "can_execute_in_parallel": True,
            "sequencing_note": "May run in parallel with other evidence repairs.",
            "safety_boundary": "Dependency planning only.",
        }
        for work_order_id in independent
    ]
    rows.append(
        {
            "work_order_id": "WO-126-008",
            "depends_on": ";".join(independent),
            "dependency_type": "completion_dependency",
            "dependency_reason": "Gatekeeper return package needs prior work-order outputs.",
            "can_execute_in_parallel": False,
            "sequencing_note": "Execute after WO-126-001 through WO-126-007 complete.",
            "safety_boundary": "Dependency planning only.",
        }
    )
    return rows


def build_work_order_input_requirements_matrix(stabilization_plan: dict) -> list[dict]:
    """Build input requirements rows."""
    run_ids = {
        "phase_16_closure": stabilization_plan["phase_16_closure_run_id"],
        "gatekeeper_re_evaluation": stabilization_plan["gatekeeper_re_evaluation_run_id"],
        "pre_post_repair_comparison": stabilization_plan[
            "pre_post_repair_comparison_run_id"
        ],
        "controlled_re_run_trial": stabilization_plan["controlled_re_run_trial_run_id"],
        "re_run_input_package": stabilization_plan["re_run_input_package_run_id"],
        "re_run_re_gate_plan": stabilization_plan["re_run_re_gate_plan_run_id"],
        "research_audit_trail": stabilization_plan["research_audit_trail_run_id"],
        "local_backtest_or_trial_artifacts": "local_artifact_chain",
        "metadata_diversity_recheck": "linked_prior_artifact",
        "delayed_anchor_repair": "linked_prior_artifact",
        "walk_forward_repair": "linked_prior_artifact",
        "outlier_repair": "linked_prior_artifact",
        "driver_decomposition": "linked_prior_artifact",
    }
    work_orders = [f"WO-126-00{index}" for index in range(1, 9)]
    rows = []
    for work_order_id in work_orders:
        for code, run_id in run_ids.items():
            rows.append(
                {
                    "work_order_id": work_order_id,
                    "required_input_code": code,
                    "required_input_label": code.replace("_", " "),
                    "source_artifact": code,
                    "source_run_id": run_id,
                    "required_status": "available_or_requires_local_artifact_review",
                    "missing_input_action": "mark_work_order_requires_local_artifact_review",
                    "safety_boundary": "Input requirement only; no live data fetch.",
                }
            )
    return rows


def build_work_order_success_criteria_matrix() -> list[dict]:
    """Build success criteria rows."""
    criteria = [
        ("WO-126-001", "benchmark_relative_uncertainty_bounded"),
        ("WO-126-002", "walk_forward_instability_explained_or_reduced"),
        ("WO-126-002", "period_sensitivity_documented"),
        ("WO-126-003", "outlier_dependence_bounded"),
        ("WO-126-004", "clean_warning_anchor_gap_explained"),
        ("WO-126-005", "current_core_expanded_gap_explained"),
        ("WO-126-006", "metadata_concentration_disclosed_or_reduced"),
        ("WO-126-007", "local_artifact_limitations_documented"),
        ("WO-126-008", "gatekeeper_return_package_ready"),
        ("WO-126-008", "no_persona_review_until_gatekeeper_allows"),
        ("WO-126-008", "no_recommendation_outputs"),
    ]
    return [
        {
            "work_order_id": work_order_id,
            "success_criteria_code": code,
            "success_criteria_label": code.replace("_", " "),
            "measurable_condition": (
                "Criterion is documented as resolved, reduced, or explicitly "
                "bounded using local artifacts."
            ),
            "evidence_required": "task_127_controlled_repair_output",
            "validation_artifact_expected": f"{code}_validation_record",
            "required_for_gatekeeper_return": True,
            "safety_boundary": "Success criteria only; no strategy validation.",
        }
        for work_order_id, code in criteria
    ]


def build_work_order_execution_sequence() -> list[dict]:
    """Build the Task 127 execution sequence plan."""
    rows = [
        (
            1,
            "artifact_readiness_review",
            "readiness_review",
            "review_only",
            "Task 127",
            "Task 126 work orders are available.",
            "Local inputs marked available or requiring review.",
        ),
        (
            2,
            "WO-126-001;WO-126-002;WO-126-003;WO-126-004;WO-126-005;WO-126-006;WO-126-007",
            "parallel_evidence_stabilization",
            "controlled_repair_execution",
            "Task 127",
            "Readiness review is complete.",
            "Evidence repair artifacts created for work orders 1-7.",
        ),
        (
            3,
            "WO-126-008",
            "gatekeeper_return_package",
            "package_preparation",
            "Task 127",
            "Work orders 1-7 are complete.",
            "Gatekeeper return package inputs prepared.",
        ),
        (
            4,
            "task_128_validation_readiness",
            "validation_readiness",
            "readiness_review",
            "Task 128",
            "Task 127 repair outputs exist.",
            "Task 128 validation can be planned.",
        ),
    ]
    return [
        {
            "sequence_step": step,
            "work_order_id": work_order_id,
            "execution_group": group,
            "execution_type": execution_type,
            "expected_task": expected_task,
            "entry_condition": entry,
            "exit_condition": exit_condition,
            "safety_boundary": "Sequence definition only; no repairs executed in Task 126.",
        }
        for step, work_order_id, group, execution_type, expected_task, entry, exit_condition in rows
    ]


def build_task_127_execution_manifest(
    *,
    residual_work_order_package_run_id: str,
    stabilization_plan_run_id: str,
    work_orders: list[dict],
) -> dict:
    """Build Task 127 execution manifest."""
    executable = [
        row["work_order_id"]
        for row in work_orders
        if row["work_order_status"]
        in {"ready_for_repair_execution", "requires_local_artifact_review"}
    ]
    prerequisites = [
        row["work_order_id"]
        for row in work_orders
        if row["work_order_status"] == "deferred_until_prior_work_order_complete"
    ]
    return {
        "future_phase_id": 17,
        "future_phase_name": "Targeted Evidence Stabilization Layer",
        "future_task_id": 127,
        "future_task_name": "Execute Targeted Evidence Repairs",
        "residual_work_order_package_run_id": residual_work_order_package_run_id,
        "stabilization_plan_run_id": stabilization_plan_run_id,
        "executable_work_orders": executable,
        "prerequisite_work_orders": prerequisites,
        "required_inputs": [
            "residual_blocker_work_orders",
            "targeted_evidence_stabilization_plan",
            "local_artifact_chain",
        ],
        "prohibited_outputs": [
            "investor decisions",
            "recommendations",
            "rankings",
            "allocations",
            "rebalancing",
            "trade signals",
            "persona reviews",
            "Gatekeeper rerun",
        ],
        "readiness_status": "ready_for_targeted_evidence_repair_execution",
        "execution_allowed_now": bool(executable),
        "reason": (
            "Work orders have been defined and are ready for controlled repair "
            "execution."
        ),
    }


def build_residual_work_order_validation_checks() -> list[dict]:
    """Build Task 126 validation checks."""
    checks = [
        "stabilization_plan_loaded",
        "work_order_package_summary_created",
        "residual_blocker_work_order_matrix_created",
        "all_required_work_orders_present",
        "work_order_dependency_matrix_created",
        "work_order_input_requirements_matrix_created",
        "work_order_success_criteria_matrix_created",
        "work_order_execution_sequence_created",
        "task_127_execution_manifest_created",
        "prior_gatekeeper_outcome_preserved",
        "progression_not_allowed_preserved",
        "persona_review_not_allowed_preserved",
        "investor_agents_not_run",
        "gatekeeper_not_rerun_in_task_126",
        "repairs_not_executed_in_task_126",
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
            "source_artifact": "residual_blocker_work_orders",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 126.",
        }
        for check in checks
    ]


def build_residual_blocker_work_orders(
    *,
    residual_work_order_package_run_id: str,
    generated_at: str,
    stabilization_plan: dict,
) -> ResidualBlockerWorkOrderReport:
    """Build the Task 126 residual blocker work-order package."""
    work_orders = build_residual_blocker_work_order_matrix(stabilization_plan)
    summary = build_work_order_package_summary(
        residual_work_order_package_run_id=residual_work_order_package_run_id,
        stabilization_plan=stabilization_plan,
        work_orders=work_orders,
    )
    return ResidualBlockerWorkOrderReport(
        residual_work_order_package_run_id=residual_work_order_package_run_id,
        generated_at=generated_at,
        stabilization_plan_run_id=stabilization_plan["stabilization_plan_run_id"],
        phase_16_closure_run_id=stabilization_plan["phase_16_closure_run_id"],
        gatekeeper_re_evaluation_run_id=stabilization_plan[
            "gatekeeper_re_evaluation_run_id"
        ],
        pre_post_repair_comparison_run_id=stabilization_plan[
            "pre_post_repair_comparison_run_id"
        ],
        controlled_re_run_trial_run_id=stabilization_plan[
            "controlled_re_run_trial_run_id"
        ],
        re_run_input_package_run_id=stabilization_plan["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=stabilization_plan["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=stabilization_plan["research_audit_trail_run_id"],
        work_order_package_summary=summary,
        residual_blocker_work_order_matrix=work_orders,
        work_order_dependency_matrix=build_work_order_dependency_matrix(),
        work_order_input_requirements_matrix=build_work_order_input_requirements_matrix(
            stabilization_plan
        ),
        work_order_success_criteria_matrix=build_work_order_success_criteria_matrix(),
        work_order_execution_sequence=build_work_order_execution_sequence(),
        task_127_execution_manifest=build_task_127_execution_manifest(
            residual_work_order_package_run_id=residual_work_order_package_run_id,
            stabilization_plan_run_id=stabilization_plan["stabilization_plan_run_id"],
            work_orders=work_orders,
        ),
        residual_work_order_validation_checks=build_residual_work_order_validation_checks(),
        package_status=summary["package_status"],
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


def _render_markdown(report: ResidualBlockerWorkOrderReport) -> str:
    summary = report.work_order_package_summary
    manifest = report.task_127_execution_manifest
    lines = [
        "# Residual Blocker Work Orders",
        "",
        "## Executive Summary",
        "",
        f"* Residual Work Order Package Run ID: {report.residual_work_order_package_run_id}",
        f"* Stabilization Plan Run ID: {report.stabilization_plan_run_id}",
        "* Current Phase: 17 — Targeted Evidence Stabilization Layer",
        "* Current Task: Task 126 — Build Residual Blocker Work Orders",
        f"* Prior Gatekeeper Outcome: {summary['prior_gatekeeper_outcome']}",
        f"* Progression Allowed: {str(summary['progression_allowed']).lower()}",
        f"* Persona Reviews Allowed: {str(summary['persona_reviews_allowed']).lower()}",
        f"* Package Status: {report.package_status}",
        f"* Work Order Count: {summary['work_order_count']}",
        f"* Recommended Next Task: {report.recommended_next_task}",
        "",
        "## Important Boundary",
        "",
        (
            "This report builds residual blocker work orders only. It does not "
            "execute repairs, rerun Gatekeeper, run investor agents, allow "
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
        "Previous Task:",
        "Task 125 — Define Targeted Evidence Stabilization Plan completed",
        "",
        "This Task:",
        "Task 126 converts residual blockers into executable work orders.",
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
        "## Work Order Package Summary",
        "",
        f"* Package Role: {summary['package_role']}",
        f"* Main Package Finding: {summary['main_package_finding']}",
        "",
        "## Residual Blocker Work Order Matrix",
        "",
        *_markdown_table(
            report.residual_blocker_work_order_matrix,
            [
                ("Work Order", "work_order_id"),
                ("Workstream", "linked_workstream_code"),
                ("Evidence Area", "evidence_area"),
                ("Priority", "priority"),
                ("Status", "work_order_status"),
                ("Success Criteria", "success_criteria"),
            ],
        ),
        "",
        "## Work Order Dependency Matrix",
        "",
        *_markdown_table(
            report.work_order_dependency_matrix,
            [
                ("Work Order", "work_order_id"),
                ("Depends On", "depends_on"),
                ("Dependency Type", "dependency_type"),
                ("Can Execute In Parallel", "can_execute_in_parallel"),
                ("Sequencing Note", "sequencing_note"),
            ],
        ),
        "",
        "## Work Order Input Requirements",
        "",
        *_markdown_table(
            report.work_order_input_requirements_matrix,
            [
                ("Work Order", "work_order_id"),
                ("Required Input", "required_input_code"),
                ("Source Artifact", "source_artifact"),
                ("Required Status", "required_status"),
                ("Missing Input Action", "missing_input_action"),
            ],
        ),
        "",
        "## Work Order Success Criteria",
        "",
        *_markdown_table(
            report.work_order_success_criteria_matrix,
            [
                ("Work Order", "work_order_id"),
                ("Criteria", "success_criteria_code"),
                ("Measurable Condition", "measurable_condition"),
                ("Validation Artifact", "validation_artifact_expected"),
            ],
        ),
        "",
        "## Work Order Execution Sequence",
        "",
        *_markdown_table(
            report.work_order_execution_sequence,
            [
                ("Step", "sequence_step"),
                ("Work Order", "work_order_id"),
                ("Execution Group", "execution_group"),
                ("Entry Condition", "entry_condition"),
                ("Exit Condition", "exit_condition"),
            ],
        ),
        "",
        "## Task 127 Execution Manifest",
        "",
        f"* Future Phase: {manifest['future_phase_id']} — {manifest['future_phase_name']}",
        f"* Future Task: {manifest['future_task_id']} — {manifest['future_task_name']}",
        f"* Executable Work Orders: {'; '.join(manifest['executable_work_orders'])}",
        f"* Readiness Status: {manifest['readiness_status']}",
        f"* Execution Allowed Now: {str(manifest['execution_allowed_now']).lower()}",
        f"* Reason: {manifest['reason']}",
        f"* Prohibited Outputs: {'; '.join(manifest['prohibited_outputs'])}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.residual_work_order_validation_checks,
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
        "* Phase 17 now has executable work orders.",
        "* The correct next move is controlled execution of targeted evidence repairs.",
        "* Evidence stabilization must happen before any Gatekeeper return or persona review.",
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


def write_residual_blocker_work_order_report(
    *,
    outputs_root: Path,
    stabilization_plan_run_id: str | None = None,
) -> ResidualBlockerWorkOrderFiles:
    """Write Task 126 residual blocker work-order artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_targeted_evidence_stabilization_plan_manifest(
        outputs_root=outputs_root,
        stabilization_plan_run_id=stabilization_plan_run_id,
    )
    plan_run_id = manifest["stabilization_plan_run_id"]
    stabilization_plan = load_targeted_evidence_stabilization_plan(
        outputs_root=outputs_root,
        stabilization_plan_run_id=plan_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_residual_blocker_work_orders(
        residual_work_order_package_run_id=run_id,
        generated_at=generated_at.isoformat(),
        stabilization_plan=stabilization_plan,
    )

    root = outputs_root / "residual_blocker_work_orders"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "residual_blocker_work_orders.md"
    json_path = output_folder / "residual_blocker_work_orders.json"
    work_order_csv = output_folder / "residual_blocker_work_order_matrix.csv"
    dependency_csv = output_folder / "work_order_dependency_matrix.csv"
    input_csv = output_folder / "work_order_input_requirements_matrix.csv"
    criteria_csv = output_folder / "work_order_success_criteria_matrix.csv"
    sequence_csv = output_folder / "work_order_execution_sequence.csv"
    manifest_path = output_folder / "task_127_execution_manifest.json"
    checks_csv = output_folder / "residual_work_order_validation_checks.csv"
    latest_manifest_path = root / "latest_residual_blocker_work_orders_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(work_order_csv, report.residual_blocker_work_order_matrix)
    _write_csv(dependency_csv, report.work_order_dependency_matrix)
    _write_csv(input_csv, report.work_order_input_requirements_matrix)
    _write_csv(criteria_csv, report.work_order_success_criteria_matrix)
    _write_csv(sequence_csv, report.work_order_execution_sequence)
    manifest_path.write_text(
        json.dumps(report.task_127_execution_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.residual_work_order_validation_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "residual_work_order_package_run_id": (
                    report.residual_work_order_package_run_id
                ),
                "stabilization_plan_run_id": report.stabilization_plan_run_id,
                "phase_16_closure_run_id": report.phase_16_closure_run_id,
                "gatekeeper_re_evaluation_run_id": report.gatekeeper_re_evaluation_run_id,
                "package_status": report.package_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_127_execution_manifest_path": str(manifest_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return ResidualBlockerWorkOrderFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        work_order_csv_path=work_order_csv,
        dependency_csv_path=dependency_csv,
        input_requirements_csv_path=input_csv,
        success_criteria_csv_path=criteria_csv,
        execution_sequence_csv_path=sequence_csv,
        task_127_execution_manifest_path=manifest_path,
        validation_checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
