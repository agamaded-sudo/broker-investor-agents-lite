"""Merge normalized market data into a Backoffice data pack."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from broker_agents.fetchers.market_data_fetcher import MarketDataSnapshot


def _present_values(values: dict[str, Any]) -> dict[str, Any]:
    """Return market fields whose values are available."""
    return {key: value for key, value in values.items() if value is not None}


def merge_market_data_into_pack(
    pack: dict,
    market_data: MarketDataSnapshot,
) -> dict:
    """Return a copy of a pack with point-in-time market data and provenance."""
    merged = deepcopy(pack)
    source_id = (
        f"market_data_{market_data.ticker.lower()}_{market_data.as_of_date}"
    )
    valuation = merged.setdefault("valuation_snapshot", {})
    valuation.update(
        {
            **_present_values(
                {
                    "current_price": market_data.current_price,
                    "market_cap": market_data.market_cap,
                    "enterprise_value": market_data.enterprise_value,
                    "pe": market_data.pe,
                    "forward_pe": market_data.forward_pe,
                    "p_fcf": market_data.p_fcf,
                    "ps": market_data.ps,
                    "pb": market_data.pb,
                    "ev_revenue": market_data.ev_revenue,
                    "ev_ebitda": market_data.ev_ebitda,
                    "ev_ebit": market_data.ev_ebit,
                    "fcf_yield": market_data.fcf_yield,
                    "dividend_yield": market_data.dividend_yield,
                }
            ),
            "currency": market_data.currency,
            "source_id": source_id,
            "confidence": "medium",
            "date": market_data.as_of_date,
            "status": "market_data_fixture",
        }
    )

    source_section = merged.setdefault("sources_confidence_data_gaps", {})
    source_log = source_section.setdefault("source_log", [])
    source_record = {
        "source_id": source_id,
        "data_field": "valuation_snapshot",
        "source_name": market_data.source_name,
        "source_type": "market_data_provider",
        "source_url": market_data.source_url,
        "confidence": "medium",
        "confidence_score": 0.70,
        "date_retrieved": market_data.as_of_date,
        "freshness": "fixture",
        "notes": "Market data merged from fixture/source.",
    }
    existing_index = next(
        (
            index
            for index, item in enumerate(source_log)
            if isinstance(item, dict) and item.get("source_id") == source_id
        ),
        None,
    )
    if existing_index is None:
        source_log.append(source_record)
    else:
        source_log[existing_index] = source_record

    return merged
