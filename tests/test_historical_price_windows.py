"""Tests for historical analysis and outcome price-window separation."""

import json
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.data_providers.csv_price_provider import CsvPriceProvider
from broker_agents.historical.price_windows import (
    build_analysis_price_window,
    build_outcome_price_window,
)
from broker_agents.historical.snapshot_contract import (
    build_historical_snapshot_contract,
)

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"
FIXTURES = ROOT / "tests" / "fixtures"
HISTORICAL_PRICES = FIXTURES / "historical_price_history"
PORTFOLIO_CONTEXT = EXAMPLES / "portfolio_context.yaml"


def test_price_window_policies_separate_analysis_and_outcomes() -> None:
    analysis = build_analysis_price_window("2023-06-30")
    outcome = build_outcome_price_window("2023-06-30", 12)

    assert analysis.window_type == "analysis"
    assert analysis.end_date.isoformat() == "2023-06-30"
    assert analysis.allowed_future_data is False
    assert analysis.enforcement_status == "analysis_window_enforced"
    assert outcome.window_type == "outcome"
    assert outcome.start_date.isoformat() == "2023-06-30"
    assert outcome.end_date.isoformat() == "2024-06-30"
    assert outcome.allowed_future_data is True
    assert outcome.enforcement_status == "outcome_evaluation_only"


def test_csv_analysis_window_excludes_future_rows_with_metadata() -> None:
    provider = CsvPriceProvider(HISTORICAL_PRICES)

    full_history = provider.get_price_history("COST")
    analysis_history = provider.get_price_history(
        "COST",
        end_date="2023-06-30",
        window_type="analysis",
    )

    assert full_history.status == "available"
    assert len(full_history.rows) == 10
    assert analysis_history.status == "analysis_window_enforced"
    assert analysis_history.window_type == "analysis"
    assert analysis_history.window_end_date == "2023-06-30"
    assert analysis_history.rows_before_filter == 10
    assert analysis_history.rows_after_filter == 7
    assert analysis_history.future_rows_excluded_count == 3
    assert max(point.date for point in analysis_history.rows).isoformat() == (
        "2023-06-30"
    )


def test_snapshot_contract_declares_csv_analysis_window_enforcement() -> None:
    contract = build_historical_snapshot_contract(
        "2023-06-30",
        price_provider="csv",
        input_mode="validation",
        price_data_root=HISTORICAL_PRICES,
    )
    prices = next(
        item
        for item in contract.provider_capabilities
        if item.section == "market_prices"
    )

    assert prices.supports_as_of_date is True
    assert prices.enforcement_level == "partial"
    assert "analysis_window_enforced" in prices.notes
    assert "prices after as_of_date are excluded" in prices.notes


def test_historical_run_manifest_and_summary_include_price_window(
    tmp_path: Path,
) -> None:
    outputs_root = tmp_path / "outputs"
    result = CliRunner().invoke(
        app,
        [
            "analyze-stock",
            "--ticker",
            "COST",
            "--examples-root",
            str(EXAMPLES),
            "--outputs-root",
            str(outputs_root),
            "--fixtures-root",
            str(FIXTURES),
            "--portfolio-context",
            str(PORTFOLIO_CONTEXT),
            "--as-of-date",
            "2023-06-30",
        ],
    )

    assert result.exit_code == 0, result.output
    manifest_path = (
        outputs_root / "COST" / "runs" / "latest_run_manifest.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    price_window = manifest["historical_price_window"]
    analysis = price_window["analysis_window"]
    assert analysis["window_type"] == "analysis"
    assert analysis["end_date"] == "2023-06-30"
    assert analysis["allowed_future_data"] is False
    assert manifest["market_price_window_enforcement"] == (
        "analysis_window_enforced"
    )
    assert "backtest evaluation" in price_window["outcome_window_note"]

    summary = (
        manifest_path.parent / manifest["run_id"] / "run_summary.md"
    ).read_text(encoding="utf-8")
    for text in (
        "Historical Price Window",
        "Future Prices Allowed in Analysis: No",
        "Outcome Prices Used for Backtest Only: Yes",
        "Analysis inputs must not use prices after the as_of_date.",
        "This historical price window enforcement is not a recommendation",
    ):
        assert text in summary


def test_historical_validation_commands_show_window_enforcement() -> None:
    snapshot = CliRunner().invoke(
        app,
        [
            "validate-historical-snapshot",
            "--as-of-date",
            "2023-06-30",
            "--price-provider",
            "csv",
            "--price-fixtures",
            str(HISTORICAL_PRICES),
        ],
    )
    price_window = CliRunner().invoke(
        app,
        [
            "validate-price-window",
            "--ticker",
            "COST",
            "--price-provider",
            "csv",
            "--price-fixtures",
            str(HISTORICAL_PRICES),
            "--as-of-date",
            "2023-06-30",
        ],
    )

    assert snapshot.exit_code == 0, snapshot.output
    assert "Analysis Price Window End Date: 2023-06-30" in snapshot.output
    assert "Market Price Window Enforcement: analysis_window_enforced" in (
        snapshot.output
    )
    assert "prices after as_of_date are excluded" in snapshot.output
    assert price_window.exit_code == 0, price_window.output
    for text in (
        "future_rows_excluded_count=3",
        "max_date_after_filter=2023-06-30",
        "status=analysis_window_enforced",
    ):
        assert text in price_window.output
