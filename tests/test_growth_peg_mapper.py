"""Tests for growth and PEG fixture merging and Lynch consumption."""

from pathlib import Path

import yaml

from broker_agents.agents.lynch_agent import LynchAgent
from broker_agents.backoffice.growth_peg_mapper import merge_growth_peg_into_pack
from broker_agents.backoffice.source_verification import verify_sources
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.fetchers.growth_peg_fetcher import (
    GrowthPegFetcher,
    load_growth_peg_fixture,
)
from broker_agents.reports.backoffice_missing_evidence_report import (
    generate_backoffice_missing_evidence_report,
)
from broker_agents.reports.investor_agent_readiness_dashboard import (
    generate_investor_agent_readiness_dashboard,
)
from broker_agents.reports.multi_company_comparison_report import (
    generate_multi_company_comparison,
)

ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _merged_pack(ticker: str) -> tuple[dict, dict]:
    pack = _load_yaml(ROOT / "examples" / f"{ticker.lower()}_input.yaml")
    fixture = load_growth_peg_fixture(
        ROOT / "tests" / "fixtures" / f"growth_peg_{ticker.lower()}.json"
    )
    snapshot = GrowthPegFetcher().map_fixture_to_growth_peg(fixture)
    return pack, merge_growth_peg_into_pack(pack, snapshot)


def _quality(result: dict, section: str) -> str:
    return next(
        item["section_quality_label"]
        for item in result["source_quality_by_section"]
        if item["section_name"] == section
    )


def test_merge_updates_growth_section_and_preserves_manual_input() -> None:
    input_path = ROOT / "examples" / "msft_input.yaml"
    original_text = input_path.read_text(encoding="utf-8")
    pack, merged = _merged_pack("MSFT")
    growth = merged["growth_peg_analysis"]

    assert growth["revenue_cagr_3y"] == 0.13
    assert growth["eps_cagr_5y"] == 0.14
    assert growth["peg_ratio"] == 2.40
    assert growth["source_id"] == "growth_peg_msft_2026-06-01"
    assert growth["growth_data_confidence"] == "medium_market_fixture"
    assert "growth_peg_analysis" not in pack
    assert input_path.read_text(encoding="utf-8") == original_text


def test_merge_adds_market_source_and_improves_source_quality() -> None:
    _, merged = _merged_pack("AAPL")
    source = next(
        item
        for item in merged["sources_confidence_data_gaps"]["source_log"]
        if item["source_id"] == "growth_peg_aapl_2026-06-01"
    )
    verification = verify_sources(merged)
    records = [
        item
        for item in verification["source_verification_records"]
        if item["section"] == "growth_peg_analysis"
    ]

    assert source["source_type"] == "growth_market_data_provider"
    assert source["confidence"] == "medium"
    assert source["notes"] == "Growth and PEG data merged from fixture/source."
    assert _quality(verification, "growth_peg_analysis") == "strong"
    assert all(item["status"] == "market_data_verified" for item in records)


def test_lynch_report_consumes_growth_evidence_without_changing_final_decision() -> None:
    _, merged = _merged_pack("NVDA")
    report = LynchAgent(
        merged,
        ROOT / "methods" / "lynch_method.yaml",
    ).generate_report()
    eligibility = evaluate_promotion_eligibility(merged, "lynch")

    assert "Growth & PEG Evidence" in report
    assert "75.0%" in report
    assert "1.4x" in report
    assert "cycle-sensitive" in report
    assert "## Decision\nFollow / Watch" in report
    assert eligibility["auto_promotion_allowed"] is False
    assert "source and methodology validation" in " ".join(
        eligibility["required_evidence"]
    )


def test_aggregate_reports_use_precise_growth_methodology_language() -> None:
    comparison = generate_multi_company_comparison(
        ["MSFT", "AAPL", "NVDA"],
        ROOT / "data" / "outputs",
        ROOT / "examples",
    )
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

    assert "Lynch Growth & PEG Comparison" in comparison
    assert "Growth / PEG source validation" in worklist
    assert "EPS CAGR methodology validation" in worklist
    assert "Revenue CAGR methodology validation" in worklist
    assert "FCF CAGR validation" in worklist
    assert "Cycle-adjusted growth validation" in worklist
    assert "growth/PEG provider validation" in dashboard
    assert "EPS growth methodology validation" in dashboard
