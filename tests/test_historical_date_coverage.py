"""Tests for offline historical readiness date coverage."""

from pathlib import Path

import pytest

from broker_agents.deals.historical_date_coverage import (
    build_historical_date_coverage_report,
    resolve_historical_date_preset,
    validate_historical_date_coverage,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
FINANCIALS = FIXTURES / "historical_financials"
HISTORICAL_PRICES = FIXTURES / "historical_price_history"
TICKERS = ["MSFT", "AAPL", "NVDA", "COST"]


def test_historical_date_presets_resolve() -> None:
    assert resolve_historical_date_preset("annual_3") == [
        "2021-06-30",
        "2022-06-30",
        "2023-06-30",
    ]
    assert resolve_historical_date_preset("semiannual_6") == [
        "2021-06-30",
        "2021-12-31",
        "2022-06-30",
        "2022-12-31",
        "2023-06-30",
        "2023-12-31",
    ]
    assert len(resolve_historical_date_preset("quarterly_9")) == 9


def test_unknown_historical_date_preset_is_rejected() -> None:
    with pytest.raises(ValueError, match="Unknown historical date preset"):
        resolve_historical_date_preset("monthly_12")


def test_semiannual_coverage_skips_unsupported_date_and_writes_reports(
    tmp_path: Path,
) -> None:
    requested = resolve_historical_date_preset("semiannual_6")
    report = validate_historical_date_coverage(
        requested_dates=requested,
        tickers=TICKERS,
        price_root=HISTORICAL_PRICES,
        financials_root=FINANCIALS,
        date_preset="semiannual_6",
    )

    assert report.validation_status == "valid_with_warnings"
    assert report.usable_dates == [
        "2021-06-30",
        "2021-12-31",
        "2022-06-30",
        "2022-12-31",
        "2023-06-30",
    ]
    assert report.skipped_dates == ["2023-12-31"]
    skipped = report.date_records[-1]
    assert skipped.usable is False
    assert any("12M outcome anchor" in reason for reason in skipped.reasons)

    json_path = tmp_path / "coverage.json"
    markdown_path = tmp_path / "coverage.md"
    build_historical_date_coverage_report(
        report=report,
        json_path=json_path,
        markdown_path=markdown_path,
    )
    assert json_path.is_file()
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "Date Preset: semiannual_6" in markdown
    assert "Skipped Dates: 2023-12-31" in markdown
    assert "unsupported dates are not fabricated" in markdown


def test_quarterly_coverage_reports_unsupported_dates() -> None:
    requested = resolve_historical_date_preset("quarterly_9")
    report = validate_historical_date_coverage(
        requested_dates=requested,
        tickers=TICKERS,
        price_root=HISTORICAL_PRICES,
        financials_root=FINANCIALS,
        date_preset="quarterly_9",
    )

    assert report.validation_status == "valid_with_warnings"
    assert report.usable_dates
    assert report.skipped_dates
    assert set(report.usable_dates + report.skipped_dates) == set(requested)
