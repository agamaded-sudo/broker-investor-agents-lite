"""Task 119 re-run and re-gate planning report."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report is a planning document only. It does not execute a re-run, "
    "rerun Gatekeeper, allow persona review, create investor decisions, "
    "recommendations, rankings, allocation instructions, rebalancing "
    "instructions, trade signals, execution instructions, strategy validation, "
    "or investment advice."
)
NEXT_TASK = "Task 120 - Build Re-Run Input Package"
NEXT_PHASE_STEP = "Build controlled re-run input package"


@dataclass(frozen=True)
class ReRunReGatePlanReport:
    """Structured Task 119 plan report."""

    re_run_re_gate_plan_run_id: str
    generated_at: str
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
    gatekeeper_run_id: str
    scorecard_run_id: str
    analysis_run_id: str
    expanded_trial_run_id: str
    backtest_run_id: str
    phase_16_context: dict
    re_run_scope_matrix: list[dict]
    controlled_trial_plan: dict
    gatekeeper_rerun_criteria: list[dict]
    phase_16_task_roadmap: list[dict]
    re_gate_decision_branches: list[dict]
    safety_plan: list[dict]
    plan_status: str
    recommended_next_task: str
    recommended_next_phase_step: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class ReRunReGatePlanFiles:
    """Generated Task 119 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    scope_matrix_csv_path: Path
    controlled_trial_plan_path: Path
    gatekeeper_criteria_csv_path: Path
    roadmap_csv_path: Path
    decision_branches_csv_path: Path
    safety_plan_csv_path: Path
    latest_manifest_path: Path
    report: ReRunReGatePlanReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_research_audit_trail_manifest(
    *,
    outputs_root: Path,
    research_audit_trail_run_id: str | None = None,
) -> dict:
    """Load one Task 118 report or the latest Task 118 manifest."""
    root = Path(outputs_root) / "research_audit_trail_bundles"
    path = (
        root
        / research_audit_trail_run_id
        / "research_audit_trail_bundle.json"
        if research_audit_trail_run_id
        else root / "latest_research_audit_trail_bundle_manifest.json"
    )
    label = (
        "Research audit trail report"
        if research_audit_trail_run_id
        else "Research audit trail manifest"
    )
    return _load_required_json(path, label)


def load_research_audit_trail_bundle(
    *,
    outputs_root: Path,
    research_audit_trail_run_id: str,
) -> dict:
    """Load the Task 118 audit bundle for a run id."""
    path = (
        Path(outputs_root)
        / "research_audit_trail_bundles"
        / research_audit_trail_run_id
        / "research_audit_trail_bundle.json"
    )
    return _load_required_json(path, "Research audit trail report")


def build_phase_16_context(*, audit: dict) -> dict:
    """Build Phase 16 context for Task 119."""
    phase = audit.get("phase_closure_summary", {})
    return {
        "phase_id": 16,
        "phase_name": "Re-Run & Re-Gate Layer",
        "previous_phase_id": 15,
        "previous_phase_name": "Backoffice Repair Execution Layer",
        "previous_phase_status": phase.get(
            "phase_status", "completed_after_audit_bundle"
        ),
        "source_research_audit_trail_run_id": audit["research_audit_trail_run_id"],
        "gatekeeper_decision": "hold",
        "progression_allowed": False,
        "persona_reviews_allowed": False,
        "current_task_id": 119,
        "current_task_name": "Define Re-Run & Re-Gate Plan",
        "current_task_role": "phase_16_planning",
        "phase_entry_finding": "Phase 15 audit trail completed; evidence remains held.",
        "next_task_id": 120,
        "next_task_name": "Build Re-Run Input Package",
    }


def build_re_run_scope_matrix() -> list[dict]:
    """Build the required re-run scope matrix."""
    rows = [
        ("full_sample_re_run", "Run full sample in controlled future task."),
        ("clean_only_re_run", "Separate clean evidence in future re-run."),
        ("warning_only_re_run", "Separate warning evidence in future re-run."),
        ("clean_vs_warning_split", "Preserve clean versus warning reporting."),
        ("clean_anchor_vs_delayed_anchor_split", "Separate anchor quality views."),
        ("current_core_vs_expanded_cohort_split", "Keep cohorts separated."),
        ("ex_nvda_control", "Retain Ex-NVDA control."),
        ("ex_top_contributor_control", "Retain ex-top-contributor controls."),
        ("ex_supportive_date_control", "Control supportive date dependence."),
        ("metadata_concentration_disclosure", "Disclose metadata concentration."),
        ("benchmark_relative_reporting", "Report benchmark-relative outcomes."),
        ("walk_forward_reporting", "Report walk-forward behavior."),
        ("outlier_dependence_reporting", "Report outlier dependence."),
        ("persona_evidence_requirement_linkage", "Link persona requirements."),
        ("bogle_index_comparison_linkage", "Link Bogle benchmark pack."),
        ("fisher_qualitative_requirements_linkage", "Link Fisher pack."),
        ("buffett_munger_quality_risk_linkage", "Link Buffett/Munger pack."),
        (
            "no_persona_review_before_gatekeeper_allows",
            "Preserve persona review block.",
        ),
    ]
    return [
        {
            "scope_area": area,
            "included_in_plan": True,
            "reason": reason,
            "source_artifact": "research_audit_trail_bundle",
            "required_control": area,
            "expected_output_in_future_task": "Task 120 input package or Task 121 controlled trial output",
            "safety_boundary": "Planning only; no re-run is executed in Task 119.",
        }
        for area, reason in rows
    ]


def build_controlled_trial_plan(*, audit: dict) -> dict:
    """Build the controlled future trial plan."""
    return {
        "controlled_trial_plan_id": "phase_16_controlled_re_run_plan",
        "purpose": "Define controlled re-run requirements without executing them.",
        "source_backtest_run_id": audit["backtest_run_id"],
        "source_expanded_trial_run_id": audit["expanded_trial_run_id"],
        "source_research_audit_trail_run_id": audit["research_audit_trail_run_id"],
        "proposed_trial_mode": "controlled_re_run_only",
        "required_controls": [
            "full_sample",
            "clean_only",
            "warning_only",
            "current_core",
            "expanded_cohort",
            "ex_nvda",
            "ex_top_contributors",
            "ex_supportive_date",
            "clean_anchor",
            "delayed_anchor",
            "benchmark_relative",
            "walk_forward",
            "metadata_concentration",
        ],
        "prohibited_outputs": [
            "investment_decision",
            "buy_sell_hold_recommendation",
            "ranking",
            "allocation",
            "rebalancing_instruction",
            "trade_signal",
            "execution_instruction",
        ],
        "expected_future_task": "Task 121 - Execute Controlled Re-Run Trial",
        "readiness_status": "planned_not_executed",
    }


def build_gatekeeper_rerun_criteria() -> list[dict]:
    """Build criteria required before a future Gatekeeper rerun."""
    criteria = [
        "controlled_re_run_completed",
        "pre_post_repair_comparison_completed",
        "clean_vs_warning_split_reported",
        "anchor_split_reported",
        "current_core_expanded_cohort_split_reported",
        "outlier_controls_reported",
        "supportive_date_control_reported",
        "metadata_concentration_disclosed",
        "persona_review_block_preserved",
        "safety_ledger_clear",
        "no_recommendation_outputs_confirmed",
    ]
    satisfied = {
        "persona_review_block_preserved",
        "safety_ledger_clear",
        "no_recommendation_outputs_confirmed",
    }
    return [
        {
            "criteria_code": code,
            "criteria_label": code.replace("_", " "),
            "current_status": "satisfied" if code in satisfied else "planned_not_completed",
            "required_before_gatekeeper_rerun": code not in satisfied,
            "source_artifact": "research_audit_trail_bundle",
            "reason": "Required before Task 123 can rerun Gatekeeper.",
            "pass_condition": f"{code} is documented and complete.",
            "failure_condition": f"{code} is missing, incomplete, or violates safety boundaries.",
        }
        for code in criteria
    ]


def build_phase_16_task_roadmap() -> list[dict]:
    """Build the Phase 16 task roadmap."""
    tasks = [
        (119, "Define Re-Run & Re-Gate Plan", "phase_16_planning", "Task 118", "re_run_re_gate_plan", "completed", False),
        (120, "Build Re-Run Input Package", "input_package", "Task 119", "re_run_input_package", "planned", False),
        (121, "Execute Controlled Re-Run Trial", "controlled_re_run", "Task 120", "controlled_re_run_trial", "planned", False),
        (122, "Compare Pre-Repair vs Post-Repair Evidence", "comparison", "Task 121", "pre_post_repair_comparison", "planned", False),
        (123, "Run Gatekeeper Re-Evaluation", "gatekeeper_rerun", "Tasks 121 and 122", "gatekeeper_re_evaluation", "planned", True),
        (124, "Phase 16 Closure & Next-Phase Recommendation", "phase_closure", "Task 123", "phase_16_closure", "planned", False),
    ]
    return [
        {
            "task_id": task_id,
            "task_name": name,
            "phase_id": 16,
            "task_role": role,
            "depends_on": depends_on,
            "expected_artifact": artifact,
            "execution_status": status,
            "allows_gatekeeper_rerun": allows_gatekeeper,
            "allows_persona_review": False,
            "safety_boundary": (
                "Persona review remains blocked unless a future Gatekeeper "
                "decision allows it after Task 123."
            ),
        }
        for task_id, name, role, depends_on, artifact, status, allows_gatekeeper in tasks
    ]


def build_re_gate_decision_branches() -> list[dict]:
    """Build future planning branches for Task 123/124."""
    rows = [
        ("hold_continues", "hold", "Gatekeeper continues hold.", "deeper_repair_phase"),
        (
            "hold_with_repair_progress",
            "hold_with_progress",
            "Evidence improved but remains held.",
            "additional_repair_or_retest",
        ),
        (
            "pass_with_warnings",
            "proceed_with_warnings",
            "Gatekeeper permits limited progression with warnings.",
            "limited_review_preparation",
        ),
        (
            "research_ready_for_limited_persona_review",
            "limited_persona_review_allowed",
            "Future Gatekeeper permits limited persona review.",
            "persona_review_preparation",
        ),
        ("block", "block", "Gatekeeper blocks progression.", "blocked_research_state"),
        (
            "insufficient_re_run_evidence",
            "insufficient_evidence",
            "Re-run evidence is incomplete.",
            "input_repair_phase",
        ),
    ]
    return [
        {
            "branch_code": code,
            "future_gatekeeper_outcome": outcome,
            "meaning": meaning,
            "allowed_next_phase": next_phase,
            "blocked_actions": "recommendations;rankings;allocations;trade_signals;execution_instructions",
            "required_follow_up": "Document future Gatekeeper result before any progression.",
        }
        for code, outcome, meaning, next_phase in rows
    ]


def build_safety_plan() -> list[dict]:
    """Build Task 119 safety plan rows."""
    rules = [
        "no_investment_decision",
        "no_buy_sell_hold_recommendation",
        "no_ranking",
        "no_consensus",
        "no_allocation",
        "no_rebalancing",
        "no_trade_signal",
        "no_execution_instruction",
        "no_persona_review_before_gatekeeper_allows",
        "gatekeeper_hold_respected",
        "no_gatekeeper_rerun_in_task_119",
        "no_network_calls",
    ]
    return [
        {
            "safety_rule": rule,
            "current_status": "satisfied",
            "enforcement_method": "Task 119 is planning-only and produces no execution outputs.",
            "source_artifact": "research_audit_trail_bundle",
            "applies_to_tasks": "119-124",
            "violation_found": False,
        }
        for rule in rules
    ]


def build_re_run_re_gate_plan(
    *,
    re_run_re_gate_plan_run_id: str,
    generated_at: str,
    audit: dict,
) -> ReRunReGatePlanReport:
    """Build Task 119 re-run and re-gate plan."""
    return ReRunReGatePlanReport(
        re_run_re_gate_plan_run_id=re_run_re_gate_plan_run_id,
        generated_at=generated_at,
        research_audit_trail_run_id=audit["research_audit_trail_run_id"],
        buffett_munger_pack_run_id=audit["buffett_munger_pack_run_id"],
        fisher_growth_pack_run_id=audit["fisher_growth_pack_run_id"],
        bogle_benchmark_pack_run_id=audit["bogle_benchmark_pack_run_id"],
        persona_evidence_pack_run_id=audit["persona_evidence_pack_run_id"],
        metadata_diversity_recheck_run_id=audit["metadata_diversity_recheck_run_id"],
        delayed_anchor_repair_run_id=audit["delayed_anchor_repair_run_id"],
        walk_forward_repair_run_id=audit["walk_forward_repair_run_id"],
        outlier_repair_run_id=audit["outlier_repair_run_id"],
        decomposition_run_id=audit["decomposition_run_id"],
        backoffice_attribution_run_id=audit["backoffice_attribution_run_id"],
        investor_persona_attribution_run_id=audit["investor_persona_attribution_run_id"],
        gatekeeper_run_id=audit["gatekeeper_run_id"],
        scorecard_run_id=audit["scorecard_run_id"],
        analysis_run_id=audit["analysis_run_id"],
        expanded_trial_run_id=audit["expanded_trial_run_id"],
        backtest_run_id=audit["backtest_run_id"],
        phase_16_context=build_phase_16_context(audit=audit),
        re_run_scope_matrix=build_re_run_scope_matrix(),
        controlled_trial_plan=build_controlled_trial_plan(audit=audit),
        gatekeeper_rerun_criteria=build_gatekeeper_rerun_criteria(),
        phase_16_task_roadmap=build_phase_16_task_roadmap(),
        re_gate_decision_branches=build_re_gate_decision_branches(),
        safety_plan=build_safety_plan(),
        plan_status="completed",
        recommended_next_task=NEXT_TASK,
        recommended_next_phase_step=NEXT_PHASE_STEP,
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


def _render_markdown(report: ReRunReGatePlanReport) -> str:
    context = report.phase_16_context
    trial = report.controlled_trial_plan
    lines = [
        "# Re-Run & Re-Gate Plan",
        "",
        "## Executive Summary",
        "",
        f"* Re-Run & Re-Gate Plan Run ID: {report.re_run_re_gate_plan_run_id}",
        f"* Research Audit Trail Run ID: {report.research_audit_trail_run_id}",
        f"* Current Phase: {context['phase_name']}",
        f"* Current Task: {context['current_task_name']}",
        f"* Gatekeeper Decision: {context['gatekeeper_decision']}",
        f"* Progression Allowed: {str(context['progression_allowed']).lower()}",
        f"* Persona Reviews Allowed: {str(context['persona_reviews_allowed']).lower()}",
        f"* Plan Status: {report.plan_status}",
        f"* Recommended Next Task: {report.recommended_next_task}",
        "",
        "## Important Boundary",
        "",
        (
            "This report is a planning document only. It does not execute a "
            "re-run, rerun Gatekeeper, allow persona review, create investor "
            "decisions, rankings, recommendations, allocations, rebalancing "
            "instructions, trade signals, or execution instructions."
        ),
        "",
        "## Where We Are Now",
        "",
        "Current Phase:",
        "16 - Re-Run & Re-Gate Layer",
        "",
        "Previous Phase:",
        "15 - Backoffice Repair Execution Layer completed_after_audit_bundle",
        "",
        "Direct Next:",
        "Task 120 - Build Re-Run Input Package",
        "",
        "This Task:",
        "Task 119 is the first task in Phase 16.",
        "",
        "Phase 16 Expected Final Task:",
        "Task 124 - Phase 16 Closure & Next-Phase Recommendation",
        "",
        "## Phase 16 Context",
        "",
        f"* Phase ID: {context['phase_id']}",
        f"* Phase Name: {context['phase_name']}",
        f"* Previous Phase ID: {context['previous_phase_id']}",
        f"* Previous Phase Status: {context['previous_phase_status']}",
        f"* Current Task ID: {context['current_task_id']}",
        f"* Next Task ID: {context['next_task_id']}",
        f"* Phase Entry Finding: {context['phase_entry_finding']}",
        "",
        "## Re-Run Scope Matrix",
        "",
        *_markdown_table(
            report.re_run_scope_matrix,
            [
                ("Scope Area", "scope_area"),
                ("Included", "included_in_plan"),
                ("Reason", "reason"),
                ("Required Control", "required_control"),
                ("Future Output", "expected_output_in_future_task"),
            ],
        ),
        "",
        "## Controlled Trial Plan",
        "",
        f"* Proposed Trial Mode: {trial['proposed_trial_mode']}",
        f"* Required Controls: {'; '.join(trial['required_controls'])}",
        f"* Prohibited Outputs: {'; '.join(trial['prohibited_outputs'])}",
        f"* Readiness Status: {trial['readiness_status']}",
        "",
        "## Gatekeeper Rerun Criteria",
        "",
        *_markdown_table(
            report.gatekeeper_rerun_criteria,
            [
                ("Criteria", "criteria_code"),
                ("Status", "current_status"),
                ("Required Before Rerun", "required_before_gatekeeper_rerun"),
                ("Pass Condition", "pass_condition"),
                ("Failure Condition", "failure_condition"),
            ],
        ),
        "",
        "## Phase 16 Task Roadmap",
        "",
        *_markdown_table(
            report.phase_16_task_roadmap,
            [
                ("Task", "task_id"),
                ("Role", "task_role"),
                ("Depends On", "depends_on"),
                ("Status", "execution_status"),
                ("Allows Gatekeeper Rerun", "allows_gatekeeper_rerun"),
                ("Allows Persona Review", "allows_persona_review"),
            ],
        ),
        "",
        "## Future Re-Gate Decision Branches",
        "",
        *_markdown_table(
            report.re_gate_decision_branches,
            [
                ("Branch", "branch_code"),
                ("Future Outcome", "future_gatekeeper_outcome"),
                ("Meaning", "meaning"),
                ("Allowed Next Phase", "allowed_next_phase"),
                ("Blocked Actions", "blocked_actions"),
            ],
        ),
        "",
        "## Safety Plan",
        "",
        *_markdown_table(
            report.safety_plan,
            [
                ("Safety Rule", "safety_rule"),
                ("Status", "current_status"),
                ("Enforcement", "enforcement_method"),
                ("Violation Found", "violation_found"),
            ],
        ),
        "",
        "## What This Suggests",
        "",
        "* Phase 16 has begun.",
        "* Re-run and re-gate planning is now documented.",
        "* Task 120 should build the controlled input package.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not execute the re-run.",
        "* It does not rerun Gatekeeper.",
        "* It does not allow persona review.",
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


def write_re_run_re_gate_plan_report(
    *,
    outputs_root: Path,
    research_audit_trail_run_id: str | None = None,
) -> ReRunReGatePlanFiles:
    """Write Task 119 plan artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_research_audit_trail_manifest(
        outputs_root=outputs_root,
        research_audit_trail_run_id=research_audit_trail_run_id,
    )
    audit_run_id = manifest["research_audit_trail_run_id"]
    audit = load_research_audit_trail_bundle(
        outputs_root=outputs_root,
        research_audit_trail_run_id=audit_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    plan_run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_re_run_re_gate_plan(
        re_run_re_gate_plan_run_id=plan_run_id,
        generated_at=generated_at.isoformat(),
        audit=audit,
    )

    root = outputs_root / "re_run_re_gate_plans"
    output_folder = root / plan_run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "re_run_re_gate_plan.md"
    json_path = output_folder / "re_run_re_gate_plan.json"
    scope_matrix_csv_path = output_folder / "re_run_scope_matrix.csv"
    controlled_trial_plan_path = output_folder / "controlled_trial_plan.json"
    gatekeeper_criteria_csv_path = output_folder / "gatekeeper_rerun_criteria.csv"
    roadmap_csv_path = output_folder / "phase_16_task_roadmap.csv"
    decision_branches_csv_path = output_folder / "re_gate_decision_branches.csv"
    safety_plan_csv_path = output_folder / "safety_plan.csv"
    latest_manifest_path = root / "latest_re_run_re_gate_plan_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(scope_matrix_csv_path, report.re_run_scope_matrix)
    controlled_trial_plan_path.write_text(
        json.dumps(report.controlled_trial_plan, indent=2),
        encoding="utf-8",
    )
    _write_csv(gatekeeper_criteria_csv_path, report.gatekeeper_rerun_criteria)
    _write_csv(roadmap_csv_path, report.phase_16_task_roadmap)
    _write_csv(decision_branches_csv_path, report.re_gate_decision_branches)
    _write_csv(safety_plan_csv_path, report.safety_plan)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "re_run_re_gate_plan_run_id": report.re_run_re_gate_plan_run_id,
                "research_audit_trail_run_id": report.research_audit_trail_run_id,
                "buffett_munger_pack_run_id": report.buffett_munger_pack_run_id,
                "fisher_growth_pack_run_id": report.fisher_growth_pack_run_id,
                "bogle_benchmark_pack_run_id": report.bogle_benchmark_pack_run_id,
                "persona_evidence_pack_run_id": report.persona_evidence_pack_run_id,
                "metadata_diversity_recheck_run_id": (
                    report.metadata_diversity_recheck_run_id
                ),
                "delayed_anchor_repair_run_id": report.delayed_anchor_repair_run_id,
                "walk_forward_repair_run_id": report.walk_forward_repair_run_id,
                "outlier_repair_run_id": report.outlier_repair_run_id,
                "decomposition_run_id": report.decomposition_run_id,
                "backoffice_attribution_run_id": report.backoffice_attribution_run_id,
                "investor_persona_attribution_run_id": (
                    report.investor_persona_attribution_run_id
                ),
                "gatekeeper_run_id": report.gatekeeper_run_id,
                "scorecard_run_id": report.scorecard_run_id,
                "analysis_run_id": report.analysis_run_id,
                "expanded_trial_run_id": report.expanded_trial_run_id,
                "backtest_run_id": report.backtest_run_id,
                "plan_status": report.plan_status,
                "recommended_next_task": report.recommended_next_task,
                "recommended_next_phase_step": report.recommended_next_phase_step,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "scope_matrix_csv_path": str(scope_matrix_csv_path),
                "controlled_trial_plan_path": str(controlled_trial_plan_path),
                "gatekeeper_criteria_csv_path": str(gatekeeper_criteria_csv_path),
                "roadmap_csv_path": str(roadmap_csv_path),
                "decision_branches_csv_path": str(decision_branches_csv_path),
                "safety_plan_csv_path": str(safety_plan_csv_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return ReRunReGatePlanFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        scope_matrix_csv_path=scope_matrix_csv_path,
        controlled_trial_plan_path=controlled_trial_plan_path,
        gatekeeper_criteria_csv_path=gatekeeper_criteria_csv_path,
        roadmap_csv_path=roadmap_csv_path,
        decision_branches_csv_path=decision_branches_csv_path,
        safety_plan_csv_path=safety_plan_csv_path,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
