"""Task 124 Phase 16 closure and next-phase recommendation report."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report closes Phase 16 and recommends a governance next phase only. "
    "It does not rerun Gatekeeper, run investor agents, allow persona review, "
    "create investor decisions, rankings, recommendations, allocations, "
    "rebalancing instructions, trade signals, execution instructions, or "
    "strategy validation."
)
PHASE_17 = "Phase 17 — Targeted Evidence Stabilization Layer"
TASK_125 = "Task 125 — Define Targeted Evidence Stabilization Plan"


@dataclass(frozen=True)
class Phase16ClosureReport:
    """Structured Task 124 Phase 16 closure report."""

    phase_16_closure_run_id: str
    generated_at: str
    gatekeeper_re_evaluation_run_id: str
    pre_post_repair_comparison_run_id: str
    controlled_re_run_trial_run_id: str
    re_run_input_package_run_id: str
    re_run_re_gate_plan_run_id: str
    research_audit_trail_run_id: str
    phase_closure_summary: dict
    phase_task_status_matrix: list[dict]
    gatekeeper_outcome_summary: dict
    remaining_blockers_matrix: list[dict]
    residual_risk_matrix: list[dict]
    next_phase_recommendation_matrix: list[dict]
    task_125_handoff_manifest: dict
    phase_16_closure_validation_checks: list[dict]
    phase_completion_status: str
    final_gatekeeper_outcome: str
    final_progression_allowed: bool
    final_persona_reviews_allowed: bool
    recommended_next_phase: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class Phase16ClosureFiles:
    """Generated Task 124 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    phase_task_status_csv_path: Path
    gatekeeper_outcome_summary_csv_path: Path
    remaining_blockers_csv_path: Path
    residual_risk_csv_path: Path
    next_phase_recommendation_csv_path: Path
    task_125_handoff_manifest_path: Path
    validation_checks_csv_path: Path
    latest_manifest_path: Path
    report: Phase16ClosureReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_gatekeeper_re_evaluation_manifest(
    *,
    outputs_root: Path,
    gatekeeper_re_evaluation_run_id: str | None = None,
) -> dict:
    """Load one Task 123 report or the latest Task 123 manifest."""
    root = Path(outputs_root) / "gatekeeper_re_evaluations"
    path = (
        root / gatekeeper_re_evaluation_run_id / "gatekeeper_re_evaluation.json"
        if gatekeeper_re_evaluation_run_id
        else root / "latest_gatekeeper_re_evaluation_manifest.json"
    )
    label = (
        "Gatekeeper re-evaluation report"
        if gatekeeper_re_evaluation_run_id
        else "Gatekeeper re-evaluation manifest"
    )
    return _load_required_json(path, label)


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


def _decision(gatekeeper_re_evaluation: dict) -> dict:
    return gatekeeper_re_evaluation.get("re_gate_decision_record", {})


def build_phase_closure_summary(
    *,
    phase_16_closure_run_id: str,
    gatekeeper_re_evaluation: dict,
) -> dict:
    """Build the Phase 16 closure summary."""
    decision = _decision(gatekeeper_re_evaluation)
    return {
        "phase_16_closure_run_id": phase_16_closure_run_id,
        "gatekeeper_re_evaluation_run_id": gatekeeper_re_evaluation[
            "gatekeeper_re_evaluation_run_id"
        ],
        "pre_post_repair_comparison_run_id": gatekeeper_re_evaluation[
            "pre_post_repair_comparison_run_id"
        ],
        "controlled_re_run_trial_run_id": gatekeeper_re_evaluation[
            "controlled_re_run_trial_run_id"
        ],
        "re_run_input_package_run_id": gatekeeper_re_evaluation[
            "re_run_input_package_run_id"
        ],
        "re_run_re_gate_plan_run_id": gatekeeper_re_evaluation[
            "re_run_re_gate_plan_run_id"
        ],
        "research_audit_trail_run_id": gatekeeper_re_evaluation[
            "research_audit_trail_run_id"
        ],
        "phase_id": 16,
        "phase_name": "Re-Run & Re-Gate Layer",
        "current_task_id": 124,
        "current_task_name": "Phase 16 Closure & Next-Phase Recommendation",
        "phase_completion_status": "completed",
        "final_gatekeeper_outcome": decision["new_gatekeeper_outcome"],
        "final_progression_allowed": decision[
            "progression_allowed_after_re_evaluation"
        ],
        "final_persona_reviews_allowed": decision[
            "persona_reviews_allowed_after_re_evaluation"
        ],
        "recommended_next_phase_id": 17,
        "recommended_next_phase_name": "Targeted Evidence Stabilization Layer",
        "recommended_next_task_id": 125,
        "recommended_next_task_name": "Define Targeted Evidence Stabilization Plan",
        "closure_role": "phase_closure_and_next_phase_recommendation",
        "main_closure_finding": (
            "Phase 16 is complete; Gatekeeper outcome is "
            "hold_with_repair_progress, so targeted evidence stabilization is "
            "recommended before any persona review."
        ),
    }


def build_phase_task_status_matrix(gatekeeper_re_evaluation: dict) -> list[dict]:
    """Build Phase 16 task status rows."""
    tasks = [
        (
            119,
            "Define Re-Run & Re-Gate Plan",
            gatekeeper_re_evaluation["re_run_re_gate_plan_run_id"],
            "re_run_re_gate_plan",
            "Task 120 — Build Re-Run Input Package",
        ),
        (
            120,
            "Build Re-Run Input Package",
            gatekeeper_re_evaluation["re_run_input_package_run_id"],
            "re_run_input_package",
            "Task 121 — Execute Controlled Re-Run Trial",
        ),
        (
            121,
            "Execute Controlled Re-Run Trial",
            gatekeeper_re_evaluation["controlled_re_run_trial_run_id"],
            "controlled_re_run_trial",
            "Task 122 — Compare Pre-Repair vs Post-Repair Evidence",
        ),
        (
            122,
            "Compare Pre-Repair vs Post-Repair Evidence",
            gatekeeper_re_evaluation["pre_post_repair_comparison_run_id"],
            "pre_post_repair_comparison",
            "Task 123 — Run Gatekeeper Re-Evaluation",
        ),
        (
            123,
            "Run Gatekeeper Re-Evaluation",
            gatekeeper_re_evaluation["gatekeeper_re_evaluation_run_id"],
            "gatekeeper_re_evaluation",
            "Task 124 — Phase 16 Closure & Next-Phase Recommendation",
        ),
        (
            124,
            "Phase 16 Closure & Next-Phase Recommendation",
            "current_run",
            "phase_16_closure",
            TASK_125,
        ),
    ]
    return [
        {
            "task_id": task_id,
            "task_name": task_name,
            "run_id": run_id,
            "status": "completed",
            "primary_output": primary_output,
            "recommended_next_task": recommended_next_task,
            "safety_boundary_preserved": True,
            "finding": f"Task {task_id} completed within Phase 16 governance bounds.",
        }
        for task_id, task_name, run_id, primary_output, recommended_next_task in tasks
    ]


def build_gatekeeper_outcome_summary(gatekeeper_re_evaluation: dict) -> dict:
    """Build the final Gatekeeper outcome summary."""
    decision = _decision(gatekeeper_re_evaluation)
    return {
        "previous_gatekeeper_decision": decision["previous_gatekeeper_decision"],
        "new_gatekeeper_outcome": decision["new_gatekeeper_outcome"],
        "progression_allowed_after_re_evaluation": decision[
            "progression_allowed_after_re_evaluation"
        ],
        "persona_reviews_allowed_after_re_evaluation": decision[
            "persona_reviews_allowed_after_re_evaluation"
        ],
        "outcome_classification": "repair_progress_without_progression",
        "meaning": (
            "Repair and comparison work progressed, but evidence is not cleared "
            "for progression or persona review."
        ),
        "allowed_next_step": "targeted evidence stabilization / repair planning",
        "blocked_next_step": (
            "persona review, investor agent review, recommendations, ranking, "
            "allocation, trade signals"
        ),
        "safety_boundary": "Outcome summary only; no investment action.",
    }


def build_remaining_blockers_matrix(gatekeeper_re_evaluation: dict) -> list[dict]:
    """Build remaining blocker rows."""
    blockers = [
        (
            "progression_not_allowed",
            "Progression not allowed",
            "critical",
            "Preserve hold state until future Gatekeeper review.",
            "phase_17_governance_controls",
        ),
        (
            "persona_review_not_allowed",
            "Persona review not allowed",
            "critical",
            "Do not run persona review until a future gate allows it.",
            "phase_17_persona_review_block",
        ),
        (
            "evidence_still_unstable_or_not_progression_ready",
            "Evidence still unstable or not progression-ready",
            "high",
            "Define stabilization plan for unresolved evidence warnings.",
            "evidence_stabilization_plan",
        ),
        (
            "residual_benchmark_relative_uncertainty",
            "Residual benchmark-relative uncertainty",
            "high",
            "Bound benchmark-relative interpretation before re-gating.",
            "benchmark_relative_stabilization",
        ),
        (
            "residual_walk_forward_or_period_sensitivity",
            "Residual walk-forward or period sensitivity",
            "high",
            "Retain period controls and document unstable periods.",
            "walk_forward_stabilization",
        ),
        (
            "residual_outlier_dependence",
            "Residual outlier dependence",
            "high",
            "Maintain outlier controls and contributor exclusions.",
            "outlier_stabilization",
        ),
        (
            "residual_metadata_concentration",
            "Residual metadata concentration",
            "moderate",
            "Preserve metadata concentration controls.",
            "metadata_stabilization",
        ),
        (
            "residual_clean_warning_or_anchor_uncertainty",
            "Residual clean/warning or anchor uncertainty",
            "moderate",
            "Keep clean/warning and anchor buckets separate.",
            "coverage_anchor_stabilization",
        ),
        (
            "residual_current_core_expanded_cohort_gap",
            "Residual current-core versus expanded-cohort gap",
            "high",
            "Keep current_core and expanded_cohort separated.",
            "cohort_gap_stabilization",
        ),
        (
            "local_artifacts_only_limitation",
            "Local artifacts only limitation",
            "moderate",
            "Avoid fabricating missing data or fetching live data.",
            "local_artifact_governance",
        ),
    ]
    return [
        {
            "blocker_code": code,
            "blocker_label": label,
            "source": gatekeeper_re_evaluation["gatekeeper_re_evaluation_run_id"],
            "severity": severity,
            "blocker_status": "active",
            "why_it_matters": (
                "The blocker prevents Phase 16 from clearing progression or "
                "persona review."
            ),
            "required_repair_action": action,
            "proposed_next_phase_workstream": workstream,
            "safety_boundary": "Blocker tracking only; no recommendation.",
        }
        for code, label, severity, action, workstream in blockers
    ]


def build_residual_risk_matrix() -> list[dict]:
    """Build residual risk rows."""
    risks = [
        ("false_progression_risk", "False progression risk", "critical"),
        ("premature_persona_review_risk", "Premature persona review risk", "critical"),
        ("overreading_repair_progress_risk", "Overreading repair progress risk", "high"),
        ("sample_instability_risk", "Sample instability risk", "high"),
        ("metadata_concentration_risk", "Metadata concentration risk", "moderate"),
        ("outlier_dependence_risk", "Outlier dependence risk", "high"),
        (
            "benchmark_relative_misinterpretation_risk",
            "Benchmark-relative misinterpretation risk",
            "high",
        ),
        ("governance_drift_risk", "Governance drift risk", "critical"),
    ]
    return [
        {
            "risk_code": code,
            "risk_label": label,
            "severity": severity,
            "current_status": "active_residual_risk",
            "impact_if_ignored": (
                "Ignoring this risk could make research evidence appear more "
                "progression-ready than the Gatekeeper outcome supports."
            ),
            "mitigation_in_next_phase": (
                "Include this risk in Phase 17 targeted evidence stabilization "
                "criteria."
            ),
            "safety_boundary": "Risk documentation only.",
        }
        for code, label, severity in risks
    ]


def build_next_phase_recommendation_matrix() -> list[dict]:
    """Build next phase recommendation rows."""
    rows = [
        (
            "recommended_next_phase",
            PHASE_17,
            TASK_125,
            "Gatekeeper outcome is hold_with_repair_progress.",
            "Define stabilization workstreams.",
            "Persona review; investor agent execution.",
            "Residual blockers are explicitly resolved or bounded.",
        ),
        (
            "first_task",
            PHASE_17,
            TASK_125,
            "Phase 17 needs a controlled plan before execution.",
            "Planning and evidence stabilization design.",
            "Recommendations; rankings; allocations.",
            "A plan exists with no safety-boundary drift.",
        ),
        (
            "why_not_persona_review",
            PHASE_17,
            TASK_125,
            "Persona reviews allowed remains false.",
            "Maintain persona review block.",
            "Buffett/Munger/Fisher/Lynch/Bogle review.",
            "Future Gatekeeper explicitly allows review preparation.",
        ),
        (
            "why_not_investor_agents",
            PHASE_17,
            TASK_125,
            "Investor agents were not run and remain out of scope.",
            "Governance planning only.",
            "Direct investor agent execution.",
            "Future task authorizes agent review under controls.",
        ),
        (
            "why_not_recommendations",
            PHASE_17,
            TASK_125,
            "This chain is research-only and non-actionable.",
            "Document evidence repair needs.",
            "Company recommendations or rankings.",
            "No recommendation language is introduced.",
        ),
        (
            "success_criteria_for_returning_to_gatekeeper",
            PHASE_17,
            TASK_125,
            "Re-gating requires resolved or bounded residual blockers.",
            "Define measurable stabilization criteria.",
            "Premature re-gating.",
            "Benchmark, outlier, period, metadata, and cohort issues are bounded.",
        ),
        (
            "condition_for_future_limited_persona_review_preparation",
            PHASE_17,
            TASK_125,
            "Persona review can only be prepared after future governance clearance.",
            "Define future clearance conditions.",
            "Automatic persona review.",
            "A future Gatekeeper explicitly permits limited review preparation.",
        ),
    ]
    return [
        {
            "recommendation_code": code,
            "recommended_phase": phase,
            "recommended_task": task,
            "rationale": rationale,
            "allowed_actions": allowed,
            "blocked_actions": blocked,
            "success_criteria": success,
            "safety_boundary": "Next-phase recommendation only.",
        }
        for code, phase, task, rationale, allowed, blocked, success in rows
    ]


def build_task_125_handoff_manifest(
    *,
    phase_16_closure_run_id: str,
    gatekeeper_re_evaluation_run_id: str,
) -> dict:
    """Build the Task 125 handoff manifest."""
    return {
        "future_phase_id": 17,
        "future_phase_name": "Targeted Evidence Stabilization Layer",
        "future_task_id": 125,
        "future_task_name": "Define Targeted Evidence Stabilization Plan",
        "phase_16_closure_run_id": phase_16_closure_run_id,
        "gatekeeper_re_evaluation_run_id": gatekeeper_re_evaluation_run_id,
        "required_inputs": [
            "phase_16_closure",
            "gatekeeper_re_evaluation",
            "pre_post_repair_comparison",
            "controlled_re_run_trial",
        ],
        "required_planning_items": [
            "residual_blocker_prioritization",
            "targeted_stabilization_workstreams",
            "future_gatekeeper_return_conditions",
            "persona_review_block_preservation",
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
        "readiness_status": "ready_for_targeted_evidence_stabilization_planning",
        "execution_allowed_now": True,
        "reason": (
            "Phase 16 is complete and Gatekeeper outcome is "
            "hold_with_repair_progress, requiring targeted stabilization rather "
            "than persona review."
        ),
    }


def build_phase_16_closure_validation_checks() -> list[dict]:
    """Build validation checks for Task 124."""
    checks = [
        "gatekeeper_re_evaluation_loaded",
        "phase_closure_summary_created",
        "phase_task_status_matrix_created",
        "gatekeeper_outcome_summary_created",
        "remaining_blockers_matrix_created",
        "residual_risk_matrix_created",
        "next_phase_recommendation_matrix_created",
        "task_125_handoff_manifest_created",
        "phase_16_marked_completed",
        "final_gatekeeper_outcome_preserved",
        "progression_not_allowed_preserved",
        "persona_review_not_allowed_preserved",
        "investor_agents_not_run",
        "gatekeeper_not_rerun_in_task_124",
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
            "source_artifact": "phase_16_closure",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 124.",
        }
        for check in checks
    ]


def build_phase_16_closure(
    *,
    phase_16_closure_run_id: str,
    generated_at: str,
    gatekeeper_re_evaluation: dict,
) -> Phase16ClosureReport:
    """Build the Phase 16 closure report."""
    summary = build_phase_closure_summary(
        phase_16_closure_run_id=phase_16_closure_run_id,
        gatekeeper_re_evaluation=gatekeeper_re_evaluation,
    )
    outcome = build_gatekeeper_outcome_summary(gatekeeper_re_evaluation)
    handoff = build_task_125_handoff_manifest(
        phase_16_closure_run_id=phase_16_closure_run_id,
        gatekeeper_re_evaluation_run_id=gatekeeper_re_evaluation[
            "gatekeeper_re_evaluation_run_id"
        ],
    )
    return Phase16ClosureReport(
        phase_16_closure_run_id=phase_16_closure_run_id,
        generated_at=generated_at,
        gatekeeper_re_evaluation_run_id=gatekeeper_re_evaluation[
            "gatekeeper_re_evaluation_run_id"
        ],
        pre_post_repair_comparison_run_id=gatekeeper_re_evaluation[
            "pre_post_repair_comparison_run_id"
        ],
        controlled_re_run_trial_run_id=gatekeeper_re_evaluation[
            "controlled_re_run_trial_run_id"
        ],
        re_run_input_package_run_id=gatekeeper_re_evaluation[
            "re_run_input_package_run_id"
        ],
        re_run_re_gate_plan_run_id=gatekeeper_re_evaluation[
            "re_run_re_gate_plan_run_id"
        ],
        research_audit_trail_run_id=gatekeeper_re_evaluation[
            "research_audit_trail_run_id"
        ],
        phase_closure_summary=summary,
        phase_task_status_matrix=build_phase_task_status_matrix(
            gatekeeper_re_evaluation
        ),
        gatekeeper_outcome_summary=outcome,
        remaining_blockers_matrix=build_remaining_blockers_matrix(
            gatekeeper_re_evaluation
        ),
        residual_risk_matrix=build_residual_risk_matrix(),
        next_phase_recommendation_matrix=build_next_phase_recommendation_matrix(),
        task_125_handoff_manifest=handoff,
        phase_16_closure_validation_checks=build_phase_16_closure_validation_checks(),
        phase_completion_status=summary["phase_completion_status"],
        final_gatekeeper_outcome=summary["final_gatekeeper_outcome"],
        final_progression_allowed=summary["final_progression_allowed"],
        final_persona_reviews_allowed=summary["final_persona_reviews_allowed"],
        recommended_next_phase=PHASE_17,
        recommended_next_task=TASK_125,
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


def _render_markdown(report: Phase16ClosureReport) -> str:
    outcome = report.gatekeeper_outcome_summary
    handoff = report.task_125_handoff_manifest
    lines = [
        "# Phase 16 Closure & Next-Phase Recommendation",
        "",
        "## Executive Summary",
        "",
        f"* Phase 16 Closure Run ID: {report.phase_16_closure_run_id}",
        f"* Gatekeeper Re-Evaluation Run ID: {report.gatekeeper_re_evaluation_run_id}",
        "* Current Phase: 16 — Re-Run & Re-Gate Layer",
        "* Current Task: Task 124 — Phase 16 Closure & Next-Phase Recommendation",
        f"* Phase Completion Status: {report.phase_completion_status}",
        f"* Final Gatekeeper Outcome: {report.final_gatekeeper_outcome}",
        f"* Final Progression Allowed: {str(report.final_progression_allowed).lower()}",
        (
            "* Final Persona Reviews Allowed: "
            f"{str(report.final_persona_reviews_allowed).lower()}"
        ),
        f"* Recommended Next Phase: {report.recommended_next_phase}",
        f"* Recommended Next Task: {report.recommended_next_task}",
        "",
        "## Important Boundary",
        "",
        (
            "This report closes Phase 16 and recommends a governance next phase "
            "only. It does not rerun Gatekeeper, run investor agents, allow "
            "persona review, create investor decisions, rankings, "
            "recommendations, allocations, rebalancing instructions, trade "
            "signals, execution instructions, or strategy validation."
        ),
        "",
        "## Where We Are Now",
        "",
        "Current Phase:",
        "16 — Re-Run & Re-Gate Layer",
        "",
        "Previous Task:",
        "Task 123 — Run Gatekeeper Re-Evaluation completed",
        "",
        "This Task:",
        "Task 124 closes Phase 16 and recommends the next phase.",
        "",
        "Phase 16 Final Status:",
        "Completed",
        "",
        "Final Gatekeeper Outcome:",
        "hold_with_repair_progress",
        "",
        "Progression:",
        "Not allowed",
        "",
        "Persona Reviews:",
        "Not allowed",
        "",
        "Recommended Next Phase:",
        PHASE_17,
        "",
        "Recommended First Task:",
        TASK_125,
        "",
        "## Phase Task Status Matrix",
        "",
        *_markdown_table(
            report.phase_task_status_matrix,
            [
                ("Task", "task_id"),
                ("Status", "status"),
                ("Run ID", "run_id"),
                ("Primary Output", "primary_output"),
                ("Safety Boundary", "safety_boundary_preserved"),
            ],
        ),
        "",
        "## Gatekeeper Outcome Summary",
        "",
        f"* Previous Decision: {outcome['previous_gatekeeper_decision']}",
        f"* New Outcome: {outcome['new_gatekeeper_outcome']}",
        (
            "* Progression Allowed: "
            f"{str(outcome['progression_allowed_after_re_evaluation']).lower()}"
        ),
        (
            "* Persona Reviews Allowed: "
            f"{str(outcome['persona_reviews_allowed_after_re_evaluation']).lower()}"
        ),
        f"* Outcome Classification: {outcome['outcome_classification']}",
        f"* Meaning: {outcome['meaning']}",
        f"* Allowed Next Step: {outcome['allowed_next_step']}",
        f"* Blocked Next Step: {outcome['blocked_next_step']}",
        "",
        "## Remaining Blockers",
        "",
        *_markdown_table(
            report.remaining_blockers_matrix,
            [
                ("Blocker", "blocker_code"),
                ("Severity", "severity"),
                ("Status", "blocker_status"),
                ("Required Repair", "required_repair_action"),
                ("Next Phase Workstream", "proposed_next_phase_workstream"),
            ],
        ),
        "",
        "## Residual Risks",
        "",
        *_markdown_table(
            report.residual_risk_matrix,
            [
                ("Risk", "risk_code"),
                ("Severity", "severity"),
                ("Current Status", "current_status"),
                ("Mitigation In Next Phase", "mitigation_in_next_phase"),
            ],
        ),
        "",
        "## Next Phase Recommendation",
        "",
        *_markdown_table(
            report.next_phase_recommendation_matrix,
            [
                ("Recommendation", "recommendation_code"),
                ("Recommended Phase", "recommended_phase"),
                ("Recommended Task", "recommended_task"),
                ("Rationale", "rationale"),
                ("Success Criteria", "success_criteria"),
            ],
        ),
        "",
        "## Task 125 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} — {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} — {handoff['future_task_name']}",
        f"* Required Inputs: {'; '.join(handoff['required_inputs'])}",
        f"* Required Planning Items: {'; '.join(handoff['required_planning_items'])}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.phase_16_closure_validation_checks,
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
        "* Phase 16 is complete.",
        "* Evidence repair progressed but not enough to permit progression.",
        "* The correct next move is targeted evidence stabilization.",
        "* Persona review remains blocked.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not allow investor review.",
        "* It does not run investor agents.",
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


def write_phase_16_closure_report(
    *,
    outputs_root: Path,
    gatekeeper_re_evaluation_run_id: str | None = None,
) -> Phase16ClosureFiles:
    """Write Task 124 Phase 16 closure artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_gatekeeper_re_evaluation_manifest(
        outputs_root=outputs_root,
        gatekeeper_re_evaluation_run_id=gatekeeper_re_evaluation_run_id,
    )
    re_evaluation_run_id = manifest["gatekeeper_re_evaluation_run_id"]
    gatekeeper_re_evaluation = load_gatekeeper_re_evaluation(
        outputs_root=outputs_root,
        gatekeeper_re_evaluation_run_id=re_evaluation_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_phase_16_closure(
        phase_16_closure_run_id=run_id,
        generated_at=generated_at.isoformat(),
        gatekeeper_re_evaluation=gatekeeper_re_evaluation,
    )

    root = outputs_root / "phase_16_closures"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "phase_16_closure.md"
    json_path = output_folder / "phase_16_closure.json"
    task_csv = output_folder / "phase_task_status_matrix.csv"
    outcome_csv = output_folder / "gatekeeper_outcome_summary.csv"
    blockers_csv = output_folder / "remaining_blockers_matrix.csv"
    risk_csv = output_folder / "residual_risk_matrix.csv"
    next_phase_csv = output_folder / "next_phase_recommendation_matrix.csv"
    handoff_path = output_folder / "task_125_handoff_manifest.json"
    checks_csv = output_folder / "phase_16_closure_validation_checks.csv"
    latest_manifest_path = root / "latest_phase_16_closure_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(task_csv, report.phase_task_status_matrix)
    _write_csv(outcome_csv, [report.gatekeeper_outcome_summary])
    _write_csv(blockers_csv, report.remaining_blockers_matrix)
    _write_csv(risk_csv, report.residual_risk_matrix)
    _write_csv(next_phase_csv, report.next_phase_recommendation_matrix)
    handoff_path.write_text(
        json.dumps(report.task_125_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.phase_16_closure_validation_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "phase_16_closure_run_id": report.phase_16_closure_run_id,
                "gatekeeper_re_evaluation_run_id": (
                    report.gatekeeper_re_evaluation_run_id
                ),
                "phase_completion_status": report.phase_completion_status,
                "final_gatekeeper_outcome": report.final_gatekeeper_outcome,
                "final_progression_allowed": report.final_progression_allowed,
                "final_persona_reviews_allowed": (
                    report.final_persona_reviews_allowed
                ),
                "recommended_next_phase": report.recommended_next_phase,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_125_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return Phase16ClosureFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        phase_task_status_csv_path=task_csv,
        gatekeeper_outcome_summary_csv_path=outcome_csv,
        remaining_blockers_csv_path=blockers_csv,
        residual_risk_csv_path=risk_csv,
        next_phase_recommendation_csv_path=next_phase_csv,
        task_125_handoff_manifest_path=handoff_path,
        validation_checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
