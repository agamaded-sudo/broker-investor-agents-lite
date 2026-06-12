"""Offline price-history utilities for deterministic backtest fixtures."""

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass(frozen=True)
class PricePoint:
    """One dated fixture close."""

    date: date
    close: float


@dataclass(frozen=True)
class ForwardReturnObservation:
    """Observed fixture anchors and return for one forward window."""

    start: PricePoint | None
    end: PricePoint | None
    value: float | None


def load_price_history(path: Path) -> list[PricePoint]:
    """Load and validate a simple date/close fixture CSV."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Price history fixture not found: {path}")
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    points = [
        PricePoint(
            date=date.fromisoformat(str(row["date"]).strip()),
            close=float(row["close"]),
        )
        for row in rows
    ]
    if not points:
        raise ValueError(f"Price history fixture is empty: {path}")
    return sorted(points, key=lambda point: point.date)


def fixture_path_for_ticker(fixtures_root: Path, ticker: str) -> Path:
    """Return the conventional fixture path for a ticker."""
    return Path(fixtures_root) / f"{ticker.strip().lower()}.csv"


def add_months(value: date, months: int) -> date:
    """Add calendar months while clamping the day to the target month."""
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    next_month_year = year + (1 if month == 12 else 0)
    next_month = 1 if month == 12 else month + 1
    last_day = (
        date(next_month_year, next_month, 1) - date.resolution
    ).day
    return date(year, month, min(value.day, last_day))


def first_point_on_or_after(
    points: list[PricePoint],
    target: date,
) -> PricePoint | None:
    """Return the first fixture observation on or after a target date."""
    return next((point for point in points if point.date >= target), None)


def forward_return(
    points: list[PricePoint],
    start_date: date,
    months: int,
) -> float | None:
    """Calculate a simple fixture return from the first available dates."""
    return forward_return_observation(points, start_date, months).value


def forward_return_observation(
    points: list[PricePoint],
    start_date: date,
    months: int,
) -> ForwardReturnObservation:
    """Return the actual fixture anchors and simple forward return."""
    start = first_point_on_or_after(points, start_date)
    end = first_point_on_or_after(points, add_months(start_date, months))
    if start is None or end is None or start.close == 0:
        return ForwardReturnObservation(start=start, end=end, value=None)
    return ForwardReturnObservation(
        start=start,
        end=end,
        value=(end.close - start.close) / start.close,
    )


def max_drawdown(
    points: list[PricePoint],
    start_date: date,
    months: int = 12,
) -> float | None:
    """Calculate maximum peak-to-trough drawdown within a fixture window."""
    end_date = add_months(start_date, months)
    window = [
        point
        for point in points
        if start_date <= point.date <= end_date
    ]
    if not window:
        return None
    peak = window[0].close
    worst = 0.0
    for point in window:
        peak = max(peak, point.close)
        if peak:
            worst = min(worst, (point.close - peak) / peak)
    return worst
