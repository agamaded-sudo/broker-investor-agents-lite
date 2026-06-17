"""Tests for BO-007 Bogle benchmark/index comparison pack."""

import csv
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.personas.bogle_benchmark_index_pack import (
    build_bogle_benchmark_index_pack,
    build_bogle_benchmark_summary,
    build_bogle_evidence_requirements_status,
    build_bogle_required_controls,
    build_concentration_risk_matrix,
    build_index_comparison_matrix,
    load_delayed_anchor_repair_report,
    load_metadata_diversity_recheck_report,
    load_outlier_repair_report,
    load_persona_evidence_pack_manifest,
    load_walk_forward_repair_report,
    write_bogle_benchmark_index_pack_report,
)


def _rows() -> list[dict]:
    specs = [
        ("NVDA", "current_core", "2021-06-30", "clean", 0.30, 0.18),
        ("AAPL", "current_core", "2021-06-30", "clean", 0.12, 0.10),
        ("NFLX", "consumer_platforms", "2021-06-30", "clean", -0.08, -0.12),
        ("ADBE", "software_platforms", "2021-06-30", "clean", -0.04, -0.10),
        ("NVDA", "current_core", "2022-06-30", "warning", 0.45, 0.22),
        ("AAPL", "current_core", "2022-06-30", "warning", 0.04, 0.02),
        ("NFLX", "consumer_platforms", "2022-06-30", "warning", -0.20, -0.24),
        ("ADBE", "software_platforms", "2022-06-30", "warning", -0.10, -0.18),
    ]
    rows = []
    for ticker, group, date, coverage, forward, relative in specs:
        rows.append(
            {
                "ticker": ticker,
                "as_of_date": date,
                "signal_date": date,
                "universe_group": group,
                "sector": "Technology",
                "category": "software_platform" if ticker == "ADBE" else "consumer_platform",
                "coverage_guardrail_status": coverage,
                "has_delayed_price_anchor": str(coverage == "warning"),
                "forward_return_12m": str(forward),
                "relative_return_12m": str(relative),
                "max_drawdown_12m": "-0.10",
            }
        )
    return rows


def _persona_pack() -> dict:
    return {
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
        "persona_requirement_matrix": [
            {"persona": "Bogle", "readiness_after_pack": "requirements_defined_only"}
        ],
    }


def _metadata() -> dict:
    return {
        "metadata_diversity_recheck_run_id": "metadata",
        "concentration_classification": {
            "metadata_diversity_status": "materially_concentrated",
            "sector_concentration_status": "materially_concentrated",
            "category_concentration_status": "partially_concentrated",
            "universe_group_concentration_status": "partially_concentrated",
            "main_metadata_finding": "Metadata concentration limits generalization.",
        },
    }


def _delayed_anchor() -> dict:
    return {
        "delayed_anchor_repair_run_id": "delayed",
        "anchor_impact_classification": {
            "delayed_anchor_exposure_status": "delayed_anchor_moderate",
            "main_anchor_finding": "Clean-anchor and delayed-anchor evidence need separation.",
        },
    }


def _walk_forward() -> dict:
    return {
        "walk_forward_repair_run_id": "walk",
        "walk_forward_repair_status": "completed",
        "supportive_date_dependence": {
            "main_supportive_date_finding": "2021-06-30 remains supportive."
        },
    }


def _outlier() -> dict:
    return {
        "outlier_repair_run_id": "outlier",
        "scenario_analysis": [
            {
                "scenario_code": "ex_nvda",
                "records": 6,
                "median_forward_return_12m": -0.02,
                "median_relative_return_12m": -0.11,
                "hit_rate_vs_benchmark_12m": 0.166667,
            },
            {
                "scenario_code": "ex_supportive_date_2021_06_30",
                "records": 4,
                "median_forward_return_12m": -0.03,
                "median_relative_return_12m": -0.08,
                "hit_rate_vs_benchmark_12m": 0.25,
            },
        ],
        "dependence_classification": {
            "overall_outlier_repair_status": "outlier_dependence_confirmed_or_needs_retest",
            "top_contributor_dependence_status": "moderate_dependence",
            "main_outlier_finding": "Evidence depends on top contributors.",
        },
    }


def _decomposition() -> dict:
    return {
        "decomposition_run_id": "decomp",
        "driver_summary": {
            "expanded_cohort_explanation": "Expanded cohort weakened the current core."
        },
    }


def _write_fixture(outputs: Path) -> None:
    persona_folder = outputs / "persona_evidence_pack_requirements" / "persona_pack"
    persona_folder.mkdir(parents=True)
    (persona_folder / "persona_evidence_pack_requirements_report.json").write_text(
        json.dumps(_persona_pack()),
        encoding="utf-8",
    )
    (
        outputs
        / "persona_evidence_pack_requirements"
        / "latest_persona_evidence_pack_requirements_manifest.json"
    ).write_text(
        json.dumps({"persona_evidence_pack_run_id": "persona_pack"}),
        encoding="utf-8",
    )
    linked = (
        (
            outputs / "metadata_diversity_rechecks" / "metadata",
            "metadata_diversity_recheck_report.json",
            _metadata(),
        ),
        (
            outputs / "delayed_anchor_repairs" / "delayed",
            "delayed_anchor_repair_report.json",
            _delayed_anchor(),
        ),
        (
            outputs / "walk_forward_repair_plans" / "walk",
            "walk_forward_repair_plan_report.json",
            _walk_forward(),
        ),
        (
            outputs / "outlier_repair_paths" / "outlier",
            "outlier_repair_path_report.json",
            _outlier(),
        ),
        (
            outputs / "backtest_driver_decompositions" / "decomp",
            "backtest_driver_decomposition_report.json",
            _decomposition(),
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

    backtest_folder = outputs / "backtests" / "backtest"
    backtest_folder.mkdir(parents=True)
    with (backtest_folder / "backtest_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=list(_rows()[0]))
        writer.writeheader()
        writer.writerows(_rows())


def test_loads_latest_and_explicit_persona_pack_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    latest = load_persona_evidence_pack_manifest(outputs_root=outputs)
    explicit = load_persona_evidence_pack_manifest(
        outputs_root=outputs,
        persona_evidence_pack_run_id="persona_pack",
    )
    assert latest["persona_evidence_pack_run_id"] == "persona_pack"
    assert explicit["backtest_run_id"] == "backtest"


def test_missing_persona_manifest_and_report_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="Persona evidence pack manifest"):
        load_persona_evidence_pack_manifest(outputs_root=outputs)
    _write_fixture(outputs)
    (
        outputs
        / "persona_evidence_pack_requirements"
        / "persona_pack"
        / "persona_evidence_pack_requirements_report.json"
    ).unlink()
    with pytest.raises(FileNotFoundError, match="Persona evidence pack report"):
        write_bogle_benchmark_index_pack_report(outputs_root=outputs)


def test_loads_linked_reports(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    assert load_metadata_diversity_recheck_report(
        outputs_root=outputs, metadata_diversity_recheck_run_id="metadata"
    )
    assert load_delayed_anchor_repair_report(
        outputs_root=outputs, delayed_anchor_repair_run_id="delayed"
    )
    assert load_walk_forward_repair_report(
        outputs_root=outputs, walk_forward_repair_run_id="walk"
    )
    assert load_outlier_repair_report(outputs_root=outputs, outlier_repair_run_id="outlier")


def test_bogle_summary_blocks_review_and_keeps_gatekeeper_hold() -> None:
    summary = build_bogle_benchmark_summary(
        bogle_pack_run_id="bogle",
        persona_pack=_persona_pack(),
        metadata=_metadata(),
        delayed_anchor=_delayed_anchor(),
        walk_forward=_walk_forward(),
        outlier=_outlier(),
    )
    assert summary["bogle_review_allowed"] is False
    assert summary["progression_allowed"] is False
    assert summary["gatekeeper_decision"] == "hold"
    assert summary["review_status"].endswith("gatekeeper_hold")


def test_index_comparison_matrix_includes_required_views() -> None:
    matrix = build_index_comparison_matrix(rows=_rows(), outlier=_outlier())
    views = {row["comparison_view"] for row in matrix}
    assert {
        "full_sample",
        "current_core",
        "expanded_cohort",
        "clean_anchor",
        "delayed_anchor",
        "ex_supportive_date",
        "ex_nvda",
        "post_2021_periods",
        "supportive_period_only",
    } <= views


def test_concentration_risk_matrix_includes_required_dimensions() -> None:
    matrix = build_concentration_risk_matrix(
        metadata=_metadata(),
        delayed_anchor=_delayed_anchor(),
        outlier=_outlier(),
        decomposition=_decomposition(),
        walk_forward=_walk_forward(),
    )
    dimensions = {row["concentration_dimension"] for row in matrix}
    assert {
        "single_stock_or_top_contributor_dependence",
        "current_core_vs_expanded_cohort",
        "sector_concentration",
        "category_concentration",
        "universe_group_concentration",
        "supportive_date_dependence",
        "delayed_anchor_exposure",
        "benchmark_relative_underperformance",
        "metadata_concentration",
    } <= dimensions


def test_bogle_requirements_and_controls_include_boundaries() -> None:
    requirements = build_bogle_evidence_requirements_status()
    codes = {row["requirement_code"] for row in requirements}
    assert {
        "broad_index_comparison",
        "benchmark_relative_performance",
        "concentration_risk_analysis",
        "single_stock_vs_index_limitations",
        "clean_anchor_vs_delayed_anchor",
        "walk_forward_stability",
        "outlier_dependence",
        "no_recommendation_boundary",
    } <= codes
    controls = build_bogle_required_controls()
    assert "No index recommendation." in controls["safety_constraints"]


def test_bogle_pack_json_sections_are_created() -> None:
    report = build_bogle_benchmark_index_pack(
        bogle_benchmark_pack_run_id="bogle",
        generated_at="2026-06-17T00:00:00+00:00",
        persona_pack=_persona_pack(),
        metadata=_metadata(),
        delayed_anchor=_delayed_anchor(),
        walk_forward=_walk_forward(),
        outlier=_outlier(),
        decomposition=_decomposition(),
        scorecard={},
        expanded_analysis={},
        backtest_rows=_rows(),
    )
    payload = report.to_dict()
    assert payload["bogle_benchmark_summary"]
    assert payload["index_comparison_matrix"]
    assert payload["concentration_risk_matrix"]
    assert payload["bogle_evidence_requirements_status"]
    assert report.recommended_next_work_order == (
        "BO-008 Fisher Qualitative Growth Evidence Pack"
    )


def test_writer_outputs_json_markdown_csv_controls_and_latest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    files = write_bogle_benchmark_index_pack_report(
        outputs_root=outputs,
        persona_evidence_pack_run_id="persona_pack",
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.index_matrix_csv_path,
        files.concentration_risk_csv_path,
        files.requirements_status_csv_path,
        files.required_controls_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["bogle_benchmark_summary"]["bogle_review_allowed"] is False
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "Important Boundary",
        "Index Comparison Matrix",
        "Concentration Risk Matrix",
        "Evidence Requirements Status",
        "What This Does Not Suggest",
    ):
        assert section in markdown


@pytest.mark.parametrize("auto_latest", [False, True])
def test_cli_explicit_and_auto_latest(tmp_path: Path, auto_latest: bool) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    args = [
        "build-bogle-benchmark-index-pack",
        "--outputs-root",
        str(outputs),
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(["--persona-evidence-pack-run-id", "persona_pack"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Bogle Benchmark / Index Comparison Pack" in result.output
    assert "bogle_review_allowed=false" in result.output
    assert "gatekeeper_decision=hold" in result.output
    assert (
        "recommended_next_work_order=BO-008 Fisher Qualitative Growth Evidence Pack"
        in result.output
    )
