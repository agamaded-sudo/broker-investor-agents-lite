"""Tests for broker-facing investor interest mapping."""

import pytest

from broker_agents.deals.investor_interest_response import (
    derive_investor_interest_response,
)


@pytest.mark.parametrize(
    ("final_decision", "candidate_decision", "level", "interest_type"),
    [
        (
            "Buy Gradually",
            "Buy Gradually Candidate",
            "Conditional Interest",
            "Buy Gradually Interest",
        ),
        (
            "Prefer Broad Index",
            "Prefer Broad Index Candidate",
            "Low Interest",
            "Index Preferred",
        ),
        (
            "Follow / Watch",
            "Follow / Watch Candidate",
            "Watchlist Interest",
            "Watchlist",
        ),
        (
            "Wait for Better Price",
            "Wait Candidate",
            "Watchlist Interest",
            "Research Only",
        ),
        (
            "Needs More Evidence",
            "Needs More Evidence Candidate",
            "Needs More Evidence",
            "Needs Evidence",
        ),
    ],
)
def test_interest_mapping(
    final_decision: str,
    candidate_decision: str,
    level: str,
    interest_type: str,
) -> None:
    response = derive_investor_interest_response(
        ticker="TEST",
        investor="Buffett",
        final_decision=final_decision,
        candidate_decision=candidate_decision,
    )

    assert response.interest_level == level
    assert response.interest_type == interest_type
    assert "not a recommendation" in response.safety_note


def test_report_fields_are_extracted_for_broker_response() -> None:
    report = """## Decision Candidate Layer
- Candidate Confidence: Medium
- Positive Drivers:
  - Strong cash generation.
- Negative Drivers:
  - Valuation is demanding.

## Promotion Eligibility
- Required Evidence:
  - Validate normalized owner earnings.
"""
    response = derive_investor_interest_response(
        ticker="TEST",
        investor="Buffett",
        final_decision="Wait",
        candidate_decision="Wait Candidate",
        report_text=report,
    )

    assert response.confidence == "Medium"
    assert response.main_positive_reason == "Strong cash generation."
    assert response.main_concern == "Valuation is demanding."
    assert (
        response.required_evidence_before_serious_interest
        == "Validate normalized owner earnings."
    )
