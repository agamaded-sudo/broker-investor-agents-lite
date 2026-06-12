"""Deterministic synthetic fixture price provider."""

from datetime import date
from pathlib import Path

from broker_agents.backtesting.price_history import (
    fixture_path_for_ticker,
    load_price_history,
)
from broker_agents.data_providers.price_provider import PriceHistoryResult
from broker_agents.historical.price_windows import (
    filter_price_history_by_date,
)


class FixturePriceProvider:
    """Read the repository's deterministic synthetic price fixtures."""

    provider_name = "fixture"
    data_type = "synthetic_fixture"
    live_data_enabled = False
    provider_status = "available"

    def __init__(self, data_root: Path) -> None:
        self.data_root = Path(data_root)

    def get_price_history(
        self,
        ticker: str,
        *,
        start_date: str | date | None = None,
        end_date: str | date | None = None,
        window_type: str | None = None,
    ) -> PriceHistoryResult:
        """Load one synthetic fixture with optional date filtering."""
        normalized = ticker.strip().upper()
        path = fixture_path_for_ticker(self.data_root, normalized)
        if not path.is_file():
            return PriceHistoryResult(
                ticker=normalized,
                provider_name=self.provider_name,
                data_type=self.data_type,
                status="missing_price_data",
                warnings=[f"Fixture price file not found: {path}"],
                window_type=window_type,
            )
        filtered = filter_price_history_by_date(
            load_price_history(path),
            start_date=start_date,
            end_date=end_date,
        )
        status = "available"
        warnings = []
        if window_type == "analysis" and end_date is not None:
            status = "analysis_window_enforced"
        if not filtered.rows:
            status = "missing_price_window_data"
            warnings.append(
                "No fixture price rows are available in the requested window."
            )
        return PriceHistoryResult(
            ticker=normalized,
            rows=filtered.rows,
            provider_name=self.provider_name,
            data_type=self.data_type,
            status=status,
            price_column_used="close",
            warnings=warnings,
            window_type=window_type,
            window_start_date=filtered.window_start_date,
            window_end_date=filtered.window_end_date,
            rows_before_filter=filtered.rows_before_filter,
            rows_after_filter=filtered.rows_after_filter,
            future_rows_excluded_count=filtered.future_rows_excluded_count,
        )
