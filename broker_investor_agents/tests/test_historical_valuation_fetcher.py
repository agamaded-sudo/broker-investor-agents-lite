"""Tests for the offline historical valuation fetcher skeleton."""

from pathlib import Path

import pytest

from broker_agents.fetchers.historical_valuation_fetcher import (
    HistoricalValuationFetcher,
    HistoricalValuationSnapshot,
    load_historical_valuation_fixture,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def test_live_historical_valuation_fetch_is_not_implemented() -> None:
    with pytest.raises(
        NotImplementedError,
        match="Live historical valuation fetching is not implemented yet",
    ):
        HistoricalValuationFetcher().fetch_historical_valuation("MSFT")


@pytest.mark.parametrize("ticker", ["msft", "aapl", "nvda"])
def test_fixture_loads_and_maps_to_historical_snapshot(ticker: str) -> None:
    raw = load_historical_valuation_fixture(
        FIXTURES / f"historical_valuation_{ticker}.json"
    )
    snapshot = (
        HistoricalValuationFetcher().map_fixture_to_historical_valuation(raw)
    )

    assert isinstance(snapshot, HistoricalValuationSnapshot)
    assert snapshot.ticker == ticker.upper()
    assert snapshot.as_of_date == "2026-06-01"
    assert snapshot.pe_5y_median is not None
    assert snapshot.p_fcf_10y_median is not None
    assert snapshot.ev_ebitda_5y_median is not None
    assert snapshot.current_vs_10y_p_fcf_percentile is not None
    assert snapshot.valuation_history_confidence == "medium_market_fixture"
    assert snapshot.confidence == "medium"
