"""Tests for the offline market data fetcher skeleton."""

from pathlib import Path

import pytest

from broker_agents.fetchers.market_data_fetcher import (
    MarketDataFetcher,
    MarketDataSnapshot,
    load_market_data_fixture,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def test_live_market_fetch_is_explicitly_not_implemented() -> None:
    with pytest.raises(
        NotImplementedError,
        match="Live market data fetching is not implemented yet",
    ):
        MarketDataFetcher().fetch_market_data("MSFT")


@pytest.mark.parametrize("ticker", ["msft", "aapl", "nvda"])
def test_market_fixture_loads_and_maps_to_snapshot(ticker: str) -> None:
    raw = load_market_data_fixture(FIXTURES / f"market_data_{ticker}.json")
    snapshot = MarketDataFetcher().map_fixture_to_market_data(raw)

    assert isinstance(snapshot, MarketDataSnapshot)
    assert snapshot.ticker == ticker.upper()
    assert snapshot.as_of_date == "2026-06-01"
    assert snapshot.current_price is not None
    assert snapshot.market_cap is not None
    assert snapshot.pe is not None
    assert snapshot.p_fcf is not None
    assert snapshot.fcf_yield is not None
    assert snapshot.dividend_yield is not None
    assert snapshot.confidence == "medium"


def test_market_snapshot_contains_optional_valuation_multiples() -> None:
    raw = load_market_data_fixture(FIXTURES / "market_data_msft.json")
    snapshot = MarketDataFetcher().map_fixture_to_market_data(raw)

    assert snapshot.enterprise_value == 3120000
    assert snapshot.forward_pe == 29.5
    assert snapshot.ev_ebitda == 23.8
    assert snapshot.currency == "USD"
