from __future__ import annotations

from broker_agents.company_selection.routing import CandidateRoutingResult
from broker_agents.company_selection.schema import CandidateSelectionRecord


def candidate_selection_record_to_payload(
    record: CandidateSelectionRecord,
) -> dict[str, object]:
    """Serialize one Candidate Selection Record.

    This is a safe handoff payload for one company only.
    It does not add recommendations, rankings, allocations, trade signals,
    execution instructions, investor decisions, or auto-promotion.
    """

    payload: dict[str, object] = {
        "record_id": record.record_id,
        "as_of_date": record.as_of_date,
        "company_name": record.company_name,
        "ticker": record.ticker,
        "exchange": record.exchange,
        "listing_country": record.listing_country,
        "selection_reason": record.selection_reason,
        "selection_signals": list(record.selection_signals),
        "pipeline_ready_intake_payload": dict(record.pipeline_ready_intake_payload),
        "safety_boundary": dict(record.safety_boundary),
    }

    if record.sector:
        payload["sector"] = record.sector
    if record.industry:
        payload["industry"] = record.industry
    if record.source_universe:
        payload["source_universe"] = record.source_universe
    if record.source_references is not None:
        payload["source_references"] = record.source_references
    if record.eligibility_filter_results is not None:
        payload["eligibility_filter_results"] = record.eligibility_filter_results
    if record.attention_filter_results is not None:
        payload["attention_filter_results"] = record.attention_filter_results
    if record.notes:
        payload["notes"] = record.notes
    if record.created_by:
        payload["created_by"] = record.created_by
    if record.created_at:
        payload["created_at"] = record.created_at

    return payload


def routing_result_to_payload(result: CandidateRoutingResult) -> dict[str, object]:
    """Serialize the result of one safe routing operation."""

    return {
        "routing_rule": result.routing_rule,
        "selected_index": result.selected_index,
        "selected_record": candidate_selection_record_to_payload(
            result.selected_record
        ),
        "skipped_candidates": list(result.skipped_candidates),
    }
