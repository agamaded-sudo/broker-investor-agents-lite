"""Integration tests for multi-date historical readiness trials."""

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
FINANCIALS = FIXTURES / "historical_financials"
HISTORICAL_PRICES = FIXTURES / "historical_price_history"
PORTFOLIO = EXAMPLES / "portfolio_context.yaml"


def _run_multidate(
    tmp_path: Path,
    *,
    tickers: str,
    as_of_dates: str | None = None,
    date_preset: str | None = None,
    full_pipeline: bool,
):
    outputs_root = tmp_path / "outputs"
    trial_ledger = tmp_path / "trial_ledgers" / "readiness.csv"
    args = [
        "run-historical-readiness-multidate",
        "--tickers",
        tickers,
        "--examples-root",
        str(EXAMPLES),
        "--outputs-root",
        str(outputs_root),
        "--fixtures-root",
        str(FIXTURES),
        "--portfolio-context",
        str(PORTFOLIO),
        "--financials-provider",
        "historical_csv",
        "--financials-root",
        str(FINANCIALS),
        "--trial-ledger",
        str(trial_ledger),
        "--price-fixtures",
        str(HISTORICAL_PRICES),
    ]
    if as_of_dates:
        args.extend(["--as-of-dates", as_of_dates])
    if date_preset:
        args.extend(["--date-preset", date_preset])
    if full_pipeline:
        args.extend(
            [
                "--export-trial-ledger",
                "--validate-trial-ledger",
                "--run-readiness-backtest",
            ]
        )
    return CliRunner().invoke(app, args), outputs_root, trial_ledger


def _latest_manifest(outputs_root: Path) -> dict:
    path = (
        outputs_root
        / "historical_readiness_multidate_runs"
        / "latest_historical_readiness_multidate_manifest.json"
    )
    return json.loads(path.read_text(encoding="utf-8"))


def test_full_multidate_trial_builds_twelve_event_sample(
    tmp_path: Path,
) -> None:
    result, outputs_root, trial_ledger = _run_multidate(
        tmp_path,
        tickers="MSFT,AAPL,NVDA,COST",
        as_of_dates="2021-06-30,2022-06-30,2023-06-30",
        full_pipeline=True,
    )

    assert result.exit_code == 0, result.output
    for text in (
        "Historical Readiness Multi-Date Trial",
        "Expected Runs",
        "12",
        "Completed Runs",
        "Failed Runs",
        "Sample Size After Dedupe",
        "multidate_run_id=",
        "total_expected_runs=12",
        "total_completed_runs=12",
        "total_failed_runs=0",
        "trial_ledger_exported=true",
        "readiness_backtest_run=true",
        "sample_size_after_dedupe=12",
        "status=completed",
    ):
        assert text in result.output

    manifest = _latest_manifest(outputs_root)
    assert manifest["tickers_requested"] == ["MSFT", "AAPL", "NVDA", "COST"]
    assert manifest["as_of_dates_requested"] == [
        "2021-06-30",
        "2022-06-30",
        "2023-06-30",
    ]
    assert manifest["total_expected_runs"] == 12
    assert manifest["total_completed_runs"] == 12
    assert manifest["total_failed_runs"] == 0
    assert manifest["completed_dates"] == manifest["as_of_dates_requested"]
    assert manifest["failed_dates"] == []
    assert len(manifest["date_batch_records"]) == 3
    assert manifest["trial_ledger_exported"] is True
    assert manifest["trial_ledger_validation_status"] == "valid"
    assert manifest["trial_ledger_validation_invalid_rows"] == 0
    assert manifest["readiness_backtest_run"] is True
    assert manifest["sample_size_after_dedupe"] == 12
    assert manifest["decision_status"] in {
        "needs_more_samples",
        "ready_for_broader_trial",
    }
    assert manifest["statistical_validity"] in {
        "limited_sample",
        "diagnostic_only",
    }
    assert "not a recommendation trial" in manifest["safety_notice"]

    for record in manifest["date_batch_records"]:
        assert record["status"] == "completed"
        assert record["completed_tickers"] == [
            "MSFT",
            "AAPL",
            "NVDA",
            "COST",
        ]
        assert record["failed_tickers"] == []
        assert record["total_completed"] == 4
        assert record["total_failed"] == 0
        assert Path(record["batch_manifest"]).is_file()
        assert Path(record["batch_summary"]).is_file()

    folder = (
        outputs_root
        / "historical_readiness_multidate_runs"
        / manifest["multidate_run_id"]
    )
    summary_path = folder / "historical_readiness_multidate_summary.md"
    results_path = folder / "historical_readiness_multidate_results.csv"
    assert (
        folder / "historical_readiness_multidate_manifest.json"
    ).is_file()
    assert summary_path.is_file()
    assert results_path.is_file()
    summary = summary_path.read_text(encoding="utf-8")
    assert "Total Completed Runs: 12" in summary
    assert "Sample Size After Dedupe: 12" in summary
    assert "Missing metadata and readiness-only sections remain visible" in summary
    assert "not a recommendation trial" in summary
    with results_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["as_of_date"] for row in rows] == [
        "2021-06-30",
        "2022-06-30",
        "2023-06-30",
    ]
    assert trial_ledger.is_file()
    assert Path(manifest["readiness_backtest_manifest"]).is_file()
    assert Path(manifest["readiness_backtest_decision_report"]).is_file()


def test_failed_date_does_not_stop_other_dates(tmp_path: Path) -> None:
    result, outputs_root, _ = _run_multidate(
        tmp_path,
        tickers="MSFT",
        as_of_dates="2023-06-30,2023/06/30",
        full_pipeline=False,
    )

    assert result.exit_code == 0, result.output
    manifest = _latest_manifest(outputs_root)
    assert manifest["total_expected_runs"] == 2
    assert manifest["total_completed_runs"] == 1
    assert manifest["total_failed_runs"] == 1
    assert manifest["completed_dates"] == ["2023-06-30"]
    assert manifest["failed_dates"] == ["2023/06/30"]
    records = {
        record["as_of_date"]: record
        for record in manifest["date_batch_records"]
    }
    assert records["2023-06-30"]["status"] == "completed"
    assert records["2023/06/30"]["status"] == "failed"
    assert records["2023/06/30"]["error"]


def test_failed_ticker_is_isolated_inside_each_date(tmp_path: Path) -> None:
    result, outputs_root, _ = _run_multidate(
        tmp_path,
        tickers="MSFT,NOTREAL",
        as_of_dates="2022-06-30,2023-06-30",
        full_pipeline=False,
    )

    assert result.exit_code == 0, result.output
    manifest = _latest_manifest(outputs_root)
    assert manifest["total_expected_runs"] == 4
    assert manifest["total_completed_runs"] == 2
    assert manifest["total_failed_runs"] == 2
    assert manifest["completed_dates"] == ["2022-06-30", "2023-06-30"]
    assert manifest["failed_dates"] == []
    for record in manifest["date_batch_records"]:
        assert record["status"] == "completed"
        assert record["completed_tickers"] == ["MSFT"]
        assert record["failed_tickers"] == ["NOTREAL"]
        assert record["total_completed"] == 1
        assert record["total_failed"] == 1


def test_semiannual_preset_expands_sample_and_records_coverage(
    tmp_path: Path,
) -> None:
    result, outputs_root, trial_ledger = _run_multidate(
        tmp_path,
        tickers="MSFT,AAPL,NVDA,COST",
        date_preset="semiannual_6",
        full_pipeline=True,
    )

    assert result.exit_code == 0, result.output
    manifest = _latest_manifest(outputs_root)
    assert manifest["date_preset"] == "semiannual_6"
    assert manifest["resolved_as_of_dates"] == [
        "2021-06-30",
        "2021-12-31",
        "2022-06-30",
        "2022-12-31",
        "2023-06-30",
        "2023-12-31",
    ]
    assert manifest["usable_dates"] == [
        "2021-06-30",
        "2021-12-31",
        "2022-06-30",
        "2022-12-31",
        "2023-06-30",
    ]
    assert manifest["skipped_dates"] == ["2023-12-31"]
    assert manifest["total_expected_runs"] == 20
    assert manifest["total_completed_runs"] == 20
    assert manifest["sample_size_after_dedupe"] == 20
    assert manifest["date_coverage_status"] == "valid_with_warnings"
    assert manifest["coverage_quality_counts"]
    assert manifest["coverage_severity_counts"]
    assert manifest["clean_record_count_estimate"] == 12
    assert manifest["warning_record_count_estimate"] == 8
    assert manifest["unsupported_date_count"] == 1
    assert Path(manifest["date_coverage_report_path"]).is_file()
    assert Path(manifest["date_coverage_report_json_path"]).is_file()
    assert trial_ledger.is_file()
    assert "date_preset=semiannual_6" in result.output
    assert "skipped_dates=2023-12-31" in result.output

    folder = Path(manifest["date_coverage_report_path"]).parent
    summary = (
        folder / "historical_readiness_multidate_summary.md"
    ).read_text(encoding="utf-8")
    assert "Date Preset: semiannual_6" in summary
    assert "Usable Dates:" in summary
    assert "Skipped Dates: 2023-12-31" in summary
    assert "Metadata Enrichment Status:" in summary
    assert "Coverage Quality Summary" in summary
    assert "Clean Record Estimate: 12" in summary
    assert "Warning Record Estimate: 8" in summary
    assert "Unsupported Dates Skipped: 1" in summary

    with (
        folder / "historical_readiness_multidate_results.csv"
    ).open(encoding="utf-8", newline="") as handle:
        result_rows = list(csv.DictReader(handle))
    for field in (
        "date_coverage_status",
        "coverage_quality_label",
        "coverage_quality_severity",
        "has_delayed_price_anchor",
        "has_limited_financials",
        "warning_count",
    ):
        assert field in result_rows[0]

    with trial_ledger.open(encoding="utf-8", newline="") as handle:
        trial_rows = list(csv.DictReader(handle))
    assert len(trial_rows) == 20
    assert all(row["coverage_quality_label"] for row in trial_rows)
    assert all(row["coverage_quality_severity"] for row in trial_rows)
    assert all(row["coverage_guardrail_status"] for row in trial_rows)
    assert not any(
        row["coverage_guardrail_status"] == "unsupported_excluded"
        for row in trial_rows
    )
    clean_rows = [
        row
        for row in trial_rows
        if row["coverage_guardrail_status"] == "clean"
    ]
    assert len(clean_rows) == 12
    assert all(row["has_delayed_price_anchor"] == "False" for row in clean_rows)
    assert all(row["has_limited_financials"] == "False" for row in clean_rows)

    backtest_manifest = json.loads(
        Path(manifest["readiness_backtest_manifest"]).read_text(
            encoding="utf-8"
        )
    )
    metrics = json.loads(
        Path(backtest_manifest["metrics_summary_path"]).read_text(
            encoding="utf-8"
        )
    )
    for field in (
        "coverage_quality_label",
        "coverage_quality_severity",
        "coverage_guardrail_status",
    ):
        assert field in metrics["grouped_metrics"]
    decision = Path(
        backtest_manifest["readiness_trial_decision_report_path"]
    ).read_text(encoding="utf-8")
    diagnostic = Path(
        backtest_manifest["readiness_trial_diagnostic_report_path"]
    ).read_text(encoding="utf-8")
    diagnostic_json = json.loads(
        Path(
            backtest_manifest[
                "readiness_trial_diagnostic_report_json_path"
            ]
        ).read_text(encoding="utf-8")
    )
    assert "Coverage Quality" in decision
    assert "Coverage Quality Guardrails" in diagnostic
    assert "coverage_quality_diagnostics" in diagnostic_json
    assert diagnostic_json["coverage_quality_diagnostics"][
        "unsupported_dates_excluded"
    ] == 1
    assert "Coverage Quality" in result.output


def test_explicit_dates_take_precedence_over_date_preset(
    tmp_path: Path,
) -> None:
    result, outputs_root, _ = _run_multidate(
        tmp_path,
        tickers="MSFT",
        as_of_dates="2022-06-30",
        date_preset="semiannual_6",
        full_pipeline=False,
    )

    assert result.exit_code == 0, result.output
    manifest = _latest_manifest(outputs_root)
    assert manifest["date_preset"] is None
    assert manifest["resolved_as_of_dates"] == ["2022-06-30"]
    assert manifest["total_expected_runs"] == 1


def test_unknown_date_preset_has_clear_cli_error(tmp_path: Path) -> None:
    result, _, _ = _run_multidate(
        tmp_path,
        tickers="MSFT",
        date_preset="monthly_12",
        full_pipeline=False,
    )

    assert result.exit_code != 0
    assert "Unknown" in result.output
    assert "historical date preset" in result.output
    assert "annual_3" in result.output


def test_task88_documentation_and_demo_runner_remain() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for text in (
        "multi-date historical readiness trial",
        "run-historical-readiness-multidate",
        "2021-06-30,2022-06-30,2023-06-30",
        "approximately 12 readiness events",
        "--export-trial-ledger",
        "--validate-trial-ledger",
        "--run-readiness-backtest",
        "dedupe remains important",
        "readiness-only sections",
    ):
        assert text in readme

    demo = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo
    assert "python -m broker_agents.cli" in demo
