"""Common price history provider interface and provider factory."""

from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Protocol

from broker_agents.backtesting.price_history import PricePoint


@dataclass(frozen=True)
class PriceHistoryResult:
    """Controlled result returned by every price history provider."""

    ticker: str
    rows: list[PricePoint] = field(default_factory=list)
    provider_name: str = ""
    data_type: str = ""
    status: str = "missing_price_data"
    price_column_used: str | None = None
    warnings: list[str] = field(default_factory=list)
    window_type: str | None = None
    window_start_date: str | None = None
    window_end_date: str | None = None
    rows_before_filter: int = 0
    rows_after_filter: int = 0
    future_rows_excluded_count: int = 0


class PriceHistoryProvider(Protocol):
    """Minimal dependency-light provider contract."""

    provider_name: str
    data_type: str
    data_root: Path | None
    live_data_enabled: bool
    provider_status: str

    def get_price_history(
        self,
        ticker: str,
        *,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        window_type: str | None = None,
    ) -> PriceHistoryResult:
        """Return controlled price history data for a ticker."""


def create_price_provider(
    provider_name: str,
    data_root: Path | None,
) -> PriceHistoryProvider:
    """Create one supported provider without importing network clients."""
    normalized = str(provider_name or "").strip().lower()
    if normalized == "fixture":
        from broker_agents.data_providers.fixture_price_provider import (
            FixturePriceProvider,
        )

        return FixturePriceProvider(Path(data_root or "tests/fixtures/price_history"))
    if normalized == "csv":
        from broker_agents.data_providers.csv_price_provider import (
            CsvPriceProvider,
        )

        return CsvPriceProvider(Path(data_root or "."))
    if normalized == "live_stub":
        from broker_agents.data_providers.live_stub_price_provider import (
            LiveStubPriceProvider,
        )

        return LiveStubPriceProvider()
    raise ValueError(
        "price_provider must be one of: fixture, csv, live_stub."
    )
