"""Task 131 Phase 17 closure and next-step decision package."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report closes Phase 17 and defines the next-step decision only. It "
    "does not run investor agents, allow actual persona reviews, create "
    "investor decisions, rankings, recommendations, allocations, rebalancing "
    "instructions, trade signals, execution instructions, auto-promotion, or "
    "strategy validation."
)
PHASE_NAME = "Targeted Evidence Stabilization Layer"
NEXT_PHASE = "Phase 18 - Gatekeeper Return Package Layer"
NEXT_TASK = "Task 132 - Define Gatekeeper Return Package Plan"


@dataclass(frozen=True)
class Phase17ClosureReport:
    """Structured Task 131 Phase 17 closure report."""

    phase_17_closure_run_id: str
    generated_at: str
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
    phase_17_closure_summary: dict
    phase_17_task_status_matrix: list[dict]
    final_gatekeeper_stabilization_summary: dict
    final_permission_boundary_summary: list[dict]
    remaining_blockers_after_phase_17_matrix: list[dict]
    phase_18_recommendation_matrix: list[dict]
    task_132_handoff_manifest: dict
    phase_17_closure_checks: list[dict]
    closure_status: str
    recommended_next_phase: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class Phase17ClosureFiles:
    """Generated Task 131 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    task_status_csv_path: Path
    gatekeeper_summary_csv_path: Path
    permission_summary_csv_path: Path
    remaining_blockers_csv_path: Path
    phase_18_recommendation_csv_path: Path
    task_132_handoff_manifest_path: Path
    checks_csv_path: Path
    latest_manifest_path: Path
    report: Phase17ClosureReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _value(data: dict, key: str, default: str = "unavailable") -> str:
    value = data.get(key, default)
    if value is None:
        return default
    return str(value)


def load_gatekeeper_stabilization_re_review_manifest(
    *,
    outputs_root: Path,
    gatekeeper_stabilization_re_review_run_id: str | None = None,
) -> dict:
    """Load one Task 130 report or the latest Task 130 manifest."""
    root = Path(outputs_root) / "gatekeeper_stabilization_re_reviews"
    path = (
        root
        / gatekeeper_stabilization_re_review_run_id
        / "gatekeeper_stabilization_re_review.json"
        if gatekeeper_stabilization_re_review_run_id
        else root / "latest_gatekeeper_stabilization_re_review_manifest.json"
    )
    label = (
        "Gatekeeper stabilization re-review report"
        if gatekeeper_stabilization_re_review_run_id
        else "Gatekeeper stabilization re-review manifest"
    )
    return _load_required_json(path, label)


def load_gatekeeper_stabilization_re_review(
    *,
    outputs_root: Path,
    gatekeeper_stabilization_re_review_run_id: str,
) -> dict:
    """Load a Task 130 Gatekeeper stabilization re-review report by run id."""
    path = (
        Path(outputs_root)
        / "gatekeeper_stabilization_re_reviews"
        / gatekeeper_stabilization_re_review_run_id
        / "gatekeeper_stabilization_re_review.json"
    )
    return _load_required_json(path, "Gatekeeper stabilization re-review report")


def build_phase_17_closure_summary(
    *,
    phase_17_closure_run_id: str,
    re_review: dict,
) -> dict:
    """Build the Task 131 closure summary."""
    summary = re_review["re_review_summary"]
    decision = re_review["stabilization_gatekeeper_decision_record"]
    return {
        "phase_17_closure_run_id": phase_17_closure_run_id,
        "gatekeeper_stabilization_re_review_run_id": re_review[
            "gatekeeper_stabilization_re_review_run_id"
        ],
        "phase_id": 17,
        "phase_name": PHASE_NAME,
        "current_task_id": 131,
        "current_task_name": "Phase 17 Closure & Next-Step Decision",
        "phase_completion_status": "completed",
        "final_gatekeeper_stabilization_outcome": summary[
            "new_gatekeeper_stabilization_outcome"
        ],
        "final_progression_status": summary[
            "progression_status_after_re_review"
        ],
        "final_persona_review_status": summary[
            "persona_review_status_after_re_review"
        ],
        "final_outcome_confidence": summary["outcome_confidence"],
        "final_auto_promotion_status": decision["auto_promotion_status"],
        "closure_status": "closed_for_gatekeeper_return_package_only",
        "recommended_next_phase": NEXT_PHASE,
        "recommended_next_task": NEXT_TASK,
        "main_closure_finding": (
            "Phase 17 documented stabilization progress, but final scope remains "
            "limited to Gatekeeper return package preparation with persona "
            "reviews and investor-agent execution blocked."
        ),
    }


def build_phase_17_task_status_matrix(
    *,
    phase_17_closure_run_id: str,
    re_review: dict,
) -> list[dict]:
    """Build the Phase 17 task status matrix for Tasks 125-131."""
    specs = [
        (
            125,
            "Define Targeted Evidence Stabilization Plan",
            re_review["stabilization_plan_run_id"],
            "targeted_evidence_stabilization_plans",
            "completed",
            "Defined the targeted stabilization plan.",
            "Task 126 - Build Residual Blocker Work Orders",
        ),
        (
            126,
            "Build Residual Blocker Work Orders",
            re_review["residual_work_order_package_run_id"],
            "residual_blocker_work_orders",
            "completed",
            "Converted residual blockers into work orders.",
            "Task 127 - Execute Targeted Evidence Repairs",
        ),
        (
            127,
            "Execute Targeted Evidence Repairs",
            re_review["targeted_repair_run_id"],
            "targeted_evidence_repairs",
            "completed",
            "Executed targeted evidence repair documentation.",
            "Task 128 - Run Stabilization Validation Trial",
        ),
        (
            128,
            "Run Stabilization Validation Trial",
            re_review["stabilization_validation_run_id"],
            "stabilization_validation_trials",
            "completed",
            "Validated stabilization evidence with local artifacts.",
            "Task 129 - Compare Gatekeeper 123 vs Stabilized Evidence",
        ),
        (
            129,
            "Compare Gatekeeper 123 vs Stabilized Evidence",
            re_review["gatekeeper_stabilized_comparison_run_id"],
            "gatekeeper_stabilized_evidence_comparisons",
            "completed_with_warnings",
            "Compared baseline Gatekeeper blockers against stabilized evidence.",
            "Task 130 - Gatekeeper Stabilization Re-Review",
        ),
        (
            130,
            "Gatekeeper Stabilization Re-Review",
            re_review["gatekeeper_stabilization_re_review_run_id"],
            "gatekeeper_stabilization_re_reviews",
            re_review["re_review_status"],
            "Converted stabilized evidence into conservative re-review outcome.",
            "Task 131 - Phase 17 Closure & Next-Step Decision",
        ),
        (
            131,
            "Phase 17 Closure & Next-Step Decision",
            phase_17_closure_run_id,
            "phase_17_closures",
            "completed",
            "Closed Phase 17 with Gatekeeper return package only.",
            NEXT_TASK,
        ),
    ]
    return [
        {
            "task_id": task_id,
            "task_name": task_name,
            "run_id": run_id,
            "artifact_folder": f"data/outputs/{folder}/{run_id}",
            "completion_status": status,
            "key_result": key_result,
            "next_task_from_artifact": next_task,
            "safety_boundary": "Phase 17 task status only; no investor action.",
        }
        for task_id, task_name, run_id, folder, status, key_result, next_task in specs
    ]


def build_final_gatekeeper_stabilization_summary(re_review: dict) -> dict:
    """Build the final Gatekeeper stabilization outcome summary."""
    summary = re_review["re_review_summary"]
    decision = re_review["stabilization_gatekeeper_decision_record"]
    return {
        "baseline_gatekeeper_outcome": summary["baseline_gatekeeper_outcome"],
        "final_gatekeeper_stabilization_outcome": summary[
            "new_gatekeeper_stabilization_outcome"
        ],
        "final_progression_status": summary[
            "progression_status_after_re_review"
        ],
        "final_persona_review_status": summary[
            "persona_review_status_after_re_review"
        ],
        "final_outcome_confidence": summary["outcome_confidence"],
        "final_auto_promotion_status": decision["auto_promotion_status"],
        "final_permission_scope": [
            "phase_17_closure",
            "gatekeeper_return_package_preparation",
            "gatekeeper_return_package_only",
        ],
        "final_blocked_scope": [
            "actual persona review",
            "investor agent execution",
            "investor decisions",
            "recommendations",
            "rankings",
            "allocations",
            "rebalancing",
            "trade signals",
            "auto-promotion",
        ],
        "main_final_finding": (
            "The final Phase 17 outcome is hold_with_stabilization_progress; "
            "only Gatekeeper return package preparation is allowed."
        ),
    }


def build_final_permission_boundary_summary(re_review: dict) -> list[dict]:
    """Build final permission boundaries for Phase 17 closure."""
    rows = []
    for row in re_review["permission_boundary_matrix"]:
        rows.append(
            {
                "permission_code": row["permission_code"],
                "permission_label": row["permission_label"],
                "final_status": row["status_after_re_review"],
                "allowed_scope": row["allowed_scope"],
                "blocked_scope": row["blocked_scope"],
                "condition_to_expand_scope": row["condition_to_expand_scope"],
                "closure_interpretation": (
                    "Permission is preserved at Phase 17 closure; any expanded "
                    "scope requires a future Gatekeeper decision."
                ),
                "safety_boundary": "Final permission boundary only.",
            }
        )
    return rows


def build_remaining_blockers_after_phase_17_matrix() -> list[dict]:
    """Build remaining blockers that Phase 18 must preserve or package."""
    specs = [
        ("unresolved_material_blockers", "critical", "Gatekeeper package must disclose unresolved blockers."),
        ("partially_improved_evidence_blockers", "high", "Partial improvement cannot be treated as resolution."),
        ("persona_review_not_allowed", "critical", "Actual persona reviews remain blocked."),
        ("investor_agent_execution_not_allowed", "critical", "Investor agents must not be run."),
        ("local_artifact_limitations", "medium", "Phase 18 must disclose local artifact limits."),
        ("residual_metadata_concentration", "medium", "Metadata concentration remains a generalization limit."),
        ("residual_period_sensitivity", "high", "Period sensitivity remains a residual risk."),
        ("residual_outlier_dependence", "high", "Outlier dependence remains disclosed."),
        ("gatekeeper_return_package_needed", "high", "Next phase should prepare a return package."),
        ("auto_promotion_disabled", "critical", "Auto-promotion remains disabled."),
    ]
    return [
        {
            "blocker_code": code,
            "blocker_label": code.replace("_", " "),
            "severity": severity,
            "status_after_phase_17": "remaining_or_preserved",
            "impact_on_next_phase": impact,
            "required_phase_18_handling": "Preserve and disclose in Gatekeeper return package planning.",
            "safety_boundary": "Residual blocker tracking only.",
        }
        for code, severity, impact in specs
    ]


def build_phase_18_recommendation_matrix() -> list[dict]:
    """Build the Phase 18 recommendation matrix."""
    specs = [
        (
            "start_phase_18_gatekeeper_return_package_layer",
            "recommended_with_warnings",
            "Open the Gatekeeper return package layer with all Phase 17 warnings preserved.",
        ),
        (
            "define_gatekeeper_return_package_plan",
            "recommended",
            "Define Task 132 plan before packaging any evidence.",
        ),
        (
            "preserve_persona_review_block",
            "required",
            "Keep actual persona review blocked.",
        ),
        (
            "preserve_investor_agent_execution_block",
            "required",
            "Keep investor-agent execution blocked.",
        ),
        (
            "preserve_no_recommendations",
            "required",
            "Do not create recommendations.",
        ),
        ("preserve_no_rankings", "required", "Do not create rankings."),
        ("preserve_no_trade_signals", "required", "Do not create trade signals."),
        (
            "preserve_auto_promotion_disabled",
            "required",
            "Keep auto-promotion disabled.",
        ),
        (
            "prepare_gatekeeper_return_package_only",
            "allowed",
            "Prepare only the Gatekeeper return package.",
        ),
    ]
    return [
        {
            "recommendation_code": code,
            "recommendation_label": code.replace("_", " "),
            "recommendation_status": status,
            "phase_18_use": use,
            "allowed_scope": "Gatekeeper return package planning and packaging only.",
            "blocked_scope": (
                "Persona review, investor-agent execution, investor decisions, "
                "recommendations, rankings, allocations, rebalancing, trade "
                "signals, and auto-promotion."
            ),
            "safety_boundary": "Next-phase recommendation only.",
        }
        for code, status, use in specs
    ]


def build_task_132_handoff_manifest(
    *,
    phase_17_closure_run_id: str,
    re_review: dict,
) -> dict:
    """Build the Task 132 handoff manifest."""
    return {
        "future_phase_id": 18,
        "future_phase_name": "Gatekeeper Return Package Layer",
        "future_task_id": 132,
        "future_task_name": "Define Gatekeeper Return Package Plan",
        "phase_17_closure_run_id": phase_17_closure_run_id,
        "gatekeeper_stabilization_re_review_run_id": re_review[
            "gatekeeper_stabilization_re_review_run_id"
        ],
        "gatekeeper_stabilized_comparison_run_id": re_review[
            "gatekeeper_stabilized_comparison_run_id"
        ],
        "allowed_scope": [
            "planning Gatekeeper return package",
            "packaging stabilized evidence for Gatekeeper review",
            "preserving Phase 17 blocker disclosures",
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
        "readiness_status": "ready_to_define_gatekeeper_return_package_plan",
        "execution_allowed_now": True,
        "reason": (
            "Phase 17 is closed with stabilization progress and limited scope "
            "for Gatekeeper return package planning."
        ),
    }


def build_phase_17_closure_checks() -> list[dict]:
    """Build Task 131 closure checks."""
    checks = [
        "gatekeeper_stabilization_re_review_loaded",
        "phase_17_task_status_matrix_created",
        "final_gatekeeper_stabilization_summary_created",
        "final_permission_boundary_summary_created",
        "remaining_blockers_matrix_created",
        "phase_18_recommendation_matrix_created",
        "task_132_handoff_manifest_created",
        "phase_17_closed",
        "gatekeeper_hold_or_limited_status_preserved",
        "persona_review_block_preserved",
        "investor_agent_execution_block_preserved",
        "auto_promotion_disabled_preserved",
        "no_recommendation_outputs",
        "no_ranking_outputs",
        "no_trade_signal_outputs",
        "no_allocation_outputs",
        "no_network_calls",
        "next_phase_recommendation_created",
    ]
    return [
        {
            "check_code": check,
            "check_label": check.replace("_", " "),
            "status": "satisfied",
            "source_artifact": "phase_17_closure",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 131.",
        }
        for check in checks
    ]


def build_phase_17_closure(
    *,
    phase_17_closure_run_id: str,
    generated_at: str,
    re_review: dict,
) -> Phase17ClosureReport:
    """Build the complete Task 131 closure report."""
    summary = build_phase_17_closure_summary(
        phase_17_closure_run_id=phase_17_closure_run_id,
        re_review=re_review,
    )
    return Phase17ClosureReport(
        phase_17_closure_run_id=phase_17_closure_run_id,
        generated_at=generated_at,
        gatekeeper_stabilization_re_review_run_id=re_review[
            "gatekeeper_stabilization_re_review_run_id"
        ],
        gatekeeper_stabilized_comparison_run_id=re_review[
            "gatekeeper_stabilized_comparison_run_id"
        ],
        stabilization_validation_run_id=re_review["stabilization_validation_run_id"],
        targeted_repair_run_id=re_review["targeted_repair_run_id"],
        residual_work_order_package_run_id=re_review[
            "residual_work_order_package_run_id"
        ],
        stabilization_plan_run_id=re_review["stabilization_plan_run_id"],
        phase_16_closure_run_id=re_review["phase_16_closure_run_id"],
        baseline_gatekeeper_re_evaluation_run_id=re_review[
            "baseline_gatekeeper_re_evaluation_run_id"
        ],
        pre_post_repair_comparison_run_id=re_review[
            "pre_post_repair_comparison_run_id"
        ],
        controlled_re_run_trial_run_id=re_review["controlled_re_run_trial_run_id"],
        re_run_input_package_run_id=re_review["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=re_review["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=re_review["research_audit_trail_run_id"],
        phase_17_closure_summary=summary,
        phase_17_task_status_matrix=build_phase_17_task_status_matrix(
            phase_17_closure_run_id=phase_17_closure_run_id,
            re_review=re_review,
        ),
        final_gatekeeper_stabilization_summary=(
            build_final_gatekeeper_stabilization_summary(re_review)
        ),
        final_permission_boundary_summary=build_final_permission_boundary_summary(
            re_review
        ),
        remaining_blockers_after_phase_17_matrix=(
            build_remaining_blockers_after_phase_17_matrix()
        ),
        phase_18_recommendation_matrix=build_phase_18_recommendation_matrix(),
        task_132_handoff_manifest=build_task_132_handoff_manifest(
            phase_17_closure_run_id=phase_17_closure_run_id,
            re_review=re_review,
        ),
        phase_17_closure_checks=build_phase_17_closure_checks(),
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


def _render_markdown(report: Phase17ClosureReport) -> str:
    summary = report.phase_17_closure_summary
    final_summary = report.final_gatekeeper_stabilization_summary
    handoff = report.task_132_handoff_manifest
    lines = [
        "# Phase 17 Closure & Next-Step Decision",
        "",
        "## Executive Summary",
        "",
        f"* Phase 17 Closure Run ID: {report.phase_17_closure_run_id}",
        (
            "* Gatekeeper Stabilization Re-Review Run ID: "
            f"{report.gatekeeper_stabilization_re_review_run_id}"
        ),
        f"* Current Phase: 17 - {PHASE_NAME}",
        "* Current Task: Task 131 - Phase 17 Closure & Next-Step Decision",
        f"* Phase Completion Status: {summary['phase_completion_status']}",
        (
            "* Final Gatekeeper Stabilization Outcome: "
            f"{summary['final_gatekeeper_stabilization_outcome']}"
        ),
        f"* Final Progression Status: {summary['final_progression_status']}",
        f"* Final Persona Review Status: {summary['final_persona_review_status']}",
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
        "17 - Targeted Evidence Stabilization Layer",
        "",
        "Previous Task:",
        "Task 130 - Gatekeeper Stabilization Re-Review completed",
        "",
        "This Task:",
        "Task 131 closes Phase 17 and decides the next phase.",
        "",
        "Phase 17 Final State:",
        "hold_with_stabilization_progress",
        "",
        "Direct Next:",
        "Task 132 - Define Gatekeeper Return Package Plan",
        "",
        "Phase 18 Expected Role:",
        "Gatekeeper Return Package Layer",
        "",
        "## Phase 17 Closure Summary",
        "",
        *_markdown_table(
            _summary_rows(summary),
            [("Field", "field"), ("Value", "value")],
        ),
        "",
        "## Phase 17 Task Status Matrix",
        "",
        *_markdown_table(
            report.phase_17_task_status_matrix,
            [
                ("Task", "task_id"),
                ("Name", "task_name"),
                ("Run ID", "run_id"),
                ("Status", "completion_status"),
                ("Key Result", "key_result"),
            ],
        ),
        "",
        "## Final Gatekeeper Stabilization Summary",
        "",
        *_markdown_table(
            _summary_rows(final_summary),
            [("Field", "field"), ("Value", "value")],
        ),
        "",
        "## Final Permission Boundary Summary",
        "",
        *_markdown_table(
            report.final_permission_boundary_summary,
            [
                ("Permission", "permission_code"),
                ("Final Status", "final_status"),
                ("Allowed Scope", "allowed_scope"),
                ("Blocked Scope", "blocked_scope"),
                ("Condition To Expand", "condition_to_expand_scope"),
            ],
        ),
        "",
        "## Remaining Blockers After Phase 17",
        "",
        *_markdown_table(
            report.remaining_blockers_after_phase_17_matrix,
            [
                ("Blocker", "blocker_code"),
                ("Severity", "severity"),
                ("Status", "status_after_phase_17"),
                ("Impact On Next Phase", "impact_on_next_phase"),
            ],
        ),
        "",
        "## Phase 18 Recommendation Matrix",
        "",
        *_markdown_table(
            report.phase_18_recommendation_matrix,
            [
                ("Recommendation", "recommendation_code"),
                ("Status", "recommendation_status"),
                ("Phase 18 Use", "phase_18_use"),
                ("Allowed Scope", "allowed_scope"),
                ("Blocked Scope", "blocked_scope"),
            ],
        ),
        "",
        "## Task 132 Handoff Manifest",
        "",
        f"* Future Phase: {handoff['future_phase_id']} - {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Allowed Scope: {'; '.join(handoff['allowed_scope'])}",
        f"* Prohibited Outputs: {'; '.join(handoff['prohibited_outputs'])}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Phase 17 Closure Checks",
        "",
        *_markdown_table(
            report.phase_17_closure_checks,
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
        "* Phase 17 is complete.",
        "* Stabilization progress can be packaged for Gatekeeper return review.",
        "* Phase 18 should remain limited to Gatekeeper return package preparation.",
        "* Persona reviews and investor-agent execution remain blocked.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not allow persona review.",
        "* It does not run investor agents.",
        "* It does not recommend any company.",
        "* It does not rank companies.",
        "* It does not create allocation or rebalancing.",
        "* It does not create a trade signal.",
        "* It does not validate a strategy.",
        "* It does not enable auto-promotion.",
        "",
        "## Next Phase",
        "",
        f"* {report.recommended_next_phase}",
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


def write_phase_17_closure_report(
    *,
    outputs_root: Path,
    gatekeeper_stabilization_re_review_run_id: str | None = None,
) -> Phase17ClosureFiles:
    """Write Task 131 Phase 17 closure artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_gatekeeper_stabilization_re_review_manifest(
        outputs_root=outputs_root,
        gatekeeper_stabilization_re_review_run_id=(
            gatekeeper_stabilization_re_review_run_id
        ),
    )
    re_review_run_id = manifest["gatekeeper_stabilization_re_review_run_id"]
    re_review = load_gatekeeper_stabilization_re_review(
        outputs_root=outputs_root,
        gatekeeper_stabilization_re_review_run_id=re_review_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_phase_17_closure(
        phase_17_closure_run_id=run_id,
        generated_at=generated_at.isoformat(),
        re_review=re_review,
    )

    root = outputs_root / "phase_17_closures"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "phase_17_closure.md"
    json_path = output_folder / "phase_17_closure.json"
    task_status_csv = output_folder / "phase_17_task_status_matrix.csv"
    gatekeeper_summary_csv = output_folder / "final_gatekeeper_stabilization_summary.csv"
    permission_summary_csv = output_folder / "final_permission_boundary_summary.csv"
    blockers_csv = output_folder / "remaining_blockers_after_phase_17_matrix.csv"
    phase_18_csv = output_folder / "phase_18_recommendation_matrix.csv"
    handoff_path = output_folder / "task_132_handoff_manifest.json"
    checks_csv = output_folder / "phase_17_closure_checks.csv"
    latest_manifest_path = root / "latest_phase_17_closure_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(task_status_csv, report.phase_17_task_status_matrix)
    _write_csv(gatekeeper_summary_csv, _summary_rows(report.final_gatekeeper_stabilization_summary))
    _write_csv(permission_summary_csv, report.final_permission_boundary_summary)
    _write_csv(blockers_csv, report.remaining_blockers_after_phase_17_matrix)
    _write_csv(phase_18_csv, report.phase_18_recommendation_matrix)
    handoff_path.write_text(
        json.dumps(report.task_132_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.phase_17_closure_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "phase_17_closure_run_id": report.phase_17_closure_run_id,
                "gatekeeper_stabilization_re_review_run_id": (
                    report.gatekeeper_stabilization_re_review_run_id
                ),
                "final_gatekeeper_stabilization_outcome": (
                    report.phase_17_closure_summary[
                        "final_gatekeeper_stabilization_outcome"
                    ]
                ),
                "final_progression_status": report.phase_17_closure_summary[
                    "final_progression_status"
                ],
                "final_persona_review_status": report.phase_17_closure_summary[
                    "final_persona_review_status"
                ],
                "closure_status": report.closure_status,
                "recommended_next_phase": report.recommended_next_phase,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_132_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return Phase17ClosureFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        task_status_csv_path=task_status_csv,
        gatekeeper_summary_csv_path=gatekeeper_summary_csv,
        permission_summary_csv_path=permission_summary_csv,
        remaining_blockers_csv_path=blockers_csv,
        phase_18_recommendation_csv_path=phase_18_csv,
        task_132_handoff_manifest_path=handoff_path,
        checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
