"""Tests for the offline SEC financials fetcher skeleton."""

from pathlib import Path

import pytest

from broker_agents.fetchers.sec_financials_fetcher import (
    SecFinancialFacts,
    SecFinancialsFetcher,
    load_sec_fixture,
    map_fixture_to_financials,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def test_resolve_supported_company_identities() -> None:
    fetcher = SecFinancialsFetcher()

    assert fetcher.resolve_company_identity("MSFT").cik == "0000789019"
    assert fetcher.resolve_company_identity("aapl").cik == "0000320193"
    assert fetcher.resolve_company_identity("NVDA").cik == "0001045810"


def test_live_fetch_is_explicitly_not_implemented() -> None:
    fetcher = SecFinancialsFetcher()

    with pytest.raises(
        NotImplementedError,
        match="Live SEC fetching is not implemented yet",
    ):
        fetcher.fetch_company_facts("MSFT")


@pytest.mark.parametrize("ticker", ["msft", "aapl", "nvda"])
def test_fixture_loads_and_maps_to_financial_facts(ticker: str) -> None:
    fixture = load_sec_fixture(FIXTURES / f"sec_company_facts_{ticker}.json")
    financials = map_fixture_to_financials(fixture)

    assert isinstance(financials, SecFinancialFacts)
    assert financials.ticker == ticker.upper()
    assert financials.revenue is not None
    assert financials.operating_cash_flow is not None
    assert financials.capital_expenditure is not None
    assert financials.free_cash_flow == (
        financials.operating_cash_flow - financials.capital_expenditure
    )
    assert financials.confidence == "high"


def test_source_log_uses_deterministic_official_source_id() -> None:
    fixture = load_sec_fixture(FIXTURES / "sec_company_facts_msft.json")
    financials = map_fixture_to_financials(fixture)
    source = SecFinancialsFetcher().build_source_log(financials)[0]

    assert source["source_id"] == "sec_company_facts_msft_FY2025"
    assert source["source_type"] == "company"
    assert source["confidence"] == "high"
