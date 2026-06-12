"""Local user-provided CSV price history provider."""

from datetime import date
from pathlib import Path

from broker_agents.backtesting.price_history import (
    fixture_path_for_ticker,
    load_local_csv_price_history,
)
from broker_agents.data_providers.price_provider import PriceHistoryResult
from broker_agents.historical.price_windows import (
    filter_price_history_by_date,
)


class CsvPriceProvider:
    """Read local ticker CSV files using the shared date/close schema."""

    provider_name = "csv"
    data_type = "local_csv"
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
        """Load one local CSV with optional auditable date filtering."""
        normalized = ticker.strip().upper()
        path = fixture_path_for_ticker(self.data_root, normalized)
        if not path.is_file():
            return PriceHistoryResult(
                ticker=normalized,
                provider_name=self.provider_name,
                data_type=self.data_type,
                status="missing_price_data",
                warnings=[f"Local CSV price file not found: {path}"],
                window_type=window_type,
            )
        try:
            rows, price_column_used = load_local_csv_price_history(path)
            filtered = filter_price_history_by_date(
                rows,
                start_date=start_date,
                end_date=end_date,
            )
        except (KeyError, TypeError, ValueError) as exc:
            return PriceHistoryResult(
                ticker=normalized,
                provider_name=self.provider_name,
                data_type=self.data_type,
                status="invalid_price_data",
                warnings=[str(exc)],
                window_type=window_type,
            )
        warnings = []
        status = "available"
        if window_type == "analysis" and end_date is not None:
            status = "analysis_window_enforced"
        if not filtered.rows:
            status = "missing_price_window_data"
            warnings.append(
                "No local CSV price rows are available in the requested window."
            )
        return PriceHistoryResult(
            ticker=normalized,
            rows=filtered.rows,
            provider_name=self.provider_name,
            data_type=self.data_type,
            status=status,
            price_column_used=price_column_used,
            warnings=warnings,
            window_type=window_type,
            window_start_date=filtered.window_start_date,
            window_end_date=filtered.window_end_date,
            rows_before_filter=filtered.rows_before_filter,
            rows_after_filter=filtered.rows_after_filter,
            future_rows_excluded_count=filtered.future_rows_excluded_count,
        )
