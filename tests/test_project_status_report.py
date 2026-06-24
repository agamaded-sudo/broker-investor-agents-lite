import json
from pathlib import Path

from broker_agents.project_status_report import (
    build_project_status_report,
    inspect_manifest,
    write_project_status_report,
)


def _write_manifest_fixtures(outputs_root: Path) -> None:
    phase_19_root = outputs_root / "phase_19_closures"
    phase_19_root.mkdir(parents=True)
    (phase_19_root / "latest_phase_19_closure_manifest.json").write_text(
        json.dumps(
            {
                "phase_19_closure_run_id": "20260620_061039",
                "phase_completion_status": "completed_with_warnings",
                "closure_status": "phase_19_closed_with_warnings",
                "next_step_decision": (
                    "pause_for_human_direction_and_simplified_workflow_selection"
                ),
            }
        ),
        encoding="utf-8",
    )

    gatekeeper_root = outputs_root / "limited_preparation_gatekeeper_reviews"
    gatekeeper_root.mkdir(parents=True)
    (
        gatekeeper_root
        / "latest_limited_preparation_gatekeeper_review_manifest.json"
    ).write_text(
        json.dumps(
            {
                "limited_preparation_gatekeeper_review_run_id": "20260619_201936",
                "review_status": "completed_with_warnings",
                "recommended_next_task": (
                    "Task 143 - Phase 19 Closure & Next-Step Decision"
                ),
            }
        ),
        encoding="utf-8",
    )


def test_inspect_manifest_reports_missing(tmp_path: Path) -> None:
    status = inspect_manifest(
        name="missing_manifest",
        path=tmp_path / "missing.json",
        run_id_key="run_id",
    )

    assert status.status == "missing"
    assert status.run_id == "unavailable"
    assert status.details == {}


def test_build_project_status_report_from_available_manifests(
    tmp_path: Path,
) -> None:
    _write_manifest_fixtures(tmp_path)

    report = build_project_status_report(
        report_run_id="status_001",
        generated_at="2026-06-20T00:00:00+00:00",
        outputs_root=tmp_path,
    )

    assert report.current_phase == (
        "Phase 19 - Limited Preparation Governance Layer"
    )
    assert report.current_phase_status == "completed_with_warnings"
    assert report.latest_phase_19_closure_run_id == "20260620_061039"
    assert report.latest_gatekeeper_review_run_id == "20260619_201936"
    assert report.closure_status == "phase_19_closed_with_warnings"
    assert report.next_step_decision == (
        "pause_for_human_direction_and_simplified_workflow_selection"
    )
    assert "status reporting" in report.allowed_scope
    assert "investor-agent execution" in report.blocked_scope
    assert "trade signals" in report.safety_notice


def test_build_project_status_report_handles_missing_manifests(
    tmp_path: Path,
) -> None:
    report = build_project_status_report(
        report_run_id="status_001",
        generated_at="2026-06-20T00:00:00+00:00",
        outputs_root=tmp_path,
    )

    assert report.latest_phase_19_closure_run_id == "unavailable"
    assert report.latest_gatekeeper_review_run_id == "unavailable"
    assert all(
        item["status"] == "missing"
        for item in report.manifest_statuses
    )


def test_write_project_status_report_writes_minimal_files(
    tmp_path: Path,
) -> None:
    _write_manifest_fixtures(tmp_path)

    files = write_project_status_report(outputs_root=tmp_path)

    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.latest_manifest_path.is_file()

    output_names = {path.name for path in files.output_folder.iterdir()}
    assert output_names == {
        "project_status_report.md",
        "project_status_report.json",
    }

    markdown = files.markdown_path.read_text(encoding="utf-8")
    assert "## أين نحن الآن؟" in markdown
    assert "## Allowed Scope" in markdown
    assert "## Blocked Scope" in markdown
    assert "does not run investor agents" in markdown

    manifest = json.loads(files.latest_manifest_path.read_text(encoding="utf-8"))
    assert manifest["project_status_report_run_id"]
    assert manifest["latest_phase_19_closure_run_id"] == "20260620_061039"
    assert manifest["latest_gatekeeper_review_run_id"] == "20260619_201936"
