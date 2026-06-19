from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


PHASE_ID = 19
PHASE_NAME = "Limited Preparation Governance Layer"
TASK_ID = 142
TASK_NAME = "Gatekeeper Review of Limited Preparation Package"
NEXT_TASK = "Task 143 - Phase 19 Closure & Next-Step Decision"

SAFETY_NOTICE = (
    "This report performs Gatekeeper review of a limited preparation package only. "
    "It does not run investor agents, run actual persona reviews, create investor "
    "decisions, rankings, recommendations, allocations, rebalancing instructions, "
    "trade signals, execution instructions, or strategy validation."
)


@dataclass(frozen=True)
class LimitedPreparationGatekeeperReview:
    limited_preparation_gatekeeper_review_run_id: str
    generated_at: str
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
    actual_persona_review_allowed: bool
    investor_agents_allowed: bool
    recommendations_allowed: bool
    rankings_allowed: bool
    allocations_allowed: bool
    trade_signals_allowed: bool
    auto_promotion_status: str
    review_status: str
    recommended_next_task: str
    safety_notice: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LimitedPreparationGatekeeperReviewFiles:
    review: LimitedPreparationGatekeeperReview
    markdown_path: Path
    json_path: Path
    output_folder: Path
    latest_manifest_path: Path


def extract_validation_summary(validation: dict) -> dict:
    summary = validation["limited_preparation_package_validation_summary"]

    return {
        "limited_preparation_package_validation_run_id": summary[
            "limited_preparation_package_validation_run_id"
        ],
        "limited_preparation_package_run_id": summary[
            "limited_preparation_package_run_id"
        ],
        "limited_preparation_artifact_inventory_run_id": summary[
            "limited_preparation_artifact_inventory_run_id"
        ],
        "limited_preparation_plan_run_id": summary[
            "limited_preparation_plan_run_id"
        ],
        "phase_18_closure_run_id": summary["phase_18_closure_run_id"],
        "source_package_validation_status": summary["validation_status"],
        "source_blocking_findings_total": summary["blocking_findings_total"],
        "source_warning_findings_total": summary["warning_findings_total"],
    }


def build_limited_preparation_gatekeeper_review(
    *,
    review_run_id: str,
    generated_at: str,
    validation: dict,
) -> LimitedPreparationGatekeeperReview:
    source = extract_validation_summary(validation)

    return LimitedPreparationGatekeeperReview(
        limited_preparation_gatekeeper_review_run_id=review_run_id,
        generated_at=generated_at,
        limited_preparation_package_validation_run_id=source[
            "limited_preparation_package_validation_run_id"
        ],
        limited_preparation_package_run_id=source[
            "limited_preparation_package_run_id"
        ],
        limited_preparation_artifact_inventory_run_id=source[
            "limited_preparation_artifact_inventory_run_id"
        ],
        limited_preparation_plan_run_id=source[
            "limited_preparation_plan_run_id"
        ],
        phase_18_closure_run_id=source["phase_18_closure_run_id"],
        current_phase=f"{PHASE_ID} - {PHASE_NAME}",
        current_task=TASK_NAME,
        source_package_validation_status=source[
            "source_package_validation_status"
        ],
        source_blocking_findings_total=source[
            "source_blocking_findings_total"
        ],
        source_warning_findings_total=source[
            "source_warning_findings_total"
        ],
        gatekeeper_review_outcome=(
            "limited_preparation_package_accepted_with_warnings"
        ),
        post_review_progression_status="phase_19_closure_only",
        actual_persona_review_allowed=False,
        investor_agents_allowed=False,
        recommendations_allowed=False,
        rankings_allowed=False,
        allocations_allowed=False,
        trade_signals_allowed=False,
        auto_promotion_status="disabled",
        review_status="completed_with_warnings",
        recommended_next_task=NEXT_TASK,
        safety_notice=SAFETY_NOTICE,
    )


def _read_json(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"Required JSON file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def load_limited_preparation_package_validation(
    *,
    outputs_root: Path,
    limited_preparation_package_validation_run_id: str,
) -> dict:
    path = (
        outputs_root
        / "limited_preparation_package_validations"
        / limited_preparation_package_validation_run_id
        / "limited_preparation_package_validation.json"
    )
    return _read_json(path)


def load_latest_limited_preparation_package_validation_manifest(
    *,
    outputs_root: Path,
) -> dict:
    path = (
        outputs_root
        / "limited_preparation_package_validations"
        / "latest_limited_preparation_package_validation_manifest.json"
    )
    return _read_json(path)


def resolve_limited_preparation_package_validation_run_id(
    *,
    outputs_root: Path,
    limited_preparation_package_validation_run_id: str | None,
    auto_latest: bool,
) -> str:
    if limited_preparation_package_validation_run_id:
        return limited_preparation_package_validation_run_id

    if auto_latest:
        manifest = load_latest_limited_preparation_package_validation_manifest(
            outputs_root=outputs_root,
        )
        return manifest["limited_preparation_package_validation_run_id"]

    raise ValueError(
        "Provide --limited-preparation-package-validation-run-id "
        "or use --auto-latest."
    )


def render_limited_preparation_gatekeeper_review_markdown(
    review: LimitedPreparationGatekeeperReview,
) -> str:
    return f"""# Gatekeeper Review of Limited Preparation Package

## Executive Summary

- Limited Preparation Gatekeeper Review Run ID: {review.limited_preparation_gatekeeper_review_run_id}
- Limited Preparation Package Validation Run ID: {review.limited_preparation_package_validation_run_id}
- Current Phase: {review.current_phase}
- Current Task: {review.current_task}
- Source Package Validation Status: {review.source_package_validation_status}
- Source Blocking Findings Total: {review.source_blocking_findings_total}
- Source Warning Findings Total: {review.source_warning_findings_total}
- Gatekeeper Review Outcome: {review.gatekeeper_review_outcome}
- Post-Review Progression Status: {review.post_review_progression_status}
- Actual Persona Review Allowed: {review.actual_persona_review_allowed}
- Investor Agents Allowed: {review.investor_agents_allowed}
- Recommended Next Task: {review.recommended_next_task}

## Important Boundary

{review.safety_notice}

## Gatekeeper Review Decision

- Outcome: {review.gatekeeper_review_outcome}
- Progression: {review.post_review_progression_status}
- Review Status: {review.review_status}
- Recommended Next Task: {review.recommended_next_task}

## What This Does Not Suggest

- It does not allow actual persona review.
- It does not run investor agents.
- It does not recommend companies.
- It does not rank companies.
- It does not create allocation or rebalancing.
- It does not create trade signals.
- It does not enable auto-promotion.

## Safety Notice

{review.safety_notice}
"""


def write_limited_preparation_gatekeeper_review_report(
    *,
    outputs_root: Path,
    limited_preparation_package_validation_run_id: str | None = None,
    auto_latest: bool = False,
) -> LimitedPreparationGatekeeperReviewFiles:
    resolved_run_id = resolve_limited_preparation_package_validation_run_id(
        outputs_root=outputs_root,
        limited_preparation_package_validation_run_id=(
            limited_preparation_package_validation_run_id
        ),
        auto_latest=auto_latest,
    )
    validation = load_limited_preparation_package_validation(
        outputs_root=outputs_root,
        limited_preparation_package_validation_run_id=resolved_run_id,
    )

    now = datetime.now(timezone.utc)
    review_run_id = now.strftime("%Y%m%d_%H%M%S")
    generated_at = now.isoformat()

    review = build_limited_preparation_gatekeeper_review(
        review_run_id=review_run_id,
        generated_at=generated_at,
        validation=validation,
    )

    output_folder = (
        outputs_root / "limited_preparation_gatekeeper_reviews" / review_run_id
    )
    output_folder.mkdir(parents=True, exist_ok=True)

    json_path = output_folder / "limited_preparation_gatekeeper_review.json"
    markdown_path = output_folder / "limited_preparation_gatekeeper_review.md"
    latest_manifest_path = (
        outputs_root
        / "limited_preparation_gatekeeper_reviews"
        / "latest_limited_preparation_gatekeeper_review_manifest.json"
    )

    json_path.write_text(
        json.dumps(review.to_dict(), indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_limited_preparation_gatekeeper_review_markdown(review),
        encoding="utf-8",
    )

    latest_manifest = {
        "limited_preparation_gatekeeper_review_run_id": review_run_id,
        "limited_preparation_package_validation_run_id": resolved_run_id,
        "output_folder": str(output_folder),
        "markdown_path": str(markdown_path),
        "json_path": str(json_path),
        "review_status": review.review_status,
        "recommended_next_task": review.recommended_next_task,
    }
    latest_manifest_path.write_text(
        json.dumps(latest_manifest, indent=2),
        encoding="utf-8",
    )

    return LimitedPreparationGatekeeperReviewFiles(
        review=review,
        markdown_path=markdown_path,
        json_path=json_path,
        output_folder=output_folder,
        latest_manifest_path=latest_manifest_path,
    )
