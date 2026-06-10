"""Tests for merging fixture historical valuation into Backoffice packs."""

from pathlib import Path

import yaml

from broker_agents.backoffice.historical_valuation_mapper import (
    merge_historical_valuation_into_pack,
)
from broker_agents.backoffice.source_verification import verify_sources
from broker_agents.fetchers.historical_valuation_fetcher import (
    HistoricalValuationFetcher,
    load_historical_valuation_fixture,
)
from broker_agents.reports.backoffice_missing_evidence_report import (
    generate_backoffice_missing_evidence_report,
)
from broker_agents.reports.investor_agent_readiness_dashboard import (
    generate_investor_agent_readiness_dashboard,
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


def _merged_pack(ticker: str) -> tuple[dict, dict]:
    pack = _load_yaml(ROOT / "examples" / f"{ticker.lower()}_input.yaml")
    fixture = load_historical_valuation_fixture(
        ROOT / "tests" / "fixtures" / f"historical_valuation_{ticker.lower()}.json"
    )
    snapshot = (
        HistoricalValuationFetcher().map_fixture_to_historical_valuation(fixture)
    )
    return pack, merge_historical_valuation_into_pack(pack, snapshot)


def test_merge_updates_history_and_preserves_manual_input() -> None:
    input_path = ROOT / "examples" / "msft_input.yaml"
    original_text = input_path.read_text(encoding="utf-8")
    pack, merged = _merged_pack("MSFT")
    history = merged["historical_valuation"]

    assert history["pe_5y_median"] == 34
    assert history["p_fcf_10y_median"] == 30
    assert history["current_vs_10y_p_fcf_percentile"] == 0.85
    assert history["source_id"] == "historical_valuation_msft_2026-06-01"
    assert history["as_of_date"] == "2026-06-01"
    assert history["valuation_history_confidence"] == "medium_market_fixture"
    assert "source_id" not in pack["historical_valuation"]
    assert input_path.read_text(encoding="utf-8") == original_text


def test_merge_adds_medium_confidence_historical_source_log() -> None:
    _, merged = _merged_pack("AAPL")
    source = next(
        item
        for item in merged["sources_confidence_data_gaps"]["source_log"]
        if item["source_id"] == "historical_valuation_aapl_2026-06-01"
    )

    assert source["data_field"] == "historical_valuation"
    assert source["source_type"] == "historical_market_data_provider"
    assert source["confidence"] == "medium"
    assert source["date_retrieved"] == "2026-06-01"
    assert source["notes"] == (
        "Historical valuation data merged from fixture/source."
    )


def test_merge_removes_placeholder_heavy_source_classification() -> None:
    pack, merged = _merged_pack("NVDA")
    before = verify_sources(pack)
    after = verify_sources(merged)

    assert _quality(before, "historical_valuation") == "placeholder-heavy"
    assert _quality(after, "historical_valuation") == "strong"
    history_records = [
        item
        for item in after["source_verification_records"]
        if item["section"] == "historical_valuation"
    ]
    assert all(item["status"] == "market_data_verified" for item in history_records)


def test_evidence_and_readiness_use_provider_methodology_language() -> None:
    worklist = generate_backoffice_missing_evidence_report(
        ["MSFT", "AAPL", "NVDA"],
        ROOT / "data" / "outputs",
        ROOT / "examples",
    )
    dashboard = generate_investor_agent_readiness_dashboard(
        ["MSFT", "AAPL", "NVDA"],
        ROOT / "data" / "outputs",
        ROOT / "examples",
    )

    assert "Historical valuation source validation" in worklist
    assert "Provider methodology validation" in worklist
    assert "5Y/10Y median calculation methodology" in worklist
    assert "Percentile methodology validation" in worklist
    assert "historical valuation provider validation" in dashboard
    assert "historical valuation methodology validation" in dashboard
