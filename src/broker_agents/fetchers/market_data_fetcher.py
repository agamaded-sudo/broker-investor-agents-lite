"""Offline-safe market data fetcher skeleton and fixture mapping."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class MarketDataSnapshot:
    """Normalized point-in-time market and valuation data."""

    ticker: str
    company_name: str
    as_of_date: str
    currency: str
    current_price: float | int | None
    market_cap: float | int | None
    enterprise_value: float | int | None
    pe: float | int | None
    forward_pe: float | int | None
    p_fcf: float | int | None
    ps: float | int | None
    pb: float | int | None
    ev_revenue: float | int | None
    ev_ebitda: float | int | None
    ev_ebit: float | int | None
    fcf_yield: float | int | None
    dividend_yield: float | int | None
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


def load_market_data_fixture(path: Path) -> dict:
    """Load a compact market-data JSON fixture."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Market data fixture not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid market data fixture JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise OSError(f"Could not read market data fixture {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Market data fixture must contain a JSON object: {path}")
    return data


class MarketDataFetcher:
    """Prepare market-data interfaces and fixture mapping without live requests."""

    def fetch_market_data(self, ticker: str) -> dict:
        """Reserve the live market-data interface without performing network I/O."""
        if not ticker.strip():
            raise ValueError("Ticker is required for market data fetching.")
        raise NotImplementedError(
            "Live market data fetching is not implemented yet. "
            "Use fixture data or manual inputs."
        )

    def map_fixture_to_market_data(self, raw: dict) -> MarketDataSnapshot:
        """Map a compact fixture dictionary into a normalized market snapshot."""
        if not isinstance(raw, dict):
            raise ValueError("Market data fixture must be a dictionary.")
        ticker = str(raw.get("ticker") or "").strip().upper()
        if not ticker:
            raise ValueError("Market data fixture is missing ticker.")
        as_of_date = str(raw.get("as_of_date") or "")
        if not as_of_date:
            raise ValueError("Market data fixture is missing as_of_date.")

        return MarketDataSnapshot(
            ticker=ticker,
            company_name=str(raw.get("company_name") or ""),
            as_of_date=as_of_date,
            currency=str(raw.get("currency") or "USD"),
            current_price=_number(raw.get("current_price")),
            market_cap=_number(raw.get("market_cap")),
            enterprise_value=_number(raw.get("enterprise_value")),
            pe=_number(raw.get("pe")),
            forward_pe=_number(raw.get("forward_pe")),
            p_fcf=_number(raw.get("p_fcf")),
            ps=_number(raw.get("ps")),
            pb=_number(raw.get("pb")),
            ev_revenue=_number(raw.get("ev_revenue")),
            ev_ebitda=_number(raw.get("ev_ebitda")),
            ev_ebit=_number(raw.get("ev_ebit")),
            fcf_yield=_number(raw.get("fcf_yield")),
            dividend_yield=_number(raw.get("dividend_yield")),
            source_name=str(raw.get("source_name") or "Market Data Fixture"),
            source_url=str(raw.get("source_url") or ""),
            confidence=str(raw.get("confidence") or "medium"),
        )
