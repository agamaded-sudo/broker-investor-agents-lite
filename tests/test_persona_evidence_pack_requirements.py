"""Tests for BO-006 persona evidence pack requirements."""

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.personas.persona_evidence_pack_requirements import (
    build_persona_evidence_pack_requirements,
    build_persona_pack_checklists,
    derive_persona_evidence_gaps,
    load_metadata_diversity_recheck_manifest,
    write_persona_evidence_pack_requirements_report,
)


def _metadata() -> dict:
    return {
        "metadata_diversity_recheck_run_id": "metadata",
        "delayed_anchor_repair_run_id": "delayed",
        "walk_forward_repair_run_id": "walk",
        "outlier_repair_run_id": "outlier",
        "decomposition_run_id": "decomp",
        "backoffice_attribution_run_id": "backoffice",
        "investor_persona_attribution_run_id": "persona",
        "gatekeeper_run_id": "gatekeeper",
        "scorecard_run_id": "scorecard",
        "analysis_run_id": "analysis",
        "expanded_trial_run_id": "expanded",
        "backtest_run_id": "backtest",
        "concentration_classification": {
            "metadata_diversity_status": "materially_concentrated",
        },
    }


def _persona_attribution() -> dict:
    return {
        "attribution_run_id": "persona",
        "gatekeeper_decision": "hold",
        "progression_allowed": False,
        "persona_attributions": [
            {
                "persona": f"{persona} Agent",
                "persona_readiness_status": "persona_review_possible_after_repair",
            }
            for persona in ("Buffett", "Munger", "Fisher", "Lynch", "Bogle")
        ],
    }


def _write_fixture(outputs: Path) -> dict:
    meta_folder = outputs / "metadata_diversity_rechecks" / "metadata"
    meta_folder.mkdir(parents=True)
    meta_path = meta_folder / "metadata_diversity_recheck_report.json"
    meta_path.write_text(json.dumps(_metadata()), encoding="utf-8")
    (
        outputs
        / "metadata_diversity_rechecks"
        / "latest_metadata_diversity_recheck_manifest.json"
    ).write_text(
        json.dumps({"metadata_diversity_recheck_run_id": "metadata"}),
        encoding="utf-8",
    )
    linked = (
        (
            outputs / "delayed_anchor_repairs" / "delayed",
            "delayed_anchor_repair_report.json",
            {"delayed_anchor_repair_run_id": "delayed"},
        ),
        (
            outputs / "walk_forward_repair_plans" / "walk",
            "walk_forward_repair_plan_report.json",
            {"walk_forward_repair_run_id": "walk"},
        ),
        (
            outputs / "outlier_repair_paths" / "outlier",
            "outlier_repair_path_report.json",
            {"outlier_repair_run_id": "outlier"},
        ),
        (
            outputs / "backtest_driver_decompositions" / "decomp",
            "backtest_driver_decomposition_report.json",
            {"decomposition_run_id": "decomp"},
        ),
        (
            outputs / "investor_persona_attributions" / "persona",
            "investor_persona_attribution_report.json",
            _persona_attribution(),
        ),
        (
            outputs / "backoffice_evidence_quality_attributions" / "backoffice",
            "backoffice_evidence_quality_attribution_report.json",
            {"backoffice_attribution_run_id": "backoffice"},
        ),
    )
    for folder, filename, payload in linked:
        folder.mkdir(parents=True)
        (folder / filename).write_text(json.dumps(payload), encoding="utf-8")
    return {"metadata_path": meta_path}


def test_loads_latest_and_explicit_metadata_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    latest = load_metadata_diversity_recheck_manifest(outputs_root=outputs)
    explicit = load_metadata_diversity_recheck_manifest(
        outputs_root=outputs,
        metadata_diversity_recheck_run_id="metadata",
    )
    assert latest["metadata_diversity_recheck_run_id"] == "metadata"
    assert explicit["backtest_run_id"] == "backtest"


def test_missing_metadata_manifest_and_report_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="manifest not found"):
        load_metadata_diversity_recheck_manifest(outputs_root=outputs)
    source = _write_fixture(outputs)
    source["metadata_path"].unlink()
    with pytest.raises(FileNotFoundError, match="report not found"):
        write_persona_evidence_pack_requirements_report(outputs_root=outputs)


def test_persona_requirement_matrix_includes_all_personas() -> None:
    report = build_persona_evidence_pack_requirements(
        persona_evidence_pack_run_id="pack",
        generated_at="2026-06-17T00:00:00+00:00",
        metadata=_metadata(),
        delayed_anchor={},
        walk_forward={},
        outlier={},
        decomposition={},
        persona_attribution=_persona_attribution(),
        backoffice={},
    )
    personas = {item["persona"] for item in report.persona_requirement_matrix}
    assert personas == {"Buffett", "Munger", "Fisher", "Lynch", "Bogle"}
    assert all(not item["gatekeeper_allowed"] for item in report.persona_requirement_matrix)
    assert all(
        item["readiness_after_pack"] != "persona_review_ready"
        for item in report.persona_requirement_matrix
    )


def test_persona_checklists_include_required_evidence() -> None:
    checklists = build_persona_pack_checklists()
    assert "normalized owner earnings evidence" in checklists["Buffett"]
    assert "intrinsic value range with assumptions" in checklists["Buffett"]
    assert "incentives and agency risk evidence" in checklists["Munger"]
    assert "inversion/risk checklist" in checklists["Munger"]
    assert "qualitative growth evidence" in checklists["Fisher"]
    assert "customer / competitive scuttlebutt proxy evidence" in checklists["Fisher"]
    assert "company story evidence" in checklists["Lynch"]
    assert "category classification evidence" in checklists["Lynch"]
    assert "benchmark-relative evidence" in checklists["Bogle"]
    assert "index comparison evidence" in checklists["Bogle"]


def test_evidence_gap_linkage_includes_required_issues() -> None:
    gaps = derive_persona_evidence_gaps()
    all_issues = {issue for issues in gaps.values() for issue in issues}
    assert {
        "benchmark_relative_underperformance",
        "walk_forward_instability",
        "expanded_cohort_underperformance",
        "outlier_dependence",
        "delayed_anchor_effect",
        "metadata_diversity_partial_concentration",
        "persona_specific_evidence_gaps",
        "qualitative_depth_gaps",
    } <= all_issues
    assert "index_comparison_gap" in gaps["Bogle"]


def test_report_contains_artifacts_linkage_and_common_requirements() -> None:
    report = build_persona_evidence_pack_requirements(
        persona_evidence_pack_run_id="pack",
        generated_at="2026-06-17T00:00:00+00:00",
        metadata=_metadata(),
        delayed_anchor={},
        walk_forward={},
        outlier={},
        decomposition={},
        persona_attribution=_persona_attribution(),
        backoffice={},
    )
    assert report.persona_evidence_gap_linkage
    assert report.persona_required_artifacts
    assert report.persona_checklists
    common_artifacts = set(report.common_requirements["required_common_artifacts"])
    assert {
        "research_gatekeeper_report",
        "research_evidence_scorecard",
        "expanded_trial_results_analysis",
        "backtest_driver_decomposition",
        "outlier_repair_path",
        "walk_forward_repair_plan",
        "delayed_anchor_repair",
        "metadata_diversity_recheck",
    } <= common_artifacts
    artifact_names = {item["artifact"] for item in report.persona_required_artifacts}
    assert "bogle_index_comparison_pack" in artifact_names


def test_writer_outputs_json_markdown_csv_checklists_and_latest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    files = write_persona_evidence_pack_requirements_report(
        outputs_root=outputs,
        metadata_diversity_recheck_run_id="metadata",
        generated_at=datetime(2026, 6, 17, tzinfo=timezone.utc),
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.matrix_csv_path,
        files.gap_linkage_csv_path,
        files.required_artifacts_csv_path,
        files.checklists_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["persona_requirement_matrix"]
    assert payload["persona_evidence_gap_linkage"]
    assert payload["persona_required_artifacts"]
    assert payload["persona_checklists"]
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "Important Boundary",
        "Buffett Evidence Pack Requirements",
        "Munger Evidence Pack Requirements",
        "Fisher Evidence Pack Requirements",
        "Lynch Evidence Pack Requirements",
        "Bogle Evidence Pack Requirements",
        "Evidence Gap Linkage",
    ):
        assert section in markdown


@pytest.mark.parametrize("auto_latest", [False, True])
def test_cli_explicit_and_auto_latest(
    tmp_path: Path, auto_latest: bool
) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    args = [
        "build-persona-evidence-pack-requirements",
        "--outputs-root",
        str(outputs),
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(["--metadata-diversity-recheck-run-id", "metadata"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Persona-Specific Evidence Pack Requirements" in result.output
    assert "persona_count=5" in result.output
    assert "progression_allowed=false" in result.output
    assert (
        "recommended_next_work_order=BO-007 Bogle Benchmark / Index Comparison Pack"
        in result.output
    )
