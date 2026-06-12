"""Tests for offline price provider adapters and the live stub."""

from pathlib import Path

from broker_agents.data_providers.csv_price_provider import CsvPriceProvider
from broker_agents.data_providers.fixture_price_provider import (
    FixturePriceProvider,
)
from broker_agents.data_providers.live_stub_price_provider import (
    LIVE_STUB_MESSAGE,
    LiveStubPriceProvider,
)

ROOT = Path(__file__).resolve().parents[1]
PRICE_FIXTURES = ROOT / "tests" / "fixtures" / "price_history"


def test_fixture_provider_loads_synthetic_history() -> None:
    provider = FixturePriceProvider(PRICE_FIXTURES)

    result = provider.get_price_history("COST")

    assert result.status == "available"
    assert result.provider_name == "fixture"
    assert result.data_type == "synthetic_fixture"
    assert len(result.rows) == 13
    assert result.rows[0].close == 920


def test_csv_provider_loads_local_history_and_handles_missing() -> None:
    provider = CsvPriceProvider(PRICE_FIXTURES)

    available = provider.get_price_history("MSFT")
    missing = provider.get_price_history("MISSING")

    assert available.status == "available"
    assert available.provider_name == "csv"
    assert available.data_type == "local_csv"
    assert available.rows
    assert missing.status == "missing_price_data"
    assert missing.rows == []
    assert "not found" in missing.warnings[0]


def test_live_stub_is_controlled_and_network_free() -> None:
    provider = LiveStubPriceProvider()

    result = provider.get_price_history("NVDA")

    assert result.status == "live_provider_not_configured"
    assert result.provider_name == "live_stub"
    assert result.data_type == "live_stub"
    assert result.rows == []
    assert result.warnings == [LIVE_STUB_MESSAGE]
    module_text = (
        ROOT
        / "src"
        / "broker_agents"
        / "data_providers"
        / "live_stub_price_provider.py"
    ).read_text(encoding="utf-8")
    for forbidden in ("requests", "httpx", "urllib", "socket", "api_key"):
        assert forbidden not in module_text.lower()
