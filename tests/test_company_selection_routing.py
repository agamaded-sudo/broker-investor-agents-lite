from __future__ import annotations

from broker_agents.company_selection import (
    ManualCandidateList,
    route_manual_priority_then_list_order,
)


def _manual_candidate_list_payload() -> dict[str, object]:
    return {
        "list_id": "manual_candidates_20260624",
        "as_of_date": "2026-06-24",
        "source_type": "manual_candidate_list",
        "candidates": [
            {
                "company_name": "Apple Inc.",
                "ticker": "AAPL",
                "exchange": "NASDAQ",
                "listing_country": "United States",
                "user_priority": "medium",
                "initial_selection_signals": ["manual_test_candidate"],
            },
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
                "company_name": "NVIDIA Corporation",
                "ticker": "NVDA",
                "exchange": "NASDAQ",
                "listing_country": "United States",
                "user_priority": "high",
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


def test_manual_priority_then_list_order_selects_high_priority_first() -> None:
    manual_list = ManualCandidateList.from_payload(_manual_candidate_list_payload())

    result = route_manual_priority_then_list_order(manual_list)

    assert result.routing_rule == "manual_priority_then_list_order"
    assert result.selected_index == 1
    assert result.selected_record.ticker == "MSFT"
    assert result.selected_record.company_name == "Microsoft Corporation"


def test_manual_priority_then_list_order_uses_list_order_for_ties() -> None:
    payload = _manual_candidate_list_payload()
    candidates = payload["candidates"]
    assert isinstance(candidates, list)

    candidates[0]["user_priority"] = "high"
    candidates[1]["user_priority"] = "high"
    candidates[2]["user_priority"] = "high"

    manual_list = ManualCandidateList.from_payload(payload)

    result = route_manual_priority_then_list_order(manual_list)

    assert result.selected_index == 0
    assert result.selected_record.ticker == "AAPL"


def test_manual_priority_then_list_order_builds_pipeline_payload() -> None:
    manual_list = ManualCandidateList.from_payload(_manual_candidate_list_payload())

    result = route_manual_priority_then_list_order(manual_list)

    pipeline_payload = result.selected_record.pipeline_ready_intake_payload

    assert pipeline_payload == {
        "company_name": "Microsoft Corporation",
        "ticker": "MSFT",
        "exchange": "NASDAQ",
        "listing_country": "United States",
        "as_of_date": "2026-06-24",
        "requested_output": ["package_readiness"],
        "sector": "Information Technology",
        "industry": "Software",
    }


def test_manual_priority_then_list_order_preserves_safety_boundary() -> None:
    manual_list = ManualCandidateList.from_payload(_manual_candidate_list_payload())

    result = route_manual_priority_then_list_order(manual_list)

    safety_boundary = result.selected_record.safety_boundary

    assert safety_boundary["discovery_and_routing_only"] is True
    assert safety_boundary["no_buy_recommendation"] is True
    assert safety_boundary["no_sell_recommendation"] is True
    assert safety_boundary["no_trade_signal"] is True
    assert safety_boundary["no_execution_instruction"] is True
    assert safety_boundary["no_investor_agent_decision"] is True
    assert safety_boundary["no_auto_promotion"] is True


def test_manual_priority_then_list_order_selection_reason_is_non_decisional() -> None:
    manual_list = ManualCandidateList.from_payload(_manual_candidate_list_payload())

    result = route_manual_priority_then_list_order(manual_list)

    reason = result.selected_record.selection_reason.lower()

    assert "pipeline preparation" in reason
    assert "routing priority" in reason
    assert "best investment" not in reason
    assert "buy" not in reason
    assert "upside" not in reason


def test_manual_priority_then_list_order_adds_routing_signals() -> None:
    manual_list = ManualCandidateList.from_payload(_manual_candidate_list_payload())

    result = route_manual_priority_then_list_order(manual_list)

    assert result.selected_record.selection_signals == (
        "manual_priority_high",
        "complete_identity_fields",
        "manual_test_candidate",
        "user_watchlist_match",
    )
