"""Safe Company Selection Agent primitives.

This package is discovery and routing only.
It does not scan live markets, produce recommendations, run investor agents,
or aggregate reports.
"""

from broker_agents.company_selection.schema import (
    CandidateSelectionError,
    CandidateSelectionRecord,
    ManualCandidate,
    ManualCandidateList,
)

__all__ = [
    "CandidateSelectionError",
    "CandidateSelectionRecord",
    "ManualCandidate",
    "ManualCandidateList",
]
