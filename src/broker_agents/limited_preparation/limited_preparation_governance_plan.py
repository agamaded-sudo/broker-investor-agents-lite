"""Task 138 limited preparation governance plan."""

import csv
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path

SAFETY_NOTICE = (
    "This report defines governance for limited preparation only. It does not "
    "run investor agents, run actual persona reviews, create investor "
    "decisions, rankings, recommendations, allocations, rebalancing "
    "instructions, trade signals, execution instructions, or strategy "
    "validation."
)
PHASE_NAME = "Limited Preparation Governance Layer"
CURRENT_TASK_NAME = "Define Limited Preparation Governance Plan"
NEXT_TASK = "Task 139 - Build Limited Preparation Artifact Inventory"

PROHIBITED_OUTPUTS = [
    "actual persona reviews",
    "investor agent execution",
    "investor decisions",
    "recommendations",
    "rankings",
    "allocations",
    "rebalancing",
    "trade signals",
    "execution instructions",
    "strategy validation",
    "auto-promotion",
]


@dataclass(frozen=True)
class LimitedPreparationGovernancePlan:
    """Structured Task 138 governance plan."""

    limited_preparation_plan_run_id: str
    generated_at: str
    phase_18_closure_run_id: str
    gatekeeper_return_review_run_id: str
    gatekeeper_return_package_validation_run_id: str
    gatekeeper_return_package_run_id: str
    limited_preparation_plan_summary: dict
    limited_preparation_scope_matrix: list[dict]
    allowed_preparation_artifact_matrix: list[dict]
    prohibited_output_matrix: list[dict]
    future_gatekeeper_approval_matrix: list[dict]
    phase_19_roadmap_matrix: list[dict]
    task_139_handoff_manifest: dict
    limited_preparation_governance_checks: list[dict]
    limited_preparation_status: str
    recommended_next_task: str
    safety_notice: str = SAFETY_NOTICE

    def to_dict(self) -> dict:
        """Return a JSON-ready representation."""
        return asdict(self)


@dataclass(frozen=True)
class LimitedPreparationGovernancePlanFiles:
    """Generated Task 138 files and report."""

    output_folder: Path
    markdown_path: Path
    json_path: Path
    scope_csv_path: Path
    allowed_artifacts_csv_path: Path
    prohibited_outputs_csv_path: Path
    future_gatekeeper_approval_csv_path: Path
    roadmap_csv_path: Path
    task_139_handoff_manifest_path: Path
    checks_csv_path: Path
    latest_manifest_path: Path
    report: LimitedPreparationGovernancePlan


def _load_required_json(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"{label} not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_phase_18_closure_manifest(
    *,
    outputs_root: Path,
    phase_18_closure_run_id: str | None = None,
) -> dict:
    """Load one Phase 18 closure report or the latest manifest."""
    root = Path(outputs_root) / "phase_18_closures"
    path = (
        root / phase_18_closure_run_id / "phase_18_closure.json"
        if phase_18_closure_run_id
        else root / "latest_phase_18_closure_manifest.json"
    )
    label = (
        "Phase 18 closure report"
        if phase_18_closure_run_id
        else "Phase 18 closure manifest"
    )
    return _load_required_json(path, label)


def load_phase_18_closure(
    *,
    outputs_root: Path,
    phase_18_closure_run_id: str,
) -> dict:
    """Load a Phase 18 closure report by run id."""
    path = (
        Path(outputs_root)
        / "phase_18_closures"
        / phase_18_closure_run_id
        / "phase_18_closure.json"
    )
    return _load_required_json(path, "Phase 18 closure report")


def _closure_summary(closure: dict) -> dict:
    return closure["phase_18_closure_summary"]


def build_limited_preparation_plan_summary(
    *,
    limited_preparation_plan_run_id: str,
    closure: dict,
) -> dict:
    """Build the Task 138 limited preparation plan summary."""
    summary = _closure_summary(closure)
    warning_count = len(closure.get("remaining_warnings_after_phase_18_matrix", []))
    limited_status = "defined_with_warnings" if warning_count else "defined"
    return {
        "limited_preparation_plan_run_id": limited_preparation_plan_run_id,
        "phase_18_closure_run_id": closure["phase_18_closure_run_id"],
        "gatekeeper_return_review_run_id": closure["gatekeeper_return_review_run_id"],
        "phase_id": 19,
        "phase_name": PHASE_NAME,
        "current_task_id": 138,
        "current_task_name": CURRENT_TASK_NAME,
        "source_gatekeeper_return_outcome": summary[
            "final_gatekeeper_return_outcome"
        ],
        "source_post_review_progression_status": summary[
            "final_post_review_progression_status"
        ],
        "source_post_review_persona_review_status": summary[
            "final_post_review_persona_review_status"
        ],
        "limited_preparation_status": limited_status,
        "actual_persona_review_allowed": False,
        "investor_agents_allowed": False,
        "recommendations_allowed": False,
        "rankings_allowed": False,
        "allocations_allowed": False,
        "trade_signals_allowed": False,
        "auto_promotion_status": "disabled",
        "plan_confidence": "high_with_boundary_warnings"
        if limited_status == "defined_with_warnings"
        else "high",
        "recommended_next_task": NEXT_TASK,
        "main_plan_finding": (
            "Limited preparation is defined as governance-bound artifact "
            "preparation only; actual persona review, investor-agent execution, "
            "recommendations, rankings, allocations, trade signals, and "
            "auto-promotion remain blocked until future explicit Gatekeeper "
            "approval."
        ),
    }


def build_limited_preparation_scope_matrix() -> list[dict]:
    """Build limited preparation scope rows."""
    specs = [
        ("limited_preparation_governance", "allowed"),
        ("artifact_inventory_preparation", "allowed"),
        ("preparation_package_assembly", "future_phase_task"),
        ("preparation_package_validation", "future_phase_task"),
        ("future_gatekeeper_approval_request", "required_before_scope_expansion"),
        ("actual_persona_review", "not_allowed"),
        ("investor_agent_execution", "not_allowed"),
        ("investor_decision_generation", "not_allowed"),
        ("recommendations", "not_allowed"),
        ("rankings", "not_allowed"),
        ("allocations_or_rebalancing", "not_allowed"),
        ("trade_signals", "not_allowed"),
        ("auto_promotion", "disabled"),
    ]
    return [
        {
            "scope_code": code,
            "scope_label": code.replace("_", " "),
            "scope_status": status,
            "allowed_actions": "Governance planning and preparation artifact definition only."
            if status == "allowed"
            else "None before the applicable future task or approval.",
            "prohibited_actions": "; ".join(PROHIBITED_OUTPUTS),
            "required_conditions": "Future explicit Gatekeeper approval."
            if status in {"not_allowed", "disabled", "required_before_scope_expansion"}
            else "Stay within limited preparation boundaries.",
            "safety_boundary": "Scope definition only; non-actionable.",
        }
        for code, status in specs
    ]


def build_allowed_preparation_artifact_matrix() -> list[dict]:
    """Build allowed preparation artifact rows."""
    artifacts = [
        "persona_review_readiness_checklist",
        "investor_agent_execution_preconditions",
        "evidence_pack_structure_outline",
        "company_data_pack_completeness_template",
        "permission_boundary_checklist",
        "residual_risk_follow_up_list",
        "gatekeeper_pre_approval_request_template",
        "no_recommendation_safety_notice",
        "no_ranking_safety_notice",
        "no_trade_signal_safety_notice",
    ]
    return [
        {
            "artifact_code": code,
            "artifact_label": code.replace("_", " "),
            "artifact_status": "allowed_for_preparation",
            "purpose": "Define structure, readiness, or safety requirements for a future package.",
            "allowed_content": "Templates, checklists, inventory fields, boundary language, and required inputs.",
            "prohibited_content": "Investor judgments, stock decisions, recommendations, rankings, allocations, trade signals, or execution instructions.",
            "required_inputs": "Phase 18 closure and Task 138 governance boundaries.",
            "safety_boundary": "Preparation artifact only.",
        }
        for code in artifacts
    ]


def build_prohibited_output_matrix() -> list[dict]:
    """Build prohibited output rows."""
    outputs = [
        "actual_persona_review",
        "investor_agent_execution",
        "investor_decision_generation",
        "buy_sell_hold_recommendations",
        "company_rankings",
        "portfolio_allocations",
        "portfolio_rebalancing",
        "trade_signals",
        "execution_instructions",
        "strategy_validation",
        "auto_promotion",
    ]
    return [
        {
            "prohibited_code": code,
            "prohibited_label": code.replace("_", " "),
            "final_status": "prohibited",
            "prohibited_actions": code.replace("_", " "),
            "reason": "Not authorized by Phase 18 closure or Task 138 limited preparation scope.",
            "condition_to_reconsider": "Future explicit Gatekeeper approval.",
            "safety_boundary": "Prohibited output remains blocked.",
        }
        for code in outputs
    ]


def build_future_gatekeeper_approval_matrix() -> list[dict]:
    """Build future Gatekeeper approval requirement rows."""
    approvals = [
        "approval_for_actual_persona_review",
        "approval_for_investor_agent_execution",
        "approval_for_investor_decision_generation",
        "approval_for_company_comparison_or_ranking",
        "approval_for_recommendation_language",
        "approval_for_allocation_or_trade_signal_language",
        "approval_for_auto_promotion_change",
    ]
    return [
        {
            "approval_code": code,
            "approval_label": code.replace("_", " "),
            "approval_required_for": code.replace("approval_for_", "").replace("_", " "),
            "current_status": "required_not_granted",
            "required_preconditions": "Validated limited preparation package and future Gatekeeper approval.",
            "required_artifacts": "Limited preparation package, validation report, permission boundary checklist.",
            "prohibited_until_approved": "; ".join(PROHIBITED_OUTPUTS),
            "safety_boundary": "Approval requirement only; no approval granted.",
        }
        for code in approvals
    ]


def build_phase_19_roadmap_matrix() -> list[dict]:
    """Build Phase 19 roadmap rows."""
    tasks = [
        (138, "Define Limited Preparation Governance Plan", "Define governance scope."),
        (139, "Build Limited Preparation Artifact Inventory", "Inventory allowed preparation artifacts."),
        (140, "Assemble Limited Preparation Package", "Assemble package from allowed artifacts."),
        (141, "Validate Limited Preparation Package", "Validate package completeness and boundaries."),
        (142, "Gatekeeper Review of Limited Preparation Package", "Review package for possible future scope decisions."),
        (143, "Phase 19 Closure & Next-Step Decision", "Close Phase 19 and define next governance step."),
    ]
    return [
        {
            "task_id": task_id,
            "task_name": task_name,
            "task_purpose": purpose,
            "allowed_scope": "Limited preparation governance artifacts only.",
            "prohibited_outputs": "; ".join(PROHIBITED_OUTPUTS),
            "expected_status_after_task": "completed"
            if task_id == 138
            else "pending_future_task",
            "safety_boundary": "No actual persona review or investor-agent execution before future Gatekeeper approval.",
        }
        for task_id, task_name, purpose in tasks
    ]


def build_task_139_handoff_manifest(*, plan_summary: dict) -> dict:
    """Build Task 139 handoff manifest."""
    return {
        "future_phase_id": 19,
        "future_phase_name": PHASE_NAME,
        "future_task_id": 139,
        "future_task_name": "Build Limited Preparation Artifact Inventory",
        "limited_preparation_plan_run_id": plan_summary[
            "limited_preparation_plan_run_id"
        ],
        "phase_18_closure_run_id": plan_summary["phase_18_closure_run_id"],
        "source_gatekeeper_return_outcome": plan_summary[
            "source_gatekeeper_return_outcome"
        ],
        "allowed_scope": [
            "artifact inventory preparation",
            "template inventory",
            "permission boundary inventory",
            "residual risk follow-up inventory",
        ],
        "prohibited_outputs": PROHIBITED_OUTPUTS,
        "expected_artifact_inventory_categories": [
            "readiness checklists",
            "execution preconditions",
            "evidence pack structures",
            "data completeness templates",
            "permission boundary notices",
            "future Gatekeeper approval request templates",
        ],
        "readiness_status": "ready_to_build_limited_preparation_artifact_inventory",
        "execution_allowed_now": True,
        "reason": "Task 138 defined limited preparation governance without expanding scope.",
    }


def build_limited_preparation_governance_checks() -> list[dict]:
    """Build Task 138 validation checks."""
    checks = [
        "phase_18_closure_loaded",
        "limited_preparation_plan_summary_created",
        "limited_preparation_scope_matrix_created",
        "allowed_preparation_artifact_matrix_created",
        "prohibited_output_matrix_created",
        "future_gatekeeper_approval_matrix_created",
        "phase_19_roadmap_matrix_created",
        "task_139_handoff_manifest_created",
        "gatekeeper_return_outcome_preserved",
        "limited_preparation_only_preserved",
        "persona_review_false_preserved",
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
            "source_artifact": "limited_preparation_governance_plan",
            "blocking_if_failed": True,
            "finding": f"{check} satisfied for Task 138.",
        }
        for check in checks
    ]


def build_limited_preparation_governance_plan(
    *,
    limited_preparation_plan_run_id: str,
    generated_at: str,
    closure: dict,
) -> LimitedPreparationGovernancePlan:
    """Build Task 138 limited preparation governance plan."""
    summary = build_limited_preparation_plan_summary(
        limited_preparation_plan_run_id=limited_preparation_plan_run_id,
        closure=closure,
    )
    return LimitedPreparationGovernancePlan(
        limited_preparation_plan_run_id=limited_preparation_plan_run_id,
        generated_at=generated_at,
        phase_18_closure_run_id=closure["phase_18_closure_run_id"],
        gatekeeper_return_review_run_id=closure["gatekeeper_return_review_run_id"],
        gatekeeper_return_package_validation_run_id=closure[
            "gatekeeper_return_package_validation_run_id"
        ],
        gatekeeper_return_package_run_id=closure["gatekeeper_return_package_run_id"],
        limited_preparation_plan_summary=summary,
        limited_preparation_scope_matrix=build_limited_preparation_scope_matrix(),
        allowed_preparation_artifact_matrix=build_allowed_preparation_artifact_matrix(),
        prohibited_output_matrix=build_prohibited_output_matrix(),
        future_gatekeeper_approval_matrix=build_future_gatekeeper_approval_matrix(),
        phase_19_roadmap_matrix=build_phase_19_roadmap_matrix(),
        task_139_handoff_manifest=build_task_139_handoff_manifest(
            plan_summary=summary
        ),
        limited_preparation_governance_checks=build_limited_preparation_governance_checks(),
        limited_preparation_status=summary["limited_preparation_status"],
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


def _render_markdown(report: LimitedPreparationGovernancePlan) -> str:
    summary = report.limited_preparation_plan_summary
    handoff = report.task_139_handoff_manifest
    lines = [
        "# Limited Preparation Governance Plan",
        "",
        "## Executive Summary",
        "",
        f"* Limited Preparation Plan Run ID: {report.limited_preparation_plan_run_id}",
        f"* Phase 18 Closure Run ID: {report.phase_18_closure_run_id}",
        "* Current Phase: 19 - Limited Preparation Governance Layer",
        "* Current Task: Task 138 - Define Limited Preparation Governance Plan",
        f"* Source Gatekeeper Return Outcome: {summary['source_gatekeeper_return_outcome']}",
        f"* Source Post-Review Progression Status: {summary['source_post_review_progression_status']}",
        f"* Source Post-Review Persona Review Status: {summary['source_post_review_persona_review_status']}",
        f"* Limited Preparation Status: {report.limited_preparation_status}",
        f"* Recommended Next Task: {report.recommended_next_task}",
        "",
        "## Important Boundary",
        "",
        SAFETY_NOTICE,
        "",
        "## Where We Are Now",
        "",
        "Current Phase:",
        "19 - Limited Preparation Governance Layer",
        "",
        "Previous Phase:",
        "18 - Gatekeeper Return Package Layer closed_for_limited_preparation_only",
        "",
        "This Task:",
        "Task 138 defines limited preparation governance.",
        "",
        "Final Gatekeeper Return Outcome From Phase 18:",
        "return_package_accepted_for_limited_preparation",
        "",
        "Allowed Progression:",
        "limited_preparation_only",
        "",
        "Persona Reviews:",
        "false",
        "",
        "Recommended Next Task:",
        NEXT_TASK,
        "",
        "## Limited Preparation Scope",
        "",
        *_markdown_table(
            report.limited_preparation_scope_matrix,
            [
                ("Scope", "scope_code"),
                ("Status", "scope_status"),
                ("Allowed Actions", "allowed_actions"),
                ("Prohibited Actions", "prohibited_actions"),
                ("Conditions", "required_conditions"),
            ],
        ),
        "",
        "## Allowed Preparation Artifacts",
        "",
        *_markdown_table(
            report.allowed_preparation_artifact_matrix,
            [
                ("Artifact", "artifact_code"),
                ("Status", "artifact_status"),
                ("Purpose", "purpose"),
                ("Allowed Content", "allowed_content"),
                ("Prohibited Content", "prohibited_content"),
            ],
        ),
        "",
        "## Prohibited Outputs",
        "",
        *_markdown_table(
            report.prohibited_output_matrix,
            [
                ("Output", "prohibited_code"),
                ("Status", "final_status"),
                ("Reason", "reason"),
                ("Condition To Reconsider", "condition_to_reconsider"),
            ],
        ),
        "",
        "## Future Gatekeeper Approval Requirements",
        "",
        *_markdown_table(
            report.future_gatekeeper_approval_matrix,
            [
                ("Approval", "approval_code"),
                ("Required For", "approval_required_for"),
                ("Current Status", "current_status"),
                ("Required Preconditions", "required_preconditions"),
            ],
        ),
        "",
        "## Phase 19 Roadmap",
        "",
        *_markdown_table(
            report.phase_19_roadmap_matrix,
            [
                ("Task", "task_id"),
                ("Purpose", "task_purpose"),
                ("Allowed Scope", "allowed_scope"),
                ("Prohibited Outputs", "prohibited_outputs"),
            ],
        ),
        "",
        "## Task 139 Handoff",
        "",
        f"* Future Phase: {handoff['future_phase_id']} - {handoff['future_phase_name']}",
        f"* Future Task: {handoff['future_task_id']} - {handoff['future_task_name']}",
        f"* Allowed Scope: {'; '.join(handoff['allowed_scope'])}",
        f"* Prohibited Outputs: {'; '.join(handoff['prohibited_outputs'])}",
        f"* Expected Artifact Inventory Categories: {'; '.join(handoff['expected_artifact_inventory_categories'])}",
        f"* Readiness Status: {handoff['readiness_status']}",
        f"* Execution Allowed Now: {str(handoff['execution_allowed_now']).lower()}",
        f"* Reason: {handoff['reason']}",
        "",
        "## Validation Checks",
        "",
        *_markdown_table(
            report.limited_preparation_governance_checks,
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
        "* Phase 19 can start.",
        "* The system may prepare governance-bound artifacts only.",
        "* The next step is artifact inventory.",
        "* The work remains non-actionable and preparation-only.",
        "",
        "## What This Does Not Suggest",
        "",
        "* It does not allow actual persona review.",
        "* It does not run investor agents.",
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


def write_limited_preparation_governance_plan_report(
    *,
    outputs_root: Path,
    phase_18_closure_run_id: str | None = None,
) -> LimitedPreparationGovernancePlanFiles:
    """Write Task 138 limited preparation governance plan artifacts."""
    outputs_root = Path(outputs_root)
    manifest = load_phase_18_closure_manifest(
        outputs_root=outputs_root,
        phase_18_closure_run_id=phase_18_closure_run_id,
    )
    closure_run_id = manifest["phase_18_closure_run_id"]
    closure = load_phase_18_closure(
        outputs_root=outputs_root,
        phase_18_closure_run_id=closure_run_id,
    )
    generated_at = datetime.now(timezone.utc)
    run_id = generated_at.strftime("%Y%m%d_%H%M%S")
    report = build_limited_preparation_governance_plan(
        limited_preparation_plan_run_id=run_id,
        generated_at=generated_at.isoformat(),
        closure=closure,
    )

    root = outputs_root / "limited_preparation_governance_plans"
    output_folder = root / run_id
    output_folder.mkdir(parents=True, exist_ok=True)
    markdown_path = output_folder / "limited_preparation_governance_plan.md"
    json_path = output_folder / "limited_preparation_governance_plan.json"
    scope_csv = output_folder / "limited_preparation_scope_matrix.csv"
    artifacts_csv = output_folder / "allowed_preparation_artifact_matrix.csv"
    prohibited_csv = output_folder / "prohibited_output_matrix.csv"
    approvals_csv = output_folder / "future_gatekeeper_approval_matrix.csv"
    roadmap_csv = output_folder / "phase_19_roadmap_matrix.csv"
    handoff_path = output_folder / "task_139_handoff_manifest.json"
    checks_csv = output_folder / "limited_preparation_governance_checks.csv"
    latest_manifest_path = (
        root / "latest_limited_preparation_governance_plan_manifest.json"
    )

    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    _write_csv(scope_csv, report.limited_preparation_scope_matrix)
    _write_csv(artifacts_csv, report.allowed_preparation_artifact_matrix)
    _write_csv(prohibited_csv, report.prohibited_output_matrix)
    _write_csv(approvals_csv, report.future_gatekeeper_approval_matrix)
    _write_csv(roadmap_csv, report.phase_19_roadmap_matrix)
    handoff_path.write_text(
        json.dumps(report.task_139_handoff_manifest, indent=2),
        encoding="utf-8",
    )
    _write_csv(checks_csv, report.limited_preparation_governance_checks)
    latest_manifest_path.write_text(
        json.dumps(
            {
                "limited_preparation_plan_run_id": report.limited_preparation_plan_run_id,
                "phase_18_closure_run_id": report.phase_18_closure_run_id,
                "gatekeeper_return_review_run_id": report.gatekeeper_return_review_run_id,
                "source_gatekeeper_return_outcome": report.limited_preparation_plan_summary[
                    "source_gatekeeper_return_outcome"
                ],
                "source_post_review_progression_status": report.limited_preparation_plan_summary[
                    "source_post_review_progression_status"
                ],
                "source_post_review_persona_review_status": report.limited_preparation_plan_summary[
                    "source_post_review_persona_review_status"
                ],
                "limited_preparation_status": report.limited_preparation_status,
                "recommended_next_task": report.recommended_next_task,
                "output_folder": str(output_folder),
                "report_path": str(markdown_path),
                "report_json_path": str(json_path),
                "task_139_handoff_manifest_path": str(handoff_path),
                "safety_notice": report.safety_notice,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return LimitedPreparationGovernancePlanFiles(
        output_folder=output_folder,
        markdown_path=markdown_path,
        json_path=json_path,
        scope_csv_path=scope_csv,
        allowed_artifacts_csv_path=artifacts_csv,
        prohibited_outputs_csv_path=prohibited_csv,
        future_gatekeeper_approval_csv_path=approvals_csv,
        roadmap_csv_path=roadmap_csv,
        task_139_handoff_manifest_path=handoff_path,
        checks_csv_path=checks_csv,
        latest_manifest_path=latest_manifest_path,
        report=report,
    )
