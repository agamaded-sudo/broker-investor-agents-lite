"""Tests for user-supplied historical financials CSV inputs."""

from dataclasses import replace
from datetime import date
from pathlib import Path

from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.historical.financials_as_of_contract import (
    build_financials_as_of_contract,
)
from broker_agents.historical.historical_financials import (
    REQUIRED_COLUMNS,
    filter_financials_as_of,
    load_historical_financials_csv,
    validate_historical_financials_csv,
)

ROOT = Path(__file__).resolve().parents[1]
FINANCIAL_FIXTURES = ROOT / "tests" / "fixtures" / "historical_financials"
PRICE_FIXTURES = ROOT / "tests" / "fixtures" / "historical_price_history"


def test_historical_financials_docs_and_four_fixtures_exist() -> None:
    readme = (
        ROOT / "data" / "inputs" / "historical_financials" / "README.md"
    ).read_text(encoding="utf-8")
    for ticker in ("msft", "aapl", "nvda", "cost"):
        assert (
            FINANCIAL_FIXTURES / f"{ticker}_financials_as_of.csv"
        ).is_file()
    for text in (
        "user-supplied point-in-time financial statement snapshots",
        "fiscal_period_end_date",
        "filing_date",
        "accepted_date",
        "statement_type",
        "period_type",
        "source_url_or_accession_number",
        "filing_date <= as_of_date",
        "not a recommendation, ranking",
        "not a recommendation",
        "trade signal",
    ):
        assert text.lower() in readme.lower()


def test_load_and_validate_historical_financials_fixture() -> None:
    path = FINANCIAL_FIXTURES / "cost_financials_as_of.csv"

    rows = load_historical_financials_csv(path)
    validation = validate_historical_financials_csv(path)

    assert len(rows) == 6
    assert rows[0].ticker == "COST"
    assert rows[0].metric == "revenue"
    assert rows[0].value == 166761.0
    assert validation.file_found is True
    assert validation.required_columns_present is True
    assert validation.missing_required_columns == []
    assert validation.rows_count == 6
    assert validation.rows_missing_availability_date_count == 0
    assert validation.rows_missing_source_traceability_count == 0
    assert validation.status == "valid"
    assert set(REQUIRED_COLUMNS).issubset(
        path.read_text(encoding="utf-8-sig").splitlines()[0].split(",")
    )


def test_filter_financials_as_of_excludes_future_rows() -> None:
    rows = load_historical_financials_csv(
        FINANCIAL_FIXTURES / "cost_financials_as_of.csv"
    )

    result = filter_financials_as_of(rows, "2023-06-30")

    assert result.as_of_date == "2023-06-30"
    assert result.rows_before_filter == 6
    assert result.rows_after_filter == 4
    assert result.future_rows_excluded_count == 2
    assert result.rows_missing_availability_date_count == 0
    assert result.max_filing_date_after_filter == "2023-05-01"
    assert result.max_accepted_date_after_filter == "2023-05-01"
    assert result.status == "as_of_filter_applied"
    assert all(
        row.fiscal_period_end_date <= date(2023, 6, 30)
        and (
        (row.filing_date and row.filing_date.isoformat() <= "2023-06-30")
        or (
            row.accepted_date
            and row.accepted_date.isoformat() <= "2023-06-30"
        )
        )
        for row in result.rows
    )


def test_filter_financials_as_of_excludes_missing_availability_dates() -> None:
    rows = load_historical_financials_csv(
        FINANCIAL_FIXTURES / "cost_financials_as_of.csv"
    )
    unsafe = replace(
        rows[0],
        filing_date=None,
        accepted_date=None,
    )

    result = filter_financials_as_of([unsafe, *rows[1:]], "2023-06-30")

    assert result.rows_after_filter == 3
    assert result.rows_missing_availability_date_count == 1
    assert any(
        "no filing or accepted date" in warning
        for warning in result.warnings
    )


def test_historical_csv_financials_contract_is_partial_and_medium() -> None:
    contract = build_financials_as_of_contract(
        "2023-06-30",
        provider_name="historical_csv",
        financials_root=FINANCIAL_FIXTURES,
        ticker="COST",
    )

    assert contract.provider_name == "historical_financials_csv"
    assert contract.supports_as_of_date is True
    assert contract.enforcement_level == "partial"
    assert contract.leakage_risk == "medium"
    assert contract.status == "supported_if_required_date_fields_present"
    assert contract.missing_date_fields == []
    assert "provenance remains user-managed" in contract.notes[0]


def test_validate_financials_csv_command_reports_all_tickers() -> None:
    result = CliRunner().invoke(
        app,
        [
            "validate-financials-csv",
            "--financials-root",
            str(FINANCIAL_FIXTURES),
            "--tickers",
            "MSFT,AAPL,NVDA,COST",
            "--as-of-date",
            "2023-06-30",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "Historical Financials CSV Validation" in result.output
    for ticker in ("MSFT", "AAPL", "NVDA", "COST"):
        assert f"ticker={ticker}" in result.output
    for text in (
        "file_found=true",
        "rows=6",
        "required_columns_present=true",
        "rows_before_filter=6",
        "rows_after_filter=4",
        "future_rows_excluded_count=2",
        "rows_missing_availability_date_count=0",
        "max_filing_date_after_filter=2023-05-01",
        "max_accepted_date_after_filter=2023-05-01",
        "status=as_of_filter_applied",
    ):
        assert text in result.output


def test_snapshot_validation_supports_historical_csv_and_default_mode() -> None:
    historical = CliRunner().invoke(
        app,
        [
            "validate-historical-snapshot",
            "--as-of-date",
            "2023-06-30",
            "--price-provider",
            "csv",
            "--price-fixtures",
            str(PRICE_FIXTURES),
            "--financials-provider",
            "historical_csv",
            "--financials-root",
            str(FINANCIAL_FIXTURES),
        ],
    )
    default = CliRunner().invoke(
        app,
        [
            "validate-historical-snapshot",
            "--as-of-date",
            "2023-06-30",
            "--price-provider",
            "csv",
            "--price-fixtures",
            str(PRICE_FIXTURES),
        ],
    )

    assert historical.exit_code == 0, historical.output
    for text in (
        "section=official_financials",
        "provider=historical_financials_csv",
        "supports_as_of_date=true",
        "enforcement_level=partial",
        "leakage_risk=medium",
        "Official Financials Status: supported_if_required_date_fields_present",
        "provenance remains user-managed",
    ):
        assert text in historical.output
    assert default.exit_code == 0, default.output
    assert "provider=sec_fixture" in default.output
    assert "supports_as_of_date=false" in default.output
    assert "Official Financials Status: readiness_only" in default.output


def test_historical_financials_module_is_network_free() -> None:
    source = (
        ROOT
        / "src"
        / "broker_agents"
        / "historical"
        / "historical_financials.py"
    ).read_text(encoding="utf-8").lower()
    for network_call in (
        "requests.get(",
        "requests.post(",
        "httpx.get(",
        "urlopen(",
    ):
        assert network_call not in source
