"""Run-local assembly of historical input readiness and leakage metadata."""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path


@dataclass(frozen=True)
class HistoricalInputSectionStatus:
    """Point-in-time readiness for one historical input section."""

    section_name: str
    provider: str
    supports_as_of_date: bool
    enforcement_level: str
    leakage_risk: str
    status: str
    artifact_path: str | None = None
    rows_before_filter: int | None = None
    rows_after_filter: int | None = None
    future_rows_excluded_count: int | None = None
    missing_availability_date_count: int | None = None
    notes: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize one section status."""
        return asdict(self)


@dataclass(frozen=True)
class HistoricalEnrichedInputAssembly:
    """Combined run-local view of historical input readiness."""

    ticker: str
    as_of_date: str
    run_id: str
    historical_mode: bool
    point_in_time_enforcement: str
    assembly_status: str
    safe_for_historical_signal_generation: bool
    supported_sections: list[str] = field(default_factory=list)
    partial_sections: list[str] = field(default_factory=list)
    readiness_only_sections: list[str] = field(default_factory=list)
    unsupported_sections: list[str] = field(default_factory=list)
    leakage_risk_sections: list[str] = field(default_factory=list)
    section_statuses: list[HistoricalInputSectionStatus] = field(
        default_factory=list
    )
    artifacts: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    next_required_steps: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize the historical input assembly."""
        return {
            "ticker": self.ticker,
            "as_of_date": self.as_of_date,
            "run_id": self.run_id,
            "historical_mode": self.historical_mode,
            "point_in_time_enforcement": self.point_in_time_enforcement,
            "assembly_status": self.assembly_status,
            "safe_for_historical_signal_generation": (
                self.safe_for_historical_signal_generation
            ),
            "supported_sections": list(self.supported_sections),
            "partial_sections": list(self.partial_sections),
            "readiness_only_sections": list(self.readiness_only_sections),
            "unsupported_sections": list(self.unsupported_sections),
            "leakage_risk_sections": list(self.leakage_risk_sections),
            "section_statuses": [
                section.to_dict() for section in self.section_statuses
            ],
            "artifacts": dict(self.artifacts),
            "warnings": list(self.warnings),
            "next_required_steps": list(self.next_required_steps),
        }


def _base_section_status(capability: dict) -> HistoricalInputSectionStatus:
    """Translate a snapshot capability into an assembly section status."""
    enforcement = capability["enforcement_level"]
    status = (
        "unsupported"
        if enforcement == "unsupported"
        else (
            "partial_as_of_capable"
            if capability["supports_as_of_date"]
            and enforcement in {"full", "partial", "analysis_window_enforced"}
            else "readiness_only"
        )
    )
    return HistoricalInputSectionStatus(
        section_name=capability["section"],
        provider=capability["provider_name"],
        supports_as_of_date=capability["supports_as_of_date"],
        enforcement_level=enforcement,
        leakage_risk=capability["leakage_risk"],
        status=status,
        notes=[capability["notes"]],
    )


def build_historical_enriched_input_assembly(
    *,
    ticker: str,
    as_of_date: str,
    run_id: str,
    point_in_time_enforcement: str,
    historical_snapshot_contract: dict,
    historical_price_window: dict | None,
    official_financials_snapshot: dict,
    artifacts: dict[str, str] | None = None,
) -> HistoricalEnrichedInputAssembly:
    """Build a deterministic readiness assembly without generating signals."""
    section_statuses = [
        _base_section_status(capability)
        for capability in historical_snapshot_contract[
            "provider_capabilities"
        ]
    ]
    by_section = {
        section.section_name: section for section in section_statuses
    }

    if historical_price_window:
        analysis_window = historical_price_window["analysis_window"]
        by_section["market_prices"] = HistoricalInputSectionStatus(
            section_name="market_prices",
            provider="csv",
            supports_as_of_date=True,
            enforcement_level=analysis_window["enforcement_status"],
            leakage_risk="medium",
            status="partial_as_of_capable",
            artifact_path="run_manifest.json#historical_price_window",
            notes=[
                analysis_window["leakage_policy_note"],
                (
                    "The analysis cutoff is enforced, while price provenance "
                    "and completeness remain user-managed."
                ),
            ],
        )

    if official_financials_snapshot.get("enabled"):
        by_section["official_financials"] = HistoricalInputSectionStatus(
            section_name="official_financials",
            provider="historical_financials_csv",
            supports_as_of_date=True,
            enforcement_level="partial",
            leakage_risk="medium",
            status=official_financials_snapshot["status"],
            artifact_path=official_financials_snapshot["snapshot_file"],
            rows_before_filter=official_financials_snapshot[
                "rows_before_filter"
            ],
            rows_after_filter=official_financials_snapshot[
                "rows_after_filter"
            ],
            future_rows_excluded_count=official_financials_snapshot[
                "future_rows_excluded_count"
            ],
            missing_availability_date_count=official_financials_snapshot[
                "rows_missing_availability_date_count"
            ],
            notes=[
                (
                    "Rows are included only when filing_date or accepted_date "
                    "is on or before as_of_date."
                )
            ],
            warnings=list(official_financials_snapshot.get("warnings", [])),
        )

    ordered_sections = [
        by_section[capability["section"]]
        for capability in historical_snapshot_contract[
            "provider_capabilities"
        ]
    ]
    supported = [
        section.section_name
        for section in ordered_sections
        if section.enforcement_level == "full"
    ]
    partial = [
        section.section_name
        for section in ordered_sections
        if section.supports_as_of_date
        and section.enforcement_level
        in {"partial", "analysis_window_enforced"}
    ]
    readiness_only = [
        section.section_name
        for section in ordered_sections
        if section.enforcement_level == "readiness_only"
    ]
    unsupported = [
        section.section_name
        for section in ordered_sections
        if section.enforcement_level == "unsupported"
    ]
    leakage_risk = [
        section.section_name
        for section in ordered_sections
        if section.leakage_risk in {"medium", "high"}
    ]
    both_core_sections_partial = {
        "market_prices",
        "official_financials",
    }.issubset(partial)
    warnings = [
        "Full point-in-time enforcement is not yet guaranteed.",
        (
            "Historical signal generation remains disabled because important "
            "input sections are readiness-only or retain leakage risk."
        ),
    ]
    warnings.extend(
        warning
        for warning in historical_snapshot_contract.get("warnings", [])
        if warning and warning not in warnings
    )
    return HistoricalEnrichedInputAssembly(
        ticker=ticker.upper(),
        as_of_date=as_of_date,
        run_id=run_id,
        historical_mode=True,
        point_in_time_enforcement=point_in_time_enforcement,
        assembly_status=(
            "partial_historical_input"
            if both_core_sections_partial
            else "readiness_only"
        ),
        safe_for_historical_signal_generation=False,
        supported_sections=supported,
        partial_sections=partial,
        readiness_only_sections=readiness_only,
        unsupported_sections=unsupported,
        leakage_risk_sections=leakage_risk,
        section_statuses=ordered_sections,
        artifacts=dict(artifacts or {}),
        warnings=warnings,
        next_required_steps=[
            "Add point-in-time historical valuation inputs.",
            "Add point-in-time growth and PEG inputs.",
            "Add an as-of-safe market snapshot.",
            (
                "Add dated scuttlebutt, management incentives, and index "
                "overlap evidence."
            ),
            "Rebuild and validate the assembly before historical signals.",
        ],
    )


def render_historical_enriched_input_assembly(
    assembly: HistoricalEnrichedInputAssembly,
) -> str:
    """Render the broker-readable historical input assembly."""
    section_lines = [
        (
            f"| {section.section_name} | {section.provider} | "
            f"{'Yes' if section.supports_as_of_date else 'No'} | "
            f"{section.enforcement_level} | {section.leakage_risk} | "
            f"{section.status} |"
        )
        for section in assembly.section_statuses
    ]
    artifact_lines = [
        f"- {name}: {path}" for name, path in assembly.artifacts.items()
    ]
    return "\n".join(
        [
            "# Historical Enriched Input Assembly",
            "",
            "## Overview",
            "",
            f"- Ticker: {assembly.ticker}",
            f"- As-Of Date: {assembly.as_of_date}",
            (
                "- Point-in-Time Enforcement: "
                f"{assembly.point_in_time_enforcement}"
            ),
            f"- Assembly Status: {assembly.assembly_status}",
            "- Safe for historical signal generation: No",
            "",
            "## Available As-Of Inputs",
            "",
            (
                ", ".join(assembly.supported_sections)
                if assembly.supported_sections
                else "None fully enforced."
            ),
            "",
            "## Partial Inputs",
            "",
            (
                ", ".join(assembly.partial_sections)
                if assembly.partial_sections
                else "None."
            ),
            "",
            "## Readiness-Only Inputs",
            "",
            (
                ", ".join(assembly.readiness_only_sections)
                if assembly.readiness_only_sections
                else "None."
            ),
            "",
            "## Section Statuses",
            "",
            (
                "| Section | Provider | Supports As-Of Date | Enforcement | "
                "Leakage Risk | Status |"
            ),
            "|---|---|---|---|---|---|",
            *section_lines,
            "",
            "## Leakage Risk Sections",
            "",
            ", ".join(assembly.leakage_risk_sections),
            "",
            "## Artifacts",
            "",
            *(artifact_lines or ["- None"]),
            "",
            "## Warnings",
            "",
            *[f"- {warning}" for warning in assembly.warnings],
            "",
            "## Next Required Steps",
            "",
            *[f"- {step}" for step in assembly.next_required_steps],
            "",
            (
                "This historical enriched input assembly is not a "
                "recommendation, ranking, vote, average score, consensus, "
                "allocation instruction, rebalancing instruction, or trade "
                "signal."
            ),
            "",
        ]
    )


def write_historical_enriched_input_assembly(
    assembly: HistoricalEnrichedInputAssembly,
    *,
    json_path: Path,
    markdown_path: Path,
) -> None:
    """Write the machine-readable and human-readable assembly artifacts."""
    json_path.write_text(
        json.dumps(assembly.to_dict(), indent=2),
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_historical_enriched_input_assembly(assembly),
        encoding="utf-8",
    )
