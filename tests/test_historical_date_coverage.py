"""Tests for offline historical readiness date coverage."""

from pathlib import Path

import pytest

from broker_agents.deals.historical_date_coverage import (
    build_historical_date_coverage_report,
    classify_coverage_quality,
    coverage_guardrail_status,
    resolve_historical_date_preset,
    validate_historical_date_coverage,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
FINANCIALS = FIXTURES / "historical_financials"
HISTORICAL_PRICES = FIXTURES / "historical_price_history"
TICKERS = ["MSFT", "AAPL", "NVDA", "COST"]


@pytest.mark.parametrize(
    (
        "delayed",
        "limited",
        "unsupported",
        "other_warning",
        "expected",
    ),
    [
        (False, False, False, False, ("clean", "none")),
        (False, False, False, True, ("usable_with_warnings", "low")),
        (True, False, False, False, ("delayed_price_anchor", "moderate")),
        (False, True, False, False, ("limited_financials", "moderate")),
        (
            True,
            True,
            False,
            False,
            ("delayed_anchor_and_limited_financials", "high"),
        ),
        (False, False, True, False, ("unsupported", "unsupported")),
    ],
)
def test_coverage_quality_classifier(
    delayed: bool,
    limited: bool,
    unsupported: bool,
    other_warning: bool,
    expected: tuple[str, str],
) -> None:
    assert classify_coverage_quality(
        has_delayed_price_anchor=delayed,
        has_limited_financials=limited,
        has_unsupported_outcome_anchor=unsupported,
        has_other_warnings=other_warning,
    ) == expected


def test_coverage_guardrail_status_is_conservative() -> None:
    assert coverage_guardrail_status("none") == "clean"
    assert (
        coverage_guardrail_status("moderate")
        == "research_usable_with_warnings"
    )
    assert coverage_guardrail_status("high") == "warning_heavy"
    assert coverage_guardrail_status("unsupported") == "unsupported_excluded"


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
    assert report.coverage_quality_counts
    assert report.coverage_severity_counts
    assert report.clean_record_count_estimate == 12
    assert report.warning_record_count_estimate == 8
    assert report.unsupported_date_count == 1
    records = {record.as_of_date: record for record in report.date_records}
    for value in ("2021-06-30", "2022-06-30", "2023-06-30"):
        assert records[value].clean_record_count_estimate == 4
        assert all(
            quality["coverage_guardrail_status"] == "clean"
            for quality in records[value].ticker_coverage_quality.values()
        )
    delayed = records["2021-12-31"]
    assert delayed.clean_record_count_estimate == 0
    assert delayed.delayed_anchor_record_count == 4
    assert delayed.limited_financials_record_count == 0
    financials = records["2023-06-30"].financials_coverage_by_ticker[
        "MSFT"
    ]
    assert financials["rows_available_as_of"] == 4
    assert financials["financials_rows_available_by_asof"] == 4
    assert financials["rows_excluded_after_asof"] == 2
    assert financials["clean_financials_available"] is True
    assert financials["limited_financials_reason"] is None
    assert financials["missing_filing_date_count"] == 1
    assert financials["missing_accepted_date_count"] == 1
    skipped = report.date_records[-1]
    assert skipped.usable is False
    assert skipped.coverage_quality_label == "unsupported"
    assert skipped.coverage_quality_severity == "unsupported"
    assert skipped.has_unsupported_outcome_anchor is True
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
    assert "Quality Summary" in markdown
    assert "Coverage Quality Counts" in markdown
    assert "Clean Record Count Estimate: 12" in markdown
    assert "Date-level warnings may coexist with clean ticker-date records" in (
        markdown
    )
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
