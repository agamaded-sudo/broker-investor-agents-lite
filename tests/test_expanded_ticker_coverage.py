"""Tests for expanded ticker fixture coverage admission."""

import csv
from datetime import datetime, timezone
import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from broker_agents.cli import app
from broker_agents.deals.expanded_ticker_coverage import (
    build_expanded_ticker_coverage_report,
    classify_ticker_eligibility,
    load_expanded_ticker_universe,
    render_expanded_ticker_coverage_report,
    validate_ticker_date_coverage,
    write_expanded_ticker_coverage_report,
)

ROOT = Path(__file__).resolve().parents[1]
UNIVERSE = ROOT / "examples" / "expanded_ticker_universe.yaml"
FINANCIALS = ROOT / "tests" / "fixtures" / "historical_financials"
PRICES = ROOT / "tests" / "fixtures" / "historical_price_history"


def _write_financials(
    root: Path,
    ticker: str,
    *,
    period_end: str = "2020-12-31",
    filing_date: str = "2021-02-01",
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{ticker.lower()}_financials_as_of.csv"
    path.write_text(
        "ticker,fiscal_period_end_date,filing_date,accepted_date,"
        "statement_type,period_type,metric,value,"
        "source_url_or_accession_number\n"
        f"{ticker},{period_end},{filing_date},{filing_date}T12:00:00Z,"
        "income_statement,annual,revenue,100,"
        f"fixture://historical-financials/{ticker}/test\n",
        encoding="utf-8",
    )


def _write_prices(
    root: Path,
    ticker: str,
    dates: list[str],
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    lines = ["date,close,adjusted_close"]
    lines.extend(
        f"{value},{100 + index},{100 + index}"
        for index, value in enumerate(dates)
    )
    (root / f"{ticker.lower()}.csv").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def _exact_dates() -> list[str]:
    return [
        "2021-06-30",
        "2021-09-30",
        "2021-12-30",
        "2022-06-30",
    ]


def test_expanded_universe_loads_core_and_added_tickers() -> None:
    universe = load_expanded_ticker_universe(UNIVERSE)
    tickers = [item["ticker"] for item in universe["tickers"]]
    assert tickers[:4] == ["MSFT", "AAPL", "NVDA", "COST"]
    assert {"GOOGL", "AMZN", "META", "AVGO", "ORCL", "CRM", "ADBE", "NFLX"} <= set(
        tickers
    )
    assert all(item["universe_group"] for item in universe["tickers"])


def test_real_fixtures_classify_core_and_added_june_rows_clean() -> None:
    for ticker in ("MSFT", "AAPL", "NVDA", "COST", "GOOGL", "AMZN"):
        row = validate_ticker_date_coverage(
            ticker=ticker,
            as_of_date="2022-06-30",
            financials_root=FINANCIALS,
            price_root=PRICES,
        )
        assert row["eligibility"] == "eligible_clean"
        assert row["coverage_quality"] == "clean"
        assert row["financials_status"] == "available_point_in_time"


def test_validator_detects_missing_and_future_only_financials(
    tmp_path: Path,
) -> None:
    financials = tmp_path / "financials"
    prices = tmp_path / "prices"
    _write_prices(prices, "SPY", _exact_dates())
    _write_prices(prices, "TEST", _exact_dates())

    missing = validate_ticker_date_coverage(
        ticker="TEST",
        as_of_date="2021-06-30",
        financials_root=financials,
        price_root=prices,
    )
    assert missing["financials_status"] == "missing_financials"
    assert missing["eligibility"] == "not_eligible"

    _write_financials(
        financials,
        "TEST",
        period_end="2021-03-31",
        filing_date="2021-08-01",
    )
    future = validate_ticker_date_coverage(
        ticker="TEST",
        as_of_date="2021-06-30",
        financials_root=financials,
        price_root=prices,
    )
    assert future["financials_status"] == "future_only_financials"
    assert future["has_limited_financials"] is True


def test_validator_detects_missing_price_and_outcomes(tmp_path: Path) -> None:
    financials = tmp_path / "financials"
    prices = tmp_path / "prices"
    _write_financials(financials, "TEST")
    _write_prices(prices, "SPY", ["2021-06-30"])

    missing_price = validate_ticker_date_coverage(
        ticker="TEST",
        as_of_date="2021-06-30",
        financials_root=financials,
        price_root=prices,
    )
    assert missing_price["price_anchor_status"] == "missing"
    assert missing_price["eligibility"] == "not_eligible"

    _write_prices(prices, "TEST", ["2021-06-30", "2021-09-30"])
    missing_outcome = validate_ticker_date_coverage(
        ticker="TEST",
        as_of_date="2021-06-30",
        financials_root=financials,
        price_root=prices,
    )
    assert missing_outcome["outcome_12m_available"] is False
    assert missing_outcome["benchmark_12m_available"] is False
    assert "missing_12m_outcome" in missing_outcome["limitations"]
    assert "missing_benchmark_12m_outcome" in missing_outcome["limitations"]


def test_ticker_date_clean_warning_and_not_eligible_classification(
    tmp_path: Path,
) -> None:
    financials = tmp_path / "financials"
    prices = tmp_path / "prices"
    _write_financials(financials, "TEST")
    _write_prices(prices, "SPY", _exact_dates())
    _write_prices(prices, "TEST", _exact_dates())
    clean = validate_ticker_date_coverage(
        ticker="TEST",
        as_of_date="2021-06-30",
        financials_root=financials,
        price_root=prices,
    )
    assert clean["eligibility"] == "eligible_clean"

    _write_prices(
        prices,
        "TEST",
        ["2021-07-01", "2021-10-01", "2021-12-31", "2022-07-01"],
    )
    warning = validate_ticker_date_coverage(
        ticker="TEST",
        as_of_date="2021-06-30",
        financials_root=financials,
        price_root=prices,
    )
    assert warning["eligibility"] == "eligible_with_warnings"
    assert warning["has_delayed_price_anchor"] is True

    (financials / "test_financials_as_of.csv").unlink()
    excluded = validate_ticker_date_coverage(
        ticker="TEST",
        as_of_date="2021-06-30",
        financials_root=financials,
        price_root=prices,
    )
    assert excluded["eligibility"] == "not_eligible"


def test_ticker_level_eligibility_rules() -> None:
    clean = {"eligibility": "eligible_clean", "main_limitation": "none"}
    warning = {
        "eligibility": "eligible_with_warnings",
        "main_limitation": "delayed_price_anchor",
    }
    excluded = {
        "eligibility": "not_eligible",
        "main_limitation": "missing_financials",
    }
    assert classify_ticker_eligibility([clean, clean, warning, excluded])[
        "status"
    ] == "eligible_for_expanded_trial"
    assert classify_ticker_eligibility([clean, warning, warning, excluded])[
        "status"
    ] == "eligible_with_caution"
    assert classify_ticker_eligibility([clean, excluded, excluded, excluded])[
        "status"
    ] == "excluded_insufficient_coverage"


def test_report_writer_outputs_matrix_yaml_and_manifest(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    files = write_expanded_ticker_coverage_report(
        ticker_universe_path=UNIVERSE,
        requested_dates=["2021-06-30", "2022-06-30", "2023-06-30"],
        financials_root=FINANCIALS,
        price_root=PRICES,
        outputs_root=outputs,
        generated_at=datetime(2026, 6, 15, tzinfo=timezone.utc),
    )
    assert files.markdown_path.is_file()
    assert files.json_path.is_file()
    assert files.matrix_csv_path.is_file()
    assert files.eligible_universe_path.is_file()
    assert files.latest_manifest_path.is_file()
    payload = json.loads(files.json_path.read_text(encoding="utf-8"))
    assert payload["ticker_date_matrix"]
    assert len(payload["eligible_tickers"]) > 4
    assert payload["validation_status"] == "valid"
    assert {"MSFT", "AAPL", "NVDA", "COST"} <= set(
        payload["eligible_tickers"]
    )
    markdown = render_expanded_ticker_coverage_report(files.report)
    assert "Eligibility Summary" in markdown
    assert "Ticker-Date Coverage Matrix" in markdown
    eligible = yaml.safe_load(
        files.eligible_universe_path.read_text(encoding="utf-8")
    )
    assert len(eligible["tickers"]) > 4
    with files.matrix_csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows


def test_report_can_include_excluded_candidate(tmp_path: Path) -> None:
    universe = {
        "tickers": [
            {
                "ticker": "MISSING",
                "sector": "Test",
                "category": "test",
                "reason_for_inclusion": "coverage failure test",
                "universe_group": "test",
            }
        ]
    }
    report = build_expanded_ticker_coverage_report(
        validation_run_id="run",
        generated_at="2026-06-15T00:00:00+00:00",
        ticker_universe_path=tmp_path / "universe.yaml",
        universe=universe,
        requested_dates=["2021-06-30"],
        financials_root=tmp_path / "financials",
        price_root=tmp_path / "prices",
    )
    assert report.excluded_tickers == ["MISSING"]
    assert report.validation_status == "insufficient_coverage"


def test_cli_explicit_dates_and_date_preset(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    runner = CliRunner()
    common = [
        "--ticker-universe",
        str(UNIVERSE),
        "--fixtures-root",
        str(ROOT / "tests" / "fixtures"),
        "--financials-root",
        str(FINANCIALS),
        "--price-fixtures",
        str(PRICES),
        "--outputs-root",
        str(outputs),
    ]
    explicit = runner.invoke(
        app,
        [
            "validate-expanded-ticker-coverage",
            *common,
            "--as-of-dates",
            "2021-06-30,2022-06-30,2023-06-30",
        ],
    )
    assert explicit.exit_code == 0, explicit.output
    assert "Expanded Ticker Coverage Validation" in explicit.output
    assert "eligible_universe=" in explicit.output

    preset = runner.invoke(
        app,
        [
            "validate-expanded-ticker-coverage",
            *common,
            "--date-preset",
            "semiannual_6",
        ],
    )
    assert preset.exit_code == 0, preset.output
    assert "2021-12-31" in preset.output
