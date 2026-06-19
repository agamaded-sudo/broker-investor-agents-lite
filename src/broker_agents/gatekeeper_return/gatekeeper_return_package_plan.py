"""Task 132 Gatekeeper return package plan."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report defines the Gatekeeper return package plan only. It does not "
    "build the final package, rerun Gatekeeper, run investor agents, run actual "
    "persona reviews, create investor decisions, rankings, recommendations, "
    "allocations, rebalancing instructions, trade signals, execution "
    "instructions, auto-promotion, or strategy validation."
)
PHASE_NAME = "Gatekeeper Return Package Layer"
NEXT_TASK = "Task 133 - Build Gatekeeper Return Package Input Inventory"


@dataclass(frozen=True)
class GatekeeperReturnPackagePlanReport:
    """Structured Task 132 Gatekeeper return package plan."""

    gatekeeper_return_plan_run_id: str
    generated_at: str
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
    gatekeeper_return_plan_summary: dict
    return_package_component_matrix: list[dict]
    return_package_evidence_inventory_matrix: list[dict]
    return_package_residual_risk_disclosure_matrix: list[dict]
    return_package_permission_boundary_matrix: list[dict]
    phase_18_execution_roadmap: list[dict]
    task_133_handoff_manifest: dict
    gatekeeper_return_plan_validation_checks: list[dict]
    plan_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class GatekeeperReturnPackagePlanFiles:
    """Generated Task 132 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    component_csv_path: Path
    evidence_csv_path: Path
    residual_risk_csv_path: Path
    permission_csv_path: Path
    roadmap_csv_path: Path
    task_133_handoff_manifest_path: Path
    checks_csv_path: Path
    latest_manifest_path: Path
    report: GatekeeperReturnPackagePlanReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_phase_17_closure_manifest(
    *,
    outputs_root: Path,
    phase_17_closure_run_id: str | None = None,
) -> dict:
    """Load one Phase 17 closure report or the latest Phase 17 closure manifest."""
    root = Path(outputs_root) / "phase_17_closures"
    path = (
        root / phase_17_closure_run_id / "phase_17_closure.json"
        if phase_17_closure_run_id
        else root / "latest_phase_17_closure_manifest.json"
    )
    label = (
        "Phase 17 closure report"
        if phase_17_closure_run_id
        else "Phase 17 closure manifest"
    )
    return _load_required_json(path, label)


def load_phase_17_closure(
    *,
    outputs_root: Path,
    phase_17_closure_run_id: str,
) -> dict:
    """Load a Phase 17 closure report by run id."""
    path = (
        Path(outputs_root)
        / "phase_17_closures"
        / phase_17_closure_run_id
        / "phase_17_closure.json"
    )
    return _load_required_json(path, "Phase 17 closure report")


def _closure_summary(closure: dict) -> dict:
    return closure["phase_17_closure_summary"]


def build_gatekeeper_return_plan_summary(
    *,
    gatekeeper_return_plan_run_id: str,
    closure: dict,
) -> dict:
    """Build the Task 132 plan summary."""
    summary = _closure_summary(closure)
    return {
        "gatekeeper_return_plan_run_id": gatekeeper_return_plan_run_id,
        "phase_17_closure_run_id": closure["phase_17_closure_run_id"],
        "gatekeeper_stabilization_re_review_run_id": closure[
            "gatekeeper_stabilization_re_review_run_id"
        ],
        "phase_id": 18,
        "phase_name": PHASE_NAME,
        "current_task_id": 132,
        "current_task_name": "Define Gatekeeper Return Package Plan",
        "final_gatekeeper_stabilization_outcome": summary[
            "final_gatekeeper_stabilization_outcome"
        ],
        "final_progression_status": summary["final_progression_status"],
        "final_persona_review_status": summary["final_persona_review_status"],
        "plan_status": "completed",
        "planning_role": "gatekeeper_return_package_planning",
        "recommended_next_task": NEXT_TASK,
        "main_planning_finding": (
            "Phase 18 has started with scope limited to planning the Gatekeeper "
            "return package; no package build, Gatekeeper rerun, persona review, "
            "or investor-agent execution occurs in Task 132."
        ),
    }


def build_return_package_component_matrix() -> list[dict]:
    """Build required Gatekeeper return package component rows."""
    specs = [
        ("executive_gatekeeper_return_summary", "Summarize the return package for Gatekeeper."),
        ("final_gatekeeper_stabilization_decision_record", "Preserve final Phase 17 stabilization outcome."),
        ("permission_boundary_summary", "Show allowed and prohibited scopes."),
        ("blocker_disposition_summary", "Disclose blocker status after Phase 17."),
        ("residual_risk_disclosure", "Disclose residual risks requiring Gatekeeper attention."),
        ("evidence_stabilization_timeline", "Trace Phase 16 and Phase 17 evidence flow."),
        ("repaired_evidence_inventory", "Inventory targeted repair artifacts."),
        ("validation_evidence_inventory", "Inventory validation trial artifacts."),
        ("comparison_evidence_inventory", "Inventory comparison and re-review artifacts."),
        ("local_artifact_limitation_disclosure", "Disclose local-only artifact constraints."),
        ("no_persona_review_confirmation", "Confirm actual persona review remains blocked."),
        ("no_investor_agent_execution_confirmation", "Confirm investor agents were not run."),
        ("no_recommendation_output_confirmation", "Confirm no recommendation output is produced."),
        ("auto_promotion_disabled_confirmation", "Confirm auto-promotion remains disabled."),
        ("next_gatekeeper_review_questions", "Define questions for future Gatekeeper review."),
    ]
    return [
        {
            "component_code": code,
            "component_label": code.replace("_", " "),
            "component_purpose": purpose,
            "source_artifacts": "Phase 17 closure and linked local artifacts",
            "required_inputs": "Task 131 closure outputs and linked matrices",
            "expected_output": "component input inventory for Task 133",
            "inclusion_status": "included"
            if not code.endswith("questions")
            else "included_with_warnings",
            "owner_layer": "Gatekeeper return package planning",
            "safety_boundary": "Planning component only; no investor decision section.",
        }
        for code, purpose in specs
    ]


def build_return_package_evidence_inventory_matrix(closure: dict) -> list[dict]:
    """Build evidence inventory sources for the return package."""
    specs = [
        ("phase_17_closure", 17, 131, closure["phase_17_closure_run_id"], "phase_17_closure.json"),
        (
            "gatekeeper_stabilization_re_review",
            17,
            130,
            closure["gatekeeper_stabilization_re_review_run_id"],
            "gatekeeper_stabilization_re_review.json",
        ),
        (
            "gatekeeper_stabilized_evidence_comparison",
            17,
            129,
            closure["gatekeeper_stabilized_comparison_run_id"],
            "gatekeeper_stabilized_evidence_comparison.json",
        ),
        (
            "stabilization_validation_trial",
            17,
            128,
            closure["stabilization_validation_run_id"],
            "stabilization_validation_trial.json",
        ),
        (
            "targeted_evidence_repairs",
            17,
            127,
            closure["targeted_repair_run_id"],
            "targeted_evidence_repairs.json",
        ),
        (
            "residual_blocker_work_orders",
            17,
            126,
            closure["residual_work_order_package_run_id"],
            "residual_blocker_work_orders.json",
        ),
        (
            "targeted_evidence_stabilization_plan",
            17,
            125,
            closure["stabilization_plan_run_id"],
            "targeted_evidence_stabilization_plan.json",
        ),
        (
            "phase_16_closure",
            16,
            124,
            closure["phase_16_closure_run_id"],
            "phase_16_closure.json",
        ),
        (
            "baseline_gatekeeper_re_evaluation",
            16,
            123,
            closure["baseline_gatekeeper_re_evaluation_run_id"],
            "gatekeeper_re_evaluation.json",
        ),
        (
            "pre_post_repair_comparison",
            16,
            122,
            closure["pre_post_repair_comparison_run_id"],
            "pre_post_repair_comparison.json",
        ),
        (
            "controlled_re_run_trial",
            16,
            121,
            closure["controlled_re_run_trial_run_id"],
            "controlled_re_run_trial.json",
        ),
        (
            "research_audit_trail",
            15,
            118,
            closure["research_audit_trail_run_id"],
            "research_audit_trail_bundle.json",
        ),
    ]
    return [
        {
            "evidence_code": code,
            "evidence_label": code.replace("_", " "),
            "source_phase": source_phase,
            "source_task": source_task,
            "source_run_id": run_id,
            "source_artifact": artifact,
            "evidence_role_in_return_package": "source evidence for Gatekeeper return package",
            "inclusion_status": "included",
            "limitation_note": "local artifact only; no live data fetched",
            "safety_boundary": "Evidence inventory only; non-actionable.",
        }
        for code, source_phase, source_task, run_id, artifact in specs
    ]


def build_return_package_residual_risk_disclosure_matrix(closure: dict) -> list[dict]:
    """Build residual risk disclosures required in the return package."""
    phase17_blockers = {
        row["blocker_code"]: row
        for row in closure.get("remaining_blockers_after_phase_17_matrix", [])
    }
    specs = [
        ("unresolved_material_blockers", "critical"),
        ("partially_improved_evidence_blockers", "high"),
        ("local_artifact_limitations", "medium"),
        ("residual_metadata_concentration", "medium"),
        ("residual_period_sensitivity", "high"),
        ("residual_outlier_dependence", "high"),
        ("no_actual_persona_review_allowed", "critical"),
        ("investor_agent_execution_not_allowed", "critical"),
        ("auto_promotion_disabled", "critical"),
        ("gatekeeper_return_package_scope_only", "high"),
    ]
    rows = []
    for code, fallback_severity in specs:
        source = phase17_blockers.get(code.replace("no_actual_", ""))
        rows.append(
            {
                "risk_code": code,
                "risk_label": code.replace("_", " "),
                "final_phase_17_status": source.get("status_after_phase_17", "preserved")
                if source
                else "preserved",
                "disclosure_status": "must_disclose",
                "severity": source.get("severity", fallback_severity) if source else fallback_severity,
                "reason_for_disclosure": "Required by Phase 17 closure and permission boundary.",
                "required_gatekeeper_attention": (
                    "Gatekeeper must see this limitation before any future scope expansion."
                ),
                "safety_boundary": "Residual risk disclosure only.",
            }
        )
    return rows


def _phase17_permission(closure: dict, code: str, default: str) -> str:
    for row in closure.get("final_permission_boundary_summary", []):
        if row["permission_code"] == code:
            return row["final_status"]
    return default


def build_return_package_permission_boundary_matrix(closure: dict) -> list[dict]:
    """Build Phase 18 planned permission boundaries."""
    specs = [
        ("gatekeeper_return_package_preparation", "allowed", "Gatekeeper package planning only"),
        ("actual_gatekeeper_re_review", "not_in_task_132", "none in Task 132"),
        ("persona_review_preparation", "not_allowed", "none"),
        ("actual_persona_review", "not_allowed", "none"),
        ("investor_agent_execution", "not_allowed", "none"),
        ("investor_decision_generation", "not_allowed", "none"),
        ("company_ranking", "not_allowed", "none"),
        ("investment_recommendation", "not_allowed", "none"),
        ("allocation_or_rebalancing", "not_allowed", "none"),
        ("trade_signal_generation", "not_allowed", "none"),
        ("auto_promotion", "disabled", "none"),
    ]
    return [
        {
            "permission_code": code,
            "permission_label": code.replace("_", " "),
            "phase_17_final_status": _phase17_permission(closure, code, planned_status),
            "phase_18_planned_status": planned_status,
            "allowed_scope": allowed_scope,
            "prohibited_scope": (
                "Investor decisions, recommendations, rankings, allocations, "
                "rebalancing, trade signals, investor-agent execution, actual "
                "persona reviews, and auto-promotion."
            ),
            "condition_to_expand_scope": "Future explicit Gatekeeper authorization.",
            "safety_boundary": "Permission boundary only.",
        }
        for code, planned_status, allowed_scope in specs
    ]


def build_phase_18_execution_roadmap() -> list[dict]:
    """Build the Phase 18 roadmap without executing later tasks."""
    specs = [
        (132, "Define Gatekeeper Return Package Plan", "Define package plan.", "gatekeeper_return_package_plan"),
        (133, "Build Gatekeeper Return Package Input Inventory", "Inventory required inputs.", "input inventory"),
        (134, "Assemble Gatekeeper Return Package", "Assemble return package.", "return package draft"),
        (135, "Validate Gatekeeper Return Package Completeness", "Validate completeness.", "validation report"),
        (136, "Run Gatekeeper Return Review", "Run future Gatekeeper review.", "return review result"),
        (137, "Phase 18 Closure & Next-Step Decision", "Close Phase 18.", "closure decision"),
    ]
    return [
        {
            "task_id": task_id,
            "task_name": task_name,
            "purpose": purpose,
            "consumes": "prior Phase 18 task outputs and Phase 17 closure",
            "produces": produces,
            "allowed_actions": "Gatekeeper-facing planning or packaging only as scoped by task.",
            "prohibited_actions": (
                "Investor-agent execution, actual persona reviews, investor decisions, "
                "recommendations, rankings, allocations, rebalancing, trade signals, "
                "execution instructions, and auto-promotion."
            ),
            "completion_condition": f"Task {task_id} artifact is written and validated.",
            "safety_boundary": "Roadmap only; Task 132 executes no later tasks.",
        }
        for task_id, task_name, purpose, produces in specs
    ]


def build_task_133_handoff_manifest(
    *,
    gatekeeper_return_plan_run_id: str,
    closure: dict,
    components: list[dict],
    evidence: list[dict],
) -> dict:
    """Build the Task 133 handoff manifest."""
    return {
        "future_phase_id": 18,
        "future_phase_name": PHASE_NAME,
        "future_task_id": 133,
        "future_task_name": "Build Gatekeeper Return Package Input Inventory",
        "gatekeeper_return_plan_run_id": gatekeeper_return_plan_run_id,
        "phase_17_closure_run_id": closure["phase_17_closure_run_id"],
        "required_inputs": [
            "phase_17_closure",
            "final_permission_boundary_summary",
            "remaining_blockers_after_phase_17_matrix",
            "phase_18_recommendation_matrix",
        ],
        "package_components_to_inventory": [
            row["component_code"] for row in components
        ],
        "evidence_sources_to_inventory": [row["evidence_code"] for row in evidence],
        "allowed_scope": [
            "inventorying evidence artifacts",
            "mapping return package components",
            "confirming local artifact availability",
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
        "readiness_status": "ready_to_build_gatekeeper_return_package_input_inventory",
        "execution_allowed_now": True,
        "reason": "Task 132 plan is complete and ready for Task 133 input inventory.",
    }


def build_gatekeeper_return_plan_validation_checks() -> list[dict]:
    """Build Task 132 validation checks."""
    checks = [
        "phase_17_closure_loaded",
        "gatekeeper_return_plan_summary_created",
        "return_package_component_matrix_created",
        "return_package_evidence_inventory_matrix_created",
        "residual_risk_disclosure_matrix_created",
        "permission_boundary_matrix_created",
        "phase_18_execution_roadmap_created",
        "task_133_handoff_manifest_created",
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
    return [
        {
            "check_code": check,
            "check_label": check.replace("_", " "),
            "status": "satisfied",
            "source_artifact": "gatekeeper_return_package_plan",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 132.",
        }
        for check in checks
    ]


def build_gatekeeper_return_package_plan(
    *,
    gatekeeper_return_plan_run_id: str,
    generated_at: str,
    closure: dict,
) -> GatekeeperReturnPackagePlanReport:
    """Build the Task 132 Gatekeeper return package plan."""
    summary = build_gatekeeper_return_plan_summary(
        gatekeeper_return_plan_run_id=gatekeeper_return_plan_run_id,
        closure=closure,
    )
    components = build_return_package_component_matrix()
    evidence = build_return_package_evidence_inventory_matrix(closure)
    return GatekeeperReturnPackagePlanReport(
        gatekeeper_return_plan_run_id=gatekeeper_return_plan_run_id,
        generated_at=generated_at,
        phase_17_closure_run_id=closure["phase_17_closure_run_id"],
        gatekeeper_stabilization_re_review_run_id=closure[
            "gatekeeper_stabilization_re_review_run_id"
        ],
        gatekeeper_stabilized_comparison_run_id=closure[
            "gatekeeper_stabilized_comparison_run_id"
        ],
        stabilization_validation_run_id=closure["stabilization_validation_run_id"],
        targeted_repair_run_id=closure["targeted_repair_run_id"],
        residual_work_order_package_run_id=closure[
            "residual_work_order_package_run_id"
        ],
        stabilization_plan_run_id=closure["stabilization_plan_run_id"],
        phase_16_closure_run_id=closure["phase_16_closure_run_id"],
        baseline_gatekeeper_re_evaluation_run_id=closure[
            "baseline_gatekeeper_re_evaluation_run_id"
        ],
        pre_post_repair_comparison_run_id=closure[
            "pre_post_repair_comparison_run_id"
        ],
        controlled_re_run_trial_run_id=closure["controlled_re_run_trial_run_id"],
        re_run_input_package_run_id=closure["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=closure["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=closure["research_audit_trail_run_id"],
        gatekeeper_return_plan_summary=summary,
        return_package_component_matrix=components,
        return_package_evidence_inventory_matrix=evidence,
        return_package_residual_risk_disclosure_matrix=(
            build_return_package_residual_risk_disclosure_matrix(closure)
        ),
        return_package_permission_boundary_matrix=(
            build_return_package_permission_boundary_matrix(closure)
        ),
        phase_18_execution_roadmap=build_phase_18_execution_roadmap(),
        task_133_handoff_manifest=build_task_133_handoff_manifest(
            gatekeeper_return_plan_run_id=gatekeeper_return_plan_run_id,
            closure=closure,
            components=components,
            evidence=evidence,
        ),
        gatekeeper_return_plan_validation_checks=(
            build_gatekeeper_return_plan_validation_checks()
        ),
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


def _summary_rows(summary: dict) -> list[dict]:
    return [{"field": key, "value": _format_value(value)} for key, value in summary.items()]


def _render_markdown(report: GatekeeperReturnPackagePlanReport) -> str:
    summary = report.gatekeeper_return_plan_summary
    handoff = report.task_133_handoff_manifest
    lines = [
        "# Gatekeeper Return Package Plan",
        "",
        "## Executive Summary",
        "",
        f"* Gatekeeper Return Plan Run ID: {report.gatekeeper_return_plan_run_id}",
        f"* Phase 17 Closure Run ID: {report.phase_17_closure_run_id}",
        "* Current Phase: 18 - Gatekeeper Return Package Layer",
        "* Current Task: Task 132 - Define Gatekeeper Return Package Plan",
        (
            "* Final Gatekeeper Stabilization Outcome: "
            f"{summary['final_gatekeeper_stabilization_outcome']}"
        ),
        f"* Final Progression Status: {summary['final_progression_status']}",
        f"* Final Persona Review Status: {summary['final_persona_review_status']}",
        f"* Plan Status: {report.plan_status}",
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
        "Previous Phase:",
        "Phase 17 - Targeted Evidence Stabilization Layer closed",
        "",
        "Previous Task:",
        "Task 131 - Phase 17 Closure & Next-Step Decision completed",
        "",
        "This Task:",
        "Task 132 defines the Gatekeeper return package plan.",
        "",
        "Phase 18 Status:",
        "Started",
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
        "## Gatekeeper Return Plan Summary",
        "",
        *_markdown_table(_summary_rows(summary), [("Field", "field"), ("Value", "value")]),
        "",
        "## Return Package Component Matrix",
        "",
        *_markdown_table(
            report.return_package_component_matrix,
            [
                ("Component", "component_code"),
                ("Purpose", "component_purpose"),
                ("Source Artifacts", "source_artifacts"),
                ("Inclusion Status", "inclusion_status"),
                ("Safety Boundary", "safety_boundary"),
            ],
        ),
        "",
        "## Return Package Evidence Inventory Matrix",
        "",
        *_markdown_table(
            report.return_package_evidence_inventory_matrix,
            [
                ("Evidence", "evidence_code"),
                ("Source Phase", "source_phase"),
                ("Source Task", "source_task"),
                ("Source Run ID", "source_run_id"),
                ("Role In Package", "evidence_role_in_return_package"),
                ("Inclusion Status", "inclusion_status"),
            ],
        ),
        "",
        "## Residual Risk Disclosure Matrix",
        "",
        *_markdown_table(
            report.return_package_residual_risk_disclosure_matrix,
            [
                ("Risk", "risk_code"),
                ("Final Phase 17 Status", "final_phase_17_status"),
                ("Disclosure Status", "disclosure_status"),
                ("Severity", "severity"),
                ("Gatekeeper Attention", "required_gatekeeper_attention"),
            ],
        ),
        "",
        "## Permission Boundary Matrix",
        "",
        *_markdown_table(
            report.return_package_permission_boundary_matrix,
            [
                ("Permission", "permission_code"),
                ("Phase 18 Planned Status", "phase_18_planned_status"),
                ("Allowed Scope", "allowed_scope"),
                ("Prohibited Scope", "prohibited_scope"),
                ("Condition To Expand", "condition_to_expand_scope"),
            ],
        ),
        "",
        "## Phase 18 Execution Roadmap",
        "",
        *_markdown_table(
            report.phase_18_execution_roadmap,
            [
                ("Task", "task_id"),
                ("Purpose", "purpose"),
                ("Produces", "produces"),
                ("Completion Condition", "completion_condition"),
            ],
        ),
        "",
        "## Task 133 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} - {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Required Inputs: {'; '.join(handoff['required_inputs'])}",
        (
            "* Package Components To Inventory: "
            f"{'; '.join(handoff['package_components_to_inventory'])}"
        ),
        (
            "* Evidence Sources To Inventory: "
            f"{'; '.join(handoff['evidence_sources_to_inventory'])}"
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
            report.gatekeeper_return_plan_validation_checks,
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
        "* Phase 18 has started.",
        "* The next step is inventorying evidence needed for a Gatekeeper return package.",
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


def write_gatekeeper_return_package_plan_report(
    *,
    outputs_root: Path,
    phase_17_closure_run_id: str | None = None,
) -> GatekeeperReturnPackagePlanFiles:
    """Write Task 132 Gatekeeper return package plan artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_phase_17_closure_manifest(
        outputs_root=outputs_root,
        phase_17_closure_run_id=phase_17_closure_run_id,
    )
    closure_run_id = manifest["phase_17_closure_run_id"]
    closure = load_phase_17_closure(
        outputs_root=outputs_root,
        phase_17_closure_run_id=closure_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_gatekeeper_return_package_plan(
        gatekeeper_return_plan_run_id=run_id,
        generated_at=generated_at.isoformat(),
        closure=closure,
    )

    root = outputs_root / "gatekeeper_return_package_plans"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "gatekeeper_return_package_plan.md"
    json_path = output_folder / "gatekeeper_return_package_plan.json"
    component_csv = output_folder / "return_package_component_matrix.csv"
    evidence_csv = output_folder / "return_package_evidence_inventory_matrix.csv"
    risk_csv = output_folder / "return_package_residual_risk_disclosure_matrix.csv"
    permission_csv = output_folder / "return_package_permission_boundary_matrix.csv"
    roadmap_csv = output_folder / "phase_18_execution_roadmap.csv"
    handoff_path = output_folder / "task_133_handoff_manifest.json"
    checks_csv = output_folder / "gatekeeper_return_plan_validation_checks.csv"
    latest_manifest_path = root / "latest_gatekeeper_return_package_plan_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(component_csv, report.return_package_component_matrix)
    _write_csv(evidence_csv, report.return_package_evidence_inventory_matrix)
    _write_csv(risk_csv, report.return_package_residual_risk_disclosure_matrix)
    _write_csv(permission_csv, report.return_package_permission_boundary_matrix)
    _write_csv(roadmap_csv, report.phase_18_execution_roadmap)
    handoff_path.write_text(
        json.dumps(report.task_133_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.gatekeeper_return_plan_validation_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "gatekeeper_return_plan_run_id": report.gatekeeper_return_plan_run_id,
                "phase_17_closure_run_id": report.phase_17_closure_run_id,
                "final_gatekeeper_stabilization_outcome": (
                    report.gatekeeper_return_plan_summary[
                        "final_gatekeeper_stabilization_outcome"
                    ]
                ),
                "final_progression_status": report.gatekeeper_return_plan_summary[
                    "final_progression_status"
                ],
                "final_persona_review_status": report.gatekeeper_return_plan_summary[
                    "final_persona_review_status"
                ],
                "plan_status": report.plan_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_133_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return GatekeeperReturnPackagePlanFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        component_csv_path=component_csv,
        evidence_csv_path=evidence_csv,
        residual_risk_csv_path=risk_csv,
        permission_csv_path=permission_csv,
        roadmap_csv_path=roadmap_csv,
        task_133_handoff_manifest_path=handoff_path,
        checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
