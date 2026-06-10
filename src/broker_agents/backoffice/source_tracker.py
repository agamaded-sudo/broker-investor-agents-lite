"""Basic source provenance helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class SourceRecord:
    """Minimal source record for early backoffice provenance tracking."""

    source_id: str
    source_name: str
    source_type: str
    retrieved_at: str
    confidence: float
    freshness: str
    notes: str = ""

    def to_dict(self) -> dict:
        """Return the source record as a plain dictionary."""
        return asdict(self)


def collect_source_log(pack: dict) -> list[dict]:
    """Return the existing source log from the pack when present."""
    if not isinstance(pack, dict):
        return []

    source_section = pack.get("sources_confidence_data_gaps", {})
    if not isinstance(source_section, dict):
        return []

    source_log = source_section.get("source_log", [])
    if not isinstance(source_log, list):
        return []

    return source_log
