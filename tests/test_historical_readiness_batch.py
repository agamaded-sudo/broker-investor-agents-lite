"""Integration tests for multi-ticker historical readiness batches."""

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


def _run_batch(
    tmp_path: Path,
    *,
    tickers: str,
    full_pipeline: bool,
):
    outputs_root = tmp_path / "outputs"
    trial_ledger = tmp_path / "trial_ledgers" / "readiness.csv"
    args = [
        "run-historical-readiness-batch",
        "--tickers",
        tickers,
        "--as-of-date",
        "2023-06-30",
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
    if full_pipeline:
        args.extend(
            [
                "--export-trial-ledger",
                "--validate-trial-ledger",
                "--run-readiness-backtest",
            ]
        )
    return CliRunner().invoke(app, args), outputs_root, trial_ledger


def test_four_ticker_historical_readiness_batch_and_trial_pipeline(
    tmp_path: Path,
) -> None:
    result, outputs_root, trial_ledger = _run_batch(
        tmp_path,
        tickers="MSFT,AAPL,NVDA,COST",
        full_pipeline=True,
    )

    assert result.exit_code == 0, result.output
    for text in (
        "Historical Readiness Batch",
        "Batch Run ID",
        "Completed",
        "4",
        "Failed",
        "Export Trial Ledger",
        "Validate Trial Ledger",
        "Run Readiness Backtest",
        "batch_run_id=",
        "total_completed=4",
        "total_failed=0",
        "trial_ledger_exported=true",
        "readiness_backtest_run=true",
        "status=completed",
    ):
        assert text in result.output

    latest = (
        outputs_root
        / "historical_readiness_batch_runs"
        / "latest_historical_readiness_batch_manifest.json"
    )
    manifest = json.loads(latest.read_text(encoding="utf-8"))
    assert manifest["tickers_requested"] == ["MSFT", "AAPL", "NVDA", "COST"]
    assert manifest["completed_tickers"] == ["MSFT", "AAPL", "NVDA", "COST"]
    assert manifest["failed_tickers"] == []
    assert manifest["total_requested"] == 4
    assert manifest["total_completed"] == 4
    assert manifest["total_failed"] == 0
    assert manifest["trial_ledger_exported"] is True
    assert manifest["trial_ledger_validation_status"] == "valid"
    assert manifest["trial_ledger_validation_invalid_rows"] == 0
    assert manifest["readiness_backtest_run"] is True
    assert manifest["sample_size_after_dedupe"] == 4
    assert manifest["decision_status"] == "not_decision_grade"
    assert manifest["statistical_validity"] == "insufficient_sample"
    assert "not a recommendation batch" in manifest["safety_notice"]
    assert len(manifest["run_records"]) == 4

    for record in manifest["run_records"]:
        assert record["status"] == "completed"
        assert Path(record["run_manifest"]).is_file()
        assert Path(record["historical_readiness_candidate_file"]).is_file()
        assert Path(
            record["historical_enriched_input_assembly_file"]
        ).is_file()
        assert record["historical_readiness_ledger_record_status"] == (
            "archived"
        )

    batch_folder = (
        outputs_root
        / "historical_readiness_batch_runs"
        / manifest["batch_run_id"]
    )
    manifest_path = (
        batch_folder / "historical_readiness_batch_manifest.json"
    )
    summary_path = batch_folder / "historical_readiness_batch_summary.md"
    results_path = batch_folder / "historical_readiness_batch_results.csv"
    assert manifest_path.is_file()
    assert summary_path.is_file()
    assert results_path.is_file()
    summary = summary_path.read_text(encoding="utf-8")
    assert "Historical Readiness Batch Summary" in summary
    assert "Sample Size After Dedupe: 4" in summary
    assert "not a recommendation batch" in summary
    with results_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["ticker"] for row in rows] == [
        "MSFT",
        "AAPL",
        "NVDA",
        "COST",
    ]
    assert trial_ledger.is_file()
    assert Path(manifest["readiness_backtest_manifest"]).is_file()
    assert Path(manifest["readiness_backtest_decision_report"]).is_file()


def test_failed_ticker_does_not_stop_historical_readiness_batch(
    tmp_path: Path,
) -> None:
    result, outputs_root, _ = _run_batch(
        tmp_path,
        tickers="MSFT,NOTREAL",
        full_pipeline=False,
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(
        (
            outputs_root
            / "historical_readiness_batch_runs"
            / "latest_historical_readiness_batch_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["completed_tickers"] == ["MSFT"]
    assert manifest["failed_tickers"] == ["NOTREAL"]
    assert manifest["total_completed"] == 1
    assert manifest["total_failed"] == 1
    records = {record["ticker"]: record for record in manifest["run_records"]}
    assert records["MSFT"]["status"] == "completed"
    assert records["NOTREAL"]["status"] == "failed"
    assert records["NOTREAL"]["error"]
    assert manifest["trial_ledger_exported"] is False
    assert manifest["readiness_backtest_run"] is False


def test_task87_documentation_and_demo_runner_remain() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for text in (
        "multi-ticker historical readiness batch",
        "run-historical-readiness-batch",
        "msft,aapl,nvda,cost",
        "--export-trial-ledger",
        "--validate-trial-ledger",
        "--run-readiness-backtest",
        "dedupe remains important",
    ):
        assert text in readme

    demo = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo
    assert "python -m broker_agents.cli" in demo
