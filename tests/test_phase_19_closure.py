import json
from pathlib import Path

import pytest

from broker_agents.limited_preparation.phase_19_closure import (
    build_phase_19_closure,
    load_limited_preparation_gatekeeper_review,
    resolve_limited_preparation_gatekeeper_review_run_id,
    write_phase_19_closure_report,
)


def _review_fixture() -> dict:
    return {
        "limited_preparation_gatekeeper_review_run_id": "20260619_201936",
        "generated_at": "2026-06-19T20:19:36+00:00",
        "limited_preparation_package_validation_run_id": "20260619_164454",
        "limited_preparation_package_run_id": "20260619_162233",
        "limited_preparation_artifact_inventory_run_id": "20260619_120518",
        "limited_preparation_plan_run_id": "20260619_112306",
        "phase_18_closure_run_id": "20260619_095701",
        "current_phase": "19 - Limited Preparation Governance Layer",
        "current_task": "Gatekeeper Review of Limited Preparation Package",
        "source_package_validation_status": "complete_with_warnings",
        "source_blocking_findings_total": 0,
        "source_warning_findings_total": 8,
        "gatekeeper_review_outcome": (
            "limited_preparation_package_accepted_with_warnings"
        ),
        "post_review_progression_status": "phase_19_closure_only",
        "actual_persona_review_allowed": False,
        "investor_agents_allowed": False,
        "recommendations_allowed": False,
        "rankings_allowed": False,
        "allocations_allowed": False,
        "trade_signals_allowed": False,
        "auto_promotion_status": "disabled",
        "review_status": "completed_with_warnings",
        "recommended_next_task": (
            "Task 143 - Phase 19 Closure & Next-Step Decision"
        ),
        "safety_notice": "does not run investor agents or trade signals",
    }


def _write_review_fixture(outputs_root: Path) -> None:
    review = _review_fixture()
    root = outputs_root / "limited_preparation_gatekeeper_reviews"
    folder = root / review["limited_preparation_gatekeeper_review_run_id"]
    folder.mkdir(parents=True)

    report_path = folder / "limited_preparation_gatekeeper_review.json"
    report_path.write_text(json.dumps(review), encoding="utf-8")

    latest_manifest = {
        "limited_preparation_gatekeeper_review_run_id": (
            review["limited_preparation_gatekeeper_review_run_id"]
        ),
        "json_path": str(report_path),
        "review_status": review["review_status"],
        "recommended_next_task": review["recommended_next_task"],
    }
    (root / "latest_limited_preparation_gatekeeper_review_manifest.json").write_text(
        json.dumps(latest_manifest),
        encoding="utf-8",
    )


def test_build_phase_19_closure_core_fields() -> None:
    report = build_phase_19_closure(
        closure_run_id="closure_001",
        generated_at="2026-06-20T00:00:00+00:00",
        review=_review_fixture(),
    )

    assert report.current_phase == "19 - Limited Preparation Governance Layer"
    assert report.current_task == "Phase 19 Closure & Next-Step Decision"
    assert report.phase_completion_status == "completed_with_warnings"
    assert report.closure_status == "phase_19_closed_with_warnings"
    assert report.next_step_decision == (
        "pause_for_human_direction_and_simplified_workflow_selection"
    )
    assert report.source_blocking_findings_total == 0
    assert report.source_warning_findings_total == 8
    assert report.actual_persona_review_allowed is False
    assert report.investor_agents_allowed is False
    assert report.recommendations_allowed is False
    assert report.rankings_allowed is False
    assert report.allocations_allowed is False
    assert report.trade_signals_allowed is False
    assert report.auto_promotion_status == "disabled"


def test_phase_19_closure_to_dict_includes_safety_notice() -> None:
    report = build_phase_19_closure(
        closure_run_id="closure_001",
        generated_at="2026-06-20T00:00:00+00:00",
        review=_review_fixture(),
    )

    payload = report.to_dict()

    assert payload["safety_notice"]
    assert "does not run investor agents" in payload["safety_notice"]
    assert "trade signals" in payload["safety_notice"]


def test_resolves_latest_limited_preparation_gatekeeper_review(
    tmp_path: Path,
) -> None:
    _write_review_fixture(tmp_path)

    run_id = resolve_limited_preparation_gatekeeper_review_run_id(
        outputs_root=tmp_path,
        limited_preparation_gatekeeper_review_run_id=None,
        auto_latest=True,
    )

    assert run_id == "20260619_201936"


def test_requires_explicit_or_auto_latest(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        resolve_limited_preparation_gatekeeper_review_run_id(
            outputs_root=tmp_path,
            limited_preparation_gatekeeper_review_run_id=None,
            auto_latest=False,
        )


def test_loads_limited_preparation_gatekeeper_review(tmp_path: Path) -> None:
    _write_review_fixture(tmp_path)

    review = load_limited_preparation_gatekeeper_review(
        outputs_root=tmp_path,
        limited_preparation_gatekeeper_review_run_id="20260619_201936",
    )

    assert (
        review["gatekeeper_review_outcome"]
        == "limited_preparation_package_accepted_with_warnings"
    )


def test_write_phase_19_closure_report_writes_minimal_files(
    tmp_path: Path,
) -> None:
    _write_review_fixture(tmp_path)

    files = write_phase_19_closure_report(
        outputs_root=tmp_path,
        limited_preparation_gatekeeper_review_run_id="20260619_201936",
    )

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.latest_manifest_path.is_file()

    output_names = {path.name for path in files.output_folder.iterdir()}
    assert output_names == {"phase_19_closure.md", "phase_19_closure.json"}

    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## Important Boundary" in markdown
    assert "## Closure Decision" in markdown
    assert "## What This Does Not Suggest" in markdown
    assert "does not run investor agents" in markdown

    manifest = json.loads(files.latest_manifest_path.read_text(encoding="utf-8"))
    assert manifest["phase_19_closure_run_id"]
    assert manifest["closure_status"] == "phase_19_closed_with_warnings"
    assert manifest["next_step_decision"] == (
        "pause_for_human_direction_and_simplified_workflow_selection"
    )
