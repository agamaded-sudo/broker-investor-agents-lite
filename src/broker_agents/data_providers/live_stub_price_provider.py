"""Network-free live price provider placeholder."""

from pathlib import Path

from broker_agents.data_providers.price_provider import PriceHistoryResult

LIVE_STUB_MESSAGE = (
    "Live data provider is not implemented in this build. "
    "Use fixture or csv provider."
)


class LiveStubPriceProvider:
    """Return a controlled status without making any network call."""

    provider_name = "live_stub"
    data_type = "live_stub"
    data_root: Path | None = None
    live_data_enabled = False
    provider_status = "live_provider_not_configured"

    def get_price_history(self, ticker: str) -> PriceHistoryResult:
        """Report that live data is intentionally unavailable."""
        return PriceHistoryResult(
            ticker=ticker.strip().upper(),
            provider_name=self.provider_name,
            data_type=self.data_type,
            status=self.provider_status,
            warnings=[LIVE_STUB_MESSAGE],
        )
