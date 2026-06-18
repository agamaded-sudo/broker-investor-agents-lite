"""Tests for BO-008 Fisher qualitative growth evidence pack."""

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.personas.fisher_qualitative_growth_pack import (
    build_fisher_evidence_requirements_status,
    build_fisher_growth_risk_matrix,
    build_fisher_growth_summary,
    build_fisher_qualitative_evidence_matrix,
    build_fisher_qualitative_growth_pack,
    build_fisher_required_controls,
    build_fisher_scuttlebutt_proxy_matrix,
    load_bogle_benchmark_pack_manifest,
    load_bogle_benchmark_pack_report,
    load_metadata_diversity_recheck_report,
    load_persona_evidence_pack_report,
    write_fisher_qualitative_growth_pack_report,
)


def _bogle_pack() -> dict:
    return {
        "bogle_benchmark_pack_run_id": "bogle",
        "persona_evidence_pack_run_id": "persona_pack",
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
        "bogle_benchmark_summary": {
            "gatekeeper_decision": "hold",
            "progression_allowed": False,
            "bogle_review_allowed": False,
        },
    }


def _persona_pack() -> dict:
    return {
        "persona_evidence_pack_run_id": "persona_pack",
        "persona_checklists": {
            "Fisher": [
                "qualitative growth evidence",
                "product pipeline evidence",
                "customer / competitive scuttlebutt proxy evidence",
            ]
        },
    }


def _metadata() -> dict:
    return {
        "metadata_diversity_recheck_run_id": "metadata",
        "concentration_classification": {
            "metadata_diversity_status": "materially_concentrated",
        },
    }


def _walk_forward() -> dict:
    return {
        "walk_forward_repair_run_id": "walk",
        "walk_forward_repair_status": "completed",
    }


def _write_fixture(outputs: Path) -> None:
    bogle_folder = outputs / "bogle_benchmark_index_packs" / "bogle"
    bogle_folder.mkdir(parents=True)
    (bogle_folder / "bogle_benchmark_index_comparison_pack.json").write_text(
        json.dumps(_bogle_pack()),
        encoding="utf-8",
    )
    (
        outputs
        / "bogle_benchmark_index_packs"
        / "latest_bogle_benchmark_index_pack_manifest.json"
    ).write_text(
        json.dumps({"bogle_benchmark_pack_run_id": "bogle"}),
        encoding="utf-8",
    )
    linked = (
        (
            outputs / "persona_evidence_pack_requirements" / "persona_pack",
            "persona_evidence_pack_requirements_report.json",
            _persona_pack(),
        ),
        (
            outputs / "metadata_diversity_rechecks" / "metadata",
            "metadata_diversity_recheck_report.json",
            _metadata(),
        ),
        (
            outputs / "delayed_anchor_repairs" / "delayed",
            "delayed_anchor_repair_report.json",
            {"delayed_anchor_repair_run_id": "delayed"},
        ),
        (
            outputs / "walk_forward_repair_plans" / "walk",
            "walk_forward_repair_plan_report.json",
            _walk_forward(),
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
            outputs / "research_evidence_scorecards" / "scorecard",
            "research_evidence_scorecard_report.json",
            {"scorecard_run_id": "scorecard"},
        ),
        (
            outputs / "expanded_trial_analyses" / "analysis",
            "expanded_trial_analysis_report.json",
            {"analysis_run_id": "analysis"},
        ),
    )
    for folder, filename, payload in linked:
        folder.mkdir(parents=True)
        (folder / filename).write_text(json.dumps(payload), encoding="utf-8")


def test_loads_latest_and_explicit_bogle_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    latest = load_bogle_benchmark_pack_manifest(outputs_root=outputs)
    explicit = load_bogle_benchmark_pack_manifest(
        outputs_root=outputs,
        bogle_benchmark_pack_run_id="bogle",
    )
    assert latest["bogle_benchmark_pack_run_id"] == "bogle"
    assert explicit["backtest_run_id"] == "backtest"


def test_missing_bogle_manifest_and_report_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="Bogle benchmark pack manifest"):
        load_bogle_benchmark_pack_manifest(outputs_root=outputs)
    _write_fixture(outputs)
    (
        outputs
        / "bogle_benchmark_index_packs"
        / "bogle"
        / "bogle_benchmark_index_comparison_pack.json"
    ).unlink()
    with pytest.raises(FileNotFoundError, match="Bogle benchmark pack report"):
        write_fisher_qualitative_growth_pack_report(outputs_root=outputs)


def test_loads_linked_persona_and_metadata_reports(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    assert load_bogle_benchmark_pack_report(
        outputs_root=outputs, bogle_benchmark_pack_run_id="bogle"
    )
    assert load_persona_evidence_pack_report(
        outputs_root=outputs, persona_evidence_pack_run_id="persona_pack"
    )
    assert load_metadata_diversity_recheck_report(
        outputs_root=outputs, metadata_diversity_recheck_run_id="metadata"
    )


def test_fisher_growth_summary_blocks_review_and_keeps_hold() -> None:
    summary = build_fisher_growth_summary(
        fisher_pack_run_id="fisher",
        bogle_pack=_bogle_pack(),
        persona_pack=_persona_pack(),
        metadata=_metadata(),
        walk_forward=_walk_forward(),
    )
    assert summary["fisher_review_allowed"] is False
    assert summary["progression_allowed"] is False
    assert summary["gatekeeper_decision"] == "hold"
    assert summary["qualitative_depth_status"] == "qualitative_evidence_gaps_remain"


def test_qualitative_evidence_matrix_includes_required_dimensions() -> None:
    matrix = build_fisher_qualitative_evidence_matrix()
    dimensions = {row["evidence_dimension"] for row in matrix}
    assert {
        "product_pipeline",
        "R&D_innovation",
        "sales_organization",
        "market_expansion",
        "management_depth",
        "customer_evidence",
        "competitive_position",
        "durable_growth_runway",
        "qualitative_growth_consistency",
        "cohort_specific_growth_evidence",
        "metadata_concentration_controls",
        "walk_forward_stability_controls",
        "anchor_controls",
        "outlier_controls",
        "no_recommendation_boundary",
    } <= dimensions
    assert any(
        row["current_status"] == "missing_or_insufficient"
        for row in matrix
        if row["evidence_dimension"] == "product_pipeline"
    )


def test_scuttlebutt_proxy_matrix_includes_required_proxy_areas() -> None:
    matrix = build_fisher_scuttlebutt_proxy_matrix()
    areas = {row["proxy_area"] for row in matrix}
    assert {
        "customer_adoption",
        "product_quality",
        "sales_execution",
        "competitive_feedback",
        "innovation_validation",
    } <= areas
    assert all(row["current_status"] == "unavailable_locally" for row in matrix)


def test_growth_risk_matrix_includes_required_risks() -> None:
    risks = {row["risk_code"] for row in build_fisher_growth_risk_matrix()}
    assert {
        "qualitative_depth_gap",
        "scuttlebutt_proxy_gap",
        "metadata_concentration_limits_generalization",
        "expanded_cohort_underperformance",
        "walk_forward_instability",
        "outlier_dependence",
        "delayed_anchor_effect",
        "no_persona_review_until_gatekeeper_allows",
    } <= risks


def test_fisher_requirements_and_controls_include_boundaries() -> None:
    requirements = build_fisher_evidence_requirements_status()
    codes = {row["requirement_code"] for row in requirements}
    assert {
        "qualitative_growth_evidence",
        "product_pipeline_evidence",
        "R&D_or_innovation_evidence",
        "sales_organization_evidence",
        "market_expansion_evidence",
        "management_depth_evidence",
        "customer_competitive_scuttlebutt_proxy",
        "durable_growth_runway_evidence",
        "no_recommendation_boundary",
    } <= codes
    controls = build_fisher_required_controls()
    assert "No Fisher decision." in controls["safety_constraints"]


def test_fisher_pack_json_sections_are_created() -> None:
    report = build_fisher_qualitative_growth_pack(
        fisher_growth_pack_run_id="fisher",
        generated_at="2026-06-18T00:00:00+00:00",
        bogle_pack=_bogle_pack(),
        persona_pack=_persona_pack(),
        metadata=_metadata(),
        delayed_anchor={},
        walk_forward=_walk_forward(),
        outlier={},
        decomposition={},
        scorecard={},
        expanded_analysis={},
    )
    payload = report.to_dict()
    assert payload["fisher_growth_summary"]
    assert payload["fisher_qualitative_evidence_matrix"]
    assert payload["fisher_scuttlebutt_proxy_matrix"]
    assert payload["fisher_growth_risk_matrix"]
    assert payload["fisher_evidence_requirements_status"]
    assert report.recommended_next_work_order == (
        "BO-009 Buffett/Munger Quality and Risk Pack"
    )


def test_writer_outputs_json_markdown_csv_controls_and_latest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    files = write_fisher_qualitative_growth_pack_report(
        outputs_root=outputs,
        bogle_benchmark_pack_run_id="bogle",
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.qualitative_matrix_csv_path,
        files.scuttlebutt_proxy_csv_path,
        files.growth_risk_csv_path,
        files.requirements_status_csv_path,
        files.required_controls_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["fisher_growth_summary"]["fisher_review_allowed"] is False
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "Important Boundary",
        "Qualitative Evidence Matrix",
        "Scuttlebutt Proxy Matrix",
        "Fisher Growth Risk Matrix",
        "What This Does Not Suggest",
    ):
        assert section in markdown


@pytest.mark.parametrize("auto_latest", [False, True])
def test_cli_explicit_and_auto_latest(tmp_path: Path, auto_latest: bool) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    args = [
        "build-fisher-qualitative-growth-pack",
        "--outputs-root",
        str(outputs),
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(["--bogle-benchmark-pack-run-id", "bogle"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Fisher Qualitative Growth Evidence Pack" in result.output
    assert "fisher_review_allowed=false" in result.output
    assert "gatekeeper_decision=hold" in result.output
    assert (
        "recommended_next_work_order=BO-009 Buffett/Munger Quality and Risk Pack"
        in result.output
    )
