"""Tests for deterministic source verification and reporting."""

from pathlib import Path

import yaml

from broker_agents.agents.bogle_agent import BogleAgent
from broker_agents.agents.buffett_agent import BuffettAgent
from broker_agents.agents.fisher_agent import FisherAgent
from broker_agents.agents.lynch_agent import LynchAgent
from broker_agents.agents.munger_agent import MungerAgent
from broker_agents.backoffice.source_verification import verify_sources
from broker_agents.calculators.promotion_eligibility import (
    evaluate_promotion_eligibility,
)
from broker_agents.reports.backoffice_missing_evidence_report import (
    generate_backoffice_missing_evidence_report,
)
from broker_agents.reports.investor_agent_readiness_dashboard import (
    generate_investor_agent_readiness_dashboard,
)
from broker_agents.reports.source_verification_report import (
    generate_source_verification_report,
)

ROOT = Path(__file__).resolve().parents[1]


def load_pack(ticker: str) -> dict:
    """Load one manual example pack."""
    path = ROOT / "examples" / f"{ticker.lower()}_input.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def section_quality(result: dict, section: str) -> str:
    """Return one section quality label."""
    return next(
        item["section_quality_label"]
        for item in result["source_quality_by_section"]
        if item["section_name"] == section
    )


def test_source_verification_classifies_manual_pack_quality() -> None:
    for ticker in ("MSFT", "AAPL", "NVDA"):
        result = verify_sources(load_pack(ticker))

        assert result["overall_source_quality"]
        assert result["source_verification_status"]
        assert section_quality(result, "historical_valuation") == "placeholder-heavy"
        assert section_quality(result, "scuttlebutt") == "weak"
        assert result["placeholder_fields_count"] > 0
        assert result["calculated_fields_count"] > 0


def test_source_verification_report_contains_required_sections() -> None:
    report = generate_source_verification_report(
        ["MSFT", "AAPL", "NVDA"],
        ROOT / "examples",
    )

    assert "Source Verification Report" in report
    assert "MSFT" in report
    assert "AAPL" in report
    assert "NVDA" in report
    assert "Source Quality by Section" in report
    assert "Critical Source Gaps" in report
    assert "Placeholder Fields" in report
    assert "Recommended Backoffice Actions" in report


def test_source_dependencies_are_visible_in_aggregate_reports() -> None:
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

    assert "Source Verification Dependencies" in worklist
    assert "valuation history placeholders" in worklist.lower()
    assert "market data placeholders" in worklist.lower()
    assert "Source Quality Dependencies by Agent" in dashboard
    assert "source quality" in dashboard.lower()
    assert "benchmark and index source quality" in dashboard.lower()


def test_source_framework_does_not_change_decisions_or_auto_promote() -> None:
    pack = load_pack("MSFT")
    agent_specs = {
        "buffett": (
            BuffettAgent,
            "buffett_method.yaml",
            "Wait for Better Price / Complete Intrinsic Value Work",
        ),
        "munger": (
            MungerAgent,
            "munger_method.yaml",
            "Buy Gradually / Wait for Better Evidence on AI Capex Returns",
        ),
        "fisher": (
            FisherAgent,
            "fisher_method.yaml",
            "Needs More Scuttlebutt / Watch Closely",
        ),
        "lynch": (LynchAgent, "lynch_method.yaml", "Follow / Watch"),
        "bogle": (BogleAgent, "bogle_method.yaml", "Prefer Broad Index"),
    }

    for investor, (agent_class, method_file, decision) in agent_specs.items():
        report = agent_class(pack, ROOT / "methods" / method_file).generate_report()
        eligibility = evaluate_promotion_eligibility(pack, investor)

        assert f"## Decision\n{decision}" in report
        assert eligibility["auto_promotion_allowed"] is False
