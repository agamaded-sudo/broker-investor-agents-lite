"""Tests for BO-005 metadata diversity recheck."""

from datetime import datetime, timezone
import csv
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.backtesting.metadata_diversity_recheck import (
    analyze_category_diversity,
    analyze_cohort_diversity,
    analyze_investor_interest_diversity,
    analyze_sector_diversity,
    analyze_universe_group_diversity,
    build_metadata_diversity_recheck,
    build_metadata_matrix,
    classify_metadata_concentration,
    load_delayed_anchor_repair_manifest,
    write_metadata_diversity_recheck_report,
)
from broker_agents.cli import app


def _rows(include_metadata: bool = True) -> list[dict]:
    specs = [
        ("NVDA", "current_core", "Technology", "semiconductor", 0.20),
        ("AAPL", "current_core", "Technology", "consumer_platform", 0.10),
        ("MSFT", "current_core", "Technology", "software_platform", 0.08),
        ("COST", "current_core", "Consumer Staples", "retail", 0.06),
        ("NFLX", "consumer_platforms", "Communication Services", "consumer_platform", -0.20),
        ("ADBE", "software_platforms", "Technology", "software_platform", -0.12),
    ]
    rows = []
    for ticker, group, sector, category, relative in specs:
        for date in ("2021-06-30", "2022-06-30"):
            row = {
                "ticker": ticker,
                "signal_date": date,
                "coverage_guardrail_status": "clean",
                "coverage_quality_label": "clean",
                "has_delayed_price_anchor": "False",
                "relative_return_12m": str(relative),
                "buffett_interest_level": "Watchlist Interest",
                "munger_interest_level": "Conditional Interest",
                "fisher_interest_level": "Needs More Evidence",
                "lynch_interest_level": "Watchlist Interest",
                "bogle_interest_level": "Low Interest",
                "source_verification_status": "partially verified",
                "promotion_blocking_bucket": "moderate_blockers",
            }
            if include_metadata:
                row.update(
                    {
                        "universe_group": group,
                        "sector": sector,
                        "category": category,
                    }
                )
            rows.append(row)
    return rows


def _analysis() -> dict:
    return {
        "analysis_run_id": "analysis",
        "ticker_attribution": [
            {
                "ticker": ticker,
                "universe_group": group,
                "sector": sector,
                "category": category,
            }
            for ticker, group, sector, category in [
                ("NVDA", "current_core", "Technology", "semiconductor"),
                ("AAPL", "current_core", "Technology", "consumer_platform"),
                ("MSFT", "current_core", "Technology", "software_platform"),
                ("COST", "current_core", "Consumer Staples", "retail"),
                (
                    "NFLX",
                    "consumer_platforms",
                    "Communication Services",
                    "consumer_platform",
                ),
                ("ADBE", "software_platforms", "Technology", "software_platform"),
            ]
        ],
    }


def _delayed_anchor() -> dict:
    return {
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
    }


def _write_fixture(outputs: Path, *, include_metadata: bool = True) -> dict:
    delayed_folder = outputs / "delayed_anchor_repairs" / "delayed"
    delayed_folder.mkdir(parents=True)
    delayed_path = delayed_folder / "delayed_anchor_repair_report.json"
    delayed_path.write_text(json.dumps(_delayed_anchor()), encoding="utf-8")
    (
        outputs
        / "delayed_anchor_repairs"
        / "latest_delayed_anchor_repair_manifest.json"
    ).write_text(
        json.dumps({"delayed_anchor_repair_run_id": "delayed"}),
        encoding="utf-8",
    )
    for folder, filename, payload in (
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
            outputs / "expanded_trial_analyses" / "analysis",
            "expanded_trial_analysis_report.json",
            _analysis(),
        ),
    ):
        folder.mkdir(parents=True)
        (folder / filename).write_text(json.dumps(payload), encoding="utf-8")
    backtest_folder = outputs / "backtests" / "backtest"
    backtest_folder.mkdir(parents=True)
    rows = _rows(include_metadata=include_metadata)
    with (backtest_folder / "backtest_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return {"delayed_path": delayed_path}


def test_loads_latest_and_explicit_delayed_anchor_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    latest = load_delayed_anchor_repair_manifest(outputs_root=outputs)
    explicit = load_delayed_anchor_repair_manifest(
        outputs_root=outputs,
        delayed_anchor_repair_run_id="delayed",
    )
    assert latest["delayed_anchor_repair_run_id"] == "delayed"
    assert explicit["backtest_run_id"] == "backtest"


def test_missing_delayed_anchor_manifest_and_report_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="manifest not found"):
        load_delayed_anchor_repair_manifest(outputs_root=outputs)
    source = _write_fixture(outputs)
    source["delayed_path"].unlink()
    with pytest.raises(FileNotFoundError, match="report not found"):
        write_metadata_diversity_recheck_report(outputs_root=outputs)


def test_metadata_matrix_fields_and_unknowns() -> None:
    matrix = build_metadata_matrix(_rows(include_metadata=False), {})
    assert matrix
    row = matrix[0]
    for field in ("ticker", "cohort", "universe_group", "sector", "category"):
        assert field in row
    assert any(item["sector"] == "unknown" for item in matrix)


def test_diversity_analyses_are_created() -> None:
    matrix = build_metadata_matrix(_rows(), _analysis())
    assert analyze_sector_diversity(matrix)
    assert analyze_category_diversity(matrix)
    assert analyze_universe_group_diversity(matrix)
    assert analyze_cohort_diversity(matrix)
    assert analyze_investor_interest_diversity(matrix)


def test_classification_and_retest_controls_are_created() -> None:
    matrix = build_metadata_matrix(_rows(), _analysis())
    sector = analyze_sector_diversity(matrix)
    category = analyze_category_diversity(matrix)
    universe = analyze_universe_group_diversity(matrix)
    cohort = analyze_cohort_diversity(matrix)
    interest = analyze_investor_interest_diversity(matrix)
    classification = classify_metadata_concentration(
        matrix=matrix,
        sector=sector,
        category=category,
        universe_group=universe,
        cohort=cohort,
        investor_interest=interest,
    )
    for key in (
        "metadata_diversity_status",
        "sector_concentration_status",
        "category_concentration_status",
        "universe_group_concentration_status",
        "cohort_concentration_status",
        "investor_interest_diversity_status",
        "metadata_effect_on_hold_status",
    ):
        assert key in classification


def test_build_report_includes_expected_sections() -> None:
    report = build_metadata_diversity_recheck(
        metadata_diversity_recheck_run_id="meta",
        generated_at="2026-06-17T00:00:00+00:00",
        delayed_anchor=_delayed_anchor(),
        walk_forward={},
        outlier={},
        decomposition={},
        analysis=_analysis(),
        rows=_rows(),
    )
    assert report.work_order_id == "BO-005"
    assert report.metadata_matrix_summary
    assert report.sector_diversity_analysis
    assert report.category_diversity_analysis
    assert report.universe_group_diversity_analysis
    assert report.cohort_diversity_analysis
    assert report.investor_interest_diversity_analysis
    assert report.concentration_classification
    assert report.metadata_retest_controls
    assert report.recommended_next_work_order == (
        "BO-006 Persona-Specific Evidence Pack Requirements"
    )


def test_metadata_retest_controls_include_required_controls() -> None:
    report = build_metadata_diversity_recheck(
        metadata_diversity_recheck_run_id="meta",
        generated_at="2026-06-17T00:00:00+00:00",
        delayed_anchor=_delayed_anchor(),
        walk_forward={},
        outlier={},
        decomposition={},
        analysis=_analysis(),
        rows=_rows(),
    )
    text = json.dumps(report.metadata_retest_controls)
    assert "current_core and expanded_cohort separately" in text
    assert "sector and category exposure separately" in text
    assert "universe_group exposure separately" in text
    assert "Do not generalize from concentrated metadata groups" in text


def test_writer_outputs_json_markdown_csv_controls_and_latest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    files = write_metadata_diversity_recheck_report(
        outputs_root=outputs,
        delayed_anchor_repair_run_id="delayed",
        generated_at=datetime(2026, 6, 17, tzinfo=timezone.utc),
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.metadata_matrix_csv_path,
        files.sector_csv_path,
        files.category_csv_path,
        files.universe_group_csv_path,
        files.cohort_csv_path,
        files.investor_interest_csv_path,
        files.retest_controls_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["metadata_matrix_summary"]
    assert payload["sector_diversity_analysis"]
    assert payload["category_diversity_analysis"]
    assert payload["universe_group_diversity_analysis"]
    assert payload["cohort_diversity_analysis"]
    assert payload["investor_interest_diversity_analysis"]
    assert payload["concentration_classification"]
    assert payload["metadata_retest_controls"]
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "Important Boundary",
        "Metadata Matrix Summary",
        "Sector Diversity",
        "Category Diversity",
        "Universe Group Diversity",
        "Cohort Diversity",
        "Retest Controls",
    ):
        assert section in markdown


@pytest.mark.parametrize("auto_latest", [False, True])
def test_cli_explicit_and_auto_latest(
    tmp_path: Path, auto_latest: bool
) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    args = [
        "build-metadata-diversity-recheck",
        "--outputs-root",
        str(outputs),
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(["--delayed-anchor-repair-run-id", "delayed"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Metadata Diversity Recheck" in result.output
    assert "ticker_count=6" in result.output
    assert (
        "recommended_next_work_order=BO-006 Persona-Specific Evidence Pack Requirements"
        in result.output
    )
