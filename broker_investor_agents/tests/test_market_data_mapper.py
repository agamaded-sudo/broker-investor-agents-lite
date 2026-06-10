"""Tests for merging fixture market data into Backoffice packs."""

from pathlib import Path

import yaml

from broker_agents.backoffice.market_data_mapper import merge_market_data_into_pack
from broker_agents.backoffice.source_verification import verify_sources
from broker_agents.fetchers.market_data_fetcher import (
    MarketDataFetcher,
    load_market_data_fixture,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _quality(result: dict, section: str) -> str:
    return next(
        item["section_quality_label"]
        for item in result["source_quality_by_section"]
        if item["section_name"] == section
    )


def test_market_merge_updates_valuation_and_preserves_manual_input() -> None:
    input_path = ROOT / "examples" / "msft_input.yaml"
    original_text = input_path.read_text(encoding="utf-8")
    pack = _load_yaml(input_path)
    snapshot = MarketDataFetcher().map_fixture_to_market_data(
        load_market_data_fixture(
            ROOT / "tests" / "fixtures" / "market_data_msft.json"
        )
    )

    merged = merge_market_data_into_pack(pack, snapshot)
    valuation = merged["valuation_snapshot"]

    assert valuation["current_price"] == 430
    assert valuation["market_cap"] == 3180000
    assert valuation["pe"] == 31.2
    assert valuation["p_fcf"] == 44.4
    assert valuation["fcf_yield"] == 0.023
    assert valuation["date"] == "2026-06-01"
    assert valuation["source_id"] == "market_data_msft_2026-06-01"
    assert "current_price" not in pack["valuation_snapshot"]
    assert input_path.read_text(encoding="utf-8") == original_text


def test_market_merge_adds_medium_confidence_source_log() -> None:
    pack = _load_yaml(ROOT / "examples" / "aapl_input.yaml")
    snapshot = MarketDataFetcher().map_fixture_to_market_data(
        load_market_data_fixture(
            ROOT / "tests" / "fixtures" / "market_data_aapl.json"
        )
    )
    merged = merge_market_data_into_pack(pack, snapshot)
    source = next(
        item
        for item in merged["sources_confidence_data_gaps"]["source_log"]
        if item["source_id"] == "market_data_aapl_2026-06-01"
    )

    assert source["data_field"] == "valuation_snapshot"
    assert source["source_type"] == "market_data_provider"
    assert source["confidence"] == "medium"
    assert source["date_retrieved"] == "2026-06-01"
    assert source["notes"] == "Market data merged from fixture/source."


def test_market_merge_improves_valuation_source_quality() -> None:
    pack = _load_yaml(ROOT / "examples" / "nvda_input.yaml")
    snapshot = MarketDataFetcher().map_fixture_to_market_data(
        load_market_data_fixture(
            ROOT / "tests" / "fixtures" / "market_data_nvda.json"
        )
    )
    before = verify_sources(pack)
    after = verify_sources(merge_market_data_into_pack(pack, snapshot))

    assert _quality(before, "valuation_snapshot") == "placeholder-heavy"
    assert _quality(after, "valuation_snapshot") == "strong"
    valuation_records = [
        item
        for item in after["source_verification_records"]
        if item["section"] == "valuation_snapshot"
    ]
    assert all(item["status"] == "market_data_verified" for item in valuation_records)
