"""Offline-safe growth and PEG fetcher skeleton and fixture mapping."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GrowthPegSnapshot:
    """Normalized historical and forward growth evidence."""

    ticker: str
    company_name: str
    as_of_date: str
    currency: str
    revenue_cagr_3y: float | int | None
    revenue_cagr_5y: float | int | None
    eps_cagr_3y: float | int | None
    eps_cagr_5y: float | int | None
    fcf_cagr_3y: float | int | None
    fcf_cagr_5y: float | int | None
    forward_revenue_growth: float | int | None
    forward_eps_growth: float | int | None
    current_pe: float | int | None
    peg_ratio: float | int | None
    growth_quality_label: str
    growth_data_confidence: str
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


def load_growth_peg_fixture(path: Path) -> dict:
    """Load a compact growth and PEG JSON fixture."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Growth and PEG fixture not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid growth and PEG fixture JSON in {path}: {exc}") from exc
    except OSError as exc:
        raise OSError(f"Could not read growth and PEG fixture {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Growth and PEG fixture must contain a JSON object: {path}")
    return data


class GrowthPegFetcher:
    """Prepare growth and PEG interfaces without live requests."""

    def fetch_growth_peg(self, ticker: str) -> dict:
        """Reserve the live fetch interface without performing network I/O."""
        if not ticker.strip():
            raise ValueError("Ticker is required for growth and PEG fetching.")
        raise NotImplementedError(
            "Live growth and PEG fetching is not implemented yet. "
            "Use fixture data or manual inputs."
        )

    def map_fixture_to_growth_peg(self, raw: dict) -> GrowthPegSnapshot:
        """Map a compact fixture into normalized growth and PEG evidence."""
        if not isinstance(raw, dict):
            raise ValueError("Growth and PEG fixture must be a dictionary.")
        ticker = str(raw.get("ticker") or "").strip().upper()
        if not ticker:
            raise ValueError("Growth and PEG fixture is missing ticker.")
        as_of_date = str(raw.get("as_of_date") or "")
        if not as_of_date:
            raise ValueError("Growth and PEG fixture is missing as_of_date.")

        return GrowthPegSnapshot(
            ticker=ticker,
            company_name=str(raw.get("company_name") or ""),
            as_of_date=as_of_date,
            currency=str(raw.get("currency") or "USD"),
            revenue_cagr_3y=_number(raw.get("revenue_cagr_3y")),
            revenue_cagr_5y=_number(raw.get("revenue_cagr_5y")),
            eps_cagr_3y=_number(raw.get("eps_cagr_3y")),
            eps_cagr_5y=_number(raw.get("eps_cagr_5y")),
            fcf_cagr_3y=_number(raw.get("fcf_cagr_3y")),
            fcf_cagr_5y=_number(raw.get("fcf_cagr_5y")),
            forward_revenue_growth=_number(raw.get("forward_revenue_growth")),
            forward_eps_growth=_number(raw.get("forward_eps_growth")),
            current_pe=_number(raw.get("current_pe")),
            peg_ratio=_number(raw.get("peg_ratio")),
            growth_quality_label=str(
                raw.get("growth_quality_label") or "not established"
            ),
            growth_data_confidence=str(
                raw.get("growth_data_confidence") or "medium_market_fixture"
            ),
            source_name=str(raw.get("source_name") or "Growth PEG Fixture"),
            source_url=str(raw.get("source_url") or ""),
            confidence=str(raw.get("confidence") or "medium"),
        )
