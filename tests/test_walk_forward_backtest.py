"""Tests for optional yearly walk-forward historical validation."""

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
TRIAL_LEDGER = (
    ROOT
    / "data"
    / "inputs"
    / "trial_ledgers"
    / "sample_historical_signal_ledger.csv"
)
HISTORICAL_PRICES = (
    ROOT / "tests" / "fixtures" / "historical_price_history"
)


def test_yearly_walk_forward_outputs_are_generated(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    result = CliRunner().invoke(
        app,
        [
            "backtest-signals",
            "--ledger",
            str(TRIAL_LEDGER),
            "--price-provider",
            "csv",
            "--price-fixtures",
            str(HISTORICAL_PRICES),
            "--outputs-root",
            str(outputs_root),
            "--lookback-years",
            "5",
            "--dedupe-mode",
            "latest_per_ticker_per_day",
            "--walk-forward",
            "--walk-forward-frequency",
            "yearly",
        ],
    )

    assert result.exit_code == 0, result.output
    for text in (
        "Walk-Forward",
        "enabled",
        "Frequency",
        "yearly",
        "Periods Evaluated",
        "Walk-Forward Summary",
        "Walk-Forward Results",
    ):
        assert text in result.output

    manifest = json.loads(
        (
            outputs_root
            / "backtests"
            / "latest_backtest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["walk_forward_enabled"] is True
    assert manifest["walk_forward_frequency"] == "yearly"
    assert manifest["walk_forward_periods_evaluated"] == 3
    for field in (
        "walk_forward_summary_path",
        "walk_forward_results_path",
        "walk_forward_metrics_path",
    ):
        assert manifest[field]
        assert Path(manifest[field]).exists()

    with Path(manifest["walk_forward_results_path"]).open(
        encoding="utf-8",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))
    assert [row["period"] for row in rows] == ["2021", "2022", "2023"]
    required_fields = {
        "period",
        "sample_size",
        "median_relative_return_12m",
        "hit_rate_vs_benchmark_12m",
        "small_sample_warning",
        "concentration_warning",
    }
    assert required_fields.issubset(rows[0])
    for row in rows:
        assert row["sample_size"] == "4"
        assert row["median_forward_return_3m"]
        assert row["median_forward_return_6m"]
        assert row["median_forward_return_12m"]
        assert row["median_relative_return_12m"]
        assert row["hit_rate_vs_benchmark_12m"]
        assert row["small_sample_warning"] == "True"
        assert row["concentration_warning"] == "False"
        assert row["data_status"] == "complete"

    metrics = json.loads(
        Path(manifest["walk_forward_metrics_path"]).read_text(
            encoding="utf-8"
        )
    )
    assert metrics["enabled"] is True
    assert metrics["frequency"] == "yearly"
    assert metrics["total_periods"] == 3
    assert len(metrics["periods"]) == 3
    assert metrics["stability_observation"] in {
        "mixed_period_results",
        "consistently_positive_relative_12m",
        "consistently_negative_relative_12m",
    }

    summary = Path(manifest["walk_forward_summary_path"]).read_text(
        encoding="utf-8"
    )
    summary_lower = summary.lower()
    for text in (
        "Walk-Forward Historical Validation",
        "Run Context",
        "Period Results",
        "Stability Notes",
        "Limitations",
        "Safety Note",
        "not a recommendation",
        "research and pipeline validation only",
    ):
        assert text.lower() in summary_lower
    for unsafe_phrase in (
        "buy recommendation",
        "sell recommendation",
        "top ranked",
        "best stock",
    ):
        assert unsafe_phrase not in summary_lower


def test_walk_forward_is_optional_and_documented(tmp_path: Path) -> None:
    outputs_root = tmp_path / "outputs"
    result = CliRunner().invoke(
        app,
        [
            "backtest-signals",
            "--ledger",
            str(TRIAL_LEDGER),
            "--price-provider",
            "csv",
            "--price-fixtures",
            str(HISTORICAL_PRICES),
            "--outputs-root",
            str(outputs_root),
        ],
    )

    assert result.exit_code == 0, result.output
    manifest = json.loads(
        (
            outputs_root
            / "backtests"
            / "latest_backtest_manifest.json"
        ).read_text(encoding="utf-8")
    )
    assert manifest["walk_forward_enabled"] is False
    assert manifest["walk_forward_frequency"] is None
    assert manifest["walk_forward_summary_path"] is None
    assert manifest["walk_forward_results_path"] is None
    assert manifest["walk_forward_metrics_path"] is None
    assert manifest["walk_forward_periods_evaluated"] == 0
    run_folder = (
        outputs_root / "backtests" / manifest["backtest_run_id"]
    )
    assert not (run_folder / "walk_forward_summary.md").exists()
    assert not (run_folder / "walk_forward_results.csv").exists()
    assert not (run_folder / "walk_forward_metrics.json").exists()

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Walk-Forward Historical Validation" in readme
    assert "--walk-forward --walk-forward-frequency yearly" in readme
    assert "does not build or simulate a portfolio" in readme
