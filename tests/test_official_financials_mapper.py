"""Tests for merging official fixture financials into Backoffice packs."""

from pathlib import Path

import yaml

from broker_agents.backoffice.official_financials_mapper import (
    merge_official_financials_into_pack,
)
from broker_agents.backoffice.source_verification import verify_sources
from broker_agents.fetchers.sec_financials_fetcher import (
    load_sec_fixture,
    map_fixture_to_financials,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _section_quality(result: dict, section: str) -> str:
    return next(
        item["section_quality_label"]
        for item in result["source_quality_by_section"]
        if item["section_name"] == section
    )


def test_merge_updates_statement_lists_and_preserves_existing_pack() -> None:
    input_path = ROOT / "examples" / "msft_input.yaml"
    original_text = input_path.read_text(encoding="utf-8")
    pack = _load_yaml(input_path)
    financials = map_fixture_to_financials(
        load_sec_fixture(ROOT / "tests" / "fixtures" / "sec_company_facts_msft.json")
    )

    merged = merge_official_financials_into_pack(pack, financials)
    statements = merged["financial_statements_summary"]

    assert statements["income_statement"][0]["revenue"] == 281700
    assert statements["balance_sheet"][0]["cash_and_equivalents"] == 94600
    assert statements["cash_flow_statement"][0]["operating_cash_flow"] == 136200
    assert statements["cash_flow_statement"][0]["free_cash_flow"] == 71600
    assert statements["annual"]["source_id"] == "sec_company_facts_msft_FY2025"
    assert "income_statement" not in pack["financial_statements_summary"]
    assert input_path.read_text(encoding="utf-8") == original_text


def test_merge_adds_high_confidence_source_log_and_note() -> None:
    pack = _load_yaml(ROOT / "examples" / "aapl_input.yaml")
    financials = map_fixture_to_financials(
        load_sec_fixture(ROOT / "tests" / "fixtures" / "sec_company_facts_aapl.json")
    )

    merged = merge_official_financials_into_pack(pack, financials)
    source_log = merged["sources_confidence_data_gaps"]["source_log"]
    source = next(
        item
        for item in source_log
        if item["source_id"] == "sec_company_facts_aapl_FY2024"
    )

    assert source["confidence"] == "high"
    assert source["source_type"] == "company"
    assert (
        "Official financials merged from SEC fixture/source."
        in merged["financial_statements_summary"]["notes"]
    )


def test_merge_improves_placeholder_financial_source_quality() -> None:
    pack = _load_yaml(ROOT / "examples" / "nvda_input.yaml")
    financials = map_fixture_to_financials(
        load_sec_fixture(ROOT / "tests" / "fixtures" / "sec_company_facts_nvda.json")
    )
    before = verify_sources(pack)
    merged = merge_official_financials_into_pack(pack, financials)
    after = verify_sources(merged)

    assert _section_quality(before, "financial_statements_summary") == (
        "placeholder-heavy"
    )
    assert _section_quality(after, "financial_statements_summary") == "strong"
    financial_records = [
        item
        for item in after["source_verification_records"]
        if item["section"] == "financial_statements_summary"
    ]
    assert all(item["status"] == "official_verified" for item in financial_records)
