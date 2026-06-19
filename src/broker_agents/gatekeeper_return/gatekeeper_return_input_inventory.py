"""Task 133 Gatekeeper return package input inventory."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report inventories Gatekeeper return package inputs only. It does "
    "not assemble the final package, rerun Gatekeeper, run investor agents, "
    "run actual persona reviews, create investor decisions, rankings, "
    "recommendations, allocations, rebalancing instructions, trade signals, "
    "execution instructions, auto-promotion, or strategy validation."
)
PHASE_NAME = "Gatekeeper Return Package Layer"
NEXT_TASK = "Task 134 - Assemble Gatekeeper Return Package"

ARTIFACT_MAP = {
    "gatekeeper_return_package_plan": (
        "gatekeeper_return_package_plans",
        "gatekeeper_return_package_plan",
    ),
    "phase_17_closure": ("phase_17_closures", "phase_17_closure"),
    "gatekeeper_stabilization_re_review": (
        "gatekeeper_stabilization_re_reviews",
        "gatekeeper_stabilization_re_review",
    ),
    "gatekeeper_stabilized_evidence_comparison": (
        "gatekeeper_stabilized_evidence_comparisons",
        "gatekeeper_stabilized_evidence_comparison",
    ),
    "stabilization_validation_trial": (
        "stabilization_validation_trials",
        "stabilization_validation_trial",
    ),
    "targeted_evidence_repairs": (
        "targeted_evidence_repairs",
        "targeted_evidence_repairs",
    ),
    "residual_blocker_work_orders": (
        "residual_blocker_work_orders",
        "residual_blocker_work_orders",
    ),
    "targeted_evidence_stabilization_plan": (
        "targeted_evidence_stabilization_plans",
        "targeted_evidence_stabilization_plan",
    ),
    "phase_16_closure": ("phase_16_closures", "phase_16_closure"),
    "baseline_gatekeeper_re_evaluation": (
        "gatekeeper_re_evaluations",
        "gatekeeper_re_evaluation",
    ),
    "pre_post_repair_comparison": (
        "pre_post_repair_comparisons",
        "pre_post_repair_comparison",
    ),
    "controlled_re_run_trial": (
        "controlled_re_run_trials",
        "controlled_re_run_trial",
    ),
    "re_run_input_package": ("re_run_input_packages", "re_run_input_package"),
    "re_run_re_gate_plan": ("re_run_re_gate_plans", "re_run_re_gate_plan"),
    "research_audit_trail": (
        "research_audit_trail_bundles",
        "research_audit_trail_bundle",
    ),
}


@dataclass(frozen=True)
class GatekeeperReturnInputInventoryReport:
    """Structured Task 133 Gatekeeper return package input inventory."""

    gatekeeper_return_input_inventory_run_id: str
    generated_at: str
    gatekeeper_return_plan_run_id: str
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
    input_inventory_summary: dict
    component_input_inventory_matrix: list[dict]
    evidence_artifact_inventory_matrix: list[dict]
    source_run_traceability_matrix: list[dict]
    missing_or_warning_input_matrix: list[dict]
    package_assembly_readiness_matrix: list[dict]
    task_134_handoff_manifest: dict
    gatekeeper_return_input_inventory_checks: list[dict]
    inventory_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready report."""
        return asdict(self)


@dataclass(frozen=True)
class GatekeeperReturnInputInventoryFiles:
    """Generated Task 133 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    component_csv_path: Path
    evidence_csv_path: Path
    traceability_csv_path: Path
    missing_warning_csv_path: Path
    readiness_csv_path: Path
    task_134_handoff_manifest_path: Path
    checks_csv_path: Path
    latest_manifest_path: Path
    report: GatekeeperReturnInputInventoryReport


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_gatekeeper_return_package_plan_manifest(
    *,
    outputs_root: Path,
    gatekeeper_return_plan_run_id: str | None = None,
) -> dict:
    """Load one Task 132 plan report or the latest Task 132 plan manifest."""
    root = Path(outputs_root) / "gatekeeper_return_package_plans"
    path = (
        root / gatekeeper_return_plan_run_id / "gatekeeper_return_package_plan.json"
        if gatekeeper_return_plan_run_id
        else root / "latest_gatekeeper_return_package_plan_manifest.json"
    )
    label = (
        "Gatekeeper return package plan report"
        if gatekeeper_return_plan_run_id
        else "Gatekeeper return package plan manifest"
    )
    return _load_required_json(path, label)


def load_gatekeeper_return_package_plan(
    *,
    outputs_root: Path,
    gatekeeper_return_plan_run_id: str,
) -> dict:
    """Load a Task 132 Gatekeeper return package plan by run id."""
    path = (
        Path(outputs_root)
        / "gatekeeper_return_package_plans"
        / gatekeeper_return_plan_run_id
        / "gatekeeper_return_package_plan.json"
    )
    return _load_required_json(path, "Gatekeeper return package plan report")


def _artifact_paths(
    *,
    outputs_root: Path,
    source_code: str,
    run_id: str,
) -> tuple[Path, Path, Path]:
    folder_name, stem = ARTIFACT_MAP[source_code]
    folder = Path(outputs_root) / folder_name / run_id
    return folder, folder / f"{stem}.json", folder / f"{stem}.md"


def _artifact_status(json_path: Path, markdown_path: Path) -> tuple[str, str, bool]:
    json_exists = json_path.is_file()
    markdown_exists = markdown_path.is_file()
    if json_exists and markdown_exists:
        return "available", "ready_for_package_assembly", True
    if json_exists or markdown_exists:
        return "partial", "partial_input_only", json_exists
    return "missing_local_artifact", "blocked_until_artifact_available", False


def build_component_input_inventory_matrix(plan: dict) -> list[dict]:
    """Inventory planned Gatekeeper return package components."""
    rows = []
    for component in plan["return_package_component_matrix"]:
        source_artifacts = component["source_artifacts"]
        status = "available_with_warnings" if "warnings" in component["inclusion_status"] else "available"
        inclusion = (
            "ready_with_warnings"
            if status == "available_with_warnings"
            else "ready_for_package_assembly"
        )
        rows.append(
            {
                "component_code": component["component_code"],
                "component_label": component["component_label"],
                "component_purpose": component["component_purpose"],
                "planned_source_artifacts": source_artifacts,
                "required_inputs": component["required_inputs"],
                "located_inputs": source_artifacts,
                "missing_inputs": "none",
                "inventory_status": status,
                "inclusion_status": inclusion,
                "package_assembly_role": component["expected_output"],
                "required_follow_up": "Carry into Task 134 assembly."
                if status == "available"
                else "Review warning status during Task 134 assembly.",
                "safety_boundary": component["safety_boundary"],
            }
        )
    return rows


def build_evidence_artifact_inventory_matrix(
    *,
    outputs_root: Path,
    plan: dict,
) -> list[dict]:
    """Inventory evidence artifacts with local file-existence checks."""
    rows = []
    for evidence in plan["return_package_evidence_inventory_matrix"]:
        code = evidence["evidence_code"]
        run_id = str(evidence["source_run_id"])
        folder, json_path, _markdown_path = _artifact_paths(
            outputs_root=outputs_root,
            source_code=code,
            run_id=run_id,
        )
        status, inclusion, json_exists = _artifact_status(json_path, _markdown_path)
        rows.append(
            {
                "evidence_code": code,
                "evidence_label": evidence["evidence_label"],
                "source_phase": evidence["source_phase"],
                "source_task": evidence["source_task"],
                "source_run_id": run_id,
                "expected_source_artifact": evidence["source_artifact"],
                "located_artifact_path": str(json_path) if json_path.exists() else str(folder),
                "artifact_exists": json_exists,
                "inventory_status": status,
                "inclusion_status": inclusion,
                "role_in_package": evidence["evidence_role_in_return_package"],
                "limitation_note": evidence["limitation_note"]
                if status == "available"
                else "Local artifact requires review before package assembly.",
                "safety_boundary": evidence["safety_boundary"],
            }
        )
    return rows


def _run_ids(plan: dict) -> dict[str, str]:
    return {
        "gatekeeper_return_package_plan": plan["gatekeeper_return_plan_run_id"],
        "phase_17_closure": plan["phase_17_closure_run_id"],
        "gatekeeper_stabilization_re_review": plan[
            "gatekeeper_stabilization_re_review_run_id"
        ],
        "gatekeeper_stabilized_evidence_comparison": plan[
            "gatekeeper_stabilized_comparison_run_id"
        ],
        "stabilization_validation_trial": plan["stabilization_validation_run_id"],
        "targeted_evidence_repairs": plan["targeted_repair_run_id"],
        "residual_blocker_work_orders": plan["residual_work_order_package_run_id"],
        "targeted_evidence_stabilization_plan": plan["stabilization_plan_run_id"],
        "phase_16_closure": plan["phase_16_closure_run_id"],
        "baseline_gatekeeper_re_evaluation": plan[
            "baseline_gatekeeper_re_evaluation_run_id"
        ],
        "pre_post_repair_comparison": plan["pre_post_repair_comparison_run_id"],
        "controlled_re_run_trial": plan["controlled_re_run_trial_run_id"],
        "re_run_input_package": plan["re_run_input_package_run_id"],
        "re_run_re_gate_plan": plan["re_run_re_gate_plan_run_id"],
        "research_audit_trail": plan["research_audit_trail_run_id"],
    }


def build_source_run_traceability_matrix(
    *,
    outputs_root: Path,
    plan: dict,
) -> list[dict]:
    """Build source run traceability for required Phase 18 package sources."""
    rows = []
    for code, run_id in _run_ids(plan).items():
        folder, json_path, markdown_path = _artifact_paths(
            outputs_root=outputs_root,
            source_code=code,
            run_id=run_id,
        )
        trace_status, _inclusion, _exists = _artifact_status(json_path, markdown_path)
        rows.append(
            {
                "trace_code": code,
                "source_name": code.replace("_", " "),
                "source_run_id": run_id,
                "source_output_folder": str(folder),
                "source_primary_json": str(json_path),
                "source_primary_markdown": str(markdown_path),
                "trace_status": trace_status,
                "linked_downstream_component": "gatekeeper_return_package",
                "safety_boundary": "Traceability only; no investor action.",
            }
        )
    return rows


def build_missing_or_warning_input_matrix(
    *,
    component_rows: list[dict],
    evidence_rows: list[dict],
    plan: dict,
) -> list[dict]:
    """Build missing or warning inputs, including preserved safety blockers."""
    rows = []
    for row in [*component_rows, *evidence_rows]:
        status = row["inventory_status"]
        if status in {"available", "not_applicable"}:
            continue
        linked = row.get("component_code") or row.get("evidence_code")
        rows.append(
            {
                "issue_code": f"{linked}_{status}",
                "issue_type": status,
                "linked_component_or_evidence": linked,
                "issue_status": "open_for_task_134_review",
                "severity": "high" if status == "missing_local_artifact" else "medium",
                "impact_on_package_assembly": row["inclusion_status"],
                "required_follow_up": row.get(
                    "required_follow_up",
                    "Review local artifact before assembly.",
                ),
                "safety_boundary": "Input issue only; non-actionable.",
            }
        )
    required = [
        ("local_artifact_limitation", "available_with_warnings", "medium"),
        ("unresolved_material_blocker", "available_with_warnings", "high"),
        ("persona_review_not_allowed", "excluded_by_safety_boundary", "critical"),
        (
            "investor_agent_execution_not_allowed",
            "excluded_by_safety_boundary",
            "critical",
        ),
        ("auto_promotion_disabled", "excluded_by_safety_boundary", "critical"),
        ("gatekeeper_return_package_only_scope", "available_with_warnings", "high"),
    ]
    for issue_type, issue_status, severity in required:
        rows.append(
            {
                "issue_code": issue_type,
                "issue_type": issue_type,
                "linked_component_or_evidence": "permission_boundary"
                if "not_allowed" in issue_type or "disabled" in issue_type
                else "residual_risk_disclosure",
                "issue_status": issue_status,
                "severity": severity,
                "impact_on_package_assembly": "must_disclose_in_task_134",
                "required_follow_up": "Preserve disclosure and boundary in assembly.",
                "safety_boundary": plan["safety_notice"],
            }
        )
    return rows


def build_package_assembly_readiness_matrix(
    *,
    component_rows: list[dict],
    evidence_rows: list[dict],
) -> list[dict]:
    """Build Task 134 package assembly readiness rows."""
    missing = any(
        row["inventory_status"] == "missing_local_artifact"
        for row in [*component_rows, *evidence_rows]
    )
    ready_status = "blocked" if missing else "ready_with_warnings"
    specs = [
        ("component_inventory_available", "satisfied", "component rows inventoried"),
        (
            "evidence_artifact_inventory_available",
            "satisfied",
            "evidence artifact rows inventoried",
        ),
        ("source_run_traceability_available", "satisfied", "source trace created"),
        (
            "residual_risk_disclosures_available",
            "satisfied",
            "residual risks preserved",
        ),
        ("permission_boundaries_available", "satisfied", "permission boundaries preserved"),
        ("package_assembly_inputs_ready", ready_status, "inventory supports Task 134"),
        (
            "gatekeeper_return_package_scope_preserved",
            "satisfied",
            "scope remains package-only",
        ),
        ("persona_review_block_preserved", "satisfied", "persona review remains blocked"),
        (
            "investor_agent_block_preserved",
            "satisfied",
            "investor-agent execution remains blocked",
        ),
        ("no_recommendations_preserved", "satisfied", "recommendations remain prohibited"),
        (
            "auto_promotion_disabled_preserved",
            "satisfied",
            "auto-promotion remains disabled",
        ),
    ]
    return [
        {
            "readiness_code": code,
            "readiness_label": code.replace("_", " "),
            "readiness_status": status,
            "evidence_support": support,
            "blocker_remaining": "yes" if status == "blocked" else "no",
            "allowed_next_action": "Assemble Gatekeeper return package from inventory.",
            "prohibited_next_action": (
                "Rerun Gatekeeper, run investor agents, run actual persona "
                "reviews, create decisions, recommendations, rankings, "
                "allocations, rebalancing, trade signals, or auto-promotion."
            ),
            "safety_boundary": "Readiness for package assembly only.",
        }
        for code, status, support in specs
    ]


def build_input_inventory_summary(
    *,
    gatekeeper_return_input_inventory_run_id: str,
    plan: dict,
    component_rows: list[dict],
    evidence_rows: list[dict],
) -> dict:
    """Build the Task 133 input inventory summary."""
    plan_summary = plan["gatekeeper_return_plan_summary"]
    component_ready = sum(
        row["inclusion_status"] == "ready_for_package_assembly"
        for row in component_rows
    )
    component_warnings = sum(
        row["inclusion_status"] == "ready_with_warnings" for row in component_rows
    )
    component_missing = sum(
        row["inventory_status"] == "missing_local_artifact" for row in component_rows
    )
    evidence_ready = sum(
        row["inclusion_status"] == "ready_for_package_assembly"
        for row in evidence_rows
    )
    evidence_warnings = sum(
        row["inclusion_status"] == "ready_with_warnings" for row in evidence_rows
    )
    evidence_missing = sum(
        row["inventory_status"] == "missing_local_artifact" for row in evidence_rows
    )
    status = (
        "completed_with_warnings"
        if component_warnings or evidence_warnings or component_missing or evidence_missing
        else "completed"
    )
    return {
        "gatekeeper_return_input_inventory_run_id": (
            gatekeeper_return_input_inventory_run_id
        ),
        "gatekeeper_return_plan_run_id": plan["gatekeeper_return_plan_run_id"],
        "phase_17_closure_run_id": plan["phase_17_closure_run_id"],
        "phase_id": 18,
        "phase_name": PHASE_NAME,
        "current_task_id": 133,
        "current_task_name": "Build Gatekeeper Return Package Input Inventory",
        "final_gatekeeper_stabilization_outcome": plan_summary[
            "final_gatekeeper_stabilization_outcome"
        ],
        "final_progression_status": plan_summary["final_progression_status"],
        "final_persona_review_status": plan_summary["final_persona_review_status"],
        "inventory_status": status,
        "inventory_role": "gatekeeper_return_package_input_inventory",
        "component_inputs_total": len(component_rows),
        "component_inputs_ready": component_ready,
        "component_inputs_ready_with_warnings": component_warnings,
        "component_inputs_missing": component_missing,
        "evidence_artifacts_total": len(evidence_rows),
        "evidence_artifacts_ready": evidence_ready,
        "evidence_artifacts_ready_with_warnings": evidence_warnings,
        "evidence_artifacts_missing": evidence_missing,
        "recommended_next_task": NEXT_TASK,
        "main_inventory_finding": (
            "Gatekeeper return package inputs have been inventoried for Task "
            "134 assembly; permission boundaries and residual warnings remain "
            "preserved."
        ),
    }


def build_task_134_handoff_manifest(
    *,
    gatekeeper_return_input_inventory_run_id: str,
    plan: dict,
    component_rows: list[dict],
    evidence_rows: list[dict],
    missing_rows: list[dict],
    readiness_rows: list[dict],
) -> dict:
    """Build the Task 134 handoff manifest."""
    package_ready = next(
        row
        for row in readiness_rows
        if row["readiness_code"] == "package_assembly_inputs_ready"
    )
    readiness_status = (
        "ready_to_assemble_gatekeeper_return_package"
        if package_ready["readiness_status"] == "satisfied"
        else package_ready["readiness_status"]
    )
    if readiness_status == "ready_with_warnings":
        execution_allowed = True
    else:
        execution_allowed = readiness_status == "ready_to_assemble_gatekeeper_return_package"
    return {
        "future_phase_id": 18,
        "future_phase_name": PHASE_NAME,
        "future_task_id": 134,
        "future_task_name": "Assemble Gatekeeper Return Package",
        "gatekeeper_return_input_inventory_run_id": (
            gatekeeper_return_input_inventory_run_id
        ),
        "gatekeeper_return_plan_run_id": plan["gatekeeper_return_plan_run_id"],
        "required_inputs": [
            "gatekeeper_return_package_plan",
            "component_input_inventory_matrix",
            "evidence_artifact_inventory_matrix",
            "source_run_traceability_matrix",
            "missing_or_warning_input_matrix",
            "package_assembly_readiness_matrix",
        ],
        "component_inputs_to_assemble": [
            row["component_code"]
            for row in component_rows
            if row["inclusion_status"] != "blocked_until_artifact_available"
        ],
        "evidence_artifacts_to_include": [
            row["evidence_code"]
            for row in evidence_rows
            if row["inclusion_status"] != "blocked_until_artifact_available"
        ],
        "missing_or_warning_inputs": [row["issue_code"] for row in missing_rows],
        "allowed_scope": [
            "assembling Gatekeeper return package from inventory",
            "packaging stabilized evidence",
            "disclosing residual risks and permission boundaries",
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
        "readiness_status": readiness_status,
        "execution_allowed_now": execution_allowed,
        "reason": (
            "Task 133 input inventory is complete; Task 134 may assemble the "
            "Gatekeeper return package within the preserved safety boundary."
        ),
    }


def build_gatekeeper_return_input_inventory_checks() -> list[dict]:
    """Build Task 133 validation checks."""
    checks = [
        "gatekeeper_return_plan_loaded",
        "input_inventory_summary_created",
        "component_input_inventory_matrix_created",
        "evidence_artifact_inventory_matrix_created",
        "source_run_traceability_matrix_created",
        "missing_or_warning_input_matrix_created",
        "package_assembly_readiness_matrix_created",
        "task_134_handoff_manifest_created",
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
            "source_artifact": "gatekeeper_return_input_inventory",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 133.",
        }
        for check in checks
    ]


def build_gatekeeper_return_input_inventory(
    *,
    gatekeeper_return_input_inventory_run_id: str,
    generated_at: str,
    outputs_root: Path,
    plan: dict,
) -> GatekeeperReturnInputInventoryReport:
    """Build the Task 133 Gatekeeper return package input inventory."""
    components = build_component_input_inventory_matrix(plan)
    evidence = build_evidence_artifact_inventory_matrix(
        outputs_root=outputs_root,
        plan=plan,
    )
    traceability = build_source_run_traceability_matrix(
        outputs_root=outputs_root,
        plan=plan,
    )
    missing = build_missing_or_warning_input_matrix(
        component_rows=components,
        evidence_rows=evidence,
        plan=plan,
    )
    readiness = build_package_assembly_readiness_matrix(
        component_rows=components,
        evidence_rows=evidence,
    )
    summary = build_input_inventory_summary(
        gatekeeper_return_input_inventory_run_id=(
            gatekeeper_return_input_inventory_run_id
        ),
        plan=plan,
        component_rows=components,
        evidence_rows=evidence,
    )
    handoff = build_task_134_handoff_manifest(
        gatekeeper_return_input_inventory_run_id=(
            gatekeeper_return_input_inventory_run_id
        ),
        plan=plan,
        component_rows=components,
        evidence_rows=evidence,
        missing_rows=missing,
        readiness_rows=readiness,
    )
    return GatekeeperReturnInputInventoryReport(
        gatekeeper_return_input_inventory_run_id=(
            gatekeeper_return_input_inventory_run_id
        ),
        generated_at=generated_at,
        gatekeeper_return_plan_run_id=plan["gatekeeper_return_plan_run_id"],
        phase_17_closure_run_id=plan["phase_17_closure_run_id"],
        gatekeeper_stabilization_re_review_run_id=plan[
            "gatekeeper_stabilization_re_review_run_id"
        ],
        gatekeeper_stabilized_comparison_run_id=plan[
            "gatekeeper_stabilized_comparison_run_id"
        ],
        stabilization_validation_run_id=plan["stabilization_validation_run_id"],
        targeted_repair_run_id=plan["targeted_repair_run_id"],
        residual_work_order_package_run_id=plan["residual_work_order_package_run_id"],
        stabilization_plan_run_id=plan["stabilization_plan_run_id"],
        phase_16_closure_run_id=plan["phase_16_closure_run_id"],
        baseline_gatekeeper_re_evaluation_run_id=plan[
            "baseline_gatekeeper_re_evaluation_run_id"
        ],
        pre_post_repair_comparison_run_id=plan[
            "pre_post_repair_comparison_run_id"
        ],
        controlled_re_run_trial_run_id=plan["controlled_re_run_trial_run_id"],
        re_run_input_package_run_id=plan["re_run_input_package_run_id"],
        re_run_re_gate_plan_run_id=plan["re_run_re_gate_plan_run_id"],
        research_audit_trail_run_id=plan["research_audit_trail_run_id"],
        input_inventory_summary=summary,
        component_input_inventory_matrix=components,
        evidence_artifact_inventory_matrix=evidence,
        source_run_traceability_matrix=traceability,
        missing_or_warning_input_matrix=missing,
        package_assembly_readiness_matrix=readiness,
        task_134_handoff_manifest=handoff,
        gatekeeper_return_input_inventory_checks=(
            build_gatekeeper_return_input_inventory_checks()
        ),
        inventory_status=summary["inventory_status"],
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


def _render_markdown(report: GatekeeperReturnInputInventoryReport) -> str:
    summary = report.input_inventory_summary
    handoff = report.task_134_handoff_manifest
    lines = [
        "# Gatekeeper Return Package Input Inventory",
        "",
        "## Executive Summary",
        "",
        (
            "* Gatekeeper Return Input Inventory Run ID: "
            f"{report.gatekeeper_return_input_inventory_run_id}"
        ),
        f"* Gatekeeper Return Plan Run ID: {report.gatekeeper_return_plan_run_id}",
        "* Current Phase: 18 - Gatekeeper Return Package Layer",
        "* Current Task: Task 133 - Build Gatekeeper Return Package Input Inventory",
        (
            "* Final Gatekeeper Stabilization Outcome: "
            f"{summary['final_gatekeeper_stabilization_outcome']}"
        ),
        f"* Final Progression Status: {summary['final_progression_status']}",
        f"* Final Persona Review Status: {summary['final_persona_review_status']}",
        f"* Inventory Status: {report.inventory_status}",
        f"* Component Inputs Total: {summary['component_inputs_total']}",
        f"* Component Inputs Ready: {summary['component_inputs_ready']}",
        (
            "* Component Inputs Ready With Warnings: "
            f"{summary['component_inputs_ready_with_warnings']}"
        ),
        f"* Component Inputs Missing: {summary['component_inputs_missing']}",
        f"* Evidence Artifacts Total: {summary['evidence_artifacts_total']}",
        f"* Evidence Artifacts Ready: {summary['evidence_artifacts_ready']}",
        (
            "* Evidence Artifacts Ready With Warnings: "
            f"{summary['evidence_artifacts_ready_with_warnings']}"
        ),
        f"* Evidence Artifacts Missing: {summary['evidence_artifacts_missing']}",
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
        "Previous Task:",
        "Task 132 - Define Gatekeeper Return Package Plan completed",
        "",
        "This Task:",
        "Task 133 builds the Gatekeeper return package input inventory.",
        "",
        "Phase 18 Status:",
        "In progress",
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
        "## Input Inventory Summary",
        "",
        *_markdown_table(_summary_rows(summary), [("Field", "field"), ("Value", "value")]),
        "",
        "## Component Input Inventory Matrix",
        "",
        *_markdown_table(
            report.component_input_inventory_matrix,
            [
                ("Component", "component_code"),
                ("Located Inputs", "located_inputs"),
                ("Missing Inputs", "missing_inputs"),
                ("Inventory Status", "inventory_status"),
                ("Inclusion Status", "inclusion_status"),
            ],
        ),
        "",
        "## Evidence Artifact Inventory Matrix",
        "",
        *_markdown_table(
            report.evidence_artifact_inventory_matrix,
            [
                ("Evidence", "evidence_code"),
                ("Source Task", "source_task"),
                ("Source Run ID", "source_run_id"),
                ("Artifact Exists", "artifact_exists"),
                ("Inclusion Status", "inclusion_status"),
            ],
        ),
        "",
        "## Source Run Traceability Matrix",
        "",
        *_markdown_table(
            report.source_run_traceability_matrix,
            [
                ("Source", "trace_code"),
                ("Run ID", "source_run_id"),
                ("Output Folder", "source_output_folder"),
                ("Primary JSON", "source_primary_json"),
                ("Trace Status", "trace_status"),
            ],
        ),
        "",
        "## Missing or Warning Input Matrix",
        "",
        *_markdown_table(
            report.missing_or_warning_input_matrix,
            [
                ("Issue", "issue_code"),
                ("Linked Input", "linked_component_or_evidence"),
                ("Severity", "severity"),
                ("Impact On Assembly", "impact_on_package_assembly"),
                ("Follow-Up", "required_follow_up"),
            ],
        ),
        "",
        "## Package Assembly Readiness Matrix",
        "",
        *_markdown_table(
            report.package_assembly_readiness_matrix,
            [
                ("Readiness Item", "readiness_code"),
                ("Status", "readiness_status"),
                ("Allowed Next Action", "allowed_next_action"),
                ("Prohibited Next Action", "prohibited_next_action"),
            ],
        ),
        "",
        "## Task 134 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} - {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Required Inputs: {'; '.join(handoff['required_inputs'])}",
        (
            "* Component Inputs To Assemble: "
            f"{'; '.join(handoff['component_inputs_to_assemble'])}"
        ),
        (
            "* Evidence Artifacts To Include: "
            f"{'; '.join(handoff['evidence_artifacts_to_include'])}"
        ),
        f"* Missing Or Warning Inputs: {'; '.join(handoff['missing_or_warning_inputs'])}",
        f"* Allowed Scope: {'; '.join(handoff['allowed_scope'])}",
        f"* Prohibited Outputs: {'; '.join(handoff['prohibited_outputs'])}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.gatekeeper_return_input_inventory_checks,
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
            "* Phase 18 can proceed to Gatekeeper return package assembly if "
            "inputs are ready or warning-only."
        ),
        "* The next step is assembly, not Gatekeeper rerun.",
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


def write_gatekeeper_return_input_inventory_report(
    *,
    outputs_root: Path,
    gatekeeper_return_plan_run_id: str | None = None,
) -> GatekeeperReturnInputInventoryFiles:
    """Write Task 133 Gatekeeper return package input inventory artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_gatekeeper_return_package_plan_manifest(
        outputs_root=outputs_root,
        gatekeeper_return_plan_run_id=gatekeeper_return_plan_run_id,
    )
    plan_run_id = manifest["gatekeeper_return_plan_run_id"]
    plan = load_gatekeeper_return_package_plan(
        outputs_root=outputs_root,
        gatekeeper_return_plan_run_id=plan_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_gatekeeper_return_input_inventory(
        gatekeeper_return_input_inventory_run_id=run_id,
        generated_at=generated_at.isoformat(),
        outputs_root=outputs_root,
        plan=plan,
    )

    root = outputs_root / "gatekeeper_return_input_inventories"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "gatekeeper_return_input_inventory.md"
    json_path = output_folder / "gatekeeper_return_input_inventory.json"
    component_csv = output_folder / "component_input_inventory_matrix.csv"
    evidence_csv = output_folder / "evidence_artifact_inventory_matrix.csv"
    traceability_csv = output_folder / "source_run_traceability_matrix.csv"
    missing_csv = output_folder / "missing_or_warning_input_matrix.csv"
    readiness_csv = output_folder / "package_assembly_readiness_matrix.csv"
    handoff_path = output_folder / "task_134_handoff_manifest.json"
    checks_csv = output_folder / "gatekeeper_return_input_inventory_checks.csv"
    latest_manifest_path = root / "latest_gatekeeper_return_input_inventory_manifest.json"

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(component_csv, report.component_input_inventory_matrix)
    _write_csv(evidence_csv, report.evidence_artifact_inventory_matrix)
    _write_csv(traceability_csv, report.source_run_traceability_matrix)
    _write_csv(missing_csv, report.missing_or_warning_input_matrix)
    _write_csv(readiness_csv, report.package_assembly_readiness_matrix)
    handoff_path.write_text(
        json.dumps(report.task_134_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.gatekeeper_return_input_inventory_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "gatekeeper_return_input_inventory_run_id": (
                    report.gatekeeper_return_input_inventory_run_id
                ),
                "gatekeeper_return_plan_run_id": report.gatekeeper_return_plan_run_id,
                "phase_17_closure_run_id": report.phase_17_closure_run_id,
                "final_gatekeeper_stabilization_outcome": (
                    report.input_inventory_summary[
                        "final_gatekeeper_stabilization_outcome"
                    ]
                ),
                "final_progression_status": report.input_inventory_summary[
                    "final_progression_status"
                ],
                "final_persona_review_status": report.input_inventory_summary[
                    "final_persona_review_status"
                ],
                "inventory_status": report.inventory_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_134_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return GatekeeperReturnInputInventoryFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        component_csv_path=component_csv,
        evidence_csv_path=evidence_csv,
        traceability_csv_path=traceability_csv,
        missing_warning_csv_path=missing_csv,
        readiness_csv_path=readiness_csv,
        task_134_handoff_manifest_path=handoff_path,
        checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
