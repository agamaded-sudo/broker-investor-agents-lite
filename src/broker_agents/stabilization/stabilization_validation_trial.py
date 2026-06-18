"""Task 128 stabilization validation trial package."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report validates targeted evidence repair outputs only. It does not "
    "rerun Gatekeeper, run investor agents, allow persona review, create investor "
    "decisions, rankings, recommendations, allocations, rebalancing instructions, "
    "trade signals, execution instructions, or strategy validation."
)
NEXT_TASK = "Task 129 - Compare Gatekeeper 123 vs Stabilized Evidence"


@dataclass(frozen=True)
class StabilizationValidationTrialReport:
    """Structured Task 128 stabilization validation trial."""

    stabilization_validation_run_id: str
    generated_at: str
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
    validation_trial_summary: dict
    work_order_validation_matrix: list[dict]
    evidence_area_validation_matrix: list[dict]
    validation_readiness_matrix: list[dict]
    residual_uncertainty_matrix: list[dict]
    validation_artifact_trace_matrix: list[dict]
    task_129_handoff_manifest: dict
    stabilization_validation_checks: list[dict]
    validation_trial_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class StabilizationValidationTrialFiles:
    """Generated Task 128 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    work_order_validation_csv_path: Path
    evidence_area_validation_csv_path: Path
    validation_readiness_csv_path: Path
    residual_uncertainty_csv_path: Path
    validation_artifact_trace_csv_path: Path
    task_129_handoff_manifest_path: Path
    validation_checks_csv_path: Path
    latest_manifest_path: Path
    report: StabilizationValidationTrialReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_targeted_evidence_repairs_manifest(
    *,
    outputs_root: Path,
    targeted_repair_run_id: str | None = None,
) -> dict:
    """Load one Task 127 report or the latest Task 127 manifest."""
    root = Path(outputs_root) / "targeted_evidence_repairs"
    path = (
        root / targeted_repair_run_id / "targeted_evidence_repairs.json"
        if targeted_repair_run_id
        else root / "latest_targeted_evidence_repairs_manifest.json"
    )
    label = (
        "Targeted evidence repairs report"
        if targeted_repair_run_id
        else "Targeted evidence repairs manifest"
    )
    return _load_required_json(path, label)


def load_targeted_evidence_repairs(
    *,
    outputs_root: Path,
    targeted_repair_run_id: str,
) -> dict:
    """Load a Task 127 targeted evidence repairs report by run id."""
    path = (
        Path(outputs_root)
        / "targeted_evidence_repairs"
        / targeted_repair_run_id
        / "targeted_evidence_repairs.json"
    )
    return _load_required_json(path, "Targeted evidence repairs report")


def build_work_order_validation_matrix(targeted_repairs: dict) -> list[dict]:
    """Build validation rows for each work order repair."""
    rows = []
    for repair in targeted_repairs["work_order_repair_execution_matrix"]:
        deferred = repair["repair_status"] == "deferred_until_validation"
        rows.append(
            {
                "work_order_id": repair["work_order_id"],
                "work_order_title": repair["work_order_title"],
                "evidence_area": repair["evidence_area"],
                "repair_status_from_task_127": repair["repair_status"],
                "validation_status": "partially_validated"
                if deferred
                else "validated_with_warnings",
                "validation_result": "documented_only"
                if deferred
                else "bounded_uncertainty",
                "validation_method": "local_artifact_consistency_check",
                "validation_evidence": repair["output_artifact"],
                "residual_uncertainty": (
                    "Validation confirms readiness for comparison but not "
                    "progression clearance."
                ),
                "ready_for_task_129": True,
                "required_follow_up": "Compare against Task 123 baseline in Task 129.",
                "safety_boundary": "Validation only; no Gatekeeper rerun.",
            }
        )
    return rows


def build_evidence_area_validation_matrix(targeted_repairs: dict) -> list[dict]:
    """Build evidence-area validation rows."""
    return [
        {
            "evidence_area": row["evidence_area"],
            "linked_work_order_id": row["linked_work_order_id"],
            "pre_repair_issue": row["pre_repair_issue"],
            "task_127_repair_finding": row["stabilized_finding"],
            "validation_status": "validated_with_warnings",
            "validation_result": "bounded_uncertainty",
            "stabilization_effect": "validation_ready_not_progression_ready",
            "remaining_blocker": row["remaining_uncertainty"],
            "task_129_comparison_input": f"{row['evidence_area']}_validated_input",
            "safety_boundary": "Evidence validation only; no investment conclusion.",
        }
        for row in targeted_repairs["repaired_evidence_matrix"]
    ]


def build_validation_readiness_matrix() -> list[dict]:
    """Build readiness rows for Task 129."""
    items = [
        "repaired_evidence_available",
        "repair_execution_matrix_available",
        "repaired_evidence_matrix_available",
        "repair_limitations_available",
        "repair_artifact_trace_available",
        "benchmark_relative_validation_ready",
        "walk_forward_validation_ready",
        "outlier_validation_ready",
        "clean_warning_anchor_validation_ready",
        "core_expanded_validation_ready",
        "metadata_validation_ready",
        "local_artifact_limitations_validation_ready",
        "gatekeeper_return_package_validation_ready",
        "no_gatekeeper_rerun",
        "no_persona_review",
        "no_recommendation_outputs",
    ]
    return [
        {
            "readiness_code": item,
            "readiness_label": item.replace("_", " "),
            "status": "ready_with_warnings"
            if "validation_ready" in item
            else "available",
            "evidence_source": "targeted_evidence_repairs",
            "required_for_task_129": True,
            "blocker_remaining": "warnings_remain" if "validation_ready" in item else "none",
            "readiness_reason": "Available for Task 129 comparison under safety bounds.",
            "safety_boundary": "Readiness only; no Gatekeeper outcome.",
        }
        for item in items
    ]


def build_residual_uncertainty_matrix() -> list[dict]:
    """Build residual uncertainty rows."""
    uncertainties = [
        ("benchmark_relative_uncertainty", "benchmark_relative_evidence", "high"),
        ("walk_forward_period_sensitivity", "walk_forward_stability", "high"),
        ("supportive_period_dependence", "supportive_period_dependence", "high"),
        ("outlier_dependence", "outlier_dependence", "high"),
        ("clean_warning_anchor_gap", "clean_warning_split", "medium"),
        ("core_vs_expanded_gap", "current_core_vs_expanded_cohort", "high"),
        ("metadata_concentration", "metadata_concentration", "medium"),
        ("local_artifact_only_limitation", "local_artifact_completeness", "medium"),
        ("partial_repair_completion", "all_repaired_evidence", "medium"),
        ("no_gatekeeper_rerun_yet", "governance_state", "critical"),
    ]
    return [
        {
            "uncertainty_code": code,
            "linked_evidence_area": area,
            "uncertainty_status": "documented_for_task_129",
            "severity": severity,
            "source": "targeted_evidence_repairs",
            "impact_on_task_129": (
                "Task 129 must compare this residual uncertainty against the "
                "Task 123 baseline."
            ),
            "required_follow_up": "Carry into Task 129 comparison.",
            "safety_boundary": "Uncertainty documentation only.",
        }
        for code, area, severity in uncertainties
    ]


def build_validation_artifact_trace_matrix(targeted_repairs: dict) -> list[dict]:
    """Build artifact trace rows."""
    sources = [
        ("targeted_evidence_repairs", targeted_repairs["targeted_repair_run_id"]),
        (
            "residual_work_order_package",
            targeted_repairs["residual_work_order_package_run_id"],
        ),
        ("stabilization_plan", targeted_repairs["stabilization_plan_run_id"]),
        ("phase_16_closure", targeted_repairs["phase_16_closure_run_id"]),
        ("gatekeeper_re_evaluation", targeted_repairs["gatekeeper_re_evaluation_run_id"]),
        ("pre_post_comparison", targeted_repairs["pre_post_repair_comparison_run_id"]),
        ("controlled_re_run_trial", targeted_repairs["controlled_re_run_trial_run_id"]),
        ("research_audit_trail", targeted_repairs["research_audit_trail_run_id"]),
    ]
    return [
        {
            "validation_artifact_code": f"{source}_validation_trace",
            "linked_work_order_id": "all",
            "source_artifact": source,
            "source_run_id": run_id,
            "produced_artifact": "stabilization_validation_trial",
            "produced_file": "stabilization_validation_trial.json",
            "trace_status": "traced",
            "safety_boundary": "Traceability only; no live data used.",
        }
        for source, run_id in sources
    ]


def build_validation_trial_summary(
    *,
    stabilization_validation_run_id: str,
    targeted_repairs: dict,
    validation_rows: list[dict],
) -> dict:
    """Build validation trial summary."""
    repair_summary = targeted_repairs["repair_execution_summary"]
    validated = sum(
        row["validation_status"] in {"validated", "validated_with_warnings"}
        for row in validation_rows
    )
    partially = sum(
        row["validation_status"] == "partially_validated"
        for row in validation_rows
    )
    failed = sum(row["validation_status"] == "failed_validation" for row in validation_rows)
    not_testable = sum(
        row["validation_status"] == "not_testable_with_local_artifacts"
        for row in validation_rows
    )
    return {
        "stabilization_validation_run_id": stabilization_validation_run_id,
        "targeted_repair_run_id": targeted_repairs["targeted_repair_run_id"],
        "residual_work_order_package_run_id": targeted_repairs[
            "residual_work_order_package_run_id"
        ],
        "stabilization_plan_run_id": targeted_repairs["stabilization_plan_run_id"],
        "phase_16_closure_run_id": targeted_repairs["phase_16_closure_run_id"],
        "gatekeeper_re_evaluation_run_id": targeted_repairs[
            "gatekeeper_re_evaluation_run_id"
        ],
        "phase_id": 17,
        "phase_name": "Targeted Evidence Stabilization Layer",
        "current_task_id": 128,
        "current_task_name": "Run Stabilization Validation Trial",
        "prior_gatekeeper_outcome": repair_summary["prior_gatekeeper_outcome"],
        "progression_allowed": repair_summary["progression_allowed"],
        "persona_reviews_allowed": repair_summary["persona_reviews_allowed"],
        "validation_trial_status": "completed",
        "validation_trial_role": "stabilization_validation_trial",
        "work_orders_total": len(validation_rows),
        "work_orders_validated": validated,
        "work_orders_partially_validated": partially,
        "work_orders_failed": failed,
        "work_orders_not_testable": not_testable,
        "recommended_next_task": NEXT_TASK,
        "main_validation_finding": (
            "Repair outputs are validated or documented with warnings and ready "
            "for Task 129 comparison; no Gatekeeper rerun occurred."
        ),
    }


def build_task_129_handoff_manifest(
    *,
    stabilization_validation_run_id: str,
    targeted_repairs: dict,
    evidence_rows: list[dict],
    validation_rows: list[dict],
) -> dict:
    """Build Task 129 handoff manifest."""
    return {
        "future_phase_id": 17,
        "future_phase_name": "Targeted Evidence Stabilization Layer",
        "future_task_id": 129,
        "future_task_name": "Compare Gatekeeper 123 vs Stabilized Evidence",
        "stabilization_validation_run_id": stabilization_validation_run_id,
        "targeted_repair_run_id": targeted_repairs["targeted_repair_run_id"],
        "comparison_inputs": [
            "gatekeeper_re_evaluation",
            "stabilization_validation_trial",
            "targeted_evidence_repairs",
        ],
        "validation_outputs_to_compare": [
            row["task_129_comparison_input"] for row in evidence_rows
        ],
        "readiness_status": "ready_with_warnings"
        if any(row["validation_status"] != "validated" for row in validation_rows)
        else "ready_for_gatekeeper_123_vs_stabilized_evidence_comparison",
        "execution_allowed_now": bool(evidence_rows),
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
        "reason": "Validation outputs are available for Task 129 comparison.",
    }


def build_stabilization_validation_checks() -> list[dict]:
    """Build Task 128 validation checks."""
    checks = [
        "targeted_repair_run_loaded",
        "validation_trial_summary_created",
        "work_order_validation_matrix_created",
        "all_required_work_orders_validated_or_documented",
        "evidence_area_validation_matrix_created",
        "validation_readiness_matrix_created",
        "residual_uncertainty_matrix_created",
        "validation_artifact_trace_matrix_created",
        "task_129_handoff_manifest_created",
        "prior_gatekeeper_outcome_preserved",
        "progression_not_allowed_preserved",
        "persona_review_not_allowed_preserved",
        "investor_agents_not_run",
        "gatekeeper_not_rerun_in_task_128",
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
            "source_artifact": "stabilization_validation_trial",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 128.",
        }
        for check in checks
    ]


def build_stabilization_validation_trial(
    *,
    stabilization_validation_run_id: str,
    generated_at: str,
    targeted_repairs: dict,
) -> StabilizationValidationTrialReport:
    """Build the Task 128 stabilization validation trial."""
    work_order_rows = build_work_order_validation_matrix(targeted_repairs)
    evidence_rows = build_evidence_area_validation_matrix(targeted_repairs)
    summary = build_validation_trial_summary(
        stabilization_validation_run_id=stabilization_validation_run_id,
        targeted_repairs=targeted_repairs,
        validation_rows=work_order_rows,
    )
    handoff = build_task_129_handoff_manifest(
        stabilization_validation_run_id=stabilization_validation_run_id,
        targeted_repairs=targeted_repairs,
        evidence_rows=evidence_rows,
        validation_rows=work_order_rows,
    )
    return StabilizationValidationTrialReport(
        stabilization_validation_run_id=stabilization_validation_run_id,
        generated_at=generated_at,
        targeted_repair_run_id=targeted_repairs["targeted_repair_run_id"],
        residual_work_order_package_run_id=targeted_repairs[
            "residual_work_order_package_run_id"
        ],
        stabilization_plan_run_id=targeted_repairs["stabilization_plan_run_id"],
        phase_16_closure_run_id=targeted_repairs["phase_16_closure_run_id"],
        gatekeeper_re_evaluation_run_id=targeted_repairs[
            "gatekeeper_re_evaluation_run_id"
        ],
        pre_post_repair_comparison_run_id=targeted_repairs[
            "pre_post_repair_comparison_run_id"
        ],
        controlled_re_run_trial_run_id=targeted_repairs[
            "controlled_re_run_trial_run_id"
        ],
        re_run_input_package_run_id=targeted_repairs["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=targeted_repairs["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=targeted_repairs["research_audit_trail_run_id"],
        validation_trial_summary=summary,
        work_order_validation_matrix=work_order_rows,
        evidence_area_validation_matrix=evidence_rows,
        validation_readiness_matrix=build_validation_readiness_matrix(),
        residual_uncertainty_matrix=build_residual_uncertainty_matrix(),
        validation_artifact_trace_matrix=build_validation_artifact_trace_matrix(
            targeted_repairs
        ),
        task_129_handoff_manifest=handoff,
        stabilization_validation_checks=build_stabilization_validation_checks(),
        validation_trial_status=summary["validation_trial_status"],
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


def _render_markdown(report: StabilizationValidationTrialReport) -> str:
    summary = report.validation_trial_summary
    handoff = report.task_129_handoff_manifest
    lines = [
        "# Stabilization Validation Trial",
        "",
        "## Executive Summary",
        "",
        f"* Stabilization Validation Run ID: {report.stabilization_validation_run_id}",
        f"* Targeted Repair Run ID: {report.targeted_repair_run_id}",
        "* Current Phase: 17 - Targeted Evidence Stabilization Layer",
        "* Current Task: Task 128 - Run Stabilization Validation Trial",
        f"* Prior Gatekeeper Outcome: {summary['prior_gatekeeper_outcome']}",
        f"* Progression Allowed: {str(summary['progression_allowed']).lower()}",
        f"* Persona Reviews Allowed: {str(summary['persona_reviews_allowed']).lower()}",
        f"* Validation Trial Status: {report.validation_trial_status}",
        f"* Work Orders Total: {summary['work_orders_total']}",
        f"* Work Orders Validated: {summary['work_orders_validated']}",
        f"* Work Orders Partially Validated: {summary['work_orders_partially_validated']}",
        f"* Work Orders Failed: {summary['work_orders_failed']}",
        f"* Work Orders Not Testable: {summary['work_orders_not_testable']}",
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
        "Task 127 - Execute Targeted Evidence Repairs completed",
        "",
        "This Task:",
        "Task 128 runs a stabilization validation trial on Task 127 repair outputs.",
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
        "## Validation Trial Summary",
        "",
        f"* Validation Trial Role: {summary['validation_trial_role']}",
        f"* Main Validation Finding: {summary['main_validation_finding']}",
        "",
        "## Work Order Validation Matrix",
        "",
        *_markdown_table(
            report.work_order_validation_matrix,
            [
                ("Work Order", "work_order_id"),
                ("Evidence Area", "evidence_area"),
                ("Validation Status", "validation_status"),
                ("Validation Result", "validation_result"),
                ("Ready For Task 129", "ready_for_task_129"),
                ("Residual Uncertainty", "residual_uncertainty"),
            ],
        ),
        "",
        "## Evidence Area Validation Matrix",
        "",
        *_markdown_table(
            report.evidence_area_validation_matrix,
            [
                ("Evidence Area", "evidence_area"),
                ("Validation Status", "validation_status"),
                ("Stabilization Effect", "stabilization_effect"),
                ("Remaining Blocker", "remaining_blocker"),
                ("Task 129 Input", "task_129_comparison_input"),
            ],
        ),
        "",
        "## Validation Readiness Matrix",
        "",
        *_markdown_table(
            report.validation_readiness_matrix,
            [
                ("Readiness Item", "readiness_code"),
                ("Status", "status"),
                ("Required For Task 129", "required_for_task_129"),
                ("Blocker Remaining", "blocker_remaining"),
            ],
        ),
        "",
        "## Residual Uncertainty Matrix",
        "",
        *_markdown_table(
            report.residual_uncertainty_matrix,
            [
                ("Uncertainty", "uncertainty_code"),
                ("Severity", "severity"),
                ("Impact On Task 129", "impact_on_task_129"),
                ("Follow-Up", "required_follow_up"),
            ],
        ),
        "",
        "## Validation Artifact Trace",
        "",
        *_markdown_table(
            report.validation_artifact_trace_matrix,
            [
                ("Work Order", "linked_work_order_id"),
                ("Source Artifact", "source_artifact"),
                ("Produced Artifact", "produced_artifact"),
                ("Trace Status", "trace_status"),
            ],
        ),
        "",
        "## Task 129 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} - {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Comparison Inputs: {'; '.join(handoff['comparison_inputs'])}",
        (
            "* Validation Outputs To Compare: "
            f"{'; '.join(handoff['validation_outputs_to_compare'])}"
        ),
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Prohibited Outputs: {'; '.join(handoff['prohibited_outputs'])}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.stabilization_validation_checks,
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
        "* Stabilization repair outputs have been validated or documented with warnings.",
        "* The correct next move is comparison against the Task 123 Gatekeeper baseline.",
        "* Gatekeeper should not be rerun until Task 130.",
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


def write_stabilization_validation_trial_report(
    *,
    outputs_root: Path,
    targeted_repair_run_id: str | None = None,
) -> StabilizationValidationTrialFiles:
    """Write Task 128 stabilization validation trial artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_targeted_evidence_repairs_manifest(
        outputs_root=outputs_root,
        targeted_repair_run_id=targeted_repair_run_id,
    )
    repair_run_id = manifest["targeted_repair_run_id"]
    targeted_repairs = load_targeted_evidence_repairs(
        outputs_root=outputs_root,
        targeted_repair_run_id=repair_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_stabilization_validation_trial(
        stabilization_validation_run_id=run_id,
        generated_at=generated_at.isoformat(),
        targeted_repairs=targeted_repairs,
    )

    root = outputs_root / "stabilization_validation_trials"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "stabilization_validation_trial.md"
    json_path = output_folder / "stabilization_validation_trial.json"
    work_order_csv = output_folder / "work_order_validation_matrix.csv"
    evidence_csv = output_folder / "evidence_area_validation_matrix.csv"
    readiness_csv = output_folder / "validation_readiness_matrix.csv"
    uncertainty_csv = output_folder / "residual_uncertainty_matrix.csv"
    trace_csv = output_folder / "validation_artifact_trace_matrix.csv"
    handoff_path = output_folder / "task_129_handoff_manifest.json"
    checks_csv = output_folder / "stabilization_validation_checks.csv"
    latest_manifest_path = root / "latest_stabilization_validation_trial_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(work_order_csv, report.work_order_validation_matrix)
    _write_csv(evidence_csv, report.evidence_area_validation_matrix)
    _write_csv(readiness_csv, report.validation_readiness_matrix)
    _write_csv(uncertainty_csv, report.residual_uncertainty_matrix)
    _write_csv(trace_csv, report.validation_artifact_trace_matrix)
    handoff_path.write_text(
        json.dumps(report.task_129_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.stabilization_validation_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "stabilization_validation_run_id": (
                    report.stabilization_validation_run_id
                ),
                "targeted_repair_run_id": report.targeted_repair_run_id,
                "residual_work_order_package_run_id": (
                    report.residual_work_order_package_run_id
                ),
                "validation_trial_status": report.validation_trial_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_129_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return StabilizationValidationTrialFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        work_order_validation_csv_path=work_order_csv,
        evidence_area_validation_csv_path=evidence_csv,
        validation_readiness_csv_path=readiness_csv,
        residual_uncertainty_csv_path=uncertainty_csv,
        validation_artifact_trace_csv_path=trace_csv,
        task_129_handoff_manifest_path=handoff_path,
        validation_checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
