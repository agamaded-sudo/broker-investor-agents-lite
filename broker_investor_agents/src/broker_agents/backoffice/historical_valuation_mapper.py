"""Merge normalized historical valuation data into a Backoffice pack."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from broker_agents.fetchers.historical_valuation_fetcher import (
    HistoricalValuationSnapshot,
)


def _present_values(values: dict[str, Any]) -> dict[str, Any]:
    """Return historical valuation fields whose values are available."""
    return {key: value for key, value in values.items() if value is not None}


def merge_historical_valuation_into_pack(
    pack: dict,
    historical_valuation: HistoricalValuationSnapshot,
) -> dict:
    """Return a copy of a pack with sourced historical valuation evidence."""
    merged = deepcopy(pack)
    source_id = (
        f"historical_valuation_{historical_valuation.ticker.lower()}_"
        f"{historical_valuation.as_of_date}"
    )
    section = merged.setdefault("historical_valuation", {})
    section.update(
        {
            **_present_values(
                {
                    "pe_5y_median": historical_valuation.pe_5y_median,
                    "pe_10y_median": historical_valuation.pe_10y_median,
                    "p_fcf_5y_median": historical_valuation.p_fcf_5y_median,
                    "p_fcf_10y_median": historical_valuation.p_fcf_10y_median,
                    "ev_ebitda_5y_median": historical_valuation.ev_ebitda_5y_median,
                    "ev_ebitda_10y_median": historical_valuation.ev_ebitda_10y_median,
                    "current_vs_5y_p_fcf_percentile": (
                        historical_valuation.current_vs_5y_p_fcf_percentile
                    ),
                    "current_vs_10y_p_fcf_percentile": (
                        historical_valuation.current_vs_10y_p_fcf_percentile
                    ),
                }
            ),
            "currency": historical_valuation.currency,
            "source_id": source_id,
            "confidence": "medium",
            "as_of_date": historical_valuation.as_of_date,
            "valuation_history_confidence": (
                historical_valuation.valuation_history_confidence
            ),
            "current_snapshot_only": False,
        }
    )

    source_section = merged.setdefault("sources_confidence_data_gaps", {})
    source_log = source_section.setdefault("source_log", [])
    source_record = {
        "source_id": source_id,
        "data_field": "historical_valuation",
        "source_name": historical_valuation.source_name,
        "source_type": "historical_market_data_provider",
        "source_url": historical_valuation.source_url,
        "confidence": "medium",
        "confidence_score": 0.70,
        "date_retrieved": historical_valuation.as_of_date,
        "freshness": "fixture",
        "notes": "Historical valuation data merged from fixture/source.",
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
