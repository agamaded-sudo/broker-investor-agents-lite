"""Tests for BO-004 delayed anchor exposure repair."""

from datetime import datetime, timezone
import csv
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.backtesting.delayed_anchor_repair import (
    analyze_anchor_exposure,
    attribute_anchor_effect_by_cohort,
    attribute_anchor_effect_by_period,
    build_delayed_anchor_repair,
    build_delayed_anchor_retest_controls,
    load_walk_forward_repair_manifest,
    write_delayed_anchor_repair_report,
)
from broker_agents.cli import app


def _rows(include_anchor_column: bool = True) -> list[dict]:
    specs = [
        ("NVDA", "current_core", "Technology", "semiconductor", 0.20),
        ("AAPL", "current_core", "Technology", "consumer_platform", 0.10),
        ("NFLX", "expanded_cohort", "Communication Services", "consumer_platform", -0.20),
        ("ADBE", "expanded_cohort", "Technology", "software_platform", -0.10),
    ]
    rows = []
    for ticker, group, sector, category, base_relative in specs:
        for date, delayed in (
            ("2021-06-30", False),
            ("2021-12-31", True),
            ("2022-06-30", False),
        ):
            row = {
                "ticker": ticker,
                "signal_date": date,
                "coverage_guardrail_status": (
                    "research_usable_with_warnings" if delayed else "clean"
                ),
                "coverage_quality_label": (
                    "delayed_price_anchor" if delayed else "clean"
                ),
                "forward_return_12m": "0.10",
                "relative_return_12m": str(
                    base_relative + (0.08 if not delayed else -0.08)
                ),
                "max_drawdown_12m": "-0.20",
                "universe_group": group,
                "sector": sector,
                "category": category,
            }
            if include_anchor_column:
                row["has_delayed_price_anchor"] = str(delayed)
            rows.append(row)
    return rows


def _analysis() -> dict:
    return {
        "analysis_run_id": "analysis",
        "ticker_attribution": [
            {
                "ticker": ticker,
                "sector": sector,
                "category": category,
                "universe_group": group,
            }
            for ticker, group, sector, category in [
                ("NVDA", "current_core", "Technology", "semiconductor"),
                ("AAPL", "current_core", "Technology", "consumer_platform"),
                (
                    "NFLX",
                    "expanded_cohort",
                    "Communication Services",
                    "consumer_platform",
                ),
                ("ADBE", "expanded_cohort", "Technology", "software_platform"),
            ]
        ],
    }


def _walk_forward() -> dict:
    return {
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


def _write_fixture(outputs: Path, *, include_anchor_column: bool = True) -> dict:
    walk_folder = outputs / "walk_forward_repair_plans" / "walk"
    walk_folder.mkdir(parents=True)
    walk_path = walk_folder / "walk_forward_repair_plan_report.json"
    walk_path.write_text(json.dumps(_walk_forward()), encoding="utf-8")
    (
        outputs
        / "walk_forward_repair_plans"
        / "latest_walk_forward_repair_plan_manifest.json"
    ).write_text(
        json.dumps({"walk_forward_repair_run_id": "walk"}),
        encoding="utf-8",
    )
    for folder, filename, payload in (
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
            outputs / "backoffice_evidence_quality_attributions" / "backoffice",
            "backoffice_evidence_quality_attribution_report.json",
            {"backoffice_attribution_run_id": "backoffice"},
        ),
        (
            outputs / "research_evidence_scorecards" / "scorecard",
            "research_evidence_scorecard_report.json",
            {"scorecard_run_id": "scorecard"},
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
    rows = _rows(include_anchor_column=include_anchor_column)
    with (backtest_folder / "backtest_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return {"walk_path": walk_path}


def test_loads_latest_and_explicit_walk_forward_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    latest = load_walk_forward_repair_manifest(outputs_root=outputs)
    explicit = load_walk_forward_repair_manifest(
        outputs_root=outputs,
        walk_forward_repair_run_id="walk",
    )
    assert latest["walk_forward_repair_run_id"] == "walk"
    assert explicit["backtest_run_id"] == "backtest"


def test_missing_walk_forward_manifest_and_report_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="manifest not found"):
        load_walk_forward_repair_manifest(outputs_root=outputs)
    source = _write_fixture(outputs)
    source["walk_path"].unlink()
    with pytest.raises(FileNotFoundError, match="report not found"):
        write_delayed_anchor_repair_report(outputs_root=outputs)


def test_anchor_exposure_includes_required_buckets() -> None:
    exposure = analyze_anchor_exposure(_rows(), _analysis())
    buckets = {item["anchor_bucket"] for item in exposure}
    assert {"full_sample", "clean_anchor", "delayed_anchor", "unknown_anchor"} == buckets
    assert next(item for item in exposure if item["anchor_bucket"] == "full_sample")


def test_unknown_anchor_bucket_created_without_explicit_anchor_field() -> None:
    rows = [
        {
            "ticker": "AAA",
            "signal_date": "2022-06-30",
            "coverage_quality_label": "research_usable_with_warnings",
            "coverage_guardrail_status": "research_usable_with_warnings",
            "forward_return_12m": "0.10",
            "relative_return_12m": "-0.05",
            "max_drawdown_12m": "-0.20",
            "universe_group": "expanded_cohort",
        }
    ]
    exposure = analyze_anchor_exposure(rows, {})
    unknown = next(item for item in exposure if item["anchor_bucket"] == "unknown_anchor")
    assert unknown["records"] == 1


def test_period_and_cohort_anchor_attribution_are_created() -> None:
    period = attribute_anchor_effect_by_period(_rows(), _analysis())
    cohort = attribute_anchor_effect_by_cohort(_rows(), _analysis())
    assert period
    assert {item["cohort"] for item in cohort} == {
        "current_core",
        "expanded_cohort",
        "full_expanded_universe",
    }


def test_build_report_creates_classification_and_controls() -> None:
    report = build_delayed_anchor_repair(
        delayed_anchor_repair_run_id="repair",
        generated_at="2026-06-16T00:00:00+00:00",
        walk_forward=_walk_forward(),
        outlier={},
        decomposition={},
        backoffice={},
        scorecard={},
        analysis=_analysis(),
        rows=_rows(),
    )
    assert report.work_order_id == "BO-004"
    assert report.anchor_exposure_analysis
    assert report.period_anchor_attribution
    assert report.cohort_anchor_attribution
    assert report.anchor_impact_classification
    assert report.delayed_anchor_retest_controls
    assert (
        report.anchor_impact_classification["anchor_data_sufficiency_status"]
        == "anchor_buckets_available_without_exact_delay_days"
    )
    assert (
        report.recommended_next_work_order
        == "BO-005 Metadata Diversity Recheck"
    )


def test_retest_controls_include_required_controls() -> None:
    controls = build_delayed_anchor_retest_controls()
    text = json.dumps(controls)
    assert "clean-anchor and delayed-anchor records separately" in text
    assert "anchor exposure by date" in text
    assert "anchor exposure by cohort" in text
    assert "No future price information may be introduced" in text


def test_writer_outputs_json_markdown_csv_controls_and_latest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    files = write_delayed_anchor_repair_report(
        outputs_root=outputs,
        walk_forward_repair_run_id="walk",
        generated_at=datetime(2026, 6, 16, tzinfo=timezone.utc),
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.anchor_csv_path,
        files.period_csv_path,
        files.cohort_csv_path,
        files.retest_controls_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["anchor_exposure_analysis"]
    assert payload["period_anchor_attribution"]
    assert payload["cohort_anchor_attribution"]
    assert payload["anchor_impact_classification"]
    assert payload["delayed_anchor_retest_controls"]
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "Important Boundary",
        "Anchor Exposure Analysis",
        "Period Anchor Attribution",
        "Cohort Anchor Attribution",
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
        "build-delayed-anchor-repair",
        "--outputs-root",
        str(outputs),
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(["--walk-forward-repair-run-id", "walk"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Delayed Anchor Exposure Repair" in result.output
    assert "anchor_bucket_count=4" in result.output
    assert "recommended_next_work_order=BO-005 Metadata Diversity Recheck" in (
        result.output
    )
