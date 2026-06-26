from __future__ import annotations

from pathlib import Path

from broker_agents.company_selection.json_io import (
    read_manual_candidate_list_json,
    write_routing_result_json,
)
from broker_agents.company_selection.routing import (
    CandidateRoutingResult,
    route_manual_priority_then_list_order,
)


def select_candidate_from_manual_list_json(
    *,
    input_path: Path,
    output_path: Path,
) -> CandidateRoutingResult:
    """Run the minimal safe Company Selection Agent workflow.

    This library workflow:
    - reads one manual candidate list JSON file
    - routes one candidate by manual_priority_then_list_order
    - writes one routing result JSON artifact

    It does not scan live markets, rank investments, recommend securities,
    run investor agents, aggregate reports, or send batches into the Pipeline.
    """

    manual_candidate_list = read_manual_candidate_list_json(input_path)
    routing_result = route_manual_priority_then_list_order(manual_candidate_list)
    write_routing_result_json(routing_result, output_path)
    return routing_result
