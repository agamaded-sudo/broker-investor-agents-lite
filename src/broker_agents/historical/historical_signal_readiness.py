"""Readiness-only candidate records for future historical signal research."""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path

from broker_agents.historical.historical_enriched_input import (
    HistoricalEnrichedInputAssembly,
)


@dataclass(frozen=True)
class HistoricalSignalReadinessCandidate:
    """Non-actionable record describing historical signal readiness."""

    ticker: str
    as_of_date: str
    run_id: str
    historical_mode: bool
    historical_signal_candidate: bool
    signal_generation_status: str
    safe_for_historical_signal_generation: bool
    not_trade_signal: bool
    not_recommendation: bool
    not_allocation_instruction: bool
    input_assembly_file: str
    assembly_status: str
    readiness_labels: list[str] = field(default_factory=list)
    partial_sections: list[str] = field(default_factory=list)
    readiness_only_sections: list[str] = field(default_factory=list)
    leakage_risk_sections: list[str] = field(default_factory=list)
    blocking_reasons: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_required_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize the readiness candidate."""
        return asdict(self)


def build_historical_signal_readiness_candidate(
    assembly: HistoricalEnrichedInputAssembly,
    *,
    input_assembly_file: Path | str,
) -> HistoricalSignalReadinessCandidate:
    """Build a non-actionable readiness candidate from one assembly."""
    blocking_reasons = [
        f"{section} remains readiness_only."
        for section in assembly.readiness_only_sections
    ]
    blocking_reasons.extend(
        f"{section} is unsupported."
        for section in assembly.unsupported_sections
    )
    if not assembly.safe_for_historical_signal_generation:
        blocking_reasons.append(
            "Historical enriched input assembly is not safe for full "
            "historical signal generation."
        )
    if "investor_outputs" in assembly.readiness_only_sections:
        blocking_reasons.append(
            "Investor outputs are not yet generated from fully historical "
            "inputs."
        )
    readiness_labels = ["research_candidate_only"]
    if assembly.partial_sections:
        readiness_labels.append("partial_historical_input_available")
    if blocking_reasons:
        readiness_labels.append("insufficient_point_in_time_coverage")
    warnings = list(assembly.warnings)
    warnings.append(
        "This candidate records readiness only and must not be treated as an "
        "investor decision or market action."
    )
    return HistoricalSignalReadinessCandidate(
        ticker=assembly.ticker,
        as_of_date=assembly.as_of_date,
        run_id=assembly.run_id,
        historical_mode=True,
        historical_signal_candidate=True,
        signal_generation_status="readiness_only",
        safe_for_historical_signal_generation=False,
        not_trade_signal=True,
        not_recommendation=True,
        not_allocation_instruction=True,
        input_assembly_file=str(input_assembly_file),
        assembly_status=assembly.assembly_status,
        readiness_labels=readiness_labels,
        partial_sections=list(assembly.partial_sections),
        readiness_only_sections=list(assembly.readiness_only_sections),
        leakage_risk_sections=list(assembly.leakage_risk_sections),
        blocking_reasons=blocking_reasons,
        warnings=warnings,
        next_required_steps=list(assembly.next_required_steps),
    )


def render_historical_signal_readiness_candidate(
    candidate: HistoricalSignalReadinessCandidate,
) -> str:
    """Render a human-readable readiness-only candidate."""
    return "\n".join(
        [
            "# Historical Signal Readiness Candidate",
            "",
            "## Overview",
            "",
            f"- Ticker: {candidate.ticker}",
            f"- As-Of Date: {candidate.as_of_date}",
            f"- Run ID: {candidate.run_id}",
            "",
            "## Status",
            "",
            (
                "- Signal generation status: "
                f"{candidate.signal_generation_status}"
            ),
            "- Safe for historical signal generation: No",
            "- Historical signal candidate: Yes",
            "",
            "## Input Assembly",
            "",
            f"- Assembly File: {candidate.input_assembly_file}",
            f"- Assembly Status: {candidate.assembly_status}",
            (
                "- Readiness Labels: "
                f"{', '.join(candidate.readiness_labels)}"
            ),
            "",
            "## Partial Sections",
            "",
            ", ".join(candidate.partial_sections) or "None.",
            "",
            "## Readiness-Only Sections",
            "",
            ", ".join(candidate.readiness_only_sections) or "None.",
            "",
            "## Blocking Reasons",
            "",
            *[f"- {reason}" for reason in candidate.blocking_reasons],
            "",
            "## Warnings",
            "",
            *[f"- {warning}" for warning in candidate.warnings],
            "",
            "## Next Required Steps",
            "",
            *[f"- {step}" for step in candidate.next_required_steps],
            "",
            "## Safety Notice",
            "",
            (
                "This historical signal readiness candidate is not a "
                "recommendation, ranking, vote, average score, consensus, "
                "allocation instruction, rebalancing instruction, trade "
                "signal, or execution instruction."
            ),
            "",
        ]
    )


def write_historical_signal_readiness_candidate(
    candidate: HistoricalSignalReadinessCandidate,
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write JSON and Markdown readiness candidate artifacts."""
    json_path.write_text(
        json.dumps(candidate.to_dict(), indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_historical_signal_readiness_candidate(candidate),
        encoding="utf-8",
    )
