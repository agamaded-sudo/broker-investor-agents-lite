"""Lightweight validation for locally supplied ticker price CSV files."""

from dataclasses import dataclass
from pathlib import Path

from broker_agents.backtesting.price_history import fixture_path_for_ticker
from broker_agents.data_providers.price_provider import create_price_provider


@dataclass(frozen=True)
class PriceCsvValidationResult:
    """One ticker's local price-file validation result."""

    ticker: str
    file_found: bool
    rows_count: int
    min_date: str | None
    max_date: str | None
    price_column_used: str | None
    status: str
    warnings: list[str]


def validate_price_csvs(
    tickers: list[str],
    data_root: Path,
    provider_name: str = "csv",
) -> list[PriceCsvValidationResult]:
    """Validate local price histories without requiring a signal ledger."""
    provider = create_price_provider(provider_name, data_root)
    results = []
    for ticker in tickers:
        normalized = ticker.strip().upper()
        if not normalized:
            continue
        provider_result = provider.get_price_history(normalized)
        path = fixture_path_for_ticker(data_root, normalized)
        dates = [point.date for point in provider_result.rows]
        results.append(
            PriceCsvValidationResult(
                ticker=normalized,
                file_found=path.is_file(),
                rows_count=len(provider_result.rows),
                min_date=min(dates).isoformat() if dates else None,
                max_date=max(dates).isoformat() if dates else None,
                price_column_used=provider_result.price_column_used,
                status=provider_result.status,
                warnings=provider_result.warnings,
            )
        )
    return results
