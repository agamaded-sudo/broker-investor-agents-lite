"""Deterministic synthetic fixture price provider."""

from pathlib import Path

from broker_agents.backtesting.price_history import (
    fixture_path_for_ticker,
    load_price_history,
)
from broker_agents.data_providers.price_provider import PriceHistoryResult


class FixturePriceProvider:
    """Read the repository's deterministic synthetic price fixtures."""

    provider_name = "fixture"
    data_type = "synthetic_fixture"
    live_data_enabled = False
    provider_status = "available"

    def __init__(self, data_root: Path) -> None:
        self.data_root = Path(data_root)

    def get_price_history(self, ticker: str) -> PriceHistoryResult:
        """Load one synthetic ticker fixture with controlled absence."""
        normalized = ticker.strip().upper()
        path = fixture_path_for_ticker(self.data_root, normalized)
        if not path.is_file():
            return PriceHistoryResult(
                ticker=normalized,
                provider_name=self.provider_name,
                data_type=self.data_type,
                status="missing_price_data",
                warnings=[f"Fixture price file not found: {path}"],
            )
        return PriceHistoryResult(
            ticker=normalized,
            rows=load_price_history(path),
            provider_name=self.provider_name,
            data_type=self.data_type,
            status="available",
            price_column_used="close",
        )
