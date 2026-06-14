"""Separate append-only ledger for historical readiness candidates."""

import csv
from dataclasses import asdict, dataclass
import json
from pathlib import Path

from broker_agents.historical.historical_signal_readiness import (
    HistoricalSignalReadinessCandidate,
)
from broker_agents.deals.readiness_metadata_enrichment import (
    CORE_METADATA_FIELDS,
)

RECORD_TYPE = "historical_signal_readiness_candidate"
COVERAGE_QUALITY_FIELDS = (
    "coverage_quality_label",
    "coverage_quality_severity",
    "date_coverage_status",
    "has_delayed_price_anchor",
    "has_limited_financials",
    "warning_count",
    "coverage_guardrail_status",
)
LEDGER_FIELDS = (
    "record_type",
    "ticker",
    "as_of_date",
    "run_id",
    "run_folder",
    "candidate_file",
    "assembly_file",
    "signal_generation_status",
    "safe_for_historical_signal_generation",
    "not_trade_signal",
    "not_recommendation",
    "not_allocation_instruction",
    "assembly_status",
    "partial_sections_count",
    "readiness_only_sections_count",
    "leakage_risk_sections_count",
    "blocking_reasons_count",
    "warnings_count",
    *COVERAGE_QUALITY_FIELDS,
    *CORE_METADATA_FIELDS,
    "metadata_enrichment_status",
    "missing_metadata_fields",
    "metadata_source_paths",
    "created_at",
    "source",
)
SAFETY_NOTICE = (
    "This historical readiness ledger contains readiness-only research "
    "artifacts. It is not a recommendation ledger, ranking ledger, allocation "
    "ledger, rebalancing ledger, trade signal ledger, or execution instruction "
    "ledger."
)


@dataclass(frozen=True)
class HistoricalReadinessLedgerRecord:
    """Stable readiness-only ledger record."""

    record_type: str
    ticker: str
    as_of_date: str
    run_id: str
    run_folder: str
    candidate_file: str
    assembly_file: str
    signal_generation_status: str
    safe_for_historical_signal_generation: bool
    not_trade_signal: bool
    not_recommendation: bool
    not_allocation_instruction: bool
    assembly_status: str
    partial_sections_count: int
    readiness_only_sections_count: int
    leakage_risk_sections_count: int
    blocking_reasons_count: int
    warnings_count: int
    coverage_quality_label: str
    coverage_quality_severity: str
    date_coverage_status: str
    has_delayed_price_anchor: bool
    has_limited_financials: bool
    warning_count: int
    coverage_guardrail_status: str
    readiness_label: object
    readiness_status: object
    readiness_score: object
    source_verification_status: object
    verified_source_count: object
    partial_source_count: object
    missing_source_count: object
    placeholder_heavy_source_count: object
    promotion_blocking_count: object
    promotion_blocking_bucket: object
    buffett_interest_level: object
    munger_interest_level: object
    fisher_interest_level: object
    lynch_interest_level: object
    bogle_interest_level: object
    buffett_decision: object
    munger_decision: object
    fisher_decision: object
    lynch_decision: object
    bogle_decision: object
    metadata_enrichment_status: str
    missing_metadata_fields: str
    metadata_source_paths: str
    created_at: str
    source: str

    def to_dict(self) -> dict:
        """Serialize the ledger record."""
        return asdict(self)


@dataclass(frozen=True)
class HistoricalReadinessArchiveResult:
    """Paths and counts updated by one readiness-ledger append."""

    record: HistoricalReadinessLedgerRecord
    jsonl_path: Path
    csv_path: Path
    snapshot_path: Path
    total_records: int


def build_historical_readiness_ledger_record(
    *,
    candidate: HistoricalSignalReadinessCandidate,
    run_folder: Path,
    candidate_file: Path,
    assembly_file: Path,
    created_at: str,
    metadata: dict | None = None,
) -> HistoricalReadinessLedgerRecord:
    """Build and enforce a readiness-only record."""
    if candidate.signal_generation_status != "readiness_only":
        raise ValueError("Historical readiness records must be readiness_only.")
    if candidate.safe_for_historical_signal_generation:
        raise ValueError("Historical readiness records cannot be signal-safe.")
    if not (
        candidate.not_trade_signal
        and candidate.not_recommendation
        and candidate.not_allocation_instruction
    ):
        raise ValueError(
            "Historical readiness records must preserve all safety invariants."
        )
    metadata = metadata or {}
    return HistoricalReadinessLedgerRecord(
        record_type=RECORD_TYPE,
        ticker=candidate.ticker,
        as_of_date=candidate.as_of_date,
        run_id=candidate.run_id,
        run_folder=str(run_folder),
        candidate_file=str(candidate_file),
        assembly_file=str(assembly_file),
        signal_generation_status="readiness_only",
        safe_for_historical_signal_generation=False,
        not_trade_signal=True,
        not_recommendation=True,
        not_allocation_instruction=True,
        assembly_status=candidate.assembly_status,
        partial_sections_count=len(candidate.partial_sections),
        readiness_only_sections_count=len(
            candidate.readiness_only_sections
        ),
        leakage_risk_sections_count=len(candidate.leakage_risk_sections),
        blocking_reasons_count=len(candidate.blocking_reasons),
        warnings_count=len(candidate.warnings),
        coverage_quality_label=str(
            metadata.get("coverage_quality_label") or "not_available"
        ),
        coverage_quality_severity=str(
            metadata.get("coverage_quality_severity") or "not_available"
        ),
        date_coverage_status=str(
            metadata.get("date_coverage_status") or "not_available"
        ),
        has_delayed_price_anchor=bool(
            metadata.get("has_delayed_price_anchor", False)
        ),
        has_limited_financials=bool(
            metadata.get("has_limited_financials", False)
        ),
        warning_count=int(metadata.get("warning_count") or 0),
        coverage_guardrail_status=str(
            metadata.get("coverage_guardrail_status") or "not_available"
        ),
        **{
            field: metadata.get(field, "Missing")
            for field in CORE_METADATA_FIELDS
        },
        metadata_enrichment_status=str(
            metadata.get("metadata_enrichment_status") or "not_available"
        ),
        missing_metadata_fields=str(
            metadata.get("missing_metadata_fields") or ""
        ),
        metadata_source_paths=str(
            metadata.get("metadata_source_paths") or ""
        ),
        created_at=created_at,
        source="analyze_stock_historical_mode",
    )


def _record_count(path: Path) -> int:
    """Count non-empty JSONL records."""
    if not path.exists():
        return 0
    return sum(
        bool(line.strip())
        for line in path.read_text(encoding="utf-8").splitlines()
    )


def append_historical_readiness_candidate(
    *,
    outputs_root: Path,
    candidate: HistoricalSignalReadinessCandidate,
    run_folder: Path,
    candidate_file: Path,
    assembly_file: Path,
    created_at: str,
    metadata: dict | None = None,
) -> HistoricalReadinessArchiveResult:
    """Append one candidate to the separate readiness research ledger."""
    record = build_historical_readiness_ledger_record(
        candidate=candidate,
        run_folder=run_folder,
        candidate_file=candidate_file,
        assembly_file=assembly_file,
        created_at=created_at,
        metadata=metadata,
    )
    ledger_dir = Path(outputs_root) / "historical_readiness_ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = ledger_dir / "historical_signal_readiness_ledger.jsonl"
    csv_path = ledger_dir / "historical_signal_readiness_ledger.csv"
    snapshot_path = (
        ledger_dir / "latest_historical_signal_readiness_ledger_snapshot.json"
    )

    with jsonl_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(record.to_dict(), separators=(",", ":")) + "\n")
    _ensure_csv_schema(csv_path)
    write_header = not csv_path.exists() or csv_path.stat().st_size == 0
    with csv_path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDS)
        if write_header:
            writer.writeheader()
        writer.writerow(record.to_dict())

    total_records = _record_count(jsonl_path)
    snapshot = {
        "total_records": total_records,
        "latest_record": record.to_dict(),
        "ledger_jsonl": str(jsonl_path),
        "ledger_csv": str(csv_path),
        "generated_at": created_at,
        "safety_notice": SAFETY_NOTICE,
    }
    snapshot_path.write_text(
        json.dumps(snapshot, indent=2),
        encoding="utf-8",
    )
    return HistoricalReadinessArchiveResult(
        record=record,
        jsonl_path=jsonl_path,
        csv_path=csv_path,
        snapshot_path=snapshot_path,
        total_records=total_records,
    )


def _ensure_csv_schema(csv_path: Path) -> None:
    """Upgrade readiness ledger CSV columns while preserving prior rows."""
    if not csv_path.exists() or csv_path.stat().st_size == 0:
        return
    with csv_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        existing_fields = tuple(reader.fieldnames or ())
        rows = list(reader)
    if existing_fields == LEDGER_FIELDS:
        return
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {field: row.get(field, "") for field in LEDGER_FIELDS}
            )
