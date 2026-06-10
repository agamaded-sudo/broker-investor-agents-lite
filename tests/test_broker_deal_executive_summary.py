"""Tests for the broker deal executive summary."""

from pathlib import Path

from broker_agents.deals.deal_executive_summary import (
    build_broker_deal_executive_summary,
)
from broker_agents.deals.investor_interest_response import (
    derive_investor_interest_response,
)
from broker_agents.reports.broker_deal_package_report import (
    generate_broker_deal_package_report,
)


def _responses():
    """Build representative independent broker responses."""
    return [
        derive_investor_interest_response(
            "MSFT",
            investor,
            final_decision,
            candidate_decision,
        )
        for investor, final_decision, candidate_decision in (
            ("Buffett", "Wait for Better Price", "Wait Candidate"),
            ("Munger", "Buy Gradually", "Buy Gradually Candidate"),
            ("Fisher", "Needs More Evidence", "Needs More Evidence Candidate"),
            ("Lynch", "Follow / Watch", "Follow / Watch Candidate"),
            ("Bogle", "Prefer Broad Index", "Index Preferred Candidate"),
        )
    ]


def test_executive_summary_groups_interest_and_actions() -> None:
    summary = build_broker_deal_executive_summary(
        ticker="MSFT",
        company_name="Microsoft Corporation",
        investor_responses=_responses(),
        source_verification_status="partially verified (mixed)",
        applied_enrichment_sources=[
            "official_financials",
            "market_data",
            "historical_valuation",
            "growth_peg",
        ],
        skipped_enrichment_sources=[],
        warnings=[],
    )

    assert summary.backoffice_readiness_label == "Ready for Investor Review"
    assert summary.conditional_interest_investors == ["Munger"]
    assert summary.watchlist_interest_investors == ["Buffett", "Lynch"]
    assert summary.needs_evidence_investors == ["Fisher"]
    assert summary.low_interest_investors == ["Bogle"]
    assert summary.index_preferred_investors == ["Bogle"]
    assert summary.pass_investors == []
    assert "Collect Fisher-style scuttlebutt evidence." in summary.backoffice_next_actions
    assert any("management incentives" in action for action in summary.backoffice_next_actions)
    assert any("normalized owner earnings" in action for action in summary.backoffice_next_actions)
    assert any("index overlap" in action for action in summary.backoffice_next_actions)
    assert {
        "no_recommendation",
        "no_ranking",
        "no_consensus",
        "no_allocation",
        "no_trade_signal",
        "final_decisions_unchanged",
        "auto_promotion_disabled",
    }.issubset(summary.safety_flags)


def test_executive_summary_is_rendered_near_top_of_package() -> None:
    responses = _responses()
    summary = build_broker_deal_executive_summary(
        ticker="MSFT",
        company_name="Microsoft Corporation",
        investor_responses=responses,
        source_verification_status="partially verified (mixed)",
        applied_enrichment_sources=["official_financials"],
        skipped_enrichment_sources=[],
        warnings=[],
    )
    report = generate_broker_deal_package_report(
        ticker="MSFT",
        company_name="Microsoft Corporation",
        enriched_pack_path=Path("msft_deal_enriched_input.yaml"),
        investor_responses=responses,
        source_verification_status="partially verified (mixed)",
        applied_enrichment_sources=["official_financials"],
        skipped_enrichment_sources=[],
        warnings=[],
        executive_summary=summary,
    )

    assert "Executive Summary for Broker" in report
    assert "Key Positive Themes" in report
    assert "Main Blockers" in report
    assert "Backoffice Next Actions" in report
    assert report.index("Executive Summary for Broker") < report.index("Deal Context")
    assert "not a recommendation, ranking, vote, average score, consensus" in report
    assert "No portfolio allocation" in report
    assert "No trade signal" in report
