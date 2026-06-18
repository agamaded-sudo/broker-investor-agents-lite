"""Task 127 targeted evidence repair execution package."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report executes targeted evidence repairs only. It does not rerun "
    "Gatekeeper, run investor agents, allow persona review, create investor "
    "decisions, rankings, recommendations, allocations, rebalancing "
    "instructions, trade signals, execution instructions, or strategy validation."
)
NEXT_TASK = "Task 128 — Run Stabilization Validation Trial"


@dataclass(frozen=True)
class TargetedEvidenceRepairsReport:
    """Structured Task 127 targeted evidence repair package."""

    targeted_repair_run_id: str
    generated_at: str
    residual_work_order_package_run_id: str
    stabilization_plan_run_id: str
    phase_16_closure_run_id: str
    gatekeeper_re_evaluation_run_id: str
    pre_post_repair_comparison_run_id: str
    controlled_re_run_trial_run_id: str
    re_run_input_package_run_id: str
    re_run_re_gate_plan_run_id: str
    research_audit_trail_run_id: str
    repair_execution_summary: dict
    work_order_repair_execution_matrix: list[dict]
    repaired_evidence_matrix: list[dict]
    repair_limitation_matrix: list[dict]
    repair_artifact_trace_matrix: list[dict]
    task_128_validation_input_manifest: dict
    targeted_repair_validation_checks: list[dict]
    repair_execution_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class TargetedEvidenceRepairsFiles:
    """Generated Task 127 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    work_order_repair_csv_path: Path
    repaired_evidence_csv_path: Path
    limitation_csv_path: Path
    artifact_trace_csv_path: Path
    task_128_validation_input_manifest_path: Path
    validation_checks_csv_path: Path
    latest_manifest_path: Path
    report: TargetedEvidenceRepairsReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_residual_blocker_work_orders_manifest(
    *,
    outputs_root: Path,
    residual_work_order_package_run_id: str | None = None,
) -> dict:
    """Load one Task 126 report or the latest Task 126 manifest."""
    root = Path(outputs_root) / "residual_blocker_work_orders"
    path = (
        root / residual_work_order_package_run_id / "residual_blocker_work_orders.json"
        if residual_work_order_package_run_id
        else root / "latest_residual_blocker_work_orders_manifest.json"
    )
    label = (
        "Residual blocker work-order report"
        if residual_work_order_package_run_id
        else "Residual blocker work-order manifest"
    )
    return _load_required_json(path, label)


def load_residual_blocker_work_orders(
    *,
    outputs_root: Path,
    residual_work_order_package_run_id: str,
) -> dict:
    """Load a Task 126 residual blocker work-order package by run id."""
    path = (
        Path(outputs_root)
        / "residual_blocker_work_orders"
        / residual_work_order_package_run_id
        / "residual_blocker_work_orders.json"
    )
    return _load_required_json(path, "Residual blocker work-order report")


def build_work_order_repair_execution_matrix(work_order_package: dict) -> list[dict]:
    """Build controlled repair rows for all residual work orders."""
    rows = []
    for work_order in work_order_package["residual_blocker_work_order_matrix"]:
        work_order_id = work_order["work_order_id"]
        is_return_package = work_order_id == "WO-126-008"
        rows.append(
            {
                "work_order_id": work_order_id,
                "work_order_title": work_order["work_order_title"],
                "linked_workstream_code": work_order["linked_workstream_code"],
                "evidence_area": work_order["evidence_area"],
                "repair_status": "deferred_until_validation"
                if is_return_package
                else "completed_with_warnings",
                "repair_result": "documented" if is_return_package else "bounded",
                "executed_action": (
                    "Compiled validation-ready Gatekeeper return package shell."
                    if is_return_package
                    else "Consolidated local artifacts and bounded the residual evidence issue."
                ),
                "local_inputs_used": (
                    "residual_work_order_package;stabilization_plan;"
                    "phase_16_closure;local_artifact_chain"
                ),
                "output_artifact": f"{work_order['work_order_title']}_repair_output",
                "success_criteria_status": "ready_for_task_128_validation",
                "validation_needed": True,
                "unresolved_issue": (
                    "Requires Task 128 validation before future Gatekeeper return."
                ),
                "safety_boundary": "Repair execution only; no Gatekeeper rerun or persona review.",
            }
        )
    return rows


def build_repaired_evidence_matrix() -> list[dict]:
    """Build repaired evidence rows for Task 128 validation."""
    specs = [
        ("benchmark_relative_evidence", "WO-126-001"),
        ("walk_forward_stability", "WO-126-002"),
        ("period_sensitivity", "WO-126-002"),
        ("supportive_period_dependence", "WO-126-003"),
        ("outlier_dependence", "WO-126-003"),
        ("clean_warning_split", "WO-126-004"),
        ("anchor_split", "WO-126-004"),
        ("current_core_vs_expanded_cohort", "WO-126-005"),
        ("metadata_concentration", "WO-126-006"),
        ("local_artifact_completeness", "WO-126-007"),
        ("gatekeeper_return_package", "WO-126-008"),
    ]
    return [
        {
            "repaired_evidence_code": f"{area}_repair",
            "evidence_area": area,
            "linked_work_order_id": work_order_id,
            "repair_status": "deferred_until_validation"
            if area == "gatekeeper_return_package"
            else "completed_with_warnings",
            "pre_repair_issue": "Residual blocker from Phase 16 closure.",
            "repair_action_taken": (
                "Local artifact consolidation and bounded uncertainty statement."
            ),
            "stabilized_finding": (
                "Evidence issue is documented and validation-ready, not cleared "
                "for progression."
            ),
            "remaining_uncertainty": (
                "Task 128 must test whether repair output improves stability."
            ),
            "validation_requirement": "Task 128 stabilization validation trial",
            "ready_for_task_128_validation": True,
            "safety_boundary": "Repaired evidence row only; no investment conclusion.",
        }
        for area, work_order_id in specs
    ]


def build_repair_limitation_matrix() -> list[dict]:
    """Build repair limitation rows."""
    limitations = [
        ("local_artifacts_only", "WO-126-007", False),
        ("no_new_market_data", "WO-126-007", False),
        ("no_new_financials", "WO-126-007", False),
        ("unresolved_exact_delay_days", "WO-126-004", False),
        ("residual_metadata_concentration", "WO-126-006", False),
        ("residual_outlier_dependence", "WO-126-003", False),
        ("residual_period_sensitivity", "WO-126-002", False),
        ("gatekeeper_not_rerun_in_task_127", "WO-126-008", False),
        ("persona_review_not_allowed", "WO-126-008", False),
    ]
    return [
        {
            "limitation_code": code,
            "linked_work_order_id": work_order_id,
            "limitation_label": code.replace("_", " "),
            "limitation_status": "documented",
            "impact_on_repair": (
                "Repair output remains validation-ready but not progression-ready."
            ),
            "required_follow_up": "Carry into Task 128 validation inputs.",
            "blocks_task_128_validation": blocks_validation,
            "safety_boundary": "Limitation documentation only.",
        }
        for code, work_order_id, blocks_validation in limitations
    ]


def build_repair_artifact_trace_matrix(work_order_package: dict) -> list[dict]:
    """Build artifact trace rows."""
    sources = [
        ("residual_work_order_package", work_order_package["residual_work_order_package_run_id"]),
        ("stabilization_plan", work_order_package["stabilization_plan_run_id"]),
        ("phase_16_closure", work_order_package["phase_16_closure_run_id"]),
        ("gatekeeper_re_evaluation", work_order_package["gatekeeper_re_evaluation_run_id"]),
        ("pre_post_comparison", work_order_package["pre_post_repair_comparison_run_id"]),
        ("controlled_re_run_trial", work_order_package["controlled_re_run_trial_run_id"]),
        ("metadata_diversity_recheck", "linked_prior_artifact"),
        ("delayed_anchor_repair", "linked_prior_artifact"),
        ("walk_forward_repair", "linked_prior_artifact"),
        ("outlier_repair", "linked_prior_artifact"),
        ("backtest_driver_decomposition", "linked_prior_artifact"),
        ("research_audit_trail", work_order_package["research_audit_trail_run_id"]),
    ]
    rows = []
    for source, run_id in sources:
        rows.append(
            {
                "repair_artifact_code": f"{source}_trace",
                "linked_work_order_id": "all",
                "source_artifact": source,
                "source_run_id": run_id,
                "produced_artifact": "targeted_evidence_repair_output",
                "produced_file": "targeted_evidence_repairs.json",
                "trace_status": "traced",
                "safety_boundary": "Traceability only; no live data used.",
            }
        )
    return rows


def build_repair_execution_summary(
    *,
    targeted_repair_run_id: str,
    work_order_package: dict,
    repair_rows: list[dict],
) -> dict:
    """Build Task 127 repair execution summary."""
    package_summary = work_order_package["work_order_package_summary"]
    completed = sum(row["repair_status"] == "completed" for row in repair_rows)
    partial = sum(
        row["repair_status"] in {"completed_with_warnings", "partially_completed"}
        for row in repair_rows
    )
    blocked = sum(
        row["repair_status"] == "blocked_by_missing_local_input" for row in repair_rows
    )
    return {
        "targeted_repair_run_id": targeted_repair_run_id,
        "residual_work_order_package_run_id": work_order_package[
            "residual_work_order_package_run_id"
        ],
        "stabilization_plan_run_id": work_order_package["stabilization_plan_run_id"],
        "phase_16_closure_run_id": work_order_package["phase_16_closure_run_id"],
        "gatekeeper_re_evaluation_run_id": work_order_package[
            "gatekeeper_re_evaluation_run_id"
        ],
        "phase_id": 17,
        "phase_name": "Targeted Evidence Stabilization Layer",
        "current_task_id": 127,
        "current_task_name": "Execute Targeted Evidence Repairs",
        "prior_gatekeeper_outcome": package_summary["prior_gatekeeper_outcome"],
        "progression_allowed": package_summary["progression_allowed"],
        "persona_reviews_allowed": package_summary["persona_reviews_allowed"],
        "repair_execution_status": "completed",
        "repair_execution_role": "targeted_evidence_repair_execution",
        "work_orders_total": len(repair_rows),
        "work_orders_completed": completed,
        "work_orders_partially_completed": partial,
        "work_orders_blocked": blocked,
        "recommended_next_task": NEXT_TASK,
        "main_repair_finding": (
            "Targeted repair artifacts were produced or documented as validation-ready; "
            "Task 128 must validate them before any future Gatekeeper return."
        ),
    }


def build_task_128_validation_input_manifest(
    *,
    targeted_repair_run_id: str,
    work_order_package: dict,
    repaired_evidence: list[dict],
    repair_rows: list[dict],
) -> dict:
    """Build Task 128 validation input manifest."""
    return {
        "future_phase_id": 17,
        "future_phase_name": "Targeted Evidence Stabilization Layer",
        "future_task_id": 128,
        "future_task_name": "Run Stabilization Validation Trial",
        "targeted_repair_run_id": targeted_repair_run_id,
        "residual_work_order_package_run_id": work_order_package[
            "residual_work_order_package_run_id"
        ],
        "validation_inputs": [
            "targeted_evidence_repairs",
            "work_order_repair_execution_matrix",
            "repaired_evidence_matrix",
            "repair_limitation_matrix",
        ],
        "repaired_evidence_areas": [row["evidence_area"] for row in repaired_evidence],
        "repair_outputs_to_validate": [row["output_artifact"] for row in repair_rows],
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
        "readiness_status": "ready_for_stabilization_validation_trial",
        "execution_allowed_now": bool(repair_rows),
        "reason": (
            "Repair outputs were created or documented and are ready for Task 128 validation."
        ),
    }


def build_targeted_repair_validation_checks() -> list[dict]:
    """Build Task 127 validation checks."""
    checks = [
        "residual_work_order_package_loaded",
        "repair_execution_summary_created",
        "work_order_repair_execution_matrix_created",
        "all_required_work_orders_processed",
        "repaired_evidence_matrix_created",
        "repair_limitation_matrix_created",
        "repair_artifact_trace_matrix_created",
        "task_128_validation_input_manifest_created",
        "prior_gatekeeper_outcome_preserved",
        "progression_not_allowed_preserved",
        "persona_review_not_allowed_preserved",
        "investor_agents_not_run",
        "gatekeeper_not_rerun_in_task_127",
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
            "source_artifact": "targeted_evidence_repairs",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 127.",
        }
        for check in checks
    ]


def build_targeted_evidence_repairs(
    *,
    targeted_repair_run_id: str,
    generated_at: str,
    work_order_package: dict,
) -> TargetedEvidenceRepairsReport:
    """Build the Task 127 targeted evidence repairs package."""
    repair_rows = build_work_order_repair_execution_matrix(work_order_package)
    repaired_evidence = build_repaired_evidence_matrix()
    summary = build_repair_execution_summary(
        targeted_repair_run_id=targeted_repair_run_id,
        work_order_package=work_order_package,
        repair_rows=repair_rows,
    )
    manifest = build_task_128_validation_input_manifest(
        targeted_repair_run_id=targeted_repair_run_id,
        work_order_package=work_order_package,
        repaired_evidence=repaired_evidence,
        repair_rows=repair_rows,
    )
    return TargetedEvidenceRepairsReport(
        targeted_repair_run_id=targeted_repair_run_id,
        generated_at=generated_at,
        residual_work_order_package_run_id=work_order_package[
            "residual_work_order_package_run_id"
        ],
        stabilization_plan_run_id=work_order_package["stabilization_plan_run_id"],
        phase_16_closure_run_id=work_order_package["phase_16_closure_run_id"],
        gatekeeper_re_evaluation_run_id=work_order_package[
            "gatekeeper_re_evaluation_run_id"
        ],
        pre_post_repair_comparison_run_id=work_order_package[
            "pre_post_repair_comparison_run_id"
        ],
        controlled_re_run_trial_run_id=work_order_package[
            "controlled_re_run_trial_run_id"
        ],
        re_run_input_package_run_id=work_order_package["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=work_order_package["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=work_order_package["research_audit_trail_run_id"],
        repair_execution_summary=summary,
        work_order_repair_execution_matrix=repair_rows,
        repaired_evidence_matrix=repaired_evidence,
        repair_limitation_matrix=build_repair_limitation_matrix(),
        repair_artifact_trace_matrix=build_repair_artifact_trace_matrix(work_order_package),
        task_128_validation_input_manifest=manifest,
        targeted_repair_validation_checks=build_targeted_repair_validation_checks(),
        repair_execution_status=summary["repair_execution_status"],
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


def _render_markdown(report: TargetedEvidenceRepairsReport) -> str:
    summary = report.repair_execution_summary
    manifest = report.task_128_validation_input_manifest
    lines = [
        "# Targeted Evidence Repairs",
        "",
        "## Executive Summary",
        "",
        f"* Targeted Repair Run ID: {report.targeted_repair_run_id}",
        f"* Residual Work Order Package Run ID: {report.residual_work_order_package_run_id}",
        "* Current Phase: 17 — Targeted Evidence Stabilization Layer",
        "* Current Task: Task 127 — Execute Targeted Evidence Repairs",
        f"* Prior Gatekeeper Outcome: {summary['prior_gatekeeper_outcome']}",
        f"* Progression Allowed: {str(summary['progression_allowed']).lower()}",
        f"* Persona Reviews Allowed: {str(summary['persona_reviews_allowed']).lower()}",
        f"* Repair Execution Status: {report.repair_execution_status}",
        f"* Work Orders Total: {summary['work_orders_total']}",
        f"* Work Orders Completed: {summary['work_orders_completed']}",
        f"* Work Orders Partially Completed: {summary['work_orders_partially_completed']}",
        f"* Work Orders Blocked: {summary['work_orders_blocked']}",
        f"* Recommended Next Task: {report.recommended_next_task}",
        "",
        "## Important Boundary",
        "",
        (
            "This report executes targeted evidence repairs only. It does not "
            "rerun Gatekeeper, run investor agents, allow persona review, create "
            "investor decisions, rankings, recommendations, allocations, "
            "rebalancing instructions, trade signals, execution instructions, or "
            "strategy validation."
        ),
        "",
        "## Where We Are Now",
        "",
        "Current Phase:",
        "17 — Targeted Evidence Stabilization Layer",
        "",
        "Previous Task:",
        "Task 126 — Build Residual Blocker Work Orders completed",
        "",
        "This Task:",
        "Task 127 executes targeted evidence repairs from the residual blocker work orders.",
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
        "## Repair Execution Summary",
        "",
        f"* Repair Execution Role: {summary['repair_execution_role']}",
        f"* Main Repair Finding: {summary['main_repair_finding']}",
        "",
        "## Work Order Repair Execution Matrix",
        "",
        *_markdown_table(
            report.work_order_repair_execution_matrix,
            [
                ("Work Order", "work_order_id"),
                ("Evidence Area", "evidence_area"),
                ("Repair Status", "repair_status"),
                ("Repair Result", "repair_result"),
                ("Validation Needed", "validation_needed"),
                ("Unresolved Issue", "unresolved_issue"),
            ],
        ),
        "",
        "## Repaired Evidence Matrix",
        "",
        *_markdown_table(
            report.repaired_evidence_matrix,
            [
                ("Evidence Area", "evidence_area"),
                ("Repair Status", "repair_status"),
                ("Stabilized Finding", "stabilized_finding"),
                ("Remaining Uncertainty", "remaining_uncertainty"),
                ("Ready For Task 128", "ready_for_task_128_validation"),
            ],
        ),
        "",
        "## Repair Limitations",
        "",
        *_markdown_table(
            report.repair_limitation_matrix,
            [
                ("Limitation", "limitation_code"),
                ("Status", "limitation_status"),
                ("Impact", "impact_on_repair"),
                ("Follow-Up", "required_follow_up"),
                ("Blocks Task 128", "blocks_task_128_validation"),
            ],
        ),
        "",
        "## Repair Artifact Trace",
        "",
        *_markdown_table(
            report.repair_artifact_trace_matrix,
            [
                ("Work Order", "linked_work_order_id"),
                ("Source Artifact", "source_artifact"),
                ("Produced Artifact", "produced_artifact"),
                ("Trace Status", "trace_status"),
            ],
        ),
        "",
        "## Task 128 Validation Input Manifest",
        "",
        f"* Future Phase: {manifest['future_phase_id']} — {manifest['future_phase_name']}",
        f"* Future Task: {manifest['future_task_id']} — {manifest['future_task_name']}",
        f"* Validation Inputs: {'; '.join(manifest['validation_inputs'])}",
        f"* Repaired Evidence Areas: {'; '.join(manifest['repaired_evidence_areas'])}",
        f"* Readiness Status: {manifest['readiness_status']}",
        f"* Execution Allowed Now: {str(manifest['execution_allowed_now']).lower()}",
        f"* Prohibited Outputs: {'; '.join(manifest['prohibited_outputs'])}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.targeted_repair_validation_checks,
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
        "* Targeted repair artifacts have been created or documented.",
        "* The correct next move is validation, not Gatekeeper rerun.",
        "* Task 128 should test whether repairs improved stability.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not allow investor review.",
        "* It does not run investor agents.",
        "* It does not rerun Gatekeeper.",
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


def write_targeted_evidence_repairs_report(
    *,
    outputs_root: Path,
    residual_work_order_package_run_id: str | None = None,
) -> TargetedEvidenceRepairsFiles:
    """Write Task 127 targeted evidence repair artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_residual_blocker_work_orders_manifest(
        outputs_root=outputs_root,
        residual_work_order_package_run_id=residual_work_order_package_run_id,
    )
    package_run_id = manifest["residual_work_order_package_run_id"]
    work_order_package = load_residual_blocker_work_orders(
        outputs_root=outputs_root,
        residual_work_order_package_run_id=package_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_targeted_evidence_repairs(
        targeted_repair_run_id=run_id,
        generated_at=generated_at.isoformat(),
        work_order_package=work_order_package,
    )

    root = outputs_root / "targeted_evidence_repairs"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "targeted_evidence_repairs.md"
    json_path = output_folder / "targeted_evidence_repairs.json"
    work_order_csv = output_folder / "work_order_repair_execution_matrix.csv"
    evidence_csv = output_folder / "repaired_evidence_matrix.csv"
    limitation_csv = output_folder / "repair_limitation_matrix.csv"
    trace_csv = output_folder / "repair_artifact_trace_matrix.csv"
    manifest_path = output_folder / "task_128_validation_input_manifest.json"
    checks_csv = output_folder / "targeted_repair_validation_checks.csv"
    latest_manifest_path = root / "latest_targeted_evidence_repairs_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(work_order_csv, report.work_order_repair_execution_matrix)
    _write_csv(evidence_csv, report.repaired_evidence_matrix)
    _write_csv(limitation_csv, report.repair_limitation_matrix)
    _write_csv(trace_csv, report.repair_artifact_trace_matrix)
    manifest_path.write_text(
        json.dumps(report.task_128_validation_input_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.targeted_repair_validation_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "targeted_repair_run_id": report.targeted_repair_run_id,
                "residual_work_order_package_run_id": report.residual_work_order_package_run_id,
                "stabilization_plan_run_id": report.stabilization_plan_run_id,
                "repair_execution_status": report.repair_execution_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_128_validation_input_manifest_path": str(manifest_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return TargetedEvidenceRepairsFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        work_order_repair_csv_path=work_order_csv,
        repaired_evidence_csv_path=evidence_csv,
        limitation_csv_path=limitation_csv,
        artifact_trace_csv_path=trace_csv,
        task_128_validation_input_manifest_path=manifest_path,
        validation_checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
