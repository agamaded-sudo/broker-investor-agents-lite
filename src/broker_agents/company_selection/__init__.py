"""Safe Company Selection Agent primitives.

This package is discovery and routing only.
It does not scan live markets, produce recommendations, run investor agents,
or aggregate reports.
"""

from broker_agents.company_selection.json_io import (
    read_candidate_selection_record_json,
    read_manual_candidate_list_json,
    write_candidate_selection_record_json,
    write_routing_result_json,
)
from broker_agents.company_selection.routing import (
    CandidateRoutingResult,
    route_manual_priority_then_list_order,
)
from broker_agents.company_selection.schema import (
    CandidateSelectionError,
    CandidateSelectionRecord,
    ManualCandidate,
    ManualCandidateList,
)
from broker_agents.company_selection.serialization import (
    candidate_selection_record_to_payload,
    routing_result_to_payload,
)

__all__ = [
    "CandidateRoutingResult",
    "CandidateSelectionError",
    "CandidateSelectionRecord",
    "ManualCandidate",
    "ManualCandidateList",
    "candidate_selection_record_to_payload",
    "read_candidate_selection_record_json",
    "read_manual_candidate_list_json",
    "route_manual_priority_then_list_order",
    "routing_result_to_payload",
    "write_candidate_selection_record_json",
    "write_routing_result_json",
]
