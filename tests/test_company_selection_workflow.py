from __future__ import annotations

import json
from pathlib import Path

from broker_agents.company_selection import (
    select_candidate_from_manual_list_json,
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


def test_select_candidate_from_manual_list_json_writes_routing_artifact(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "manual_candidates.json"
    output_path = tmp_path / "routing_result.json"
    input_path.write_text(
        json.dumps(_manual_candidate_list_payload(), indent=2),
        encoding="utf-8",
    )

    result = select_candidate_from_manual_list_json(
        input_path=input_path,
        output_path=output_path,
    )

    assert result.routing_rule == "manual_priority_then_list_order"
    assert result.selected_index == 1
    assert result.selected_record.ticker == "MSFT"
    assert output_path.exists()


def test_select_candidate_from_manual_list_json_output_is_single_company(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "manual_candidates.json"
    output_path = tmp_path / "routing_result.json"
    input_path.write_text(
        json.dumps(_manual_candidate_list_payload(), indent=2),
        encoding="utf-8",
    )

    select_candidate_from_manual_list_json(
        input_path=input_path,
        output_path=output_path,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    selected_record = payload["selected_record"]
    pipeline_payload = selected_record["pipeline_ready_intake_payload"]

    assert selected_record["ticker"] == "MSFT"
    assert pipeline_payload["ticker"] == "MSFT"
    assert pipeline_payload["requested_output"] == ["package_readiness"]
    assert "candidates" not in pipeline_payload
    assert "companies" not in pipeline_payload
    assert "universe" not in pipeline_payload


def test_select_candidate_from_manual_list_json_preserves_safety_boundary(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "manual_candidates.json"
    output_path = tmp_path / "routing_result.json"
    input_path.write_text(
        json.dumps(_manual_candidate_list_payload(), indent=2),
        encoding="utf-8",
    )

    select_candidate_from_manual_list_json(
        input_path=input_path,
        output_path=output_path,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    safety_boundary = payload["selected_record"]["safety_boundary"]

    assert safety_boundary["discovery_and_routing_only"] is True
    assert safety_boundary["no_buy_recommendation"] is True
    assert safety_boundary["no_sell_recommendation"] is True
    assert safety_boundary["no_trade_signal"] is True
    assert safety_boundary["no_execution_instruction"] is True
    assert safety_boundary["no_investor_agent_decision"] is True
    assert safety_boundary["no_auto_promotion"] is True


def test_select_candidate_from_manual_list_json_does_not_add_decision_fields(
    tmp_path: Path,
) -> None:
    input_path = tmp_path / "manual_candidates.json"
    output_path = tmp_path / "routing_result.json"
    input_path.write_text(
        json.dumps(_manual_candidate_list_payload(), indent=2),
        encoding="utf-8",
    )

    select_candidate_from_manual_list_json(
        input_path=input_path,
        output_path=output_path,
    )

    payload = json.loads(output_path.read_text(encoding="utf-8"))
    selected_record = payload["selected_record"]

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
