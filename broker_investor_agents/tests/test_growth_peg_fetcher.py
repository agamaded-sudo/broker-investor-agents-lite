"""Tests for the offline growth and PEG fetcher skeleton."""

from pathlib import Path

import pytest

from broker_agents.fetchers.growth_peg_fetcher import (
    GrowthPegFetcher,
    GrowthPegSnapshot,
    load_growth_peg_fixture,
)

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


def test_live_growth_peg_fetch_is_not_implemented() -> None:
    with pytest.raises(
        NotImplementedError,
        match="Live growth and PEG fetching is not implemented yet",
    ):
        GrowthPegFetcher().fetch_growth_peg("MSFT")


@pytest.mark.parametrize("ticker", ["msft", "aapl", "nvda"])
def test_fixture_loads_and_maps_to_growth_snapshot(ticker: str) -> None:
    raw = load_growth_peg_fixture(FIXTURES / f"growth_peg_{ticker}.json")
    snapshot = GrowthPegFetcher().map_fixture_to_growth_peg(raw)

    assert isinstance(snapshot, GrowthPegSnapshot)
    assert snapshot.ticker == ticker.upper()
    assert snapshot.as_of_date == "2026-06-01"
    assert snapshot.revenue_cagr_3y is not None
    assert snapshot.eps_cagr_5y is not None
    assert snapshot.fcf_cagr_3y is not None
    assert snapshot.forward_eps_growth is not None
    assert snapshot.peg_ratio is not None
    assert snapshot.growth_data_confidence == "medium_market_fixture"
    assert snapshot.confidence == "medium"
