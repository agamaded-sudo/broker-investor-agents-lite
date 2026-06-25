from __future__ import annotations

import json
from pathlib import Path

import pytest

from broker_agents.company_selection import (
    CandidateSelectionError,
    CandidateSelectionRecord,
    ManualCandidateList,
    read_candidate_selection_record_json,
    read_manual_candidate_list_json,
    route_manual_priority_then_list_order,
    write_candidate_selection_record_json,
    write_routing_result_json,
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


def _candidate_selection_record_payload() -> dict[str, object]:
    return {
        "record_id": "candidate_msft_20260624",
        "as_of_date": "2026-06-24",
        "company_name": "Microsoft Corporation",
        "ticker": "MSFT",
        "exchange": "NASDAQ",
        "listing_country": "United States",
        "selection_reason": (
            "Selected for Pipeline preparation by "
            "manual_priority_then_list_order."
        ),
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


def _write_payload(path: Path, payload: dict[str, object], *, bom: bool = False) -> None:
    encoding = "utf-8-sig" if bom else "utf-8"
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding=encoding,
    )


def test_read_manual_candidate_list_json_accepts_safe_payload(tmp_path: Path) -> None:
    path = tmp_path / "manual_candidates.json"
    _write_payload(path, _manual_candidate_list_payload())

    manual_list = read_manual_candidate_list_json(path)

    assert isinstance(manual_list, ManualCandidateList)
    assert manual_list.list_id == "manual_candidates_20260624"
    assert len(manual_list.candidates) == 2
    assert manual_list.candidates[1].ticker == "MSFT"


def test_read_manual_candidate_list_json_accepts_utf8_bom(tmp_path: Path) -> None:
    path = tmp_path / "manual_candidates_bom.json"
    _write_payload(path, _manual_candidate_list_payload(), bom=True)

    manual_list = read_manual_candidate_list_json(path)

    assert manual_list.list_id == "manual_candidates_20260624"


def test_read_manual_candidate_list_json_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not-json", encoding="utf-8")

    with pytest.raises(CandidateSelectionError, match="Invalid JSON"):
        read_manual_candidate_list_json(path)


def test_write_candidate_selection_record_json_round_trips(tmp_path: Path) -> None:
    record = CandidateSelectionRecord.from_payload(
        _candidate_selection_record_payload()
    )
    path = tmp_path / "candidate_msft.json"

    write_candidate_selection_record_json(record, path)

    round_tripped = read_candidate_selection_record_json(path)

    assert round_tripped == record


def test_write_routing_result_json_writes_selected_record(tmp_path: Path) -> None:
    manual_list = ManualCandidateList.from_payload(_manual_candidate_list_payload())
    result = route_manual_priority_then_list_order(manual_list)
    path = tmp_path / "routing_result.json"

    write_routing_result_json(result, path)

    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["routing_rule"] == "manual_priority_then_list_order"
    assert payload["selected_index"] == 1
    assert payload["selected_record"]["ticker"] == "MSFT"
    assert payload["selected_record"]["pipeline_ready_intake_payload"][
        "requested_output"
    ] == ["package_readiness"]
