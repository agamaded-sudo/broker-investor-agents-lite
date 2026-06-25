from __future__ import annotations

import pytest

from broker_agents.company_selection import (
    CandidateSelectionError,
    CandidateSelectionRecord,
    ManualCandidateList,
)


def _manual_candidate_list_payload() -> dict[str, object]:
    return {
        "list_id": "manual_candidates_20260624",
        "as_of_date": "2026-06-24",
        "source_type": "manual_candidate_list",
        "description": "Small manually supplied list.",
        "candidates": [
            {
                "company_name": "Microsoft Corporation",
                "ticker": "MSFT",
                "exchange": "NASDAQ",
                "listing_country": "United States",
                "sector": "Information Technology",
                "industry": "Software",
                "source_universe": "Manual Watchlist",
                "user_priority": "high",
                "initial_selection_signals": [
                    "manual_test_candidate",
                    "user_watchlist_match",
                ],
                "initial_eligibility_assumptions": {
                    "listed_on_organized_market": True,
                    "official_financials_expected_available": True,
                    "operating_revenue_expected_visible": True,
                },
            },
            {
                "company_name": "Apple Inc.",
                "ticker": "AAPL",
                "exchange": "NASDAQ",
                "listing_country": "United States",
                "user_priority": "medium",
            },
        ],
        "safety_boundary": {
            "manual_discovery_input_only": True,
            "no_buy_recommendation": True,
            "no_sell_recommendation": True,
            "no_investment_ranking": True,
            "no_allocation": True,
            "no_portfolio_weight": True,
            "no_trade_signal": True,
            "no_execution_instruction": True,
            "no_investor_agent_decision": True,
            "no_auto_promotion": True,
        },
    }


def _candidate_selection_record_payload() -> dict[str, object]:
    return {
        "record_id": "candidate_msft_20260624",
        "as_of_date": "2026-06-24",
        "company_name": "Microsoft Corporation",
        "ticker": "MSFT",
        "exchange": "NASDAQ",
        "listing_country": "United States",
        "sector": "Information Technology",
        "industry": "Software",
        "source_universe": "Manual Watchlist",
        "selection_reason": (
            "Selected for Pipeline preparation by "
            "manual_priority_then_list_order."
        ),
        "selection_signals": [
            "manual_priority_high",
            "complete_identity_fields",
        ],
        "eligibility_filter_results": {
            "listed_on_organized_market": True,
            "official_financials_available": True,
            "real_operating_revenue_visible": True,
        },
        "pipeline_ready_intake_payload": {
            "company_name": "Microsoft Corporation",
            "ticker": "MSFT",
            "exchange": "NASDAQ",
            "listing_country": "United States",
            "as_of_date": "2026-06-24",
            "requested_output": ["package_readiness"],
        },
        "safety_boundary": {
            "discovery_and_routing_only": True,
            "no_buy_recommendation": True,
            "no_sell_recommendation": True,
            "no_ranking": True,
            "no_allocation": True,
            "no_trade_signal": True,
            "no_execution_instruction": True,
            "no_investor_agent_decision": True,
            "no_auto_promotion": True,
        },
    }


def test_manual_candidate_list_accepts_safe_payload() -> None:
    manual_list = ManualCandidateList.from_payload(
        _manual_candidate_list_payload()
    )

    assert manual_list.list_id == "manual_candidates_20260624"
    assert manual_list.as_of_date == "2026-06-24"
    assert manual_list.source_type == "manual_candidate_list"
    assert len(manual_list.candidates) == 2
    assert manual_list.candidates[0].ticker == "MSFT"
    assert manual_list.candidates[0].user_priority == "high"


def test_manual_candidate_list_rejects_forbidden_decision_field() -> None:
    payload = _manual_candidate_list_payload()
    candidates = payload["candidates"]
    assert isinstance(candidates, list)
    candidates[0]["target_price"] = 500

    with pytest.raises(CandidateSelectionError, match="Forbidden decision field"):
        ManualCandidateList.from_payload(payload)


def test_manual_candidate_list_rejects_missing_candidate_identity() -> None:
    payload = _manual_candidate_list_payload()
    candidates = payload["candidates"]
    assert isinstance(candidates, list)
    del candidates[0]["company_name"]

    with pytest.raises(CandidateSelectionError, match="company_name"):
        ManualCandidateList.from_payload(payload)


def test_candidate_selection_record_accepts_safe_payload() -> None:
    record = CandidateSelectionRecord.from_payload(
        _candidate_selection_record_payload()
    )

    assert record.record_id == "candidate_msft_20260624"
    assert record.company_name == "Microsoft Corporation"
    assert record.ticker == "MSFT"
    assert record.pipeline_ready_intake_payload["requested_output"] == [
        "package_readiness"
    ]


def test_candidate_selection_record_rejects_multi_company_pipeline_payload() -> None:
    payload = _candidate_selection_record_payload()
    pipeline_payload = payload["pipeline_ready_intake_payload"]
    assert isinstance(pipeline_payload, dict)
    pipeline_payload["candidates"] = []

    with pytest.raises(CandidateSelectionError, match="single-company"):
        CandidateSelectionRecord.from_payload(payload)


def test_candidate_selection_record_rejects_non_preparation_output() -> None:
    payload = _candidate_selection_record_payload()
    pipeline_payload = payload["pipeline_ready_intake_payload"]
    assert isinstance(pipeline_payload, dict)
    pipeline_payload["requested_output"] = ["package_readiness", "recommendation"]

    with pytest.raises(CandidateSelectionError, match="preparation-only"):
        CandidateSelectionRecord.from_payload(payload)


def test_candidate_selection_record_requires_matching_pipeline_identity() -> None:
    payload = _candidate_selection_record_payload()
    pipeline_payload = payload["pipeline_ready_intake_payload"]
    assert isinstance(pipeline_payload, dict)
    pipeline_payload["ticker"] = "AAPL"

    with pytest.raises(CandidateSelectionError, match="identity must match"):
        CandidateSelectionRecord.from_payload(payload)
