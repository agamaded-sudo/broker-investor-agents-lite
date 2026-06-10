"""Offline-safe historical valuation fetcher skeleton and fixture mapping."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class HistoricalValuationSnapshot:
    """Normalized historical valuation summary for one company."""

    ticker: str
    company_name: str
    as_of_date: str
    currency: str
    pe_5y_median: float | int | None
    pe_10y_median: float | int | None
    p_fcf_5y_median: float | int | None
    p_fcf_10y_median: float | int | None
    ev_ebitda_5y_median: float | int | None
    ev_ebitda_10y_median: float | int | None
    current_vs_5y_p_fcf_percentile: float | int | None
    current_vs_10y_p_fcf_percentile: float | int | None
    valuation_history_confidence: str
    source_name: str
    source_url: str
    confidence: str

    def to_dict(self) -> dict:
        """Return the normalized snapshot as a plain dictionary."""
        return asdict(self)


def _number(value: Any) -> float | int | None:
    """Return a numeric fixture value or None."""
    if value in (None, "") or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def load_historical_valuation_fixture(path: Path) -> dict:
    """Load a compact historical valuation JSON fixture."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(
            f"Historical valuation fixture not found: {path}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Invalid historical valuation fixture JSON in {path}: {exc}"
        ) from exc
    except OSError as exc:
        raise OSError(
            f"Could not read historical valuation fixture {path}: {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise ValueError(
            f"Historical valuation fixture must contain a JSON object: {path}"
        )
    return data


class HistoricalValuationFetcher:
    """Prepare historical valuation interfaces without live requests."""

    def fetch_historical_valuation(self, ticker: str) -> dict:
        """Reserve the live fetch interface without performing network I/O."""
        if not ticker.strip():
            raise ValueError("Ticker is required for historical valuation fetching.")
        raise NotImplementedError(
            "Live historical valuation fetching is not implemented yet. "
            "Use fixture data or manual inputs."
        )

    def map_fixture_to_historical_valuation(
        self,
        raw: dict,
    ) -> HistoricalValuationSnapshot:
        """Map a compact fixture into a normalized historical valuation snapshot."""
        if not isinstance(raw, dict):
            raise ValueError("Historical valuation fixture must be a dictionary.")
        ticker = str(raw.get("ticker") or "").strip().upper()
        if not ticker:
            raise ValueError("Historical valuation fixture is missing ticker.")
        as_of_date = str(raw.get("as_of_date") or "")
        if not as_of_date:
            raise ValueError("Historical valuation fixture is missing as_of_date.")

        return HistoricalValuationSnapshot(
            ticker=ticker,
            company_name=str(raw.get("company_name") or ""),
            as_of_date=as_of_date,
            currency=str(raw.get("currency") or "USD"),
            pe_5y_median=_number(raw.get("pe_5y_median")),
            pe_10y_median=_number(raw.get("pe_10y_median")),
            p_fcf_5y_median=_number(raw.get("p_fcf_5y_median")),
            p_fcf_10y_median=_number(raw.get("p_fcf_10y_median")),
            ev_ebitda_5y_median=_number(raw.get("ev_ebitda_5y_median")),
            ev_ebitda_10y_median=_number(raw.get("ev_ebitda_10y_median")),
            current_vs_5y_p_fcf_percentile=_number(
                raw.get("current_vs_5y_p_fcf_percentile")
            ),
            current_vs_10y_p_fcf_percentile=_number(
                raw.get("current_vs_10y_p_fcf_percentile")
            ),
            valuation_history_confidence=str(
                raw.get("valuation_history_confidence")
                or "medium_market_fixture"
            ),
            source_name=str(
                raw.get("source_name") or "Historical Valuation Fixture"
            ),
            source_url=str(raw.get("source_url") or ""),
            confidence=str(raw.get("confidence") or "medium"),
        )
