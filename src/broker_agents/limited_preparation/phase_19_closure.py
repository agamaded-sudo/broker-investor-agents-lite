from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


PHASE_ID = 19
PHASE_NAME = "Limited Preparation Governance Layer"
TASK_ID = 143
TASK_NAME = "Phase 19 Closure & Next-Step Decision"

SAFETY_NOTICE = (
    "This report closes Phase 19 only. It does not run investor agents, run "
    "actual persona reviews, create investor decisions, rankings, "
    "recommendations, allocations, rebalancing instructions, trade signals, "
    "execution instructions, or strategy validation."
)

NEXT_STEP_DECISION = "pause_for_human_direction_and_simplified_workflow_selection"
RECOMMENDED_NEXT_STEP = (
    "Human decision required before starting any next workflow or governance layer."
)


@dataclass(frozen=True)
class Phase19ClosureReport:
    phase_19_closure_run_id: str
    generated_at: str
    limited_preparation_gatekeeper_review_run_id: str
    limited_preparation_package_validation_run_id: str
    limited_preparation_package_run_id: str
    limited_preparation_artifact_inventory_run_id: str
    limited_preparation_plan_run_id: str
    phase_18_closure_run_id: str
    current_phase: str
    current_task: str
    source_package_validation_status: str
    source_blocking_findings_total: int
    source_warning_findings_total: int
    gatekeeper_review_outcome: str
    post_review_progression_status: str
    phase_completion_status: str
    closure_status: str
    next_step_decision: str
    recommended_next_step: str
    actual_persona_review_allowed: bool
    investor_agents_allowed: bool
    recommendations_allowed: bool
    rankings_allowed: bool
    allocations_allowed: bool
    trade_signals_allowed: bool
    auto_promotion_status: str
    safety_notice: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class Phase19ClosureFiles:
    report: Phase19ClosureReport
    markdown_path: Path
    json_path: Path
    output_folder: Path
    latest_manifest_path: Path


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Required JSON file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_limited_preparation_gatekeeper_review(
    *,
    outputs_root: Path,
    limited_preparation_gatekeeper_review_run_id: str,
) -> dict:
    path = (
        outputs_root
        / "limited_preparation_gatekeeper_reviews"
        / limited_preparation_gatekeeper_review_run_id
        / "limited_preparation_gatekeeper_review.json"
    )
    return _read_json(path)


def load_latest_limited_preparation_gatekeeper_review_manifest(
    *,
    outputs_root: Path,
) -> dict:
    path = (
        outputs_root
        / "limited_preparation_gatekeeper_reviews"
        / "latest_limited_preparation_gatekeeper_review_manifest.json"
    )
    return _read_json(path)


def resolve_limited_preparation_gatekeeper_review_run_id(
    *,
    outputs_root: Path,
    limited_preparation_gatekeeper_review_run_id: str | None,
    auto_latest: bool,
) -> str:
    if limited_preparation_gatekeeper_review_run_id:
        return limited_preparation_gatekeeper_review_run_id

    if auto_latest:
        manifest = load_latest_limited_preparation_gatekeeper_review_manifest(
            outputs_root=outputs_root,
        )
        return manifest["limited_preparation_gatekeeper_review_run_id"]

    raise ValueError(
        "Provide --limited-preparation-gatekeeper-review-run-id "
        "or use --auto-latest."
    )


def build_phase_19_closure(
    *,
    closure_run_id: str,
    generated_at: str,
    review: dict,
) -> Phase19ClosureReport:
    return Phase19ClosureReport(
        phase_19_closure_run_id=closure_run_id,
        generated_at=generated_at,
        limited_preparation_gatekeeper_review_run_id=review[
            "limited_preparation_gatekeeper_review_run_id"
        ],
        limited_preparation_package_validation_run_id=review[
            "limited_preparation_package_validation_run_id"
        ],
        limited_preparation_package_run_id=review[
            "limited_preparation_package_run_id"
        ],
        limited_preparation_artifact_inventory_run_id=review[
            "limited_preparation_artifact_inventory_run_id"
        ],
        limited_preparation_plan_run_id=review[
            "limited_preparation_plan_run_id"
        ],
        phase_18_closure_run_id=review["phase_18_closure_run_id"],
        current_phase=f"{PHASE_ID} - {PHASE_NAME}",
        current_task=TASK_NAME,
        source_package_validation_status=review[
            "source_package_validation_status"
        ],
        source_blocking_findings_total=review[
            "source_blocking_findings_total"
        ],
        source_warning_findings_total=review[
            "source_warning_findings_total"
        ],
        gatekeeper_review_outcome=review["gatekeeper_review_outcome"],
        post_review_progression_status=review["post_review_progression_status"],
        phase_completion_status="completed_with_warnings",
        closure_status="phase_19_closed_with_warnings",
        next_step_decision=NEXT_STEP_DECISION,
        recommended_next_step=RECOMMENDED_NEXT_STEP,
        actual_persona_review_allowed=False,
        investor_agents_allowed=False,
        recommendations_allowed=False,
        rankings_allowed=False,
        allocations_allowed=False,
        trade_signals_allowed=False,
        auto_promotion_status="disabled",
        safety_notice=SAFETY_NOTICE,
    )


def render_phase_19_closure_markdown(report: Phase19ClosureReport) -> str:
    return f"""# Phase 19 Closure & Next-Step Decision

## Executive Summary

- Phase 19 Closure Run ID: {report.phase_19_closure_run_id}
- Limited Preparation Gatekeeper Review Run ID: {report.limited_preparation_gatekeeper_review_run_id}
- Current Phase: {report.current_phase}
- Current Task: {report.current_task}
- Source Package Validation Status: {report.source_package_validation_status}
- Source Blocking Findings Total: {report.source_blocking_findings_total}
- Source Warning Findings Total: {report.source_warning_findings_total}
- Gatekeeper Review Outcome: {report.gatekeeper_review_outcome}
- Post-Review Progression Status: {report.post_review_progression_status}
- Phase Completion Status: {report.phase_completion_status}
- Closure Status: {report.closure_status}
- Next-Step Decision: {report.next_step_decision}
- Recommended Next Step: {report.recommended_next_step}

## Important Boundary

{report.safety_notice}

## Closure Decision

Phase 19 is closed with warnings. The only allowed forward movement is a
human decision on the next simplified workflow. No actual persona review,
investor-agent execution, recommendations, rankings, allocations,
rebalancing, trade signals, execution instructions, strategy validation,
or auto-promotion are allowed by this closure.

## Permission Status

- Actual Persona Review Allowed: {report.actual_persona_review_allowed}
- Investor Agents Allowed: {report.investor_agents_allowed}
- Recommendations Allowed: {report.recommendations_allowed}
- Rankings Allowed: {report.rankings_allowed}
- Allocations Allowed: {report.allocations_allowed}
- Trade Signals Allowed: {report.trade_signals_allowed}
- Auto-Promotion Status: {report.auto_promotion_status}

## What This Does Not Suggest

- It does not allow actual persona review.
- It does not run investor agents.
- It does not recommend companies.
- It does not rank companies.
- It does not create allocation or rebalancing.
- It does not create trade signals.
- It does not create execution instructions.
- It does not validate a strategy.
- It does not enable auto-promotion.

## Next Step

{report.recommended_next_step}

## Safety Notice

{report.safety_notice}
"""


def write_phase_19_closure_report(
    *,
    outputs_root: Path,
    limited_preparation_gatekeeper_review_run_id: str | None = None,
    auto_latest: bool = False,
) -> Phase19ClosureFiles:
    resolved_run_id = resolve_limited_preparation_gatekeeper_review_run_id(
        outputs_root=outputs_root,
        limited_preparation_gatekeeper_review_run_id=(
            limited_preparation_gatekeeper_review_run_id
        ),
        auto_latest=auto_latest,
    )
    review = load_limited_preparation_gatekeeper_review(
        outputs_root=outputs_root,
        limited_preparation_gatekeeper_review_run_id=resolved_run_id,
    )

    now = datetime.now(timezone.utc)
    closure_run_id = now.strftime("%Y%m%d_%H%M%S")
    generated_at = now.isoformat()

    report = build_phase_19_closure(
        closure_run_id=closure_run_id,
        generated_at=generated_at,
        review=review,
    )

    output_folder = outputs_root / "phase_19_closures" / closure_run_id
    output_folder.mkdir(parents=True, exist_ok=True)

    markdown_path = output_folder / "phase_19_closure.md"
    json_path = output_folder / "phase_19_closure.json"
    latest_manifest_path = (
        outputs_root
        / "phase_19_closures"
        / "latest_phase_19_closure_manifest.json"
    )

    markdown_path.write_text(
        render_phase_19_closure_markdown(report),
        encoding="utf-8",
    )
    json_path.write_text(
        json.dumps(report.to_dict(), indent=2),
        encoding="utf-8",
    )

    latest_manifest = {
        "phase_19_closure_run_id": report.phase_19_closure_run_id,
        "limited_preparation_gatekeeper_review_run_id": (
            report.limited_preparation_gatekeeper_review_run_id
        ),
        "phase_completion_status": report.phase_completion_status,
        "closure_status": report.closure_status,
        "next_step_decision": report.next_step_decision,
        "recommended_next_step": report.recommended_next_step,
        "output_folder": str(output_folder),
        "markdown_path": str(markdown_path),
        "json_path": str(json_path),
        "safety_notice": report.safety_notice,
    }
    latest_manifest_path.write_text(
        json.dumps(latest_manifest, indent=2),
        encoding="utf-8",
    )

    return Phase19ClosureFiles(
        report=report,
        markdown_path=markdown_path,
        json_path=json_path,
        output_folder=output_folder,
        latest_manifest_path=latest_manifest_path,
    )
