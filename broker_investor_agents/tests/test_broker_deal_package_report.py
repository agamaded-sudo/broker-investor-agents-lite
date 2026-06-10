"""Tests for broker deal package rendering."""

from pathlib import Path

from broker_agents.deals.investor_interest_response import (
    derive_investor_interest_response,
)
from broker_agents.deals.deal_executive_summary import (
    build_broker_deal_executive_summary,
)
from broker_agents.reports.broker_deal_package_report import (
    generate_broker_deal_package_report,
)


def test_broker_deal_package_contains_required_sections() -> None:
    responses = [
        derive_investor_interest_response(
            ticker="MSFT",
            investor=investor,
            final_decision=decision,
            candidate_decision=candidate,
        )
        for investor, decision, candidate in (
            ("Buffett", "Wait for Better Price", "Wait Candidate"),
            ("Munger", "Buy Gradually", "Buy Gradually Candidate"),
            ("Fisher", "Needs More Evidence", "Needs More Evidence Candidate"),
            ("Lynch", "Follow / Watch", "Follow / Watch Candidate"),
            ("Bogle", "Prefer Broad Index", "Index Preferred Candidate"),
        )
    ]

    report = generate_broker_deal_package_report(
        ticker="MSFT",
        company_name="Microsoft Corporation",
        enriched_pack_path=Path("msft_deal_enriched_input.yaml"),
        investor_responses=responses,
        source_verification_status="partially verified (mixed)",
        applied_enrichment_sources=["official_financials", "market_data"],
        skipped_enrichment_sources=[],
        warnings=[],
        executive_summary=build_broker_deal_executive_summary(
            ticker="MSFT",
            company_name="Microsoft Corporation",
            investor_responses=responses,
            source_verification_status="partially verified (mixed)",
            applied_enrichment_sources=["official_financials", "market_data"],
            skipped_enrichment_sources=[],
            warnings=[],
        ),
        investor_response_letter_paths={
            response.investor: Path(
                f"letters/msft_{response.investor.lower()}_response_letter.md"
            )
            for response in responses
        },
    )

    for heading in (
        "Broker Deal Package",
        "Executive Summary for Broker",
        "Key Positive Themes",
        "Main Blockers",
        "Backoffice Next Actions",
        "Backoffice Preparation Summary",
        "Independent Investor Responses",
        "Investor Response Letters",
        "Investor Response Details",
        "Broker Interpretation",
        "Next Backoffice Actions",
        "Safety Check",
    ):
        assert heading in report
    assert "not a recommendation" in report
    assert "No ranking" in report
    assert "No consensus" in report
    assert "No portfolio allocation" in report
    assert "No trade signal" in report
    assert "Final investor decisions unchanged" in report
    assert "Auto-promotion disabled" in report
    assert "should not treat these letters as a vote, ranking, or consensus" in report
