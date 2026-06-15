"""Tests for the coverage-validated expanded ticker readiness trial."""

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from typer.testing import CliRunner
import yaml

from broker_agents.backoffice.data_validator import validate_backoffice_pack
from broker_agents.cli import app
from broker_agents.deals.expanded_ticker_readiness_trial import (
    load_eligible_ticker_universe,
    run_expanded_ticker_readiness_trial,
)
from broker_agents.deals.historical_readiness_multidate import (
    HistoricalReadinessMultidateResult,
)

TICKERS = [
    "MSFT",
    "AAPL",
    "NVDA",
    "COST",
    "GOOGL",
    "AMZN",
    "META",
    "AVGO",
    "ORCL",
    "CRM",
    "ADBE",
    "NFLX",
]
NEW_TICKERS = ["GOOGL", "AMZN", "META", "AVGO", "ORCL", "CRM", "ADBE", "NFLX"]


def _eligible(path: Path) -> Path:
    path.write_text(
        yaml.safe_dump(
            {
                "validation_run_id": "source-run",
                "tickers": TICKERS,
                "eligible_tickers": [
                    {"ticker": ticker, "status": "eligible_for_expanded_trial"}
                    for ticker in TICKERS
                ],
            }
        ),
        encoding="utf-8",
    )
    return path


def _fake_multidate(tmp_path: Path) -> HistoricalReadinessMultidateResult:
    folder = tmp_path / "outputs" / "historical_readiness_multidate_runs" / "multi"
    backtest = tmp_path / "outputs" / "backtests" / "backtest"
    folder.mkdir(parents=True)
    backtest.mkdir(parents=True)
    metrics = {
        "median_forward_return_12m": 0.2,
        "median_relative_return_12m": 0.1,
        "hit_rate_vs_benchmark_12m": 0.7,
        "worst_max_drawdown_12m": -0.3,
    }
    metrics_path = backtest / "backtest_metrics_summary.json"
    metrics_path.write_text(json.dumps(metrics), encoding="utf-8")
    backtest_manifest = {
        "backtest_run_id": "backtest",
        "metrics_summary_path": str(metrics_path),
        "clean_record_count": 36,
        "warning_record_count": 24,
        "warning_heavy_record_count": 0,
        "diagnostic_status": "promising_but_unproven",
        "decision_status": "needs_more_samples",
        "statistical_validity": "limited_sample",
        "walk_forward_stability_judgment": "mixed",
    }
    backtest_manifest_path = backtest / "backtest_manifest.json"
    backtest_manifest_path.write_text(
        json.dumps(backtest_manifest), encoding="utf-8"
    )
    manifest_path = folder / "historical_readiness_multidate_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "readiness_backtest_run_id": "backtest",
                "readiness_backtest_manifest": str(backtest_manifest_path),
                "trial_ledger_path": str(tmp_path / "trial.csv"),
                "pipeline_warnings": ["Unsupported date excluded."],
            }
        ),
        encoding="utf-8",
    )
    summary = folder / "summary.md"
    results = folder / "results.csv"
    latest = folder.parent / "latest.json"
    summary.write_text("summary", encoding="utf-8")
    results.write_text("date\n", encoding="utf-8")
    latest.write_text("{}", encoding="utf-8")
    return HistoricalReadinessMultidateResult(
        multidate_run_id="multi",
        multidate_folder=folder,
        manifest_path=manifest_path,
        summary_path=summary,
        results_path=results,
        latest_manifest_path=latest,
        total_expected_runs=60,
        total_completed_runs=60,
        total_failed_runs=0,
        trial_ledger_exported=True,
        trial_ledger_validation_status="valid",
        readiness_backtest_run=True,
        sample_size_after_dedupe=60,
        decision_status="needs_more_samples",
        statistical_validity="limited_sample",
        date_preset="semiannual_6",
        resolved_as_of_dates=[
            "2021-06-30",
            "2021-12-31",
            "2022-06-30",
            "2022-12-31",
            "2023-06-30",
            "2023-12-31",
        ],
        usable_dates=[
            "2021-06-30",
            "2021-12-31",
            "2022-06-30",
            "2022-12-31",
            "2023-06-30",
        ],
        skipped_dates=["2023-12-31"],
        date_coverage_status="valid_with_warnings",
    )


def test_eligible_universe_loads_and_rejects_invalid_files(
    tmp_path: Path,
) -> None:
    path = _eligible(tmp_path / "eligible.yaml")
    tickers, payload = load_eligible_ticker_universe(path)
    assert tickers == TICKERS
    assert payload["validation_run_id"] == "source-run"

    with pytest.raises(FileNotFoundError, match="not found"):
        load_eligible_ticker_universe(tmp_path / "missing.yaml")
    empty = tmp_path / "empty.yaml"
    empty.write_text("tickers: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="does not contain any tickers"):
        load_eligible_ticker_universe(empty)


@pytest.mark.parametrize("ticker", NEW_TICKERS)
def test_expanded_manual_input_pack_is_schema_valid(ticker: str) -> None:
    root = Path(__file__).resolve().parents[1]
    path = root / "examples" / f"{ticker.lower()}_input.yaml"
    pack = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert validate_backoffice_pack(pack) == []


def test_expanded_trial_writes_summary_and_preserves_provenance(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    outputs = tmp_path / "outputs"
    eligible = _eligible(tmp_path / "eligible.yaml")
    fake = _fake_multidate(tmp_path)
    captured = {}

    def fake_runner(**kwargs):
        captured.update(kwargs)
        return fake

    monkeypatch.setattr(
        "broker_agents.deals.expanded_ticker_readiness_trial."
        "run_historical_readiness_multidate",
        fake_runner,
    )
    result = run_expanded_ticker_readiness_trial(
        eligible_universe=eligible,
        date_preset="semiannual_6",
        as_of_dates=None,
        examples_root=tmp_path,
        outputs_root=outputs,
        fixtures_root=tmp_path,
        portfolio_context=None,
        financials_provider="historical_csv",
        financials_root=tmp_path,
        price_fixtures_path=tmp_path,
        export_trial_ledger=True,
        validate_trial_ledger=True,
        run_readiness_backtest=True,
        walk_forward=True,
        generated_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )

    assert captured["tickers"] == TICKERS
    assert captured["walk_forward"] is True
    assert captured["walk_forward_frequency"] == "yearly"
    assert result.status == "expanded_trial_completed_with_warnings"
    assert result.backtest_run_id == "backtest"
    assert result.clean_record_count == 36
    assert result.warning_record_count == 24
    assert result.summary_path.is_file()
    assert result.summary_json_path.is_file()
    assert result.latest_manifest_path.is_file()
    summary = json.loads(result.summary_json_path.read_text(encoding="utf-8"))
    assert summary["expanded_trial"] is True
    assert summary["source_validation_run_id"] == "source-run"
    assert summary["eligible_tickers"] == TICKERS
    assert summary["expected_usable_records"] == 60
    assert summary["prior_trial_comparison"]["prior_sample_size"] == 20
    markdown = result.summary_path.read_text(encoding="utf-8")
    assert "Comparison to Prior 4-Ticker Trial" in markdown
    assert "Safety Notice" in markdown


def test_cli_command_runs_with_eligible_universe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    eligible = _eligible(tmp_path / "eligible.yaml")
    fake = _fake_multidate(tmp_path)

    def fake_trial(**kwargs):
        monkeypatch.setattr(
            "broker_agents.deals.expanded_ticker_readiness_trial."
            "run_historical_readiness_multidate",
            lambda **inner: fake,
        )
        return run_expanded_ticker_readiness_trial(
            **kwargs,
            generated_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )

    monkeypatch.setattr(
        "broker_agents.cli.run_expanded_ticker_readiness_trial",
        fake_trial,
    )
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "run-expanded-ticker-readiness-trial",
            "--eligible-universe",
            str(eligible),
            "--outputs-root",
            str(tmp_path / "outputs"),
            "--examples-root",
            str(tmp_path),
            "--fixtures-root",
            str(tmp_path),
            "--financials-root",
            str(tmp_path),
            "--price-fixtures",
            str(tmp_path),
            "--export-trial-ledger",
            "--validate-trial-ledger",
            "--run-readiness-backtest",
            "--walk-forward",
        ],
    )
    assert result.exit_code == 0, result.output
    assert "Expanded Ticker Readiness Trial" in result.output
    assert "Backtest Run ID" in result.output
    assert "eligible_ticker_count=12" in result.output
