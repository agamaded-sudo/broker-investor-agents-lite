"""Merge normalized growth and PEG evidence into a Backoffice pack."""

from __future__ import annotations

from copy import deepcopy

from broker_agents.fetchers.growth_peg_fetcher import GrowthPegSnapshot


def merge_growth_peg_into_pack(
    pack: dict,
    growth_peg: GrowthPegSnapshot,
) -> dict:
    """Return a copy of a pack with sourced growth and PEG evidence."""
    merged = deepcopy(pack)
    source_id = f"growth_peg_{growth_peg.ticker.lower()}_{growth_peg.as_of_date}"
    section = merged.setdefault("growth_peg_analysis", {})
    section.update(growth_peg.to_dict())
    section.update(
        {
            "source_id": source_id,
            "as_of_date": growth_peg.as_of_date,
            "growth_data_confidence": "medium_market_fixture",
            "confidence": "medium",
        }
    )

    source_section = merged.setdefault("sources_confidence_data_gaps", {})
    source_log = source_section.setdefault("source_log", [])
    source_record = {
        "source_id": source_id,
        "data_field": "growth_peg_analysis",
        "source_name": growth_peg.source_name,
        "source_type": "growth_market_data_provider",
        "source_url": growth_peg.source_url,
        "confidence": "medium",
        "confidence_score": 0.70,
        "date_retrieved": growth_peg.as_of_date,
        "freshness": "fixture",
        "notes": "Growth and PEG data merged from fixture/source.",
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
