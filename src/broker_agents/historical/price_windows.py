"""Date-window policies that separate analysis inputs from outcomes."""

from dataclasses import asdict, dataclass, field
from datetime import date

from broker_agents.backtesting.price_history import PricePoint, add_months


@dataclass(frozen=True)
class PriceWindowPolicy:
    """Explicit allowed date range for one use of price history."""

    window_type: str
    start_date: date | None
    end_date: date | None
    as_of_date: date | None
    signal_date: date | None
    forward_months: int | None
    allowed_future_data: bool
    enforcement_status: str
    leakage_policy_note: str

    def to_dict(self) -> dict:
        """Serialize dates using stable ISO strings."""
        data = asdict(self)
        for key in ("start_date", "end_date", "as_of_date", "signal_date"):
            value = data[key]
            data[key] = value.isoformat() if value else None
        return data


@dataclass(frozen=True)
class PriceHistoryFilterResult:
    """Filtered rows plus audit metadata for the applied date cutoff."""

    rows: list[PricePoint] = field(default_factory=list)
    window_start_date: str | None = None
    window_end_date: str | None = None
    rows_before_filter: int = 0
    rows_after_filter: int = 0
    future_rows_excluded_count: int = 0


def _parse_date(value: str | date, field_name: str) -> date:
    """Parse one ISO date while preserving already parsed dates."""
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ValueError(f"{field_name} must use YYYY-MM-DD format.") from exc


def build_analysis_price_window(as_of_date: str | date) -> PriceWindowPolicy:
    """Build a cutoff policy that excludes future analysis prices."""
    cutoff = _parse_date(as_of_date, "as_of_date")
    return PriceWindowPolicy(
        window_type="analysis",
        start_date=None,
        end_date=cutoff,
        as_of_date=cutoff,
        signal_date=None,
        forward_months=None,
        allowed_future_data=False,
        enforcement_status="analysis_window_enforced",
        leakage_policy_note=(
            "Analysis price window excludes prices after as_of_date."
        ),
    )


def build_outcome_price_window(
    signal_date: str | date,
    forward_months: int,
) -> PriceWindowPolicy:
    """Build a forward window reserved for outcome evaluation."""
    if forward_months <= 0:
        raise ValueError("forward_months must be greater than zero.")
    signal = _parse_date(signal_date, "signal_date")
    return PriceWindowPolicy(
        window_type="outcome",
        start_date=signal,
        end_date=add_months(signal, forward_months),
        as_of_date=None,
        signal_date=signal,
        forward_months=forward_months,
        allowed_future_data=True,
        enforcement_status="outcome_evaluation_only",
        leakage_policy_note=(
            "Outcome windows may use future prices only for backtest evaluation."
        ),
    )


def filter_price_history_by_date(
    rows: list[PricePoint],
    *,
    start_date: str | date | None = None,
    end_date: str | date | None = None,
) -> PriceHistoryFilterResult:
    """Filter price rows inclusively and report excluded future rows."""
    start = _parse_date(start_date, "start_date") if start_date else None
    end = _parse_date(end_date, "end_date") if end_date else None
    if start and end and start > end:
        raise ValueError("start_date must not be after end_date.")
    filtered = [
        point
        for point in rows
        if (start is None or point.date >= start)
        and (end is None or point.date <= end)
    ]
    return PriceHistoryFilterResult(
        rows=filtered,
        window_start_date=start.isoformat() if start else None,
        window_end_date=end.isoformat() if end else None,
        rows_before_filter=len(rows),
        rows_after_filter=len(filtered),
        future_rows_excluded_count=(
            sum(point.date > end for point in rows) if end else 0
        ),
    )
