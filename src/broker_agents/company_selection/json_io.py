from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from broker_agents.company_selection.routing import CandidateRoutingResult
from broker_agents.company_selection.schema import (
    CandidateSelectionError,
    CandidateSelectionRecord,
    ManualCandidateList,
)
from broker_agents.company_selection.serialization import (
    candidate_selection_record_to_payload,
    routing_result_to_payload,
)


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise CandidateSelectionError(f"Invalid JSON file: {path}") from exc

    if not isinstance(payload, dict):
        raise CandidateSelectionError(f"JSON file must contain an object: {path}")

    return payload


def _write_json_object(payload: dict[str, object], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def read_manual_candidate_list_json(path: Path) -> ManualCandidateList:
    """Read one manual candidate list JSON file.

    The list may contain many candidates, but it is discovery input only.
    It must not be passed directly into the Single-Company Pipeline.
    """

    return ManualCandidateList.from_payload(_read_json_object(path))


def read_candidate_selection_record_json(path: Path) -> CandidateSelectionRecord:
    """Read one Candidate Selection Record JSON file."""

    return CandidateSelectionRecord.from_payload(_read_json_object(path))


def write_candidate_selection_record_json(
    record: CandidateSelectionRecord,
    path: Path,
) -> Path:
    """Write one Candidate Selection Record as JSON."""

    return _write_json_object(candidate_selection_record_to_payload(record), path)


def write_routing_result_json(
    result: CandidateRoutingResult,
    path: Path,
) -> Path:
    """Write one safe routing result as JSON."""

    return _write_json_object(routing_result_to_payload(result), path)
