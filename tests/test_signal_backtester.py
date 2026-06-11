"""Tests for the research-only archived signal backtesting skeleton."""

import csv
import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.backtesting.price_history import (
    forward_return,
    load_price_history,
    max_drawdown,
)
from broker_agents.cli import app

ROOT = Path(__file__).resolve().parents[1]
PRICE_FIXTURES = ROOT / "tests" / "fixtures" / "price_history"


def _write_test_ledger(path: Path) -> None:
    """Create a small ledger containing one complete and one missing ticker."""
    fieldnames = [
        "archive_record_id",
        "ticker",
        "run_id",
        "generated_at",
        "status",
        "readiness_label",
        "source_verification_status",
        "promotion_blocking_categories",
        "total_work_orders",
        "buffett_interest_level",
        "munger_interest_level",
        "fisher_interest_level",
        "lynch_interest_level",
        "bogle_interest_level",
    ]
    rows = [
        {
            "archive_record_id": "COST-test-run",
            "ticker": "COST",
            "run_id": "test-run",
            "generated_at": "2026-06-11T12:00:00+00:00",
            "status": "completed",
            "readiness_label": "Investor Review Possible with Evidence Gaps",
            "source_verification_status": (
                "partially verified (placeholder-heavy)"
            ),
            "promotion_blocking_categories": (
                "scuttlebutt;management_incentives;index_overlap"
            ),
            "total_work_orders": "21",
            "buffett_interest_level": "Watchlist Interest",
            "munger_interest_level": "Conditional Interest",
            "fisher_interest_level": "Needs More Evidence",
            "lynch_interest_level": "Watchlist Interest",
            "bogle_interest_level": "Low Interest",
        },
        {
            "archive_record_id": "MISSING-test-run",
            "ticker": "MISSING",
            "run_id": "missing-run",
            "generated_at": "2026-06-11T12:00:00+00:00",
            "status": "completed",
            "readiness_label": "Needs Evidence",
            "source_verification_status": "weak",
            "promotion_blocking_categories": "scuttlebutt",
            "total_work_orders": "4",
            "buffett_interest_level": "Needs More Evidence",
            "munger_interest_level": "Needs More Evidence",
            "fisher_interest_level": "Needs More Evidence",
            "lynch_interest_level": "Needs More Evidence",
            "bogle_interest_level": "Needs More Evidence",
        },
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def test_backtest_signals_creates_research_outputs(tmp_path: Path) -> None:
    ledger_path = tmp_path / "signal_ledger.csv"
    outputs_root = tmp_path / "outputs"
    _write_test_ledger(ledger_path)

    result = CliRunner().invoke(
        app,
        [
            "backtest-signals",
            "--ledger",
            str(ledger_path),
            "--price-fixtures",
            str(PRICE_FIXTURES),
            "--outputs-root",
            str(outputs_root),
            "--lookback-years",
            "5",
        ],
    )

    assert result.exit_code == 0, result.output
    for field in (
        "Archived Signal Backtest",
        "Backtest Run ID",
        "Backtest Folder",
        "Backtest Summary",
        "Backtest Results",
        "Backtest Manifest",
        "Evaluated Records",
        "Skipped Records",
        "completed",
    ):
        assert field in result.output

    latest_path = outputs_root / "backtests" / "latest_backtest_manifest.json"
    assert latest_path.exists()
    manifest = json.loads(latest_path.read_text(encoding="utf-8"))
    backtest_folder = outputs_root / "backtests" / manifest["backtest_run_id"]
    summary_path = backtest_folder / "backtest_summary.md"
    results_path = backtest_folder / "backtest_results.csv"
    manifest_path = backtest_folder / "backtest_manifest.json"
    assert summary_path.exists()
    assert results_path.exists()
    assert manifest_path.exists()
    assert manifest["ledger_path"] == str(ledger_path)
    assert manifest["lookback_years"] == 5
    assert manifest["evaluated_records"] == 1
    assert manifest["skipped_records"] == 1
    assert manifest["status"] == "completed"
    assert manifest["benchmark"] == "SPY synthetic fixture"

    with results_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 2
    required_columns = {
        "ticker",
        "run_id",
        "readiness_label",
        "source_verification_status",
        "forward_return_3m",
        "forward_return_6m",
        "forward_return_12m",
        "relative_return_12m",
        "data_status",
    }
    assert required_columns.issubset(rows[0])
    cost = next(row for row in rows if row["ticker"] == "COST")
    missing = next(row for row in rows if row["ticker"] == "MISSING")
    assert cost["forward_return_3m"]
    assert cost["forward_return_6m"]
    assert cost["forward_return_12m"]
    assert cost["relative_return_12m"]
    assert cost["max_drawdown_12m"]
    assert cost["data_status"] == "complete_synthetic_fixture"
    assert missing["data_status"] == "missing_price_data"
    assert missing["forward_return_12m"] == ""

    summary = summary_path.read_text(encoding="utf-8")
    for text in (
        "Lookback Years: 5",
        "Evaluated Records: 1",
        "Forward Windows",
        "readiness_label",
        "source_verification_status",
        "Safety Note",
        "synthetic fixtures",
    ):
        assert text in summary
    summary_lower = summary.lower()
    for unsafe_phrase in (
        "buy recommendation",
        "sell recommendation",
        "top ranked",
        "best stock",
    ):
        assert unsafe_phrase not in summary_lower
    assert "not a recommendation" in summary_lower
    assert "or trade signal" in summary_lower


def test_price_fixture_calculations_are_deterministic() -> None:
    points = load_price_history(PRICE_FIXTURES / "cost.csv")
    start = points[0].date

    assert forward_return(points, start, 3) == (945 - 920) / 920
    assert forward_return(points, start, 6) == (970 - 920) / 920
    assert forward_return(points, start, 12) == (1025 - 920) / 920
    assert max_drawdown(points, start, 12) == (900 - 920) / 920


def test_backtesting_is_documented_and_demo_runner_remains() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Backtesting Framework Skeleton" in readme
    assert (
        "python -m broker_agents.cli backtest-signals --ledger "
        "data/outputs/signal_archive/signal_ledger.csv"
    ) in readme
    assert "Default lookback is 5 years" in readme

    demo_script = (ROOT / "scripts" / "run_first_demo.ps1").read_text(
        encoding="utf-8"
    )
    assert "python -m ruff check ." in demo_script
    assert "python -m pytest --basetemp=.pytest_tmp_demo" in demo_script
    assert "python -m broker_agents.cli deal-intakes" in demo_script
    assert "python -m broker_agents.cli run-deals" in demo_script
