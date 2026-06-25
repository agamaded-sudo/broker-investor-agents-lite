from __future__ import annotations

from broker_agents.company_selection import (
    CandidateSelectionRecord,
    ManualCandidateList,
    candidate_selection_record_to_payload,
    route_manual_priority_then_list_order,
    routing_result_to_payload,
)


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
                "initial_selection_signals": ["manual_test_candidate"],
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


def test_candidate_selection_record_to_payload_round_trips() -> None:
    record = CandidateSelectionRecord.from_payload(
        _candidate_selection_record_payload()
    )

    payload = candidate_selection_record_to_payload(record)

    round_tripped = CandidateSelectionRecord.from_payload(payload)

    assert round_tripped == record


def test_candidate_selection_record_to_payload_preserves_single_company_payload() -> None:
    record = CandidateSelectionRecord.from_payload(
        _candidate_selection_record_payload()
    )

    payload = candidate_selection_record_to_payload(record)

    pipeline_payload = payload["pipeline_ready_intake_payload"]
    assert isinstance(pipeline_payload, dict)
    assert pipeline_payload["ticker"] == "MSFT"
    assert pipeline_payload["requested_output"] == ["package_readiness"]
    assert "candidates" not in pipeline_payload
    assert "companies" not in pipeline_payload
    assert "universe" not in pipeline_payload


def test_candidate_selection_record_to_payload_preserves_safety_boundary() -> None:
    record = CandidateSelectionRecord.from_payload(
        _candidate_selection_record_payload()
    )

    payload = candidate_selection_record_to_payload(record)

    safety_boundary = payload["safety_boundary"]
    assert isinstance(safety_boundary, dict)
    assert safety_boundary["discovery_and_routing_only"] is True
    assert safety_boundary["no_buy_recommendation"] is True
    assert safety_boundary["no_sell_recommendation"] is True
    assert safety_boundary["no_trade_signal"] is True
    assert safety_boundary["no_execution_instruction"] is True


def test_routing_result_to_payload_serializes_selected_record() -> None:
    manual_list = ManualCandidateList.from_payload(_manual_candidate_list_payload())
    result = route_manual_priority_then_list_order(manual_list)

    payload = routing_result_to_payload(result)

    assert payload["routing_rule"] == "manual_priority_then_list_order"
    assert payload["selected_index"] == 1

    selected_record = payload["selected_record"]
    assert isinstance(selected_record, dict)
    assert selected_record["ticker"] == "MSFT"
    assert selected_record["selection_signals"] == [
        "manual_priority_high",
        "complete_identity_fields",
        "manual_test_candidate",
    ]


def test_routing_result_to_payload_does_not_add_decision_fields() -> None:
    manual_list = ManualCandidateList.from_payload(_manual_candidate_list_payload())
    result = route_manual_priority_then_list_order(manual_list)

    payload = routing_result_to_payload(result)
    selected_record = payload["selected_record"]
    assert isinstance(selected_record, dict)

    forbidden_fields = {
        "recommendation",
        "buy_recommendation",
        "sell_recommendation",
        "rating",
        "rank",
        "target_price",
        "allocation",
        "portfolio_weight",
        "trade_signal",
        "execution_instruction",
        "investor_decision",
        "auto_promotion",
    }

    assert forbidden_fields.isdisjoint(selected_record)
