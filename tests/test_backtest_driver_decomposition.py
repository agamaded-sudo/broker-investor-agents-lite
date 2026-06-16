"""Tests for BO-001 backtest driver decomposition."""

from datetime import datetime, timezone
import csv
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from broker_agents.backtesting.backtest_driver_decomposition import (
    build_backtest_driver_decomposition,
    decompose_by_ticker,
    load_backoffice_attribution_manifest,
    write_backtest_driver_decomposition_report,
)
from broker_agents.cli import app


def _rows() -> list[dict]:
    tickers = [
        ("AAA", "current_core", "Technology", "software"),
        ("BBB", "expanded_cohort", "Consumer", "platform"),
        ("CCC", "expanded_cohort", "Technology", "semiconductor"),
    ]
    dates = ["2021-06-30", "2022-06-30", "2023-06-30"]
    rows = []
    for ticker, group, sector, category in tickers:
        for index, date in enumerate(dates):
            relative = (
                0.12
                if ticker == "AAA"
                else -0.14
                if ticker == "BBB"
                else -0.04
            )
            rows.append(
                {
                    "ticker": ticker,
                    "signal_date": date,
                    "coverage_guardrail_status": (
                        "clean" if index == 0 else "research_usable_with_warnings"
                    ),
                    "coverage_quality_label": (
                        "clean" if index == 0 else "delayed_price_anchor"
                    ),
                    "forward_return_12m": "0.10",
                    "relative_return_12m": str(relative),
                    "max_drawdown_12m": "-0.10",
                    "universe_group": group,
                    "sector": sector,
                    "category": category,
                }
            )
    return rows


def _analysis() -> dict:
    return {
        "analysis_run_id": "analysis",
        "ticker_attribution": [
            {
                "ticker": "AAA",
                "sector": "Technology",
                "category": "software",
                "universe_group": "current_core",
            },
            {
                "ticker": "BBB",
                "sector": "Consumer",
                "category": "platform",
                "universe_group": "expanded_cohort",
            },
            {
                "ticker": "CCC",
                "sector": "Technology",
                "category": "semiconductor",
                "universe_group": "expanded_cohort",
            },
        ],
        "date_attribution": [
            {"as_of_date": "2021-06-30", "period_label": "supportive_period"},
            {"as_of_date": "2022-06-30", "period_label": "negative_period"},
        ],
    }


def _backoffice() -> dict:
    return {
        "backoffice_attribution_run_id": "backoffice",
        "investor_persona_attribution_run_id": "persona",
        "gatekeeper_run_id": "gate",
        "scorecard_run_id": "scorecard",
        "analysis_run_id": "analysis",
        "expanded_trial_run_id": "expanded",
        "backtest_run_id": "backtest",
    }


def _write_fixture(outputs: Path) -> dict:
    backoffice_folder = (
        outputs / "backoffice_evidence_quality_attributions" / "backoffice"
    )
    backoffice_folder.mkdir(parents=True)
    backoffice_path = (
        backoffice_folder / "backoffice_evidence_quality_attribution_report.json"
    )
    backoffice_path.write_text(json.dumps(_backoffice()), encoding="utf-8")
    (outputs / "backoffice_evidence_quality_attributions" / (
        "latest_backoffice_evidence_quality_attribution_manifest.json"
    )).write_text(
        json.dumps({"backoffice_attribution_run_id": "backoffice"}),
        encoding="utf-8",
    )
    analysis_folder = outputs / "expanded_trial_analyses" / "analysis"
    analysis_folder.mkdir(parents=True)
    (analysis_folder / "expanded_trial_analysis_report.json").write_text(
        json.dumps(_analysis()), encoding="utf-8"
    )
    expanded_folder = outputs / "expanded_ticker_trials" / "expanded"
    expanded_folder.mkdir(parents=True)
    (expanded_folder / "expanded_ticker_trial_summary.json").write_text(
        json.dumps({"sample_size_after_dedupe": 9}), encoding="utf-8"
    )
    backtest_folder = outputs / "backtests" / "backtest"
    backtest_folder.mkdir(parents=True)
    (backtest_folder / "backtest_manifest.json").write_text(
        json.dumps({"sample_size_after_dedupe": 9}), encoding="utf-8"
    )
    with (backtest_folder / "backtest_results.csv").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_rows()[0]))
        writer.writeheader()
        writer.writerows(_rows())
    return {"backoffice_path": backoffice_path}


def test_loads_latest_and_explicit_backoffice_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    latest = load_backoffice_attribution_manifest(outputs_root=outputs)
    explicit = load_backoffice_attribution_manifest(
        outputs_root=outputs,
        backoffice_attribution_run_id="backoffice",
    )
    assert latest["backoffice_attribution_run_id"] == "backoffice"
    assert explicit["backtest_run_id"] == "backtest"


def test_missing_backoffice_manifest_and_report_raise(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    with pytest.raises(FileNotFoundError, match="manifest not found"):
        load_backoffice_attribution_manifest(outputs_root=outputs)
    source = _write_fixture(outputs)
    source["backoffice_path"].unlink()
    with pytest.raises(FileNotFoundError, match="report not found"):
        write_backtest_driver_decomposition_report(outputs_root=outputs)


def test_driver_tables_and_labels_are_created() -> None:
    report = build_backtest_driver_decomposition(
        decomposition_run_id="decomp",
        generated_at="2026-06-16T00:00:00+00:00",
        backoffice=_backoffice(),
        analysis=_analysis(),
        expanded_summary={"sample_size_after_dedupe": 9},
        backtest_manifest={},
        rows=_rows(),
    )
    assert len(report.ticker_drivers) == 3
    assert len(report.date_drivers) == 3
    assert {item["cohort"] for item in report.cohort_drivers} == {
        "current_core",
        "expanded_cohort",
        "full_expanded_universe",
    }
    assert report.sector_drivers
    assert report.category_drivers
    assert report.universe_group_drivers
    labels = {item["driver_label"] for item in report.ticker_drivers}
    assert "positive_driver" in labels
    assert "negative_driver" in labels or "severe_negative_driver" in labels


def test_absolute_relative_reconciliation_and_summary() -> None:
    report = build_backtest_driver_decomposition(
        decomposition_run_id="decomp",
        generated_at="2026-06-16T00:00:00+00:00",
        backoffice=_backoffice(),
        analysis=_analysis(),
        expanded_summary={"sample_size_after_dedupe": 9},
        backtest_manifest={},
        rows=_rows(),
    )
    assert report.reconciliation["reconciliation_status"] == "reconciled"
    assert report.reconciliation["rows_reconciled"] == 9
    assert report.absolute_vs_relative_decomposition["absolute_positive"] is True
    assert (
        report.driver_summary["recommended_next_work_order"]
        == "BO-002 Outlier and Ex-NVDA Repair Path"
    )
    comparison = report.driver_summary["core_vs_expanded_comparison"]
    assert comparison["relative_gap_expanded_minus_core"] < 0


def test_decompose_by_ticker_handles_insufficient_evidence() -> None:
    row = _rows()[0]
    drivers = decompose_by_ticker([row])
    assert drivers[0]["driver_label"] == "insufficient_evidence"


def test_writer_outputs_json_markdown_csvs_and_latest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    files = write_backtest_driver_decomposition_report(
        outputs_root=outputs,
        backoffice_attribution_run_id="backoffice",
        generated_at=datetime(2026, 6, 16, tzinfo=timezone.utc),
    )
    for path in (
        files.markdown_path,
        files.json_path,
        files.ticker_csv_path,
        files.date_csv_path,
        files.cohort_csv_path,
        files.sector_csv_path,
        files.category_csv_path,
        files.universe_group_csv_path,
        files.latest_manifest_path,
    ):
        assert path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["reconciliation"]["reconciliation_status"] == "reconciled"
    assert payload["ticker_drivers"]
    assert payload["date_drivers"]
    assert payload["cohort_drivers"]
    assert payload["driver_summary"]
    markdown = files.markdown_path.read_text(encoding="utf-8")
    for section in (
        "Important Boundary",
        "Reconciliation",
        "Absolute vs Benchmark-Relative Evidence",
        "Ticker Driver Decomposition",
        "Cohort Driver Decomposition",
        "Main Driver Findings",
    ):
        assert section in markdown


@pytest.mark.parametrize("auto_latest", [False, True])
def test_cli_explicit_and_auto_latest(
    tmp_path: Path, auto_latest: bool
) -> None:
    outputs = tmp_path / "outputs"
    _write_fixture(outputs)
    args = [
        "build-backtest-driver-decomposition",
        "--outputs-root",
        str(outputs),
    ]
    if auto_latest:
        args.append("--auto-latest")
    else:
        args.extend(["--backoffice-attribution-run-id", "backoffice"])
    result = CliRunner().invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "Backtest Driver Decomposition" in result.output
    assert "reconciliation_status=reconciled" in result.output
    assert "recommended_next_work_order=BO-002 Outlier and Ex-NVDA Repair Path" in (
        result.output
    )
