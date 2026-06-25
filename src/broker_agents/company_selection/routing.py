from __future__ import annotations

from dataclasses import dataclass

from broker_agents.company_selection.schema import (
    CandidateSelectionError,
    CandidateSelectionRecord,
    ManualCandidate,
    ManualCandidateList,
)


_PRIORITY_ORDER = {
    "high": 0,
    "medium": 1,
    "low": 2,
    None: 3,
}


@dataclass(frozen=True)
class CandidateRoutingResult:
    """Result of routing one candidate into a Candidate Selection Record."""

    selected_record: CandidateSelectionRecord
    routing_rule: str
    selected_index: int
    skipped_candidates: tuple[dict[str, str], ...] = ()


def _candidate_sort_key(indexed_candidate: tuple[int, ManualCandidate]) -> tuple[int, int]:
    index, candidate = indexed_candidate
    return (_PRIORITY_ORDER.get(candidate.user_priority, 3), index)


def _priority_signal(candidate: ManualCandidate) -> str:
    if candidate.user_priority in {"high", "medium", "low"}:
        return f"manual_priority_{candidate.user_priority}"
    return "manual_priority_unspecified"


def _record_id_for(candidate: ManualCandidate, *, as_of_date: str) -> str:
    normalized_ticker = candidate.ticker.lower().replace(".", "_").replace("-", "_")
    normalized_date = as_of_date.replace("-", "")
    return f"candidate_{normalized_ticker}_{normalized_date}"


def _selection_reason_for(candidate: ManualCandidate) -> str:
    priority_text = candidate.user_priority or "unspecified"
    return (
        "Selected for Pipeline preparation by manual_priority_then_list_order "
        f"because it had {priority_text} routing priority and complete identity fields."
    )


def _selection_signals_for(candidate: ManualCandidate) -> tuple[str, ...]:
    signals = [
        _priority_signal(candidate),
        "complete_identity_fields",
    ]

    for signal in candidate.initial_selection_signals:
        if signal not in signals:
            signals.append(signal)

    return tuple(signals)


def _pipeline_payload_for(
    candidate: ManualCandidate,
    *,
    as_of_date: str,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "company_name": candidate.company_name,
        "ticker": candidate.ticker,
        "exchange": candidate.exchange,
        "listing_country": candidate.listing_country,
        "as_of_date": as_of_date,
        "requested_output": ["package_readiness"],
    }

    if candidate.sector:
        payload["sector"] = candidate.sector
    if candidate.industry:
        payload["industry"] = candidate.industry
    if candidate.source_references is not None:
        payload["source_references"] = candidate.source_references

    return payload


def _record_payload_for(
    candidate: ManualCandidate,
    *,
    as_of_date: str,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "record_id": _record_id_for(candidate, as_of_date=as_of_date),
        "as_of_date": as_of_date,
        "company_name": candidate.company_name,
        "ticker": candidate.ticker,
        "exchange": candidate.exchange,
        "listing_country": candidate.listing_country,
        "selection_reason": _selection_reason_for(candidate),
        "selection_signals": list(_selection_signals_for(candidate)),
        "pipeline_ready_intake_payload": _pipeline_payload_for(
            candidate,
            as_of_date=as_of_date,
        ),
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

    if candidate.sector:
        payload["sector"] = candidate.sector
    if candidate.industry:
        payload["industry"] = candidate.industry
    if candidate.source_universe:
        payload["source_universe"] = candidate.source_universe
    if candidate.source_references is not None:
        payload["source_references"] = candidate.source_references
    if candidate.initial_eligibility_assumptions is not None:
        payload["eligibility_filter_results"] = candidate.initial_eligibility_assumptions

    return payload


def route_manual_priority_then_list_order(
    manual_candidate_list: ManualCandidateList,
) -> CandidateRoutingResult:
    """Route one candidate by manual priority and list order.

    This is routing only. It does not rank investment attractiveness,
    recommend securities, run investor agents, or aggregate reports.
    """

    if not manual_candidate_list.candidates:
        raise CandidateSelectionError(
            "manual candidate list must contain at least one candidate."
        )

    indexed_candidates = tuple(enumerate(manual_candidate_list.candidates))
    selected_index, selected_candidate = min(
        indexed_candidates,
        key=_candidate_sort_key,
    )

    selected_record = CandidateSelectionRecord.from_payload(
        _record_payload_for(
            selected_candidate,
            as_of_date=manual_candidate_list.as_of_date,
        )
    )

    return CandidateRoutingResult(
        selected_record=selected_record,
        routing_rule="manual_priority_then_list_order",
        selected_index=selected_index,
    )
